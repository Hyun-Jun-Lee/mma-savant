from typing import Dict, List, Optional
from datetime import date
from pydantic import BaseModel, Field

from match.models import MatchSchema


class FighterBasicInfoDTO(BaseModel):
    """매치에서 사용되는 파이터 기본 정보"""
    id: int = Field(description="파이터 ID")
    name: str = Field(description="파이터 이름")


class MatchWithFightersDTO(BaseModel):
    """매치 정보와 참가 파이터들"""
    match: MatchSchema = Field(description="매치 기본 정보")
    winner_fighter: Optional[FighterBasicInfoDTO] = Field(description="승자 파이터 정보")
    loser_fighter: Optional[FighterBasicInfoDTO] = Field(description="패자 파이터 정보")
    draw_fighters: Optional[List[FighterBasicInfoDTO]] = Field(default=None, description="무승부인 경우 파이터들")


class EventMatchesDTO(BaseModel):
    """이벤트의 모든 매치 정보"""
    event_name: str = Field(description="이벤트명")
    event_date: date = Field(description="이벤트 날짜")
    matches: List[MatchWithFightersDTO] = Field(description="매치 목록", example=[
        {
            "match": {"id": 1, "method": "KO", "result_round": 1},
            "winner_fighter": {"id": 1, "name": "Jon Jones"},
            "loser_fighter": {"id": 2, "name": "Daniel Cormier"}
        }
    ])