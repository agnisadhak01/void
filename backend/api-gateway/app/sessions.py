"""Chat session persistence."""

import json
from typing import Any

import asyncpg

from app.auth import AuthUser


async def upsert_session(
    conn: asyncpg.Connection,
    user: AuthUser,
    session_id: str | None,
    project_id: str | None,
    title: str | None,
    mode: str = "agent",
    external_thread_id: str | None = None,
) -> str:
    meta: dict[str, Any] = {}
    if external_thread_id:
        meta["pulse_thread_id"] = external_thread_id
    if session_id:
        row = await conn.fetchrow(
            """
            UPDATE chat_sessions
            SET title = COALESCE($2, title),
                mode = COALESCE($3, mode),
                project_id = COALESCE($4::uuid, project_id),
                updated_at = NOW()
            WHERE id = $1::uuid
            RETURNING id
            """,
            session_id,
            title,
            mode,
            project_id,
        )
        if row:
            return str(row["id"])
    row = await conn.fetchrow(
        """
        INSERT INTO chat_sessions (project_id, user_id, title, mode)
        VALUES ($1::uuid, $2::uuid, $3, $4)
        RETURNING id
        """,
        project_id,
        user.id if _is_uuid(user.id) else None,
        title or "Agent session",
        mode,
    )
    return str(row["id"])


async def get_session(conn: asyncpg.Connection, session_id: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT id, project_id, user_id, title, mode, created_at, updated_at FROM chat_sessions WHERE id = $1::uuid",
        session_id,
    )
    return dict(row) if row else None


def _is_uuid(value: str) -> bool:
    import uuid

    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
