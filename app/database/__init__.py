"""Database module initialization."""

from app.database.connection import get_engine
from app.database.models.base import Base


def __getattr__(name):
    if name == "engine":
        return get_engine()
    if name == "SessionLocal":
        from app.database.session import SessionLocal
        return SessionLocal
    if name == "get_db_session":
        from app.database.session import get_db_session
        return get_db_session
    if name == "get_db":
        from app.database.session import get_db
        return get_db
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "engine",
    "SessionLocal",
    "get_db_session",
    "get_db",
    "Base",
]

