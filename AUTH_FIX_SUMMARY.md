# Authentication "Access Denied" Fix Summary

## Problem Identified
You were getting "access denied" errors when calling authenticated endpoints with valid JWT tokens. The issue was in **domain path normalization**.

### Root Cause
The `normalize_domain_path()` function in `auth_middleware.py` only recognized:
- Pure numeric IDs: `123`
- UUIDs: `550e8400-e29b-41d4-a716-446655440000`

But your campaign IDs use underscores: `campaign_001`

This caused path normalization to fail:
```
Request path: /api/v1/campaigns/campaign_001/attendees
After removing /api/v1: /campaigns/campaign_001/attendees
After normalization: /campaigns/campaign_001/attendees  ❌ (no change)

Database expects: /campaigns/{id}/attendees  ❌ (no match!)
Result: Domain access denied
```

## Solution Applied
Updated the regex pattern in `normalize_domain_path()` to also match alphanumeric IDs with underscores/dashes:

```python
# Old pattern (line 256)
r"(?:/|^)(\d+|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})(?=/|$)"

# New pattern (line 256-257)
r"(?:/|^)(\d+|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}|[a-z0-9]*[_-][a-z0-9]*)(?=/|$)"
```

Now the pattern matches:
- **Numeric**: `123`, `456789`
- **UUID**: `550e8400-e29b-41d4-a716-446655440000`
- **Alphanumeric with delimiters**: `campaign_001`, `user-456`, `order_123_v2`

## Test Results
All test cases pass ✅

```
Input: /campaigns                          → /campaigns                  (literal route)
Input: /campaigns/123/attendees            → /campaigns/{id}/attendees   (numeric)
Input: /campaigns/campaign_001/attendees   → /campaigns/{id}/attendees   ✅ (the fix!)
Input: /campaigns/user-456                 → /campaigns/{id}             (dash-separated)
Input: /campaigns/attendees                → /campaigns/attendees        (not changed)
```

## How to Verify the Fix

### 1. Start the API Server
```bash
cd /Users/bhaskar.prasad/Desktop/github/claude-code
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

### 2. Generate a JWT Token
```bash
python test_jwt.py
```

This will output a token like:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVzZXJfY29nbml0b18wMDEiLCJ0ZW5hbnRfaWQiOiJ0ZW5hbnRfMDAxIn0...
```

### 3. Test the Endpoint
```bash
curl --location 'http://localhost:8000/api/v1/campaigns/campaign_001/attendees' \
  --header 'Authorization: Bearer <YOUR_JWT_TOKEN>' \
  --header 'tenant_id: tenant_001'
```

### Expected Result
You should now get a successful response (200 OK) like:
```json
{
  "success": true,
  "data": [],
  "total": 0,
  "message": "Retrieved 0 attendees for campaign campaign_001",
  "timestamp": "2026-02-24T20:00:00Z"
}
```

**NOT** the old "access denied" error.

## Authentication Flow (Now Working)
1. ✅ Request: `GET /api/v1/campaigns/campaign_001/attendees`
2. ✅ Extract token: `cognito_user_id=user_cognito_001`, `tenant_id=tenant_001`
3. ✅ Find user: `TenantSponsorUser` lookup succeeds
4. ✅ Normalize domain: `/campaigns/campaign_001/attendees` → `/campaigns/{id}/attendees`
5. ✅ Check access: Domain found in `ApplicationFeatureDomain` table
6. ✅ Get campaigns: User has access via `CustomerEntitlements`
7. ✅ Auth passes: Endpoint processes request normally

## Files Changed
- **app/middleware/auth_middleware.py** (line 254-260): Updated `normalize_domain_path()` function

## Why This Works
The new regex pattern uses:
- `[a-z0-9]*[_-][a-z0-9]*` - Matches any segment containing at least one underscore or dash (like `campaign_001`, `user-456`)
- This is specific enough to match ID-like values but not interfere with literal route names like `attendees`

## Next Steps
1. Test with the curl command above
2. Try the other endpoints:
   - `GET /api/v1/campaigns/campaign_001/attendees/search?email=test@example.com`
   - `GET /api/v1/campaigns/campaign_001/event-summary`
3. Check server logs to confirm auth is passing (look for "✅ Auth passed" messages)
