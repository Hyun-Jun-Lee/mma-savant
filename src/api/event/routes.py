from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection.postgres_conn import get_async_db
from event import services as event_service
from event.dto import EventDetailDTO, EventListDTO, EventSearchDTO
from event.exceptions import EventNotFoundError, EventValidationError, EventDateError, EventQueryError


router = APIRouter(prefix="/api/events", tags=["Event"])


@router.get("", response_model=EventListDTO)
async def get_events(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await event_service.get_events(db, page=page, limit=limit, year=year, month=month)
    except EventValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except EventDateError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except EventQueryError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)


@router.get("/search", response_model=EventSearchDTO)
async def search_events(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await event_service.search_events(db, query=q, search_type="name", limit=limit)
    except EventValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except EventQueryError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)


@router.get("/{event_id}", response_model=EventDetailDTO)
async def get_event_detail(
    event_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await event_service.get_event_detail(db, event_id)
    except EventNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except EventValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except EventQueryError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)
