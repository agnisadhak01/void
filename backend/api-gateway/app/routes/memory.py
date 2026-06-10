from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import AuthUser, require_role
from memory_service.store import add_memory, recall_memories

router = APIRouter(prefix="/v1/memory", tags=["memory"])

DevUser = Annotated[AuthUser, Depends(require_role("admin", "developer"))]


class MemoryAddRequest(BaseModel):
    project_id: str
    category: str
    fact: str
    source_run_id: str | None = None


class MemoryRecallRequest(BaseModel):
    project_id: str
    limit: int = 10


@router.post("/add")
async def memory_add(req: MemoryAddRequest, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        mid = await add_memory(conn, req.project_id, req.category, req.fact, req.source_run_id)
    return {"id": mid}


@router.post("/recall")
async def memory_recall(req: MemoryRecallRequest, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        facts = await recall_memories(conn, req.project_id, req.limit)
    return {"facts": facts}
