"""
Common Pydantic schemas for API.
"""
from ninja import Schema
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class ErrorSchema(Schema):
    """Standard error response."""
    detail: str


class PaginatedResponse(Schema):
    """Paginated response wrapper."""
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[Any]


class SuccessSchema(Schema):
    """Generic success response."""
    status: str = "ok"
    message: str = ""


class SyncStatusSchema(Schema):
    """Sync status response."""
    id: str
    status: str
    message: str = ""


class LocationSchema(Schema):
    """Geographic location."""
    latitud: float
    longitud: float
    precision_metros: Optional[float] = None
