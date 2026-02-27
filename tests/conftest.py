"""Shared pytest fixtures for the test suite."""

import asyncio
import jwt
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_session


# Test JWT tokens
def create_test_jwt_token(
    user_id: str = "user_cognito_001",
    tenant_id: str = "tenant_001",
    expires_in_seconds: int = 3600,
) -> str:
    """Create a test JWT token without signature verification."""
    payload = {
        "username": user_id,
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(seconds=expires_in_seconds),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return token


@pytest.fixture
def valid_jwt_token() -> str:
    """Fixture for a valid JWT token."""
    return create_test_jwt_token()


@pytest.fixture
def valid_auth_headers(valid_jwt_token) -> dict:
    """Fixture for valid auth headers."""
    return {
        "Authorization": f"Bearer {valid_jwt_token}",
        "tenant_id": "tenant_001",
    }


@pytest.fixture
def mock_auth_data() -> dict:
    """Fixture for mock auth data (what gets attached to request.state)."""
    return {
        "user_id": 1,
        "cognito_user_id": "user_cognito_001",
        "tenant_id": "tenant_001",
        "sponsor_id": "sponsor_001",
        "access_level": "admin",
        "first_name": "Test",
        "last_name": "User",
        "campaigns": ["campaign_001", "campaign_002"],
        "license_model_ids": [1, 2],
    }


@pytest.fixture
async def mock_session() -> AsyncMock:
    """Fixture for mocked AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def client(mock_session) -> TestClient:
    """Fixture for FastAPI TestClient with mocked database session."""
    # Override get_session dependency
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(mock_session) -> AsyncClient:
    """Fixture for async HTTP client."""
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def event_loop():
    """Fixture for pytest-asyncio event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_request(valid_auth_headers, mock_auth_data) -> Request:
    """Fixture for a mock FastAPI Request."""
    request = MagicMock(spec=Request)
    request.headers = valid_auth_headers
    request.url.path = "/api/v1/campaigns/campaign_001/attendees"
    request.method = "GET"
    request.state = MagicMock()
    request.state.auth_data = mock_auth_data
    return request


@pytest.fixture
def mock_auth_request(valid_auth_headers) -> Request:
    """Fixture for a request with auth headers but no auth_data attached yet."""
    request = MagicMock(spec=Request)
    request.headers = valid_auth_headers
    request.url.path = "/api/v1/campaigns/campaign_001/attendees"
    request.method = "GET"
    request.state = MagicMock()
    return request
