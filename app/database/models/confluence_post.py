import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from app.database.models.base import Base, GUID


class ConfluencePost(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    dispute_id = Column(GUID(), ForeignKey("dispute.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(128), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    url = Column(String(255), nullable=True)
    excerpt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    dispute = relationship("Dispute", back_populates="confluence_posts")

    __table_args__ = (
        Index("ix_confluence_post_dispute_id", "dispute_id"),
    )
