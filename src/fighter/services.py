from typing import Optional, List, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from common.models import WeightClassSchema
from fighter.dto import FighterWithRankingsDTO, WeightClassRankingsDTO, RankedFighterDTO
from fighter.models import FighterSchema
from fighter.repositories import (
    get_fighter_by_id,
    get_fighter_by_name,
    get_ranking_by_fighter_id,
    get_fighters_by_weight_class_ranking,
    get_top_fighter_by_record
)

async def _get_fighter_by_id(session: AsyncSession, fighter_id: int) -> Optional[FighterSchema]:
    fighter = await get_fighter_by_id(session, fighter_id)
    if not fighter:
        return None
    return fighter

async def _build_fighter_with_rankings(session: AsyncSession, fighter: FighterSchema) -> Optional[FighterWithRankingsDTO]:
    rankings = await get_ranking_by_fighter_id(session, fighter.id)
    
    # 랭킹 데이터 변환
    ranking_result = {}
    for ranking_obj in rankings:
        weight_class_name = WeightClassSchema.get_name_by_id(ranking_obj.weight_class_id)
        ranking_result[weight_class_name] = ranking_obj.ranking
    
    return FighterWithRankingsDTO(
        fighter=fighter,
        rankings=ranking_result
    )

async def get_fighter_by_id(session: AsyncSession, fighter_id: int) -> Optional[FighterWithRankingsDTO]:
    """
    fighter_id로 fighter 조회.
    """
    fighter = await _get_fighter_by_id(session, fighter_id)
    if not fighter:
        raise ValueError(f"Fighter not found: {fighter_id}")

    return await _build_fighter_with_rankings(session, fighter)
    

async def get_fighter_by_name(session: AsyncSession, name: str) -> Optional[FighterWithRankingsDTO]:
    """
    fighter_name로 fighter 조회.
    """
    fighter = await get_fighter_by_name(session, name)
    if not fighter:
        raise ValueError(f"Fighter not found: {name}")
    return await _build_fighter_with_rankings(session, fighter)

async def get_fighter_by_nickname(session: AsyncSession, nickname: str) -> Optional[FighterWithRankingsDTO]:
    """
    fighter_nickname로 fighter 조회.
    """
    fighter = await get_fighter_by_nickname(session, nickname)
    if not fighter:
        raise ValueError(f"Fighter not found: {nickname}")
    
    return await _build_fighter_with_rankings(session, fighter)

async def get_fighter_ranking_by_weight_class(session: AsyncSession, weight_class_name: str) -> WeightClassRankingsDTO:
    """
    특정 체급에 소속된 랭킹 있는 파이터들을 랭킹 순으로 조회
    """
    # 이름으로부터 ID 가져오기
    weight_class_id = WeightClassSchema.get_id_by_name(weight_class_name)
    if not weight_class_id:
        raise ValueError(f"Unknown weight class: {weight_class_name}")
        
    # Repository에서 랭킹 데이터 조회
    fighters = await get_fighters_by_weight_class_ranking(session, weight_class_id)
    
    # 랭킹과 파이터 정보를 결합한 DTO 생성
    ranked_fighters = []
    for index, fighter in enumerate(fighters):
        ranked_fighters.append(
            RankedFighterDTO(
                ranking=index + 1,
                fighter=fighter
            )
        )
    
    # 랭킹 순으로 정렬
    ranked_fighters.sort(key=lambda x: x.ranking)
    
    return WeightClassRankingsDTO(
        weight_class_name=weight_class_name,
        rankings=ranked_fighters,
    )

async def get_top_fighters_by_record(session: AsyncSession, record: Literal["win", "loss", "draw"], weight_class_id: int = None, limit: int = 10) -> List[RankedFighterDTO]:
    """
    파이터의 기록(승,패,무) 기준으로 상위 limit개의 파이터 조회
    """
    fighter_with_rank = await get_top_fighter_by_record(session, record, weight_class_id, limit)
    ranked_fighters = []
    
    weight_class_name = None
    if weight_class_id:
        weight_class_name = WeightClassSchema.get_name_by_id(weight_class_id)
    
    for rank_dict in fighter_with_rank:
        ranked_fighter = RankedFighterDTO(
            ranking=rank_dict["ranking"],
            fighter=rank_dict["fighter"],  
        )
        ranked_fighters.append(ranked_fighter)
    
    return WeightClassRankingsDTO(
        weight_class_name=weight_class_name,
        rankings=ranked_fighters,
    )
    