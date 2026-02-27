"""Router for campaign attendees endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.base import ErrorResponse, SuccessResponse, SuccessListResponse, ErrorDetail
from app.schemas.example import CampaignAttendeeResponse, EventSummaryResponse
from app.services.example import CampaignAttendeeService
from app.middleware.auth_middleware import add_auth_context_to_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@router.get(
    "/{campaign_id}/attendees",
    response_model=SuccessListResponse[CampaignAttendeeResponse],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid campaign ID",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def get_campaign_attendees(
    request: Request,
    campaign_id: str = Path(..., description="Campaign ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    session: AsyncSession = Depends(get_session),
):
    """
    Retrieve attendees for a specific campaign.

    - **campaign_id**: Campaign ID (must be positive)
    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum results per page (default: 50, max: 100)
    """
    try:
        # Check authentication
        is_authorized, auth_data, error_response = await add_auth_context_to_request(request, session)

        if not is_authorized:
            logger.warning(f"Unauthorized access attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_response,
            )

        logger.info(f"✅ Auth passed for user {auth_data['user_id']} - Accessing campaign {campaign_id}")
        logger.info(f"📋 User campaigns: {auth_data['campaigns']}")

        service = CampaignAttendeeService(session)
        attendees, total_count = await service.get_attendees_with_count(
            campaign_id, skip=skip, limit=limit
        )

        return SuccessListResponse(
            data=attendees,
            total=total_count,
            message=f"Retrieved {len(attendees)} attendees for campaign {campaign_id}",
            timestamp=get_timestamp(),
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                message="Invalid campaign ID",
                error_code="INVALID_CAMPAIGN_ID",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error retrieving attendees: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                message="Failed to retrieve attendees",
                error_code="ATTENDEES_RETRIEVAL_ERROR",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )


@router.get(
    "/{campaign_id}/attendees/search",
    response_model=SuccessResponse[CampaignAttendeeResponse],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid parameters",
        },
        404: {
            "model": ErrorResponse,
            "description": "Attendee not found",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def get_campaign_attendee_by_email(
    request: Request,
    campaign_id: str = Path(..., description="Campaign ID"),
    email: str = Query(..., min_length=1, description="Attendee email"),
    session: AsyncSession = Depends(get_session),
):
    """
    Find a specific attendee by campaign ID and email.

    - **campaign_id**: Campaign ID (must be positive)
    - **email**: Attendee email address
    """
    try:
        # Check authentication
        is_authorized, auth_data, error_response = await add_auth_context_to_request(request, session)

        if not is_authorized:
            logger.warning(f"Unauthorized access attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_response,
            )

        logger.info(f"✅ Auth passed for user {auth_data['user_id']} - Searching attendee in campaign {campaign_id}")

        if not email or "@" not in email:
            raise ValueError("Invalid email format")

        service = CampaignAttendeeService(session)
        attendee = await service.get_attendee_by_email(campaign_id, email)

        return SuccessResponse(
            data=attendee,
            message=f"Attendee found for campaign {campaign_id}",
            timestamp=get_timestamp(),
        )
    except ValueError as e:
        logger.warning(f"Validation/not found error: {str(e)}")
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "NOT_FOUND"

        if "Invalid email" in str(e):
            status_code = status.HTTP_400_BAD_REQUEST
            error_code = "INVALID_EMAIL"

        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse(
                message="Invalid parameters or attendee not found",
                error_code=error_code,
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error searching attendee: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                message="Failed to search attendee",
                error_code="SEARCH_ERROR",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )


@router.get(
    "/{campaign_id}/event-summary",
    response_model=SuccessResponse[EventSummaryResponse],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid campaign ID",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def get_event_summary(
    request: Request,
    campaign_id: str = Path(..., description="Campaign ID"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get event summary for a campaign.

    Returns total unique attendees and companies for the campaign.

    - **campaign_id**: Campaign ID
    """
    try:
        # Check authentication
        is_authorized, auth_data, error_response = await add_auth_context_to_request(request, session)

        if not is_authorized:
            logger.warning(f"Unauthorized access attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_response,
            )

        logger.info(f"✅ Auth passed for user {auth_data['user_id']} - Getting event summary for campaign {campaign_id}")
        logger.info(f"📊 Calling get_tenant_sponsor_user and check_auth middleware functions")

        service = CampaignAttendeeService(session)
        summary = await service.get_event_summary(campaign_id)

        return SuccessResponse(
            data=summary,
            message=f"Event summary retrieved for campaign {campaign_id}",
            timestamp=get_timestamp(),
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                message="Invalid campaign ID",
                error_code="INVALID_CAMPAIGN_ID",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error retrieving event summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                message="Failed to retrieve event summary",
                error_code="SUMMARY_ERROR",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )
