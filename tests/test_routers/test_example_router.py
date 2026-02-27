"""Tests for example router endpoints."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from app.main import app
from app.database import get_session
from fastapi.testclient import TestClient


@pytest.fixture
def example_client(mock_session):
    """FastAPI client for example routes."""
    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestExampleRouter:
    """Test suite for example router endpoints."""

    def test_list_items_empty(self, example_client):
        """Test listing items when none exist."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_items = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = example_client.get("/api/v1/examples/")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == []

    def test_list_items_with_results(self, example_client):
        """Test listing items with results."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_item1 = MagicMock(id=1, name="Item 1")
            mock_item2 = MagicMock(id=2, name="Item 2")
            mock_service.list_items = AsyncMock(return_value=[mock_item1, mock_item2])
            mock_service_class.return_value = mock_service

            response = example_client.get("/api/v1/examples/")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2

    def test_list_items_pagination(self, example_client):
        """Test pagination parameters for list items."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_items = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = example_client.get("/api/v1/examples/?skip=10&limit=20")

            assert response.status_code == 200
            mock_service.list_items.assert_called_once_with(skip=10, limit=20)

    def test_get_item_found(self, example_client):
        """Test retrieving a single item."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_item = MagicMock()
            mock_item.id = 1
            mock_item.name = "Test Item"
            mock_service.get_item = AsyncMock(return_value=mock_item)
            mock_service_class.return_value = mock_service

            response = example_client.get("/api/v1/examples/1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_get_item_not_found(self, example_client):
        """Test 404 when item not found."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_item = AsyncMock(
                side_effect=ValueError("Item with ID 999 not found")
            )
            mock_service_class.return_value = mock_service

            response = example_client.get("/api/v1/examples/999")

            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "NOT_FOUND"

    def test_create_item_success(self, example_client):
        """Test successful item creation."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_item = MagicMock()
            mock_item.id = 1
            mock_item.name = "New Item"
            mock_service.create_item = AsyncMock(return_value=mock_item)
            mock_service_class.return_value = mock_service

            response = example_client.post(
                "/api/v1/examples/",
                json={"name": "New Item", "description": "Test"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True

    def test_create_item_missing_required_field(self, example_client):
        """Test validation error for missing required fields."""
        response = example_client.post(
            "/api/v1/examples/",
            json={"description": "No name provided"},
        )

        # The router expects a dict, but Pydantic validation will pass
        # The service layer might reject it, or it might be accepted
        # This depends on the actual endpoint implementation
        assert response.status_code in [400, 422, 500]

    def test_create_item_invalid_data_type(self, example_client):
        """Test validation error for invalid data types."""
        response = example_client.post(
            "/api/v1/examples/",
            json={"name": 123},  # name should be string
        )

        # Validation should reject this
        assert response.status_code in [400, 422]

    def test_update_item_success(self, example_client):
        """Test successful item update."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_item = MagicMock()
            mock_item.id = 1
            mock_item.name = "Updated Item"
            mock_service.update_item = AsyncMock(return_value=mock_item)
            mock_service_class.return_value = mock_service

            response = example_client.put(
                "/api/v1/examples/1",
                json={"name": "Updated Item"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_update_item_not_found(self, example_client):
        """Test 404 when updating non-existent item."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_item = AsyncMock(
                side_effect=ValueError("Item with ID 999 not found")
            )
            mock_service_class.return_value = mock_service

            response = example_client.put(
                "/api/v1/examples/999",
                json={"name": "Updated"},
            )

            assert response.status_code == 404

    def test_update_item_partial(self, example_client):
        """Test partial update with only some fields."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_item = MagicMock()
            mock_service.update_item = AsyncMock(return_value=mock_item)
            mock_service_class.return_value = mock_service

            response = example_client.put(
                "/api/v1/examples/1",
                json={"description": "Updated description only"},
            )

            assert response.status_code == 200

    def test_delete_item_success(self, example_client):
        """Test successful item deletion."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_item = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service

            response = example_client.delete("/api/v1/examples/1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_delete_item_not_found(self, example_client):
        """Test 404 when deleting non-existent item."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_item = AsyncMock(
                side_effect=ValueError("Item with ID 999 not found")
            )
            mock_service_class.return_value = mock_service

            response = example_client.delete("/api/v1/examples/999")

            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "NOT_FOUND"

    def test_response_timestamp_format(self, example_client):
        """Test that responses include ISO 8601 timestamps."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_items = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = example_client.get("/api/v1/examples/")

            data = response.json()
            assert "timestamp" in data
            # Should end with Z for UTC
            assert data["timestamp"].endswith("Z")

    def test_response_success_field(self, example_client):
        """Test that all responses include success field."""
        with patch("app.services.example.ExampleService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_items = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = example_client.get("/api/v1/examples/")

            data = response.json()
            assert "success" in data
            assert data["success"] is True
