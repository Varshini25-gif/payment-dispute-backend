from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.database.models import Dispute, SlaTracking
from app.database.models.enums import SlaStatus
from app.database.session import get_db
from app.services.sla.tracker import SlaTracker

router = APIRouter(tags=["SLA"])


class SlaTrackRequest(BaseModel):
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    sla_due_at: Optional[datetime] = None
    notes: Optional[str] = None


class SlaResponse(BaseModel):
    id: UUID
    dispute_id: UUID
    sla_due_at: datetime
    sla_status: SlaStatus
    breached_at: Optional[datetime] = None
    escalation_flag: bool = Field(default=False)
    response_hours: float
    resolution_hours: float
    breach_detected: bool = Field(default=False)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.post("/sla/{dispute_id}/track", response_model=SlaResponse, status_code=status.HTTP_201_CREATED)
async def track_sla(dispute_id: UUID, payload: SlaTrackRequest, db: Session = Depends(get_db)) -> SlaTracking:
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found.")

    tracker = SlaTracker()
    result = tracker.track(dispute, db=db, created_at=payload.created_at, resolved_at=payload.resolved_at,
                           sla_due_at=payload.sla_due_at, notes=payload.notes)
    return result["record"]


@router.get("/sla/{dispute_id}", response_model=SlaResponse)
async def get_sla(dispute_id: UUID, db: Session = Depends(get_db)) -> SlaTracking:
    record = db.query(SlaTracking).filter(SlaTracking.dispute_id == dispute_id).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA tracking not found.")
    return record


@router.get("/sla", response_model=list[SlaResponse])
async def list_sla(
    status: Optional[SlaStatus] = Query(default=None),
    breached: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(SlaTracking)
    if status is not None:
        query = query.filter(SlaTracking.sla_status == status)
    if breached is not None:
        query = query.filter(SlaTracking.breach_detected.is_(breached))
    return query.order_by(SlaTracking.created_at.desc()).all()
