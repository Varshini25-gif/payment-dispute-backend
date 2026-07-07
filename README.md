# payment-dispute-backend

## Overview

Payment dispute backend scaffolded with FastAPI, environment configuration, structured logging, and a health check endpoint.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy the environment sample:

```bash
copy .env.example .env
```

3. Initialize the database:

```bash
python -m app.database.create
```

4. Run Alembic migrations:

```bash
python -m alembic upgrade head
```

5. Start the app:

```bash
python -m uvicorn app.main:app --reload
```

## Docker Setup

1. Create a local environment file:

```bash
copy .env.example .env
```

2. Build and start backend + PostgreSQL:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

Or use the helper script (Windows PowerShell):

```powershell
./scripts/docker-up.ps1
```

3. Verify containers:

```bash
docker compose -f docker/docker-compose.yml ps
```

4. Stop and remove containers:

```bash
docker compose -f docker/docker-compose.yml down
```

Or use:

```powershell
./scripts/docker-down.ps1
```

## API

- `GET /api/health` - health check endpoint

## Confluence Integration

Configure these environment variables before publishing case summaries:

- `CONFLUENCE_BASE_URL` - Atlassian site URL (example: `https://your-org.atlassian.net`)
- `CONFLUENCE_EMAIL` - account email used for Confluence API access
- `CONFLUENCE_API_TOKEN` - Atlassian API token
- `CONFLUENCE_SPACE_KEY` - Confluence space key where pages are created
- `CONFLUENCE_PARENT_PAGE_ID` - optional default parent page ID for new summaries

Confluence API endpoints:

- `POST /api/confluence/disputes/{dispute_id}/publish` - publish a dispute case summary
- `GET /api/confluence/disputes/{dispute_id}/posts` - list all publish attempts/pages
- `GET /api/confluence/disputes/{dispute_id}/publish-status` - get latest publish status
- `GET /api/confluence/posts/{post_id}` - fetch a Confluence post record