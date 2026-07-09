"""Database session management and factory."""

from typing import Generator
from sqlalchemy.orm import sessionmaker, Session
from app.database.connection import get_engine


# Create session factory without binding during import so migration imports stay lightweight.
SessionLocal = sessionmaker(
    class_=Session,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    future=True,
)


def get_db_session() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes.
    
    Yields a database session and ensures it's properly closed.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    """
    session = SessionLocal(bind=get_engine())
    try:
        yield session
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Alias for get_db_session for backwards compatibility.
    
    Yields:
        Session: SQLAlchemy database session
    """
    yield from get_db_session()


__all__ = ["SessionLocal", "get_db_session", "get_db"]

