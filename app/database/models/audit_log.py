import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from app.database.models.base import Base, GUID
from app.database.models.enums import AuditAction


class AuditLog(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    dispute_id = Column(GUID(), ForeignKey("dispute.id", ondelete="CASCADE"), nullable=False, index=True)
    actor = Column(String(128), nullable=False)
    action = Column(SAEnum(AuditAction, native_enum=False), nullable=False)
    field_name = Column(String(128), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    dispute = relationship("Dispute", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_log_dispute_id", "dispute_id"),
        Index("ix_audit_log_action", "action"),
        Index("ix_audit_log_created_at", "created_at"),
    )
