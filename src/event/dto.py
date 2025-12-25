from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from event.models import EventSchema


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
