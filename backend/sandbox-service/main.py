"""Per-workspace Docker sandbox for Ausome agent terminal commands."""

import asyncio
import subprocess
import uuid

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Ausome Sandbox Service", version="0.1.0")

SANDBOX_IMAGE = "alpine:3.20"
_containers: dict[str, str] = {}


class SandboxExecRequest(BaseModel):
    workspace_id: str
    command: str
    cwd: str | None = None


class SandboxCreateRequest(BaseModel):
    workspace_id: str


def _container_name(workspace_id: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in workspace_id)[:48]
    return f"ausome-sandbox-{safe}"


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ausome-sandbox"}


@app.post("/v1/sandbox/create")
async def sandbox_create(req: SandboxCreateRequest) -> dict:
    name = _container_name(req.workspace_id)
    if name in _containers.values():
        return {"workspace_id": req.workspace_id, "container": name, "status": "running"}

    container_id = str(uuid.uuid4())[:12]
    proc = await asyncio.create_subprocess_exec(
        "docker",
        "run",
        "-d",
        "--name",
        name,
        SANDBOX_IMAGE,
        "sleep",
        "infinity",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return {"workspace_id": req.workspace_id, "status": "error", "message": stderr.decode()}
    _containers[req.workspace_id] = name
    return {"workspace_id": req.workspace_id, "container": name, "container_id": container_id, "status": "created"}


@app.post("/v1/sandbox/exec")
async def sandbox_exec(req: SandboxExecRequest) -> dict:
    name = _container_name(req.workspace_id)
    if name not in _containers.values():
        await sandbox_create(SandboxCreateRequest(workspace_id=req.workspace_id))

    workdir = req.cwd or "/tmp"
    proc = await asyncio.create_subprocess_exec(
        "docker",
        "exec",
        "-w",
        workdir,
        name,
        "sh",
        "-lc",
        req.command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return {
        "workspace_id": req.workspace_id,
        "stdout": stdout.decode(errors="replace"),
        "stderr": stderr.decode(errors="replace"),
        "exit_code": proc.returncode or 0,
    }
