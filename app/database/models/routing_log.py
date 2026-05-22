import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from app.database.models.base import Base, GUID
from app.database.models.enums import RoutingStatus, SourceSystem


class RoutingLog(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    dispute_id = Column(GUID(), ForeignKey("dispute.id", ondelete="CASCADE"), nullable=False, index=True)
    source_system = Column(SAEnum(SourceSystem, native_enum=False), nullable=False, default=SourceSystem.INTERNAL)
    destination = Column(String(128), nullable=True)
    status = Column(SAEnum(RoutingStatus, native_enum=False), nullable=False, default=RoutingStatus.PENDING)
    dispatched_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    dispute = relationship("Dispute", back_populates="routing_logs")

    __table_args__ = (
        Index("ix_routing_log_dispute_id", "dispute_id"),
        Index("ix_routing_log_status", "status"),
        Index("ix_routing_log_dispatched_at", "dispatched_at"),
    )
