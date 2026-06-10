from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth import AuthUser, require_role
from app.sessions import get_session, upsert_session

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])

DevUser = Annotated[AuthUser, Depends(require_role("admin", "developer", "viewer"))]


class SessionUpsertRequest(BaseModel):
    session_id: str | None = None
    project_id: str | None = None
    title: str | None = None
    mode: str = "agent"
    pulse_thread_id: str | None = None


@router.post("/upsert")
async def session_upsert(req: SessionUpsertRequest, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        sid = await upsert_session(
            conn, user, req.session_id, req.project_id, req.title, req.mode, req.pulse_thread_id
        )
        row = await get_session(conn, sid)
    return row


@router.get("/{session_id}")
async def session_get(session_id: str, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        row = await get_session(conn, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return row
