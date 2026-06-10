# Ausome API Gateway

FastAPI OpenAI-compatible gateway for Pulse. Modular monolith entry point — imports packages from `backend/` via `PYTHONPATH`.

## Run locally

```bash
# From repo root with Docker (recommended)
docker compose -f deployment/docker-compose.yml up api-gateway --build

# Or direct (Windows)
$env:PYTHONPATH="X:\Void\backend\api-gateway\app;X:\Void\backend"
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Structure

```
app/
  main.py              # LLM proxy, startup, middleware
  config.py            # pydantic-settings env
  auth.py              # Supabase + Keycloak JWKS
  audit.py             # agent_runs, steps, audit_logs
  model_router.py      # M15 task matrix + fallbacks
  embeddings.py        # vLLM embeddings
  storage.py           # MinIO client
  routes/
    agent.py           # /v1/agent/*
    observability.py   # list runs, trace, summary
    eval.py graph.py memory.py snapshots.py sessions.py app_builder.py
  middleware/
    rate_limit.py opa.py
db/
  schema.sql schema_v3.sql schema_v4.sql
```

## Environment

See `app/config.py`. Key variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection |
| `AUSOME_AUTH_DISABLED` | Dev auth bypass |
| `SUPABASE_JWT_SECRET` | HS256 validation |
| `KEYCLOAK_JWKS_URL` / `KEYCLOAK_ISSUER` | OIDC (M14) |
| `VLLM_BASE_URL` | Inference upstream |
| `MINIO_*` | Snapshot storage |
| `OPA_URL` | Policy sidecar |
| `RATE_LIMIT_PER_MINUTE` | Token bucket |
| `REQUIRE_PLAN_APPROVAL` | Default plan gate |

## Health

`GET /health` → `{ status, service, vllm }`

## Docs

- [../../docs/ausome/ARCHITECTURE.md](../../docs/ausome/ARCHITECTURE.md)
- [../README.md](../README.md)
