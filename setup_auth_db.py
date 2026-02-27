#!/usr/bin/env python3
"""
Setup script to:
1. Create PostgreSQL roles (ro/rw)
2. Create database tables
3. Populate sample data
"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from urllib.parse import quote
from app.config import settings
from app.database import Base
from app.models.auth_models import (
    User, Tenant, Sponsor, TenantSponsorUser, Application,
    LicenseModel, ApplicationFeatureDomain, License,
    CustomerEntitlements, ClientEntitlements, Campaign,
    TenantSponsorCampaign, LicenseProducts
)


async def setup_roles(engine):
    """Create PostgreSQL roles for read-only and read-write access."""
    async with engine.begin() as conn:
        print("📋 Setting up PostgreSQL roles...")

        # Drop existing roles if they exist (handle with try-except)
        try:
            await conn.execute(text("DROP ROLE IF EXISTS app_ro"))
        except:
            pass

        try:
            await conn.execute(text("DROP ROLE IF EXISTS app_rw"))
        except:
            pass

        # Create read-only role
        try:
            await conn.execute(text("CREATE ROLE app_ro WITH LOGIN PASSWORD 'readonly_pass_123'"))
            await conn.execute(text("GRANT USAGE ON SCHEMA test TO app_ro"))
            await conn.execute(text("GRANT SELECT ON ALL TABLES IN SCHEMA test TO app_ro"))
            print("✅ Created app_ro (read-only) role")
        except Exception as e:
            print(f"⚠️  app_ro role already exists or error: {str(e)}")

        # Create read-write role
        try:
            await conn.execute(text("CREATE ROLE app_rw WITH LOGIN PASSWORD 'readwrite_pass_123'"))
            await conn.execute(text("GRANT USAGE ON SCHEMA test TO app_rw"))
            await conn.execute(text("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA test TO app_rw"))
            print("✅ Created app_rw (read-write) role")
        except Exception as e:
            print(f"⚠️  app_rw role already exists or error: {str(e)}")


async def create_tables(engine):
    """Create all tables in the database."""
    async with engine.begin() as conn:
        print("\n📋 Creating tables...")

        # Create schema if it doesn't exist
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS test"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully")


async def populate_sample_data(engine):
    """Populate database with sample data."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("\n📋 Populating sample data...")

        # 1. Create tenants
        tenant1 = Tenant(tenant_id="tenant_001", name="Acme Corporation")
        tenant2 = Tenant(tenant_id="tenant_002", name="TechCorp Inc")
        session.add(tenant1)
        session.add(tenant2)
        await session.flush()
        print("✅ Created 2 sample tenants")

        # 2. Create sponsors
        sponsor1 = Sponsor(sponsor_id="sponsor_001", name="Sales Sponsor", tenant_id="tenant_001")
        sponsor2 = Sponsor(sponsor_id="sponsor_002", name="Marketing Sponsor", tenant_id="tenant_001")
        sponsor3 = Sponsor(sponsor_id="sponsor_003", name="Tech Sponsor", tenant_id="tenant_002")
        session.add(sponsor1)
        session.add(sponsor2)
        session.add(sponsor3)
        await session.flush()
        print("✅ Created 3 sample sponsors")

        # 3. Create users
        user1 = User(
            cognito_user_id="user_cognito_001",
            email="admin@example.com",
            first_name="John",
            last_name="Admin"
        )
        user2 = User(
            cognito_user_id="user_cognito_002",
            email="viewer@example.com",
            first_name="Jane",
            last_name="Viewer"
        )
        session.add(user1)
        session.add(user2)
        await session.flush()
        print("✅ Created 2 sample users")

        # 4. Create tenant-sponsor-user mappings
        tsu1 = TenantSponsorUser(
            tenant_id="tenant_001",
            sponsor_id="sponsor_001",
            user_id=user1.id,
            access_level="leadinsights_admin",
            status="accepted"
        )
        tsu2 = TenantSponsorUser(
            tenant_id="tenant_001",
            sponsor_id="sponsor_001",
            user_id=user2.id,
            access_level="viewer",
            status="accepted"
        )
        session.add(tsu1)
        session.add(tsu2)
        await session.flush()
        print("✅ Created 2 sample tenant-sponsor-user mappings")

        # 5. Create applications
        app1 = Application(name="leadinsights_campaigns", description="Campaigns application")
        app2 = Application(name="leadinsights_analytics", description="Analytics application")
        session.add(app1)
        session.add(app2)
        await session.flush()
        print("✅ Created 2 sample applications")

        # 6. Create license models
        lic_model1 = LicenseModel(license_model_id="license_model_001", name="Premium License")
        lic_model2 = LicenseModel(license_model_id="license_model_002", name="Standard License")
        session.add(lic_model1)
        session.add(lic_model2)
        await session.flush()
        print("✅ Created 2 sample license models")

        # 7. Create application feature domains
        afd1 = ApplicationFeatureDomain(
            application_id=app1.id,
            tenant_id="tenant_001",
            license_model_id="license_model_001",
            domain="/campaigns",
            method="GET",
            impersonation_access=True
        )
        afd2 = ApplicationFeatureDomain(
            application_id=app1.id,
            tenant_id="tenant_001",
            license_model_id="license_model_001",
            domain="/campaigns/{id}/attendees",
            method="GET",
            impersonation_access=True
        )
        session.add(afd1)
        session.add(afd2)
        await session.flush()
        print("✅ Created 2 sample application feature domains")

        # 8. Create licenses
        lic1 = License(
            license_model_id="license_model_001",
            application_id=app1.id,
            tenant_id="tenant_001",
            sponsor_id="sponsor_001",
            status="active"
        )
        session.add(lic1)
        await session.flush()
        print("✅ Created 1 sample license")

        # 9. Create campaigns
        campaign1 = Campaign(
            id="campaign_001",
            name="Summer Campaign 2024",
            division_id="division_001",
            vertical_id="vertical_001",
            brand_id="brand_001",
            status="active"
        )
        campaign2 = Campaign(
            id="campaign_002",
            name="Winter Campaign 2024",
            division_id="division_001",
            vertical_id="vertical_002",
            brand_id="brand_001",
            status="active"
        )
        session.add(campaign1)
        session.add(campaign2)
        await session.flush()
        print("✅ Created 2 sample campaigns")

        # 10. Create tenant-sponsor-campaign mappings
        tsc1 = TenantSponsorCampaign(
            tenant_id="tenant_001",
            sponsor_id="sponsor_001",
            campaign_id="campaign_001"
        )
        tsc2 = TenantSponsorCampaign(
            tenant_id="tenant_001",
            sponsor_id="sponsor_001",
            campaign_id="campaign_002"
        )
        session.add(tsc1)
        session.add(tsc2)
        await session.flush()
        print("✅ Created 2 sample tenant-sponsor-campaign mappings")

        # 11. Create customer entitlements
        ce1 = CustomerEntitlements(
            user_id=user1.id,
            sponsor_id="sponsor_001",
            tenant_id="tenant_001",
            application_id=app1.id,
            license_model_id="license_model_001",
            campaign_id="campaign_001",
            status="active"
        )
        session.add(ce1)
        await session.flush()
        print("✅ Created 1 sample customer entitlement")

        # 12. Create client entitlements
        cl1 = ClientEntitlements(
            user_id=user1.id,
            tenant_id="tenant_001",
            division="division_001",
            family="vertical_001",
            brand="brand_001"
        )
        session.add(cl1)
        await session.flush()
        print("✅ Created 1 sample client entitlement")

        # 13. Create license products
        lp1 = LicenseProducts(
            license_id=lic1.id,
            application_id=app1.id,
            campaign_id="campaign_001"
        )
        session.add(lp1)
        await session.flush()
        print("✅ Created 1 sample license product")

        # Commit all changes
        await session.commit()
        print("\n✅ All sample data committed successfully!")


async def main():
    """Main setup function."""
    try:
        # Build connection string
        db_user = quote(settings.DB_USER, safe='')
        db_password = quote(settings.DB_PASSWORD, safe='')

        db_url = (
            f"postgresql+asyncpg://"
            f"{db_user}:{db_password}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/"
            f"{settings.DB_NAME}"
        )

        engine = create_async_engine(db_url, echo=False)

        print("🚀 Starting database setup...\n")

        # Setup roles
        await setup_roles(engine)

        # Create tables
        await create_tables(engine)

        # Populate sample data
        await populate_sample_data(engine)

        await engine.dispose()

        print("\n" + "=" * 60)
        print("✨ Database setup completed successfully!")
        print("=" * 60)
        print("\n📊 Connection Strings:")
        print(f"  Read-Only:  postgresql://app_ro:readonly_pass_123@localhost:5432/postgres")
        print(f"  Read-Write: postgresql://app_rw:readwrite_pass_123@localhost:5432/postgres")
        print("\n📋 Sample User Credentials:")
        print(f"  Admin:  cognito_user_id=user_cognito_001 (leadinsights_admin)")
        print(f"  Viewer: cognito_user_id=user_cognito_002 (viewer)")

    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
