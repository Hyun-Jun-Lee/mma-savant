from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from event.models import EventSchema
from match.models import BasicMatchStatSchema, SigStrMatchStatSchema


class EventListDTO(BaseModel):
    """이벤트 목록 (페이지네이션 포함)"""
    events: List[EventSchema] = Field(description="이벤트 목록")
    total: int = Field(description="전체 이벤트 수")
    page: int = Field(description="현재 페이지", ge=1)
    limit: int = Field(description="페이지당 이벤트 수", ge=1)
    year: Optional[int] = Field(default=None, description="필터링된 연도")
    month: Optional[int] = Field(default=None, description="필터링된 월")


class EventSearchResultDTO(BaseModel):
    """이벤트 검색 결과 항목"""
    event: EventSchema = Field(description="이벤트 정보")
    match_type: str = Field(description="매칭 타입", example="name")
    relevance: float = Field(description="관련성 점수", ge=0.0, le=1.0)


class EventSearchDTO(BaseModel):
    """이벤트 검색 결과"""
    results: List[EventSearchResultDTO] = Field(description="검색 결과 목록")
    total: int = Field(description="총 검색 결과 수")
    query: str = Field(description="검색 쿼리")
    search_type: str = Field(description="검색 타입")


class MonthlyCalendarDTO(BaseModel):
    """월별 캘린더 정보"""
    type: str = Field(description="캘린더 타입", example="monthly")
    year: int = Field(description="연도")
    month: int = Field(description="월")
    total_events: int = Field(description="총 이벤트 수")
    calendar: Dict[str, List[EventSchema]] = Field(description="일별 이벤트 정보")


class MonthlyBreakdownDTO(BaseModel):
    """월별 이벤트 요약"""
    count: int = Field(description="이벤트 수")
    events: List[EventSchema] = Field(description="이벤트 목록")


class YearlyCalendarDTO(BaseModel):
    """연간 캘린더 정보"""
    type: str = Field(description="캘린더 타입", example="yearly")
    year: int = Field(description="연도")
    total_events: int = Field(description="총 이벤트 수")
    monthly_breakdown: Dict[str, MonthlyBreakdownDTO] = Field(description="월별 이벤트 요약")


class EventFighterStatDTO(BaseModel):
    """이벤트 매치 내 파이터 정보 및 스탯"""
    fighter_id: int = Field(description="파이터 ID")
    name: str = Field(description="파이터 이름")
    nickname: Optional[str] = Field(default=None, description="파이터 별명")
    nationality: Optional[str] = Field(default=None, description="국적")
    height_cm: Optional[float] = Field(default=None, description="키 (cm)")
    weight_kg: Optional[float] = Field(default=None, description="체중 (kg)")
    reach_cm: Optional[float] = Field(default=None, description="리치 (cm)")
    stance: Optional[str] = Field(default=None, description="스탠스 (Orthodox/Southpaw/Switch)")
    result: Optional[str] = Field(default=None, description="경기 결과 (Win/Loss/Draw/NC)")
    ranking: Optional[int] = Field(default=None, description="해당 체급 랭킹")
    stats: Optional[BasicMatchStatSchema] = Field(default=None, description="기본 경기 통계")
    round_stats: Optional[List[BasicMatchStatSchema]] = Field(default=None, description="라운드별 경기 통계")
    strike_stats: Optional[SigStrMatchStatSchema] = Field(default=None, description="부위별 유효 타격 통계")


class EventMatchDTO(BaseModel):
    """이벤트 내 개별 매치"""
    match_id: int = Field(description="매치 ID")
    weight_class: Optional[str] = Field(default=None, description="체급명")
    method: Optional[str] = Field(default=None, description="경기 종료 방법")
    result_round: Optional[int] = Field(default=0, description="종료 라운드")
    time: Optional[str] = Field(default=None, description="종료 시간")
    order: Optional[int] = Field(default=0, description="카드 순서")
    is_main_event: bool = Field(default=False, description="메인 이벤트 여부")
    fighters: List[EventFighterStatDTO] = Field(default_factory=list, description="참가 파이터 목록")


class EventSummaryDTO(BaseModel):
    """이벤트 요약 통계"""
    total_bouts: int = Field(default=0, description="총 경기 수")
    ko_tko_count: int = Field(default=0, description="KO/TKO 종료 수")
    submission_count: int = Field(default=0, description="서브미션 종료 수")
    decision_count: int = Field(default=0, description="판정 종료 수")
    other_count: int = Field(default=0, description="기타 종료 수 (DQ, NC 등)")
    avg_fight_duration_seconds: float = Field(default=0.0, description="평균 경기 시간 (초)")


class EventDetailDTO(BaseModel):
    """이벤트 상세 정보"""
    event: EventSchema = Field(description="이벤트 기본 정보")
    matches: List[EventMatchDTO] = Field(default_factory=list, description="매치 목록")
    summary: EventSummaryDTO = Field(default_factory=EventSummaryDTO, description="이벤트 요약 통계")
