"""Pydantic schemas for models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ExampleCreate(BaseModel):
    """Schema for creating a new example."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the example",
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional description",
    )


class ExampleUpdate(BaseModel):
    """Schema for updating an example."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Name of the example",
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional description",
    )


class ExampleResponse(BaseModel):
    """Schema for example response."""

    id: int = Field(..., description="Example ID")
    name: str = Field(..., description="Example name")
    description: Optional[str] = Field(None, description="Example description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class EventSummaryResponse(BaseModel):
    """Schema for event/campaign summary response."""

    campaign_id: str = Field(..., description="Campaign ID")
    total_attendees: int = Field(..., description="Total unique attendees")
    total_companies: int = Field(..., description="Total unique companies")

    class Config:
        from_attributes = True


class CampaignAttendeeResponse(BaseModel):
    """Schema for campaign attendee response."""

    id: int = Field(..., description="Attendee ID")
    campaign_id: str = Field(..., description="Campaign ID")
    email: str = Field(..., description="Attendee email")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    company_name: Optional[str] = Field(None, description="Company name")
    company_id: Optional[int] = Field(None, description="Company ID")
    job_title: Optional[str] = Field(None, description="Job title")
    industry: Optional[str] = Field(None, description="Industry")
    company_revenue: Optional[Decimal] = Field(None, description="Company revenue")
    company_size: Optional[int] = Field(None, description="Company size")
    country: Optional[str] = Field(None, description="Country")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")

    class Config:
        from_attributes = True
