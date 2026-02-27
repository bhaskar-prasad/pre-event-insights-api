"""Tests for base response schemas."""

import pytest
from datetime import datetime

from app.schemas.base import ErrorDetail, ErrorResponse, SuccessResponse, SuccessListResponse


class TestErrorDetail:
    """Test suite for ErrorDetail schema."""

    def test_error_detail_with_all_fields(self):
        """Test ErrorDetail with all fields."""
        detail = ErrorDetail(
            field="email",
            message="Invalid email format",
            code="INVALID_EMAIL",
        )

        assert detail.field == "email"
        assert detail.message == "Invalid email format"
        assert detail.code == "INVALID_EMAIL"

    def test_error_detail_message_only(self):
        """Test ErrorDetail with only message (required field)."""
        detail = ErrorDetail(message="Error occurred")

        assert detail.message == "Error occurred"
        assert detail.field is None
        assert detail.code is None

    def test_error_detail_serialization(self):
        """Test ErrorDetail serialization."""
        detail = ErrorDetail(
            field="name",
            message="Name is required",
            code="REQUIRED_FIELD",
        )
        data = detail.model_dump()

        assert data["field"] == "name"
        assert data["message"] == "Name is required"
        assert data["code"] == "REQUIRED_FIELD"


class TestErrorResponse:
    """Test suite for ErrorResponse schema."""

    def test_error_response_required_fields(self):
        """Test ErrorResponse with required fields."""
        response = ErrorResponse(
            message="Authentication failed",
            error_code="AUTH_ERROR",
            timestamp="2024-01-01T00:00:00Z",
        )

        assert response.success is False
        assert response.message == "Authentication failed"
        assert response.error_code == "AUTH_ERROR"
        assert response.timestamp == "2024-01-01T00:00:00Z"
        assert response.details == []

    def test_error_response_with_details(self):
        """Test ErrorResponse with error details."""
        detail = ErrorDetail(
            field="password",
            message="Password too short",
            code="VALIDATION_ERROR",
        )
        response = ErrorResponse(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details=[detail],
            timestamp="2024-01-01T00:00:00Z",
        )

        assert len(response.details) == 1
        assert response.details[0].field == "password"

    def test_error_response_always_false(self):
        """Test that ErrorResponse success is always False."""
        response = ErrorResponse(
            message="Error",
            error_code="ERROR",
            timestamp="2024-01-01T00:00:00Z",
        )

        assert response.success is False

    def test_error_response_serialization(self):
        """Test ErrorResponse serialization."""
        response = ErrorResponse(
            message="Error message",
            error_code="ERROR_CODE",
            timestamp="2024-01-01T00:00:00Z",
        )
        data = response.model_dump()

        assert data["success"] is False
        assert data["message"] == "Error message"
        assert data["error_code"] == "ERROR_CODE"


class TestSuccessResponse:
    """Test suite for SuccessResponse schema."""

    def test_success_response_with_data(self):
        """Test SuccessResponse with data."""
        response = SuccessResponse(
            data={"id": 1, "name": "Test"},
            message="Operation successful",
            timestamp="2024-01-01T00:00:00Z",
        )

        assert response.success is True
        assert response.data == {"id": 1, "name": "Test"}
        assert response.message == "Operation successful"

    def test_success_response_default_message(self):
        """Test SuccessResponse uses default message."""
        response = SuccessResponse(
            data=None,
            timestamp="2024-01-01T00:00:00Z",
        )

        assert response.message == "Operation successful"
        assert response.success is True

    def test_success_response_always_true(self):
        """Test that SuccessResponse success is always True."""
        response = SuccessResponse(
            data="test",
            timestamp="2024-01-01T00:00:00Z",
        )

        assert response.success is True

    def test_success_response_serialization(self):
        """Test SuccessResponse serialization."""
        response = SuccessResponse(
            data="test data",
            message="Success",
            timestamp="2024-01-01T00:00:00Z",
        )
        data = response.model_dump()

        assert data["success"] is True
        assert data["message"] == "Success"
        assert data["data"] == "test data"

    def test_success_response_with_none_data(self):
        """Test SuccessResponse with None data."""
        response = SuccessResponse(
            data=None,
            timestamp="2024-01-01T00:00:00Z",
        )

        assert response.data is None
        assert response.success is True


class TestSuccessListResponse:
    """Test suite for SuccessListResponse schema."""

    def test_success_list_response_with_data(self):
        """Test SuccessListResponse with list data."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = SuccessListResponse(
            data=items,
            total=3,
            timestamp="2024-01-01T00:00:00Z",
        )

        assert response.success is True
        assert len(response.data) == 3
        assert response.total == 3

    def test_success_list_response_empty(self):
        """Test SuccessListResponse with empty list."""
        response = SuccessListResponse(
            data=[],
            total=0,
            timestamp="2024-01-01T00:00:00Z",
        )

        assert response.data == []
        assert response.total == 0
        assert response.success is True

    def test_success_list_response_default_values(self):
        """Test SuccessListResponse default values."""
        response = SuccessListResponse(
            timestamp="2024-01-01T00:00:00Z",
        )

        assert response.data == []
        assert response.total == 0
        assert response.message == "Operation successful"

    def test_success_list_response_serialization(self):
        """Test SuccessListResponse serialization."""
        items = [{"id": 1}, {"id": 2}]
        response = SuccessListResponse(
            data=items,
            total=2,
            message="Items retrieved",
            timestamp="2024-01-01T00:00:00Z",
        )
        data = response.model_dump()

        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["total"] == 2
