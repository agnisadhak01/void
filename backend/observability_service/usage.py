"""Token usage and cost estimation."""

from pathlib import Path
from typing import Any

import yaml

# Default $/1K tokens (input+output blended) when config missing
_DEFAULT_COSTS: dict[str, float] = {
    "qwen3-coder": 0.0002,
    "deepseek-coder-v2": 0.00015,
    "qwen3-235b-a22b": 0.001,
    "deepseek-v3": 0.0008,
    "bge-m3": 0.00005,
}

_cost_cache: dict[str, float] | None = None


def _load_costs() -> dict[str, float]:
    global _cost_cache
    if _cost_cache is not None:
        return _cost_cache
    costs = dict(_DEFAULT_COSTS)
    for path in (
        Path(__file__).resolve().parents[2] / "ai" / "embeddings" / "config.yaml",
        Path("/ai/embeddings/config.yaml"),
    ):
        if path.is_file():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                for model, cfg in (data.get("models") or {}).items():
                    if isinstance(cfg, dict) and "cost_per_1k_tokens" in cfg:
                        costs[model] = float(cfg["cost_per_1k_tokens"])
                for model, cfg in data.items():
                    if model == "models":
                        continue
                    if isinstance(cfg, dict) and "cost_per_1k_tokens" in cfg:
                        costs[model] = float(cfg["cost_per_1k_tokens"])
            except Exception:
                pass
            break
    _cost_cache = costs
    return costs


def estimate_cost(model: str, total_tokens: int) -> float:
    rate = _load_costs().get(model, _load_costs().get("qwen3-coder", 0.0002))
    return round((total_tokens / 1000.0) * rate, 6)


def parse_vllm_usage(body: dict[str, Any]) -> dict[str, int]:
    usage = body.get("usage") or {}
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    total = int(usage.get("total_tokens") or prompt + completion)
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": total}
