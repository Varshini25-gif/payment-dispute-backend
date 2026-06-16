from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.database.connection import get_engine
from app.database.models import Dispute, RoutingLog
from app.database.models.enums import DisputeStatus, RoutingStatus
from app.database.session import SessionLocal
from app.services.dispute.routing_service import DisputeRoutingService

logger = logging.getLogger("app.workers.routing_worker")


class RoutingWorker:
    """Worker that retries failed route dispatch attempts and keeps route status up to date."""

    def retry_and_sync_routes(self) -> None:
        logger.info("Starting routing worker job")

        now = datetime.now(timezone.utc)
        retry_cutoff = now - timedelta(minutes=settings.ROUTING_RETRY_DELAY_MINUTES)
        stale_cutoff = now - timedelta(minutes=settings.ROUTING_SYNC_DELAY_MINUTES)

        retry_count = 0
        resynced_count = 0

        with SessionLocal(bind=get_engine()) as db:
            failed_logs = (
                db.query(RoutingLog)
                .filter(
                    RoutingLog.status.in_([RoutingStatus.FAILED, RoutingStatus.RETRY]),
                    RoutingLog.dispatched_at < retry_cutoff,
                )
                .all()
            )

            for log in failed_logs:
                dispute = log.dispute
                if dispute is None or dispute.status in (DisputeStatus.RESOLVED, DisputeStatus.CLOSED):
                    continue

                try:
                    log.status = RoutingStatus.RETRY
                    log.details = (
                        f"Retrying routing after failure. Original details: {log.details or 'none'}"
                    )
                    db.add(log)
                    db.commit()

                    DisputeRoutingService().route_dispute(dispute, db=db)
                    retry_count += 1
                    logger.info("Routing retry scheduled for dispute=%s", dispute.external_id)
                except Exception:  # pragma: no cover
                    db.rollback()
                    log.status = RoutingStatus.FAILED
                    log.details = f"Routing retry attempt failed: {log.details or 'none'}"
                    db.add(log)
                    db.commit()
                    logger.exception("Routing retry failed for dispute=%s", dispute.external_id)

            stale_disputes = (
                db.query(Dispute)
                .filter(
                    Dispute.status.in_([DisputeStatus.NEW, DisputeStatus.OPEN, DisputeStatus.ESCALATED]),
                    Dispute.updated_at < stale_cutoff,
                )
                .all()
            )

            for dispute in stale_disputes:
                try:
                    DisputeRoutingService().route_dispute(dispute, db=db)
                    resynced_count += 1
                    logger.info("Resynced stale dispute=%s", dispute.external_id)
                except Exception:  # pragma: no cover
                    db.rollback()
                    logger.exception("Failed to resync stale dispute=%s", dispute.external_id)

        logger.info(
            "Routing worker completed. retried=%d resynced=%d",
            retry_count,
            resynced_count,
        )
