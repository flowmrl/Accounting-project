"""JWT Bearer authentication — stdlib HMAC HS256 + passlib sha256_crypt."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config import settings
from src.db.session import get_session

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload["exp"] = expire.timestamp()
    header = _b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64encode(json.dumps(payload).encode())
    signing_input = f"{header}.{body}"
    sig = _b64encode(
        hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    )
    return f"{signing_input}.{sig}"


def decode_token(token: str) -> dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        header_b64, body_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{body_b64}"
        expected_sig = _b64encode(
            hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig_b64, expected_sig):
            raise ValueError("Signature mismatch")
        payload = json.loads(_b64decode(body_b64))
        if "exp" in payload and payload["exp"] < datetime.now(timezone.utc).timestamp():
            raise ValueError("Token expired")
        return payload
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session),
) -> dict[str, Any]:
    from src.core.models.user import User
    payload = decode_token(token)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_superadmin": user.is_superadmin,
        "roles": payload.get("roles", {}),
        "payload": payload,
    }


def require_role(*roles: str):
    """Dépendance FastAPI — vérifie que l'utilisateur a au moins un des rôles pour la société."""
    async def _check(
        company_id: str,
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user.get("is_superadmin"):
            return current_user
        user_roles: dict = current_user.get("roles", {})
        role = user_roles.get(company_id)
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle requis : {', '.join(roles)}",
            )
        return current_user
    return _check
