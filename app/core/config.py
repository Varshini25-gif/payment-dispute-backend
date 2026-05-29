import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


class Settings(BaseSettings):
    APP_NAME: str = "payment-dispute-backend"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/payment_dispute_db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    DB_FUTURE: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


