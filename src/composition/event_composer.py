from typing import Optional, List, Dict, Any
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from event import repositories as event_repo
from match import repositories as match_repo
from composition.repositories import get_event_with_matches_summary, get_event_main_event_match
from composition.dto import (
    EventWithAllMatchesDTO, EventWithMainMatchDTO, UpcomingEventWithFeaturedMatchesDTO,
    EventComparisonDTO, EventRankingImpactDTO, MatchDetailDTO, MatchFighterResultDTO,
    EventSummaryStatsDTO, EventComparisonItemDTO, EventComparisonStatsDTO,
    FeaturedMatchDTO, MatchRankingImpactDTO, RankingImpactFighterDTO, 
    PotentialImpactDTO, RankingImpactSummaryDTO, RankingInfoDTO
)


async def get_event_with_all_matches(session: AsyncSession, event_name: str) -> Optional[EventWithAllMatchesDTO]:
    """
    특정 이벤트에 속한 모든 경기와 승패결과를 조회합니다.
    """
    # 이벤트 이름으로 이벤트 조회
    event = await event_repo.get_event_by_name(session, event_name)
    if not event:
        return None
    
    # 이벤트의 모든 매치와 요약 정보 조회
    event_summary = await get_event_with_matches_summary(session, event.id)
    
    if not event_summary:
        return None
    
    # 각 매치의 파이터 정보와 결과 추가
    matches_with_results = []
    for match in event_summary["matches"]:
        # 매치에 참여한 파이터들과 결과 조회
        match_result = await match_repo.get_match_with_winner_loser(session, match.id)
        if match_result:
            # fighters를 MatchFighterResultDTO로 변환
            fighters = [
                MatchFighterResultDTO(
                    fighter=fighter["fighter"],
                    result=fighter.get("result")
                ) for fighter in match_result["fighters"]
            ]
            
            winner = None
            loser = None
            if match_result.get("winner"):
                winner = MatchFighterResultDTO(
                    fighter=match_result["winner"]["fighter"],
                    result=match_result["winner"].get("result")
                )
            if match_result.get("loser"):
                loser = MatchFighterResultDTO(
                    fighter=match_result["loser"]["fighter"],
                    result=match_result["loser"].get("result")
                )
            
            matches_with_results.append(MatchDetailDTO(
                match_info=match,
                fighters=fighters,
                winner=winner,
                loser=loser
            ))
    
    return EventWithAllMatchesDTO(
        event=event_summary["event"],
        matches=matches_with_results,
        summary=EventSummaryStatsDTO(
            total_matches=event_summary["summary"]["total_matches"],
            main_events_count=event_summary["summary"]["main_events_count"],
            finish_methods=event_summary["summary"]["finish_methods"]
        )
    )


async def get_recent_events_with_main_match(session: AsyncSession, limit: int = 10) -> List[EventWithMainMatchDTO]:
    """
    최근 event와 메인 이벤트 경기만 조회
    """
    # 최근 이벤트들 조회
    recent_events = await event_repo.get_recent_events(session, limit)
    
    results = []
    for event in recent_events:
        # 각 이벤트의 메인 이벤트 매치 조회
        main_match = await get_event_main_event_match(session, event.id)
        
        main_match_detail = None
        if main_match:
            # 메인 매치의 파이터 정보와 결과 조회
            match_detail = await match_repo.get_match_with_winner_loser(session, main_match.id)
            if match_detail:
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
                
                main_match_detail = MatchDetailDTO(
                    match_info=main_match,
                    fighters=fighters,
                    winner=winner,
                    loser=loser
                )
        
        results.append(EventWithMainMatchDTO(
            event=event,
            main_match=main_match_detail
        ))
    
    return results


async def get_upcoming_events_with_featured_matches(session: AsyncSession, limit: int = 5) -> List[UpcomingEventWithFeaturedMatchesDTO]:
    """
    다가오는 이벤트들과 주목할만한 매치들을 조회합니다.
    """
    # 다가오는 이벤트들 조회
    upcoming_events = await event_repo.get_upcoming_events(session, limit)
    
    results = []
    for event in upcoming_events:
        # 이벤트의 모든 매치 조회
        event_matches = await match_repo.get_matches_by_event_id(session, event.id)
        
        # 메인 이벤트와 주요 매치들 식별
        main_event = None
        featured_matches = []
        
        for match in event_matches:
            match_detail = await match_repo.get_match_with_participants(session, match.id)
            
            # fighters를 MatchFighterResultDTO로 변환
            fighters = []
            if match_detail and match_detail.get("fighters"):
                fighters = [
                    MatchFighterResultDTO(
                        fighter=fighter["fighter"],
                        result=fighter.get("result")
                    ) for fighter in match_detail["fighters"]
                ]
            
            if match.is_main_event:
                main_event = FeaturedMatchDTO(
                    match_info=match,
                    fighters=fighters
                )
            elif match.order and match.order >= 3:  # 상위 카드 매치들
                featured_matches.append(FeaturedMatchDTO(
                    match_info=match,
                    fighters=fighters
                ))
        
        results.append(UpcomingEventWithFeaturedMatchesDTO(
            event=event,
            main_event=main_event,
            featured_matches=featured_matches[:3]  # 최대 3개의 주요 매치
        ))
    
    return results


async def compare_events_by_performance(session: AsyncSession, event_id1: int, event_id2: int) -> Optional[EventComparisonDTO]:
    """
    두 이벤트의 성과를 비교 분석합니다.
    """
    # 두 이벤트의 요약 정보 조회
    event1_summary = await get_event_with_matches_summary(session, event_id1)
    event2_summary = await get_event_with_matches_summary(session, event_id2)
    
    if not event1_summary or not event2_summary:
        return None
    
    # 매치 통계 비교
    event1_stats = event1_summary["summary"]
    event2_stats = event2_summary["summary"]
    
    return EventComparisonDTO(
        event1=EventComparisonItemDTO(
            event_info=event1_summary["event"],
            stats=EventSummaryStatsDTO(
                total_matches=event1_stats["total_matches"],
                main_events_count=event1_stats["main_events_count"],
                finish_methods=event1_stats["finish_methods"]
            )
        ),
        event2=EventComparisonItemDTO(
            event_info=event2_summary["event"],
            stats=EventSummaryStatsDTO(
                total_matches=event2_stats["total_matches"],
                main_events_count=event2_stats["main_events_count"],
                finish_methods=event2_stats["finish_methods"]
            )
        ),
        comparison=EventComparisonStatsDTO(
            more_matches="event1" if event1_stats["total_matches"] > event2_stats["total_matches"] else "event2" if event2_stats["total_matches"] > event1_stats["total_matches"] else "equal",
            more_main_events="event1" if event1_stats["main_events_count"] > event2_stats["main_events_count"] else "event2" if event2_stats["main_events_count"] > event1_stats["main_events_count"] else "equal",
            match_difference=abs(event1_stats["total_matches"] - event2_stats["total_matches"])
        )
    )


async def get_event_rankings_impact(session: AsyncSession, event_id: int) -> EventRankingImpactDTO:
    """
    특정 이벤트가 파이터 랭킹에 미친 영향을 분석합니다.
    """
    from fighter import repositories as fighter_repo
    
    # 이벤트의 모든 매치 조회
    event_matches = await match_repo.get_matches_by_event_id(session, event_id)
    
    ranking_impacts = []
    
    for match in event_matches:
        # 매치 결과 조회
        match_result = await match_repo.get_match_with_winner_loser(session, match.id)
        
        if match_result and match_result.get("winner") and match_result.get("loser"):
            winner = match_result["winner"]
            loser = match_result["loser"]
            
            # 승자와 패자의 현재 랭킹 조회
            winner_fighter = winner["fighter"] if isinstance(winner["fighter"], dict) else winner["fighter"]
            loser_fighter = loser["fighter"] if isinstance(loser["fighter"], dict) else loser["fighter"]
            
            winner_fighter_id = winner_fighter.id if hasattr(winner_fighter, 'id') else winner_fighter["id"]
            loser_fighter_id = loser_fighter.id if hasattr(loser_fighter, 'id') else loser_fighter["id"]
            
            winner_rankings = await fighter_repo.get_ranking_by_fighter_id(session, winner_fighter_id)
            loser_rankings = await fighter_repo.get_ranking_by_fighter_id(session, loser_fighter_id)
            
            # RankingInfoDTO 변환
            winner_ranking_dtos = [
                RankingInfoDTO(ranking=r.ranking, weight_class_id=r.weight_class_id)
                for r in winner_rankings
            ]
            loser_ranking_dtos = [
                RankingInfoDTO(ranking=r.ranking, weight_class_id=r.weight_class_id)
                for r in loser_rankings
            ]
            
            ranking_impacts.append(MatchRankingImpactDTO(
                match=match,
                winner=RankingImpactFighterDTO(
                    fighter=winner_fighter,
                    rankings=winner_ranking_dtos
                ),
                loser=RankingImpactFighterDTO(
                    fighter=loser_fighter,
                    rankings=loser_ranking_dtos
                ),
                potential_impact=PotentialImpactDTO(
                    winner_moving_up=len(winner_rankings) > 0,
                    loser_moving_down=len(loser_rankings) > 0,
                    title_implications=match.is_main_event or any(r.ranking <= 5 for r in winner_rankings + loser_rankings)
                )
            ))
    
    return EventRankingImpactDTO(
        event_id=event_id,
        ranking_impacts=ranking_impacts,
        summary=RankingImpactSummaryDTO(
            matches_with_ranked_fighters=len([r for r in ranking_impacts if r.potential_impact.winner_moving_up or r.potential_impact.loser_moving_down]),
            title_implication_matches=len([r for r in ranking_impacts if r.potential_impact.title_implications])
        )
    )