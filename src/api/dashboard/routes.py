"""
Dashboard API 라우터
탭별 aggregate 엔드포인트 + 차트별 개별 엔드포인트 제공
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection.postgres_conn import get_async_db
from dashboard import services as dashboard_service
from dashboard.dto import (
    HomeResponseDTO,
    OverviewResponseDTO,
    StrikingResponseDTO,
    GrapplingResponseDTO,
    FinishMethodDTO,
    FightDurationDTO,
    LeaderboardDTO,
    StrikeTargetDTO,
    StrikingAccuracyLeaderboardDTO,
    KoTkoLeaderDTO,
    SigStrikesLeaderboardDTO,
    TakedownLeaderboardDTO,
    SubmissionTechniqueDTO,
    GroundStrikesDTO,
    SubmissionEfficiencyDTO,
)
from dashboard.exceptions import DashboardQueryError


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ===========================
# Tab-level endpoints
# ===========================

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
    ufc_only: bool = True,
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


# ===========================
# Chart-level endpoints
# ===========================

@router.get("/chart/finish-methods", response_model=List[FinishMethodDTO])
async def get_chart_finish_methods(
    weight_class_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """피니시 방법 분포 (Overview)"""
    try:
        return await dashboard_service.get_chart_finish_methods(db, weight_class_id)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/fight-duration", response_model=FightDurationDTO)
async def get_chart_fight_duration(
    weight_class_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """경기 종료 라운드 분포 및 평균 (Overview)"""
    try:
        return await dashboard_service.get_chart_fight_duration(db, weight_class_id)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/leaderboard", response_model=LeaderboardDTO)
async def get_chart_leaderboard(
    weight_class_id: Optional[int] = None,
    ufc_only: bool = True,
    db: AsyncSession = Depends(get_async_db),
):
    """리더보드: 다승, 승률 (Overview)"""
    try:
        return await dashboard_service.get_chart_leaderboard(db, weight_class_id, ufc_only)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/strike-targets", response_model=List[StrikeTargetDTO])
async def get_chart_strike_targets(
    weight_class_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """타격 부위별 유효타 수 (Striking)"""
    try:
        return await dashboard_service.get_chart_strike_targets(db, weight_class_id)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/striking-accuracy", response_model=StrikingAccuracyLeaderboardDTO)
async def get_chart_striking_accuracy(
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
):
    """타격 정확도 리더보드 (Striking)"""
    try:
        return await dashboard_service.get_chart_striking_accuracy(db, weight_class_id, min_fights, limit)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/ko-tko-leaders", response_model=List[KoTkoLeaderDTO])
async def get_chart_ko_tko_leaders(
    weight_class_id: Optional[int] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
):
    """KO/TKO 리더 (Striking)"""
    try:
        return await dashboard_service.get_chart_ko_tko_leaders(db, weight_class_id, limit)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/sig-strikes", response_model=SigStrikesLeaderboardDTO)
async def get_chart_sig_strikes(
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
):
    """경기당 유효타격 리더보드 (Striking)"""
    try:
        return await dashboard_service.get_chart_sig_strikes(db, weight_class_id, min_fights, limit)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/takedown-accuracy", response_model=TakedownLeaderboardDTO)
async def get_chart_takedown_accuracy(
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
):
    """테이크다운 정확도 리더보드 (Grappling)"""
    try:
        return await dashboard_service.get_chart_takedown_accuracy(db, weight_class_id, min_fights, limit)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/submission-techniques", response_model=List[SubmissionTechniqueDTO])
async def get_chart_submission_techniques(
    weight_class_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """서브미션 기술 분포 (Grappling)"""
    try:
        return await dashboard_service.get_chart_submission_techniques(db, weight_class_id)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/ground-strikes", response_model=List[GroundStrikesDTO])
async def get_chart_ground_strikes(
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
):
    """그라운드 스트라이크 리더보드 (Grappling)"""
    try:
        return await dashboard_service.get_chart_ground_strikes(db, weight_class_id, min_fights, limit)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )


@router.get("/chart/submission-efficiency", response_model=SubmissionEfficiencyDTO)
async def get_chart_submission_efficiency(
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
):
    """서브미션 효율 (Grappling)"""
    try:
        return await dashboard_service.get_chart_submission_efficiency(db, weight_class_id, min_fights, limit)
    except DashboardQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
