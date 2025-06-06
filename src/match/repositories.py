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

async def get_matches_between_fighters(
    session: AsyncSession, fighter_id_1: int, fighter_id_2: int
) -> List[MatchSchema]:
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

async def get_fighters_matches(session: AsyncSession, fighter_id: int, limit: int = 10) -> List[FighterMatchSchema]:
    result = await session.execute(
        select(MatchModel)
        .join(FighterMatchModel)
        .where(FighterMatchModel.fighter_id == fighter_id)
        .order_by(MatchModel.created_at.desc())
        .limit(limit)
        .options(selectinload(MatchModel.event), selectinload(MatchModel.weight_class))
    )
    fighters_matches = result.scalars().all()
    return [fm.to_schema() for fm in fighters_matches]

async def get_basic_match_stats(
    session: AsyncSession, fighter_id: int, match_id: int
) -> Optional[BasicMatchStatSchema]:
    """
    fighter_id와 match_id를 통해 해당 파이터의 기본 경기 통계 조회
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
    fighter_id와 match_id를 통해 해당 파이터의 유효 타격 통계 조회
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

