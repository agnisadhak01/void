"""M16 App Builder — scaffold templates (Phase 3 foundation)."""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import AuthUser, require_role

router = APIRouter(prefix="/v1/app-builder", tags=["app-builder"])

DevUser = Annotated[AuthUser, Depends(require_role("admin", "developer"))]

TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "crm-saas",
        "description": "CRM with React frontend, FastAPI backend, Postgres",
        "stack": {"frontend": "react", "backend": "fastapi", "db": "postgres"},
        "scaffold": {
            "tasks": ["Init monorepo", "Auth JWT", "Contacts API", "Dashboard UI", "Docker compose"],
            "helm": True,
        },
    },
    {
        "name": "api-starter",
        "description": "FastAPI + Postgres REST API",
        "stack": {"backend": "fastapi", "db": "postgres"},
        "scaffold": {"tasks": ["OpenAPI", "CRUD", "Migrations", "Tests"]},
    },
]


class ScaffoldRequest(BaseModel):
    template_name: str
    project_name: str
    goal: str | None = None


@router.get("/templates")
async def list_templates(user: DevUser):
    return {"templates": TEMPLATES}


@router.post("/scaffold")
async def scaffold(req: ScaffoldRequest, user: DevUser, request: Request):
    tpl = next((t for t in TEMPLATES if t["name"] == req.template_name), None)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    pool = request.app.state.db_pool
    if pool:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO app_builder_templates (name, description, stack, scaffold)
                VALUES ($1, $2, $3::jsonb, $4::jsonb)
                ON CONFLICT (name) DO NOTHING
                """,
                tpl["name"],
                tpl["description"],
                json.dumps(tpl["stack"]),
                json.dumps(tpl["scaffold"]),
            )
    return {
        "template": tpl["name"],
        "project_name": req.project_name,
        "plan": {
            "tasks": tpl["scaffold"].get("tasks", []),
            "goal": req.goal or f"Build {req.project_name} from {tpl['name']} template",
        },
        "next": "POST /v1/agent/run with returned plan goal",
    }
