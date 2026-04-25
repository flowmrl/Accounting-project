"""SQLAlchemy async engine + session factory."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.core.models.base import Base  # noqa: F401 — triggers model registration
import src.core.models  # noqa: F401

from src.config import settings


def _make_engine():
    return create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
    )


engine = _make_engine()
SessionLocal: sessionmaker[Session] = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Session:
    """Yield a DB session (use as context manager or FastAPI dependency)."""
    with SessionLocal() as session:
        yield session


def create_all_tables() -> None:
    Base.metadata.create_all(engine)
