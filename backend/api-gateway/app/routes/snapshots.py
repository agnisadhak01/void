import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth import AuthUser, require_role
from app.storage import get_object, put_object

router = APIRouter(prefix="/v1/snapshots", tags=["snapshots"])

DevUser = Annotated[AuthUser, Depends(require_role("admin", "developer"))]


class SnapshotCreateRequest(BaseModel):
    workspace_id: str
    project_id: str | None = None
    manifest: dict | None = None


@router.post("/create")
async def snapshot_create(req: SnapshotCreateRequest, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    snap_id = str(uuid.uuid4())
    key = f"snapshots/{req.workspace_id}/{snap_id}.json"
    payload = json.dumps(req.manifest or {"workspace_id": req.workspace_id, "note": "pre-agent snapshot"}).encode()
    put_object(key, payload, "application/json")
    if pool:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workspace_snapshots (id, workspace_id, project_id, object_key, size_bytes)
                VALUES ($1::uuid, $2, $3::uuid, $4, $5)
                """,
                snap_id,
                req.workspace_id,
                req.project_id,
                key,
                len(payload),
            )
    return {"snapshot_id": snap_id, "object_key": key}


@router.post("/{snapshot_id}/restore")
async def snapshot_restore(snapshot_id: str, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT object_key FROM workspace_snapshots WHERE id = $1::uuid",
            snapshot_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    data = get_object(row["object_key"])
    return {"snapshot_id": snapshot_id, "manifest": json.loads(data.decode())}
