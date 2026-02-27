"""Authentication and authorization models."""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    cognito_user_id = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class Tenant(Base):
    """Tenant model."""

    __tablename__ = "tenants"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class Sponsor(Base):
    """Sponsor model."""

    __tablename__ = "sponsors"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    sponsor_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    tenant_id = Column(String(255), ForeignKey("test.tenants.tenant_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class TenantSponsorUser(Base):
    """Mapping between tenant, sponsor, and user with access level."""

    __tablename__ = "tenant_sponsor_users"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    tenant_id = Column(String(255), ForeignKey("test.tenants.tenant_id"), nullable=False, index=True)
    sponsor_id = Column(String(255), ForeignKey("test.sponsors.sponsor_id"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("test.users.id"), nullable=False, index=True)
    access_level = Column(String(100), nullable=False)  # e.g., "admin", "viewer", "leadinsights_admin"
    status = Column(String(50), nullable=False, default="accepted")  # accepted, pending, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class Application(Base):
    """Application model."""

    __tablename__ = "applications"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class LicenseModel(Base):
    """License model."""

    __tablename__ = "license_models"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    license_model_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class ApplicationFeatureDomain(Base):
    """Defines which domains/methods are accessible per application and license."""

    __tablename__ = "application_feature_domains"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    application_id = Column(BigInteger, ForeignKey("test.applications.id"), nullable=False, index=True)
    tenant_id = Column(String(255), ForeignKey("test.tenants.tenant_id"), nullable=False, index=True)
    license_model_id = Column(String(255), ForeignKey("test.license_models.license_model_id"), nullable=False)
    domain = Column(String(255), nullable=False)  # e.g., "/campaigns"
    method = Column(String(50), nullable=False)  # e.g., "GET", "POST"
    impersonation_access = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class License(Base):
    """License model linking sponsor, application, and license model."""

    __tablename__ = "licenses"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    license_model_id = Column(String(255), ForeignKey("test.license_models.license_model_id"), nullable=False)
    application_id = Column(BigInteger, ForeignKey("test.applications.id"), nullable=False, index=True)
    tenant_id = Column(String(255), ForeignKey("test.tenants.tenant_id"), nullable=False, index=True)
    sponsor_id = Column(String(255), ForeignKey("test.sponsors.sponsor_id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active")  # active, inactive, expired
    deleted_on = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class CustomerEntitlements(Base):
    """User-level campaign entitlements."""

    __tablename__ = "customer_entitlements"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("test.users.id"), nullable=False, index=True)
    sponsor_id = Column(String(255), ForeignKey("test.sponsors.sponsor_id"), nullable=False, index=True)
    tenant_id = Column(String(255), ForeignKey("test.tenants.tenant_id"), nullable=False, index=True)
    application_id = Column(BigInteger, ForeignKey("test.applications.id"), nullable=False)
    license_model_id = Column(String(255), ForeignKey("test.license_models.license_model_id"), nullable=False)
    campaign_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active")  # active, inactive
    deleted_on = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class ClientEntitlements(Base):
    """Client-level entitlements (division, family, brand filters)."""

    __tablename__ = "client_entitlements"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("test.users.id"), nullable=False, index=True)
    tenant_id = Column(String(255), ForeignKey("test.tenants.tenant_id"), nullable=False, index=True)
    division = Column(String(255), nullable=True, index=True)
    family = Column(String(255), nullable=True, index=True)
    brand = Column(String(255), nullable=True, index=True)
    deleted_on = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class Campaign(Base):
    """Campaign model."""

    __tablename__ = "campaigns"
    __table_args__ = {"schema": "test"}

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    division_id = Column(String(255), nullable=True, index=True)
    vertical_id = Column(String(255), nullable=True, index=True)  # family
    brand_id = Column(String(255), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="active")  # active, draft, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class TenantSponsorCampaign(Base):
    """Mapping between tenant, sponsor, and campaigns."""

    __tablename__ = "tenant_sponsor_campaigns"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    tenant_id = Column(String(255), ForeignKey("test.tenants.tenant_id"), nullable=False, index=True)
    sponsor_id = Column(String(255), ForeignKey("test.sponsors.sponsor_id"), nullable=False, index=True)
    campaign_id = Column(String(255), ForeignKey("test.campaigns.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class LicenseProducts(Base):
    """Products associated with licenses and campaigns."""

    __tablename__ = "license_products"
    __table_args__ = {"schema": "test"}

    id = Column(BigInteger, primary_key=True, index=True)
    license_id = Column(BigInteger, ForeignKey("test.licenses.id"), nullable=False, index=True)
    application_id = Column(BigInteger, ForeignKey("test.applications.id"), nullable=False)
    campaign_id = Column(String(255), ForeignKey("test.campaigns.id"), nullable=False, index=True)
    deleted_on = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
