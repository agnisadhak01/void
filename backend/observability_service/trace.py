"""Build full agent run trace for observability API."""

from typing import Any

import asyncpg

from app.audit import get_agent_run, list_run_steps


async def list_agent_runs(
    conn: asyncpg.Connection,
    *,
    project_id: str | None = None,
    pulse_thread_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    clauses = ["1=1"]
    args: list[Any] = []
    n = 1
    if project_id:
        clauses.append(f"project_id = ${n}::uuid")
        args.append(project_id)
        n += 1
    if pulse_thread_id:
        clauses.append(f"pulse_thread_id = ${n}")
        args.append(pulse_thread_id)
        n += 1
    if status:
        clauses.append(f"status = ${n}")
        args.append(status)
        n += 1
    args.append(min(limit, 200))
    rows = await conn.fetch(
        f"""
        SELECT id, status, goal, project_id, phase, pulse_thread_id, started_at, ended_at
        FROM agent_runs
        WHERE {' AND '.join(clauses)}
        ORDER BY started_at DESC
        LIMIT ${n}
        """,
        *args,
    )
    return [dict(r) for r in rows]


async def _list_spans(conn: asyncpg.Connection, run_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT id, span_type, phase, name, started_at, ended_at, latency_ms, status, payload
        FROM agent_trace_spans
        WHERE run_id = $1::uuid
        ORDER BY started_at
        """,
        run_id,
    )
    out = []
    for r in rows:
        d = dict(r)
        if d.get("payload") and isinstance(d["payload"], str):
            import json

            d["payload"] = json.loads(d["payload"])
        out.append(d)
    return out


async def _usage_summary(conn: asyncpg.Connection, run_id: str) -> dict:
    row = await conn.fetchrow(
        """
        SELECT
            COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
            COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
            COALESCE(SUM(total_tokens), 0) AS total_tokens,
            COALESCE(SUM(estimated_cost_usd), 0) AS estimated_cost_usd
        FROM llm_usage WHERE run_id = $1::uuid
        """,
        run_id,
    )
    by_model = await conn.fetch(
        """
        SELECT model, SUM(total_tokens) AS tokens, SUM(estimated_cost_usd) AS cost
        FROM llm_usage WHERE run_id = $1::uuid
        GROUP BY model
        """,
        run_id,
    )
    return {
        **dict(row),
        "by_model": [dict(m) for m in by_model],
    }


async def build_run_trace(conn: asyncpg.Connection, run_id: str) -> dict | None:
    run = await get_agent_run(conn, run_id)
    if not run:
        return None
    steps = await list_run_steps(conn, run_id)
    spans = await _list_spans(conn, run_id)
    usage = await _usage_summary(conn, run_id)

    eval_rows = await conn.fetch(
        "SELECT id, status, passed, results, created_at, completed_at FROM eval_runs WHERE agent_run_id = $1::uuid",
        run_id,
    )
    snapshot = None
    if run.get("snapshot_id"):
        snap = await conn.fetchrow(
            "SELECT id, workspace_id, object_key, size_bytes, created_at FROM workspace_snapshots WHERE id = $1::uuid",
            str(run["snapshot_id"]),
        )
        snapshot = dict(snap) if snap else None

    memories = await conn.fetch(
        "SELECT category, fact, confidence, created_at FROM project_memories WHERE source_run_id = $1::uuid",
        run_id,
    )

    duration_ms = None
    if run.get("started_at") and run.get("ended_at"):
        duration_ms = int((run["ended_at"] - run["started_at"]).total_seconds() * 1000)

    return {
        "run": run,
        "steps": steps,
        "spans": spans,
        "usage": usage,
        "eval_runs": [dict(e) for e in eval_rows],
        "snapshot": snapshot,
        "memories_written": [dict(m) for m in memories],
        "duration_ms": duration_ms,
    }


async def observability_summary(conn: asyncpg.Connection, project_id: str | None = None) -> dict:
    pid_filter = "AND project_id = $1::uuid" if project_id else ""
    args = [project_id] if project_id else []

    totals = await conn.fetchrow(
        f"""
        SELECT
            COUNT(*) AS total_runs,
            COUNT(*) FILTER (WHERE status = 'completed') AS completed,
            COUNT(*) FILTER (WHERE status = 'failed') AS failed,
            COUNT(*) FILTER (WHERE started_at > NOW() - INTERVAL '24 hours') AS runs_24h
        FROM agent_runs
        WHERE 1=1 {pid_filter}
        """,
        *args,
    )

    latency = await conn.fetchrow(
        f"""
        SELECT AVG(latency_ms)::int AS avg_span_latency_ms
        FROM agent_trace_spans s
        JOIN agent_runs r ON r.id = s.run_id
        WHERE s.latency_ms IS NOT NULL {pid_filter.replace('project_id', 'r.project_id')}
        """,
        *args,
    )

    token_row = await conn.fetchrow(
        f"""
        SELECT COALESCE(SUM(u.total_tokens), 0) AS total_tokens,
               COALESCE(SUM(u.estimated_cost_usd), 0) AS total_cost_usd
        FROM llm_usage u
        JOIN agent_runs r ON r.id = u.run_id
        WHERE 1=1 {pid_filter.replace('project_id', 'r.project_id')}
        """,
        *args,
    )

    pass_rate = 0.0
    if totals and totals["total_runs"]:
        pass_rate = round((totals["completed"] or 0) / totals["total_runs"], 3)

    return {
        "total_runs": totals["total_runs"] if totals else 0,
        "completed": totals["completed"] if totals else 0,
        "failed": totals["failed"] if totals else 0,
        "runs_24h": totals["runs_24h"] if totals else 0,
        "pass_rate": pass_rate,
        "avg_span_latency_ms": latency["avg_span_latency_ms"] if latency else None,
        "total_tokens": float(token_row["total_tokens"]) if token_row else 0,
        "total_cost_usd": float(token_row["total_cost_usd"]) if token_row else 0,
    }
