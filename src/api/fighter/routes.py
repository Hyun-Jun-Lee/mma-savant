from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection.postgres_conn import get_async_db
from fighter import services as fighter_service
from fighter.dto import FighterDetailResponseDTO, FighterWithRankingsDTO
from fighter.exceptions import FighterNotFoundError, FighterValidationError, FighterQueryError, FighterSearchError


router = APIRouter(prefix="/api/fighters", tags=["Fighter"])


@router.get("/search", response_model=List[FighterWithRankingsDTO])
async def search_fighters(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await fighter_service.search_fighters(db, q, limit)
    except FighterValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except FighterSearchError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)


@router.get("/{fighter_id}", response_model=FighterDetailResponseDTO)
async def get_fighter_detail(
    fighter_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await fighter_service.get_fighter_detail(db, fighter_id)
    except FighterNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except FighterValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except FighterQueryError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)
