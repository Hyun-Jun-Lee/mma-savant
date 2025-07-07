from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from match.dto import EventMatchesDTO, MatchWithFightersDTO, FighterBasicInfoDTO

from match import repositories as match_repo
from event import repositories as event_repo
from fighter import repositories as fighter_repo


async def get_event_matches(session: AsyncSession, event_name: str) -> Optional[EventMatchesDTO]:
    """
    특정 이벤트에 속한 모든 경기와 참가 파이터 정보를 조회합니다.
    """
    event = await event_repo.get_event_by_name(session, event_name)
    if not event:
        return None

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

async def get_match_detail(session: AsyncSession, match_id: int) -> Optional[Dict]:
    """
    특정 경기의 정보와 fighter들의 stat을 조회합니다.
    """
    pass

async def get_highest_stats_matches(session: AsyncSession, stat_name: str, limit: int = 10):
    """
    특정 스탯 기준 TOP 10 경기 조회
    """
    pass