# Ausome AI Studio — Roadmap

North-star document for the platform. Pulse editor docs remain in [../INDEX.md](../INDEX.md).

## Phases

| Phase | Horizon | Goal |
|-------|---------|------|
| 1 | Months 1–3 | Cursor alternative: gateway, vLLM, pgvector search, agent + audit |
| 2 | Months 4–8 | Multi-agent SE: planner, evaluation, graph, memory, snapshots |
| 3 | Months 9–18 | AI app builder: generate, deploy, infra, CI/CD |

## MVP milestones (Phase 1 — complete)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1–2 | M1 Foundation | Pulse + gateway stub, docker-compose, `ausome` provider |
| 3–4 | M2 Chat + auth | FastAPI gateway, Supabase JWT, vLLM routing |
| 5–6 | M3 Completion + context | FIM endpoint, indexing worker, semantic search |
| 7–8 | M4 Edit mode | Gateway routing for Ctrl+K / apply |
| 9–10 | M5 Agent + audit | RBAC, audit logs, git tools |
| 11–12 | M6 Production | Docker sandboxes, Helm umbrella chart |

## Agent platform (M7–M16)

| Milestone | Status | Deliverable |
|-----------|--------|-------------|
| **Phase 0** | Done | Agent run lifecycle, JWT user upsert, session CRUD, real embeddings, `index_jobs` worker, MinIO client |
| **M7** | Done | `agent_service` runtime, `/v1/agent/run\|status\|cancel\|tool-result`, `agent_run_steps`, Pulse hybrid loop |
| **M8** | Done | `planner_service`, structured `PlanOutput`, reasoning route, plan approval gate |
| **M11** | Done | `evaluation_service`, sandbox check runners, completion gate |
| **M9** | Done | Postgres `graph_nodes` / `graph_edges`, graph extractor, graph-indexing worker |
| **M10** | Done | `project_memories`, recall/extract in planner and runtime |
| **M12** | Done | Phase actors: plan → code → review → test in state machine |
| **M13** | Done | MinIO workspace snapshots before execution, restore API |
| **M14** | Done | Keycloak JWKS path, OPA middleware stub, rate limiting, security docs |
| **M15** | Done | Task-specific model matrix with fallbacks in `model_router.py` |
| **M16** | Scaffold | App builder templates + `/v1/app-builder/scaffold` (full generation deferred) |

### Hybrid orchestration

- **Gateway** owns planning, state machine, verification, audit.
- **Pulse** executes tools that need local workspace access (`semantic_search`, `read_lint_errors`, etc.) and POSTs `/v1/agent/runs/{id}/tool-result`.
- Enable in Pulse: **Settings → Agent orchestration** (or `agentOrchestrationEnabled` in global settings) with `ausome` provider.

### Key paths

| Component | Path |
|-----------|------|
| Agent runtime | `backend/agent_service/runtime.py` |
| Planner | `backend/planner_service/` |
| Evaluation | `backend/evaluation_service/` |
| Graph | `backend/graph_service/` |
| Memory | `backend/memory_service/` |
| API routes | `backend/api-gateway/app/routes/` |
| Schema v3 | `backend/api-gateway/db/schema_v3.sql` |
| Pulse gateway client | `src/vs/workbench/contrib/void/common/ausomeGatewayHelper.ts` |

## Current status

- Pulse editor fork with chat, agent, apply, FIM
- `backend/api-gateway` — modular FastAPI with agent, eval, graph, memory, snapshots
- `deployment/docker-compose.yml` — Postgres, MinIO, gateway, sandbox, indexing + graph workers
- `ausome` LLM provider with optional server-side agent orchestration

## Execution order (reference)

```
Phase 0 → M7 → M8 → M11 → M9 → M10 → M12 → M13 → M14 → M15 → M16
```
