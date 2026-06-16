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

    # Jira configuration
    JIRA_BASE_URL: str = ""
    JIRA_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""
    JIRA_PROJECT_KEY: str = "PAY"

    # Database configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/payment_dispute_db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    DB_FUTURE: bool = True

    # Background worker scheduling
    SLA_MONITOR_INTERVAL_SECONDS: int = 300
    CLEANUP_INTERVAL_SECONDS: int = 3600
    ROUTING_SYNC_INTERVAL_SECONDS: int = 300
    STALE_DISPUTE_SCAN_INTERVAL_SECONDS: int = 900
    ROUTING_RETRY_DELAY_MINUTES: int = 15
    ROUTING_SYNC_DELAY_MINUTES: int = 60
    CLEANUP_DISPUTE_RETENTION_DAYS: int = 30
    CLEANUP_LOG_RETENTION_DAYS: int = 30
    STALE_DISPUTE_AGE_HOURS: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


