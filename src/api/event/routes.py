from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection.postgres_conn import get_async_db
from event import services as event_service
from event.dto import EventDetailDTO
from event.exceptions import EventNotFoundError, EventValidationError, EventQueryError


router = APIRouter(prefix="/api/events", tags=["Event"])


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
