from typing import List, Optional, Dict, Literal

from sqlalchemy import select, delete, or_, text
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from fighter.models import FighterModel, RankingModel, FighterSchema, RankingSchema
from match.models import FighterMatchModel, MatchModel, BasicMatchStatModel, SigStrMatchStatModel
from event.models import EventModel
from common.utils import normalize_name

async def get_all_fighter(
    session: AsyncSession,
    page: int = 1,
    page_size: Optional[int] = 10
) -> List[FighterSchema]:
    """
    모든 파이터를 조회합니다.

    Args:
        session: 데이터베이스 세션
        page: 페이지 번호 (1부터 시작, 기본값 1)
        page_size: 페이지당 항목 수 (기본값 10, None이면 전체 조회)
    """
    query = select(FighterModel)

    if page_size is not None:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
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


# ===========================
# Fighter Detail queries
# ===========================

async def get_fight_history(session: AsyncSession, fighter_id: int) -> list[dict]:
    """
    파이터의 전체 경기 이력을 단일 쿼리로 조회합니다.
    상대 선수, 이벤트 정보를 JOIN으로 한번에 가져옵니다.
    """
    opp_fm = aliased(FighterMatchModel)
    opp_f = aliased(FighterModel)

    stmt = (
        select(
            FighterMatchModel.id.label("fighter_match_id"),
            FighterMatchModel.match_id,
            FighterMatchModel.result,
            MatchModel.method,
            MatchModel.result_round,
            MatchModel.time,
            MatchModel.is_main_event,
            MatchModel.weight_class_id,
            EventModel.id.label("event_id"),
            EventModel.name.label("event_name"),
            EventModel.event_date,
            opp_f.id.label("opponent_id"),
            opp_f.name.label("opponent_name"),
            opp_f.nationality.label("opponent_nationality"),
        )
        .join(MatchModel, MatchModel.id == FighterMatchModel.match_id)
        .outerjoin(EventModel, EventModel.id == MatchModel.event_id)
        .outerjoin(
            opp_fm,
            (opp_fm.match_id == FighterMatchModel.match_id) & (opp_fm.fighter_id != fighter_id),
        )
        .outerjoin(opp_f, opp_f.id == opp_fm.fighter_id)
        .where(FighterMatchModel.fighter_id == fighter_id)
        .order_by(EventModel.event_date.desc().nullslast())
    )

    result = await session.execute(stmt)
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def get_per_match_stats(session: AsyncSession, fighter_match_ids: list[int]) -> dict[int, dict]:
    """
    여러 fighter_match_id에 대한 경기별 스탯을 배치 조회합니다.
    round=0 (전체 합산) 행만 가져옵니다.
    """
    if not fighter_match_ids:
        return {}

    # basic stats 배치 조회
    basic_result = await session.execute(
        select(BasicMatchStatModel).where(
            BasicMatchStatModel.fighter_match_id.in_(fighter_match_ids),
            BasicMatchStatModel.round == 0,
        )
    )
    basic_rows = basic_result.scalars().all()

    # sig_str stats 배치 조회
    sig_str_result = await session.execute(
        select(SigStrMatchStatModel).where(
            SigStrMatchStatModel.fighter_match_id.in_(fighter_match_ids),
            SigStrMatchStatModel.round == 0,
        )
    )
    sig_str_rows = sig_str_result.scalars().all()

    # {fm_id: {"basic": ..., "sig_str": ...}} 조합
    stats_map: dict[int, dict] = {}
    for row in basic_rows:
        fm_id = row.fighter_match_id
        if fm_id not in stats_map:
            stats_map[fm_id] = {}
        stats_map[fm_id]["basic"] = row.to_schema()

    for row in sig_str_rows:
        fm_id = row.fighter_match_id
        if fm_id not in stats_map:
            stats_map[fm_id] = {}
        stats_map[fm_id]["sig_str"] = row.to_schema()

    return stats_map


async def get_finish_breakdown(session: AsyncSession, fighter_id: int) -> dict:
    """
    파이터의 승리 방법별 집계를 단일 쿼리로 조회합니다.
    """
    stmt = text("""
        SELECT
            COUNT(*) FILTER (WHERE m.method ILIKE '%%ko%%' OR m.method ILIKE '%%tko%%') AS ko_tko,
            COUNT(*) FILTER (WHERE m.method ILIKE '%%sub%%') AS submission,
            COUNT(*) FILTER (WHERE m.method ILIKE '%%dec%%') AS decision
        FROM fighter_match fm
        JOIN "match" m ON m.id = fm.match_id
        WHERE fm.fighter_id = :fighter_id AND LOWER(fm.result) = 'win'
    """)
    result = await session.execute(stmt, {"fighter_id": fighter_id})
    row = result.mappings().one()
    return {
        "ko_tko": row["ko_tko"] or 0,
        "submission": row["submission"] or 0,
        "decision": row["decision"] or 0,
    }


async def get_top_submission_technique(session: AsyncSession, fighter_id: int) -> Optional[str]:
    """
    파이터의 가장 많이 성공한 서브미션 기술을 반환합니다.
    """
    stmt = text("""
        SELECT
            REPLACE(m.method, 'SUB-', '') AS technique,
            COUNT(*) AS cnt
        FROM fighter_match fm
        JOIN "match" m ON m.id = fm.match_id
        WHERE fm.fighter_id = :fighter_id
          AND LOWER(fm.result) = 'win'
          AND m.method LIKE 'SUB-%%'
        GROUP BY m.method
        ORDER BY cnt DESC
        LIMIT 1
    """)
    result = await session.execute(stmt, {"fighter_id": fighter_id})
    row = result.mappings().one_or_none()
    return row["technique"] if row else None