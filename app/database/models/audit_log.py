import uuid
import json
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

    def __init__(self, **kwargs):
        entity_id = kwargs.pop("entity_id", None)
        user_id = kwargs.pop("user_id", None)
        entity_type = kwargs.pop("entity_type", None)
        changes = kwargs.pop("changes", None)

        if entity_id is not None and "dispute_id" not in kwargs:
            kwargs["dispute_id"] = entity_id
        if user_id is not None and "actor" not in kwargs:
            kwargs["actor"] = user_id

        super().__init__(**kwargs)

        if entity_type is not None:
            self.entity_type = entity_type
        if changes is not None:
            self.changes = changes

    @property
    def entity_id(self):
        return self.dispute_id

    @entity_id.setter
    def entity_id(self, value):
        self.dispute_id = value

    @property
    def user_id(self):
        return self.actor

    @user_id.setter
    def user_id(self, value):
        self.actor = value

    @property
    def entity_type(self):
        if not self.metadata_json:
            return None
        try:
            data = json.loads(self.metadata_json)
            return data.get("entity_type")
        except (TypeError, ValueError):
            return None

    @entity_type.setter
    def entity_type(self, value):
        payload = {}
        if self.metadata_json:
            try:
                payload = json.loads(self.metadata_json)
            except (TypeError, ValueError):
                payload = {}
        payload["entity_type"] = value
        self.metadata_json = json.dumps(payload)

    @property
    def changes(self):
        if not self.metadata_json:
            return None
        try:
            data = json.loads(self.metadata_json)
            return data.get("changes")
        except (TypeError, ValueError):
            return None

    @changes.setter
    def changes(self, value):
        payload = {}
        if self.metadata_json:
            try:
                payload = json.loads(self.metadata_json)
            except (TypeError, ValueError):
                payload = {}
        payload["changes"] = value
        self.metadata_json = json.dumps(payload)
