from typing import Dict, List, Optional, Any
from datetime import date
from pydantic import BaseModel, Field

from event.models import EventSchema


class EventTimelineDTO(BaseModel):
    """이벤트 타임라인 정보"""
    period: str = Field(description="기간 타입", example="monthly")
    current_period: str = Field(description="현재 기간", example="2024-07")
    previous_events: List[EventSchema] = Field(description="이전 기간 이벤트들")
    current_events: List[EventSchema] = Field(description="현재 기간 이벤트들")
    upcoming_events: List[EventSchema] = Field(description="다음 기간 이벤트들")


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


class LocationStatisticsDTO(BaseModel):
    """장소별 통계 정보"""
    location_breakdown: Dict[str, int] = Field(description="장소별 이벤트 수")
    total_major_locations: int = Field(description="주요 장소 총 이벤트 수")
    total_events_this_year: int = Field(description="올해 총 이벤트 수")
    other_locations: int = Field(description="기타 장소 이벤트 수")


class EventRecommendationsDTO(BaseModel):
    """이벤트 추천 정보"""
    type: str = Field(description="추천 타입", example="upcoming")
    title: str = Field(description="추천 제목")
    events: List[EventSchema] = Field(description="추천 이벤트 목록")
    description: str = Field(description="추천 설명")


class NextAndLastEventsDTO(BaseModel):
    """다음/마지막 이벤트 정보"""
    next_event: Optional[EventSchema] = Field(description="다음 이벤트")
    last_event: Optional[EventSchema] = Field(description="마지막 이벤트")
    days_until_next: Optional[int] = Field(description="다음 이벤트까지 남은 일수")
    days_since_last: Optional[int] = Field(description="마지막 이벤트로부터 경과 일수")


class EventTrendsDTO(BaseModel):
    """이벤트 트렌드 정보"""
    period: str = Field(description="분석 기간", example="yearly")
    trends: Dict[str, int] = Field(description="기간별 이벤트 수")
    total: int = Field(description="총 이벤트 수")
    average: float = Field(description="평균 이벤트 수")