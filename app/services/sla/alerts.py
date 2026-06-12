from __future__ import annotations

from typing import Any


class SlaAlerts:
    """Lightweight helper for escalation flags and reasons."""

    @staticmethod
    def should_escalate(metrics: dict[str, Any]) -> bool:
        return bool(metrics.get("escalate") or metrics.get("is_breached"))

    @staticmethod
    def build_reason(metrics: dict[str, Any]) -> str:
        if metrics.get("is_breached"):
            return "SLA window breached. Escalation required."
        if metrics.get("response_hours", 0) >= 4:
            return "Response time is approaching the SLA threshold."
        return "Within SLA threshold."
