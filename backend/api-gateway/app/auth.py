from dataclasses import dataclass
from typing import Annotated, Any

import asyncpg
import httpx
from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwk, jwt

from app.config import settings

_jwks_cache: dict[str, Any] | None = None


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


async def _fetch_jwks() -> dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    if not settings.keycloak_jwks_url:
        return {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(settings.keycloak_jwks_url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        return _jwks_cache


def _role_from_claims(payload: dict[str, Any]) -> str:
    groups = payload.get("groups") or payload.get("realm_access", {}).get("roles") or []
    if isinstance(groups, list):
        for g in ("admin", "developer", "viewer"):
            if g in groups:
                return g
    role = payload.get("role", "developer")
    return role if role in ("admin", "developer", "viewer") else "developer"


async def _decode_keycloak_token(token: str) -> dict[str, Any]:
    jwks = await _fetch_jwks()
    if not jwks.get("keys"):
        raise HTTPException(status_code=500, detail="Keycloak JWKS unavailable")
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    key_data = next((k for k in jwks["keys"] if k.get("kid") == kid), jwks["keys"][0])
    key = jwk.construct(key_data)
    alg = header.get("alg", "RS256")
    options = {"verify_aud": False}
    if settings.keycloak_issuer:
        return jwt.decode(token, key, algorithms=[alg], issuer=settings.keycloak_issuer, options=options)
    return jwt.decode(token, key, algorithms=[alg], options=options)


async def get_current_user(request: Request) -> AuthUser:
    if settings.ausome_auth_disabled:
        return _dev_user()

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = auth[7:]

    try:
        if settings.keycloak_jwks_url:
            payload = await _decode_keycloak_token(token)
        elif settings.supabase_jwt_secret:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        else:
            raise HTTPException(status_code=500, detail="No JWT verifier configured (SUPABASE_JWT_SECRET or KEYCLOAK_JWKS_URL)")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    role = _role_from_claims(payload)

    return AuthUser(
        id=sub,
        supabase_id=sub,
        role=role,
        email=payload.get("email"),
    )


async def upsert_user(conn: asyncpg.Connection, user: AuthUser) -> str:
    """Sync JWT user into users table; returns canonical user UUID."""
    row = await conn.fetchrow(
        """
        INSERT INTO users (supabase_id, email, role)
        VALUES ($1, $2, $3)
        ON CONFLICT (supabase_id) DO UPDATE SET
            email = COALESCE(EXCLUDED.email, users.email),
            role = EXCLUDED.role
        RETURNING id
        """,
        user.supabase_id,
        user.email,
        user.role,
    )
    return str(row["id"])


async def resolve_user(request: Request) -> AuthUser:
    user = await get_current_user(request)
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        return user
    async with pool.acquire() as conn:
        uid = await upsert_user(conn, user)
        return AuthUser(id=uid, supabase_id=user.supabase_id, role=user.role, email=user.email)


ResolvedUser = Annotated[AuthUser, Depends(resolve_user)]


def require_role(*allowed: str):
    async def checker(user: Annotated[AuthUser, Depends(resolve_user)]) -> AuthUser:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail=f"Role {user.role} not permitted")
        return user

    return checker


CurrentUser = Annotated[AuthUser, Depends(resolve_user)]
