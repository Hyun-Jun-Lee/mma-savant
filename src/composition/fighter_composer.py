from typing import Optional, Dict, List, Any
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from common.models import WeightClassSchema
from event.repositories import get_event_by_id
from common.utils import calculate_fighter_accuracy
from match.models import (
    BasicMatchStatSchema,
    SigStrMatchStatSchema,
    BasicMatchStatModel,
    SigStrMatchStatModel
)
from fighter.repositories import (
    get_fighter_by_id,
    get_top_fighter_by_record
)
from match.repositories import (
    get_fighters_matches,
    get_match_by_id,
    get_fighter_match_by_match_id,
    get_fighter_basic_stats_aggregate, 
    get_fighter_sig_str_stats_aggregate,
)
from composition.dto import (
    FighterMatchRecordDTO, MatchInfoDTO, FighterVsRecordDTO, FighterVsRecordItemDTO,
    FighterTotalStatsDTO, FighterStatsComparisonDTO, FighterComparisonItemDTO,
    FighterComparisonStatsDTO, StatComparisonDTO, AccuracyComparisonDTO,
    TopStatFighterDTO, FighterCareerTimelineDTO, CareerSummaryDTO, CareerHighlightDTO,
    FighterVsStanceAnalysisDTO, StanceAnalysisStatsDTO, StanceAnalysisDetailDTO,
    DivisionalEliteComparisonDTO, EliteFighterComparisonDTO, StatLeaderDTO,
    FightOutcomePredictionDTO, MatchupInfoDTO, FightPredictionDTO, AnalysisFactorsDTO, ScoringBreakdownDTO
)

async def get_fighter_all_matches(session: AsyncSession, fighter_id: int) -> List[FighterMatchRecordDTO]:
    """
    특정 선수의 모든 경기 기록을 조회합니다.
    """
    results = []

    fighter_matches = await get_fighters_matches(session, fighter_id, limit=None)

    for fm in fighter_matches:
        match = await get_match_by_id(session, fm.match_id)
        if not match:
            continue
        weight_class = WeightClassSchema.get_name_by_id(match.weight_class_id)
        event = await get_event_by_id(session, match.event_id)
        participants = await get_fighter_match_by_match_id(session, fm.match_id)
        opponent = next((p for p in participants if p.fighter_id != fighter_id), None)

        results.append(FighterMatchRecordDTO(
            event=event,
            opponent=opponent.__dict__ if opponent else None,
            match=match,
            result=fm.result,
            weight_class=weight_class
        ))

    return results

async def get_fighter_vs_record(
    session: AsyncSession, 
    fighter_id1: int, 
    fighter_id2: int
) -> List[FighterVsRecordDTO]:
    """
    두 파이터간 과거 대전 기록을 조회합니다.
    """
    # 두 파이터 기본 정보 조회
    fighter1 = await get_fighter_by_id(session, fighter_id1)
    fighter2 = await get_fighter_by_id(session, fighter_id2)
    
    if not fighter1 or not fighter2:
        raise ValueError("One or both fighters not found")
    
    # 두 파이터간 경기 기록 조회 (이 함수는 추후 구현 필요)
    # matches = await get_matches_between_fighters(session, fighter_id1, fighter_id2)
    matches = []  # 임시 처리
    
    if not matches:
        return []
    
    results = []
    
    for match in matches:
        # 각 경기에서의 파이터 매치 정보 조회
        fighter_matches = await get_fighter_match_by_match_id(session, match.id)
        
        # 각 파이터의 결과 찾기
        fighter1_match = next((fm for fm in fighter_matches if fm.fighter_id == fighter_id1), None)
        fighter2_match = next((fm for fm in fighter_matches if fm.fighter_id == fighter_id2), None)
        
        # 이벤트 정보 조회 (만약 EventModel이 있다면)
        event = await get_event_by_id(session, match.event_id) if match.event_id else None
        
        # 각 파이터의 경기 통계 조회 (임시 처리)
        fighter1_basic_stats = {}
        fighter1_sig_str_stats = {}
        
        fighter2_basic_stats = {}
        fighter2_sig_str_stats = {}
        
        # 체급 정보 (WeightClassSchema가 있다면)
        weight_class = None
        if hasattr(match, 'weight_class_id') and match.weight_class_id:
            weight_class = WeightClassSchema.get_name_by_id(match.weight_class_id)
        
        match_result = FighterVsRecordDTO(
            match_info=MatchInfoDTO(
                event_name=event.name if event else None,
                event_date=event.event_date if event else None,
                is_main_event=match.is_main_event,
                order=match.order,
                match_id=match.id,
                method=match.method,
                result_round=match.result_round,
                time=match.time,
                weight_class=weight_class
            ),
            fighter1=FighterVsRecordItemDTO(
                info=fighter1,
                result=fighter1_match.result if fighter1_match else None,
                basic_stats=fighter1_basic_stats,
                sig_str_stats=fighter1_sig_str_stats
            ),
            fighter2=FighterVsRecordItemDTO(
                info=fighter2,
                result=fighter2_match.result if fighter2_match else None,
                basic_stats=fighter2_basic_stats,
                sig_str_stats=fighter2_sig_str_stats
            )
        )
        
        results.append(match_result)
    
    # 최신 경기순으로 정렬 (match.id 기준)
    results.sort(key=lambda x: x.match_info.match_id, reverse=True)
    
    return results

async def get_fighter_total_stat(session: AsyncSession, fighter_id: int) -> Optional[FighterTotalStatsDTO]:
    """
    특정 선수의 모든 경기 통계를 데이터베이스 레벨에서 필드별로 합산하여 반환합니다.
    """
    fighter = await get_fighter_by_id(session, fighter_id)
    if not fighter:
        return None
    
    total_basic_stats = await get_fighter_basic_stats_aggregate(session, fighter_id)
    
    total_sig_str_stats = await get_fighter_sig_str_stats_aggregate(session, fighter_id)
    
    accuracy_stats = calculate_fighter_accuracy(total_basic_stats, total_sig_str_stats)
    
    return FighterTotalStatsDTO(
        fighter=fighter,
        basic_stats=total_basic_stats,
        sig_str_stats=total_sig_str_stats,
        accuracy=accuracy_stats
    )

async def compare_fighters_stats(
    session: AsyncSession,
    fighter_id_1: int,
    fighter_id_2: int,
) -> Optional[FighterStatsComparisonDTO]:
    """
    두 선수의 모든 스탯을 비교합니다.
    """
    fighter1 = await get_fighter_by_id(session, fighter_id_1)
    fighter2 = await get_fighter_by_id(session, fighter_id_2)
    
    if not fighter1 or not fighter2:
        raise ValueError("One or both fighters not found")

    # 각 파이터의 통계 데이터 조회
    fighter1_basic_stats = await get_fighter_basic_stats_aggregate(session, fighter_id_1)
    fighter1_sig_str_stats = await get_fighter_sig_str_stats_aggregate(session, fighter_id_1)
    
    fighter2_basic_stats = await get_fighter_basic_stats_aggregate(session, fighter_id_2)
    fighter2_sig_str_stats = await get_fighter_sig_str_stats_aggregate(session, fighter_id_2)
    
    # 정확도 계산
    fighter1_accuracy = calculate_fighter_accuracy(fighter1_basic_stats, fighter1_sig_str_stats)
    fighter2_accuracy = calculate_fighter_accuracy(fighter2_basic_stats, fighter2_sig_str_stats)
    
    # 비교 결과 생성
    comparison = {}
    
    # 기본 통계 비교
    for stat_name in fighter1_basic_stats:
        if stat_name != "match_count":  # 경기 수는 별도 처리
            fighter1_val = fighter1_basic_stats[stat_name]
            fighter2_val = fighter2_basic_stats[stat_name]
            
            comparison[stat_name] = {
                "fighter1_value": fighter1_val,
                "fighter2_value": fighter2_val,
                "winner": "fighter1" if fighter1_val > fighter2_val else "fighter2" if fighter2_val > fighter1_val else "tie"
            }
    
    # 유효 타격 통계 비교
    for stat_name in fighter1_sig_str_stats:
        if stat_name != "match_count":
            fighter1_val = fighter1_sig_str_stats[stat_name]
            fighter2_val = fighter2_sig_str_stats[stat_name]
            
            comparison[stat_name] = {
                "fighter1_value": fighter1_val,
                "fighter2_value": fighter2_val,
                "winner": "fighter1" if fighter1_val > fighter2_val else "fighter2" if fighter2_val > fighter1_val else "tie"
            }
    
    # 정확도 비교
    accuracy_comparison = {}
    for acc_name in fighter1_accuracy:
        fighter1_acc = fighter1_accuracy[acc_name]
        fighter2_acc = fighter2_accuracy[acc_name]
        
        accuracy_comparison[acc_name] = {
            "fighter1_accuracy": fighter1_acc,
            "fighter2_accuracy": fighter2_acc,
            "winner": "fighter1" if fighter1_acc > fighter2_acc else "fighter2" if fighter2_acc > fighter1_acc else "tie"
        }
    
    return FighterStatsComparisonDTO(
        fighter1=FighterComparisonItemDTO(
            info=fighter1,
            basic_stats=fighter1_basic_stats,
            sig_str_stats=fighter1_sig_str_stats,
            accuracy=fighter1_accuracy
        ),
        fighter2=FighterComparisonItemDTO(
            info=fighter2,
            basic_stats=fighter2_basic_stats,
            sig_str_stats=fighter2_sig_str_stats,
            accuracy=fighter2_accuracy
        ),
        comparison=FighterComparisonStatsDTO(
            stats={k: StatComparisonDTO(**v) for k, v in comparison.items()},
            accuracy={k: AccuracyComparisonDTO(**v) for k, v in accuracy_comparison.items()}
        )
    )

async def get_fighter_with_top_stat(session: AsyncSession, stat_name: str, limit: int = 10) -> List[TopStatFighterDTO]:
    """
    특정 스탯에서 가장 높은 값을 가진 파이터를 조회
    """
    # 기본 스탯 매핑 (간단한 버전)
    if stat_name in ["wins", "losses", "draws"]:
        result = await get_top_fighter_by_record(session, stat_name, limit=limit)
        
        formatted_result = []
        for item in result:
            fighter = item["fighter"]
            total_stat = getattr(fighter, stat_name, 0)
            formatted_result.append(TopStatFighterDTO(
                rank=item["ranking"],
                fighter_name=fighter.name,
                fighter_id=fighter.id,
                stat_name=stat_name,
                total_stat=total_stat
            ))
        
        return formatted_result
    else:
        raise ValueError(f"Invalid stat_name: {stat_name}")


async def get_fighter_career_timeline(session: AsyncSession, fighter_id: int) -> FighterCareerTimelineDTO:
    """
    파이터의 커리어 타임라인을 이벤트와 매치 정보와 함께 조회합니다.
    """
    # 파이터의 모든 경기 기록 조회
    all_matches = await get_fighter_all_matches(session, fighter_id)
    
    if not all_matches:
        return FighterCareerTimelineDTO(
            fighter_id=fighter_id,
            career_timeline=[],
            summary=CareerSummaryDTO(
                total_fights=0, wins=0, losses=0, draws=0, max_win_streak=0, main_events=0, career_highlights=[]
            )
        )
    
    # 시간순으로 정렬 (이벤트 날짜 기준)
    sorted_matches = sorted(
        all_matches,
        key=lambda x: x.event.event_date if x.event and x.event.event_date else date.min
    )
    
    # 커리어 하이라이트 식별
    career_highlights = []
    win_streak = 0
    current_streak = 0
    max_win_streak = 0
    
    for i, match_data in enumerate(sorted_matches):
        result = match_data.result
        
        if result == "Win":
            current_streak += 1
            max_win_streak = max(max_win_streak, current_streak)
        else:
            current_streak = 0
        
        # 중요한 경기 식별 (메인 이벤트, 타이틀전 등)
        if match_data.match.is_main_event:
            career_highlights.append({
                "type": "main_event",
                "match_index": i,
                "description": f"Main event at {match_data.event.name if match_data.event else 'Unknown Event'}"
            })
    
    return FighterCareerTimelineDTO(
        fighter_id=fighter_id,
        career_timeline=sorted_matches,
        summary=CareerSummaryDTO(
            total_fights=len(sorted_matches),
            wins=len([m for m in sorted_matches if m.result == "Win"]),
            losses=len([m for m in sorted_matches if m.result == "Loss"]),
            draws=len([m for m in sorted_matches if m.result == "Draw"]),
            max_win_streak=max_win_streak,
            main_events=len([m for m in sorted_matches if m.match.is_main_event]),
            career_highlights=[CareerHighlightDTO(**h) for h in career_highlights]
        )
    )


async def analyze_fighter_vs_style(session: AsyncSession, fighter_id: int, opponent_stance: str) -> FighterVsStanceAnalysisDTO:
    """
    특정 파이터가 특정 스탠스의 상대들과의 대전 성과를 분석합니다.
    """
    from fighter.repositories import get_fighter_by_id
    from composition.repositories import get_all_opponents
    
    # 파이터 기본 정보 조회
    fighter = await get_fighter_by_id(session, fighter_id)
    if not fighter:
        from fighter.models import FighterSchema
        dummy_fighter = FighterSchema(id=0, name="Not Found", wins=0, losses=0, draws=0)
        return FighterVsStanceAnalysisDTO(
            fighter=dummy_fighter,
            opponent_stance=opponent_stance,
            analysis=StanceAnalysisStatsDTO(
                total_fights_vs_stance=0,
                wins=0,
                losses=0,
                win_percentage=0.0,
                detailed_results=[]
            )
        )
    
    # 모든 상대 조회
    all_opponents = await get_all_opponents(session, fighter_id)
    
    # 특정 스탠스의 상대들 필터링
    stance_opponents = [opp for opp in all_opponents if opp.stance and opp.stance.lower() == opponent_stance.lower()]
    
    if not stance_opponents:
        return FighterVsStanceAnalysisDTO(
            fighter=fighter,
            opponent_stance=opponent_stance,
            analysis=StanceAnalysisStatsDTO(
                total_fights_vs_stance=0,
                wins=0,
                losses=0,
                win_percentage=0.0,
                detailed_results=[]
            )
        )
    
    # 각 상대와의 결과 조회
    results = []
    wins = 0
    losses = 0
    
    for opponent in stance_opponents:
        # 해당 상대와의 대전 기록 조회
        vs_records = await get_fighter_vs_record(session, fighter_id, opponent.id)
        
        for record in vs_records:
            fighter_result = record.fighter1.result
            if fighter_result == "Win":
                wins += 1
            elif fighter_result == "Loss":
                losses += 1
            
            results.append(StanceAnalysisDetailDTO(
                opponent=opponent,
                result=fighter_result,
                match_details=record.match_info
            ))
    
    total_fights = wins + losses
    win_percentage = (wins / total_fights * 100) if total_fights > 0 else 0
    
    return FighterVsStanceAnalysisDTO(
        fighter=fighter,
        opponent_stance=opponent_stance,
        analysis=StanceAnalysisStatsDTO(
            total_fights_vs_stance=total_fights,
            wins=wins,
            losses=losses,
            win_percentage=round(win_percentage, 2),
            detailed_results=results
        )
    )


async def get_divisional_elite_comparison(session: AsyncSession, weight_class_id: int, top_n: int = 5) -> DivisionalEliteComparisonDTO:
    """
    특정 체급의 상위 파이터들을 종합적으로 비교 분석합니다.
    """
    from fighter.repositories import get_fighters_by_weight_class_ranking
    from common.models import WeightClassSchema
    
    # 체급명 조회
    weight_class_name = WeightClassSchema.get_name_by_id(weight_class_id)
    if not weight_class_name:
        # Return empty result for invalid weight class
        return DivisionalEliteComparisonDTO(
            weight_class="Unknown",
            weight_class_id=weight_class_id,
            elite_fighters=[],
            stat_leaders={},
            division_depth=0
        )
    
    # 해당 체급의 상위 랭킹 파이터들 조회
    top_fighters = await get_fighters_by_weight_class_ranking(session, weight_class_id)
    
    if not top_fighters:
        # Return empty result for no fighters
        return DivisionalEliteComparisonDTO(
            weight_class=weight_class_name,
            weight_class_id=weight_class_id,
            elite_fighters=[],
            stat_leaders={},
            division_depth=0
        )
    
    # 상위 N명만 선택
    elite_fighters = top_fighters[:top_n]
    
    # 각 파이터의 상세 통계 조회
    fighter_comparisons = []
    
    for fighter in elite_fighters:
        # 파이터의 종합 통계 조회
        fighter_stats = await get_fighter_total_stat(session, fighter.id)
        
        if fighter_stats:
            fighter_comparisons.append(EliteFighterComparisonDTO(
                fighter=fighter,
                stats=fighter_stats,
                ranking=elite_fighters.index(fighter) + 1
            ))
    
    # 통계별 리더 분석
    if fighter_comparisons:
        # 주요 통계 비교
        stat_leaders = {}
        
        # 기본 통계에서 리더 찾기
        for stat_name in ["knockdowns", "submission_attempts", "control_time_seconds"]:
            best_fighter = max(
                fighter_comparisons,
                key=lambda x: x.stats.basic_stats.get(stat_name, 0),
                default=None
            )
            if best_fighter:
                stat_leaders[stat_name] = StatLeaderDTO(
                    fighter=best_fighter.fighter,
                    value=best_fighter.stats.basic_stats.get(stat_name, 0)
                )
        
        # 정확도에서 리더 찾기
        for acc_name in ["overall_accuracy", "head_accuracy"]:
            best_fighter = max(
                fighter_comparisons,
                key=lambda x: x.stats.accuracy.get(acc_name, 0),
                default=None
            )
            if best_fighter:
                stat_leaders[acc_name] = StatLeaderDTO(
                    fighter=best_fighter.fighter,
                    value=best_fighter.stats.accuracy.get(acc_name, 0)
                )
    else:
        stat_leaders = {}
    
    return DivisionalEliteComparisonDTO(
        weight_class=weight_class_name,
        weight_class_id=weight_class_id,
        elite_fighters=fighter_comparisons,
        stat_leaders=stat_leaders,
        division_depth=len(top_fighters)
    )


async def predict_fight_outcome(session: AsyncSession, fighter_id1: int, fighter_id2: int) -> FightOutcomePredictionDTO:
    """
    두 파이터 간의 가상 매치업을 분석하고 결과를 예측합니다.
    """
    # 두 파이터의 종합 통계 비교
    comparison = await compare_fighters_stats(session, fighter_id1, fighter_id2)
    
    if not comparison:
        # Return dummy prediction for failed comparison
        from fighter.models import FighterSchema
        dummy_fighter = FighterSchema(id=0, name="Unknown", wins=0, losses=0, draws=0)
        return FightOutcomePredictionDTO(
            matchup=MatchupInfoDTO(fighter1=dummy_fighter, fighter2=dummy_fighter),
            prediction=FightPredictionDTO(
                fighter1_win_probability=50.0,
                fighter2_win_probability=50.0,
                predicted_winner=dummy_fighter,
                confidence="low"
            ),
            analysis_factors=AnalysisFactorsDTO(
                head_to_head_fights=0,
                common_opponents=0,
                statistical_comparison=FighterComparisonStatsDTO(
                    stats={}, accuracy={}
                ),
                scoring_breakdown=ScoringBreakdownDTO(fighter1_score=0, fighter2_score=0)
            )
        )
    
    # 과거 대전 기록 조회
    head_to_head = await get_fighter_vs_record(session, fighter_id1, fighter_id2)
    
    # 공통 상대 분석
    from composition.repositories import get_fighters_common_opponents
    common_opponents = await get_fighters_common_opponents(session, fighter_id1, fighter_id2)
    
    # 예측 점수 계산
    fighter1_score = 0
    fighter2_score = 0
    
    # 전적 기반 점수
    f1_record = comparison.fighter1.info
    f2_record = comparison.fighter2.info
    
    f1_win_rate = f1_record.wins / (f1_record.wins + f1_record.losses) if (f1_record.wins + f1_record.losses) > 0 else 0
    f2_win_rate = f2_record.wins / (f2_record.wins + f2_record.losses) if (f2_record.wins + f2_record.losses) > 0 else 0
    
    if f1_win_rate > f2_win_rate:
        fighter1_score += 2
    elif f2_win_rate > f1_win_rate:
        fighter2_score += 2
    
    # 과거 대전 기록 기반 점수
    if head_to_head:
        f1_wins_vs_f2 = len([h for h in head_to_head if h.fighter1.result == "Win"])
        f2_wins_vs_f1 = len([h for h in head_to_head if h.fighter2.result == "Win"])
        
        if f1_wins_vs_f2 > f2_wins_vs_f1:
            fighter1_score += 3
        elif f2_wins_vs_f1 > f1_wins_vs_f2:
            fighter2_score += 3
    
    # 공통 상대 기반 점수
    f1_wins_vs_common = len([c for c in common_opponents if c.get("fighter1_result") == "Win"])
    f2_wins_vs_common = len([c for c in common_opponents if c.get("fighter2_result") == "Win"])
    
    if f1_wins_vs_common > f2_wins_vs_common:
        fighter1_score += 1
    elif f2_wins_vs_common > f1_wins_vs_common:
        fighter2_score += 1
    
    # 통계 기반 점수 (정확도, 피니시 능력 등)
    f1_accuracy = comparison.fighter1.accuracy.get("overall_accuracy", 0)
    f2_accuracy = comparison.fighter2.accuracy.get("overall_accuracy", 0)
    
    if f1_accuracy > f2_accuracy:
        fighter1_score += 1
    elif f2_accuracy > f1_accuracy:
        fighter2_score += 1
    
    # 예측 결과
    total_score = fighter1_score + fighter2_score
    f1_probability = (fighter1_score / total_score * 100) if total_score > 0 else 50
    f2_probability = (fighter2_score / total_score * 100) if total_score > 0 else 50
    
    return FightOutcomePredictionDTO(
        matchup=MatchupInfoDTO(
            fighter1=comparison.fighter1.info,
            fighter2=comparison.fighter2.info
        ),
        prediction=FightPredictionDTO(
            fighter1_win_probability=round(f1_probability, 2),
            fighter2_win_probability=round(f2_probability, 2),
            predicted_winner=comparison.fighter1.info if fighter1_score > fighter2_score else comparison.fighter2.info,
            confidence="high" if abs(fighter1_score - fighter2_score) >= 3 else "medium" if abs(fighter1_score - fighter2_score) >= 2 else "low"
        ),
        analysis_factors=AnalysisFactorsDTO(
            head_to_head_fights=len(head_to_head),
            common_opponents=len(common_opponents),
            statistical_comparison=comparison.comparison,
            scoring_breakdown=ScoringBreakdownDTO(
                fighter1_score=fighter1_score,
                fighter2_score=fighter2_score
            )
        )
    )