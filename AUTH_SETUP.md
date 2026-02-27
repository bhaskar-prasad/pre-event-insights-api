# Authentication & Authorization Setup Guide

Complete guide for setting up authentication, authorization, and database with PostgreSQL roles.

## Overview

This authentication system includes:
- JWT token-based authentication
- Role-based access control (RBAC)
- Campaign entitlement management
- PostgreSQL read-only and read-write roles
- Multi-tenant support

## Database Models

### Core Models

| Table | Purpose |
|-------|---------|
| `users` | User accounts with Cognito integration |
| `tenants` | Multi-tenant support |
| `sponsors` | Business sponsors/clients |
| `applications` | Applications with features |
| `campaigns` | Marketing campaigns |
| `license_models` | License definitions |

### Authorization Models

| Table | Purpose |
|-------|---------|
| `tenant_sponsor_users` | User access levels per tenant/sponsor |
| `application_feature_domains` | API domain/method access control |
| `licenses` | Sponsor licenses for applications |
| `customer_entitlements` | User-level campaign access |
| `client_entitlements` | Division/family/brand level access |
| `license_products` | Campaign-specific products |
| `tenant_sponsor_campaigns` | Campaign ownership mapping |

## Setup Instructions

### 1. Create Database Tables and Roles

```bash
# From the project root directory
source venv/bin/activate
python setup_auth_db.py
```

This script will:
- Create PostgreSQL roles:
  - `app_ro`: Read-only access
  - `app_rw`: Read-write access
- Create all database tables
- Populate sample data

### 2. PostgreSQL Roles

**Read-Only Role (app_ro):**
```
Username: app_ro
Password: readonly_pass_123
Permissions: SELECT only
```

**Read-Write Role (app_rw):**
```
Username: app_rw
Password: readwrite_pass_123
Permissions: SELECT, INSERT, UPDATE, DELETE
```

### 3. Sample Data Created

**Users:**
- Admin: cognito_user_id=`user_cognito_001`, email=`admin@example.com`
- Viewer: cognito_user_id=`user_cognito_002`, email=`viewer@example.com`

**Tenants:**
- `tenant_001`: Acme Corporation
- `tenant_002`: TechCorp Inc

**Sponsors:**
- `sponsor_001`: Sales Sponsor (tenant_001)
- `sponsor_002`: Marketing Sponsor (tenant_001)
- `sponsor_003`: Tech Sponsor (tenant_002)

**Campaigns:**
- `campaign_001`: Summer Campaign 2024
- `campaign_002`: Winter Campaign 2024

## Authentication Flow

### 1. JWT Token Format

```json
{
  "username": "user_cognito_001",
  "client_id": "tenant_001",
  "tenant_id": "tenant_001",
  "exp": 1234567890
}
```

### 2. Request Headers

```http
Authorization: Bearer <jwt_token>
tenant_id: tenant_001
sponsor_id: sponsor_001 (optional)
```

### 3. Authentication Process

1. Extract JWT from Authorization header
2. Decode token to get `username` and `tenant_id`
3. Query `tenant_sponsor_users` for access level
4. Validate domain/method access
5. Get accessible campaigns
6. Attach auth data to request context

## API Endpoints with Authentication

### Campaign Endpoints (Protected)

All endpoints require:
- Valid JWT token
- tenant_id header
- User must have at least "viewer" access level

```
GET /api/v1/campaigns/{campaign_id}/attendees
GET /api/v1/campaigns/{campaign_id}/attendees/search
GET /api/v1/campaigns/{campaign_id}/event-summary
```

### Health Check (No Auth Required)

```
GET /api/v1/health
GET /health
```

## Testing Authentication

### 1. Generate a Test JWT Token

```python
import jwt
from datetime import datetime, timedelta

payload = {
    "username": "user_cognito_001",
    "client_id": "tenant_001",
    "tenant_id": "tenant_001",
    "exp": datetime.utcnow() + timedelta(hours=1)
}

token = jwt.encode(payload, "secret_key", algorithm="HS256")
print(token)
```

### 2. Test API with Token

```bash
# Using curl
TOKEN="<your_jwt_token>"
curl -X GET "http://localhost:8000/api/v1/campaigns/campaign_001/attendees" \
  -H "Authorization: Bearer $TOKEN" \
  -H "tenant_id: tenant_001"
```

### 3. Test with Sample Data

```bash
# Using Python
import httpx
import jwt
from datetime import datetime, timedelta

# Generate token
payload = {
    "username": "user_cognito_001",
    "client_id": "tenant_001",
    "tenant_id": "tenant_001",
    "exp": datetime.utcnow() + timedelta(hours=1)
}
token = jwt.encode(payload, "secret", algorithm="HS256")

# Make request
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/campaigns/campaign_001/attendees",
        headers={
            "Authorization": f"Bearer {token}",
            "tenant_id": "tenant_001"
        }
    )
    print(response.json())
```

## Access Levels

| Level | Permissions |
|-------|------------|
| `leadinsights_admin` | Full access to all features and campaigns |
| `admin` | Admin-level access to sponsor campaigns |
| `viewer` | Read-only access to assigned campaigns |
| `editor` | Read-write access to assigned campaigns |

## Authorization Rules

### Campaign Access

Users can access campaigns if:
1. They have an active `tenant_sponsor_users` record
2. Campaign has a `tenant_sponsor_campaigns` mapping
3. User has a `customer_entitlements` record for the campaign
4. User's `client_entitlements` match campaign division/family/brand

### Domain Access

Endpoints are protected based on:
1. `application_feature_domains` entries
2. Active license for the sponsor
3. Correct HTTP method (GET, POST, etc.)

## Database Connection

### Using Read-Only Role

```python
from app.config import settings

DB_URL = "postgresql+asyncpg://app_ro:readonly_pass_123@localhost:5432/postgres"
```

### Using Read-Write Role

```python
DB_URL = "postgresql+asyncpg://app_rw:readwrite_pass_123@localhost:5432/postgres"
```

## Middleware Integration

The middleware is integrated in `app/main.py`:

```python
from app.middleware.auth_middleware import authorization_middleware

app.add_middleware(authorization_middleware)
```

### Using Auth in Endpoints

```python
from fastapi import Depends
from app.middleware.auth_middleware import add_auth_context_to_request
from app.database import get_session

@router.get("/protected")
async def protected_endpoint(session: AsyncSession = Depends(get_session)):
    request: Request = ...  # Injected by FastAPI
    is_auth, auth_data, error = await add_auth_context_to_request(request, session)

    if not is_auth:
        return error

    user_id = auth_data["user_id"]
    campaigns = auth_data["campaigns"]
    # ... use auth_data
```

## Error Responses

### Unauthorized (401)

```json
{
  "success": false,
  "message": "Unauthorized access",
  "error_code": "AUTH_ERROR",
  "details": [
    {
      "field": null,
      "message": "Token expired",
      "code": null
    }
  ],
  "timestamp": "2026-02-24T13:30:00.000Z"
}
```

### Access Denied (401)

```json
{
  "success": false,
  "message": "Access denied",
  "error_code": "AUTH_ERROR",
  "details": [
    {
      "field": null,
      "message": "User does not have access to this resource",
      "code": null
    }
  ],
  "timestamp": "2026-02-24T13:30:00.000Z"
}
```

## Security Best Practices

1. **Token Validation**
   - Always validate token signature (disable in test only)
   - Check token expiration
   - Verify tenant_id in token matches request

2. **Database Access**
   - Use `app_ro` role for read-only operations
   - Use `app_rw` role for write operations
   - Don't use superuser credentials in application

3. **Secrets Management**
   - Store JWT secret in Vault
   - Use environment variables for credentials
   - Never commit secrets to version control

4. **Rate Limiting**
   - Implement rate limiting on auth endpoints
   - Monitor failed auth attempts
   - Block suspicious IPs

## Troubleshooting

### "Token not found" Error

```
Check:
1. Authorization header is present
2. Format is "Bearer <token>"
3. Token is not expired
```

### "Access Denied" Error

```
Check:
1. User exists in tenant_sponsor_users
2. Status is "accepted"
3. tenant_id header matches token
4. User has entitlements for the campaign
```

### "Database Connection Failed"

```
Check:
1. PostgreSQL is running
2. Database credentials are correct
3. Role (app_ro/app_rw) exists and has permissions
4. Vault credentials are correct if using Vault
```

## Next Steps

1. ✅ Run `python setup_auth_db.py`
2. ✅ Start the application
3. ✅ Generate JWT token with sample user
4. ✅ Test endpoints with token
5. ✅ Customize access levels for your use case
6. ✅ Configure JWT secret in production
7. ✅ Set up token refresh mechanism

## Files Created

```
app/
├── models/
│   ├── auth_models.py          # Database models
├── middleware/
│   ├── auth_middleware.py      # Authentication logic
│   └── __init__.py
app/main.py                       # Middleware integration
setup_auth_db.py                  # Database setup script
AUTH_SETUP.md                     # This file
```

## References

- [JWT.io](https://jwt.io)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [PostgreSQL Roles](https://www.postgresql.org/docs/current/user-manag.html)
