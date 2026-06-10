from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, condecimal, constr
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import Dispute
from app.database.models.enums import DisputeStatus, DisputeType
from app.database.session import get_db
from app.services.dispute.routing_service import DisputeRoutingService

router = APIRouter(tags=["Disputes"])


class DisputeBase(BaseModel):
    external_id: constr(strip_whitespace=True, min_length=1, max_length=64)
    status: DisputeStatus = DisputeStatus.NEW
    type: DisputeType = DisputeType.OTHER
    amount: condecimal(max_digits=12, decimal_places=2, ge=0) = Field(default=Decimal("0.00"))
    currency: constr(strip_whitespace=True, min_length=3, max_length=3) = Field(default="USD")
    customer_id: Optional[constr(strip_whitespace=True, max_length=64)] = None
    reason: Optional[str] = None


class DisputeCreate(DisputeBase):
    pass


class DisputeUpdate(BaseModel):
    external_id: Optional[constr(strip_whitespace=True, min_length=1, max_length=64)] = None
    status: Optional[DisputeStatus] = None
    type: Optional[DisputeType] = None
    amount: Optional[condecimal(max_digits=12, decimal_places=2, ge=0)] = None
    currency: Optional[constr(strip_whitespace=True, min_length=3, max_length=3)] = None
    customer_id: Optional[constr(strip_whitespace=True, max_length=64)] = None
    reason: Optional[str] = None


class DisputeResponse(DisputeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DisputeListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[DisputeResponse]


def _apply_filters(
    status: Optional[DisputeStatus],
    type_: Optional[DisputeType],
    customer_id: Optional[str],
    external_id: Optional[str],
    min_amount: Optional[Decimal],
    max_amount: Optional[Decimal],
    currency: Optional[str],
) -> list[Any]:
    filters: list[Any] = []
    if status is not None:
        filters.append(Dispute.status == status)
    if type_ is not None:
        filters.append(Dispute.type == type_)
    if customer_id is not None:
        filters.append(Dispute.customer_id == customer_id)
    if external_id is not None:
        filters.append(Dispute.external_id == external_id)
    if min_amount is not None:
        filters.append(Dispute.amount >= min_amount)
    if max_amount is not None:
        filters.append(Dispute.amount <= max_amount)
    if currency is not None:
        filters.append(Dispute.currency == currency.upper())
    return filters


@router.post("/disputes", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    dispute_in: DisputeCreate,
    db: Session = Depends(get_db),
) -> Dispute:
    dispute = Dispute(**dispute_in.model_dump())
    db.add(dispute)
    try:
        db.commit()
        db.refresh(dispute)
    except IntegrityError as exc:
        db.rollback()
        detail = "A dispute with the provided external_id already exists."
        if "external_id" not in str(exc).lower():
            detail = "Unable to create dispute."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    DisputeRoutingService().route_dispute(dispute, db=db)

    return dispute


@router.get("/disputes", response_model=DisputeListResponse)
async def list_disputes(
    status: Optional[DisputeStatus] = Query(None),
    type_: Optional[DisputeType] = Query(None, alias="type"),
    customer_id: Optional[str] = Query(None, min_length=1, max_length=64),
    external_id: Optional[str] = Query(None, min_length=1, max_length=64),
    currency: Optional[str] = Query(None, min_length=3, max_length=3),
    min_amount: Optional[Decimal] = Query(None, ge=0),
    max_amount: Optional[Decimal] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DisputeListResponse:
    filters = _apply_filters(status, type_, customer_id, external_id, min_amount, max_amount, currency)
    query = select(Dispute).where(*filters).order_by(Dispute.created_at.desc())
    total = db.scalar(select(func.count()).select_from(Dispute).where(*filters))
    offset = (page - 1) * page_size
    disputes = db.scalars(query.offset(offset).limit(page_size)).all()

    return DisputeListResponse(
        page=page,
        page_size=page_size,
        total=total or 0,
        items=disputes,
    )


@router.get("/disputes/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(dispute_id: UUID, db: Session = Depends(get_db)) -> Dispute:
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found.")
    return dispute


@router.put("/disputes/{dispute_id}", response_model=DisputeResponse)
async def update_dispute(
    dispute_id: UUID,
    dispute_in: DisputeUpdate,
    db: Session = Depends(get_db),
) -> Dispute:
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found.")

    update_data = dispute_in.model_dump(exclude_unset=True)
    if not update_data:
        return dispute

    for field, value in update_data.items():
        setattr(dispute, field, value)

    try:
        db.commit()
        db.refresh(dispute)
    except IntegrityError as exc:
        db.rollback()
        detail = "Unable to update dispute."
        if "external_id" in str(exc).lower():
            detail = "A dispute with the provided external_id already exists."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    return dispute


@router.delete("/disputes/{dispute_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dispute(dispute_id: UUID, db: Session = Depends(get_db)) -> Response:
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found.")

    db.delete(dispute)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

