from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from match.models import (
    MatchModel,
    FighterMatchModel,
    BasicMatchStatModel,
    SigStrMatchStatModel,
    MatchSchema,
    FighterMatchSchema,
    BasicMatchStatSchema,
    SigStrMatchStatSchema
)

################################
######### Match #########
################################

async def get_matches_by_event_id(
    session: AsyncSession, event_id: int
) -> List[MatchSchema]:
    """
    특정 이벤트에 속한 모든 경기를 조회합니다.
    """
    result = await session.execute(
        select(MatchModel)
        .where(MatchModel.event_id == event_id)
    )
    matches = result.scalars().all()
    return [match.to_schema() for match in matches]

async def get_matches_between_fighters(
    session: AsyncSession, fighter_id_1: int, fighter_id_2: int
) -> List[MatchSchema]:
    """
    두 선수 간의 모든 대결 경기를 조회합니다.
    """
    fm1 = aliased(FighterMatchModel)
    fm2 = aliased(FighterMatchModel)

    result = await session.execute(
        select(MatchModel)
        .join(fm1, fm1.match_id == MatchModel.id)
        .join(fm2, fm2.match_id == MatchModel.id)
        .where(
            fm1.fighter_id == fighter_id_1,
            fm2.fighter_id == fighter_id_2
        )
        .distinct()
    )

    matches = result.scalars().all()
    return [match.to_schema() for match in matches]

async def get_basic_match_stats(
    session: AsyncSession, fighter_id: int, match_id: int
) -> Optional[BasicMatchStatSchema]:
    """
    특정 경기에서 선수의 기본 통계(넉다운, 컨트롤 타임 등)를 조회합니다.
    """
    result = await session.execute(
        select(BasicMatchStatModel)
        .join(FighterMatchModel)
        .where(
            FighterMatchModel.fighter_id == fighter_id,
            FighterMatchModel.match_id == match_id,
            BasicMatchStatModel.fighter_match_id == FighterMatchModel.id
        )
    )
    basic_match_stat = result.scalar_one_or_none()
    return basic_match_stat.to_schema() if basic_match_stat else None


async def get_sig_str_match_stats(
    session: AsyncSession, fighter_id: int, match_id: int
) -> Optional[SigStrMatchStatSchema]:
    """
    특정 경기에서 선수의 유효 타격 통계(헤드샷, 바디샷 등)를 조회합니다.
    """
    result = await session.execute(
        select(SigStrMatchStatModel)
        .join(FighterMatchModel)
        .where(
            FighterMatchModel.fighter_id == fighter_id,
            FighterMatchModel.match_id == match_id,
            SigStrMatchStatModel.fighter_match_id == FighterMatchModel.id
        )
    )
    sig_str_match_stat = result.scalar_one_or_none()
    return sig_str_match_stat.to_schema() if sig_str_match_stat else None

################################
######### FighterMatch #########
################################

async def get_fighters_matches(session: AsyncSession, fighter_id: int, limit: int = 10) -> List[FighterMatchSchema]:
    """
    특정 선수의 경기 기록을 최신순으로 조회합니다.
    """
    result = await session.execute(
        select(FighterMatchModel)
        .where(FighterMatchModel.fighter_id == fighter_id)
        .order_by(FighterMatchModel.created_at.desc())
        .limit(limit)
    )
    fighter_matches = result.scalars().all()
    return [fm.to_schema() for fm in fighter_matches]


async def get_fighter_match_by_match_id(
    session: AsyncSession, match_id: int
) -> List[FighterMatchSchema]:
    """
    특정 경기에 참여한 모든 선수의 기록을 조회합니다.
    """
    result = await session.execute(
        select(FighterMatchModel)
        .where(FighterMatchModel.match_id == match_id)
    )
    fighter_matches = result.scalars().all()
    return [fighter_match.to_schema() for fighter_match in fighter_matches]