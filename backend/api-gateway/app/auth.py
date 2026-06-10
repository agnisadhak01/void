from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt

from app.config import settings


@dataclass
class AuthUser:
    id: str
    supabase_id: str
    role: str
    email: str | None = None


def _dev_user() -> AuthUser:
    return AuthUser(
        id="00000000-0000-0000-0000-000000000099",
        supabase_id="dev-user",
        role="admin",
        email="dev@ausome.local",
    )


async def get_current_user(request: Request) -> AuthUser:
    if settings.ausome_auth_disabled:
        return _dev_user()

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = auth[7:]
    if not settings.supabase_jwt_secret:
        raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET not configured")

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    role = payload.get("role", "developer")
    if role not in ("admin", "developer", "viewer"):
        role = "developer"

    return AuthUser(
        id=sub,
        supabase_id=sub,
        role=role,
        email=payload.get("email"),
    )


def require_role(*allowed: str):
    async def checker(user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail=f"Role {user.role} not permitted")
        return user

    return checker


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
