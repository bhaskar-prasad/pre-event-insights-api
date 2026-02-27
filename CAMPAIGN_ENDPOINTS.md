# Campaign Attendees API Endpoints

Complete guide for the campaign attendees API endpoints.

## Overview

Two endpoints are available to retrieve campaign attendees data:

1. **Get all attendees for a campaign** - Paginated list
2. **Search for a specific attendee** - By email within a campaign

## Endpoints

### 1. Get Campaign Attendees (Paginated)

**Endpoint:** `GET /api/v1/campaigns/{campaign_id}/attendees`

**Description:** Retrieve all attendees for a specific campaign with pagination.

**Parameters:**

| Name | Type | Required | Description | Constraints |
|------|------|----------|-------------|-------------|
| campaign_id | integer | Yes | Campaign ID | Must be > 0 |
| skip | integer | No | Records to skip | Default: 0, >= 0 |
| limit | integer | No | Max records to return | Default: 50, 1-100 |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/campaigns/1/attendees?skip=0&limit=50"
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Retrieved 50 attendees for campaign 1",
  "data": [
    {
      "id": 1001,
      "campaign_id": 1,
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company_name": "Acme Corp",
      "company_id": 100,
      "job_title": "Manager",
      "industry": "Technology",
      "company_revenue": 5000000,
      "company_size": 500,
      "country": "USA",
      "city": "San Francisco",
      "state": "CA"
    },
    ...
  ],
  "total": 342,
  "timestamp": "2026-02-24T12:30:00.000Z"
}
```

**Error Response (400 Bad Request):**

```json
{
  "success": false,
  "message": "Invalid campaign ID",
  "error_code": "INVALID_CAMPAIGN_ID",
  "details": [
    {
      "field": null,
      "message": "Campaign ID must be a positive integer",
      "code": null
    }
  ],
  "timestamp": "2026-02-24T12:30:00.000Z"
}
```

---

### 2. Search Attendee by Email

**Endpoint:** `GET /api/v1/campaigns/{campaign_id}/attendees/search`

**Description:** Find a specific attendee by campaign ID and email address.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| campaign_id | integer | Yes | Campaign ID (must be > 0) |
| email | string | Yes | Attendee email address |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/campaigns/1/attendees/search?email=john@example.com"
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Attendee found for campaign 1",
  "data": {
    "id": 1001,
    "campaign_id": 1,
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "company_name": "Acme Corp",
    "company_id": 100,
    "job_title": "Manager",
    "industry": "Technology",
    "company_revenue": 5000000,
    "company_size": 500,
    "country": "USA",
    "city": "San Francisco",
    "state": "CA"
  },
  "timestamp": "2026-02-24T12:30:00.000Z"
}
```

**Error Response (404 Not Found):**

```json
{
  "success": false,
  "message": "Invalid parameters or attendee not found",
  "error_code": "NOT_FOUND",
  "details": [
    {
      "field": null,
      "message": "Attendee with email john@example.com not found for campaign 1",
      "code": null
    }
  ],
  "timestamp": "2026-02-24T12:30:00.000Z"
}
```

**Error Response (400 Bad Request - Invalid Email):**

```json
{
  "success": false,
  "message": "Invalid parameters or attendee not found",
  "error_code": "INVALID_EMAIL",
  "details": [
    {
      "field": null,
      "message": "Invalid email format",
      "code": null
    }
  ],
  "timestamp": "2026-02-24T12:30:00.000Z"
}
```

---

## Implementation Details

### Project Structure

```
app/
├── models/example.py           # CampaignAttendee model
├── schemas/example.py          # CampaignAttendeeResponse schema
├── queries/example.py          # CampaignAttendeeQueries
├── services/example.py         # CampaignAttendeeService
└── routers/campaigns.py        # Campaigns endpoints
```

### Key Components

**Model (app/models/example.py):**
- Maps to `test.campaign_attendees` table
- Uses schema: `test`
- Fields: id, campaign_id, email, name, company info, location, etc.

**Queries (app/queries/example.py):**
- `get_by_campaign_id()` - Fetch attendees with pagination
- `get_count_by_campaign_id()` - Get total count for a campaign
- `get_by_campaign_and_email()` - Find specific attendee

**Service (app/services/example.py):**
- `get_attendees()` - Retrieve attendees with validation
- `get_attendees_with_count()` - Retrieve + total count
- `get_attendee_by_email()` - Find attendee by email

**Router (app/routers/campaigns.py):**
- GET `/api/v1/campaigns/{campaign_id}/attendees` - List attendees
- GET `/api/v1/campaigns/{campaign_id}/attendees/search` - Search attendee

### Features

✅ **Pagination** - Skip/limit parameters for large datasets
✅ **Error Handling** - Consistent error responses with codes
✅ **Validation** - Input validation at endpoint level
✅ **Async** - Full async/await throughout
✅ **Schema-based** - Pydantic schemas for type safety
✅ **Logging** - Detailed logging for debugging

---

## Usage Examples

### Example 1: Get First 50 Attendees

```python
import httpx
import asyncio

async def get_attendees():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/campaigns/1/attendees?skip=0&limit=50"
        )
        data = response.json()

        print(f"Total attendees: {data['total']}")
        print(f"Retrieved: {len(data['data'])}")

        for attendee in data['data']:
            print(f"  {attendee['email']} - {attendee['first_name']} {attendee['last_name']}")

asyncio.run(get_attendees())
```

### Example 2: Search for Specific Attendee

```python
import httpx
import asyncio

async def search_attendee():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/campaigns/1/attendees/search",
            params={"email": "john@example.com"}
        )
        data = response.json()

        if data['success']:
            attendee = data['data']
            print(f"Name: {attendee['first_name']} {attendee['last_name']}")
            print(f"Company: {attendee['company_name']}")
            print(f"Job Title: {attendee['job_title']}")
        else:
            print(f"Error: {data['message']}")

asyncio.run(search_attendee())
```

### Example 3: Paginate Through All Attendees

```python
import httpx
import asyncio

async def get_all_attendees():
    async with httpx.AsyncClient() as client:
        campaign_id = 1
        limit = 50
        skip = 0
        all_attendees = []

        while True:
            response = await client.get(
                f"http://localhost:8000/api/v1/campaigns/{campaign_id}/attendees",
                params={"skip": skip, "limit": limit}
            )
            data = response.json()

            all_attendees.extend(data['data'])

            if len(all_attendees) >= data['total']:
                break

            skip += limit

        print(f"Retrieved {len(all_attendees)} total attendees")
        return all_attendees

asyncio.run(get_all_attendees())
```

---

## Testing in Swagger UI

1. Start the application:
```bash
python -m uvicorn app.main:app --reload
```

2. Open: http://localhost:8000/docs

3. Navigate to the **Campaigns** section

4. Try the endpoints with test parameters

---

## Testing with Sample Data

If the table is empty, you can add sample data:

```sql
INSERT INTO test.campaign_attendees (
    id, campaign_id, email, first_name, last_name,
    company_name, job_title, industry, country, city, state
) VALUES
(1, 1, 'john@example.com', 'John', 'Doe', 'Acme Corp', 'Manager', 'Tech', 'USA', 'San Francisco', 'CA'),
(2, 1, 'jane@example.com', 'Jane', 'Smith', 'Tech Solutions', 'Director', 'Tech', 'USA', 'New York', 'NY'),
(3, 2, 'bob@example.com', 'Bob', 'Johnson', 'Finance Inc', 'Analyst', 'Finance', 'USA', 'Boston', 'MA');
```

Then test the endpoints with campaign_id=1 or campaign_id=2.

---

## Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| INVALID_CAMPAIGN_ID | 400 | Campaign ID must be positive |
| INVALID_EMAIL | 400 | Email format is invalid |
| NOT_FOUND | 404 | Attendee or campaign not found |
| ATTENDEES_RETRIEVAL_ERROR | 500 | Database query failed |
| SEARCH_ERROR | 500 | Search operation failed |

---

## Future Enhancements

- Add filtering by company, industry, country
- Add sorting by name, email, company
- Add export to CSV/Excel
- Add attendee count by company
- Add bulk operations
- Add caching for frequently accessed campaigns

---

## Related Files

- Models: `app/models/example.py`
- Schemas: `app/schemas/example.py`
- Queries: `app/queries/example.py`
- Services: `app/services/example.py`
- Routes: `app/routers/campaigns.py`
- Main: `app/main.py`
