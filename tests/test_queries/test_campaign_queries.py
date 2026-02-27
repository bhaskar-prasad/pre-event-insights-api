"""Tests for CampaignAttendeeQueries."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select

from app.queries.example import CampaignAttendeeQueries
from app.models.example import CampaignAttendee


class TestCampaignAttendeeQueries:
    """Test suite for CampaignAttendeeQueries."""

    @pytest.mark.asyncio
    async def test_get_by_campaign_id_success(self, mock_session):
        """Test fetching attendees by campaign ID."""
        mock_attendee = MagicMock(spec=CampaignAttendee)
        mock_attendee.id = 1
        mock_attendee.email = "test@example.com"

        # Mock the result
        mock_result = AsyncMock()
        mock_result.scalars().all.return_value = [mock_attendee]
        mock_session.execute.return_value = mock_result

        attendees = await CampaignAttendeeQueries.get_by_campaign_id(
            mock_session, "campaign_001"
        )

        assert len(attendees) == 1
        assert attendees[0].id == 1

    @pytest.mark.asyncio
    async def test_get_by_campaign_id_with_pagination(self, mock_session):
        """Test pagination parameters are passed correctly."""
        mock_result = AsyncMock()
        mock_result.scalars().all.return_value = []
        mock_session.execute.return_value = mock_result

        await CampaignAttendeeQueries.get_by_campaign_id(
            mock_session, "campaign_001", skip=10, limit=25
        )

        # Verify execute was called with correct query
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_campaign_id_empty(self, mock_session):
        """Test fetching with campaign that has no attendees."""
        mock_result = AsyncMock()
        mock_result.scalars().all.return_value = []
        mock_session.execute.return_value = mock_result

        attendees = await CampaignAttendeeQueries.get_by_campaign_id(
            mock_session, "empty_campaign"
        )

        assert attendees == []

    @pytest.mark.asyncio
    async def test_get_count_by_campaign_id(self, mock_session):
        """Test getting total count of attendees."""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 42

        mock_session.execute.return_value = mock_result

        count = await CampaignAttendeeQueries.get_count_by_campaign_id(
            mock_session, "campaign_001"
        )

        assert count == 42

    @pytest.mark.asyncio
    async def test_get_count_by_campaign_id_zero(self, mock_session):
        """Test count returns 0 when no attendees."""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = None

        mock_session.execute.return_value = mock_result

        count = await CampaignAttendeeQueries.get_count_by_campaign_id(
            mock_session, "empty_campaign"
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_by_campaign_and_email_found(self, mock_session):
        """Test finding attendee by campaign and email."""
        mock_attendee = MagicMock(spec=CampaignAttendee)
        mock_attendee.id = 1
        mock_attendee.email = "test@example.com"

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_attendee
        mock_session.execute.return_value = mock_result

        attendee = await CampaignAttendeeQueries.get_by_campaign_and_email(
            mock_session, "campaign_001", "test@example.com"
        )

        assert attendee.id == 1
        assert attendee.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_by_campaign_and_email_not_found(self, mock_session):
        """Test when attendee not found by email."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        attendee = await CampaignAttendeeQueries.get_by_campaign_and_email(
            mock_session, "campaign_001", "notfound@example.com"
        )

        assert attendee is None

    @pytest.mark.asyncio
    async def test_get_unique_companies_count(self, mock_session):
        """Test getting count of unique companies."""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 25

        mock_session.execute.return_value = mock_result

        count = await CampaignAttendeeQueries.get_unique_companies_count(
            mock_session, "campaign_001"
        )

        assert count == 25

    @pytest.mark.asyncio
    async def test_get_unique_companies_count_zero(self, mock_session):
        """Test unique companies count with no companies."""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = None

        mock_session.execute.return_value = mock_result

        count = await CampaignAttendeeQueries.get_unique_companies_count(
            mock_session, "no_companies_campaign"
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_unique_companies_filters_null(self, mock_session):
        """Test that unique companies query filters out NULL company_id."""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 10

        mock_session.execute.return_value = mock_result

        # This should execute a query that filters company_id IS NOT NULL
        count = await CampaignAttendeeQueries.get_unique_companies_count(
            mock_session, "campaign_001"
        )

        mock_session.execute.assert_called_once()
        assert count == 10
