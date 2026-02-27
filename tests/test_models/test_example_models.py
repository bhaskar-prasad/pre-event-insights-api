"""Tests for example ORM models."""

import pytest
from datetime import datetime
from decimal import Decimal

from app.models.example import Example, CampaignAttendee


class TestExampleModel:
    """Test suite for Example ORM model."""

    def test_example_instantiation(self):
        """Test creating an Example instance."""
        example = Example(
            id=1,
            name="Test Example",
            description="This is a test example",
        )

        assert example.id == 1
        assert example.name == "Test Example"
        assert example.description == "This is a test example"

    def test_example_repr(self):
        """Test Example model repr method."""
        example = Example(id=42, name="Test Example")
        repr_str = repr(example)

        assert "Example" in repr_str
        assert "id=42" in repr_str
        assert "name=Test Example" in repr_str

    def test_example_nullable_description(self):
        """Test that description can be None."""
        example = Example(id=1, name="Test")
        assert example.description is None

    def test_example_with_timestamps(self):
        """Test Example model with timestamp fields."""
        now = datetime.utcnow()
        example = Example(
            id=1,
            name="Test",
            created_at=now,
            updated_at=now,
        )

        assert example.created_at == now
        assert example.updated_at == now


class TestCampaignAttendeeModel:
    """Test suite for CampaignAttendee ORM model."""

    def test_campaign_attendee_instantiation(self):
        """Test creating a CampaignAttendee instance."""
        attendee = CampaignAttendee(
            id=1,
            campaign_id=100,
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )

        assert attendee.id == 1
        assert attendee.campaign_id == 100
        assert attendee.email == "test@example.com"
        assert attendee.first_name == "John"
        assert attendee.last_name == "Doe"

    def test_campaign_attendee_full_data(self):
        """Test CampaignAttendee with all fields."""
        attendee = CampaignAttendee(
            id=1,
            campaign_id=100,
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            company_name="Acme Corp",
            company_id=200,
            job_title="Manager",
            industry="Technology",
            company_revenue=Decimal("1000000"),
            company_size=500,
            country="USA",
            city="San Francisco",
            state="CA",
        )

        assert attendee.company_name == "Acme Corp"
        assert attendee.company_id == 200
        assert attendee.job_title == "Manager"
        assert attendee.company_revenue == Decimal("1000000")
        assert attendee.company_size == 500

    def test_campaign_attendee_nullable_fields(self):
        """Test that optional fields default to None."""
        attendee = CampaignAttendee(
            id=1,
            campaign_id=100,
            email="test@example.com",
        )

        assert attendee.first_name is None
        assert attendee.last_name is None
        assert attendee.company_name is None
        assert attendee.company_id is None
        assert attendee.job_title is None
        assert attendee.industry is None
        assert attendee.company_revenue is None
        assert attendee.company_size is None
        assert attendee.country is None
        assert attendee.city is None
        assert attendee.state is None

    def test_campaign_attendee_repr(self):
        """Test CampaignAttendee model repr method."""
        attendee = CampaignAttendee(
            id=42,
            campaign_id=100,
            email="test@example.com",
        )
        repr_str = repr(attendee)

        assert "CampaignAttendee" in repr_str
        assert "id=42" in repr_str
        assert "campaign_id=100" in repr_str
        assert "email=test@example.com" in repr_str

    def test_campaign_attendee_large_id(self):
        """Test CampaignAttendee with BigInteger IDs."""
        large_id = 9223372036854775807  # Max BigInteger
        attendee = CampaignAttendee(
            id=large_id,
            campaign_id=1234567890,
            email="test@example.com",
        )

        assert attendee.id == large_id
        assert attendee.campaign_id == 1234567890
