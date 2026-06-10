import json
from typing import Any

import asyncpg

from app.auth import AuthUser


async def log_audit(
    conn: asyncpg.Connection,
    user: AuthUser,
    action_type: str,
    resource: str | None = None,
    payload: dict[str, Any] | None = None,
    agent_run_id: str | None = None,
) -> None:
    await conn.execute(
        """
        INSERT INTO audit_logs (user_id, agent_run_id, action_type, resource, payload)
        VALUES ($1::uuid, $2::uuid, $3, $4, $5::jsonb)
        """,
        user.id if _is_uuid(user.id) else None,
        agent_run_id,
        action_type,
        resource,
        json.dumps(payload or {}),
    )


async def start_agent_run(
    conn: asyncpg.Connection,
    user: AuthUser,
    session_id: str | None = None,
    *,
    goal: str | None = None,
    project_id: str | None = None,
    status: str = "queued",
) -> str:
    row = await conn.fetchrow(
        """
        INSERT INTO agent_runs (session_id, user_id, status, goal, project_id)
        VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid)
        RETURNING id
        """,
        session_id,
        user.id if _is_uuid(user.id) else None,
        status,
        goal,
        project_id,
    )
    return str(row["id"])


async def update_agent_run(
    conn: asyncpg.Connection,
    run_id: str,
    *,
    status: str | None = None,
    phase: str | None = None,
    plan: dict | None = None,
    pending_tool: dict | None = None,
    snapshot_id: str | None = None,
) -> None:
    await conn.execute(
        """
        UPDATE agent_runs SET
            status = COALESCE($2, status),
            phase = COALESCE($3, phase),
            plan = COALESCE($4::jsonb, plan),
            pending_tool = $5::jsonb,
            snapshot_id = COALESCE($6::uuid, snapshot_id)
        WHERE id = $1::uuid
        """,
        run_id,
        status,
        phase,
        json.dumps(plan) if plan is not None else None,
        json.dumps(pending_tool) if pending_tool is not None else None,
        snapshot_id,
    )


async def end_agent_run(conn: asyncpg.Connection, run_id: str, status: str) -> None:
    await conn.execute(
        """
        UPDATE agent_runs SET status = $2, ended_at = NOW(), pending_tool = NULL
        WHERE id = $1::uuid
        """,
        run_id,
        status,
    )


async def add_run_step(
    conn: asyncpg.Connection,
    run_id: str,
    step_index: int,
    step_type: str,
    payload: dict | None = None,
    phase: str | None = None,
) -> str:
    row = await conn.fetchrow(
        """
        INSERT INTO agent_run_steps (run_id, step_index, step_type, phase, payload)
        VALUES ($1::uuid, $2, $3, $4, $5::jsonb)
        RETURNING id
        """,
        run_id,
        step_index,
        step_type,
        phase,
        json.dumps(payload or {}),
    )
    return str(row["id"])


async def get_agent_run(conn: asyncpg.Connection, run_id: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, session_id, user_id, status, goal, project_id, phase, plan, pending_tool,
               snapshot_id, started_at, ended_at
        FROM agent_runs WHERE id = $1::uuid
        """,
        run_id,
    )
    if not row:
        return None
    d = dict(row)
    for k in ("plan", "pending_tool"):
        if d.get(k) and isinstance(d[k], str):
            d[k] = json.loads(d[k])
    return d


async def list_run_steps(conn: asyncpg.Connection, run_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT step_index, step_type, phase, payload, created_at
        FROM agent_run_steps WHERE run_id = $1::uuid ORDER BY step_index
        """,
        run_id,
    )
    out = []
    for r in rows:
        d = dict(r)
        if d.get("payload") and isinstance(d["payload"], str):
            d["payload"] = json.loads(d["payload"])
        out.append(d)
    return out


def _is_uuid(value: str) -> bool:
    import uuid

    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
