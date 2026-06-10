# Ausome AI Studio — Productization Roadmap

After M7–M16 (agent runtime, planner, eval, graph, memory, multi-agent, snapshots, security, router v2), the platform shifts from **feature milestones** to **productization phases**.

Phase A (Agent Observatory) is implemented. See [ROADMAP.md](ROADMAP.md) for engineering milestones.

## Maturity snapshot

| Capability | Status |
|------------|--------|
| Cursor-class editor (Pulse) | Done |
| Gateway + hybrid agent runtime | Done |
| Multi-phase agents (plan/code/review/test) | Done |
| Evaluation gates | Done (real exit codes) |
| Knowledge graph (MVP) | Done |
| Project memory (MVP) | Done |
| **Agent Observatory (Phase A)** | Done |
| Software factory / cloud platform | Next |

---

## Phase A — Agent Observatory (complete)

**Goal:** Debug agent runs without reading Postgres or raw logs.

### Backend

- Schema: [`backend/api-gateway/db/schema_v4.sql`](../backend/api-gateway/db/schema_v4.sql) — `agent_trace_spans`, `llm_usage`, `prompt_versions`, `pulse_thread_id`
- Package: [`backend/observability_service/`](../backend/observability_service/)
- APIs:
  - `GET /v1/agent/runs` — list runs (filter by `pulse_thread_id`, `project_id`, `status`)
  - `GET /v1/agent/runs/{id}/trace` — full timeline + token/cost summary
  - `GET /v1/observability/summary` — aggregates

### Pulse

- Collapsible **Agent runs** panel in chat sidebar ([`AgentRunsPanel.tsx`](../src/vs/workbench/contrib/void/browser/react/src/sidebar-tsx/agent-runs/AgentRunsPanel.tsx))
- Run selector, timeline, span details, **Approve plan** button
- `lastGatewayRunId` on thread state

### Enable

1. `ausome` provider configured
2. Settings → **Server agent orchestration** enabled
3. Send an agent message — panel shows runs for the current thread

### Smoke test

```bash
docker compose -f deployment/docker-compose.yml up --build -d
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/v1/agent/run \
  -H "Authorization: Bearer ausome-dev" -H "Content-Type: application/json" \
  -d '{"goal":"smoke test","pulse_thread_id":"test-thread","require_plan_approval":false}'
# Use run_id from response:
curl -s http://127.0.0.1:8000/v1/agent/runs/{run_id}/trace -H "Authorization: Bearer ausome-dev"
curl -s "http://127.0.0.1:8000/v1/agent/runs?pulse_thread_id=test-thread" -H "Authorization: Bearer ausome-dev"
```

---

## Phase B — Human-in-the-loop workflows

**Depends on:** A

| Deliverable | Description |
|-------------|-------------|
| `approval_requests` table | Plan, execute, code review, deploy approval chains |
| Role actors | Approvers, reviewers, auditors (Keycloak groups) |
| Panel actions | Approve/reject/request changes from Agent Observatory |

**Enterprise flow:** Plan → Approval → Execute → Code review → Deploy approval → Done

---

## Phase C — Project Knowledge Graph v2

**Depends on:** A

Extend [`graph_service/extractor.py`](../backend/graph_service/extractor.py):

- API endpoints, database tables, auth flows, external services
- Planner injects `graph_query` for impact analysis

**Queries:** “Where does payment processing start?”, “What breaks if I remove this table?”

---

## Phase D — Continuous learning memory

**Depends on:** A, C

Upgrade [`memory_service`](../backend/memory_service/):

- Outcome tags: success, failure, incident
- Semantic recall (pgvector on facts)
- Post-mortem extraction from failed runs

---

## Phase E — Autonomous repository maintenance

**Depends on:** A, B

Scheduled workers:

| Schedule | Jobs |
|----------|------|
| Weekly | Dependency updates, security scans, dead code |
| Daily | Broken test detection |
| Monthly | Architecture audit |

---

## Phase F — Deployment agents

**Depends on:** E, Helm ([`infrastructure/helm/ausome-studio`](../../infrastructure/helm/ausome-studio))

Pipeline: Generate → Build → Containerize → Deploy → Verify → Monitor

Integrations: Argo CD, Traefik, Prometheus

---

## Phase G — Self-hosted team platform

**Depends on:** B, M14 security

- Organizations, teams, permissions
- Shared memories and knowledge graphs per project

---

## Phase H — Model evaluation lab

**Depends on:** A

Benchmark suite: fix bug, create API, refactor, write tests, migrate DB

Measure per model: success rate, latency, cost, tool usage, verification pass rate

Auto-route tasks to best-performing model (extends M15 router)

---

## Phase I — Full app generator

**Depends on:** F, H

Prompt → multi-agent (frontend, backend, DB, DevOps, QA) → deploy → live URL

Builds on M16 app builder templates

---

## Execution order

```
A (done) → B or H → C → D → E → F → G → I
```

| Weeks | Focus |
|-------|-------|
| 1–2 | Phase A (complete) |
| 3–5 | Phase B (external users) or Phase H (model tuning) |
| 6+ | C → D → E → F → G → I |

---

## Related docs

- [ROADMAP.md](ROADMAP.md) — M1–M16 engineering milestones
- [SECURITY.md](SECURITY.md) — production controls
- [ARCHITECTURE.md](ARCHITECTURE.md) — system design
