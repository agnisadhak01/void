from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from agent_service.models import AgentRunRequest, ToolResultRequest
from agent_service.runtime import AgentRuntime
from app.auth import AuthUser, require_role

router = APIRouter(prefix="/v1/agent", tags=["agent"])

DevUser = Annotated[AuthUser, Depends(require_role("admin", "developer"))]


def _runtime(request: Request) -> AgentRuntime:
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return AgentRuntime(pool)


@router.post("/run")
async def agent_run(req: AgentRunRequest, user: DevUser, request: Request):
    try:
        return await _runtime(request).start_run(user, req)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs/{run_id}")
async def agent_status(run_id: str, user: DevUser, request: Request):
    try:
        return await _runtime(request).get_status(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/runs/{run_id}/tool-result")
async def agent_tool_result(run_id: str, body: ToolResultRequest, user: DevUser, request: Request):
    try:
        return await _runtime(request).submit_tool_result(user, run_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runs/{run_id}/cancel")
async def agent_cancel(run_id: str, user: DevUser, request: Request):
    return await _runtime(request).cancel_run(user, run_id)


@router.post("/runs/{run_id}/approve-plan")
async def agent_approve_plan(run_id: str, user: DevUser, request: Request):
    try:
        return await _runtime(request).approve_plan(user, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
