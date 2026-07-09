# Monitoring and Logging

This document defines practical monitoring for the payment dispute backend.

## Health Endpoints

Use these for uptime and dependency monitoring:

- GET /api/health/live
  - Purpose: process liveness.
- GET /api/health/ready
  - Purpose: dependency readiness (database checks).
- GET /api/health
  - Purpose: full health details including checks and metadata.

Recommended alert conditions:

- /api/health/ready status != ready for 5 minutes.
- /api/health status == degraded for 5 minutes.

## Logging Strategy

The service uses structured logs and request context fields:

- correlation_id
- request_id
- method
- path
- status_code
- duration_ms
- client_ip

Configuration:

- LOG_LEVEL (default INFO)
- LOG_JSON (default true)
- SLOW_REQUEST_THRESHOLD_MS (default 1500)

Slow request detection:

- Requests exceeding SLOW_REQUEST_THRESHOLD_MS generate warning logs with request metadata.

## Audit Logging

API request traces are persisted in the apirequestlog table.

Captured fields include:

- method, path, query_string
- status_code, duration_ms
- actor, user_agent, client_ip
- correlation_id, request_id
- metadata_json

Security controls:

- Request bodies for sensitive auth/token/password routes are not persisted.

## Database Monitoring

Track:

- Connection pool saturation and timeout events.
- Query latency for /api/disputes list endpoint.
- Growth of apirequestlog and retention policy compliance.

Index coverage added for dispute list access patterns:

- ix_dispute_status_created_at
- ix_dispute_customer_created_at
- ix_dispute_currency_created_at

## Operational Dashboards

Minimum dashboard panels:

1. API request volume by path.
2. Request latency p50/p95/p99.
3. Error rate by status_code.
4. Slow request warning count.
5. Readiness and full-health status over time.

## Incident Triage Flow

1. Check readiness and full health endpoints.
2. Filter logs by correlation_id.
3. Review recent apirequestlog failures and duration spikes.
4. Validate database connectivity and pool health.
5. Roll back release if health remains degraded.
