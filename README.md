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

## API

- `GET /api/health` - health check endpoint