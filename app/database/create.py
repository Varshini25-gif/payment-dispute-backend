"""Database initialization and management functions."""

from app.database.connection import engine
from app.database.models.base import Base


def init_db() -> None:
    """Create all database tables for the application."""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def drop_db() -> None:
    """Drop all database tables. Use with caution."""
    Base.metadata.drop_all(bind=engine)
    print("✓ Database tables dropped successfully")


if __name__ == "__main__":
    init_db()
