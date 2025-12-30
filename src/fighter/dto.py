from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from fighter.models import FighterSchema


class FighterWithRankingsDTO(BaseModel):
    """Fighter 기본 정보 + 랭킹 정보 (가장 기본적인 조합)"""
    fighter: FighterSchema
    rankings: Dict[str, int] = Field(
        example={"Lightweight": 5, "Welterweight": 12}
    )


class RankedFighterDTO(BaseModel):
    """랭킹이 있는 파이터 정보"""
    ranking: int = Field(description="현재 랭킹 순위")
    fighter: FighterSchema = Field(description="파이터 기본 정보")


class WeightClassRankingsDTO(BaseModel):
    """특정 체급의 랭킹 리스트"""
    weight_class_name: Optional[str] = None
    rankings: List[RankedFighterDTO] = Field(
        example=[
            {"ranking": 1, "fighter": {"name": "Islam Makhachev"}},
            {"ranking": 2, "fighter": {"name": "Charles Oliveira"}}
        ]
    )
