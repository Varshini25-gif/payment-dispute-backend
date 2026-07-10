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

    def __init__(self, **kwargs):
        endpoint = kwargs.pop("endpoint", None)
        response_time_ms = kwargs.pop("response_time_ms", None)
        user_id = kwargs.pop("user_id", None)

        if endpoint is not None and "path" not in kwargs:
            kwargs["path"] = endpoint
        if response_time_ms is not None and "duration_ms" not in kwargs:
            kwargs["duration_ms"] = response_time_ms
        if user_id is not None and "actor" not in kwargs:
            kwargs["actor"] = user_id

        kwargs.setdefault("correlation_id", "test-correlation-id")
        kwargs.setdefault("path", "/")
        kwargs.setdefault("duration_ms", 0)

        super().__init__(**kwargs)

    @property
    def endpoint(self):
        return self.path

    @endpoint.setter
    def endpoint(self, value):
        self.path = value

    @property
    def response_time_ms(self):
        return self.duration_ms

    @response_time_ms.setter
    def response_time_ms(self, value):
        self.duration_ms = value

    @property
    def user_id(self):
        return self.actor

    @user_id.setter
    def user_id(self, value):
        self.actor = value


# Backward-compatible alias kept for older imports/tests.
ApiRequestLog = APIRequestLog
