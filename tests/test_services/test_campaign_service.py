"""Tests for CampaignAttendeeService."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.example import CampaignAttendeeService
from app.models.example import CampaignAttendee


class TestCampaignAttendeeService:
    """Test suite for CampaignAttendeeService."""

    @pytest.mark.asyncio
    async def test_get_attendees_success(self, mock_session):
        """Test successful retrieval of attendees."""
        mock_attendee = MagicMock(spec=CampaignAttendee)
        mock_attendee.id = 1
        mock_attendee.email = "test@example.com"

        service = CampaignAttendeeService(mock_session)
        service.queries.get_by_campaign_id = AsyncMock(return_value=[mock_attendee])

        result = await service.get_attendees("campaign_001")

        assert len(result) == 1
        assert result[0].id == 1
        service.queries.get_by_campaign_id.assert_called_once_with(
            mock_session, "campaign_001", skip=0, limit=50
        )

    @pytest.mark.asyncio
    async def test_get_attendees_with_pagination(self, mock_session):
        """Test get_attendees with pagination parameters."""
        service = CampaignAttendeeService(mock_session)
        service.queries.get_by_campaign_id = AsyncMock(return_value=[])

        await service.get_attendees("campaign_001", skip=10, limit=25)

        service.queries.get_by_campaign_id.assert_called_once_with(
            mock_session, "campaign_001", skip=10, limit=25
        )

    @pytest.mark.asyncio
    async def test_get_attendees_empty_campaign_id(self, mock_session):
        """Test that empty campaign_id raises ValueError."""
        service = CampaignAttendeeService(mock_session)

        with pytest.raises(ValueError, match="Campaign ID cannot be empty"):
            await service.get_attendees("")

    @pytest.mark.asyncio
    async def test_get_attendees_whitespace_campaign_id(self, mock_session):
        """Test that whitespace-only campaign_id raises ValueError."""
        service = CampaignAttendeeService(mock_session)

        with pytest.raises(ValueError, match="Campaign ID cannot be empty"):
            await service.get_attendees("   ")

    @pytest.mark.asyncio
    async def test_get_attendees_with_count(self, mock_session):
        """Test getting attendees with total count."""
        mock_attendee = MagicMock(spec=CampaignAttendee)
        service = CampaignAttendeeService(mock_session)
        service.queries.get_by_campaign_id = AsyncMock(return_value=[mock_attendee])
        service.queries.get_count_by_campaign_id = AsyncMock(return_value=5)

        attendees, count = await service.get_attendees_with_count("campaign_001")

        assert len(attendees) == 1
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_attendee_by_email_found(self, mock_session):
        """Test finding attendee by email."""
        mock_attendee = MagicMock(spec=CampaignAttendee)
        mock_attendee.id = 1
        mock_attendee.email = "test@example.com"

        service = CampaignAttendeeService(mock_session)
        service.queries.get_by_campaign_and_email = AsyncMock(return_value=mock_attendee)

        result = await service.get_attendee_by_email("campaign_001", "test@example.com")

        assert result.id == 1
        service.queries.get_by_campaign_and_email.assert_called_once_with(
            mock_session, "campaign_001", "test@example.com"
        )

    @pytest.mark.asyncio
    async def test_get_attendee_by_email_not_found(self, mock_session):
        """Test error when attendee not found by email."""
        service = CampaignAttendeeService(mock_session)
        service.queries.get_by_campaign_and_email = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Attendee with email .* not found"):
            await service.get_attendee_by_email("campaign_001", "notfound@example.com")

    @pytest.mark.asyncio
    async def test_get_event_summary(self, mock_session):
        """Test getting event summary."""
        service = CampaignAttendeeService(mock_session)
        service.queries.get_count_by_campaign_id = AsyncMock(return_value=100)
        service.queries.get_unique_companies_count = AsyncMock(return_value=25)

        result = await service.get_event_summary("campaign_001")

        assert result["campaign_id"] == "campaign_001"
        assert result["total_attendees"] == 100
        assert result["total_companies"] == 25

    @pytest.mark.asyncio
    async def test_get_event_summary_empty_campaign_id(self, mock_session):
        """Test event summary with empty campaign_id raises ValueError."""
        service = CampaignAttendeeService(mock_session)

        with pytest.raises(ValueError, match="Campaign ID cannot be empty"):
            await service.get_event_summary("")

    @pytest.mark.asyncio
    async def test_get_event_summary_zero_counts(self, mock_session):
        """Test event summary with zero counts."""
        service = CampaignAttendeeService(mock_session)
        service.queries.get_count_by_campaign_id = AsyncMock(return_value=0)
        service.queries.get_unique_companies_count = AsyncMock(return_value=0)

        result = await service.get_event_summary("empty_campaign")

        assert result["total_attendees"] == 0
        assert result["total_companies"] == 0
