"""Tests for example schemas."""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from app.schemas.example import (
    ExampleCreate,
    ExampleUpdate,
    ExampleResponse,
    EventSummaryResponse,
    CampaignAttendeeResponse,
)


class TestExampleCreate:
    """Test suite for ExampleCreate schema."""

    def test_example_create_valid(self):
        """Test creating valid ExampleCreate."""
        schema = ExampleCreate(
            name="Test Example",
            description="This is a test example",
        )

        assert schema.name == "Test Example"
        assert schema.description == "This is a test example"

    def test_example_create_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            ExampleCreate(description="Only description")

    def test_example_create_description_optional(self):
        """Test that description is optional."""
        schema = ExampleCreate(name="Test")
        assert schema.name == "Test"
        assert schema.description is None

    def test_example_create_name_too_short(self):
        """Test validation of minimum name length."""
        with pytest.raises(ValidationError):
            ExampleCreate(name="")  # Empty string fails min_length=1

    def test_example_create_name_too_long(self):
        """Test validation of maximum name length."""
        long_name = "x" * 256
        with pytest.raises(ValidationError):
            ExampleCreate(name=long_name)

    def test_example_create_description_too_long(self):
        """Test validation of maximum description length."""
        long_desc = "x" * 1001
        with pytest.raises(ValidationError):
            ExampleCreate(name="Test", description=long_desc)


class TestExampleUpdate:
    """Test suite for ExampleUpdate schema."""

    def test_example_update_all_fields_optional(self):
        """Test that all fields in ExampleUpdate are optional."""
        schema = ExampleUpdate()
        assert schema.name is None
        assert schema.description is None

    def test_example_update_name_only(self):
        """Test updating only name."""
        schema = ExampleUpdate(name="Updated Name")
        assert schema.name == "Updated Name"
        assert schema.description is None

    def test_example_update_description_only(self):
        """Test updating only description."""
        schema = ExampleUpdate(description="Updated Description")
        assert schema.name is None
        assert schema.description == "Updated Description"

    def test_example_update_both_fields(self):
        """Test updating both fields."""
        schema = ExampleUpdate(
            name="Updated",
            description="Updated Description",
        )
        assert schema.name == "Updated"
        assert schema.description == "Updated Description"

    def test_example_update_name_min_length_validation(self):
        """Test name minimum length validation in update."""
        with pytest.raises(ValidationError):
            ExampleUpdate(name="")


class TestExampleResponse:
    """Test suite for ExampleResponse schema."""

    def test_example_response_valid(self):
        """Test creating valid ExampleResponse."""
        now = datetime.utcnow()
        schema = ExampleResponse(
            id=1,
            name="Test",
            description="Test description",
            created_at=now,
            updated_at=now,
        )

        assert schema.id == 1
        assert schema.name == "Test"
        assert schema.description == "Test description"
        assert schema.created_at == now
        assert schema.updated_at == now

    def test_example_response_description_optional(self):
        """Test that description is optional in response."""
        now = datetime.utcnow()
        schema = ExampleResponse(
            id=1,
            name="Test",
            created_at=now,
            updated_at=now,
        )

        assert schema.description is None

    def test_example_response_from_attributes(self):
        """Test from_attributes config for ORM mapping."""
        # ExampleResponse should have from_attributes = True
        # This allows it to be instantiated from ORM objects
        assert ExampleResponse.model_config.get("from_attributes") is True

    def test_example_response_serialization(self):
        """Test serialization of ExampleResponse."""
        now = datetime.utcnow()
        schema = ExampleResponse(
            id=1,
            name="Test",
            created_at=now,
            updated_at=now,
        )
        data = schema.model_dump()

        assert data["id"] == 1
        assert data["name"] == "Test"


class TestEventSummaryResponse:
    """Test suite for EventSummaryResponse schema."""

    def test_event_summary_response_valid(self):
        """Test creating valid EventSummaryResponse."""
        schema = EventSummaryResponse(
            campaign_id="campaign_001",
            total_attendees=100,
            total_companies=25,
        )

        assert schema.campaign_id == "campaign_001"
        assert schema.total_attendees == 100
        assert schema.total_companies == 25

    def test_event_summary_response_zero_values(self):
        """Test EventSummaryResponse with zero values."""
        schema = EventSummaryResponse(
            campaign_id="empty_campaign",
            total_attendees=0,
            total_companies=0,
        )

        assert schema.total_attendees == 0
        assert schema.total_companies == 0

    def test_event_summary_response_from_attributes(self):
        """Test from_attributes config."""
        assert EventSummaryResponse.model_config.get("from_attributes") is True


class TestCampaignAttendeeResponse:
    """Test suite for CampaignAttendeeResponse schema."""

    def test_campaign_attendee_response_minimal(self):
        """Test creating CampaignAttendeeResponse with required fields."""
        schema = CampaignAttendeeResponse(
            id=1,
            campaign_id="campaign_001",
            email="test@example.com",
        )

        assert schema.id == 1
        assert schema.campaign_id == "campaign_001"
        assert schema.email == "test@example.com"

    def test_campaign_attendee_response_full(self):
        """Test creating CampaignAttendeeResponse with all fields."""
        schema = CampaignAttendeeResponse(
            id=1,
            campaign_id="campaign_001",
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

        assert schema.first_name == "John"
        assert schema.company_name == "Acme Corp"
        assert schema.company_revenue == Decimal("1000000")
        assert schema.company_size == 500

    def test_campaign_attendee_response_optional_fields(self):
        """Test that optional fields default to None."""
        schema = CampaignAttendeeResponse(
            id=1,
            campaign_id="campaign_001",
            email="test@example.com",
        )

        assert schema.first_name is None
        assert schema.last_name is None
        assert schema.company_name is None
        assert schema.company_id is None
        assert schema.job_title is None
        assert schema.company_revenue is None

    def test_campaign_attendee_response_from_attributes(self):
        """Test from_attributes config for ORM mapping."""
        assert CampaignAttendeeResponse.model_config.get("from_attributes") is True

    def test_campaign_attendee_response_decimal_revenue(self):
        """Test handling of Decimal company revenue."""
        schema = CampaignAttendeeResponse(
            id=1,
            campaign_id="campaign_001",
            email="test@example.com",
            company_revenue=Decimal("999999.99"),
        )

        assert isinstance(schema.company_revenue, Decimal)
        assert schema.company_revenue == Decimal("999999.99")

    def test_campaign_attendee_response_serialization(self):
        """Test serialization of CampaignAttendeeResponse."""
        schema = CampaignAttendeeResponse(
            id=1,
            campaign_id="campaign_001",
            email="test@example.com",
            company_revenue=Decimal("1000000"),
        )
        data = schema.model_dump()

        assert data["id"] == 1
        assert data["campaign_id"] == "campaign_001"
        assert data["email"] == "test@example.com"
