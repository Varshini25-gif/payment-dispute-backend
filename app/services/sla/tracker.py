from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from app.database.models import SlaTracking
from app.database.models.enums import SlaStatus
from app.services.sla.alerts import SlaAlerts
from app.services.sla.breach_detector import detect_sla_breach
from app.services.sla.calculators import calculate_sla_metrics


class SlaTracker:
    """Track SLA metrics and persist threat or breach status."""

    def track(
        self,
        dispute: Any,
        db: Optional[Any] = None,
        created_at: Optional[datetime] = None,
        resolved_at: Optional[datetime] = None,
        sla_due_at: Optional[datetime] = None,
        notes: Optional[str] = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        created_at = created_at or getattr(dispute, "created_at", None) or datetime.now(timezone.utc)
        resolved_at = resolved_at or getattr(dispute, "resolved_at", None)
        if sla_due_at is None:
            sla_due_at = created_at + timedelta(hours=24)

        metrics = calculate_sla_metrics(
            created_at=created_at,
            updated_at=resolved_at,
            sla_due_at=sla_due_at,
            resolved_at=resolved_at,
        )

        breach = detect_sla_breach(due_at=sla_due_at, status=SlaStatus.ON_TRACK, now=resolved_at or datetime.now(timezone.utc))
        escalation = SlaAlerts.should_escalate(metrics) or breach["escalate"]

        record = None
        if db is not None and hasattr(db, "query"):
            record = db.query(SlaTracking).filter(SlaTracking.dispute_id == dispute.id).first()

        if record is None:
            record = SlaTracking(
                dispute_id=getattr(dispute, "id", None),
                sla_due_at=sla_due_at,
                sla_status=breach["status"],
                breached_at=sla_due_at if breach["breached"] else None,
                notes=notes,
                response_hours=Decimal(str(metrics["response_hours"])),
                resolution_hours=Decimal(str(metrics["resolution_hours"])),
                escalation_flag=escalation,
                escalation_reason=SlaAlerts.build_reason(metrics),
                breach_detected=bool(breach["breached"]),
            )
        else:
            record.sla_due_at = sla_due_at
            record.sla_status = breach["status"]
            record.breached_at = sla_due_at if breach["breached"] else record.breached_at
            record.notes = notes or record.notes
            record.response_hours = Decimal(str(metrics["response_hours"]))
            record.resolution_hours = Decimal(str(metrics["resolution_hours"]))
            record.escalation_flag = escalation
            record.escalation_reason = SlaAlerts.build_reason(metrics)
            record.breach_detected = bool(breach["breached"])

        if db is not None and persist:
            db.add(record)
            db.commit()
            db.refresh(record)

        return {
            "record": record,
            "response_hours": metrics["response_hours"],
            "resolution_hours": metrics["resolution_hours"],
            "breach_detected": breach["breached"],
            "sla_status": breach["status"],
            "escalate": escalation,
            "response_time_hours": metrics["response_hours"],
            "sla_hours_remaining": (
                round(max(0.0, (sla_due_at - (resolved_at or datetime.now(timezone.utc))).total_seconds() / 3600), 2)
                if sla_due_at is not None and not breach["breached"]
                else None
            ),
            "sla_hours_exceeded": (
                round(max(0.0, ((resolved_at or datetime.now(timezone.utc)) - sla_due_at).total_seconds() / 3600), 2)
                if sla_due_at is not None and breach["breached"]
                else None
            ),
        }
