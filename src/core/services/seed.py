"""Seed de démarrage — crée le superadmin si la table users est vide."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from src.api.middleware.auth import hash_password
from src.core.models.user import User


def seed_admin(db: Session, email: str = "admin@compta-pme.fr", password: str = "admin") -> bool:
    """Crée le superadmin initial. Retourne True si créé, False si déjà existant."""
    if db.query(User).count() > 0:
        return False
    admin = User(
        id=str(uuid.uuid4()),
        email=email,
        full_name="Administrateur",
        hashed_password=hash_password(password),
        is_superadmin=True,
    )
    db.add(admin)
    db.commit()
    return True
