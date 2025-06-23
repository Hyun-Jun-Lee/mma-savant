from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from common.models import WeightClassSchema
from fighter.repositories import (
    get_fighter_by_id,
    get_fighter_by_name,
    get_ranking_by_fighter_id,
    get_fighters_by_weight_class_ranking,
)

async def search_fighter_by_name(session: AsyncSession, name: str) -> Optional[Dict]:
    """
    fighter_name로 fighter 조회.
    """
    fighter = await get_fighter_by_name(session, name)
    if not fighter:
        return None
    rankings = await get_ranking_by_fighter_id(session, fighter.id)

    ranking_result = {}
    for ranking_obj in rankings:
        weight_class_id = ranking_obj.weight_class_id
        weight_class_name = WeightClassSchema.get_name_by_id(weight_class_id)
        ranking_result[weight_class_name] = ranking_obj.ranking

    return {
        "fighter": fighter,
        "ranking": ranking_result
    }

async def search_fighter_by_nickname(session: AsyncSession, nickname: str) -> Optional[Dict]:
    """
    fighter_nickname로 fighter 조회.
    """
    fighter = await get_fighter_by_nickname(session, nickname)
    if not fighter:
        return None
    rankings = await get_ranking_by_fighter_id(session, fighter.id)

    ranking_result = {}
    for ranking_obj in rankings:
        weight_class_id = ranking_obj.weight_class_id
        weight_class_name = WeightClassSchema.get_name_by_id(weight_class_id)
        ranking_result[weight_class_name] = ranking_obj.ranking

    return {
        "fighter": fighter,
        "ranking": ranking_result
    }

async def get_fighter_info(session: AsyncSession, fighter_id: int) -> Optional[Dict]:
    """
    특정 선수의 기본 정보와 랭킹을 조회합니다.
    """
    fighter = await get_fighter_by_id(session, fighter_id)
    if not fighter:
        return None

    ranking_result = {}
    rankings = await get_ranking_by_fighter_id(session, fighter_id)
    for ranking_obj in rankings:
        weight_class_id = ranking_obj.weight_class_id
        weight_class_name = WeightClassSchema.get_name_by_id(weight_class_id)
        ranking_result[weight_class_name] = ranking_obj.ranking

    return {
        "fighter": fighter,
        "ranking": ranking_result,
    }

async def get_fighter_by_ranking(session: AsyncSession, weight_class_id: int) -> List[Dict[int,Dict]]:
    """
    특정 체급에 소속된 랭킹 있는 파이터들을 랭킹 순으로 조회
    """
    fighters = await get_fighters_by_weight_class_ranking(session, weight_class_id)
    return fighters