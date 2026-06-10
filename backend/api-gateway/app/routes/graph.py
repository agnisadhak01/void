from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import AuthUser, require_role
from graph_service.extractor import scan_directory
from graph_service.store import query_neighbors, upsert_graph

router = APIRouter(prefix="/v1/graph", tags=["graph"])

DevUser = Annotated[AuthUser, Depends(require_role("admin", "developer"))]


class GraphUpsertRequest(BaseModel):
    project_id: str
    watch_path: str | None = None
    nodes: list[dict[str, Any]] | None = None
    edges: list[dict[str, Any]] | None = None


class GraphQueryRequest(BaseModel):
    project_id: str
    name: str
    limit: int = 20


@router.post("/upsert")
async def graph_upsert(req: GraphUpsertRequest, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    if req.nodes is not None:
        nodes, edges = req.nodes, req.edges or []
    elif req.watch_path:
        nodes, edges = scan_directory(Path(req.watch_path))
    else:
        raise HTTPException(status_code=400, detail="Provide nodes or watch_path")
    async with pool.acquire() as conn:
        stats = await upsert_graph(conn, req.project_id, nodes, edges)
    return {"project_id": req.project_id, **stats}


@router.post("/query")
async def graph_query(req: GraphQueryRequest, user: DevUser, request: Request):
    pool = request.app.state.db_pool
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    async with pool.acquire() as conn:
        results = await query_neighbors(conn, req.project_id, req.name, req.limit)
    return {"query": req.name, "results": results}
