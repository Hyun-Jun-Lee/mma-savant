from typing import Dict, List, Optional, Any
from datetime import date
from pydantic import BaseModel, Field

from event.models import EventSchema
from match.models import MatchSchema
from fighter.models import FighterSchema


class MatchFighterResultDTO(BaseModel):
    """매치 파이터 결과 정보"""
    fighter: FighterSchema = Field(description="파이터 정보")
    result: Optional[str] = Field(description="경기 결과", example="Win")


class MatchDetailDTO(BaseModel):
    """매치 상세 정보 (파이터와 결과 포함)"""
    match_info: MatchSchema = Field(description="매치 기본 정보")
    fighters: List[MatchFighterResultDTO] = Field(description="참가 파이터들")
    winner: Optional[MatchFighterResultDTO] = Field(description="승자 정보")
    loser: Optional[MatchFighterResultDTO] = Field(description="패자 정보")


class EventSummaryStatsDTO(BaseModel):
    """이벤트 매치 요약 통계"""
    total_matches: int = Field(description="총 매치 수")
    main_events_count: int = Field(description="메인 이벤트 수")
    finish_methods: Dict[str, int] = Field(description="결승 방식별 통계")


class EventWithAllMatchesDTO(BaseModel):
    """이벤트와 모든 매치 정보"""
    event: EventSchema = Field(description="이벤트 기본 정보")
    matches: List[MatchDetailDTO] = Field(description="모든 매치 상세 정보")
    summary: EventSummaryStatsDTO = Field(description="이벤트 통계 요약")


class EventWithMainMatchDTO(BaseModel):
    """이벤트와 메인 매치 정보"""
    event: EventSchema = Field(description="이벤트 기본 정보")
    main_match: Optional[MatchDetailDTO] = Field(description="메인 매치 상세 정보")


class FeaturedMatchDTO(BaseModel):
    """주요 매치 정보"""
    match_info: MatchSchema = Field(description="매치 기본 정보")
    fighters: List[MatchFighterResultDTO] = Field(description="참가 파이터들")


class UpcomingEventWithFeaturedMatchesDTO(BaseModel):
    """다가오는 이벤트와 주요 매치들"""
    event: EventSchema = Field(description="이벤트 기본 정보")
    main_event: Optional[FeaturedMatchDTO] = Field(description="메인 이벤트 매치")
    featured_matches: List[FeaturedMatchDTO] = Field(description="주요 매치들", max_items=3)


class EventComparisonStatsDTO(BaseModel):
    """이벤트 비교 통계"""
    more_matches: str = Field(description="더 많은 매치를 가진 이벤트", example="event1")
    more_main_events: str = Field(description="더 많은 메인 이벤트를 가진 이벤트", example="event2")
    match_difference: int = Field(description="매치 수 차이", ge=0)


class EventComparisonItemDTO(BaseModel):
    """이벤트 비교 항목"""
    event_info: EventSchema = Field(description="이벤트 정보")
    stats: EventSummaryStatsDTO = Field(description="이벤트 통계")


class EventComparisonDTO(BaseModel):
    """두 이벤트 비교 결과"""
    event1: EventComparisonItemDTO = Field(description="첫 번째 이벤트")
    event2: EventComparisonItemDTO = Field(description="두 번째 이벤트")
    comparison: EventComparisonStatsDTO = Field(description="비교 결과")


class RankingInfoDTO(BaseModel):
    """랭킹 정보"""
    ranking: int = Field(description="랭킹 순위")
    weight_class_id: int = Field(description="체급 ID")


class PotentialImpactDTO(BaseModel):
    """랭킹 영향 가능성"""
    winner_moving_up: bool = Field(description="승자의 랭킹 상승 가능성")
    loser_moving_down: bool = Field(description="패자의 랭킹 하락 가능성")
    title_implications: bool = Field(description="타이틀 관련 영향")


class RankingImpactFighterDTO(BaseModel):
    """랭킹 영향 파이터 정보"""
    fighter: FighterSchema = Field(description="파이터 정보")
    rankings: List[RankingInfoDTO] = Field(description="현재 랭킹 정보")


class MatchRankingImpactDTO(BaseModel):
    """매치별 랭킹 영향"""
    match: MatchSchema = Field(description="매치 정보")
    winner: RankingImpactFighterDTO = Field(description="승자 정보")
    loser: RankingImpactFighterDTO = Field(description="패자 정보")
    potential_impact: PotentialImpactDTO = Field(description="예상 영향")


class RankingImpactSummaryDTO(BaseModel):
    """랭킹 영향 요약"""
    matches_with_ranked_fighters: int = Field(description="랭킹 파이터가 참여한 매치 수")
    title_implication_matches: int = Field(description="타이틀 관련 매치 수")


class EventRankingImpactDTO(BaseModel):
    """이벤트의 랭킹 영향 분석"""
    event_id: int = Field(description="이벤트 ID")
    ranking_impacts: List[MatchRankingImpactDTO] = Field(description="매치별 랭킹 영향")
    summary: RankingImpactSummaryDTO = Field(description="영향 요약")


class StatTopPerformerDTO(BaseModel):
    """스탯 최고 성과자"""
    fighter: FighterSchema = Field(description="파이터 정보")
    stat: float = Field(description="통계 값")


class CommonOpponentResultDTO(BaseModel):
    """공통 상대 결과"""
    opponent: FighterSchema = Field(description="공통 상대 파이터")
    fighter1_result: Optional[str] = Field(description="첫 번째 파이터의 결과")
    fighter2_result: Optional[str] = Field(description="두 번째 파이터의 결과")


class PerformanceTrendMatchDTO(BaseModel):
    """성과 트렌드 매치 정보"""
    match: MatchSchema = Field(description="매치 정보")
    result: str = Field(description="경기 결과")


class FighterPerformanceTrendDTO(BaseModel):
    """파이터 성과 트렌드"""
    fighter_id: int = Field(description="파이터 ID")
    last_n_fights: int = Field(description="분석 대상 경기 수")
    trend: str = Field(description="트렌드", example="hot_streak")
    wins: int = Field(description="승수")
    losses: int = Field(description="패수")
    draws: int = Field(description="무승부 수")
    win_percentage: float = Field(description="승률")
    recent_matches: List[PerformanceTrendMatchDTO] = Field(description="최근 경기들")


class LocationAnalysisDTO(BaseModel):
    """장소별 분석"""
    location: str = Field(description="장소명")
    event_count: int = Field(description="이벤트 수")
    total_matches: int = Field(description="총 매치 수")
    avg_matches_per_event: float = Field(description="이벤트당 평균 매치 수")


class EventAttendanceAnalysisDTO(BaseModel):
    """이벤트 참석률 분석"""
    location_analysis: List[LocationAnalysisDTO] = Field(description="장소별 분석")


class WeightClassAnalysisDTO(BaseModel):
    """체급별 분석"""
    weight_class_id: int = Field(description="체급 ID")
    weight_class_name: Optional[str] = Field(description="체급명")
    match_count: int = Field(description="매치 수")
    unique_fighters: int = Field(description="고유 파이터 수")
    avg_fights_per_fighter: float = Field(description="파이터당 평균 경기 수")


class WeightClassActivityAnalysisDTO(BaseModel):
    """체급별 활동 분석"""
    year: str = Field(description="분석 연도")
    weight_class_analysis: List[WeightClassAnalysisDTO] = Field(description="체급별 분석 결과")


class FinishMethodStatsDTO(BaseModel):
    """결승 방식 통계"""
    method: str = Field(description="결승 방식")
    count: int = Field(description="횟수")
    percentage: float = Field(description="비율")


class FinishRateAnalysisDTO(BaseModel):
    """결승률 분석"""
    event_id: Optional[int] = Field(description="이벤트 ID")
    total_matches: int = Field(description="총 매치 수")
    finish_methods: List[FinishMethodStatsDTO] = Field(description="결승 방식별 통계")


class EventTopPerformerDTO(BaseModel):
    """이벤트 최고 성과자"""
    fighter: FighterSchema = Field(description="파이터 정보")
    stat_name: str = Field(description="통계 항목명")
    stat_value: float = Field(description="통계 값")


# Match Composer DTOs

class FOTNAnalysisDTO(BaseModel):
    """Fight of the Night 분석 정보"""
    duration_rounds: int = Field(description="지속 라운드 수")
    finish_method: Optional[str] = Field(description="결승 방식")
    entertainment_value: str = Field(description="엔터테인먼트 가치", example="high")


class FOTNCandidateDTO(BaseModel):
    """Fight of the Night 후보"""
    match: MatchSchema = Field(description="매치 정보")
    fighters: List[MatchFighterResultDTO] = Field(description="참가 파이터들")
    winner: Optional[MatchFighterResultDTO] = Field(description="승자 정보")
    loser: Optional[MatchFighterResultDTO] = Field(description="패자 정보")
    fotn_score: float = Field(description="FOTN 점수")
    analysis: FOTNAnalysisDTO = Field(description="분석 정보")


class FOTNCandidatesDTO(BaseModel):
    """Fight of the Night 후보들"""
    event: EventSchema = Field(description="이벤트 정보")
    fotn_candidates: List[FOTNCandidateDTO] = Field(description="FOTN 후보들", max_items=5)
    analysis_criteria: str = Field(description="분석 기준")


class QualityIndicatorsDTO(BaseModel):
    """카드 품질 지표"""
    overall_grade: str = Field(description="전체 등급", example="Premium")
    quality_score: int = Field(description="품질 점수")
    max_score: int = Field(description="최대 점수", default=10)


class CardAnalysisDTO(BaseModel):
    """카드 분석 정보"""
    total_matches: int = Field(description="총 매치 수")
    main_events: int = Field(description="메인 이벤트 수")
    ranked_fighters: int = Field(description="랭킹 파이터 수")
    champions: int = Field(description="챔피언 수")
    weight_classes: List[int] = Field(description="체급 ID 목록")
    finish_methods: Dict[str, int] = Field(description="결승 방식별 횟수")
    unique_fighters: int = Field(description="고유 파이터 수")
    ranked_fighter_percentage: float = Field(description="랭킹 파이터 비율")
    finish_rate: float = Field(description="피니시율")


class CardQualityAnalysisDTO(BaseModel):
    """카드 품질 분석"""
    event: EventSchema = Field(description="이벤트 정보")
    card_analysis: CardAnalysisDTO = Field(description="카드 분석")
    quality_assessment: QualityIndicatorsDTO = Field(description="품질 평가")


class ExcitingMatchHighlightsDTO(BaseModel):
    """흥미진진한 매치 하이라이트"""
    finish_method: Optional[str] = Field(description="결승 방식")
    ranked_fighters: int = Field(description="랭킹 파이터 수")
    champions_involved: int = Field(description="참여 챔피언 수")
    main_event: bool = Field(description="메인 이벤트 여부")


class ExcitingMatchDTO(BaseModel):
    """흥미진진한 매치"""
    event: EventSchema = Field(description="이벤트 정보")
    match: MatchSchema = Field(description="매치 정보")
    fighters: List[MatchFighterResultDTO] = Field(description="참가 파이터들")
    winner: Optional[MatchFighterResultDTO] = Field(description="승자 정보")
    excitement_score: float = Field(description="흥미도 점수")
    highlights: ExcitingMatchHighlightsDTO = Field(description="하이라이트")


class ComebackAnalysisDTO(BaseModel):
    """컴백 분석 정보"""
    finish_round: int = Field(description="결승 라운드")
    finish_method: Optional[str] = Field(description="결승 방식")
    winner_recent_form: str = Field(description="승자 최근 폼")
    loser_recent_form: str = Field(description="패자 최근 폼")
    upset_factor: float = Field(description="업셋 요인")


class ComebackPerformanceDTO(BaseModel):
    """컴백 성과"""
    match: MatchSchema = Field(description="매치 정보")
    winner: MatchFighterResultDTO = Field(description="승자 정보")
    loser: MatchFighterResultDTO = Field(description="패자 정보")
    comeback_type: List[str] = Field(description="컴백 유형")
    analysis: ComebackAnalysisDTO = Field(description="분석 정보")


class ComebackPerformancesDTO(BaseModel):
    """컴백 성과 분석"""
    event_id: int = Field(description="이벤트 ID")
    comeback_performances: List[ComebackPerformanceDTO] = Field(description="컴백 성과들")
    total_comebacks: int = Field(description="총 컴백 수")


class StyleContrastDTO(BaseModel):
    """스타일 대조"""
    aspect: str = Field(description="대조 측면", example="stance")
    fighter1: Optional[str] = Field(default=None, description="파이터1 특성")
    fighter2: Optional[str] = Field(default=None, description="파이터2 특성")
    analysis: str = Field(description="분석 내용")
    advantage: Optional[str] = Field(default=None, description="우위 파이터")
    difference: Optional[float] = Field(default=None, description="차이값")


class StyleClashAnalysisDTO(BaseModel):
    """스타일 충돌 분석"""
    match: MatchSchema = Field(description="매치 정보")
    fighters: List[FighterSchema] = Field(description="파이터들", max_items=2)
    style_contrasts: List[StyleContrastDTO] = Field(description="스타일 대조들")
    match_result: Dict[str, Any] = Field(description="매치 결과")
    outcome_analysis: str = Field(description="결과 분석")
    contrast_summary: str = Field(description="대조 요약")


class OutlierPerformanceDTO(BaseModel):
    """예외적 성과"""
    stat_name: str = Field(description="통계 항목명")
    value: float = Field(description="통계 값")
    threshold: float = Field(description="기준값")


class PerformanceOutlierDTO(BaseModel):
    """성과 예외자"""
    fighter: FighterSchema = Field(description="파이터 정보")
    category: str = Field(description="카테고리", example="striking")
    performance: OutlierPerformanceDTO = Field(description="성과 정보")
    outlier_rating: str = Field(description="예외 등급", example="exceptional")


class OutlierAnalysisSummaryDTO(BaseModel):
    """예외 분석 요약"""
    total_outliers: int = Field(description="총 예외자 수")
    exceptional_performances: int = Field(description="예외적 성과 수")
    categories_analyzed: List[str] = Field(description="분석된 카테고리들")


class PerformanceOutliersDTO(BaseModel):
    """성과 예외자들"""
    event_id: int = Field(description="이벤트 ID")
    outlier_performances: List[PerformanceOutlierDTO] = Field(description="예외적 성과들")
    analysis_summary: OutlierAnalysisSummaryDTO = Field(description="분석 요약")


# Fighter Composer DTOs

class FighterMatchRecordDTO(BaseModel):
    """파이터 매치 기록"""
    event: Optional[EventSchema] = Field(description="이벤트 정보")
    opponent: Optional[Dict[str, Any]] = Field(description="상대방 정보")
    match: MatchSchema = Field(description="매치 정보")
    result: str = Field(description="경기 결과")
    weight_class: Optional[str] = Field(description="체급명")


class MatchInfoDTO(BaseModel):
    """매치 기본 정보"""
    event_name: Optional[str] = Field(description="이벤트명")
    event_date: Optional[date] = Field(description="이벤트 날짜")
    is_main_event: bool = Field(description="메인 이벤트 여부")
    order: Optional[int] = Field(description="매치 순서")
    match_id: int = Field(description="매치 ID")
    method: Optional[str] = Field(description="결승 방식")
    result_round: Optional[int] = Field(description="결승 라운드")
    time: Optional[str] = Field(description="경기 시간")
    weight_class: Optional[str] = Field(description="체급")


class FighterVsRecordItemDTO(BaseModel):
    """파이터 대전 기록 항목"""
    info: FighterSchema = Field(description="파이터 정보")
    result: Optional[str] = Field(description="경기 결과")
    basic_stats: Optional[Dict[str, Any]] = Field(description="기본 통계")
    sig_str_stats: Optional[Dict[str, Any]] = Field(description="유효타 통계")


class FighterVsRecordDTO(BaseModel):
    """파이터 대전 기록"""
    match_info: MatchInfoDTO = Field(description="매치 정보")
    fighter1: FighterVsRecordItemDTO = Field(description="첫 번째 파이터")
    fighter2: FighterVsRecordItemDTO = Field(description="두 번째 파이터")


class FighterTotalStatsDTO(BaseModel):
    """파이터 종합 통계"""
    fighter: FighterSchema = Field(description="파이터 정보")
    basic_stats: Dict[str, Any] = Field(description="기본 통계")
    sig_str_stats: Dict[str, Any] = Field(description="유효타 통계")
    accuracy: Dict[str, Any] = Field(description="정확도 통계")


class StatComparisonDTO(BaseModel):
    """통계 비교"""
    fighter1_value: float = Field(description="파이터1 값")
    fighter2_value: float = Field(description="파이터2 값")
    winner: str = Field(description="우위 파이터", example="fighter1")


class AccuracyComparisonDTO(BaseModel):
    """정확도 비교"""
    fighter1_accuracy: float = Field(description="파이터1 정확도")
    fighter2_accuracy: float = Field(description="파이터2 정확도")
    winner: str = Field(description="우위 파이터", example="fighter1")


class FighterComparisonStatsDTO(BaseModel):
    """파이터 비교 통계"""
    stats: Dict[str, StatComparisonDTO] = Field(description="통계 비교")
    accuracy: Dict[str, AccuracyComparisonDTO] = Field(description="정확도 비교")


class FighterComparisonItemDTO(BaseModel):
    """파이터 비교 항목"""
    info: FighterSchema = Field(description="파이터 정보")
    basic_stats: Dict[str, Any] = Field(description="기본 통계")
    sig_str_stats: Dict[str, Any] = Field(description="유효타 통계")
    accuracy: Dict[str, Any] = Field(description="정확도")


class FighterStatsComparisonDTO(BaseModel):
    """파이터 통계 비교"""
    fighter1: FighterComparisonItemDTO = Field(description="첫 번째 파이터")
    fighter2: FighterComparisonItemDTO = Field(description="두 번째 파이터")
    comparison: FighterComparisonStatsDTO = Field(description="비교 결과")


class TopStatFighterDTO(BaseModel):
    """상위 통계 파이터"""
    rank: int = Field(description="순위")
    fighter_name: str = Field(description="파이터명")
    fighter_id: int = Field(description="파이터 ID")
    stat_name: str = Field(description="통계 항목명")
    total_stat: float = Field(description="총 통계값")


class CareerHighlightDTO(BaseModel):
    """커리어 하이라이트"""
    type: str = Field(description="하이라이트 타입", example="main_event")
    match_index: int = Field(description="매치 인덱스")
    description: str = Field(description="설명")


class CareerSummaryDTO(BaseModel):
    """커리어 요약"""
    total_fights: int = Field(description="총 경기 수")
    wins: int = Field(description="승수")
    losses: int = Field(description="패수")
    draws: int = Field(description="무승부 수")
    max_win_streak: int = Field(description="최대 연승")
    main_events: int = Field(description="메인 이벤트 수")
    career_highlights: List[CareerHighlightDTO] = Field(description="커리어 하이라이트")


class FighterCareerTimelineDTO(BaseModel):
    """파이터 커리어 타임라인"""
    fighter_id: int = Field(description="파이터 ID")
    career_timeline: List[FighterMatchRecordDTO] = Field(description="커리어 타임라인")
    summary: CareerSummaryDTO = Field(description="커리어 요약")


class StanceAnalysisDetailDTO(BaseModel):
    """스탠스 분석 상세"""
    opponent: FighterSchema = Field(description="상대방 파이터")
    result: str = Field(description="경기 결과")
    match_details: MatchInfoDTO = Field(description="매치 상세")


class StanceAnalysisStatsDTO(BaseModel):
    """스탠스 분석 통계"""
    total_fights_vs_stance: int = Field(description="해당 스탠스와의 총 경기 수")
    wins: int = Field(description="승수")
    losses: int = Field(description="패수")
    win_percentage: float = Field(description="승률")
    detailed_results: List[StanceAnalysisDetailDTO] = Field(description="상세 결과")


class FighterVsStanceAnalysisDTO(BaseModel):
    """파이터 대 스탠스 분석"""
    fighter: FighterSchema = Field(description="파이터 정보")
    opponent_stance: str = Field(description="상대방 스탠스")
    analysis: StanceAnalysisStatsDTO = Field(description="분석 결과")


class StatLeaderDTO(BaseModel):
    """통계 리더"""
    fighter: FighterSchema = Field(description="파이터 정보")
    value: float = Field(description="통계값")


class EliteFighterComparisonDTO(BaseModel):
    """엘리트 파이터 비교"""
    fighter: FighterSchema = Field(description="파이터 정보")
    stats: FighterTotalStatsDTO = Field(description="파이터 통계")
    ranking: int = Field(description="랭킹")


class DivisionalEliteComparisonDTO(BaseModel):
    """체급 엘리트 비교"""
    weight_class: str = Field(description="체급명")
    weight_class_id: int = Field(description="체급 ID")
    elite_fighters: List[EliteFighterComparisonDTO] = Field(description="엘리트 파이터들")
    stat_leaders: Dict[str, StatLeaderDTO] = Field(description="통계 리더들")
    division_depth: int = Field(description="체급 선수층 깊이")


class MatchupInfoDTO(BaseModel):
    """매치업 정보"""
    fighter1: FighterSchema = Field(description="첫 번째 파이터")
    fighter2: FighterSchema = Field(description="두 번째 파이터")


class FightPredictionDTO(BaseModel):
    """경기 예측"""
    fighter1_win_probability: float = Field(description="파이터1 승리 확률")
    fighter2_win_probability: float = Field(description="파이터2 승리 확률")
    predicted_winner: FighterSchema = Field(description="예측 승자")
    confidence: str = Field(description="예측 신뢰도", example="high")


class ScoringBreakdownDTO(BaseModel):
    """점수 세부사항"""
    fighter1_score: int = Field(description="파이터1 점수")
    fighter2_score: int = Field(description="파이터2 점수")


class AnalysisFactorsDTO(BaseModel):
    """분석 요소들"""
    head_to_head_fights: int = Field(description="과거 대전 횟수")
    common_opponents: int = Field(description="공통 상대 수")
    statistical_comparison: FighterComparisonStatsDTO = Field(description="통계 비교")
    scoring_breakdown: ScoringBreakdownDTO = Field(description="점수 세부사항")


class FightOutcomePredictionDTO(BaseModel):
    """경기 결과 예측"""
    matchup: MatchupInfoDTO = Field(description="매치업 정보")
    prediction: FightPredictionDTO = Field(description="예측 결과")
    analysis_factors: AnalysisFactorsDTO = Field(description="분석 요소들")