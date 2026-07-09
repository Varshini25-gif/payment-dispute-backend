# Production Readiness Checklist

This checklist tracks production-critical work for the payment dispute backend.

## Application Health

- [x] Add liveness probe endpoint at /api/health/live.
- [x] Add readiness probe endpoint at /api/health/ready.
- [x] Add dependency-aware health endpoint at /api/health (database + scheduler checks).
- [x] Include UTC timestamp and environment in health responses.

## Database and Query Performance

- [x] Validate dispute amount range filters to avoid invalid query plans.
- [x] Add composite indexes for common list filters and sort patterns:
  - status + created_at
  - customer_id + created_at
  - currency + created_at
- [x] Track migration for index creation in Alembic revision 0004_dispute_query_indexes.

## Monitoring

- [x] Emit structured logs with correlation IDs for request tracing.
- [x] Persist API request audit logs for troubleshooting.
- [x] Expose health probes for container orchestrator monitoring.
- [x] Document deployment-time smoke checks and rollback path.

## Logging

- [x] Add slow request warning threshold via SLOW_REQUEST_THRESHOLD_MS.
- [x] Add high-signal warning logs for slow endpoints.
- [x] Redact auth/token request bodies from persisted audit logs.

## Deployment Validation

- [x] Validate container health checks in docker compose.
- [x] Verify migration execution as part of startup flow.
- [x] Validate endpoint health after deployment.
- [x] Validate log output and correlation ID propagation.

## Production Bug Fixes Completed

- [x] Prevent sensitive auth payloads from being stored in API request audit logs.
- [x] Improve health reporting to distinguish ok and degraded states.
- [x] Add readiness signal for dependency validation.
