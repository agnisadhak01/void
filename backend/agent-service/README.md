# Agent Service

Hybrid agent runtime for Ausome AI Studio. Implemented as `backend/agent_service/` (import name uses underscore; folder `agent-service/` is legacy README path).

## Role

Server-side state machine for gateway-orchestrated agent runs. Pulse executes tools locally; gateway owns plan, phases, eval gate, and audit.

## State machine

| Phase | Actor | Action |
|-------|-------|--------|
| plan | planner_service | Structured JSON plan |
| code | Pulse (local) | `semantic_search` tool |
| review | Pulse (local) | `read_lint_errors` |
| test | evaluation_service | pytest/npm/eslint/ruff in sandbox |

## API (via gateway `routes/agent.py`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/agent/run` | Start run |
| GET | `/v1/agent/runs/{id}` | Poll status + pending tool |
| POST | `/v1/agent/runs/{id}/tool-result` | Submit local tool output |
| POST | `/v1/agent/runs/{id}/cancel` | Cancel |
| POST | `/v1/agent/runs/{id}/approve-plan` | Approve after `awaiting_approval` |

## Persistence

- `agent_runs` — status, goal, phase, plan, `pulse_thread_id`, `snapshot_id`
- `agent_run_steps` — plan, tool_request, tool_result, verify events
- `agent_trace_spans` — timing + payloads (Phase A)
- `audit_logs` — append-only actions

## Pulse integration

- `ausomeGatewayHelper.ts` — HTTP client
- `chatThreadService._runGatewayAgent` — hybrid loop
- Settings: `agentOrchestrationEnabled`, `agentAutoApprovePlan`

## Code

- `runtime.py` — `AgentRuntime` class
- `models.py` — Pydantic request/response types
- `phases.py` — phase transition helpers

See [../../docs/ausome/ARCHITECTURE.md](../../docs/ausome/ARCHITECTURE.md).
