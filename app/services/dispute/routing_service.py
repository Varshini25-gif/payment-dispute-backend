from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from app.database.models import RoutingLog
from app.database.models.enums import DisputeStatus, JiraPriority, RoutingStatus, SourceSystem


def _as_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError):
        return Decimal("0.00")


def _as_lower_text(value: Any) -> str:
    return str(value or "").strip().lower()


def determine_queue(dispute: Any) -> str:
    """Auto-assign a queue based on amount, type, and reason."""
    amount = _as_decimal(getattr(dispute, "amount", 0))
    dispute_type = _as_lower_text(getattr(dispute, "type", "other"))
    reason = _as_lower_text(getattr(dispute, "reason", ""))
    customer_id = _as_lower_text(getattr(dispute, "customer_id", ""))

    if amount >= Decimal("10000"):
        return "high_value"

    if dispute_type in {"fraud", "chargeback"} or "fraud" in reason or "vip" in customer_id:
        return "fraud_review" if "fraud" in reason or dispute_type == "fraud" else "chargeback_queue"

    if amount >= Decimal("1000"):
        return "priority"

    return "standard"


def determine_priority(dispute: Any) -> str:
    """Set a priority label for the dispute."""
    amount = _as_decimal(getattr(dispute, "amount", 0))
    dispute_type = _as_lower_text(getattr(dispute, "type", "other"))
    reason = _as_lower_text(getattr(dispute, "reason", ""))

    if amount >= Decimal("10000") or dispute_type in {"fraud", "chargeback"} or "fraud" in reason:
        return JiraPriority.CRITICAL.value

    if amount >= Decimal("5000"):
        return JiraPriority.HIGH.value

    if amount >= Decimal("1000"):
        return JiraPriority.MEDIUM.value

    return JiraPriority.LOW.value


def should_escalate(dispute: Any) -> bool:
    """Determine whether the dispute should be escalated."""
    amount = _as_decimal(getattr(dispute, "amount", 0))
    dispute_type = _as_lower_text(getattr(dispute, "type", "other"))
    reason = _as_lower_text(getattr(dispute, "reason", ""))
    customer_id = _as_lower_text(getattr(dispute, "customer_id", ""))

    return (
        amount >= Decimal("5000")
        or dispute_type in {"fraud", "chargeback"}
        or "fraud" in reason
        or "vip" in customer_id
        or getattr(dispute, "status", None) == DisputeStatus.ESCALATED
    )


class DisputeRoutingService:
    """Centralize dispute routing decisions and persistence."""

    def route_dispute(self, dispute: Any, db: Optional[Any] = None, persist: bool = True) -> dict[str, Any]:
        queue = determine_queue(dispute)
        priority = determine_priority(dispute)
        escalated = should_escalate(dispute)

        current_status = getattr(dispute, "status", None)
        next_status = DisputeStatus.ESCALATED if escalated else DisputeStatus.OPEN

        if current_status in (None, DisputeStatus.NEW):
            setattr(dispute, "status", next_status)
        elif escalated and current_status != DisputeStatus.ESCALATED:
            setattr(dispute, "status", DisputeStatus.ESCALATED)

        result: dict[str, Any] = {
            "queue": queue,
            "priority": priority,
            "escalated": escalated,
            "status": getattr(dispute, "status", next_status),
        }

        if db is not None and persist:
            routing_log = RoutingLog(
                dispute_id=getattr(dispute, "id", None),
                source_system=SourceSystem.INTERNAL,
                destination=queue,
                status=RoutingStatus.SENT,
                details=(
                    f"Queue={queue}; priority={priority}; escalated={escalated}; "
                    f"status={getattr(dispute, 'status', next_status).value}"
                ),
                dispatched_at=datetime.utcnow(),
            )
            db.add(routing_log)
            db.commit()
            db.refresh(routing_log)
            result["routing_log"] = routing_log

        return result


def route_dispute(dispute: Any, db: Optional[Any] = None, persist: bool = True) -> dict[str, Any]:
    return DisputeRoutingService().route_dispute(dispute, db=db, persist=persist)
