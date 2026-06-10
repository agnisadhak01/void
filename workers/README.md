# Ausome Workers

| Worker | Path | Role |
|--------|------|------|
| Indexing | `indexing/` | Watch workspace files → embeddings → pgvector |
| Document processing | `document-processing/` | Phase 2 document parsers |

Run via `deployment/docker-compose.yml` (`indexing-worker` service).
