"""PostgreSQL connection setup and SQLAlchemy engine configuration."""

from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from app.core.config import settings


@lru_cache(maxsize=1)
def create_db_engine() -> Engine:
    """
    Create and configure SQLAlchemy engine with PostgreSQL connection.
    
    Features:
    - Connection pooling with QueuePool
    - Connection timeout and recycling
    - Pre-ping to verify connections
    - Echo SQL statements in debug mode
    
    Returns:
        Engine: Configured SQLAlchemy engine
    """
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        future=settings.DB_FUTURE,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
    )
    
    # Register event listeners for connection management
    _register_connection_events(engine)
    
    return engine


def get_engine() -> Engine:
    """Return the cached SQLAlchemy engine."""
    return create_db_engine()


def _register_connection_events(engine: Engine) -> None:
    """
    Register SQLAlchemy event listeners for connection management.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set pragmas for SQLite connections if needed."""
        # Only apply to non-PostgreSQL databases
        if "sqlite" in settings.DATABASE_URL:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    

__all__ = ["create_db_engine", "get_engine"]

