import hashlib
import json
from typing import Any

import asyncpg

from app.config import settings


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(float(x)) for x in vec) + "]"


async def ensure_project(conn: asyncpg.Connection, project_id: str) -> None:
    row = await conn.fetchrow("SELECT id FROM projects WHERE id = $1::uuid", project_id)
    if row:
        return
    await conn.execute(
        """
        INSERT INTO projects (id, workspace_id, name, root_uri)
        VALUES ($1::uuid, $1::uuid, 'default', '/')
        ON CONFLICT DO NOTHING
        """,
        project_id,
    )
    await conn.execute(
        """
        INSERT INTO workspaces (id, owner_id, name)
        VALUES ($1::uuid, '00000000-0000-0000-0000-000000000099'::uuid, 'default')
        ON CONFLICT DO NOTHING
        """,
        project_id,
    )


async def upsert_file_chunks(
    conn: asyncpg.Connection,
    project_id: str,
    path: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> int:
    await ensure_project(conn, project_id)
    content_hash = _hash_text("".join(chunks))
    file_row = await conn.fetchrow(
        """
        INSERT INTO files (project_id, path, content_hash)
        VALUES ($1::uuid, $2, $3)
        ON CONFLICT (project_id, path) DO UPDATE SET content_hash = EXCLUDED.content_hash, updated_at = NOW()
        RETURNING id
        """,
        project_id,
        path,
        content_hash,
    )
    file_id = file_row["id"]
    await conn.execute("DELETE FROM embeddings WHERE file_id = $1", file_id)
    count = 0
    for i, (chunk, vec) in enumerate(zip(chunks, embeddings)):
        await conn.execute(
            """
            INSERT INTO embeddings (file_id, chunk_index, chunk_text, chunk_hash, embedding)
            VALUES ($1, $2, $3, $4, $5)
            """,
            file_id,
            i,
            chunk,
            _hash_text(chunk),
            _vec_literal(vec),
        )
        count += 1
    return count


async def semantic_search(
    conn: asyncpg.Connection,
    project_id: str,
    query: str,
    query_embedding: list[float],
    limit: int = 10,
) -> list[dict[str, Any]]:
    await ensure_project(conn, project_id)
    vec_literal = _vec_literal(query_embedding)
    rows = await conn.fetch(
        """
        SELECT f.path, e.chunk_text, e.chunk_index,
               1 - (e.embedding <=> $2::vector) AS score
        FROM embeddings e
        JOIN files f ON f.id = e.file_id
        WHERE f.project_id = $1::uuid
        ORDER BY e.embedding <=> $2::vector
        LIMIT $3
        """,
        project_id,
        vec_literal,
        limit,
    )
    # Keyword boost via FTS-style ILIKE
    keyword_rows = await conn.fetch(
        """
        SELECT f.path, e.chunk_text, e.chunk_index, 0.5 AS score
        FROM embeddings e
        JOIN files f ON f.id = e.file_id
        WHERE f.project_id = $1::uuid AND e.chunk_text ILIKE $2
        LIMIT $3
        """,
        project_id,
        f"%{query[:200]}%",
        limit,
    )
    seen: set[tuple[str, int]] = set()
    results: list[dict[str, Any]] = []
    for row in list(rows) + list(keyword_rows):
        key = (row["path"], row["chunk_index"])
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "path": row["path"],
                "chunk": row["chunk_text"],
                "chunk_index": row["chunk_index"],
                "score": float(row["score"]),
            }
        )
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


async def get_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
