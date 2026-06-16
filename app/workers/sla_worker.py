from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.database.connection import get_engine
from app.database.models import Dispute
from app.database.models.enums import DisputeStatus
from app.database.session import SessionLocal
from app.services.sla.tracker import SlaTracker

logger = logging.getLogger("app.workers.sla_worker")


class SlaMonitorWorker:
    """Worker that scans disputes and persists SLA tracking state."""

    def scan_and_update_sla(self) -> None:
        logger.info("Starting SLA monitor job")

        with SessionLocal(bind=get_engine()) as db:
            query = db.query(Dispute).filter(
                Dispute.status.in_(
                    [
                        DisputeStatus.NEW,
                        DisputeStatus.OPEN,
                        DisputeStatus.ESCALATED,
                        DisputeStatus.RESOLVED,
                    ]
                )
            )
            disputes = query.all()

            updated = 0
            for dispute in disputes:
                try:
                    result = SlaTracker().track(dispute, db=db)
                    logger.info(
                        "SLA updated dispute=%s status=%s breached=%s escalate=%s",
                        dispute.external_id,
                        result["sla_status"].value,
                        result["breach_detected"],
                        result["escalate"],
                    )
                    updated += 1
                except Exception:  # pragma: no cover
                    logger.exception("Failed to update SLA tracking for dispute=%s", dispute.external_id)

        logger.info("SLA monitor job completed. Disputes scanned=%d", updated)
