# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Production-ready FastAPI application with async PostgreSQL + SQLAlchemy ORM, Hashicorp Vault integration, JWT authentication, RBAC, multi-tenant support, and campaign management. The project uses a layered architecture with routers, services, queries, and schemas.

## Development Commands

### Setup & Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Development with auto-reload
./run.sh
# Or directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Database Setup
```bash
# Initialize database tables and sample data (creates PostgreSQL roles app_ro/app_rw)
python setup_auth_db.py
```

### Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## Architecture

### Layered Design
1. **Routers** (`app/routers/`) - HTTP endpoints, request/response validation, error handling
2. **Services** (`app/services/`) - Business logic, data validation, query orchestration
3. **Queries** (`app/queries/`) - Direct database operations with SQLAlchemy
4. **Schemas** (`app/schemas/`) - Pydantic models for request/response validation
5. **Models** (`app/models/`) - SQLAlchemy ORM models
6. **Middleware** (`app/middleware/`) - Auth/authorization, error handling

### Response Format
All endpoints return standardized JSON responses:
```json
{
  "success": true/false,
  "message": "description",
  "data": {},
  "error_code": "ERROR_CODE",
  "details": [{...}],
  "timestamp": "2026-02-25T...Z"
}
```

## Authentication & Authorization

### Overview
- JWT token-based auth (decoded without signature verification)
- Role-based access control (RBAC) via `tenant_sponsor_users` table
- Multi-tenant support with campaign entitlements
- PostgreSQL roles: `app_ro` (read-only), `app_rw` (read-write)

### Auth Flow
1. Extract JWT token from `Authorization: Bearer <token>` header
2. Extract `cognito_user_id` (from `username`/`sub`) and `tenant_id` from token or `tenant_id` header
3. Query `tenant_sponsor_users` for access level and sponsor mapping
4. Validate API domain/method access via `application_feature_domains` table
5. Get accessible campaigns from `customer_entitlements` table
6. Attach `auth_data` to `request.state` for use in endpoints

### Key Files
- `app/middleware/auth_middleware.py` - Auth logic, domain normalization, campaign entitlements
- `app/models/auth_models.py` - 14 database tables for auth/licensing
- `AUTH_SETUP.md` - Complete authentication documentation
- `setup_auth_db.py` - Database initialization with sample data

### Domain Path Normalization
Campaign IDs (e.g., `campaign_001`) are normalized to `{id}` placeholder for domain matching. The regex pattern recognizes:
- Numeric IDs: `123` → `{id}`
- UUIDs: `550e8400-e29b-41d4-a716-446655440000` → `{id}`
- Alphanumeric with underscores/dashes: `campaign_001`, `user-456` → `{id}`
- Literal routes unchanged: `/attendees` → `/attendees`

### Using Auth in Endpoints
```python
from app.middleware.auth_middleware import add_auth_context_to_request

async def your_endpoint(request: Request, session: AsyncSession = Depends(get_session)):
    is_authorized, auth_data, error_response = await add_auth_context_to_request(request, session)
    if not is_authorized:
        raise HTTPException(status_code=401, detail=error_response)
    # auth_data contains: user_id, cognito_user_id, tenant_id, sponsor_id, access_level, campaigns, etc.
```

## Database

### Configuration
Set via `.env` file:
```env
ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=fastapi_db
```

### Vault Integration (Optional)
```env
VAULT_ENABLED=true
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=s.xxxxx
VAULT_SECRET_PATH=secret/data/fastapi/database
```

### Tables (14 total)
**Core**: users, tenants, sponsors, applications, campaigns, license_models, tenant_sponsor_campaigns
**Auth**: tenant_sponsor_users, application_feature_domains, licenses, customer_entitlements, client_entitlements, license_products

### Sample Data
- 2 users: admin (user_cognito_001), viewer (user_cognito_002)
- 2 tenants: tenant_001, tenant_002
- 3 sponsors: sponsor_001, sponsor_002, sponsor_003
- 2 campaigns: campaign_001, campaign_002

## Campaign Endpoints

### GET /api/v1/campaigns/{campaign_id}/attendees
Paginated attendee list for a campaign. Requires JWT auth with campaign entitlement.
- Query params: `skip` (default 0), `limit` (default 50, max 100)
- Response: List of attendees with pagination info

### GET /api/v1/campaigns/{campaign_id}/attendees/search
Find specific attendee by email. Requires JWT auth.
- Query params: `email` (required)
- Response: Single attendee or 404

### GET /api/v1/campaigns/{campaign_id}/event-summary
Campaign summary (total attendees, companies). Requires JWT auth.
- Response: Event summary data

## Configuration & Environment

### env_file (.env)
Located at project root. Loaded automatically via `pydantic-settings`.

### Environment Variables
- `ENV`: "development" or "production" (controls reload, logging)
- `DB_*`: PostgreSQL connection details
- `VAULT_*`: Hashicorp Vault settings (optional)

## Adding New Features

### Adding a New Endpoint
1. Create model in `app/models/` if needed
2. Add Pydantic schemas in `app/schemas/`
3. Create database queries in `app/queries/`
4. Add business logic to `app/services/`
5. Add FastAPI routes to `app/routers/`
6. Include router in `app/main.py`

### Using Async/Await
- Always use `async def` for routes and service methods
- Use `await` with async operations (database queries, external APIs)
- Use `AsyncSession` for database operations
- Never use `asyncio.run()` inside async code

### Error Handling
- Use consistent error responses via `ErrorResponse` schema
- Attach error details via `ErrorDetail` list
- Log errors with context before raising HTTPException
- Use appropriate HTTP status codes (400, 401, 404, 500)

## Dependencies
- FastAPI 0.104.1
- Uvicorn 0.24.0
- SQLAlchemy 2.0.23 (async support)
- asyncpg 0.29.0 (PostgreSQL async driver)
- Pydantic 2.5.0
- python-dotenv 1.0.0
- hvac 1.2.1 (Vault client)
