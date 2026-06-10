# Ausome AI Studio — Backend

Modular monolith: Python packages under `backend/` wired into the FastAPI **api-gateway**. Pulse (editor) talks to the gateway only; workers run asynchronously.

## Services

| Package / service | Path | Status | Purpose |
|-------------------|------|--------|---------|
| **API Gateway** | `api-gateway/` | Production | FastAPI OpenAI-compatible surface, auth, routing, all `/v1/*` routes |
| **Agent runtime** | `agent_service/` | Done (M7–M12) | Hybrid state machine: plan → code → review → test → verify |
| **Planner** | `planner_service/` | Done (M8) | Structured `PlanOutput` via reasoning model |
| **Evaluation** | `evaluation_service/` | Done (M11) | Sandbox check runners (pytest, npm, eslint, ruff) + completion gate |
| **Graph** | `graph_service/` | Done (M9) | Postgres adjacency graph: files, classes, imports |
| **Memory** | `memory_service/` | Done (M10) | `project_memories` recall + post-run extraction |
| **Observability** | `observability_service/` | Done (Phase A) | Trace spans, token usage, cost, run timeline APIs |
| **Sandbox** | `sandbox-service/` | Done (M6) | Docker exec per workspace |
| Auth | `auth-service/` | Embedded | Supabase JWT + Keycloak JWKS in gateway |
| Model router | `model-router/` | Embedded | Task-based model matrix (M15) in `app/model_router.py` |
| Context | `context-service/` | Embedded | pgvector semantic search in gateway |

## API surface (gateway)

| Area | Endpoints |
|------|-----------|
| LLM | `POST /v1/chat/completions`, `POST /v1/completions`, `POST /v1/embeddings` |
| Context | `POST /v1/context/search`, `POST /v1/context/index` |
| Agent | `POST /v1/agent/run`, `GET /v1/agent/runs/{id}`, `POST .../tool-result`, `.../cancel`, `.../approve-plan` |
| Observability | `GET /v1/agent/runs`, `GET /v1/agent/runs/{id}/trace`, `GET /v1/observability/summary` |
| Eval | `POST /v1/eval/run`, `GET /v1/eval/runs/{id}` |
| Graph | `POST /v1/graph/upsert`, `POST /v1/graph/query` |
| Memory | `POST /v1/memory/recall`, `POST /v1/memory/upsert` |
| Snapshots | `POST /v1/snapshots/create`, `POST /v1/snapshots/{id}/restore` |
| Sessions | CRUD ` /v1/sessions/*` |
| App builder | `GET /v1/app-builder/templates`, `POST /v1/app-builder/scaffold` (M16 scaffold) |
| Sandbox | `POST /v1/sandbox/create`, `POST /v1/sandbox/exec` |

## Database schemas

Applied in order via `deployment/docker-compose.yml` Postgres init:

1. `api-gateway/db/schema.sql` — core tables, pgvector, `agent_runs`, `audit_logs`
2. `schema_v3.sql` — agent steps, graph, memory, eval, snapshots
3. `schema_v4.sql` — observability: `agent_trace_spans`, `llm_usage`, `prompt_versions`, `pulse_thread_id`

Gateway also applies `schema_v4.sql` on startup for existing volumes.

## Local development

```bash
docker compose -f deployment/docker-compose.yml up --build
```

| Service | URL |
|---------|-----|
| Gateway | http://127.0.0.1:8000 |
| Health | http://127.0.0.1:8000/health |
| MinIO console | http://127.0.0.1:9001 |
| Sandbox | http://127.0.0.1:8010 |

Configure Pulse **ausome** provider: endpoint `http://127.0.0.1:8000`, API key `ausome-dev` when `AUSOME_AUTH_DISABLED=true`.

Enable **Server agent orchestration** in Pulse Settings for hybrid gateway agent loop.

## PYTHONPATH (local)

```powershell
$env:PYTHONPATH="X:\Void\backend\api-gateway\app;X:\Void\backend"
cd X:\Void\backend\api-gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Related docs

- [docs/ausome/ARCHITECTURE.md](../docs/ausome/ARCHITECTURE.md)
- [docs/ausome/ROADMAP.md](../docs/ausome/ROADMAP.md)
- [docs/ausome/PRODUCTIZATION.md](../docs/ausome/PRODUCTIZATION.md)
- [docs/ausome/SECURITY.md](../docs/ausome/SECURITY.md)
- [deployment/README.md](../deployment/README.md)
