"""Example router demonstrating FastAPI endpoints with consistent responses."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.base import ErrorResponse, SuccessResponse, ErrorDetail
from app.services.example import ExampleService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/examples", tags=["examples"])


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


@router.get(
    "/",
    response_model=SuccessResponse,
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        }
    },
)
async def list_items(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
):
    """
    List all items with pagination.

    - **skip**: Number of items to skip (default: 0)
    - **limit**: Maximum items to return (default: 10)
    """
    try:
        service = ExampleService(session)
        items = await service.list_items(skip=skip, limit=limit)

        return SuccessResponse(
            data=items,
            message="Items retrieved successfully",
            timestamp=get_timestamp(),
        )
    except Exception as e:
        logger.error(f"Error listing items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                message="Failed to retrieve items",
                error_code="LIST_ERROR",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )


@router.get(
    "/{item_id}",
    response_model=SuccessResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    """Get a single item by ID."""
    try:
        service = ExampleService(session)
        item = await service.get_item(item_id)

        return SuccessResponse(
            data=item,
            message="Item retrieved successfully",
            timestamp=get_timestamp(),
        )
    except ValueError as e:
        logger.warning(f"Item not found: {item_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                message="Item not found",
                error_code="NOT_FOUND",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                message="Failed to retrieve item",
                error_code="GET_ERROR",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )


@router.post(
    "/",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def create_item(
    data: dict,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new item.

    - **data**: Item attributes
    """
    try:
        service = ExampleService(session)
        item = await service.create_item(**data)

        return SuccessResponse(
            data=item,
            message="Item created successfully",
            timestamp=get_timestamp(),
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                message="Invalid request data",
                error_code="VALIDATION_ERROR",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                message="Failed to create item",
                error_code="CREATE_ERROR",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )


@router.put(
    "/{item_id}",
    response_model=SuccessResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
        },
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def update_item(
    item_id: int,
    data: dict,
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing item.

    - **item_id**: ID of the item to update
    - **data**: Fields to update
    """
    try:
        service = ExampleService(session)
        item = await service.update_item(item_id, **data)

        return SuccessResponse(
            data=item,
            message="Item updated successfully",
            timestamp=get_timestamp(),
        )
    except ValueError as e:
        logger.warning(f"Update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                message="Item not found",
                error_code="NOT_FOUND",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                message="Failed to update item",
                error_code="UPDATE_ERROR",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )


@router.delete(
    "/{item_id}",
    response_model=SuccessResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
async def delete_item(item_id: int, session: AsyncSession = Depends(get_session)):
    """Delete an item by ID."""
    try:
        service = ExampleService(session)
        await service.delete_item(item_id)

        return SuccessResponse(
            data={"id": item_id},
            message="Item deleted successfully",
            timestamp=get_timestamp(),
        )
    except ValueError as e:
        logger.warning(f"Delete error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                message="Item not found",
                error_code="NOT_FOUND",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                message="Failed to delete item",
                error_code="DELETE_ERROR",
                details=[ErrorDetail(message=str(e))],
                timestamp=get_timestamp(),
            ).model_dump(),
        )
