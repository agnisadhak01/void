from typing import Any

import httpx

from app.config import settings

# M15 — task-specific model matrix with fallbacks
ROUTING: dict[str, dict[str, str]] = {
    "chat": {"primary": "qwen3-coder", "fallback": "deepseek-coder-v2"},
    "completion": {"primary": "qwen3-coder", "fallback": "deepseek-coder-v2"},
    "embedding": {"primary": settings.embedding_model, "fallback": settings.embedding_model},
    "rerank": {"primary": settings.rerank_model, "fallback": settings.rerank_model},
    "reasoning": {"primary": "qwen3-235b-a22b", "fallback": "deepseek-v3"},
    "review": {"primary": "deepseek-v3", "fallback": "qwen3-coder"},
}

_health_cache: dict[str, bool] = {}


def resolve_task(headers: dict[str, str], body: dict[str, Any]) -> str:
    task = headers.get("x-ausome-task") or headers.get("X-Ausome-Task")
    if task:
        return task
    if body.get("suffix") is not None:
        return "completion"
    route = body.get("route") or headers.get("x-ausome-route")
    if route == "reasoning":
        return "reasoning"
    if route == "review":
        return "review"
    return "chat"


def resolve_model(task: str, requested: str | None, *, prefer_fast: bool = False) -> str:
    if requested and requested not in ("auto", "default"):
        return requested
    policy = ROUTING.get(task, ROUTING["chat"])
    if prefer_fast and task == "completion":
        return policy.get("fallback", policy["primary"])
    primary = policy["primary"]
    if _health_cache.get(primary) is False:
        return policy["fallback"]
    return primary


async def check_vllm_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.vllm_base_url.rstrip('/')}/models", headers=vllm_headers())
            ok = resp.status_code < 400
            for model in {p["primary"] for p in ROUTING.values()}:
                _health_cache[model] = ok
            return ok
    except httpx.HTTPError:
        return False


def vllm_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.vllm_api_key}"}
