from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.core.config import settings
from app.database.connection import get_engine
from app.database.models import Dispute, RoutingLog
from app.database.models.enums import DisputeStatus
from app.database.session import SessionLocal

logger = logging.getLogger("app.workers.cleanup_worker")


class CleanupWorker:
    """Worker that removes stale dispute records and old routing logs."""

    def run(self) -> None:
        self.cleanup_stale_records()

    def cleanup_stale_records(self) -> None:
        logger.info("Starting cleanup worker job")

        now = datetime.now(timezone.utc)
        dispute_threshold = now - timedelta(days=settings.CLEANUP_DISPUTE_RETENTION_DAYS)
        log_threshold = now - timedelta(days=settings.CLEANUP_LOG_RETENTION_DAYS)

        deleted_disputes = 0
        deleted_logs = 0

        with SessionLocal(bind=get_engine()) as db:
            stale_disputes = (
                db.query(Dispute)
                .filter(
                    Dispute.status.in_([DisputeStatus.RESOLVED, DisputeStatus.CLOSED]),
                    Dispute.updated_at < dispute_threshold,
                )
                .all()
            )

            for dispute in stale_disputes:
                db.delete(dispute)
                deleted_disputes += 1

            if deleted_disputes:
                db.commit()

            result = db.execute(delete(RoutingLog).where(RoutingLog.created_at < log_threshold))
            deleted_logs = result.rowcount or 0

            if deleted_logs:
                db.commit()

        logger.info(
            "Cleanup worker completed. Disputes deleted=%d, routing logs deleted=%d",
            deleted_disputes,
            deleted_logs,
        )
