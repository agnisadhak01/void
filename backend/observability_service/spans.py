"""Trace span persistence."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import asyncpg

from observability_service.usage import estimate_cost


async def ensure_prompt_version(conn: asyncpg.Connection, template_id: str, content: str) -> str:
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
    row = await conn.fetchrow(
        """
        INSERT INTO prompt_versions (template_id, content_hash)
        VALUES ($1, $2)
        ON CONFLICT (template_id, content_hash) DO UPDATE SET template_id = EXCLUDED.template_id
        RETURNING id
        """,
        template_id,
        content_hash,
    )
    return str(row["id"])


async def record_span(
    conn: asyncpg.Connection,
    run_id: str,
    span_type: str,
    name: str,
    *,
    phase: str | None = None,
    status: str = "ok",
    payload: dict[str, Any] | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    latency_ms: int | None = None,
    prompt_version_id: str | None = None,
) -> str:
    span_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO agent_trace_spans (
            id, run_id, span_type, phase, name, started_at, ended_at, latency_ms, status, payload, prompt_version_id
        )
        VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::uuid)
        """,
        span_id,
        run_id,
        span_type,
        phase,
        name,
        started_at or datetime.now(timezone.utc),
        ended_at,
        latency_ms,
        status,
        json.dumps(payload or {}),
        prompt_version_id,
    )
    return span_id


async def record_llm_usage(
    conn: asyncpg.Connection,
    span_id: str,
    run_id: str | None,
    model: str,
    route: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    total = prompt_tokens + completion_tokens
    cost = estimate_cost(model, total)
    await conn.execute(
        """
        INSERT INTO llm_usage (span_id, run_id, model, route, prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd)
        VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8)
        """,
        span_id,
        run_id,
        model,
        route,
        prompt_tokens,
        completion_tokens,
        total,
        cost,
    )


class SpanTimer:
    """Context helper for timed spans."""

    def __init__(
        self,
        conn: asyncpg.Connection,
        run_id: str,
        span_type: str,
        name: str,
        phase: str | None = None,
        payload: dict[str, Any] | None = None,
    ):
        self.conn = conn
        self.run_id = run_id
        self.span_type = span_type
        self.name = name
        self.phase = phase
        self.payload = payload or {}
        self.span_id: str | None = None
        self._start: datetime | None = None

    async def __aenter__(self) -> "SpanTimer":
        self._start = datetime.now(timezone.utc)
        self.span_id = await record_span(
            self.conn,
            self.run_id,
            self.span_type,
            self.name,
            phase=self.phase,
            status="running",
            payload=self.payload,
            started_at=self._start,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if not self.span_id or not self._start:
            return
        end = datetime.now(timezone.utc)
        latency = int((end - self._start).total_seconds() * 1000)
        status = "error" if exc else "ok"
        await self.conn.execute(
            """
            UPDATE agent_trace_spans
            SET ended_at = $2, latency_ms = $3, status = $4
            WHERE id = $1::uuid
            """,
            self.span_id,
            end,
            latency,
            status,
        )
