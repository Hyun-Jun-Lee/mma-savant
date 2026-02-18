"""
Dashboard API 라우터
탭별 aggregate 엔드포인트 제공
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection.postgres_conn import get_async_db
from dashboard import services as dashboard_service
from dashboard.dto import (
    HomeResponseDTO,
    OverviewResponseDTO,
    StrikingResponseDTO,
    GrapplingResponseDTO,
)
from dashboard.exceptions import DashboardQueryError


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/home", response_model=HomeResponseDTO)
async def get_home(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Home 탭 데이터: 요약 카드 + 최근/향후 이벤트 + 랭킹
    """
    try:
        return await dashboard_service.get_home(db)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/overview", response_model=OverviewResponseDTO)
async def get_overview(
    weight_class_id: Optional[int] = None,
    ufc_only: bool = False,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Overview 탭 데이터: 피니시 분포, 체급별 활동, 이벤트 추이, 리더보드, 종료 라운드
    """
    try:
        return await dashboard_service.get_overview(db, weight_class_id, ufc_only)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/striking", response_model=StrikingResponseDTO)
async def get_striking(
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Striking 탭 데이터: 타격 부위, 타격 정확도, KO/TKO TOP, 경기당 유효타격
    """
    try:
        return await dashboard_service.get_striking(db, weight_class_id, min_fights, limit)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/grappling", response_model=GrapplingResponseDTO)
async def get_grappling(
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Grappling 탭 데이터: 테이크다운, 서브미션 기술, 컨트롤 타임, 그라운드 스트라이크, 서브미션 효율
    """
    try:
        return await dashboard_service.get_grappling(db, weight_class_id, min_fights, limit)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
