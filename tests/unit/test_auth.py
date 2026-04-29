"""Tests — Auth multi-tenant + RBAC."""
from __future__ import annotations

import asyncio
import uuid
from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from src.api.middleware.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def test_hash_and_verify_password():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_hash_is_different_each_time():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # salted


# ---------------------------------------------------------------------------
# JWT token
# ---------------------------------------------------------------------------

def test_create_and_decode_token():
    data = {"sub": "user-123", "email": "test@example.com", "roles": {}, "is_superadmin": False}
    token = create_access_token(data, timedelta(minutes=30))
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@example.com"


def test_token_expired():
    from fastapi import HTTPException
    data = {"sub": "user-123"}
    token = create_access_token(data, timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_token_tampered():
    from fastapi import HTTPException
    data = {"sub": "user-123"}
    token = create_access_token(data, timedelta(minutes=10))
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(HTTPException):
        decode_token(tampered)


def test_token_invalid_format():
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        decode_token("not.a.valid.jwt.token.at.all")


# ---------------------------------------------------------------------------
# User model (no DB)
# ---------------------------------------------------------------------------

def test_user_model_fields():
    from src.core.models.user import User
    user = User(
        id=str(uuid.uuid4()),
        email="chef@example.com",
        full_name="Chef Comptable",
        hashed_password=hash_password("pass"),
        is_active=True,
        is_superadmin=False,
    )
    assert user.email == "chef@example.com"
    assert user.is_superadmin is False
    assert user.is_active is True


def test_user_role_enum_values():
    from src.core.models.user import UserRole
    assert UserRole.ADMIN == "ADMIN"
    assert UserRole.EXPERT_COMPTABLE == "EXPERT_COMPTABLE"
    assert UserRole.DAF == "DAF"
    assert UserRole.COMPTABLE == "COMPTABLE"
    assert UserRole.READONLY == "READONLY"


# ---------------------------------------------------------------------------
# get_current_user (mocked DB)
# ---------------------------------------------------------------------------

def test_get_current_user_valid():
    from src.api.middleware.auth import get_current_user
    from src.core.models.user import User

    mock_user = User(
        id="user-abc",
        email="admin@example.com",
        full_name="Admin",
        hashed_password=hash_password("x"),
        is_active=True,
        is_superadmin=True,
    )
    token = create_access_token(
        {"sub": "user-abc", "email": "admin@example.com", "roles": {}, "is_superadmin": True},
        timedelta(minutes=30),
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    result = asyncio.run(get_current_user(token=token, db=mock_db))
    assert result["user_id"] == "user-abc"
    assert result["is_superadmin"] is True


def test_get_current_user_inactive():
    from fastapi import HTTPException
    from src.api.middleware.auth import get_current_user

    token = create_access_token(
        {"sub": "user-xyz", "email": "x@x.com", "roles": {}, "is_superadmin": False},
        timedelta(minutes=30),
    )
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(token=token, db=mock_db))
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# require_role
# ---------------------------------------------------------------------------

def test_require_role_superadmin_bypasses():
    from src.api.middleware.auth import require_role

    current = {"is_superadmin": True, "roles": {}}
    checker = require_role("ADMIN")

    result = asyncio.run(checker(company_id="company-1", current_user=current))
    assert result["is_superadmin"] is True


def test_require_role_correct_role():
    from src.api.middleware.auth import require_role

    current = {"is_superadmin": False, "roles": {"company-1": "ADMIN"}}
    checker = require_role("ADMIN", "EXPERT_COMPTABLE")

    result = asyncio.run(checker(company_id="company-1", current_user=current))
    assert result["roles"]["company-1"] == "ADMIN"


def test_require_role_insufficient():
    from fastapi import HTTPException
    from src.api.middleware.auth import require_role

    current = {"is_superadmin": False, "roles": {"company-1": "READONLY"}}
    checker = require_role("ADMIN", "EXPERT_COMPTABLE")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(checker(company_id="company-1", current_user=current))
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# seed_admin
# ---------------------------------------------------------------------------

def test_seed_admin_creates_user():
    from src.core.services.seed import seed_admin

    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0

    result = seed_admin(mock_db, email="admin@test.com", password="pass")
    assert result is True
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_seed_admin_skips_if_exists():
    from src.core.services.seed import seed_admin

    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 1

    result = seed_admin(mock_db)
    assert result is False
    mock_db.add.assert_not_called()
