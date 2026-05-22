"""Authentication routes — login, register, me, users."""
from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.api.middleware.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from src.config import settings
from src.core.models.user import User, UserCompanyRole, UserRole
from src.db.session import get_session

router = APIRouter(prefix="/auth", tags=["Authentification"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str


class InviteRequest(BaseModel):
    email: str
    full_name: str
    password: str
    company_id: str
    role: str = UserRole.COMPTABLE


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_superadmin: bool
    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_token(user: User, db: Session) -> str:
    roles = {
        r.company_id: r.role
        for r in db.query(UserCompanyRole).filter(UserCompanyRole.user_id == user.id).all()
    }
    return create_access_token(
        {"sub": user.id, "email": user.email, "roles": roles, "is_superadmin": user.is_superadmin},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/token", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
) -> TokenResponse:
    """OAuth2 password flow (Swagger UI + frontend compatible)."""
    user = db.query(User).filter(User.email == form_data.username, User.is_active.is_(True)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")
    token = _build_token(user, db)
    return TokenResponse(access_token=token, expires_in=settings.access_token_expire_minutes * 60)


@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: RegisterRequest, db: Session = Depends(get_session)) -> User:
    """Crée le premier compte (superadmin) si aucun utilisateur n'existe encore."""
    if db.query(User).count() > 0:
        raise HTTPException(status_code=403, detail="Inscription publique désactivée. Utilisez /auth/invite.")
    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        is_superadmin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/invite", response_model=UserOut, status_code=201)
async def invite_user(
    body: InviteRequest,
    db: Session = Depends(get_session),
    current: dict = Depends(get_current_user),
) -> User:
    """Invite un utilisateur sur une société (réservé aux admins/superadmins)."""
    if not current.get("is_superadmin"):
        role = current.get("roles", {}).get(body.company_id)
        if role not in (UserRole.ADMIN, UserRole.EXPERT_COMPTABLE):
            raise HTTPException(status_code=403, detail="Droits insuffisants pour inviter")

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        user = existing
    else:
        user = User(
            id=str(uuid.uuid4()),
            email=body.email,
            full_name=body.full_name,
            hashed_password=hash_password(body.password),
        )
        db.add(user)
        db.flush()

    assoc = UserCompanyRole(
        id=str(uuid.uuid4()),
        user_id=user.id,
        company_id=body.company_id,
        role=body.role,
    )
    db.add(assoc)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
async def me(
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> User:
    user = db.query(User).filter(User.id == current["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: Session = Depends(get_session),
    current: dict = Depends(get_current_user),
) -> list[User]:
    if not current.get("is_superadmin"):
        raise HTTPException(status_code=403, detail="Réservé aux superadmins")
    return db.query(User).all()


@router.post("/change-password", status_code=200)
async def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_session),
    current: dict = Depends(get_current_user),
) -> dict:
    user = db.query(User).filter(User.id == current["user_id"]).first()
    if not user or not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour"}
