# Deployment Guide

This guide describes a production-like deployment flow for the backend.

## 1. Pre-Deployment

1. Ensure environment variables are set in .env.
2. Ensure database is reachable from the target runtime.
3. Ensure migrations are up to date.
4. Ensure image build succeeds.

Required environment variables (minimum):

- APP_NAME
- ENVIRONMENT
- DATABASE_URL
- SECRET_KEY
- LOG_LEVEL
- LOG_JSON

Optional production tuning:

- DB_POOL_SIZE
- DB_MAX_OVERFLOW
- DB_POOL_TIMEOUT
- DB_POOL_RECYCLE
- DB_POOL_PRE_PING
- SLOW_REQUEST_THRESHOLD_MS
- HEALTH_DB_CHECK_ENABLED

## 2. Build and Start

From repository root:

1. Build and start services:
   - docker compose -f docker/docker-compose.yml up --build -d
2. Confirm containers:
   - docker compose -f docker/docker-compose.yml ps
3. Verify backend logs:
   - docker compose -f docker/docker-compose.yml logs backend --tail=100

## 3. Migration Validation

1. Ensure Alembic has applied latest migration:
   - docker compose -f docker/docker-compose.yml exec backend alembic current
2. Expected current revision includes:
   - 0004_dispute_query_indexes

## 4. Health Validation (Smoke Test)

Run these checks after startup:

1. Liveness:
   - GET /api/health/live
2. Readiness:
   - GET /api/health/ready
3. Full health:
   - GET /api/health

Expected behavior:

- Liveness returns status=ok.
- Readiness returns status=ready when database is available.
- Full health returns status=ok or status=degraded with check details.

## 5. Functional Validation

1. Basic API path:
   - GET /api/disputes
2. Auth path:
   - POST /api/auth/login
3. Create path:
   - POST /api/disputes

## 6. Rollback Plan

1. Roll back application image to previous known-good tag.
2. If needed, roll back migration:
   - alembic downgrade -1
3. Re-run health endpoints and confirm readiness.

## 7. Post-Deployment Checks

1. Confirm error rate and latency in logs.
2. Confirm slow-request warnings are within expected baseline.
3. Confirm correlation ID appears in response headers and logs.
4. Confirm no sensitive auth payloads are present in persisted API request logs.
