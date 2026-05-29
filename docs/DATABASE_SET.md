# Database Setup - PostgreSQL & SQLAlchemy Configuration

## Overview

This document describes the database setup for the Payment Dispute Backend application, including PostgreSQL connection, SQLAlchemy configuration, and session management.

## Architecture

```
app/database/
├── __init__.py          # Module exports
├── connection.py        # PostgreSQL connection & engine setup
├── session.py           # Session management & factories
├── create.py            # Database initialization
├── models/
│   ├── __init__.py      # Models exports
│   ├── base.py          # Base model class
│   └── *.py             # Individual models
```

## Components

### 1. connection.py - PostgreSQL Connection Setup

**Purpose**: Creates and configures the SQLAlchemy engine with PostgreSQL.

**Features**:
- **Engine Configuration**: Connects to PostgreSQL with `create_engine()`
- **Connection Pooling**: Uses QueuePool for efficient connection management
- **Pool Parameters**:
  - `pool_size=20`: Base pool connections
  - `max_overflow=10`: Additional overflow connections
  - `pool_timeout=30`: Wait time for connection availability
  - `pool_recycle=3600`: Recycle connections every hour
  - `pool_pre_ping=True`: Verify connection health before use
- **Event Listeners**: Registers connection lifecycle handlers

**Usage**:
```python
from app.database import engine
# Engine is ready for use
```

### 2. session.py - Database Session Management

**Purpose**: Provides session factory and dependency injection for FastAPI.

**Key Components**:

#### SessionLocal Factory
```python
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    future=True,
)
```

#### get_db_session() - FastAPI Dependency
```python
from fastapi import Depends
from app.database import get_db_session

@app.get("/items/")
def read_items(db: Session = Depends(get_db_session)):
    return db.query(Item).all()
```

**Session Configuration**:
- `expire_on_commit=False`: Keep model instances after commit
- `autoflush=False`: Manual flush control
- `autocommit=False`: Explicit transaction management

### 3. connection.py - Base Model

The base model in `models/base.py` provides:

```python
@as_declarative()
class Base:
    """Base class for all ORM models"""
    __tablename__  # Automatically generated from class name
    __table_args__  # Empty tuple for table arguments
```

**Custom Types**:
- `GUID`: Cross-database UUID type that uses PostgreSQL's native UUID and CHAR(36) for others

### 4. create.py - Database Initialization

**Functions**:
- `init_db()`: Creates all tables based on models
- `drop_db()`: Drops all tables (use with caution)

**Usage**:
```python
python -m app.database.create
# or
from app.database.create import init_db
init_db()
```

## Configuration (config.py)

Database settings in `app/core/config.py`:

```python
DATABASE_URL: str = "postgresql://user:password@localhost:5432/payment_dispute_db"
DB_ECHO: bool = False                 # Log SQL statements
DB_POOL_SIZE: int = 20                # Base pool size
DB_MAX_OVERFLOW: int = 10             # Overflow connections
DB_POOL_TIMEOUT: int = 30             # Connection wait timeout (seconds)
DB_POOL_RECYCLE: int = 3600           # Connection recycle time (seconds)
DB_POOL_PRE_PING: bool = True         # Verify connections before use
DB_FUTURE: bool = True                # Enable SQLAlchemy 2.0 behavior
```

All settings are loaded from `.env` file.

## Environment Configuration

Create a `.env` file with your database credentials:

```bash
# PostgreSQL Connection
DATABASE_URL=postgresql://user:password@localhost:5432/payment_dispute_db

# Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

See `.env.example` for all available options.

## Connection Pool Explained

### Why Connection Pooling?
- **Performance**: Reuse existing connections instead of creating new ones
- **Resource Management**: Limit concurrent connections
- **Stability**: Handle connection failures gracefully

### Pool Parameters:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `pool_size` | 20 | Number of connections to keep in pool |
| `max_overflow` | 10 | Additional connections when pool exhausted |
| `pool_timeout` | 30 | Seconds to wait for available connection |
| `pool_recycle` | 3600 | Recycle connections after N seconds (prevents stale connections) |
| `pool_pre_ping` | True | Execute "SELECT 1" before using connection |

### Example Scenarios:
```
Scenario 1: 15 concurrent requests
- Requests 1-15 use pool connections (no wait)
- New connections created from pool

Scenario 2: 25 concurrent requests
- Requests 1-20 use pool connections
- Requests 21-25 use overflow (up to max_overflow=10 allowed)
- Request 26+ waits until connection available (timeout: 30s)

Scenario 3: Connection idle > 3600s
- Connection recycled (new connection created)
- Prevents "connection lost" errors
```

## Models

All models inherit from `Base`:

```python
from app.database.models.base import Base

class Dispute(Base):
    __tablename__ = "disputes"
    
    id = Column(GUID, primary_key=True, default=uuid4)
    status = Column(String, nullable=False)
    # ...
```

## Usage Examples

### In API Routes
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db_session
from app.database.models import Dispute

router = APIRouter()

@router.get("/disputes/")
def list_disputes(db: Session = Depends(get_db_session)):
    disputes = db.query(Dispute).all()
    return disputes
```

### In Services
```python
from app.database import SessionLocal
from app.database.models import Dispute

def create_dispute(data: dict):
    db = SessionLocal()
    try:
        dispute = Dispute(**data)
        db.add(dispute)
        db.commit()
        db.refresh(dispute)
        return dispute
    finally:
        db.close()
```

### Database Initialization
```bash
# Initialize all tables
python -m app.database.create

# Or in code
from app.database.create import init_db
init_db()
```

## Troubleshooting

### "Could not connect to PostgreSQL"
- Check `DATABASE_URL` format
- Verify PostgreSQL is running
- Check credentials and database exists

### "QueuePool limit exceeded"
- Increase `DB_POOL_SIZE` or `DB_MAX_OVERFLOW`
- Check for connection leaks (not closing sessions)

### "Connection closed" errors
- Increase `DB_POOL_RECYCLE`
- Enable `DB_POOL_PRE_PING=true`

## Dependencies

```
SQLAlchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.11.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Tasks Completed

✅ **Setup PostgreSQL Connection** - Configured in `connection.py` with proper pooling
✅ **Configure SQLAlchemy** - Engine created with optimal settings in `config.py`
✅ **Setup DB Sessions** - Session factory and dependency injection in `session.py`
✅ **Configure Engine Pooling** - QueuePool with customizable parameters
✅ **Add Base Model** - Located in `models/base.py` with GUID support

## Next Steps

1. Create `.env` file from `.env.example` with your PostgreSQL credentials
2. Run `python -m app.database.create` to initialize tables
3. Start using sessions in your API routes with `Depends(get_db_session)`
4. Use Alembic for schema migrations: `alembic revision --autogenerate`
