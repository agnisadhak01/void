import json
from typing import Any

import asyncpg


async def upsert_graph(
    conn: asyncpg.Connection,
    project_id: str,
    nodes: list[dict],
    edges: list[dict],
) -> dict[str, int]:
    node_ids: dict[tuple, str] = {}
    n_count = 0
    for n in nodes:
        row = await conn.fetchrow(
            """
            INSERT INTO graph_nodes (project_id, node_type, name, path, metadata)
            VALUES ($1::uuid, $2, $3, $4, $5::jsonb)
            ON CONFLICT (project_id, node_type, name, path) DO UPDATE SET metadata = EXCLUDED.metadata
            RETURNING id
            """,
            project_id,
            n["node_type"],
            n["name"],
            n.get("path"),
            json.dumps(n.get("metadata") or {}),
        )
        key = (n["node_type"], n["name"], n.get("path"))
        node_ids[key] = str(row["id"])
        n_count += 1

    e_count = 0
    for e in edges:
        src_path = e.get("source_path", "")
        src_key = ("file", Path_name(src_path), src_path) if src_path else None
        src_id = node_ids.get(src_key) if src_key else None
        if not src_id:
            continue
        tgt_row = await conn.fetchrow(
            """
            SELECT id FROM graph_nodes
            WHERE project_id = $1::uuid AND name = $2 LIMIT 1
            """,
            project_id,
            e.get("target_name", ""),
        )
        if not tgt_row:
            tgt = await conn.fetchrow(
                """
                INSERT INTO graph_nodes (project_id, node_type, name, path, metadata)
                VALUES ($1::uuid, 'module', $2, NULL, '{}'::jsonb)
                ON CONFLICT (project_id, node_type, name, path) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """,
                project_id,
                e.get("target_name", "unknown"),
            )
            tgt_id = str(tgt["id"])
        else:
            tgt_id = str(tgt_row["id"])
        await conn.execute(
            """
            INSERT INTO graph_edges (project_id, source_id, target_id, edge_type)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4)
            ON CONFLICT (project_id, source_id, target_id, edge_type) DO NOTHING
            """,
            project_id,
            src_id,
            tgt_id,
            e["edge_type"],
        )
        e_count += 1
    return {"nodes": n_count, "edges": e_count}


def Path_name(p: str) -> str:
    return p.split("/")[-1] if p else ""


async def query_neighbors(conn: asyncpg.Connection, project_id: str, name: str, limit: int = 20) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT gn.name, gn.node_type, gn.path, ge.edge_type
        FROM graph_nodes gn
        JOIN graph_edges ge ON ge.target_id = gn.id OR ge.source_id = gn.id
        WHERE gn.project_id = $1::uuid AND gn.name ILIKE $2
        LIMIT $3
        """,
        project_id,
        f"%{name}%",
        limit,
    )
    return [dict(r) for r in rows]
