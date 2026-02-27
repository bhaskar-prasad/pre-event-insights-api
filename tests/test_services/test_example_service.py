"""Tests for ExampleService."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.example import ExampleService
from app.models.example import Example


class TestExampleService:
    """Test suite for ExampleService."""

    @pytest.mark.asyncio
    async def test_get_item_found(self, mock_session):
        """Test retrieving an existing item."""
        mock_item = MagicMock(spec=Example)
        mock_item.id = 1
        mock_item.name = "Test Item"

        service = ExampleService(mock_session)
        service.queries.get_by_id = AsyncMock(return_value=mock_item)

        result = await service.get_item(1)

        assert result.id == 1
        assert result.name == "Test Item"
        service.queries.get_by_id.assert_called_once_with(mock_session, 1)

    @pytest.mark.asyncio
    async def test_get_item_not_found(self, mock_session):
        """Test error when item not found."""
        service = ExampleService(mock_session)
        service.queries.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Item with ID .* not found"):
            await service.get_item(999)

    @pytest.mark.asyncio
    async def test_list_items(self, mock_session):
        """Test listing items with pagination."""
        mock_items = [
            MagicMock(spec=Example, id=1),
            MagicMock(spec=Example, id=2),
        ]
        service = ExampleService(mock_session)
        service.queries.get_all = AsyncMock(return_value=mock_items)

        result = await service.list_items(skip=0, limit=10)

        assert len(result) == 2
        service.queries.get_all.assert_called_once_with(mock_session, skip=0, limit=10)

    @pytest.mark.asyncio
    async def test_list_items_empty(self, mock_session):
        """Test listing items when no items exist."""
        service = ExampleService(mock_session)
        service.queries.get_all = AsyncMock(return_value=[])

        result = await service.list_items()

        assert result == []

    @pytest.mark.asyncio
    async def test_create_item(self, mock_session):
        """Test creating a new item."""
        mock_item = MagicMock(spec=Example)
        mock_item.id = 1
        mock_item.name = "New Item"

        service = ExampleService(mock_session)
        service.queries.create = AsyncMock(return_value=mock_item)

        result = await service.create_item(name="New Item")

        assert result.id == 1
        service.queries.create.assert_called_once_with(mock_session, name="New Item")

    @pytest.mark.asyncio
    async def test_create_item_with_kwargs(self, mock_session):
        """Test creating item with multiple kwargs."""
        mock_item = MagicMock(spec=Example)
        service = ExampleService(mock_session)
        service.queries.create = AsyncMock(return_value=mock_item)

        await service.create_item(name="Test", description="A test item")

        service.queries.create.assert_called_once_with(
            mock_session, name="Test", description="A test item"
        )

    @pytest.mark.asyncio
    async def test_create_item_error(self, mock_session):
        """Test error handling during item creation."""
        service = ExampleService(mock_session)
        service.queries.create = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception, match="Database error"):
            await service.create_item(name="Test")

    @pytest.mark.asyncio
    async def test_update_item_found(self, mock_session):
        """Test updating an existing item."""
        mock_item = MagicMock(spec=Example)
        mock_item.id = 1
        mock_item.name = "Updated Item"

        service = ExampleService(mock_session)
        service.queries.update = AsyncMock(return_value=mock_item)

        result = await service.update_item(1, name="Updated Item")

        assert result.id == 1
        assert result.name == "Updated Item"
        service.queries.update.assert_called_once_with(mock_session, 1, name="Updated Item")

    @pytest.mark.asyncio
    async def test_update_item_not_found(self, mock_session):
        """Test error when updating non-existent item."""
        service = ExampleService(mock_session)
        service.queries.update = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Item with ID .* not found"):
            await service.update_item(999, name="New Name")

    @pytest.mark.asyncio
    async def test_delete_item_found(self, mock_session):
        """Test deleting an existing item."""
        service = ExampleService(mock_session)
        service.queries.delete = AsyncMock(return_value=True)

        result = await service.delete_item(1)

        assert result is True
        service.queries.delete.assert_called_once_with(mock_session, 1)

    @pytest.mark.asyncio
    async def test_delete_item_not_found(self, mock_session):
        """Test error when deleting non-existent item."""
        service = ExampleService(mock_session)
        service.queries.delete = AsyncMock(return_value=False)

        with pytest.raises(ValueError, match="Item with ID .* not found"):
            await service.delete_item(999)
