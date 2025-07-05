from typing import Optional, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from common.models import WeightClassSchema
from fighter.dto import FighterWithRankingsDTO, WeightClassRankingsDTO, RankedFighterDTO
from fighter.models import FighterSchema
from fighter import repositories as fighter_repo
from fighter import exceptions as fighter_exc

async def _build_fighter_with_rankings(session: AsyncSession, fighter: FighterSchema) -> Optional[FighterWithRankingsDTO]:
    rankings = await fighter_repo.get_ranking_by_fighter_id(session, fighter.id)
    
    ranking_result = {}
    for ranking_obj in rankings:
        weight_class_name = WeightClassSchema.get_name_by_id(ranking_obj.weight_class_id)
        if weight_class_name:  # None 값 체크
            ranking_result[weight_class_name] = ranking_obj.ranking
    
    return FighterWithRankingsDTO(
        fighter=fighter,
        rankings=ranking_result
    )

async def get_fighter_by_id(session: AsyncSession, fighter_id: int) -> Optional[FighterWithRankingsDTO]:
    """
    fighter_id로 fighter 조회.
    """
    fighter = await fighter_repo.get_fighter_by_id(session, fighter_id)
    if not fighter:
        raise fighter_exc.FighterNotFoundError(str(fighter_id))

    return await _build_fighter_with_rankings(session, fighter)
    

async def get_fighter_by_name(session: AsyncSession, name: str) -> Optional[FighterWithRankingsDTO]:
    """
    fighter_name로 fighter 조회.
    """
    fighter = await fighter_repo.get_fighter_by_name(session, name)
    if not fighter:
        raise fighter_exc.FighterNotFoundError(name)
    return await _build_fighter_with_rankings(session, fighter)

async def get_fighter_by_nickname(session: AsyncSession, nickname: str) -> Optional[FighterWithRankingsDTO]:
    """
    fighter_nickname로 fighter 조회.
    """
    fighter = await fighter_repo.get_fighter_by_nickname(session, nickname)
    if not fighter:
        raise fighter_exc.FighterNotFoundError(nickname)
    
    return await _build_fighter_with_rankings(session, fighter)

async def get_fighter_ranking_by_weight_class(session: AsyncSession, weight_class_name: str) -> WeightClassRankingsDTO:
    """
    특정 체급에 소속된 랭킹 있는 파이터들을 랭킹 순으로 조회
    """
    weight_class_id = WeightClassSchema.get_id_by_name(weight_class_name)
    if not weight_class_id:
        raise fighter_exc.InvalidWeightClassError(weight_class_name)
        
    fighters = await fighter_repo.get_fighters_by_weight_class_ranking(session, weight_class_id)
    
    ranked_fighters = []
    for index, fighter in enumerate(fighters):
        ranked_fighters.append(
            RankedFighterDTO(
                ranking=index + 1,
                fighter=fighter
            )
        )
    
    ranked_fighters.sort(key=lambda x: x.ranking)
    
    return WeightClassRankingsDTO(
        weight_class_name=weight_class_name,
        rankings=ranked_fighters,
    )

async def get_top_fighters_by_record(session: AsyncSession, record: Literal["win", "loss", "draw"], weight_class_id: int = None, limit: int = 10) -> WeightClassRankingsDTO:
    """
    파이터의 기록(승,패,무) 기준으로 상위 limit개의 파이터 조회
    """
    fighter_with_rank = await fighter_repo.get_top_fighter_by_record(session, record, weight_class_id, limit)
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
    