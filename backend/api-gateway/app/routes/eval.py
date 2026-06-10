from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import AuthUser, require_role
from evaluation_service.runner import get_eval_run, start_eval_run

router = APIRouter(prefix="/v1/eval", tags=["eval"])

DevUser = Annotated[AuthUser, Depends(require_role("admin", "developer"))]


class EvalRunRequest(BaseModel):
    project_id: str | None = None
    agent_run_id: str | None = None
    workspace_id: str = "default"
    checks: list[dict[str, Any]] | None = None


@router.post("/run")
async def eval_run(req: EvalRunRequest, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        eval_id = await start_eval_run(conn, req.project_id, req.agent_run_id, req.workspace_id, req.checks)
        row = await get_eval_run(conn, eval_id)
    return {"eval_id": eval_id, **(row or {})}


@router.get("/runs/{eval_id}")
async def eval_status(eval_id: str, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        row = await get_eval_run(conn, eval_id)
    if not row:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return row
