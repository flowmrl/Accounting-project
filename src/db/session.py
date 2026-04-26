"""SQLAlchemy engine + session factory."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.core.models.base import Base  # noqa: F401 — triggers model registration
import src.core.models  # noqa: F401

from src.config import settings

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            echo=settings.db_echo,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


# Expose engine property for compatibility
class _EngineProxy:
    def __getattr__(self, name):
        return getattr(_get_engine(), name)


engine = _EngineProxy()
SessionLocal = _get_session_factory


def get_session() -> Session:
    """Yield a DB session (FastAPI dependency)."""
    factory = _get_session_factory()
    with factory() as session:
        yield session


def create_all_tables() -> None:
    Base.metadata.create_all(_get_engine())
