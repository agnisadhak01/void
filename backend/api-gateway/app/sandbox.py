"""Docker sandbox runtime for agent terminal commands."""

import httpx

from app.config import settings


async def run_in_sandbox(workspace_id: str, command: str, cwd: str | None = None) -> dict:
    if not settings.ausome_sandbox_enabled:
        return {
            "sandboxed": False,
            "message": "Sandbox disabled; commands run on host in dev mode.",
            "command": command,
        }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.sandbox_service_url}/v1/sandbox/exec",
            json={"workspace_id": workspace_id, "command": command, "cwd": cwd},
        )
        resp.raise_for_status()
        data = resp.json()
        data["sandboxed"] = True
        return data


async def create_sandbox(workspace_id: str) -> dict:
    if not settings.ausome_sandbox_enabled:
        return {"workspace_id": workspace_id, "status": "host-mode"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.sandbox_service_url}/v1/sandbox/create",
            json={"workspace_id": workspace_id},
        )
        resp.raise_for_status()
        return resp.json()
