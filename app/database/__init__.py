from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_env

DATABASE_URL = get_env("DATABASE_URL", "sqlite:///./payment_dispute.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, future=True, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    with SessionLocal() as session:
        yield session
