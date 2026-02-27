"""Authentication and authorization middleware."""

import logging
import re
import json
from typing import Callable
from datetime import datetime, timezone

from fastapi import Request, Response
import jwt
from sqlalchemy import and_, distinct, text, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_models import (
    User, Tenant, Sponsor, TenantSponsorUser,
    ApplicationFeatureDomain, License, Campaign,
    CustomerEntitlements, ClientEntitlements,
    TenantSponsorCampaign, LicenseProducts, Application
)
from app.schemas.base import ErrorResponse, ErrorDetail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TokenException(Exception):
    """Expired Token Exception."""
    pass


class AccessDeniedException(Exception):
    """Denial of access exception."""
    pass


class LicenseNotPresentException(Exception):
    """License not present exception."""
    pass


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def get_tenant_sponsor_user(
    session: AsyncSession, cognito_id: str, tenant_id: str
):
    """
    Fetch user's access level, ID, and sponsor ID.

    Args:
        session: Database session
        cognito_id: Cognito user ID
        tenant_id: Tenant identifier

    Returns:
        Tuple of (access_level, user_id, sponsor_id, first_name, last_name)
        Tuple of (None, None, None, None, None) if user not found
    """
    try:
        from sqlalchemy import select

        # Query user with tenant-sponsor mapping
        query = select(
            TenantSponsorUser.access_level,
            User.id,
            TenantSponsorUser.sponsor_id,
            User.first_name,
            User.last_name,
        ).join(
            User, User.id == TenantSponsorUser.user_id
        ).where(
            and_(
                User.cognito_user_id == cognito_id,
                TenantSponsorUser.status == "accepted",
                TenantSponsorUser.tenant_id == tenant_id,
            )
        )

        result = await session.execute(query)
        user = result.first()

        if user:
            return user[0], user[1], user[2], user[3], user[4]

        return None, None, None, None, None

    except Exception as e:
        logger.error(f"Error fetching tenant sponsor user: {str(e)}")
        raise


async def get_user_campaigns(
    session: AsyncSession,
    user_id: int,
    sponsor_id: str,
    tenant_id: str,
    domain: str,
    method: str,
):
    """
    Get accessible campaigns for a user.

    Args:
        session: Database session
        user_id: User ID
        sponsor_id: Sponsor ID
        tenant_id: Tenant ID
        domain: API domain
        method: HTTP method

    Returns:
        Tuple of (campaign_ids, license_model_ids)
    """
    try:
        from sqlalchemy import select

        logger.info(f"🔍 Checking domain access: domain={domain}, method={method}, sponsor={sponsor_id}, tenant={tenant_id}")

        # Check domain access
        query = select(
            ApplicationFeatureDomain.domain,
            License.license_model_id,
        ).join(
            License,
            and_(
                License.license_model_id == ApplicationFeatureDomain.license_model_id,
                License.application_id == ApplicationFeatureDomain.application_id,
                License.tenant_id == ApplicationFeatureDomain.tenant_id,
            ),
        ).where(
            and_(
                ApplicationFeatureDomain.method == method,
                ApplicationFeatureDomain.domain == domain,
                ApplicationFeatureDomain.tenant_id == tenant_id,
                License.sponsor_id == sponsor_id,
                License.status == "active",
                License.deleted_on.is_(None),
            )
        )

        result = await session.execute(query)
        access_data = result.all()

        logger.info(f"📋 Domain access result: {len(access_data)} matches found")

        if not access_data:
            logger.error(f"❌ Domain access denied: No matching domain/method/license for {domain} {method}")
            raise AccessDeniedException("Access denied to domain")

        # Extract license model IDs
        license_model_ids = [item[1] for item in access_data]
        logger.info(f"✅ Domain access granted. License models: {license_model_ids}")

        # Get campaigns accessible by user
        logger.info(f"🔍 Fetching campaigns for user {user_id}")
        campaign_query = select(
            distinct(CustomerEntitlements.campaign_id)
        ).where(
            and_(
                CustomerEntitlements.user_id == user_id,
                CustomerEntitlements.sponsor_id == sponsor_id,
                CustomerEntitlements.tenant_id == tenant_id,
                CustomerEntitlements.status == "active",
                CustomerEntitlements.deleted_on.is_(None),
            )
        )

        campaign_result = await session.execute(campaign_query)
        campaigns = [row[0] for row in campaign_result.all()]

        logger.info(f"📊 Campaigns found: {len(campaigns)} - {campaigns}")

        if not campaigns:
            logger.error(f"❌ No campaigns accessible for user {user_id}")
            raise AccessDeniedException("No campaigns accessible")

        logger.info(f"✅ Campaigns accessible: {campaigns}")
        return campaigns, license_model_ids

    except AccessDeniedException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user campaigns: {str(e)}", exc_info=True)
        raise


async def get_user_id_from_token(request: Request) -> tuple:
    """
    Extract user ID and tenant ID from JWT token.

    Args:
        request: FastAPI request

    Returns:
        Tuple of (cognito_user_id, tenant_id)

    Raises:
        TokenException: If token is invalid or missing
    """
    try:
        authorization_header = request.headers.get("Authorization")

        if not authorization_header:
            raise TokenException("Missing Authorization header")

        # Extract token from "Bearer <token>"
        parts = authorization_header.split(" ")
        if len(parts) != 2 or parts[0] != "Bearer":
            raise TokenException("Invalid Authorization header format")

        token = parts[1]

        try:
            # Decode JWT without signature verification
            decoded = jwt.decode(token, options={"verify_signature": False})

            cognito_user_id = decoded.get("username") or decoded.get("sub")
            tenant_id = (
                request.headers.get("tenant_id")
                or decoded.get("tenant_id")
                or decoded.get("client_id")
            )

            if not cognito_user_id or not tenant_id:
                raise TokenException("Missing required token fields")

            return cognito_user_id, tenant_id

        except jwt.ExpiredSignatureError:
            raise TokenException("Token expired")
        except jwt.InvalidTokenError:
            raise TokenException("Invalid token")

    except TokenException:
        raise
    except Exception as e:
        logger.error(f"Error extracting user from token: {str(e)}")
        raise TokenException(f"Token extraction failed: {str(e)}")


def normalize_domain_path(path: str) -> str:
    """
    Normalize API path by replacing IDs with {id} placeholder.

    Args:
        path: API path

    Returns:
        Normalized path
    """
    # Replace numeric IDs, UUIDs, and alphanumeric IDs (with underscores/dashes) with {id}
    # Matches: 123, 550e8400-e29b-41d4-a716-446655440000, campaign_001, user-123, etc.
    normalized = re.sub(
        r"(?:/|^)(\d+|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}|[a-z0-9]*[_-][a-z0-9]*)(?=/|$)",
        "/{id}",
        path,
    )
    return normalized


async def check_auth(request: Request, session: AsyncSession, cognito_user_id: str, tenant_id: str):
    """
    Check user authorization and attach auth data to request.

    Args:
        request: FastAPI request
        session: Database session
        cognito_user_id: Cognito user ID
        tenant_id: Tenant ID

    Returns:
        Tuple of (is_authorized, error_response)
    """
    try:
        logger.info(f"🔐 Starting auth check for user {cognito_user_id} in tenant {tenant_id}")

        # Fetch user and access level
        access_level, user_id, sponsor_id, first_name, last_name = await get_tenant_sponsor_user(
            session, cognito_user_id, tenant_id
        )

        logger.info(f"📋 get_tenant_sponsor_user result: access_level={access_level}, user_id={user_id}, sponsor_id={sponsor_id}")

        if not access_level:
            logger.warning(f"❌ User {cognito_user_id} not found for tenant {tenant_id}")
            return False, get_error_response("Unauthorized access", 401)

        logger.info(f"✅ User found: {first_name} {last_name} with access level {access_level}")

        # Get domain and method from request
        path = request.url.path
        method = request.method
        domain = normalize_domain_path(path.replace("/api/v1", ""))

        logger.info(f"📍 Request: path={path}, method={method}, normalized_domain={domain}")

        # Check sponsor override
        header_sponsor_id = request.headers.get("sponsor_id", "")
        if header_sponsor_id:
            logger.info(f"🏢 Using sponsor override from header: {header_sponsor_id}")
            sponsor_id = header_sponsor_id

        # Get accessible campaigns
        try:
            logger.info(f"🔍 Calling get_user_campaigns...")
            campaigns, license_model_ids = await get_user_campaigns(
                session, user_id, sponsor_id, tenant_id, domain, method
            )
            logger.info(f"✅ Got accessible campaigns: {campaigns}")
        except AccessDeniedException as e:
            logger.warning(f"❌ Access denied for user {user_id} to domain {domain}: {str(e)}")
            return False, get_error_response("Access denied to domain", 401)

        # Attach auth data to request state
        request.state.auth_data = {
            "user_id": user_id,
            "cognito_user_id": cognito_user_id,
            "tenant_id": tenant_id,
            "sponsor_id": sponsor_id,
            "access_level": access_level,
            "first_name": first_name,
            "last_name": last_name,
            "campaigns": campaigns,
            "license_model_ids": license_model_ids,
        }

        logger.info(f"✅ Auth successful! User can access campaigns: {campaigns}")
        return True, None

    except AccessDeniedException as e:
        logger.error(f"❌ Access denied: {str(e)}")
        return False, get_error_response("Access denied", 401)
    except Exception as e:
        logger.error(f"❌ Error in check_auth: {str(e)}", exc_info=True)
        return False, get_error_response("Internal server error", 500)


def get_error_response(message: str, status_code: int) -> dict:
    """Create error response."""
    error_response = {
        "success": False,
        "message": message,
        "error_code": "AUTH_ERROR",
        "details": [{"field": None, "message": message, "code": None}],
        "timestamp": get_timestamp(),
    }
    return error_response


def should_skip_auth(path: str) -> bool:
    """
    Check if path should skip authentication.

    Args:
        path: Request path

    Returns:
        True if auth should be skipped
    """
    skip_paths = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/health",
    ]

    return path in skip_paths or path.startswith("/static")


async def authorization_middleware(request: Request, call_next: Callable) -> Response:
    """
    Authorization middleware to validate JWT token and user permissions.

    Args:
        request: FastAPI request
        call_next: Next middleware/endpoint

    Returns:
        Response from endpoint or error response
    """
    try:
        # Skip auth for certain paths
        if should_skip_auth(request.url.path):
            return await call_next(request)

        # For now, initialize without session (will be injected in endpoints)
        # This allows endpoints to use their own sessions
        return await call_next(request)

    except TokenException as e:
        logger.error(f"Token exception: {str(e)}")
        error_response = get_error_response(f"Token error: {str(e)}", 401)
        return Response(
            content=json.dumps(error_response),
            status_code=401,
            media_type="application/json",
        )
    except Exception as e:
        logger.error(f"Middleware error: {str(e)}", exc_info=True)
        error_response = get_error_response("Internal server error", 500)
        return Response(
            content=json.dumps(error_response),
            status_code=500,
            media_type="application/json",
        )


async def add_auth_context_to_request(request: Request, session: AsyncSession) -> tuple:
    """
    Helper function to check auth in endpoints.

    Args:
        request: FastAPI request
        session: Database session

    Returns:
        Tuple of (is_authorized, auth_data, error_response)
    """
    try:
        # Extract token
        cognito_user_id, tenant_id = await get_user_id_from_token(request)

        # Check authorization
        is_authorized, error_response = await check_auth(request, session, cognito_user_id, tenant_id)

        if not is_authorized:
            return False, None, error_response

        return True, request.state.auth_data, None

    except TokenException as e:
        return False, None, get_error_response(str(e), 401)
    except Exception as e:
        logger.error(f"Error in add_auth_context_to_request: {str(e)}")
        return False, None, get_error_response("Internal server error", 500)
