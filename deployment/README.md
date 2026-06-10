# Ausome AI Studio — Local Deployment

Docker Compose stack for full platform development on a single machine.

## Quick start

```powershell
cd X:\Void
docker compose -f deployment/docker-compose.yml up -d --build
```

## Services

| Compose service | Image / build | Port | Role |
|-----------------|---------------|------|------|
| `postgres` | pgvector/pgvector:pg16 | 5432 | Postgres + pgvector; init schemas v1–v4 |
| `minio` | minio/minio | 9000, 9001 | Object storage (workspace snapshots) |
| `api-gateway` | `backend/` Dockerfile | 8000 | FastAPI gateway + all Python packages |
| `sandbox-service` | `backend/sandbox-service` | 8010 | Per-workspace Docker exec |
| `indexing-worker` | `workers/indexing` | — | File watch → embeddings → pgvector (`index_jobs`) |
| `graph-indexing-worker` | `workers/graph-indexing` | — | Import graph extraction → `/v1/graph/upsert` |

## Endpoints

| URL | Purpose |
|-----|---------|
| http://localhost:8000/health | Gateway health (+ vLLM probe) |
| http://localhost:8000/v1/models | Model list |
| http://localhost:9001 | MinIO console (`ausome` / `ausome_dev_minio`) |

## Pulse configuration

**Settings → Models → Ausome Gateway**

| Field | Dev value |
|-------|-----------|
| Gateway URL | `http://127.0.0.1:8000` |
| API Key | `ausome-dev` (when auth disabled) |
| Custom headers JSON | `{"X-Ausome-Project-Id":"00000000-0000-0000-0000-000000000001","X-Ausome-Sandbox":"true"}` |

**Settings → Chat**

- Enable **Server agent orchestration** for hybrid gateway agent runtime (M7)
- **Auto-approve agent plans** — skip `awaiting_approval` gate (M8)

## Optional: vLLM on host

Gateway defaults to `VLLM_BASE_URL=http://host.docker.internal:8001/v1`. Run vLLM locally or via [infrastructure/helm/vllm](../infrastructure/helm/vllm).

Without vLLM, gateway returns stub completions and planner uses fallback plans.

## Environment (api-gateway)

| Variable | Default | Notes |
|----------|---------|-------|
| `AUSOME_AUTH_DISABLED` | `true` | Dev bypass |
| `DATABASE_URL` | postgres in compose | |
| `MINIO_*` | minio service | Snapshots (M13) |
| `REQUIRE_PLAN_APPROVAL` | `false` in compose | Set `true` to test approval flow |
| `SANDBOX_SERVICE_URL` | sandbox-service:8010 | |
| `RATE_LIMIT_PER_MINUTE` | 120 | M14 |
| `KEYCLOAK_JWKS_URL` | — | Production OIDC |
| `OPA_URL` | — | Policy sidecar |

## Smoke test (agent + trace)

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/v1/agent/run \
  -H "Authorization: Bearer ausome-dev" -H "Content-Type: application/json" \
  -d '{"goal":"smoke test","pulse_thread_id":"test-thread","require_plan_approval":false}'
curl -s http://127.0.0.1:8000/v1/agent/runs/{run_id}/trace -H "Authorization: Bearer ausome-dev"
```

## Related

- [backend/README.md](../backend/README.md)
- [docs/ausome/PRODUCTIZATION.md](../docs/ausome/PRODUCTIZATION.md)
