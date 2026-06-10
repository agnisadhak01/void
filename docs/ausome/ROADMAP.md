# Ausome AI Studio — Roadmap

North-star document for the platform. Pulse editor docs remain in [../INDEX.md](../INDEX.md).

## Phases

| Phase | Horizon | Goal |
|-------|---------|------|
| 1 | Months 1–3 | Cursor alternative: gateway, vLLM, pgvector search, agent + audit |
| 2 | Months 4–8 | Multi-agent SE: refactor, QA, DevOps, docs agents |
| 3 | Months 9–18 | AI app builder: generate, deploy, infra, CI/CD |

## MVP milestones (12 weeks)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1–2 | M1 Foundation | Pulse + gateway stub, docker-compose, `ausome` provider |
| 3–4 | M2 Chat + auth | FastAPI gateway, Supabase JWT, vLLM routing |
| 5–6 | M3 Completion + context | FIM endpoint, indexing worker, semantic search |
| 7–8 | M4 Edit mode | Gateway routing for Ctrl+K / apply |
| 9–10 | M5 Agent + audit | RBAC, audit logs, git tools |
| 11–12 | M6 Production | Docker sandboxes, Helm umbrella chart |

## Current status

- Pulse editor fork with Phase 1 UI features (chat, agent, apply, FIM)
- `backend/api-gateway` — FastAPI OpenAI-compatible surface
- `deployment/docker-compose.yml` — local stack
- `ausome` LLM provider in Pulse
