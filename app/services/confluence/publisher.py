from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.models import ConfluencePost, Dispute
from app.services.confluence.client import ConfluenceClient
from app.services.confluence.html_builder import build_page_title, build_resolution_html


class ConfluencePublishError(Exception):
    pass


class ConfluencePublisher:
    """Publishes dispute summaries and tracks publishing state in the database."""

    def __init__(self, client: Optional[ConfluenceClient] = None) -> None:
        self.client = client or ConfluenceClient()

    def _latest_post_for_dispute(self, dispute_id: UUID, db: Session) -> Optional[ConfluencePost]:
        return db.scalar(
            select(ConfluencePost)
            .where(ConfluencePost.dispute_id == dispute_id)
            .order_by(desc(ConfluencePost.created_at))
            .limit(1)
        )

    def publish_dispute_summary(
        self,
        dispute: Dispute,
        *,
        db: Session,
        parent_page_id: Optional[str] = None,
    ) -> ConfluencePost:
        existing = self._latest_post_for_dispute(dispute.id, db)
        now = datetime.utcnow()

        post = existing or ConfluencePost(
            dispute_id=dispute.id,
            title=build_page_title(dispute),
            publish_status="pending",
            publish_attempts=0,
        )
        if existing is None:
            db.add(post)

        post.publish_status = "in_progress"
        post.last_attempted_at = now
        post.publish_attempts = (post.publish_attempts or 0) + 1
        post.failure_reason = None
        post.title = build_page_title(dispute)

        try:
            body_html = build_resolution_html(dispute, published_at=now)
            page = self.client.create_page(post.title, body_html, parent_page_id=parent_page_id)

            post.page_id = str(page.get("id") or "") or post.page_id
            post.url = page.get("resolved_url")
            post.excerpt = (getattr(dispute, "reason", "") or "")[:500]
            post.publish_status = "published"
            post.last_published_at = now
            post.failure_reason = None
            db.commit()
            db.refresh(post)
            return post
        except Exception as exc:  # noqa: BLE001
            post.publish_status = "failed"
            post.failure_reason = str(exc)
            db.commit()
            db.refresh(post)
            raise ConfluencePublishError(str(exc)) from exc