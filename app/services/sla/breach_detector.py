from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.database.models.enums import SlaStatus


def detect_sla_breach(
    due_at: Optional[datetime],
    status: SlaStatus = SlaStatus.ON_TRACK,
    now: Optional[datetime] = None,
) -> dict[str, object]:
    """Return whether the dispute is at risk or already breached its SLA."""
    current_time = now or datetime.now(timezone.utc)
    if due_at is None:
        return {"status": status, "breached": False, "escalate": False}

    breached = current_time >= due_at
    if breached:
        status = SlaStatus.BREACHED
    elif current_time >= due_at - timedelta(hours=2):
        status = SlaStatus.AT_RISK

    escalate = breached or status == SlaStatus.AT_RISK

    return {
        "status": status,
        "breached": breached,
        "escalate": escalate,
    }
