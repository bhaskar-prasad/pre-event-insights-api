# FastAPI PostgreSQL Template

A production-ready template for building async APIs with FastAPI, PostgreSQL, SQLAlchemy ORM, and Hashicorp Vault integration.

## Features

- ✅ **Async/Await Throughout** - Full async support with async SQLAlchemy and AsyncSession
- ✅ **PostgreSQL with SQLAlchemy ORM** - Type-safe database operations
- ✅ **Consistent JSON Responses** - Standardized error and success response formats
- ✅ **Structured Repository** - Organized into routers, services, and queries layers
- ✅ **Vault Integration** - Fetch database credentials securely from Hashicorp Vault
- ✅ **Environment Configuration** - Easy configuration via environment variables
- ✅ **Schema-Based Responses** - Pydantic schemas for all API responses
- ✅ **Error Handling** - Global exception handling with consistent error responses

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application setup
│   ├── config.py            # Configuration management
│   ├── database.py          # Database initialization and session management
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── base.py          # Base response schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   └── example.py       # Example API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── example.py       # Business logic layer
│   └── queries/
│       ├── __init__.py
│       └── example.py       # Database queries layer
├── .env.example             # Example environment variables
├── .gitignore
├── requirements.txt         # Python dependencies
└── README.md
```

## Architecture Layers

### 1. **Routers** (`app/routers/`)
- FastAPI route handlers
- Request/response validation
- HTTP status codes and error handling
- Dependency injection for database sessions

### 2. **Services** (`app/services/`)
- Business logic layer
- Data validation and processing
- Orchestration of queries
- Error handling and logging

### 3. **Queries** (`app/queries/`)
- Direct database operations
- SQLAlchemy query building
- Pure data access without business logic

### 4. **Schemas** (`app/schemas/`)
- Pydantic models for request/response validation
- Consistent error response format
- Type safety and documentation

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Hashicorp Vault (optional, if using Vault for credentials)

### Installation

1. **Clone and setup the project:**

```bash
cd /Users/bhaskar.prasad/Desktop/github/claude-code
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables:**

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
ENV=development

# Database credentials
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=fastapi_db

# Vault configuration (optional)
VAULT_ENABLED=false
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=your_vault_token
VAULT_SECRET_PATH=secret/data/fastapi/database
```

### Database Setup

1. **Create PostgreSQL database:**

```bash
createdb fastapi_db
```

2. **Run migrations** (if using Alembic - add later):

```bash
# alembic upgrade head
```

## Running the Application

### Development

```bash
python -m app.main
```

Or with Uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The application will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Using Hashicorp Vault

### Setup Vault Secret

1. **Start Vault** (if running locally):

```bash
vault server -dev
```

2. **Set database credentials in Vault:**

```bash
vault kv put secret/fastapi/database \
  username=postgres \
  password=your_password \
  host=localhost \
  port=5432 \
  database=fastapi_db
```

3. **Configure environment**:

```env
VAULT_ENABLED=true
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=s.xxxxxxxxxxxxxxxx
VAULT_SECRET_PATH=secret/data/fastapi/database
```

## API Response Format

### Success Response

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": 1,
    "name": "Example"
  },
  "timestamp": "2024-02-24T10:30:00.000Z"
}
```

### Error Response

```json
{
  "success": false,
  "message": "Item not found",
  "error_code": "NOT_FOUND",
  "details": [
    {
      "field": null,
      "message": "Item with ID 999 not found",
      "code": null
    }
  ],
  "timestamp": "2024-02-24T10:30:00.000Z"
}
```

## Adding New Features

### 1. Create a Database Model

Create `app/models/example.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 2. Create Request/Response Schemas

Create `app/schemas/example.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ExampleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ExampleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
```

### 3. Update Queries Layer

Update `app/queries/example.py`:

```python
from app.models.example import Example

async def get_by_id(session: AsyncSession, id: int):
    result = await session.execute(
        select(Example).where(Example.id == id)
    )
    return result.scalar_one_or_none()
```

### 4. Update Service Layer

Update `app/services/example.py` to use the models and validate business logic.

### 5. Update Router

Update `app/routers/example.py` to use the new schemas and service methods.

## Database Migrations (with Alembic)

### Initialize Alembic

```bash
alembic init migrations
```

### Create a Migration

```bash
alembic revision --autogenerate -m "Add examples table"
```

### Apply Migrations

```bash
alembic upgrade head
```

## Testing

Create `tests/test_routers.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| ENV | No | development | Environment (development/production) |
| DB_HOST | No | localhost | PostgreSQL host |
| DB_PORT | No | 5432 | PostgreSQL port |
| DB_USER | No | postgres | PostgreSQL user |
| DB_PASSWORD | No | "" | PostgreSQL password |
| DB_NAME | No | fastapi_db | Database name |
| VAULT_ENABLED | No | false | Enable Vault integration |
| VAULT_ADDR | No | http://localhost:8200 | Vault address |
| VAULT_TOKEN | No | "" | Vault token |
| VAULT_SECRET_PATH | No | secret/data/fastapi/database | Vault secret path |

## Logging

The application uses Python's built-in logging module. Configure logging in `app/main.py`.

## Best Practices

1. **Always use async/await** - Use `async def` and `await` for all I/O operations
2. **Session management** - Use `Depends(get_session)` to manage database sessions automatically
3. **Error handling** - Use consistent error responses with appropriate HTTP status codes
4. **Validation** - Validate at boundaries (API endpoints), trust internal code
5. **Security** - Store sensitive data in Vault, never commit `.env` files
6. **Logging** - Log important operations and errors for debugging

## Troubleshooting

### Connection refused to Vault

- Ensure Vault is running: `vault status`
- Check VAULT_ADDR is correct
- Verify VAULT_TOKEN is valid

### Database connection errors

- Verify PostgreSQL is running
- Check DATABASE_URL or credentials are correct
- Ensure database exists: `psql -l`

### Async errors

- Always use `await` with async functions
- Never use `asyncio.run()` inside async code
- Use `AsyncSession` from SQLAlchemy

## License

MIT

## Support

For issues or questions, refer to:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Hashicorp Vault Documentation](https://www.vaultproject.io/docs)
