import json
import re

import httpx

from planner_service.schemas import PLANNER_SYSTEM, PlanOutput

from app.config import settings
from app.model_router import resolve_model, vllm_headers


async def generate_plan(goal: str, memories: list[str] | None = None) -> PlanOutput:
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
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, json=body, headers={**vllm_headers(), "X-Ausome-Task": "reasoning"})
            if resp.status_code >= 400:
                return _fallback_plan(goal)
            content = resp.json()["choices"][0]["message"]["content"]
            return _parse_plan(content, goal)
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
