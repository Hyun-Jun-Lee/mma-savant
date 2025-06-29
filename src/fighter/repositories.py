from typing import List, Optional, Dict, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fighter.models import FighterModel, RankingModel, FighterSchema, RankingSchema
from common.utils import normalize_name

async def get_all_fighter(session: AsyncSession) -> List[FighterSchema]:
    result = await session.execute(
        select(FighterModel)
    )
    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]

async def get_fighter_by_id(session: AsyncSession, fighter_id: int) -> Optional[FighterSchema]:
    """
    fighter_id로 fighter 조회.
    """
    result = await session.execute(
        select(FighterModel).where(FighterModel.id == fighter_id)
    )
    fighter = result.scalar_one_or_none()
    return fighter.to_schema() if fighter else None

async def get_fighter_by_name(session: AsyncSession, name: str) -> Optional[FighterSchema]:
    """
    fighter_name로 fighter 조회.
    """
    normalized_name = normalize_name(name)
    result = await session.execute(
        select(FighterModel).where(FighterModel.name == normalized_name)
    )
    fighter = result.scalar_one_or_none()
    return fighter.to_schema() if fighter else None

async def get_fighter_by_nickname(session: AsyncSession, nickname: str) -> Optional[FighterSchema]:
    """
    fighter_nickname로 fighter 조회.
    """
    normalized_nickname = normalize_name(nickname)
    result = await session.execute(
        select(FighterModel).where(FighterModel.nickname == normalized_nickname)
    )
    fighter = result.scalar_one_or_none()
    return fighter.to_schema() if fighter else None

async def get_ranking_by_fighter_id(session: AsyncSession, fighter_id: int) -> List[RankingSchema]:
    """
    fighter_id로 해당 선수의 모든 랭킹을 조회합니다.
    동일한 선수가 여러 체급에서 랭킹을 보유하고 있을 수 있습니다.
    """
    result = await session.execute(
        select(RankingModel).where(RankingModel.fighter_id == fighter_id)
    )
    rankings = result.scalars().all()
    return [ranking.to_schema() for ranking in rankings]

async def get_fighters_by_weight_class_ranking(session: AsyncSession, weight_class_id: int) -> List[FighterSchema]:
    """
    특정 체급에 소속된 랭킹 있는 파이터들을 랭킹 순으로 조회
    """
    result = await session.execute(
        select(FighterModel)
        .join(RankingModel, FighterModel.id == RankingModel.fighter_id)
        .where(RankingModel.weight_class_id == weight_class_id)
        .order_by(RankingModel.ranking)
    )
    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]

async def get_top_fighter_by_record(session: AsyncSession, record: Literal["win", "loss", "draw"], weight_class_id: Optional[int] = None, limit: int = 10) -> List[Dict[int, FighterSchema]]:
    """
    파이터의 승,패,무 기준 상위 선수들 조회
    """
    # record에 따른 정렬 기준 설정
    if record == "win":
        order_by_clause = FighterModel.wins.desc()
        record_field = FighterModel.wins
    elif record == "loss":
        order_by_clause = FighterModel.losses.desc()
        record_field = FighterModel.losses
    elif record == "draw":
        order_by_clause = FighterModel.draws.desc()
        record_field = FighterModel.draws
    else:
        return []
    
    # 쿼리 빌드 - record 값도 함께 조회
    query = select(FighterModel, record_field).order_by(order_by_clause)
    
    # 체급 필터링이 있으면 적용
    if weight_class_id is not None:
        # 체급 테이블과 조인하여 해당 체급의 파이터만 필터링
        query = query.join(RankingModel, FighterModel.id == RankingModel.fighter_id)\
                   .filter(RankingModel.weight_class_id == weight_class_id)
    
    query = query.limit(limit)
    
    result = await session.execute(query)
    rows = result.all()
    
    return [{"ranking": idx + 1, "fighter": fighter.to_schema()} for idx, (fighter, _) in enumerate(rows)]

async def delete_all_rankings(session: AsyncSession) -> None:
    await session.execute(delete(RankingModel))
    await session.commit()