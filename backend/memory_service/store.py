import json

import asyncpg


async def add_memory(
    conn: asyncpg.Connection,
    project_id: str,
    category: str,
    fact: str,
    source_run_id: str | None = None,
    confidence: float = 1.0,
) -> str:
    row = await conn.fetchrow(
        """
        INSERT INTO project_memories (project_id, category, fact, source_run_id, confidence)
        VALUES ($1::uuid, $2, $3, $4::uuid, $5)
        RETURNING id
        """,
        project_id,
        category,
        fact,
        source_run_id,
        confidence,
    )
    return str(row["id"])


async def recall_memories(conn: asyncpg.Connection, project_id: str, limit: int = 10) -> list[str]:
    rows = await conn.fetch(
        """
        SELECT fact FROM project_memories
        WHERE project_id = $1::uuid
        ORDER BY created_at DESC
        LIMIT $2
        """,
        project_id,
        limit,
    )
    return [r["fact"] for r in rows]


async def extract_memories_from_run(goal: str, plan: dict | None, success: bool) -> list[tuple[str, str]]:
    """Heuristic memory extraction post-run."""
    out: list[tuple[str, str]] = []
    if goal:
        out.append(("architecture", f"User goal addressed: {goal[:500]}"))
    if plan and plan.get("dependencies"):
        for d in plan["dependencies"][:5]:
            out.append(("dependency", str(d)))
    if success:
        out.append(("convention", "Agent run completed successfully with evaluation gates"))
    return out
