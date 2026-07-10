import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.models.base import Base, GUID
from app.database.models.enums import SlaStatus


class SlaTracking(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    dispute_id = Column(GUID(), ForeignKey("dispute.id", ondelete="CASCADE"), nullable=False, unique=True)
    sla_due_at = Column(DateTime(timezone=True), nullable=False)
    sla_status = Column(SAEnum(SlaStatus, native_enum=False), nullable=False, default=SlaStatus.ON_TRACK)
    breached_at = Column(DateTime(timezone=True), nullable=True)
    breach_detected = Column(Boolean, nullable=False, default=False)
    escalation_flag = Column(Boolean, nullable=False, default=False)
    escalation_reason = Column(String(255), nullable=True)
    response_hours = Column(Numeric(8, 2), nullable=True, default=0)
    resolution_hours = Column(Numeric(8, 2), nullable=True, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    dispute = relationship("Dispute", back_populates="sla_tracking")

    __table_args__ = (
        Index("ix_sla_tracking_sla_due_at", "sla_due_at"),
        Index("ix_sla_tracking_sla_status", "sla_status"),
    )

    @property
    def status(self):
        return self.sla_status

    @status.setter
    def status(self, value):
        self.sla_status = value

    @property
    def breached(self):
        return self.breach_detected

    @breached.setter
    def breached(self, value):
        self.breach_detected = value


# Backward-compatible alias kept for older imports/tests.
SLATracking = SlaTracking
