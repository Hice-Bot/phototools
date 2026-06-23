from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import httpx
import jwt
from fastapi import HTTPException, Request
from jwt import PyJWKClient


def _split_env(name: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def allowed_origins() -> list[str]:
    configured = _split_env("PHOTO_TOOLS_ALLOWED_ORIGINS")
    if configured:
        return configured
    return [
        "http://76.13.106.218:8091",
        "http://localhost:8091",
        "http://127.0.0.1:8091",
    ]


def clerk_publishable_key() -> str:
    return os.getenv("CLERK_PUBLISHABLE_KEY", "pk_test_dummy_phototools")


@lru_cache(maxsize=1)
def _jwk_client() -> PyJWKClient | None:
    jwks_url = os.getenv("CLERK_JWKS_URL")
    if not jwks_url:
        frontend_api = os.getenv("CLERK_FRONTEND_API")
        if frontend_api:
            jwks_url = frontend_api.rstrip("/") + "/.well-known/jwks.json"
    return PyJWKClient(jwks_url) if jwks_url else None


def _verify_clerk_jwt(token: str) -> dict[str, Any]:
    client = _jwk_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Clerk JWT verification is not configured")
    try:
        key = client.get_signing_key_from_jwt(token)
        options = {"verify_aud": bool(os.getenv("CLERK_JWT_AUDIENCE"))}
        payload = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=os.getenv("CLERK_JWT_AUDIENCE") or None,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Clerk session") from exc

    authorized_parties = _split_env("CLERK_AUTHORIZED_PARTIES")
    if authorized_parties and payload.get("azp") not in authorized_parties:
        raise HTTPException(status_code=401, detail="Unauthorized token origin")
    return payload


async def require_paid_api_access(request: Request) -> dict[str, Any]:
    api_keys = set(_split_env("PHOTO_TOOLS_DUMMY_API_KEYS"))
    supplied_key = request.headers.get("x-phototools-api-key")
    if supplied_key and supplied_key in api_keys:
        return {"subject": "api-key", "plan": "dummy"}

    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Paid API/MCP access requires a Clerk session or API key")

    token = auth.split(" ", 1)[1].strip()
    payload = _verify_clerk_jwt(token)
    subject = payload.get("sub")
    paid_users = set(_split_env("PHOTO_TOOLS_DUMMY_PAID_USERS"))
    if "*" in paid_users or (subject and subject in paid_users):
        return {"subject": subject, "plan": "dummy", "claims": payload}

    raise HTTPException(status_code=402, detail="No paid API/MCP entitlement found")


async def pricing_payload() -> dict[str, Any]:
    return {
        "billingMode": os.getenv("PHOTO_TOOLS_BILLING_MODE", "dummy"),
        "publishableKey": clerk_publishable_key(),
        "tiers": [
            {
                "name": "Free Web",
                "price": "$0",
                "credits": "Ad-supported browser usage",
                "features": ["Web tools", "Dummy ad-supported limits", "No API key"],
            },
            {
                "name": "Starter API/MCP",
                "price": "$12/mo",
                "credits": "200 credits",
                "features": ["1 API key", "MCP access", "Basic batch usage"],
            },
            {
                "name": "Pro API/MCP",
                "price": "$29/mo",
                "credits": "500 credits",
                "features": ["3 API keys", "Higher rate limits", "Batch workflows"],
            },
            {
                "name": "Studio",
                "price": "$79/mo",
                "credits": "1,500 credits",
                "features": ["Team keys", "Priority queue", "$0.06/credit overage"],
            },
        ],
    }


async def clerk_health() -> dict[str, Any]:
    jwks_url = os.getenv("CLERK_JWKS_URL")
    if not jwks_url:
        frontend_api = os.getenv("CLERK_FRONTEND_API")
        jwks_url = frontend_api.rstrip("/") + "/.well-known/jwks.json" if frontend_api else None
    if not jwks_url:
        return {"configured": False, "mode": os.getenv("PHOTO_TOOLS_BILLING_MODE", "dummy")}
    async with httpx.AsyncClient(timeout=5) as client:
        res = await client.get(jwks_url)
        return {"configured": res.status_code == 200, "jwksStatus": res.status_code}
