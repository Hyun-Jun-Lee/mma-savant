from typing import List, Optional, Dict, Literal

from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from fighter.models import FighterModel, RankingModel, FighterSchema, RankingSchema
from common.utils import normalize_name

async def get_all_fighter(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 10
) -> List[FighterSchema]:
    """
    모든 파이터를 페이지네이션하여 조회합니다.

    Args:
        session: 데이터베이스 세션
        page: 페이지 번호 (1부터 시작, 기본값 1)
        page_size: 페이지당 항목 수 (기본값 10)
    """
    offset = (page - 1) * page_size
    result = await session.execute(
        select(FighterModel)
        .offset(offset)
        .limit(page_size)
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

async def get_fighter_by_name_best_record(session: AsyncSession, name: str) -> Optional[FighterSchema]:
    """
    이름 또는 닉네임으로 파이터를 검색합니다.
    동명이인이 있을 경우 전적(승수)이 가장 좋은 선수를 반환.
    """
    normalized_name = normalize_name(name)

    # 이름 또는 닉네임으로 검색하고 승수 기준 정렬
    result = await session.execute(
        select(FighterModel)
        .where(
            or_(
                FighterModel.name.ilike(f'%{normalized_name}%'),
                FighterModel.nickname.ilike(f'%{normalized_name}%')
            )
        )
        .order_by(FighterModel.wins.desc())
    )
    fighter_model = result.scalars().first()

    return fighter_model.to_schema() if fighter_model else None

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

async def search_fighters_by_name(session: AsyncSession, search_term: str, limit: int = 10) -> List[FighterSchema]:
    """
    이름이나 닉네임으로 파이터를 검색합니다. (부분 매칭)
    """
    normalized_search = normalize_name(search_term)
    result = await session.execute(
        select(FighterModel)
        .where(
            or_(
                FighterModel.name.ilike(f'%{normalized_search}%'),
                FighterModel.nickname.ilike(f'%{normalized_search}%')
            )
        )
        .limit(limit)
    )
    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]

async def get_champions(session: AsyncSession) -> List[FighterSchema]:
    """
    현재 벨트를 보유한 모든 챔피언 파이터들을 조회합니다.
    """
    result = await session.execute(
        select(FighterModel)
        .where(FighterModel.belt == True)
        .order_by(FighterModel.name)
    )
    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]

async def get_ranked_fighters_by_weight_class(
    session: AsyncSession, 
    weight_class_id: int, 
    limit: int = 15
    ) -> List[Dict]:
    """
    특정 체급의 랭킹된 파이터들을 랭킹 순으로 조회합니다.
    """
    result = await session.execute(
        select(FighterModel, RankingModel.ranking)
        .join(RankingModel, FighterModel.id == RankingModel.fighter_id)
        .where(RankingModel.weight_class_id == weight_class_id)
        .order_by(RankingModel.ranking)
        .limit(limit)
    )
    
    rows = result.all()
    return [
        {
            "fighter": fighter.to_schema(),
            "ranking": ranking,
            "weight_class_id": weight_class_id
        }
        for fighter, ranking in rows
    ]