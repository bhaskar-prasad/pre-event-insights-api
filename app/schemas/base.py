from pydantic import BaseModel, Field
from typing import Any, Optional, Generic, TypeVar


class ErrorDetail(BaseModel):
    """Error detail information."""

    field: Optional[str] = Field(
        None, description="Field name that caused the error (for validation errors)"
    )
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standardized error response format."""

    success: bool = Field(False, description="Always False for error responses")
    message: str = Field(..., description="High-level error message")
    error_code: str = Field(
        ..., description="Error code for programmatic handling"
    )
    details: list[ErrorDetail] = Field(
        default_factory=list, description="Detailed error information"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp of when error occurred")


T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standardized success response format."""

    success: bool = Field(True, description="Always True for success responses")
    message: str = Field(
        default="Operation successful", description="Success message"
    )
    data: Optional[T] = Field(None, description="Response payload")
    timestamp: str = Field(..., description="ISO 8601 timestamp of response")


class SuccessListResponse(BaseModel, Generic[T]):
    """Standardized list response format."""

    success: bool = Field(True, description="Always True for success responses")
    message: str = Field(
        default="Operation successful", description="Success message"
    )
    data: list[T] = Field(default_factory=list, description="List of items")
    total: int = Field(0, description="Total count of items")
    timestamp: str = Field(..., description="ISO 8601 timestamp of response")
