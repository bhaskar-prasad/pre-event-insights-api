"""Tests for authentication middleware."""

import pytest
import jwt
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta

from app.middleware.auth_middleware import (
    normalize_domain_path,
    get_user_id_from_token,
    should_skip_auth,
    check_auth,
    get_error_response,
    add_auth_context_to_request,
    TokenException,
    AccessDeniedException,
)


class TestNormalizeDomainPath:
    """Test suite for normalize_domain_path function."""

    def test_numeric_id_normalization(self):
        """Test that numeric IDs are normalized to {id}."""
        assert normalize_domain_path("/campaigns/123/attendees") == "/campaigns/{id}/attendees"
        assert normalize_domain_path("/123/test") == "/{id}/test"

    def test_uuid_normalization(self):
        """Test that UUIDs are normalized to {id}."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        path = f"/campaigns/{uuid}/attendees"
        normalized = normalize_domain_path(path)
        assert normalized == "/campaigns/{id}/attendees"

    def test_alphanumeric_with_underscore_normalization(self):
        """Test that alphanumeric IDs with underscores are normalized."""
        assert normalize_domain_path("/campaigns/campaign_001/attendees") == "/campaigns/{id}/attendees"
        assert normalize_domain_path("/campaigns/user_456/detail") == "/campaigns/{id}/detail"

    def test_alphanumeric_with_dash_normalization(self):
        """Test that alphanumeric IDs with dashes are normalized."""
        assert normalize_domain_path("/campaigns/user-456/data") == "/campaigns/{id}/data"
        assert normalize_domain_path("/campaigns/resource-name") == "/campaigns/{id}"

    def test_literal_routes_unchanged(self):
        """Test that literal routes without IDs are unchanged."""
        assert normalize_domain_path("/campaigns/attendees") == "/campaigns/attendees"
        assert normalize_domain_path("/health") == "/health"
        assert normalize_domain_path("/api/v1/examples") == "/api/v1/examples"

    def test_multiple_ids_in_path(self):
        """Test normalization of paths with multiple IDs."""
        path = "/campaigns/campaign_001/attendees/123"
        normalized = normalize_domain_path(path)
        assert normalized == "/campaigns/{id}/attendees/{id}"

    def test_empty_path(self):
        """Test normalization of empty path."""
        assert normalize_domain_path("") == ""

    def test_path_with_trailing_slash(self):
        """Test normalization with trailing slash."""
        assert normalize_domain_path("/campaigns/campaign_001/") == "/campaigns/{id}/"


class TestGetUserIdFromToken:
    """Test suite for get_user_id_from_token function."""

    @pytest.mark.asyncio
    async def test_valid_token_with_username(self):
        """Test extraction of user ID and tenant ID from valid token."""
        payload = {
            "username": "user_cognito_001",
            "tenant_id": "tenant_001",
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "Authorization": f"Bearer {token}",
            "tenant_id": None,
        }.get(key)

        cognito_id, tenant_id = await get_user_id_from_token(request)
        assert cognito_id == "user_cognito_001"
        assert tenant_id == "tenant_001"

    @pytest.mark.asyncio
    async def test_valid_token_with_sub(self):
        """Test extraction using 'sub' claim if 'username' is missing."""
        payload = {
            "sub": "user_cognito_002",
            "tenant_id": "tenant_002",
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "Authorization": f"Bearer {token}",
            "tenant_id": None,
        }.get(key)

        cognito_id, tenant_id = await get_user_id_from_token(request)
        assert cognito_id == "user_cognito_002"
        assert tenant_id == "tenant_002"

    @pytest.mark.asyncio
    async def test_tenant_id_from_header(self):
        """Test that tenant_id can come from request header."""
        payload = {
            "username": "user_cognito_001",
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "Authorization": f"Bearer {token}",
            "tenant_id": "tenant_from_header",
        }.get(key)

        cognito_id, tenant_id = await get_user_id_from_token(request)
        assert cognito_id == "user_cognito_001"
        assert tenant_id == "tenant_from_header"

    @pytest.mark.asyncio
    async def test_missing_authorization_header(self):
        """Test error when Authorization header is missing."""
        request = MagicMock()
        request.headers.get.return_value = None

        with pytest.raises(TokenException, match="Missing Authorization header"):
            await get_user_id_from_token(request)

    @pytest.mark.asyncio
    async def test_invalid_authorization_format(self):
        """Test error when Authorization header format is invalid."""
        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "Authorization": "InvalidFormat token",
        }.get(key)

        with pytest.raises(TokenException, match="Invalid Authorization header format"):
            await get_user_id_from_token(request)

    @pytest.mark.asyncio
    async def test_missing_token_fields(self):
        """Test error when required token fields are missing."""
        payload = {
            "username": "user_cognito_001",
            # tenant_id missing
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "Authorization": f"Bearer {token}",
            "tenant_id": None,
        }.get(key)

        with pytest.raises(TokenException, match="Missing required token fields"):
            await get_user_id_from_token(request)


class TestShouldSkipAuth:
    """Test suite for should_skip_auth function."""

    def test_skip_docs(self):
        """Test that /docs path skips auth."""
        assert should_skip_auth("/docs") is True

    def test_skip_redoc(self):
        """Test that /redoc path skips auth."""
        assert should_skip_auth("/redoc") is True

    def test_skip_openapi(self):
        """Test that /openapi.json path skips auth."""
        assert should_skip_auth("/openapi.json") is True

    def test_skip_health_v1(self):
        """Test that /api/v1/health path skips auth."""
        assert should_skip_auth("/api/v1/health") is True

    def test_skip_health_root(self):
        """Test that /health path skips auth."""
        assert should_skip_auth("/health") is True

    def test_skip_static_files(self):
        """Test that /static/* paths skip auth."""
        assert should_skip_auth("/static/file.js") is True
        assert should_skip_auth("/static/css/style.css") is True

    def test_no_skip_for_api_endpoints(self):
        """Test that API endpoints don't skip auth."""
        assert should_skip_auth("/api/v1/campaigns") is False
        assert should_skip_auth("/api/v1/examples") is False

    def test_no_skip_for_campaigns(self):
        """Test that campaign endpoints don't skip auth."""
        assert should_skip_auth("/api/v1/campaigns/campaign_001/attendees") is False


class TestGetErrorResponse:
    """Test suite for get_error_response function."""

    def test_error_response_structure(self):
        """Test that error response has correct structure."""
        response = get_error_response("Test error", 401)

        assert response["success"] is False
        assert response["message"] == "Test error"
        assert response["error_code"] == "AUTH_ERROR"
        assert "timestamp" in response
        assert response["details"][0]["message"] == "Test error"

    def test_error_response_different_codes(self):
        """Test error response with different status codes."""
        response_401 = get_error_response("Unauthorized", 401)
        response_500 = get_error_response("Server error", 500)

        assert response_401["error_code"] == "AUTH_ERROR"
        assert response_500["error_code"] == "AUTH_ERROR"


class TestCheckAuth:
    """Test suite for check_auth function."""

    @pytest.mark.asyncio
    async def test_check_auth_success(self, mock_session, mock_request, mock_auth_data):
        """Test successful auth check."""
        # Mock get_tenant_sponsor_user to return user data
        with patch("app.middleware.auth_middleware.get_tenant_sponsor_user") as mock_get_user:
            mock_get_user.return_value = (
                "admin",  # access_level
                1,  # user_id
                "sponsor_001",  # sponsor_id
                "Test",  # first_name
                "User",  # last_name
            )

            with patch("app.middleware.auth_middleware.get_user_campaigns") as mock_get_campaigns:
                mock_get_campaigns.return_value = (
                    ["campaign_001"],  # campaigns
                    [1],  # license_model_ids
                )

                is_authorized, error_response = await check_auth(
                    mock_request, mock_session, "user_cognito_001", "tenant_001"
                )

                assert is_authorized is True
                assert error_response is None
                assert mock_request.state.auth_data["user_id"] == 1
                assert mock_request.state.auth_data["campaigns"] == ["campaign_001"]

    @pytest.mark.asyncio
    async def test_check_auth_user_not_found(self, mock_session, mock_request):
        """Test auth check when user is not found."""
        with patch("app.middleware.auth_middleware.get_tenant_sponsor_user") as mock_get_user:
            mock_get_user.return_value = (None, None, None, None, None)

            is_authorized, error_response = await check_auth(
                mock_request, mock_session, "unknown_user", "tenant_001"
            )

            assert is_authorized is False
            assert error_response is not None
            assert error_response["error_code"] == "AUTH_ERROR"

    @pytest.mark.asyncio
    async def test_check_auth_access_denied(self, mock_session, mock_request):
        """Test auth check when access is denied."""
        with patch("app.middleware.auth_middleware.get_tenant_sponsor_user") as mock_get_user:
            mock_get_user.return_value = (
                "viewer",  # access_level
                1,  # user_id
                "sponsor_001",  # sponsor_id
                "Test",  # first_name
                "User",  # last_name
            )

            with patch("app.middleware.auth_middleware.get_user_campaigns") as mock_get_campaigns:
                mock_get_campaigns.side_effect = AccessDeniedException("No campaigns accessible")

                is_authorized, error_response = await check_auth(
                    mock_request, mock_session, "user_cognito_001", "tenant_001"
                )

                assert is_authorized is False
                assert error_response is not None


class TestAddAuthContextToRequest:
    """Test suite for add_auth_context_to_request function."""

    @pytest.mark.asyncio
    async def test_add_auth_context_success(self, mock_session, mock_auth_request):
        """Test successful auth context addition."""
        token = jwt.encode(
            {"username": "user_cognito_001", "tenant_id": "tenant_001"},
            "secret",
            algorithm="HS256",
        )
        mock_auth_request.headers.get.side_effect = lambda key: {
            "Authorization": f"Bearer {token}",
            "tenant_id": "tenant_001",
        }.get(key)

        with patch("app.middleware.auth_middleware.get_user_id_from_token") as mock_get_token:
            mock_get_token.return_value = ("user_cognito_001", "tenant_001")

            with patch("app.middleware.auth_middleware.check_auth") as mock_check:
                mock_check.return_value = (True, None)
                mock_auth_request.state.auth_data = {
                    "user_id": 1,
                    "campaigns": ["campaign_001"],
                }

                is_authorized, auth_data, error_response = await add_auth_context_to_request(
                    mock_auth_request, mock_session
                )

                assert is_authorized is True
                assert auth_data is not None
                assert error_response is None

    @pytest.mark.asyncio
    async def test_add_auth_context_invalid_token(self, mock_session, mock_auth_request):
        """Test auth context with invalid token."""
        mock_auth_request.headers.get.return_value = None

        is_authorized, auth_data, error_response = await add_auth_context_to_request(
            mock_auth_request, mock_session
        )

        assert is_authorized is False
        assert auth_data is None
        assert error_response is not None
        assert error_response["error_code"] == "AUTH_ERROR"

    @pytest.mark.asyncio
    async def test_add_auth_context_unauthorized(self, mock_session, mock_auth_request):
        """Test auth context when authorization fails."""
        token = jwt.encode(
            {"username": "user_cognito_001", "tenant_id": "tenant_001"},
            "secret",
            algorithm="HS256",
        )
        mock_auth_request.headers.get.side_effect = lambda key: {
            "Authorization": f"Bearer {token}",
            "tenant_id": "tenant_001",
        }.get(key)

        with patch("app.middleware.auth_middleware.get_user_id_from_token") as mock_get_token:
            mock_get_token.return_value = ("user_cognito_001", "tenant_001")

            with patch("app.middleware.auth_middleware.check_auth") as mock_check:
                mock_check.return_value = (False, {"error_code": "AUTH_ERROR"})

                is_authorized, auth_data, error_response = await add_auth_context_to_request(
                    mock_auth_request, mock_session
                )

                assert is_authorized is False
                assert auth_data is None
                assert error_response is not None
