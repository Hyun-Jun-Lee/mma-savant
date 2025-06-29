from typing import List

from fighter.models import FighterSchema, RankingSchema, FighterModel
from fighter import repositories as fighter_repo
from event.models import EventSchema
from match.models import MatchSchema, FighterMatchSchema, BasicMatchStatSchema, SigStrMatchStatSchema

async def save_fighters(session, fighters: List[FighterSchema]):
    result = []
    
    for fighter in fighters:
        if not fighter.name:
            continue
            
        # 기존 파이터 조회
        existing = fighter_repo.get_fighter_by_name(session, fighter.name)
        if existing:
            # 업데이트
            for key, value in fighter.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                setattr(existing, key, value)
            result.append(existing)
        else:
            # 새로 생성
            new_fighter = FighterModel.from_schema(fighter)
            session.add(new_fighter)
            result.append(new_fighter)
    
    session.commit()
    return [f.to_schema() for f in result]

async def save_events(session, events: List[EventSchema]):
    pass

async def save_match(session, match: MatchSchema) -> MatchSchema:
    pass

async def save_fighter_match(session, fighter_match: FighterMatchSchema) -> FighterMatchSchema:
    pass

async def save_basic_match_stat(session, basic_match_stat: BasicMatchStatSchema) -> BasicMatchStatSchema:
    pass

async def save_sig_str_match_stat(session, sig_str_match_stat: SigStrMatchStatSchema) -> SigStrMatchStatSchema:
    pass

async def save_rankings(session, rankings: List[RankingSchema]):
    pass