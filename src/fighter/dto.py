from typing import Dict, List, Optional, Any
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


class StanceAnalysisDTO(BaseModel):
    """스탠스별 파이터 분석 정보"""
    average_wins: float = Field(description="평균 승수")
    total_wins: int = Field(description="총 승수")
    total_losses: int = Field(description="총 패수")
    total_fights: int = Field(description="총 경기 수")
    champions_count: int = Field(description="챔피언 수")
    win_percentage: float = Field(description="승률 (%)")


class FightersByStanceDTO(BaseModel):
    """특정 스탠스 파이터들의 분석 결과"""
    stance: str = Field(description="스탠스 종류")
    total_fighters: int = Field(description="해당 스탠스 총 파이터 수")
    fighters: List[FighterSchema] = Field(description="파이터 목록 (상위 10명)")
    analysis: StanceAnalysisDTO = Field(description="분석 정보")


class UndefeatedAnalysisDTO(BaseModel):
    """무패 파이터 분석 정보"""
    average_wins: float = Field(description="평균 승수")
    total_wins: int = Field(description="총 승수")
    champions_count: int = Field(description="챔피언 수")
    most_wins: int = Field(description="최다 승수")


class UndefeatedFightersDTO(BaseModel):
    """무패 파이터들의 분석 결과"""
    total_undefeated: int = Field(description="총 무패 파이터 수")
    min_wins_threshold: int = Field(description="최소 승수 조건")
    fighters: List[FighterWithRankingsDTO] = Field(description="무패 파이터 목록")
    analysis: UndefeatedAnalysisDTO = Field(description="분석 정보")


class PhysicalCriteriaDTO(BaseModel):
    """신체 조건 검색 기준"""
    min_height: Optional[float] = Field(default=None, description="최소 키")
    max_height: Optional[float] = Field(default=None, description="최대 키")
    min_weight: Optional[float] = Field(default=None, description="최소 체중")
    max_weight: Optional[float] = Field(default=None, description="최대 체중")
    min_reach: Optional[float] = Field(default=None, description="최소 리치")


class PhysicalRangeDTO(BaseModel):
    """신체 수치 범위"""
    min: float = Field(description="최솟값")
    max: float = Field(description="최댓값")


class PhysicalAnalysisDTO(BaseModel):
    """신체 통계 분석 정보"""
    avg_height: float = Field(description="평균 키")
    avg_weight: float = Field(description="평균 체중")
    avg_reach: float = Field(description="평균 리치")
    height_range: PhysicalRangeDTO = Field(description="키 범위")
    weight_range: PhysicalRangeDTO = Field(description="체중 범위")


class FightersByPhysicalAttributesDTO(BaseModel):
    """신체 조건별 파이터 검색 결과"""
    criteria: PhysicalCriteriaDTO = Field(description="검색 조건")
    total_fighters: int = Field(description="조건에 맞는 총 파이터 수")
    fighters: List[FighterSchema] = Field(description="파이터 목록")
    physical_analysis: PhysicalAnalysisDTO = Field(description="신체 통계 분석")


class OverallStatisticsDTO(BaseModel):
    """전체 파이터 통계 정보"""
    total_fighters: int = Field(description="총 파이터 수")
    avg_wins: float = Field(description="평균 승수")
    avg_losses: float = Field(description="평균 패수")
    champions: int = Field(description="챔피언 수")


class PerformanceInsightsDTO(BaseModel):
    """성과 분석 인사이트"""
    average_career_length: float = Field(description="평균 경력 길이")
    competitive_ratio: float = Field(description="경쟁 비율")
    champion_percentage: float = Field(description="챔피언 비율 (%)")


class FightersPerformanceAnalysisDTO(BaseModel):
    """파이터 성과 분석 결과"""
    overall_statistics: OverallStatisticsDTO = Field(description="전체 통계")
    win_percentage_leaders: List[FighterSchema] = Field(description="승률 상위 파이터들")
    performance_insights: PerformanceInsightsDTO = Field(description="성과 인사이트")


class RankedFighterWithStatsDTO(BaseModel):
    """랭킹과 통계를 포함한 파이터 정보"""
    ranking: int = Field(description="랭킹")
    fighter: FighterSchema = Field(description="파이터 정보")


class DepthAnalysisDTO(BaseModel):
    """체급 깊이 분석 정보"""
    average_wins_in_rankings: float = Field(description="랭킹권 평균 승수")
    top_5_average_wins: float = Field(description="상위 5명 평균 승수")
    ranking_competition: str = Field(description="랭킹 경쟁도", example="high")
    champion_dominance: int = Field(description="챔피언 지배력 (승수)")


class WeightClassDepthAnalysisDTO(BaseModel):
    """체급 깊이 분석 결과"""
    weight_class: str = Field(description="체급명")
    total_ranked_fighters: int = Field(description="랭킹권 파이터 수")
    total_fighters_in_division: int = Field(description="체급 내 총 파이터 수")
    champion: Optional[FighterSchema] = Field(description="챔피언 정보")
    ranked_fighters: List[RankedFighterWithStatsDTO] = Field(description="랭킹권 파이터 목록")
    depth_analysis: DepthAnalysisDTO = Field(description="깊이 분석 정보")
