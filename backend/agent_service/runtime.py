"""Hybrid agent runtime state machine."""

import json
import uuid
from typing import Any

import asyncpg

from agent_service.models import AgentPhase, AgentRunRequest, AgentRunResponse, RunStatus, ToolResultRequest
from agent_service.phases import next_phase, phase_status_after_plan, status_for_phase
from app.audit import add_run_step, end_agent_run, get_agent_run, list_run_steps, log_audit, start_agent_run, update_agent_run
from app.auth import AuthUser
from app.config import settings
from app.sessions import upsert_session
from app.storage import put_object
from evaluation_service.gates import eval_passed
from evaluation_service.runner import get_eval_run, start_eval_run
from memory_service.store import add_memory, extract_memories_from_run, recall_memories
from planner_service.planner import generate_plan


class AgentRuntime:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def start_run(self, user: AuthUser, req: AgentRunRequest) -> AgentRunResponse:
        async with self.pool.acquire() as conn:
            session_id = await upsert_session(
                conn,
                user,
                req.session_id,
                req.project_id,
                req.goal[:120],
                "agent",
                req.pulse_thread_id,
            )
            run_id = await start_agent_run(
                conn, user, session_id, goal=req.goal, project_id=req.project_id, status=RunStatus.planning.value
            )
            await log_audit(conn, user, "agent.run.start", req.goal[:200], {"run_id": run_id}, agent_run_id=run_id)
            await update_agent_run(conn, run_id, phase=AgentPhase.plan.value)

            memories = await recall_memories(conn, req.project_id)
            plan = await generate_plan(req.goal, memories)
            plan_dict = plan.model_dump()
            await add_run_step(conn, run_id, 0, "plan", plan_dict, phase=AgentPhase.plan.value)
            await update_agent_run(conn, run_id, plan=plan_dict)

            require_approval = req.require_plan_approval
            if require_approval is None:
                require_approval = settings.require_plan_approval
            status = phase_status_after_plan(require_approval)
            await update_agent_run(conn, run_id, status=status.value, phase=AgentPhase.code.value)

            if status == RunStatus.awaiting_approval:
                return AgentRunResponse(
                    run_id=run_id,
                    status=status.value,
                    phase=AgentPhase.plan.value,
                    plan=plan_dict,
                    message="Plan ready for approval",
                )

            snap_id = await self._create_snapshot(conn, run_id, req.project_id)
            return await self._begin_execution(conn, user, run_id, req, plan_dict, snap_id)

    async def approve_plan(self, user: AuthUser, run_id: str) -> AgentRunResponse:
        async with self.pool.acquire() as conn:
            run = await get_agent_run(conn, run_id)
            if not run:
                raise ValueError("Run not found")
            if run["status"] != RunStatus.awaiting_approval.value:
                raise ValueError(f"Run not awaiting approval: {run['status']}")
            await update_agent_run(conn, run_id, status=RunStatus.executing.value, phase=AgentPhase.code.value)
            await log_audit(conn, user, "agent.plan.approved", run_id, {}, agent_run_id=run_id)
            req = AgentRunRequest(goal=run["goal"] or "", project_id=str(run["project_id"] or settings.default_project_id))
            snap_id = run.get("snapshot_id") or await self._create_snapshot(conn, run_id, str(run.get("project_id") or settings.default_project_id))
            return await self._begin_execution(conn, user, run_id, req, run.get("plan") or {}, snap_id)

    async def _create_snapshot(self, conn: asyncpg.Connection, run_id: str, project_id: str) -> str:
        snap_id = str(uuid.uuid4())
        workspace_id = "default"
        key = f"snapshots/{workspace_id}/{snap_id}.json"
        payload = json.dumps({"run_id": run_id, "project_id": project_id, "pre_agent": True}).encode()
        put_object(key, payload, "application/json")
        await conn.execute(
            """
            INSERT INTO workspace_snapshots (id, workspace_id, project_id, object_key, size_bytes)
            VALUES ($1::uuid, $2, $3::uuid, $4, $5)
            """,
            snap_id,
            workspace_id,
            project_id,
            key,
            len(payload),
        )
        await update_agent_run(conn, run_id, snapshot_id=snap_id)
        return snap_id

    async def _begin_execution(
        self,
        conn: asyncpg.Connection,
        user: AuthUser,
        run_id: str,
        req: AgentRunRequest,
        plan: dict,
        snapshot_id: str | None = None,
    ) -> AgentRunResponse:
        pending = {
            "tool_name": "semantic_search",
            "arguments": {"query": req.goal, "limit": 5},
            "tool_call_id": str(uuid.uuid4()),
            "phase": AgentPhase.code.value,
        }
        step_idx = await self._next_step_index(conn, run_id)
        await add_run_step(conn, run_id, step_idx, "tool_request", pending, phase=AgentPhase.code.value)
        await update_agent_run(conn, run_id, status=RunStatus.executing.value, pending_tool=pending)
        return AgentRunResponse(
            run_id=run_id,
            status=RunStatus.executing.value,
            phase=AgentPhase.code.value,
            plan=plan,
            pending_tool=pending,
            message=f"Snapshot {snapshot_id} created — execute pending tool locally and submit tool-result",
        )

    async def submit_tool_result(self, user: AuthUser, run_id: str, body: ToolResultRequest) -> AgentRunResponse:
        async with self.pool.acquire() as conn:
            run = await get_agent_run(conn, run_id)
            if not run:
                raise ValueError("Run not found")
            if run["status"] in (RunStatus.completed.value, RunStatus.cancelled.value, RunStatus.failed.value):
                raise ValueError("Run already finished")

            step_idx = await self._next_step_index(conn, run_id)
            await add_run_step(
                conn,
                run_id,
                step_idx,
                "tool_result",
                {"tool_name": body.tool_name, "result": body.result[:8000], "success": body.success},
                phase=run.get("phase"),
            )
            await log_audit(
                conn,
                user,
                f"agent.tool.result.{body.tool_name}",
                body.tool_name,
                {"success": body.success},
                agent_run_id=run_id,
            )
            await update_agent_run(conn, run_id, pending_tool=None)

            phase = run.get("phase") or AgentPhase.code.value
            if phase == AgentPhase.code.value:
                await update_agent_run(conn, run_id, phase=AgentPhase.review.value, status=RunStatus.executing.value)
                review_step = {
                    "tool_name": "read_lint_errors",
                    "arguments": {},
                    "tool_call_id": str(uuid.uuid4()),
                    "phase": AgentPhase.review.value,
                }
                await add_run_step(conn, run_id, step_idx + 1, "tool_request", review_step, phase=AgentPhase.review.value)
                await update_agent_run(conn, run_id, pending_tool=review_step)
                return AgentRunResponse(
                    run_id=run_id,
                    status=RunStatus.executing.value,
                    phase=AgentPhase.review.value,
                    pending_tool=review_step,
                    plan=run.get("plan"),
                )

            if phase == AgentPhase.review.value:
                await update_agent_run(conn, run_id, phase=AgentPhase.test.value, status=RunStatus.verifying.value)
                workspace_id = "default"
                eval_id = await start_eval_run(conn, str(run.get("project_id") or settings.default_project_id), run_id, workspace_id)
                eval_row = await get_eval_run(conn, eval_id)
                passed = eval_passed(eval_row, admin_override=user.role == "admin")
                await add_run_step(conn, run_id, step_idx + 1, "verify", {"eval_id": eval_id, "passed": passed}, phase=AgentPhase.test.value)

                if passed:
                    await end_agent_run(conn, run_id, RunStatus.completed.value)
                    for cat, fact in extract_memories_from_run(run.get("goal") or "", run.get("plan"), True):
                        await add_memory(conn, str(run.get("project_id") or settings.default_project_id), cat, fact, run_id)
                    await log_audit(conn, user, "agent.run.completed", run_id, {"eval_id": eval_id}, agent_run_id=run_id)
                    return AgentRunResponse(
                        run_id=run_id,
                        status=RunStatus.completed.value,
                        phase=AgentPhase.test.value,
                        message="Agent run completed — evaluation passed",
                        plan=run.get("plan"),
                    )

                await end_agent_run(conn, run_id, RunStatus.failed.value)
                return AgentRunResponse(
                    run_id=run_id,
                    status=RunStatus.failed.value,
                    phase=AgentPhase.test.value,
                    message="Evaluation failed — run blocked",
                    plan=run.get("plan"),
                )

            nxt = next_phase(phase)
            if nxt:
                await update_agent_run(conn, run_id, phase=nxt, status=status_for_phase(nxt).value)
            return await self.get_status(run_id)

    async def cancel_run(self, user: AuthUser, run_id: str) -> AgentRunResponse:
        async with self.pool.acquire() as conn:
            await end_agent_run(conn, run_id, RunStatus.cancelled.value)
            await log_audit(conn, user, "agent.run.cancelled", run_id, {}, agent_run_id=run_id)
            return AgentRunResponse(run_id=run_id, status=RunStatus.cancelled.value, message="Cancelled")

    async def get_status(self, run_id: str) -> AgentRunResponse:
        async with self.pool.acquire() as conn:
            run = await get_agent_run(conn, run_id)
            if not run:
                raise ValueError("Run not found")
            steps = await list_run_steps(conn, run_id)
            return AgentRunResponse(
                run_id=run_id,
                status=run["status"],
                phase=run.get("phase"),
                plan=run.get("plan"),
                pending_tool=run.get("pending_tool"),
                steps=steps,
            )

    async def _next_step_index(self, conn: asyncpg.Connection, run_id: str) -> int:
        row = await conn.fetchrow(
            "SELECT COALESCE(MAX(step_index), -1) + 1 AS idx FROM agent_run_steps WHERE run_id = $1::uuid",
            run_id,
        )
        return int(row["idx"])
