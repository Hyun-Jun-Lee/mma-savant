from typing import List, Optional, Dict, Literal

from sqlalchemy import select, delete, func, and_, or_
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
        select(FighterModel).where(FighterModel.name.ilike(f'%{normalized_name}%'))
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

async def get_fighters_by_stance(session: AsyncSession, stance: str) -> List[FighterSchema]:
    """
    특정 스탠스의 파이터들을 조회합니다.
    """
    result = await session.execute(
        select(FighterModel)
        .where(FighterModel.stance.ilike(stance))
        .order_by(FighterModel.wins.desc())
    )
    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]

async def get_fighters_by_record_range(
    session: AsyncSession, 
    min_wins: Optional[int] = None,
    max_losses: Optional[int] = None,
    min_total_fights: Optional[int] = None,
    limit: int = 20
) -> List[FighterSchema]:
    """
    전적 조건에 따라 파이터들을 조회합니다.
    """
    query = select(FighterModel)
    conditions = []
    
    if min_wins is not None:
        conditions.append(FighterModel.wins >= min_wins)
    
    if max_losses is not None:
        conditions.append(FighterModel.losses <= max_losses)
        
    if min_total_fights is not None:
        conditions.append(
            (FighterModel.wins + FighterModel.losses + FighterModel.draws) >= min_total_fights
        )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(FighterModel.wins.desc()).limit(limit)
    
    result = await session.execute(query)
    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]

async def get_undefeated_fighters(session: AsyncSession, min_wins: int = 5) -> List[FighterSchema]:
    """
    무패 파이터들을 조회합니다.
    """
    result = await session.execute(
        select(FighterModel)
        .where(
            and_(
                FighterModel.losses == 0,
                FighterModel.wins >= min_wins
            )
        )
        .order_by(FighterModel.wins.desc())
    )
    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]

async def get_fighters_by_physical_stats(
    session: AsyncSession,
    min_height: Optional[float] = None,
    max_height: Optional[float] = None, 
    min_weight: Optional[float] = None,
    max_weight: Optional[float] = None,
    min_reach: Optional[float] = None,
    limit: int = 20
) -> List[FighterSchema]:
    """
    신체 조건에 따라 파이터들을 조회합니다.
    """
    query = select(FighterModel)
    conditions = []
    
    if min_height is not None:
        conditions.append(FighterModel.height >= min_height)
    if max_height is not None:
        conditions.append(FighterModel.height <= max_height)
    if min_weight is not None:
        conditions.append(FighterModel.weight >= min_weight)
    if max_weight is not None:
        conditions.append(FighterModel.weight <= max_weight)
    if min_reach is not None:
        conditions.append(FighterModel.reach >= min_reach)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(FighterModel.wins.desc()).limit(limit)
    
    result = await session.execute(query)
    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]

async def get_fighter_count_by_weight_class(session: AsyncSession, weight_class_id: int) -> int:
    """
    특정 체급에 랭킹된 파이터 수를 반환합니다.
    """
    result = await session.execute(
        select(func.count(FighterModel.id))
        .join(RankingModel, FighterModel.id == RankingModel.fighter_id)
        .where(RankingModel.weight_class_id == weight_class_id)
    )
    return result.scalar() or 0

async def get_fighters_statistics(session: AsyncSession) -> Dict:
    """
    전체 파이터들의 통계 정보를 반환합니다.
    """
    result = await session.execute(
        select(
            func.count(FighterModel.id).label("total_fighters"),
            func.count().filter(FighterModel.belt == True).label("champions"),
            func.avg(FighterModel.wins).label("avg_wins"),
            func.avg(FighterModel.losses).label("avg_losses"),
            func.avg(FighterModel.height).label("avg_height"),
            func.avg(FighterModel.weight).label("avg_weight"),
            func.max(FighterModel.wins).label("max_wins"),
            func.max(FighterModel.losses).label("max_losses")
        )
    )
    
    stats = result.mappings().one()
    return {
        "total_fighters": stats["total_fighters"] or 0,
        "champions": stats["champions"] or 0,
        "avg_wins": float(stats["avg_wins"]) if stats["avg_wins"] else 0.0,
        "avg_losses": float(stats["avg_losses"]) if stats["avg_losses"] else 0.0,
        "avg_height": float(stats["avg_height"]) if stats["avg_height"] else 0.0,
        "avg_weight": float(stats["avg_weight"]) if stats["avg_weight"] else 0.0,
        "max_wins": stats["max_wins"] or 0,
        "max_losses": stats["max_losses"] or 0
    }

async def get_fighters_by_win_percentage(
    session: AsyncSession, 
    min_fights: int = 5, 
    limit: int = 10
) -> List[Dict]:
    """
    승률이 높은 파이터들을 조회합니다.
    """
    # 승률 계산: wins / (wins + losses + draws)
    total_fights = FighterModel.wins + FighterModel.losses + FighterModel.draws
    win_percentage = func.cast(FighterModel.wins, func.Float) / func.cast(total_fights, func.Float) * 100
    
    result = await session.execute(
        select(
            FighterModel,
            win_percentage.label("win_percentage")
        )
        .where(total_fights >= min_fights)
        .order_by(win_percentage.desc())
        .limit(limit)
    )
    
    rows = result.all()
    return [
        {
            "fighter": fighter.to_schema(),
            "win_percentage": round(float(percentage), 2),
            "total_fights": fighter.wins + fighter.losses + fighter.draws
        }
        for fighter, percentage in rows
    ]

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

async def get_fighters_by_experience_level(
    session: AsyncSession,
    experience_level: Literal["rookie", "veteran", "legend"],
    limit: int = 20
) -> List[FighterSchema]:
    """
    경험 수준별로 파이터들을 조회합니다.
    rookie: 총 경기 수 1-10
    veteran: 총 경기 수 11-25
    legend: 총 경기 수 26+
    """
    total_fights = FighterModel.wins + FighterModel.losses + FighterModel.draws
    
    if experience_level == "rookie":
        condition = and_(total_fights >= 1, total_fights <= 10)
    elif experience_level == "veteran":
        condition = and_(total_fights >= 11, total_fights <= 25)
    elif experience_level == "legend":
        condition = total_fights >= 26
    else:
        return []
    
    result = await session.execute(
        select(FighterModel)
        .where(condition)
        .order_by(FighterModel.wins.desc())
        .limit(limit)
    )
    
    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]