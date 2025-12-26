"""
LANCH - Pagination Utilities
Provides consistent pagination across all list endpoints
"""

from typing import TypeVar, Generic, List, Optional, Any
from pydantic import BaseModel, Field
from fastapi import Query
from sqlalchemy.orm import Query as SQLQuery


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of records to return")
    
    @property
    def offset(self) -> int:
        """Alias for skip"""
        return self.skip
    

class PagedResponse(BaseModel, Generic[T]):
    """Generic paged response model"""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool
    
    @classmethod
    def create(cls, items: List[T], total: int, skip: int, limit: int):
        """Create a paged response"""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )


class PaginatedResponse(BaseModel):
    """Paginated response with page-based navigation"""
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool


def paginate(query: SQLQuery, page: int = 1, limit: int = 20) -> PaginatedResponse:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        limit: Items per page
        
    Returns:
        PaginatedResponse with items and pagination info
    """
    total = query.count()
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    # Ensure page is within bounds
    page = max(1, min(page, pages))
    
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


def get_pagination_params(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of records")
) -> PaginationParams:
    """
    Dependency to get pagination parameters from query string
    
    Usage:
        @app.get("/items")
        def get_items(pagination: PaginationParams = Depends(get_pagination_params)):
            items = db.query(Item).offset(pagination.skip).limit(pagination.limit).all()
            total = db.query(Item).count()
            return PagedResponse.create(items, total, pagination.skip, pagination.limit)
    """
    return PaginationParams(skip=skip, limit=limit)

