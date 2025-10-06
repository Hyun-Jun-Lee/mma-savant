from typing import List

from sqlalchemy import select

from common.utils import normalize_name
from fighter.models import FighterSchema, RankingSchema, FighterModel, RankingModel
from event.models import EventSchema, EventModel
from match.models import (
    MatchSchema, 
    FighterMatchSchema, 
    BasicMatchStatSchema, 
    SigStrMatchStatSchema, 
    MatchModel,
    FighterMatchModel,
    BasicMatchStatModel,
    SigStrMatchStatModel
)

async def save_fighters(session, fighters: List[FighterSchema]):
    
    for fighter in fighters:
        if not fighter.name:
            continue

        fighter_name = normalize_name(fighter.name)
            
        # 기존 파이터 조회 (Pydantic 스키마 반환)
        existing_model_query = await session.execute(
            select(FighterModel).where(FighterModel.name == fighter_name)
        )
        existing_model = existing_model_query.scalar_one_or_none()
        
        if existing_model:            
            # 업데이트
            for key, value in fighter.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                setattr(existing_model, key, value)
        else:
            # 새로 생성
            new_fighter = FighterModel.from_schema(fighter)
            session.add(new_fighter)
    
    await session.commit()

async def save_events(session, events: List[EventSchema]):
    
    for event in events:
        if not event.name:
            continue

            
        # 기존 이벤트 조회 (Pydantic 스키마 반환)
        existing_model_query = await session.execute(
            select(EventModel).where(EventModel.url == event.url)
        )
        existing_model = existing_model_query.scalar_one_or_none()
        
        if existing_model:            
            # 업데이트
            for key, value in event.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                setattr(existing_model, key, value)
        else:
            # 새로 생성
            new_event = EventModel.from_schema(event)
            session.add(new_event)
    
    await session.commit()

async def save_match(session, match: MatchSchema) -> MatchSchema:
    existing_model_query = await session.execute(
        select(MatchModel).where(MatchModel.detail_url == match.detail_url)
    )
    existing_model = existing_model_query.scalar_one_or_none()

    if existing_model:
        # 업데이트
        for key, value in match.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
            setattr(existing_model, key, value)
        return_model = existing_model
    else:
        # 새로 생성
        new_match = MatchModel.from_schema(match)
        session.add(new_match)
        return_model = new_match

    await session.commit()
    await session.refresh(return_model)
    return return_model.to_schema()
    

async def save_fighter_match(session, fighter_id: int, match_id: int, result: str) -> FighterMatchSchema:
    existing_model_query = await session.execute(
        select(FighterMatchModel).where(FighterMatchModel.fighter_id == fighter_id, FighterMatchModel.match_id == match_id)
    )
    existing_model = existing_model_query.scalar_one_or_none()

    if existing_model:
        # 업데이트
        existing_model.result = result
        return_model = existing_model
    else:
        # 새로 생성
        new_match = FighterMatchModel(
            fighter_id=fighter_id,
            match_id=match_id,
            result=result
        )
        session.add(new_match)
        return_model = new_match

    await session.commit()
    await session.refresh(return_model)
    return return_model.to_schema()

async def save_basic_match_stat(session, basic_match_stat_list: List[BasicMatchStatSchema]):
    for basic_match_stat in basic_match_stat_list:
        existing_stats = await session.execute(
            select(BasicMatchStatModel)
            .where(
                BasicMatchStatModel.fighter_match_id == basic_match_stat.fighter_match_id,
                BasicMatchStatModel.round == basic_match_stat.round
            )
        )
        existing_stats = existing_stats.scalar_one_or_none()
        
        if existing_stats:            
            # 업데이트
            for key, value in basic_match_stat.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                setattr(existing_stats, key, value)
        else:
            # 새로 생성
            new_stats = BasicMatchStatModel.from_schema(basic_match_stat)
            session.add(new_stats)
    
    await session.commit()

async def save_sig_str_match_stat(session, sig_str_match_stat_list: List[SigStrMatchStatSchema]):
    for sig_str_match_stat in sig_str_match_stat_list:
        existing_stats = await session.execute(
            select(SigStrMatchStatModel)
            .where(
                SigStrMatchStatModel.fighter_match_id == sig_str_match_stat.fighter_match_id,
                SigStrMatchStatModel.round == sig_str_match_stat.round
            )
        )
        existing_stats = existing_stats.scalar_one_or_none()
        
        if existing_stats:            
            # 업데이트
            for key, value in sig_str_match_stat.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                setattr(existing_stats, key, value)
        else:
            # 새로 생성
            new_stats = SigStrMatchStatModel.from_schema(sig_str_match_stat)
            session.add(new_stats)
    
    await session.commit()

async def save_rankings(session, rankings: List[RankingSchema]):
    for ranking in rankings:
        new_stats = RankingModel.from_schema(ranking)
        session.add(new_stats)
    
    await session.commit()