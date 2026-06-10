import json
import time
import uuid
from typing import Any, AsyncIterator

import asyncpg
import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.audit import log_audit, start_agent_run
from app.auth import AuthUser, CurrentUser, require_role
from app.config import settings
from app.context_service import get_pool, semantic_search, upsert_file_chunks
from app.embeddings import embed_texts
from app.middleware.opa import OPAMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.model_router import check_vllm_health, resolve_model, resolve_task, vllm_headers
from app.routes import agent, app_builder, eval as eval_routes, graph, memory, observability, sessions, snapshots
from observability_service.spans import record_llm_usage, record_span
from observability_service.usage import parse_vllm_usage
from app.sandbox import create_sandbox, run_in_sandbox
from typing import Annotated

app = FastAPI(title="Ausome AI Studio API Gateway", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(OPAMiddleware)

app.include_router(agent.router)
app.include_router(eval_routes.router)
app.include_router(graph.router)
app.include_router(memory.router)
app.include_router(snapshots.router)
app.include_router(sessions.router)
app.include_router(app_builder.router)
app.include_router(observability.router)

_pool: asyncpg.Pool | None = None


async def _apply_schema_migrations(pool: asyncpg.Pool) -> None:
    schema_path = __import__("pathlib").Path(__file__).resolve().parent.parent / "db" / "schema_v4.sql"
    if not schema_path.is_file():
        return
    sql = schema_path.read_text(encoding="utf-8")
    async with pool.acquire() as conn:
        await conn.execute(sql)


@app.on_event("startup")
async def startup() -> None:
    global _pool
    try:
        _pool = await get_pool()
        app.state.db_pool = _pool
        await _apply_schema_migrations(_pool)
        await check_vllm_health()
    except Exception:
        _pool = None
        app.state.db_pool = None


@app.on_event("shutdown")
async def shutdown() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        app.state.db_pool = None


def _pool_or_503() -> asyncpg.Pool:
    if _pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return _pool


@app.get("/health")
async def health() -> dict:
    vllm_ok = await check_vllm_health()
    return {"status": "ok", "service": "ausome-api-gateway", "vllm": vllm_ok}


@app.get("/v1/models")
async def list_models(user: CurrentUser) -> dict:
    return {
        "object": "list",
        "data": [
            {"id": "qwen3-coder", "object": "model"},
            {"id": "deepseek-coder-v2", "object": "model"},
            {"id": "qwen3-235b-a22b", "object": "model"},
            {"id": "deepseek-v3", "object": "model"},
            {"id": settings.embedding_model, "object": "model"},
        ],
    }


async def _record_gateway_llm(
    run_id: str | None,
    task: str,
    model: str,
    data: dict,
    latency_ms: int,
) -> None:
    if not _pool or not run_id:
        return
    usage = parse_vllm_usage(data)
    async with _pool.acquire() as conn:
        span_id = await record_span(
            conn,
            run_id,
            "llm",
            f"gateway/{task}",
            status="ok",
            latency_ms=latency_ms,
            payload={"model": model, "route": task},
        )
        await record_llm_usage(
            conn,
            span_id,
            run_id,
            model,
            task,
            usage["prompt_tokens"],
            usage["completion_tokens"],
        )


async def _proxy_vllm(
    path: str,
    body: dict,
    stream: bool,
    *,
    task: str = "chat",
    run_id: str | None = None,
) -> Any:
    url = f"{settings.vllm_base_url.rstrip('/')}/{path.lstrip('/')}"
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=300.0) as client:
        if stream:
            req = client.build_request("POST", url, json=body, headers=vllm_headers())
            resp = await client.send(req, stream=True)

            async def gen() -> AsyncIterator[bytes]:
                async for chunk in resp.aiter_bytes():
                    yield chunk

            return StreamingResponse(gen(), media_type="text/event-stream")
        resp = await client.post(url, json=body, headers=vllm_headers())
        latency_ms = int((time.perf_counter() - t0) * 1000)
        if resp.status_code >= 400:
            return await _stub_completion(body, stream, task=task, run_id=run_id, latency_ms=latency_ms)
        data = resp.json()
        await _record_gateway_llm(run_id, task, body.get("model", ""), data, latency_ms)
        return JSONResponse(content=data)


async def _stub_completion(
    body: dict,
    stream: bool,
    *,
    task: str = "chat",
    run_id: str | None = None,
    latency_ms: int = 0,
) -> Any:
    model = body.get("model", "qwen3-coder")
    if body.get("suffix") is not None or "prompt" in body:
        text = "// Ausome stub completion\n"
        payload = {
            "id": f"cmpl-{uuid.uuid4().hex[:8]}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{"text": text, "index": 0, "finish_reason": "stop"}],
        }
        return JSONResponse(content=payload)

    content = "Ausome AI Studio gateway stub response. Connect vLLM at VLLM_BASE_URL for live inference."
    if stream:
        chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
        }
        done = {**chunk, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}

        async def gen() -> AsyncIterator[bytes]:
            yield f"data: {json.dumps(chunk)}\n\n".encode()
            yield f"data: {json.dumps(done)}\n\n".encode()
            yield b"data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    payload = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": len(content.split()), "total_tokens": len(content.split())},
    }
    await _record_gateway_llm(run_id, task, model, payload, latency_ms)
    return JSONResponse(content=payload)


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, user: CurrentUser) -> Any:
    body = await request.json()
    task = resolve_task(dict(request.headers), body)
    body["model"] = resolve_model(task, body.get("model"))
    stream = bool(body.get("stream", False))

    run_id = request.headers.get("x-ausome-run-id") or request.headers.get("X-Ausome-Run-Id")
    if _pool:
        async with _pool.acquire() as conn:
            await log_audit(conn, user, "llm.chat", body.get("model"), {"task": task, "run_id": run_id})

    try:
        return await _proxy_vllm("chat/completions", body, stream, task=task, run_id=run_id)
    except httpx.HTTPError:
        return await _stub_completion(body, stream, task=task, run_id=run_id)


@app.post("/v1/completions")
async def completions(request: Request, user: CurrentUser) -> Any:
    body = await request.json()
    body["model"] = resolve_model("completion", body.get("model"), prefer_fast=True)
    stream = bool(body.get("stream", False))

    if _pool:
        async with _pool.acquire() as conn:
            await log_audit(conn, user, "llm.completion", body.get("model"), {})

    run_id = request.headers.get("x-ausome-run-id") or request.headers.get("X-Ausome-Run-Id")
    try:
        return await _proxy_vllm("completions", body, stream, task="completion", run_id=run_id)
    except httpx.HTTPError:
        return await _stub_completion(body, stream, task="completion", run_id=run_id)


@app.post("/v1/embeddings")
async def embeddings_endpoint(request: Request, user: CurrentUser) -> dict:
    body = await request.json()
    input_text = body.get("input", "")
    inputs = input_text if isinstance(input_text, list) else [input_text]
    vectors = await embed_texts(inputs)
    data = [{"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vectors)]
    return {"object": "list", "data": data, "model": settings.embedding_model}


class ContextSearchRequest(BaseModel):
    project_id: str = Field(default_factory=lambda: settings.default_project_id)
    query: str
    limit: int = 10


@app.post("/v1/context/search")
async def context_search(req: ContextSearchRequest, user: CurrentUser) -> dict:
    pool = _pool_or_503()
    query_vecs = await embed_texts([req.query])
    query_vec = query_vecs[0]
    async with pool.acquire() as conn:
        await log_audit(conn, user, "context.search", req.query[:100], {"project_id": req.project_id})
        results = await semantic_search(conn, req.project_id, req.query, query_vec, req.limit)
    return {"query": req.query, "results": results}


class IndexChunkRequest(BaseModel):
    project_id: str
    path: str
    chunks: list[str]
    embeddings: list[list[float]] | None = None


DevUser = Annotated[AuthUser, Depends(require_role("admin", "developer"))]


@app.post("/v1/context/index")
async def context_index(req: IndexChunkRequest, user: DevUser) -> dict:
    pool = _pool_or_503()
    embs = req.embeddings
    if not embs:
        embs = await embed_texts(req.chunks)
    async with pool.acquire() as conn:
        count = await upsert_file_chunks(conn, req.project_id, req.path, req.chunks, embs)
        await log_audit(conn, user, "context.index", req.path, {"chunks": count})
    return {"indexed_chunks": count, "path": req.path}


class AgentToolRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None


@app.post("/v1/agent/tool")
async def agent_tool(req: AgentToolRequest, user: DevUser) -> dict:
    pool = _pool_or_503()
    async with pool.acquire() as conn:
        run_id = await start_agent_run(conn, user, req.session_id)
        await log_audit(
            conn,
            user,
            f"agent.tool.{req.tool_name}",
            req.arguments.get("uri") or req.arguments.get("command"),
            req.arguments,
            agent_run_id=run_id,
        )
    return {"agent_run_id": run_id, "status": "logged"}


class SandboxExecRequest(BaseModel):
    workspace_id: str
    command: str
    cwd: str | None = None


@app.post("/v1/sandbox/exec")
async def sandbox_exec(req: SandboxExecRequest, user: DevUser) -> dict:
    result = await run_in_sandbox(req.workspace_id, req.command, req.cwd)
    if _pool:
        async with _pool.acquire() as conn:
            await log_audit(conn, user, "sandbox.exec", req.command[:200], result)
    return result


class SandboxCreateRequest(BaseModel):
    workspace_id: str


@app.post("/v1/sandbox/create")
async def sandbox_create_endpoint(req: SandboxCreateRequest, user: DevUser) -> dict:
    return await create_sandbox(req.workspace_id)


@app.post("/v1/rerank")
async def rerank(request: Request, user: CurrentUser) -> dict:
    body = await request.json()
    query = body.get("query", "")
    documents = body.get("documents", [])
    scored = [{"index": i, "score": 1.0 - i * 0.01, "document": d} for i, d in enumerate(documents)]
    return {"query": query, "results": scored}
