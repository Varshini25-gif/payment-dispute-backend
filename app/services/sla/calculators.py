from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def _coerce_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def calculate_elapsed_hours(start_at: Optional[datetime], end_at: Optional[datetime]) -> float:
    """Return elapsed time in hours between two timestamps."""
    start = _coerce_datetime(start_at)
    end = _coerce_datetime(end_at)
    if start is None or end is None:
        return 0.0
    return max(0.0, (end - start).total_seconds() / 3600)


def calculate_sla_metrics(
    created_at: Optional[datetime],
    updated_at: Optional[datetime] = None,
    sla_due_at: Optional[datetime] = None,
    resolved_at: Optional[datetime] = None,
) -> dict[str, object]:
    """Calculate response/resolution metrics and flag SLA breaches."""
    response_hours = calculate_elapsed_hours(created_at, updated_at or resolved_at or created_at)
    resolution_hours = calculate_elapsed_hours(created_at, resolved_at or updated_at or created_at)

    reference_time = resolved_at or updated_at or datetime.now(timezone.utc)
    is_breached = bool(sla_due_at is not None and reference_time >= sla_due_at)

    return {
        "response_hours": round(response_hours, 2),
        "resolution_hours": round(resolution_hours, 2),
        "is_breached": is_breached,
        "escalate": is_breached,
        "sla_due_at": sla_due_at,
    }
