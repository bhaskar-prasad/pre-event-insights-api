"""Database models using SQLAlchemy ORM."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Numeric
from sqlalchemy.sql import func

from app.database import Base


class Example(Base):
    """Example model for demonstration."""

    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Example(id={self.id}, name={self.name})>"


class CampaignAttendee(Base):
    """Campaign attendees model."""

    __tablename__ = "campaign_attendees"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    campaign_id = Column(BigInteger, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    company_id = Column(BigInteger, nullable=True)
    job_title = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    company_revenue = Column(Numeric, nullable=True)
    company_size = Column(Integer, nullable=True)
    country = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<CampaignAttendee(id={self.id}, campaign_id={self.campaign_id}, email={self.email})>"
