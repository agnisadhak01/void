"""Open Policy Agent integration stub (M14)."""

import httpx
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class OPAMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.opa_url or not request.url.path.startswith("/v1/agent"):
            return await call_next(request)
        body = {
            "input": {
                "path": request.url.path,
                "method": request.method,
                "role": request.headers.get("x-ausome-role", "developer"),
            }
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(f"{settings.opa_url.rstrip('/')}/v1/data/ausome/allow", json=body)
                if resp.status_code == 200 and not resp.json().get("result", True):
                    raise HTTPException(status_code=403, detail="OPA policy denied")
        except httpx.HTTPError:
            pass
        return await call_next(request)
