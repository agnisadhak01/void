import json
import re
import time

import asyncpg
import httpx

from planner_service.schemas import PLANNER_SYSTEM, PlanOutput

from app.config import settings
from app.model_router import resolve_model, vllm_headers
from observability_service.spans import ensure_prompt_version, record_llm_usage, record_span
from observability_service.usage import parse_vllm_usage


async def generate_plan(
    goal: str,
    memories: list[str] | None = None,
    *,
    conn: asyncpg.Connection | None = None,
    run_id: str | None = None,
) -> PlanOutput:
    memory_block = ""
    if memories:
        memory_block = "\nProject memories:\n" + "\n".join(f"- {m}" for m in memories[:10])

    messages = [
        {"role": "system", "content": PLANNER_SYSTEM},
        {"role": "user", "content": f"Goal: {goal}{memory_block}"},
    ]
    model = resolve_model("reasoning", None)
    body = {"model": model, "messages": messages, "temperature": 0.2}
    url = f"{settings.vllm_base_url.rstrip('/')}/chat/completions"
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, json=body, headers={**vllm_headers(), "X-Ausome-Task": "reasoning"})
            latency_ms = int((time.perf_counter() - t0) * 1000)
            if resp.status_code >= 400:
                if conn and run_id:
                    await record_span(
                        conn,
                        run_id,
                        "llm",
                        "planner",
                        phase="plan",
                        status="error",
                        latency_ms=latency_ms,
                        payload={"model": model, "http_status": resp.status_code},
                    )
                return _fallback_plan(goal)
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            plan = _parse_plan(content, goal)
            if conn and run_id:
                prompt_id = await ensure_prompt_version(conn, "planner", PLANNER_SYSTEM + goal)
                span_id = await record_span(
                    conn,
                    run_id,
                    "llm",
                    "planner",
                    phase="plan",
                    status="ok",
                    latency_ms=latency_ms,
                    payload={"model": model, "route": "reasoning"},
                    prompt_version_id=prompt_id,
                )
                usage = parse_vllm_usage(data)
                await record_llm_usage(
                    conn,
                    span_id,
                    run_id,
                    model,
                    "reasoning",
                    usage["prompt_tokens"],
                    usage["completion_tokens"],
                )
            return plan
    except (httpx.HTTPError, KeyError, IndexError):
        return _fallback_plan(goal)


def _parse_plan(content: str, goal: str) -> PlanOutput:
    match = re.search(r"\{[\s\S]*\}", content)
    if match:
        try:
            data = json.loads(match.group())
            return PlanOutput.model_validate(data)
        except Exception:
            pass
    return _fallback_plan(goal)


def _fallback_plan(goal: str) -> PlanOutput:
    return PlanOutput(
        tasks=[
            "Explore codebase structure",
            "Identify relevant files",
            f"Implement: {goal}",
            "Run tests and lint",
            "Summarize changes",
        ],
        files=[],
        risks=["Plan generated without reasoning model — review carefully"],
        dependencies=[],
    )
