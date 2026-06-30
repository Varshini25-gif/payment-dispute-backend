from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.models import ConfluencePost, Dispute
from app.database.session import get_db
from app.services.confluence.publisher import ConfluencePublishError, ConfluencePublisher

router = APIRouter(tags=["Confluence"])


class ConfluencePostResponse(BaseModel):
    id: UUID
    dispute_id: UUID
    page_id: Optional[str]
    title: str
    url: Optional[str]
    excerpt: Optional[str]
    publish_status: str
    publish_attempts: int
    last_attempted_at: Optional[datetime]
    last_published_at: Optional[datetime]
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublishRequest(BaseModel):
    parent_page_id: Optional[str] = None


@router.post(
    "/confluence/disputes/{dispute_id}/publish",
    response_model=ConfluencePostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def publish_dispute_summary(
    dispute_id: UUID,
    body: Optional[PublishRequest] = None,
    db: Session = Depends(get_db),
) -> ConfluencePost:
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found.")

    try:
        post = ConfluencePublisher().publish_dispute_summary(
            dispute,
            db=db,
            parent_page_id=(body.parent_page_id if body else None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ConfluencePublishError as exc:
        raise HTTPException(
            status_code=getattr(exc, "status_code", status.HTTP_502_BAD_GATEWAY),
            detail=f"Confluence publish failed: {exc}",
        ) from exc

    return post


@router.get("/confluence/disputes/{dispute_id}/posts", response_model=list[ConfluencePostResponse])
async def list_dispute_posts(
    dispute_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ConfluencePost]:
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found.")

    posts = db.scalars(
        select(ConfluencePost)
        .where(ConfluencePost.dispute_id == dispute_id)
        .order_by(desc(ConfluencePost.created_at))
        .limit(limit)
    ).all()
    return list(posts)


@router.get("/confluence/posts/{post_id}", response_model=ConfluencePostResponse)
async def get_post(post_id: UUID, db: Session = Depends(get_db)) -> ConfluencePost:
    post = db.get(ConfluencePost, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confluence post not found.")
    return post


@router.get("/confluence/disputes/{dispute_id}/publish-status", response_model=ConfluencePostResponse)
async def get_latest_publish_status(dispute_id: UUID, db: Session = Depends(get_db)) -> ConfluencePost:
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found.")

    latest = db.scalar(
        select(ConfluencePost)
        .where(ConfluencePost.dispute_id == dispute_id)
        .order_by(desc(ConfluencePost.created_at))
        .limit(1)
    )
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Confluence publish attempts found.")
    return latest