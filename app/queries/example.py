"""Queries module for database operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.example import CampaignAttendee


class CampaignAttendeeQueries:
    """Database queries for campaign attendees."""

    @staticmethod
    async def get_by_campaign_id(
        session: AsyncSession, campaign_id: str, skip: int = 0, limit: int = 50
    ):
        """
        Fetch campaign attendees by campaign ID with pagination.

        Args:
            session: Database session
            campaign_id: Campaign ID to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of campaign attendees
        """
        result = await session.execute(
            select(CampaignAttendee)
            .where(CampaignAttendee.campaign_id == campaign_id)
            .offset(skip)
            .limit(limit)
            .order_by(CampaignAttendee.id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_count_by_campaign_id(session: AsyncSession, campaign_id: str):
        """
        Get total count of attendees for a campaign.

        Args:
            session: Database session
            campaign_id: Campaign ID

        Returns:
            Total count of attendees
        """
        from sqlalchemy import func

        result = await session.execute(
            select(func.count(CampaignAttendee.id)).where(
                CampaignAttendee.campaign_id == campaign_id
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def get_by_campaign_and_email(
        session: AsyncSession, campaign_id: str, email: str
    ):
        """
        Fetch a specific attendee by campaign ID and email.

        Args:
            session: Database session
            campaign_id: Campaign ID
            email: Attendee email

        Returns:
            Campaign attendee or None
        """
        result = await session.execute(
            select(CampaignAttendee).where(
                (CampaignAttendee.campaign_id == campaign_id)
                & (CampaignAttendee.email == email)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_unique_companies_count(session: AsyncSession, campaign_id: str):
        """
        Get count of unique companies for a campaign.

        Args:
            session: Database session
            campaign_id: Campaign ID

        Returns:
            Count of unique companies
        """
        from sqlalchemy import func

        result = await session.execute(
            select(func.count(func.distinct(CampaignAttendee.company_id))).where(
                (CampaignAttendee.campaign_id == campaign_id)
                & (CampaignAttendee.company_id.isnot(None))
            )
        )
        return result.scalar() or 0


class ExampleQueries:
    """Database queries for example operations."""

    @staticmethod
    async def get_by_id(session: AsyncSession, id: int):
        """
        Example: Fetch an item by ID.

        Replace this with your actual model and queries.
        """
        # from app.models import YourModel
        # result = await session.execute(
        #     select(YourModel).where(YourModel.id == id)
        # )
        # return result.scalar_one_or_none()
        pass

    @staticmethod
    async def get_all(session: AsyncSession, skip: int = 0, limit: int = 10):
        """
        Example: Fetch all items with pagination.

        Replace this with your actual model and queries.
        """
        # from app.models import YourModel
        # result = await session.execute(
        #     select(YourModel).offset(skip).limit(limit)
        # )
        # return result.scalars().all()
        pass

    @staticmethod
    async def create(session: AsyncSession, **kwargs):
        """
        Example: Create a new item.

        Replace this with your actual model.
        """
        # from app.models import YourModel
        # item = YourModel(**kwargs)
        # session.add(item)
        # await session.commit()
        # await session.refresh(item)
        # return item
        pass

    @staticmethod
    async def update(session: AsyncSession, id: int, **kwargs):
        """
        Example: Update an existing item.

        Replace this with your actual model.
        """
        # from app.models import YourModel
        # result = await session.execute(
        #     select(YourModel).where(YourModel.id == id)
        # )
        # item = result.scalar_one_or_none()
        # if item:
        #     for key, value in kwargs.items():
        #         setattr(item, key, value)
        #     await session.commit()
        #     await session.refresh(item)
        # return item
        pass

    @staticmethod
    async def delete(session: AsyncSession, id: int) -> bool:
        """
        Example: Delete an item.

        Replace this with your actual model.
        """
        # from app.models import YourModel
        # result = await session.execute(
        #     select(YourModel).where(YourModel.id == id)
        # )
        # item = result.scalar_one_or_none()
        # if item:
        #     await session.delete(item)
        #     await session.commit()
        #     return True
        # return False
        pass
