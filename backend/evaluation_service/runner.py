import uuid
from typing import Any

import asyncpg

from app.sandbox import run_in_sandbox

DEFAULT_CHECKS = [
    {"name": "pytest", "command": "pytest -q"},
    {"name": "npm_test", "command": "npm test --if-present"},
    {"name": "eslint", "command": "npx eslint . --max-warnings 0"},
    {"name": "ruff", "command": "ruff check ."},
]


async def start_eval_run(
    conn: asyncpg.Connection,
    project_id: str | None,
    agent_run_id: str | None,
    workspace_id: str,
    checks: list[dict] | None = None,
) -> str:
    check_list = checks or DEFAULT_CHECKS
    row = await conn.fetchrow(
        """
        INSERT INTO eval_runs (project_id, agent_run_id, status, checks)
        VALUES ($1::uuid, $2::uuid, 'running', $3::jsonb)
        RETURNING id
        """,
        project_id,
        agent_run_id,
        __import__("json").dumps(check_list),
    )
    run_id = str(row["id"])
    results: list[dict[str, Any]] = []
    passed = True
    for check in check_list:
        name = check.get("name", "check")
        cmd = check["command"]
        out = await run_in_sandbox(workspace_id, cmd, None)
        exit_code = out.get("exit_code", 1)
        if isinstance(exit_code, int) and exit_code != 0:
            passed = False
        results.append({"name": name, "command": cmd, "output": out, "passed": exit_code == 0 if isinstance(exit_code, int) else False})

    import json

    await conn.execute(
        """
        UPDATE eval_runs SET status = 'completed', results = $2::jsonb, passed = $3, completed_at = NOW()
        WHERE id = $1::uuid
        """,
        run_id,
        json.dumps(results),
        passed,
    )
    return run_id


async def get_eval_run(conn: asyncpg.Connection, eval_id: str) -> dict | None:
    row = await conn.fetchrow("SELECT * FROM eval_runs WHERE id = $1::uuid", eval_id)
    return dict(row) if row else None
