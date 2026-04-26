"""Authentication routes — login + token."""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from src.api.middleware.auth import create_access_token, verify_password
from src.config import settings

router = APIRouter(prefix="/auth", tags=["Authentification"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    username: str
    password: str
    company_id: str | None = None


# ---------------------------------------------------------------------------
# Stub user store — replace with DB lookup in production
# ---------------------------------------------------------------------------

_DEMO_USERS: dict[str, dict] = {
    "admin": {
        # sha256_crypt hash of "secret"
        "hashed_password": "$5$rounds=535000$sh9t5U655t/fHJwT$o7AZbPHH4Hz7uoAmy4xfKkq1vjlyxj3qMaph7/mjMcB",
        "role": "ADMIN",
        "company_id": None,
    }
}


def _authenticate(username: str, password: str) -> dict | None:
    user = _DEMO_USERS.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/token", response_model=TokenResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    """OAuth2 password flow (Swagger UI compatible)."""
    user = _authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")
    token = create_access_token(
        {"sub": form_data.username, "role": user["role"], "company_id": user.get("company_id")},
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    return TokenResponse(access_token=token, expires_in=settings.access_token_expire_minutes * 60)


@router.post("/login", response_model=TokenResponse)
async def login_json(body: LoginRequest) -> TokenResponse:
    """JSON login endpoint."""
    user = _authenticate(body.username, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")
    company_id = body.company_id or user.get("company_id")
    token = create_access_token(
        {"sub": body.username, "role": user["role"], "company_id": company_id},
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    return TokenResponse(access_token=token, expires_in=settings.access_token_expire_minutes * 60)
