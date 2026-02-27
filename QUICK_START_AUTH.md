# Quick Start: Authentication & Authorization

## 5-Minute Setup

### Step 1: Run Setup Script

```bash
source venv/bin/activate
python setup_auth_db.py
```

**Expected Output:**
```
🚀 Starting database setup...

📋 Setting up PostgreSQL roles...
✅ Created app_ro (read-only) role
✅ Created app_rw (read-write) role

📋 Creating tables...
✅ All tables created successfully

📋 Populating sample data...
✅ Created 2 sample tenants
✅ Created 3 sample sponsors
✅ Created 2 sample users
✅ Created 2 sample tenant-sponsor-user mappings
✅ Created 2 sample applications
✅ Created 2 sample license models
✅ Created 2 sample application feature domains
✅ Created 1 sample license
✅ Created 2 sample campaigns
✅ Created 2 sample tenant-sponsor-campaign mappings
✅ Created 1 sample customer entitlement
✅ Created 1 sample client entitlement
✅ Created 1 sample license product
✅ All sample data committed successfully!

============================================================
✨ Database setup completed successfully!
============================================================

📊 Connection Strings:
  Read-Only:  postgresql://app_ro:readonly_pass_123@localhost:5432/postgres
  Read-Write: postgresql://app_rw:readwrite_pass_123@localhost:5432/postgres

📋 Sample User Credentials:
  Admin:  cognito_user_id=user_cognito_001 (leadinsights_admin)
  Viewer: cognito_user_id=user_cognito_002 (viewer)
```

### Step 2: Start the Application

```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Generate JWT Token

Create a test script `test_auth.py`:

```python
import jwt
from datetime import datetime, timedelta
import json

# Generate JWT token
payload = {
    "username": "user_cognito_001",
    "client_id": "tenant_001",
    "tenant_id": "tenant_001",
    "exp": datetime.utcnow() + timedelta(hours=1)
}

# Note: In production, use proper secret key
token = jwt.encode(payload, "test-secret", algorithm="HS256")

print("Generated JWT Token:")
print(token)
print("\n" + "="*60)
print("\nUsage in curl:")
print(f'TOKEN="{token}"')
print('curl -X GET "http://localhost:8000/api/v1/campaigns/campaign_001/attendees" \\')
print('  -H "Authorization: Bearer $TOKEN" \\')
print('  -H "tenant_id: tenant_001"')
```

Run it:

```bash
python test_auth.py
```

### Step 4: Test API Endpoint

Using the token from Step 3:

```bash
TOKEN="<token_from_step_3>"

curl -X GET "http://localhost:8000/api/v1/campaigns/campaign_001/attendees" \
  -H "Authorization: Bearer $TOKEN" \
  -H "tenant_id: tenant_001" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "success": true,
  "message": "Retrieved 0 attendees for campaign campaign_001",
  "data": [],
  "total": 0,
  "timestamp": "2026-02-24T13:30:00.000Z"
}
```

## Testing Different Scenarios

### Test 1: Without Token

```bash
curl http://localhost:8000/api/v1/campaigns/campaign_001/attendees
```

Response: `401 Unauthorized`

### Test 2: Invalid Token

```bash
curl -X GET "http://localhost:8000/api/v1/campaigns/campaign_001/attendees" \
  -H "Authorization: Bearer invalid_token" \
  -H "tenant_id: tenant_001"
```

Response: `401 Token error: Invalid token`

### Test 3: Missing Tenant ID

```bash
TOKEN="<your_token>"
curl -X GET "http://localhost:8000/api/v1/campaigns/campaign_001/attendees" \
  -H "Authorization: Bearer $TOKEN"
```

Response: `401 Token error: Missing required token fields`

### Test 4: Health Check (No Auth)

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "environment": "development",
  "timestamp": "2026-02-24T13:30:00.000Z"
}
```

## Database Credentials

### Connect as Read-Only User

```bash
psql -U app_ro -h localhost -d postgres -W
# Password: readonly_pass_123
```

Try to create a table (should fail):
```sql
CREATE TABLE test (id INT);
-- ERROR: permission denied for schema test
```

### Connect as Read-Write User

```bash
psql -U app_rw -h localhost -d postgres -W
# Password: readwrite_pass_123
```

Insert data:
```sql
INSERT INTO test.campaigns VALUES ('campaign_003', 'New Campaign', NULL, NULL, NULL, 'active');
-- SUCCESS
```

## Sample User Details

### Admin User

```
Username (Cognito ID): user_cognito_001
Email: admin@example.com
Access Level: leadinsights_admin
Tenant: tenant_001
Sponsor: sponsor_001
```

### Viewer User

```
Username (Cognito ID): user_cognito_002
Email: viewer@example.com
Access Level: viewer
Tenant: tenant_001
Sponsor: sponsor_001
```

## Database Tables

View all tables in test schema:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'test'
ORDER BY table_name;
```

Output:
```
application_feature_domains
applications
campaign_attendees
campaigns
client_entitlements
customer_entitlements
license_models
license_products
licenses
sponsors
tenant_sponsor_campaigns
tenant_sponsor_users
tenants
users
```

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "relation does not exist" | Run `setup_auth_db.py` first |
| "password authentication failed" | Check PostgreSQL password in .env |
| "401 Unauthorized" | Generate valid JWT token |
| "Access denied" | User doesn't have access level for that domain |
| "Token expired" | Generate new token with future exp time |

## Next Steps

1. ✅ Complete setup above
2. Modify JWT secret in `app/middleware/auth_middleware.py` for production
3. Customize access levels for your business logic
4. Add more users to `tenant_sponsor_users` table
5. Create entitlements for users
6. Test with Postman or Swagger UI at http://localhost:8000/docs

## Interactive API Testing

Visit http://localhost:8000/docs and:

1. Click "Authorize" button
2. Select "OAuth2PasswordBearer" scheme
3. Enter your JWT token (prefixed with "Bearer ")
4. Try endpoints

## Files Structure

```
project/
├── app/
│   ├── models/
│   │   ├── auth_models.py        ← Database models
│   ├── middleware/
│   │   ├── auth_middleware.py    ← Auth logic
│   ├── main.py                    ← Middleware added
├── setup_auth_db.py               ← Run this first!
├── AUTH_SETUP.md                  ← Full documentation
└── QUICK_START_AUTH.md            ← This file
```

## Helpful Commands

```bash
# Check if tables exist
psql -U postgres -d postgres -c "\dt test.*"

# View sample user
psql -U app_rw -d postgres -c "SELECT * FROM test.users LIMIT 1;"

# Test read-only role (should fail INSERT)
psql -U app_ro -d postgres -c "INSERT INTO test.campaigns VALUES ('test', 'test', NULL, NULL, NULL, 'active');"

# Test read-write role (should succeed INSERT)
psql -U app_rw -d postgres -c "INSERT INTO test.campaigns VALUES ('test2', 'test', NULL, NULL, NULL, 'active');"
```

## Performance Notes

- Middleware checks authentication on every request (except whitelisted paths)
- Campaign entitlements are cached per request
- Domain access is validated against license status
- All queries use indexed fields for performance

---

**Done!** Your API is now protected with authentication and authorization. 🚀
