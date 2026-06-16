from __future__ import annotations

import logging
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings

logger = logging.getLogger("app.core.scheduler")

scheduler = BackgroundScheduler(
    jobstores={"default": MemoryJobStore()},
    executors={"default": ThreadPoolExecutor(max_workers=4)},
    job_defaults={"coalesce": True, "max_instances": 1},
    timezone="UTC",
)


def _register_jobs() -> None:
    from app.workers.cleanup_worker import CleanupWorker
    from app.workers.routing_worker import RoutingWorker
    from app.workers.sla_worker import SlaMonitorWorker
    from app.workers.sync_worker import StaleDisputeScanner

    scheduler.add_job(
        SlaMonitorWorker().scan_and_update_sla,
        trigger="interval",
        seconds=settings.SLA_MONITOR_INTERVAL_SECONDS,
        id="sla_monitor",
        replace_existing=True,
    )
    scheduler.add_job(
        CleanupWorker().cleanup_stale_records,
        trigger="interval",
        seconds=settings.CLEANUP_INTERVAL_SECONDS,
        id="cleanup_worker",
        replace_existing=True,
    )
    scheduler.add_job(
        RoutingWorker().retry_and_sync_routes,
        trigger="interval",
        seconds=settings.ROUTING_SYNC_INTERVAL_SECONDS,
        id="routing_worker",
        replace_existing=True,
    )
    scheduler.add_job(
        StaleDisputeScanner().scan_stale_disputes,
        trigger="interval",
        seconds=settings.STALE_DISPUTE_SCAN_INTERVAL_SECONDS,
        id="stale_dispute_scanner",
        replace_existing=True,
    )


def start_scheduler() -> None:
    if scheduler.running:
        logger.debug("Scheduler already running")
        return

    _register_jobs()
    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))


def shutdown_scheduler(wait: bool = True) -> None:
    if not scheduler.running:
        logger.debug("Scheduler already stopped")
        return

    scheduler.shutdown(wait=wait)
    logger.info("Scheduler shutdown complete")
