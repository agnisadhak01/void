from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import AuthUser, require_role
from observability_service.trace import build_run_trace, list_agent_runs, observability_summary

router = APIRouter(prefix="/v1", tags=["observability"])

ViewerUser = Annotated[AuthUser, Depends(require_role("admin", "developer", "viewer"))]


@router.get("/agent/runs")
async def list_runs(
    user: ViewerUser,
    request: Request,
    project_id: str | None = None,
    pulse_thread_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        runs = await list_agent_runs(
            conn,
            project_id=project_id,
            pulse_thread_id=pulse_thread_id,
            status=status,
            limit=limit,
        )
    return {"runs": runs}


@router.get("/agent/runs/{run_id}/trace")
async def get_run_trace(run_id: str, user: ViewerUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        trace = await build_run_trace(conn, run_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Run not found")
    return trace


@router.get("/observability/summary")
async def get_summary(
    user: ViewerUser,
    request: Request,
    project_id: str | None = None,
):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        return await observability_summary(conn, project_id)
