"""Tests for campaigns router endpoints."""

import pytest
import jwt
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.main import app
from app.database import get_session
from fastapi.testclient import TestClient


@pytest.fixture
def auth_client(mock_session, valid_auth_headers):
    """FastAPI client with auth setup."""
    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    client.headers.update(valid_auth_headers)
    yield client
    app.dependency_overrides.clear()


class TestCampaignsRouter:
    """Test suite for campaigns router endpoints."""

    def test_get_campaign_attendees_missing_auth(self, client):
        """Test that missing auth header returns 401."""
        response = client.get("/api/v1/campaigns/campaign_001/attendees")
        assert response.status_code == 401

    def test_get_campaign_attendees_invalid_token(self, client):
        """Test that invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid_token", "tenant_id": "tenant_001"}
        response = client.get("/api/v1/campaigns/campaign_001/attendees", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_campaign_attendees_success(self, auth_client, mock_session):
        """Test successful retrieval of campaign attendees."""
        with patch("app.middleware.auth_middleware.add_auth_context_to_request") as mock_auth:
            mock_auth.return_value = (
                True,
                {
                    "user_id": 1,
                    "campaigns": ["campaign_001"],
                    "tenant_id": "tenant_001",
                },
                None,
            )

            with patch("app.services.example.CampaignAttendeeService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.get_attendees_with_count = AsyncMock(
                    return_value=([], 0)
                )
                mock_service_class.return_value = mock_service

                response = auth_client.get("/api/v1/campaigns/campaign_001/attendees")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"] == []

    def test_get_campaign_attendees_pagination(self, auth_client):
        """Test pagination parameters work correctly."""
        with patch("app.middleware.auth_middleware.add_auth_context_to_request") as mock_auth:
            mock_auth.return_value = (
                True,
                {"user_id": 1, "campaigns": ["campaign_001"], "tenant_id": "tenant_001"},
                None,
            )

            with patch("app.services.example.CampaignAttendeeService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.get_attendees_with_count = AsyncMock(return_value=([], 0))
                mock_service_class.return_value = mock_service

                response = auth_client.get(
                    "/api/v1/campaigns/campaign_001/attendees?skip=10&limit=25"
                )

                assert response.status_code == 200

    def test_get_campaign_attendee_by_email_missing_email(self, auth_client):
        """Test that missing email param returns 422."""
        with patch("app.middleware.auth_middleware.add_auth_context_to_request") as mock_auth:
            mock_auth.return_value = (
                True,
                {"user_id": 1, "campaigns": ["campaign_001"], "tenant_id": "tenant_001"},
                None,
            )

            response = auth_client.get("/api/v1/campaigns/campaign_001/attendees/search")
            assert response.status_code == 422

    def test_get_campaign_attendee_by_email_success(self, auth_client):
        """Test successful retrieval of attendee by email."""
        with patch("app.middleware.auth_middleware.add_auth_context_to_request") as mock_auth:
            mock_auth.return_value = (
                True,
                {"user_id": 1, "campaigns": ["campaign_001"], "tenant_id": "tenant_001"},
                None,
            )

            with patch("app.services.example.CampaignAttendeeService") as mock_service_class:
                mock_service = MagicMock()
                mock_attendee = MagicMock()
                mock_attendee.id = 1
                mock_attendee.email = "test@example.com"
                mock_service.get_attendee_by_email = AsyncMock(return_value=mock_attendee)
                mock_service_class.return_value = mock_service

                response = auth_client.get(
                    "/api/v1/campaigns/campaign_001/attendees/search?email=test@example.com"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_get_campaign_attendee_by_email_not_found(self, auth_client):
        """Test 404 when attendee not found."""
        with patch("app.middleware.auth_middleware.add_auth_context_to_request") as mock_auth:
            mock_auth.return_value = (
                True,
                {"user_id": 1, "campaigns": ["campaign_001"], "tenant_id": "tenant_001"},
                None,
            )

            with patch("app.services.example.CampaignAttendeeService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.get_attendee_by_email = AsyncMock(
                    side_effect=ValueError("Attendee not found")
                )
                mock_service_class.return_value = mock_service

                response = auth_client.get(
                    "/api/v1/campaigns/campaign_001/attendees/search?email=notfound@example.com"
                )

                assert response.status_code == 404

    def test_get_event_summary_success(self, auth_client):
        """Test successful retrieval of event summary."""
        with patch("app.middleware.auth_middleware.add_auth_context_to_request") as mock_auth:
            mock_auth.return_value = (
                True,
                {"user_id": 1, "campaigns": ["campaign_001"], "tenant_id": "tenant_001"},
                None,
            )

            with patch("app.services.example.CampaignAttendeeService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.get_event_summary = AsyncMock(
                    return_value={
                        "campaign_id": "campaign_001",
                        "total_attendees": 100,
                        "total_companies": 25,
                    }
                )
                mock_service_class.return_value = mock_service

                response = auth_client.get("/api/v1/campaigns/campaign_001/event-summary")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["total_attendees"] == 100

    def test_get_event_summary_missing_auth(self, client):
        """Test that event summary requires auth."""
        response = client.get("/api/v1/campaigns/campaign_001/event-summary")
        assert response.status_code == 401

    def test_health_check_skips_auth(self, client):
        """Test that health check endpoints skip authentication."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_docs_skip_auth(self, client):
        """Test that /docs skips authentication."""
        response = client.get("/docs")
        # May return 301 or 200 depending on FastAPI version
        assert response.status_code in [200, 307, 308]
