import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Enum as SAEnum, Index, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.models.base import Base, GUID
from app.database.models.enums import DisputeStatus, DisputeType


class Dispute(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    external_id = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(SAEnum(DisputeStatus, native_enum=False), nullable=False, default=DisputeStatus.NEW)
    type = Column(SAEnum(DisputeType, native_enum=False), nullable=False, default=DisputeType.OTHER)
    amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency = Column(String(3), nullable=False, default="USD")
    customer_id = Column(String(64), nullable=True, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    routing_logs = relationship("RoutingLog", back_populates="dispute", cascade="all, delete-orphan")
    sla_tracking = relationship("SlaTracking", back_populates="dispute", uselist=False, cascade="all, delete-orphan")
    jira_issues = relationship("JiraIssue", back_populates="dispute", cascade="all, delete-orphan")
    confluence_posts = relationship("ConfluencePost", back_populates="dispute", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="dispute", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_dispute_status", "status"),
        Index("ix_dispute_type", "type"),
        Index("ix_dispute_created_at", "created_at"),
        Index("ix_dispute_status_created_at", "status", "created_at"),
        Index("ix_dispute_customer_created_at", "customer_id", "created_at"),
        Index("ix_dispute_currency_created_at", "currency", "created_at"),
    )
