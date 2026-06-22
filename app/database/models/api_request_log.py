import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from app.database.models.base import Base, GUID


class APIRequestLog(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    correlation_id = Column(String(64), nullable=False, index=True)
    request_id = Column(String(64), nullable=True, index=True)
    method = Column(String(16), nullable=False)
    path = Column(String(512), nullable=False)
    query_string = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    client_ip = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    actor = Column(String(128), nullable=True)
    request_body = Column(Text, nullable=True)
    error_detail = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_api_request_log_correlation_id", "correlation_id"),
        Index("ix_api_request_log_status_code", "status_code"),
        Index("ix_api_request_log_created_at", "created_at"),
    )
