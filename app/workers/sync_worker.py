from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.database.connection import get_engine
from app.database.models import Dispute
from app.database.models.enums import DisputeStatus
from app.database.session import SessionLocal
from app.services.dispute.routing_service import DisputeRoutingService
from app.services.sla.tracker import SlaTracker

logger = logging.getLogger("app.workers.sync_worker")


class StaleDisputeScanner:
    """Worker that identifies stale disputes and escalates or re-routes them."""

    def run(self) -> None:
        self.scan_stale_disputes()

    def sync(self) -> None:
        self.scan_stale_disputes()

    def scan_stale_disputes(self) -> None:
        logger.info("Starting stale dispute scanner job")

        now = datetime.now(timezone.utc)
        stale_threshold = now - timedelta(hours=settings.STALE_DISPUTE_AGE_HOURS)

        with SessionLocal(bind=get_engine()) as db:
            stale_disputes = (
                db.query(Dispute)
                .filter(
                    Dispute.status.in_([DisputeStatus.NEW, DisputeStatus.OPEN]),
                    Dispute.updated_at < stale_threshold,
                )
                .all()
            )

            scanned = 0
            for dispute in stale_disputes:
                try:
                    dispute.status = DisputeStatus.ESCALATED
                    db.add(dispute)
                    SlaTracker().track(dispute, db=db)
                    DisputeRoutingService().route_dispute(dispute, db=db)
                    scanned += 1
                    logger.info("Escalated stale dispute=%s", dispute.external_id)
                except Exception:  # pragma: no cover
                    db.rollback()
                    logger.exception("Failed to process stale dispute=%s", dispute.external_id)

        logger.info("Stale dispute scanner completed. scanned=%d", scanned)


# Backward-compatible alias kept for older imports/tests.
class SyncWorker(StaleDisputeScanner):
    pass
