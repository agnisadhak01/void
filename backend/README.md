# Ausome AI Studio — Backend

| Service | Path | Purpose |
|---------|------|---------|
| API Gateway | `api-gateway/` | FastAPI OpenAI-compatible surface, auth, routing, audit |
| Auth | `auth-service/` | Supabase JWT validation (embedded in gateway) |
| Model router | `model-router/` | Task-based model selection (embedded in gateway) |
| Context | `context-service/` | pgvector retrieval (embedded in gateway) |
| Agent | `agent-service/` | Agent run logging (Phase 2 orchestration) |
| Sandbox | `sandbox-service/` | Docker exec per workspace |

## Local development

```bash
docker compose -f deployment/docker-compose.yml up --build
```

Gateway: http://127.0.0.1:8000/health

Configure Pulse **Ausome Gateway** provider with endpoint `http://127.0.0.1:8000` and API key `ausome-dev` (when `AUSOME_AUTH_DISABLED=true`).
