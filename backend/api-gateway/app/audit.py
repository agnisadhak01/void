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


async def start_agent_run(conn: asyncpg.Connection, user: AuthUser, session_id: str | None = None) -> str:
    row = await conn.fetchrow(
        """
        INSERT INTO agent_runs (session_id, user_id, status)
        VALUES ($1::uuid, $2::uuid, 'running')
        RETURNING id
        """,
        session_id,
        user.id if _is_uuid(user.id) else None,
    )
    return str(row["id"])


def _is_uuid(value: str) -> bool:
    import uuid

    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
