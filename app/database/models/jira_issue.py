import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from app.database.models.base import Base, GUID
from app.database.models.enums import JiraIssueStatus, JiraPriority


class JiraIssue(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    dispute_id = Column(GUID(), ForeignKey("dispute.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_key = Column(String(64), nullable=False, unique=True)
    project_key = Column(String(32), nullable=True)
    status = Column(SAEnum(JiraIssueStatus, native_enum=False), nullable=False, default=JiraIssueStatus.OPEN)
    priority = Column(SAEnum(JiraPriority, native_enum=False), nullable=False, default=JiraPriority.MEDIUM)
    url = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    dispute = relationship("Dispute", back_populates="jira_issues")

    __table_args__ = (
        Index("ix_jira_issue_dispute_id", "dispute_id"),
        Index("ix_jira_issue_status", "status"),
    )

    def __init__(self, **kwargs):
        jira_key = kwargs.pop("jira_key", None)
        jira_id = kwargs.pop("jira_id", None)

        if jira_key is not None and "issue_key" not in kwargs:
            kwargs["issue_key"] = jira_key

        super().__init__(**kwargs)

        if jira_id is not None:
            self.jira_id = jira_id

    @property
    def jira_key(self):
        return self.issue_key

    @jira_key.setter
    def jira_key(self, value):
        self.issue_key = value
