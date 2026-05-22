"""Utilisateurs et rôles — modèle multi-tenant."""
from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class UserRole(StrEnum):
    ADMIN = "ADMIN"                         # Accès total
    EXPERT_COMPTABLE = "EXPERT_COMPTABLE"   # Toutes les écritures, lecture tout
    DAF = "DAF"                             # Validation, reporting, lecture tout
    COMPTABLE = "COMPTABLE"                 # Saisie et validation écritures
    READONLY = "READONLY"                   # Lecture seule


class User(Base, UUIDMixin, TimestampMixin):
    """Compte utilisateur (indépendant des sociétés)."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    company_roles: Mapped[list["UserCompanyRole"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserCompanyRole(Base, UUIDMixin, TimestampMixin):
    """Association utilisateur ↔ société avec rôle."""
    __tablename__ = "user_company_roles"
    __table_args__ = (UniqueConstraint("user_id", "company_id", name="uq_user_company"),)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default=UserRole.COMPTABLE, nullable=False)

    user: Mapped[User] = relationship(back_populates="company_roles")
