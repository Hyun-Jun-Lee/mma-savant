from typing import Optional, List, Dict, Any
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from event import repositories as event_repo
from match import repositories as match_repo
from composition.repositories import get_event_with_matches_summary, get_event_main_event_match


async def get_event_with_all_matches(session: AsyncSession, event_name: str) -> Optional[Dict[str, Any]]:
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
            matches_with_results.append({
                "match_info": match,
                "fighters": match_result["fighters"],
                "winner": match_result.get("winner"),
                "loser": match_result.get("loser")
            })
    
    return {
        "event": event_summary["event"],
        "matches": matches_with_results,
        "summary": event_summary["summary"]
    }


async def get_recent_events_with_main_match(session: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
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
                main_match_detail = {
                    "match_info": main_match,
                    "fighters": match_detail["fighters"],
                    "winner": match_detail.get("winner"),
                    "loser": match_detail.get("loser")
                }
        
        results.append({
            "event": event,
            "main_match": main_match_detail
        })
    
    return results


async def get_upcoming_events_with_featured_matches(session: AsyncSession, limit: int = 5) -> List[Dict[str, Any]]:
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
            
            if match.is_main_event:
                main_event = {
                    "match_info": match,
                    "fighters": match_detail.get("fighters", []) if match_detail else []
                }
            elif match.order and match.order >= 3:  # 상위 카드 매치들
                featured_matches.append({
                    "match_info": match,
                    "fighters": match_detail.get("fighters", []) if match_detail else []
                })
        
        results.append({
            "event": event,
            "main_event": main_event,
            "featured_matches": featured_matches[:3]  # 최대 3개의 주요 매치
        })
    
    return results


async def compare_events_by_performance(session: AsyncSession, event_id1: int, event_id2: int) -> Dict[str, Any]:
    """
    두 이벤트의 성과를 비교 분석합니다.
    """
    # 두 이벤트의 요약 정보 조회
    event1_summary = await get_event_with_matches_summary(session, event_id1)
    event2_summary = await get_event_with_matches_summary(session, event_id2)
    
    if not event1_summary or not event2_summary:
        return {"error": "One or both events not found"}
    
    # 매치 통계 비교
    event1_stats = event1_summary["summary"]
    event2_stats = event2_summary["summary"]
    
    comparison = {
        "event1": {
            "event_info": event1_summary["event"],
            "stats": event1_stats
        },
        "event2": {
            "event_info": event2_summary["event"],
            "stats": event2_stats
        },
        "comparison": {
            "more_matches": "event1" if event1_stats["total_matches"] > event2_stats["total_matches"] else "event2" if event2_stats["total_matches"] > event1_stats["total_matches"] else "equal",
            "more_main_events": "event1" if event1_stats["main_events_count"] > event2_stats["main_events_count"] else "event2" if event2_stats["main_events_count"] > event1_stats["main_events_count"] else "equal",
            "match_difference": abs(event1_stats["total_matches"] - event2_stats["total_matches"])
        }
    }
    
    return comparison


async def get_event_rankings_impact(session: AsyncSession, event_id: int) -> Dict[str, Any]:
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
            winner_rankings = await fighter_repo.get_ranking_by_fighter_id(session, winner["fighter"]["id"])
            loser_rankings = await fighter_repo.get_ranking_by_fighter_id(session, loser["fighter"]["id"])
            
            ranking_impacts.append({
                "match": match,
                "winner": {
                    "fighter": winner["fighter"],
                    "rankings": winner_rankings
                },
                "loser": {
                    "fighter": loser["fighter"],
                    "rankings": loser_rankings
                },
                "potential_impact": {
                    "winner_moving_up": len(winner_rankings) > 0,
                    "loser_moving_down": len(loser_rankings) > 0,
                    "title_implications": match.is_main_event or any(r.ranking <= 5 for r in winner_rankings + loser_rankings)
                }
            })
    
    return {
        "event_id": event_id,
        "ranking_impacts": ranking_impacts,
        "summary": {
            "matches_with_ranked_fighters": len([r for r in ranking_impacts if r["potential_impact"]["winner_moving_up"] or r["potential_impact"]["loser_moving_down"]]),
            "title_implication_matches": len([r for r in ranking_impacts if r["potential_impact"]["title_implications"]])
        }
    }