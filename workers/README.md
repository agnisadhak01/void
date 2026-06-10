# Ausome Workers

Background workers for indexing and graph extraction. Started via [deployment/docker-compose.yml](../deployment/docker-compose.yml).

## Workers

| Worker | Path | Role | Gateway endpoints |
|--------|------|------|-------------------|
| **Indexing** | `indexing/` | Watch workspace → chunk → embed → pgvector | `POST /v1/context/index` |
| **Graph indexing** | `graph-indexing/` | Extract imports/symbols → graph upsert | `POST /v1/graph/upsert` |
| Document processing | `document-processing/` | Phase 2 parsers (scaffold) | — |

## Indexing worker

- Tracks jobs in `index_jobs` table (status, files_processed).
- Uses gateway embeddings API (not local hash stub).
- Watches `WATCH_PATH` (compose: repo mounted at `/workspace`).
- Env: `DATABASE_URL`, `GATEWAY_URL`, `PROJECT_ID`, `SCAN_INTERVAL`.

## Graph indexing worker

- Uses `graph_service.extractor` for regex MVP (files, classes, functions, imports).
- Posts nodes/edges to gateway per file.
- Build context: repo root (`dockerfile` at `workers/graph-indexing/Dockerfile`).

## Run individually

```bash
cd workers/indexing
pip install -r requirements.txt
GATEWAY_URL=http://127.0.0.1:8000 python worker.py
```

## Related

- [../backend/graph_service/](../backend/graph_service/)
- [../docs/ausome/ARCHITECTURE.md](../docs/ausome/ARCHITECTURE.md)
