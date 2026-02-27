"""Service module for business logic layer."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.queries.example import ExampleQueries, CampaignAttendeeQueries

logger = logging.getLogger(__name__)


class CampaignAttendeeService:
    """Service for campaign attendees business logic."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.queries = CampaignAttendeeQueries()

    async def get_attendees(
        self, campaign_id: str, skip: int = 0, limit: int = 50
    ):
        """
        Get all attendees for a campaign with pagination.

        Args:
            campaign_id: Campaign ID
            skip: Number of records to skip
            limit: Maximum records per page

        Returns:
            List of attendees
        """
        if not campaign_id or not str(campaign_id).strip():
            raise ValueError("Campaign ID cannot be empty")

        attendees = await self.queries.get_by_campaign_id(
            self.session, campaign_id, skip=skip, limit=limit
        )

        logger.info(f"Retrieved {len(attendees)} attendees for campaign {campaign_id}")
        return attendees

    async def get_attendees_with_count(
        self, campaign_id: str, skip: int = 0, limit: int = 50
    ):
        """
        Get attendees with total count for pagination.

        Args:
            campaign_id: Campaign ID
            skip: Number of records to skip
            limit: Maximum records per page

        Returns:
            Tuple of (attendees, total_count)
        """
        attendees = await self.get_attendees(campaign_id, skip=skip, limit=limit)
        total_count = await self.queries.get_count_by_campaign_id(
            self.session, campaign_id
        )
        return attendees, total_count

    async def get_attendee_by_email(self, campaign_id: str, email: str):
        """
        Get a specific attendee by campaign ID and email.

        Args:
            campaign_id: Campaign ID
            email: Attendee email

        Returns:
            Campaign attendee

        Raises:
            ValueError: If attendee not found
        """
        attendee = await self.queries.get_by_campaign_and_email(
            self.session, campaign_id, email
        )
        if not attendee:
            raise ValueError(
                f"Attendee with email {email} not found for campaign {campaign_id}"
            )

        logger.info(
            f"Retrieved attendee {email} for campaign {campaign_id}"
        )
        return attendee

    async def get_event_summary(self, campaign_id: str):
        """
        Get event summary with total attendees and companies.

        Args:
            campaign_id: Campaign ID

        Returns:
            Dict with campaign_id, total_attendees, total_companies

        Raises:
            ValueError: If campaign ID is empty
        """
        if not campaign_id or not str(campaign_id).strip():
            raise ValueError("Campaign ID cannot be empty")

        total_attendees = await self.queries.get_count_by_campaign_id(
            self.session, campaign_id
        )
        total_companies = await self.queries.get_unique_companies_count(
            self.session, campaign_id
        )

        logger.info(
            f"Event summary for campaign {campaign_id}: "
            f"{total_attendees} attendees, {total_companies} companies"
        )

        return {
            "campaign_id": campaign_id,
            "total_attendees": total_attendees,
            "total_companies": total_companies,
        }


class ExampleService:
    """Service for business logic related to examples."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.queries = ExampleQueries()

    async def get_item(self, id: int):
        """
        Get a single item by ID.

        Args:
            id: Item ID

        Returns:
            Item object or None

        Raises:
            ValueError: If item not found
        """
        item = await self.queries.get_by_id(self.session, id)
        if not item:
            raise ValueError(f"Item with ID {id} not found")
        return item

    async def list_items(self, skip: int = 0, limit: int = 10):
        """
        List all items with pagination.

        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of items
        """
        items = await self.queries.get_all(self.session, skip=skip, limit=limit)
        return items

    async def create_item(self, **kwargs):
        """
        Create a new item.

        Args:
            **kwargs: Item attributes

        Returns:
            Created item
        """
        try:
            item = await self.queries.create(self.session, **kwargs)
            logger.info(f"Item created: {item.id}")
            return item
        except Exception as e:
            logger.error(f"Failed to create item: {str(e)}")
            raise

    async def update_item(self, id: int, **kwargs):
        """
        Update an existing item.

        Args:
            id: Item ID
            **kwargs: Fields to update

        Returns:
            Updated item

        Raises:
            ValueError: If item not found
        """
        item = await self.queries.update(self.session, id, **kwargs)
        if not item:
            raise ValueError(f"Item with ID {id} not found")

        logger.info(f"Item updated: {id}")
        return item

    async def delete_item(self, id: int):
        """
        Delete an item.

        Args:
            id: Item ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If item not found
        """
        deleted = await self.queries.delete(self.session, id)
        if not deleted:
            raise ValueError(f"Item with ID {id} not found")

        logger.info(f"Item deleted: {id}")
        return deleted
