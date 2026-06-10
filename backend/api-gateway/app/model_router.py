from typing import Any

from app.config import settings

# Task routing policy — see docs/ausome/ROADMAP.md
ROUTING = {
    "chat": {"primary": "qwen3-coder", "fallback": "deepseek-coder-v2"},
    "completion": {"primary": "qwen3-coder", "fallback": "deepseek-coder-v2"},
    "embedding": {"primary": settings.embedding_model, "fallback": settings.embedding_model},
    "rerank": {"primary": settings.rerank_model, "fallback": settings.rerank_model},
    "reasoning": {"primary": "qwen3-235b-a22b", "fallback": "deepseek-v3"},
}


def resolve_task(headers: dict[str, str], body: dict[str, Any]) -> str:
    task = headers.get("x-ausome-task") or headers.get("X-Ausome-Task")
    if task:
        return task
    if body.get("suffix") is not None:
        return "completion"
    route = body.get("route") or headers.get("x-ausome-route")
    if route == "reasoning":
        return "reasoning"
    return "chat"


def resolve_model(task: str, requested: str | None) -> str:
    if requested and requested not in ("auto", "default"):
        return requested
    policy = ROUTING.get(task, ROUTING["chat"])
    return policy["primary"]


def vllm_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.vllm_api_key}"}
