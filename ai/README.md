# Ausome AI Assets

Shared model routing, embedding, and cost configuration for the gateway and workers.

## Layout

| Path | Purpose |
|------|---------|
| `embeddings/config.yaml` | Model matrix (M15), embedding dims, **cost_per_1k_tokens** |
| `rerankers/config.yaml` | BGE-Reranker-v2 settings |
| `prompts/` | Shared prompt templates |

## Model routing (M15)

Gateway [`model_router.py`](../backend/api-gateway/app/model_router.py) and `embeddings/config.yaml` define task routes:

| Task key | Primary model | Use |
|----------|---------------|-----|
| `chat` | qwen3-coder | Agent coding, chat |
| `completion` | qwen3-coder | FIM (&lt;150ms target) |
| `reasoning` | qwen3-235b-a22b | Planner |
| `review` | deepseek-v3 | Reviewer phase |
| `embedding` | bge-m3 | Context search |

Fallback chains and health checks in `model_router.py`. Cost estimation in `observability_service/usage.py` reads `cost_per_1k_tokens` from this config (mounted at `/ai` in gateway Docker image).

## Related

- [../docs/ausome/ARCHITECTURE.md](../docs/ausome/ARCHITECTURE.md)
- [../backend/api-gateway/app/model_router.py](../backend/api-gateway/app/model_router.py)
