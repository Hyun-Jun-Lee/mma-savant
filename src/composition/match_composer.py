from typing import List, Dict, Any, Optional
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from match import repositories as match_repo
from match.exceptions import MatchValidationError, MatchNotFoundError, MatchQueryError
from event import repositories as event_repo
from fighter import repositories as fighter_repo
from composition.repositories import (
    get_event_with_matches_summary,
    get_fighter_performance_trend,
    get_top_performers_in_event,
    get_finish_rate_by_method
)
from composition.exceptions import (
    CompositionValidationError, CompositionNotFoundError, CompositionQueryError,
    CompositionDomainError
)
from composition.dto import (
    FOTNCandidatesDTO, FOTNCandidateDTO, FOTNAnalysisDTO, MatchFighterResultDTO,
    CardQualityAnalysisDTO, CardAnalysisDTO, QualityIndicatorsDTO,
    ExcitingMatchDTO, ExcitingMatchHighlightsDTO,
    ComebackPerformancesDTO, ComebackPerformanceDTO, ComebackAnalysisDTO,
    StyleClashAnalysisDTO, StyleContrastDTO,
    PerformanceOutliersDTO, PerformanceOutlierDTO, OutlierPerformanceDTO, OutlierAnalysisSummaryDTO,
    EventMatchesDTO, MatchWithFightersDTO, FighterBasicInfoDTO
)


async def get_event_matches(session: AsyncSession, event_name: str) -> EventMatchesDTO:
    """
    특정 이벤트에 속한 모든 경기와 참가 파이터 정보를 조회합니다.
    """
    # 입력 검증
    if not event_name or not event_name.strip():
        raise MatchValidationError("event_name", event_name, "Event name cannot be empty")
    
    try:
        event = await event_repo.get_event_by_name(session, event_name)
        if not event:
            raise MatchNotFoundError(event_name, "event_name")

        matches = await match_repo.get_matches_by_event_id(session, event.id)
        matches_list = []
        # match.order로 정렬
        sorted_matches = sorted(matches, key=lambda m: m.order if m.order is not None else 999)
        
        for match in sorted_matches:
            fighter_matches = await match_repo.get_fighter_match_by_match_id(session, match.id)
            winner_fighter = None
            loser_fighter = None        
            draw_fighters = []
            
            for fighter_match in fighter_matches:
                fighter = await fighter_repo.get_fighter_by_id(session, fighter_match.fighter_id)
                if not fighter:
                    # 파이터를 찾을 수 없는 경우 경고만 하고 계속 진행
                    continue
                
                if fighter_match.result == "win":
                    winner_fighter = FighterBasicInfoDTO(
                        id=fighter.id,
                        name=fighter.name
                    )
                elif fighter_match.result == "loss":
                    loser_fighter = FighterBasicInfoDTO(
                        id=fighter.id,
                        name=fighter.name
                    )
                elif fighter_match.result == "draw":
                    draw_fighters.append(FighterBasicInfoDTO(
                        id=fighter.id,
                        name=fighter.name
                    ))
            
            match_info = MatchWithFightersDTO(
                match=match,
                winner_fighter=winner_fighter,
                loser_fighter=loser_fighter,
                draw_fighters=draw_fighters if draw_fighters else None
            )
                
            matches_list.append(match_info)

        return EventMatchesDTO(
            event_name=event.name,
            event_date=event.event_date,
            matches=matches_list
        )
    
    except MatchNotFoundError:
        raise CompositionNotFoundError("Event", event_name, "get_event_matches")
    except MatchValidationError as e:
        raise CompositionValidationError("event_name", event_name, str(e))
    except Exception as e:
        raise CompositionQueryError("get_event_matches", {"event_name": event_name}, str(e))


async def get_fight_of_the_night_candidates(session: AsyncSession, event_id: int) -> FOTNCandidatesDTO:
    """
    특정 이벤트에서 Fight of the Night 후보가 될만한 경기들을 분석합니다.
    통계적 성과와 엔터테인먼트 가치를 기준으로 평가합니다.
    """
    # 입력 검증
    if not isinstance(event_id, int) or event_id <= 0:
        raise CompositionValidationError("event_id", event_id, "event_id must be a positive integer")
    
    try:
        # 이벤트의 모든 매치와 요약 정보 조회
        event_summary = await get_event_with_matches_summary(session, event_id)
        
        if not event_summary:
            raise CompositionNotFoundError("Event", event_id, "get_fight_of_the_night_candidates")
        
        fight_candidates = []
        
        for match in event_summary["matches"]:
            # 매치의 파이터들과 결과 조회
            match_detail = await match_repo.get_match_with_winner_loser(session, match.id)
            
            if not match_detail:
                continue
            
            # 매치의 통계 데이터 조회
            match_stats = await match_repo.get_match_statistics(session, match.id)
            
            # Fight of the Night 점수 계산
            fotn_score = 0
            
            # 경기 지속 시간 (라운드 수와 시간)
            round_factor = match.result_round if match.result_round else 1
            if round_factor >= 3:  # 3라운드 이상 지속
                fotn_score += 3
            elif round_factor >= 2:
                fotn_score += 2
            
            # 피니시 방법 (KO/TKO, 서브미션은 엔터테인먼트 가치 높음)
            if match.method:
                if "KO" in match.method or "TKO" in match.method:
                    fotn_score += 2
                elif "Submission" in match.method:
                    fotn_score += 2
                elif "Decision" in match.method and round_factor >= 3:
                    fotn_score += 1
            
            # 통계 기반 점수 (활발한 경기)
            if match_stats:
                total_strikes = match_stats.get("total_strikes_attempted", 0)
                if total_strikes > 200:  # 활발한 타격전
                    fotn_score += 2
                elif total_strikes > 100:
                    fotn_score += 1
            
            # 메인 이벤트나 상위 카드는 가산점
            if match.is_main_event:
                fotn_score += 1
            elif match.order and match.order >= 4:
                fotn_score += 0.5
            
            # fighters를 MatchFighterResultDTO로 변환
            fighters = [
                MatchFighterResultDTO(
                    fighter=fighter["fighter"],
                    result=fighter.get("result")
                ) for fighter in match_detail["fighters"]
            ]
            
            winner = None
            loser = None
            if match_detail.get("winner"):
                winner = MatchFighterResultDTO(
                    fighter=match_detail["winner"]["fighter"],
                    result=match_detail["winner"].get("result")
                )
            if match_detail.get("loser"):
                loser = MatchFighterResultDTO(
                    fighter=match_detail["loser"]["fighter"],
                    result=match_detail["loser"].get("result")
                )
            
            fight_candidates.append(FOTNCandidateDTO(
                match=match,
                fighters=fighters,
                winner=winner,
                loser=loser,
                fotn_score=fotn_score,
                analysis=FOTNAnalysisDTO(
                    duration_rounds=round_factor,
                    finish_method=match.method,
                    entertainment_value="high" if fotn_score >= 5 else "medium" if fotn_score >= 3 else "low"
                )
            ))
        
        # 점수순으로 정렬
        fight_candidates.sort(key=lambda x: x.fotn_score, reverse=True)
    
        return FOTNCandidatesDTO(
            event=event_summary["event"],
            fotn_candidates=fight_candidates[:5],  # 상위 5개 후보
            analysis_criteria="Duration, finish method, striking activity, card position"
        )
    
    except CompositionValidationError:
        raise
    except CompositionNotFoundError:
        raise
    except Exception as e:
        raise CompositionQueryError("get_fight_of_the_night_candidates", {"event_id": event_id}, str(e))


async def analyze_card_quality(session: AsyncSession, event_id: int) -> CardQualityAnalysisDTO:
    """
    이벤트 카드의 전반적인 품질을 분석합니다.
    랭킹된 파이터 수, 타이틀전, 경기 다양성 등을 평가합니다.
    """
    # 입력 검증
    if not isinstance(event_id, int) or event_id <= 0:
        raise CompositionValidationError("event_id", event_id, "event_id must be a positive integer")
    
    try:
        # 이벤트 기본 정보 조회
        event = await event_repo.get_event_by_id(session, event_id)
        if not event:
            raise CompositionNotFoundError("Event", event_id, "analyze_card_quality")
        
        # 이벤트의 모든 매치 조회
        event_matches = await match_repo.get_matches_by_event_id(session, event_id)
        
        if not event_matches:
            # Return empty analysis for events with no matches
            return CardQualityAnalysisDTO(
                event=event,
                card_analysis=CardAnalysisDTO(
                    total_matches=0,
                    main_events=0,
                    ranked_fighters=0,
                    champions=0,
                    weight_classes=[],
                    finish_methods={},
                    unique_fighters=0,
                    ranked_fighter_percentage=0.0,
                    finish_rate=0.0
                ),
                quality_assessment=QualityIndicatorsDTO(
                    overall_grade="No Matches",
                    quality_score=0,
                    max_score=10
                )
            )
        
        # 카드 품질 분석
        card_analysis = {
            "total_matches": len(event_matches),
            "main_events": 0,
            "ranked_fighters": 0,
            "champions": 0,
            "weight_classes": set(),
            "finish_methods": {},
            "quality_indicators": {}
        }
        
        all_fighters = set()
        
        for match in event_matches:
            if match.is_main_event:
                card_analysis["main_events"] += 1
            
            # 체급 다양성
            if match.weight_class_id:
                card_analysis["weight_classes"].add(match.weight_class_id)
            
            # 피니시 방법 통계
            if match.method:
                method = match.method
                card_analysis["finish_methods"][method] = card_analysis["finish_methods"].get(method, 0) + 1
            
            # 매치의 파이터들 조회
            fighter_matches = await match_repo.get_fighter_match_by_match_id(session, match.id)
            
            for fm in fighter_matches:
                fighter = await fighter_repo.get_fighter_by_id(session, fm.fighter_id)
                if fighter:
                    all_fighters.add(fighter.id)
                    
                    # 랭킹 확인
                    rankings = await fighter_repo.get_ranking_by_fighter_id(session, fighter.id)
                    if rankings:
                        card_analysis["ranked_fighters"] += 1
                    
                    # 챔피언 확인
                    if fighter.belt:
                        card_analysis["champions"] += 1
        
        # 품질 지표 계산
        ranked_fighter_percentage = (card_analysis["ranked_fighters"] / (len(all_fighters) * 2)) * 100 if all_fighters else 0
        weight_class_diversity = len(card_analysis["weight_classes"])
        finish_rate = len([m for m in event_matches if m.method and "Decision" not in m.method]) / len(event_matches) * 100
        
        # 전반적인 카드 등급 계산
        quality_score = 0
        
        # 랭킹된 파이터 비율 (40% 이상이면 high quality)
        if ranked_fighter_percentage >= 40:
            quality_score += 3
        elif ranked_fighter_percentage >= 20:
            quality_score += 2
        elif ranked_fighter_percentage >= 10:
            quality_score += 1
        
        # 챔피언 참여
        if card_analysis["champions"] >= 2:
            quality_score += 3
        elif card_analysis["champions"] >= 1:
            quality_score += 2
        
        # 체급 다양성
        if weight_class_diversity >= 5:
            quality_score += 2
        elif weight_class_diversity >= 3:
            quality_score += 1
        
        # 피니시 레이트
        if finish_rate >= 60:
            quality_score += 2
        elif finish_rate >= 40:
            quality_score += 1
        
        # 카드 등급 결정
        if quality_score >= 8:
            card_grade = "Premium"
        elif quality_score >= 6:
            card_grade = "High Quality"
        elif quality_score >= 4:
            card_grade = "Good"
        elif quality_score >= 2:
            card_grade = "Average"
        else:
            card_grade = "Below Average"
        
        return CardQualityAnalysisDTO(
            event=event,
            card_analysis=CardAnalysisDTO(
                total_matches=card_analysis["total_matches"],
                main_events=card_analysis["main_events"],
                ranked_fighters=card_analysis["ranked_fighters"],
                champions=card_analysis["champions"],
                weight_classes=list(card_analysis["weight_classes"]),
                finish_methods=card_analysis["finish_methods"],
                unique_fighters=len(all_fighters),
                ranked_fighter_percentage=round(ranked_fighter_percentage, 2),
                finish_rate=round(finish_rate, 2)
            ),
            quality_assessment=QualityIndicatorsDTO(
                overall_grade=card_grade,
                quality_score=quality_score,
                max_score=10
            )
        )
    
    except CompositionValidationError:
        raise
    except CompositionNotFoundError:
        raise
    except Exception as e:
        raise CompositionQueryError("analyze_card_quality", {"event_id": event_id}, str(e))


async def get_most_exciting_matches_by_period(session: AsyncSession, days: int = 30, limit: int = 10) -> List[ExcitingMatchDTO]:
    """
    지정된 기간 내에서 가장 흥미진진한 경기들을 분석합니다.
    """
    # 입력 검증
    if not isinstance(days, int) or days <= 0:
        raise CompositionValidationError("days", days, "days must be a positive integer")
    if not isinstance(limit, int) or limit <= 0:
        raise CompositionValidationError("limit", limit, "limit must be a positive integer")
    
    try:
        # 지정된 기간의 시작일 계산
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # 해당 기간의 이벤트들 조회
        events = await event_repo.get_events_date_range(session, start_date, end_date)
        
        exciting_matches = []
        
        for event in events:
            # 각 이벤트의 매치들 조회
            event_matches = await match_repo.get_matches_by_event_id(session, event.id)
            
            for match in event_matches:
                # 매치 상세 정보와 통계 조회
                match_detail = await match_repo.get_match_with_winner_loser(session, match.id)
                
                if not match_detail:
                    continue
                
                # 흥미도 점수 계산
                excitement_score = 0
                
                # 피니시 보너스
                if match.method:
                    if "KO" in match.method or "TKO" in match.method:
                        excitement_score += 4
                    elif "Submission" in match.method:
                        excitement_score += 3
                    elif "Decision" in match.method:
                        # 결정승이면 라운드 수에 따라 점수
                        if match.result_round and match.result_round >= 3:
                            excitement_score += 2
                
                # 메인 이벤트 보너스
                if match.is_main_event:
                    excitement_score += 2
                
                # 랭킹된 파이터들 보너스
                ranked_fighters = 0
                for fighter_info in match_detail["fighters"]:
                    fighter = fighter_info["fighter"]
                    rankings = await fighter_repo.get_ranking_by_fighter_id(session, fighter["id"])
                    if rankings:
                        ranked_fighters += 1
                
                if ranked_fighters >= 2:
                    excitement_score += 3
                elif ranked_fighters >= 1:
                    excitement_score += 1
                
                # 챔피언 참여 보너스
                champions = sum(1 for f in match_detail["fighters"] if f["fighter"].get("belt", False))
                excitement_score += champions * 2
                
                # fighters를 MatchFighterResultDTO로 변환
                fighters = [
                    MatchFighterResultDTO(
                        fighter=fighter["fighter"],
                        result=fighter.get("result")
                    ) for fighter in match_detail["fighters"]
                ]
                
                winner = None
                if match_detail.get("winner"):
                    winner = MatchFighterResultDTO(
                        fighter=match_detail["winner"]["fighter"],
                        result=match_detail["winner"].get("result")
                    )
                
                exciting_matches.append(ExcitingMatchDTO(
                    event=event,
                    match=match,
                    fighters=fighters,
                    winner=winner,
                    excitement_score=excitement_score,
                    highlights=ExcitingMatchHighlightsDTO(
                        finish_method=match.method,
                        ranked_fighters=ranked_fighters,
                        champions_involved=champions,
                        main_event=match.is_main_event
                    )
                ))
        
        # 흥미도 점수순으로 정렬
        exciting_matches.sort(key=lambda x: x.excitement_score, reverse=True)
        
        return exciting_matches[:limit]
    
    except CompositionValidationError:
        raise
    except Exception as e:
        raise CompositionQueryError("get_most_exciting_matches_by_period", {"days": days, "limit": limit}, str(e))


async def analyze_comeback_performances(session: AsyncSession, event_id: int) -> ComebackPerformancesDTO:
    """
    특정 이벤트에서 컴백 승리나 역전승을 분석합니다.
    """
    # 입력 검증
    if not isinstance(event_id, int) or event_id <= 0:
        raise CompositionValidationError("event_id", event_id, "event_id must be a positive integer")
    
    try:
        # 이벤트의 모든 매치 조회
        event_matches = await match_repo.get_matches_by_event_id(session, event_id)
        
        comeback_performances = []
        
        for match in event_matches:
            # 매치가 2라운드 이상 지속되고 피니시로 끝난 경우만 분석
            if not match.result_round or match.result_round < 2:
                continue
            
            if not match.method or "Decision" in match.method:
                continue
            
            # 매치 결과와 파이터 정보 조회
            match_detail = await match_repo.get_match_with_winner_loser(session, match.id)
            
            if not match_detail or not match_detail.get("winner"):
                continue
            
            # 각 파이터의 최근 성과 트렌드 분석
            winner = match_detail["winner"]
            loser = match_detail["loser"]
            
            if winner and loser:
                # 승자의 최근 폼 확인
                winner_trend = await get_fighter_performance_trend(session, winner["fighter"]["id"], 3)
                loser_trend = await get_fighter_performance_trend(session, loser["fighter"]["id"], 3)
                
                # 컴백 시나리오 확인
                comeback_indicators = []
                
                # 패배자가 더 좋은 최근 폼을 가지고 있었다면
                if (loser_trend.get("win_percentage", 0) > winner_trend.get("win_percentage", 0) and 
                    loser_trend.get("win_percentage", 0) >= 70):
                    comeback_indicators.append("upset_victory")
                
                # 늦은 라운드 피니시 (3라운드 이후)
                if match.result_round >= 3:
                    comeback_indicators.append("late_finish")
                
                # 서브미션이나 KO로 끝난 경우
                if match.method:
                    if "Submission" in match.method:
                        comeback_indicators.append("submission_comeback")
                    elif "KO" in match.method or "TKO" in match.method:
                        comeback_indicators.append("knockout_comeback")
                
                if comeback_indicators:
                    winner_dto = MatchFighterResultDTO(
                        fighter=winner["fighter"],
                        result=winner.get("result")
                    )
                    loser_dto = MatchFighterResultDTO(
                        fighter=loser["fighter"],
                        result=loser.get("result")
                    )
                    
                    comeback_performances.append(ComebackPerformanceDTO(
                        match=match,
                        winner=winner_dto,
                        loser=loser_dto,
                        comeback_type=comeback_indicators,
                        analysis=ComebackAnalysisDTO(
                            finish_round=match.result_round,
                            finish_method=match.method,
                            winner_recent_form=winner_trend.get("trend", "unknown"),
                            loser_recent_form=loser_trend.get("trend", "unknown"),
                            upset_factor=loser_trend.get("win_percentage", 0) - winner_trend.get("win_percentage", 0)
                        )
                    ))
        
        return ComebackPerformancesDTO(
            event_id=event_id,
            comeback_performances=comeback_performances,
            total_comebacks=len(comeback_performances)
        )
    
    except CompositionValidationError:
        raise
    except Exception as e:
        raise CompositionQueryError("analyze_comeback_performances", {"event_id": event_id}, str(e))


async def get_style_clash_analysis(session: AsyncSession, match_id: int) -> StyleClashAnalysisDTO:
    """
    특정 매치에서 파이터들의 스타일 대조를 분석합니다.
    """
    # 입력 검증
    if not isinstance(match_id, int) or match_id <= 0:
        raise CompositionValidationError("match_id", match_id, "match_id must be a positive integer")
    
    try:
        # 매치 기본 정보 조회
        match = await match_repo.get_match_by_id(session, match_id)
        if not match:
            raise CompositionNotFoundError("Match", match_id, "get_style_clash_analysis")
    
        # 매치의 파이터들 조회
        match_detail = await match_repo.get_match_with_winner_loser(session, match_id)
        if not match_detail or len(match_detail["fighters"]) != 2:
            raise CompositionNotFoundError("Match fighters", match_id, "two fighters required for style analysis")
    
        fighter1 = match_detail["fighters"][0]["fighter"]
        fighter2 = match_detail["fighters"][1]["fighter"]
        
        # 각 파이터의 상세 정보 조회
        fighter1_detail = await fighter_repo.get_fighter_by_id(session, fighter1["id"])
        fighter2_detail = await fighter_repo.get_fighter_by_id(session, fighter2["id"])
        
        if not fighter1_detail:
            raise CompositionNotFoundError("Fighter", fighter1["id"], "get_style_clash_analysis")
        if not fighter2_detail:
            raise CompositionNotFoundError("Fighter", fighter2["id"], "get_style_clash_analysis")
    
        # 스타일 대조 분석
        style_contrasts = []
        
        # 스탠스 대조
        if fighter1_detail.stance and fighter2_detail.stance:
            if fighter1_detail.stance != fighter2_detail.stance:
                style_contrasts.append(StyleContrastDTO(
                    aspect="stance",
                    fighter1=fighter1_detail.stance,
                    fighter2=fighter2_detail.stance,
                    analysis=f"Orthodox vs Southpaw clash" if {fighter1_detail.stance, fighter2_detail.stance} == {"Orthodox", "Southpaw"} else "Different stances"
                ))
        
        # 신체 조건 대조
        if fighter1_detail.height and fighter2_detail.height:
            height_diff = abs(fighter1_detail.height - fighter2_detail.height)
            if height_diff >= 10:  # 10cm 이상 차이
                taller = fighter1_detail if fighter1_detail.height > fighter2_detail.height else fighter2_detail
                shorter = fighter2_detail if fighter1_detail.height > fighter2_detail.height else fighter1_detail
                style_contrasts.append(StyleContrastDTO(
                    aspect="height",
                    analysis=f"Significant height advantage: {taller.name} ({taller.height}cm) vs {shorter.name} ({shorter.height}cm)",
                    advantage=taller.name,
                    difference=round(height_diff, 1)
                ))
        
        # 리치 대조
        if fighter1_detail.reach and fighter2_detail.reach:
            reach_diff = abs(fighter1_detail.reach - fighter2_detail.reach)
            if reach_diff >= 8:  # 8cm 이상 차이
                longer_reach = fighter1_detail if fighter1_detail.reach > fighter2_detail.reach else fighter2_detail
                shorter_reach = fighter2_detail if fighter1_detail.reach > fighter2_detail.reach else fighter1_detail
                style_contrasts.append(StyleContrastDTO(
                    aspect="reach",
                    analysis=f"Reach advantage: {longer_reach.name} ({longer_reach.reach}cm) vs {shorter_reach.name} ({shorter_reach.reach}cm)",
                    advantage=longer_reach.name,
                    difference=round(reach_diff, 1)
                ))
        
        # 경험 대조
        f1_experience = fighter1_detail.wins + fighter1_detail.losses + fighter1_detail.draws
        f2_experience = fighter2_detail.wins + fighter2_detail.losses + fighter2_detail.draws
        
        experience_diff = abs(f1_experience - f2_experience)
        if experience_diff >= 10:  # 10경기 이상 차이
            veteran = fighter1_detail if f1_experience > f2_experience else fighter2_detail
            newer = fighter2_detail if f1_experience > f2_experience else fighter1_detail
            style_contrasts.append(StyleContrastDTO(
                aspect="experience",
                analysis=f"Experience gap: {veteran.name} ({f1_experience if veteran == fighter1_detail else f2_experience} fights) vs {newer.name} ({f2_experience if veteran == fighter1_detail else f1_experience} fights)",
                advantage=veteran.name,
                difference=experience_diff
            ))
        
        # 매치 결과와 스타일 대조의 상관관계 분석
        match_outcome_analysis = ""
        if match_detail.get("winner"):
            winner_name = match_detail["winner"]["fighter"]["name"]
            
            # 어떤 스타일적 우위가 승리로 이어졌는지 분석
            winner_advantages = [contrast for contrast in style_contrasts if contrast.advantage == winner_name]
            
            if winner_advantages:
                match_outcome_analysis = f"{winner_name} capitalized on advantages in: {', '.join([adv.aspect for adv in winner_advantages])}"
            else:
                match_outcome_analysis = f"{winner_name} overcame physical/experience disadvantages"
        
        return StyleClashAnalysisDTO(
            match=match,
            fighters=[fighter1_detail, fighter2_detail],
            style_contrasts=style_contrasts,
            match_result=match_detail,
            outcome_analysis=match_outcome_analysis,
            contrast_summary=f"Found {len(style_contrasts)} significant style contrasts"
        )
    
    except CompositionValidationError:
        raise
    except CompositionNotFoundError:
        raise
    except Exception as e:
        raise CompositionQueryError("get_style_clash_analysis", {"match_id": match_id}, str(e))


async def get_performance_outliers_in_event(session: AsyncSession, event_id: int) -> PerformanceOutliersDTO:
    """
    특정 이벤트에서 예상을 뛰어넘는 성과를 보인 파이터들을 분석합니다.
    """
    # 입력 검증
    if not isinstance(event_id, int) or event_id <= 0:
        raise CompositionValidationError("event_id", event_id, "event_id must be a positive integer")
    
    try:
        # 각 통계 카테고리별 상위 성과자들 조회
        striking_leaders = await get_top_performers_in_event(session, event_id, "sig_str_landed", 3)
        grappling_leaders = await get_top_performers_in_event(session, event_id, "takedowns", 3)
        control_leaders = await get_top_performers_in_event(session, event_id, "control_time_seconds", 3)
        
        outlier_performances = []
        
        # 각 카테고리에서 예외적 성과 분석
        for category, leaders, threshold in [
            ("striking", striking_leaders, 50),  # 50타 이상
            ("grappling", grappling_leaders, 3),  # 3회 이상 테이크다운
            ("control", control_leaders, 300)   # 5분 이상 컨트롤
        ]:
            
            for leader in leaders:
                if leader["stat_value"] >= threshold:
                    # 해당 파이터의 평균 성과와 비교
                    fighter = leader["fighter"]
                    fighter_id = fighter.id if hasattr(fighter, 'id') else fighter["id"]
                    
                    # 최근 경기들에서의 평균 성과 조회 (간단한 분석을 위해 현재 성과와 비교)
                    outlier_performances.append(PerformanceOutlierDTO(
                        fighter=leader["fighter"],
                        category=category,
                        performance=OutlierPerformanceDTO(
                            stat_name=leader["stat_name"],
                            value=leader["stat_value"],
                            threshold=threshold
                        ),
                        outlier_rating="exceptional" if leader["stat_value"] >= threshold * 2 else "notable"
                    ))
        
        return PerformanceOutliersDTO(
            event_id=event_id,
            outlier_performances=outlier_performances,
            analysis_summary=OutlierAnalysisSummaryDTO(
                total_outliers=len(outlier_performances),
                exceptional_performances=len([p for p in outlier_performances if p.outlier_rating == "exceptional"]),
                categories_analyzed=["striking", "grappling", "control"]
            )
        )
    
    except CompositionValidationError:
        raise
    except Exception as e:
        raise CompositionQueryError("get_performance_outliers_in_event", {"event_id": event_id}, str(e))