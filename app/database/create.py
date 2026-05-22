from app.database import engine
from app.database.models import Base


def init_db() -> None:
    """Create all database tables for the application."""
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables. Use with caution."""
    Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    init_db()
