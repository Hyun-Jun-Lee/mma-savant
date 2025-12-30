from typing import List, Optional, Dict

from sqlalchemy import select, func
from sqlalchemy.orm import aliased
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
from match.dto import (
    FighterResultDTO,
    MatchWithFightersDTO,
    MatchWithResultDTO,
    FighterMatchStatDTO,
    CombinedMatchStatsDTO,
    MatchStatisticsDTO,
    FighterBasicStatsAggregateDTO,
    FighterSigStrStatsAggregateDTO
)
from fighter.repositories import get_fighter_by_id

################################
######### Match #########
################################

async def get_match_by_id(session: AsyncSession, match_id: int) -> Optional[MatchSchema]:
    result = await session.execute(
        select(MatchModel)
        .where(MatchModel.id == match_id)
    )
    match = result.scalar_one_or_none()
    return match.to_schema() if match else None

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

async def get_fighter_basic_stats_aggregate(session: AsyncSession, fighter_id: int) -> FighterBasicStatsAggregateDTO:
    """
    특정 선수의 기본 통계 데이터를 데이터베이스 레벨에서 집계하여 가져옵니다.
    """
    result = await session.execute(
        select(
            func.sum(BasicMatchStatModel.knockdowns).label("knockdowns"),
            func.sum(BasicMatchStatModel.control_time_seconds).label("control_time_seconds"),
            func.sum(BasicMatchStatModel.submission_attempts).label("submission_attempts"),
            func.sum(BasicMatchStatModel.sig_str_landed).label("sig_str_landed"),
            func.sum(BasicMatchStatModel.sig_str_attempted).label("sig_str_attempted"),
            func.sum(BasicMatchStatModel.total_str_landed).label("total_str_landed"),
            func.sum(BasicMatchStatModel.total_str_attempted).label("total_str_attempted"),
            func.sum(BasicMatchStatModel.td_landed).label("td_landed"),
            func.sum(BasicMatchStatModel.td_attempted).label("td_attempted"),
            func.count().label("match_count")
        )
        .join(FighterMatchModel)
        .where(FighterMatchModel.fighter_id == fighter_id)
    )

    stats = result.mappings().one_or_none()
    if stats:
        return FighterBasicStatsAggregateDTO(
            knockdowns=stats["knockdowns"] or 0,
            control_time_seconds=stats["control_time_seconds"] or 0,
            submission_attempts=stats["submission_attempts"] or 0,
            sig_str_landed=stats["sig_str_landed"] or 0,
            sig_str_attempted=stats["sig_str_attempted"] or 0,
            total_str_landed=stats["total_str_landed"] or 0,
            total_str_attempted=stats["total_str_attempted"] or 0,
            td_landed=stats["td_landed"] or 0,
            td_attempted=stats["td_attempted"] or 0,
            match_count=stats["match_count"] or 0
        )
    return FighterBasicStatsAggregateDTO()

async def get_fighter_sig_str_stats_aggregate(session: AsyncSession, fighter_id: int) -> FighterSigStrStatsAggregateDTO:
    """
    특정 선수의 유효 타격 통계 데이터를 데이터베이스 레벨에서 집계하여 가져옵니다.
    """
    result = await session.execute(
        select(
            func.sum(SigStrMatchStatModel.head_strikes_landed).label("head_strikes_landed"),
            func.sum(SigStrMatchStatModel.head_strikes_attempts).label("head_strikes_attempts"),
            func.sum(SigStrMatchStatModel.body_strikes_landed).label("body_strikes_landed"),
            func.sum(SigStrMatchStatModel.body_strikes_attempts).label("body_strikes_attempts"),
            func.sum(SigStrMatchStatModel.leg_strikes_landed).label("leg_strikes_landed"),
            func.sum(SigStrMatchStatModel.leg_strikes_attempts).label("leg_strikes_attempts"),
            func.sum(SigStrMatchStatModel.takedowns_landed).label("takedowns_landed"),
            func.sum(SigStrMatchStatModel.takedowns_attempts).label("takedowns_attempts"),
            func.sum(SigStrMatchStatModel.clinch_strikes_landed).label("clinch_strikes_landed"),
            func.sum(SigStrMatchStatModel.clinch_strikes_attempts).label("clinch_strikes_attempts"),
            func.sum(SigStrMatchStatModel.ground_strikes_landed).label("ground_strikes_landed"),
            func.sum(SigStrMatchStatModel.ground_strikes_attempts).label("ground_strikes_attempts"),
            func.count().label("match_count")
        )
        .join(FighterMatchModel)
        .where(FighterMatchModel.fighter_id == fighter_id)
    )

    stats = result.mappings().one_or_none()
    if stats:
        return FighterSigStrStatsAggregateDTO(
            head_strikes_landed=stats["head_strikes_landed"] or 0,
            head_strikes_attempts=stats["head_strikes_attempts"] or 0,
            body_strikes_landed=stats["body_strikes_landed"] or 0,
            body_strikes_attempts=stats["body_strikes_attempts"] or 0,
            leg_strikes_landed=stats["leg_strikes_landed"] or 0,
            leg_strikes_attempts=stats["leg_strikes_attempts"] or 0,
            takedowns_landed=stats["takedowns_landed"] or 0,
            takedowns_attempts=stats["takedowns_attempts"] or 0,
            clinch_strikes_landed=stats["clinch_strikes_landed"] or 0,
            clinch_strikes_attempts=stats["clinch_strikes_attempts"] or 0,
            ground_strikes_landed=stats["ground_strikes_landed"] or 0,
            ground_strikes_attempts=stats["ground_strikes_attempts"] or 0,
            match_count=stats["match_count"] or 0
        )
    return FighterSigStrStatsAggregateDTO()

################################
######### FighterMatch #########
################################

async def get_fighters_matches(session: AsyncSession, fighter_id: int, limit: Optional[int] = None) -> List[FighterMatchSchema]:
    """
    특정 선수의 경기 기록을 최신순으로 조회합니다.
    limit이 주어지면 해당 개수만큼만 반환하고, 주어지지 않으면 전체를 반환합니다.
    """
    query = select(FighterMatchModel)\
        .where(FighterMatchModel.fighter_id == fighter_id)\
        .order_by(FighterMatchModel.created_at.desc())
    
    # limit이 주어진 경우에만 적용
    if limit is not None:
        query = query.limit(limit)
        
    result = await session.execute(query)
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

# function for scraping
async def get_match_fighter_mapping(session: AsyncSession) -> Dict[str, Dict[int, FighterMatchSchema]]:
    """detail_url을 키로 하고 fighter_id를 서브키로 하는 딕셔너리 반환"""
    result_dict = {}
    
    # Match와 FighterMatch 조인하여 한 번에 가져오기
    stmt = (
        select(MatchModel, FighterMatchModel)
        .join(FighterMatchModel, FighterMatchModel.match_id == MatchModel.id)
        .where(MatchModel.detail_url.is_not(None))
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    for match, fighter_match in rows:
        detail_url = match.detail_url
        fighter_id = fighter_match.fighter_id
        
        if detail_url not in result_dict:
            result_dict[detail_url] = {}
        result_dict[detail_url][fighter_id] = fighter_match.to_schema()
    
    return result_dict


async def get_match_with_winner_loser(session: AsyncSession, match_id: int) -> Optional[MatchWithResultDTO]:
    """
    특정 매치의 정보와 승자/패자 정보를 조회합니다.
    """
    # 매치 기본 정보 조회
    match = await get_match_by_id(session, match_id)
    if not match:
        return None

    # 매치에 참여한 파이터들 조회
    fighter_matches = await get_fighter_match_by_match_id(session, match_id)

    if not fighter_matches:
        return None

    fighters = []
    winner = None
    loser = None
    draw_fighters = []

    for fm in fighter_matches:
        # 파이터 상세 정보 조회
        fighter = await get_fighter_by_id(session, fm.fighter_id)
        if not fighter:
            continue

        fighter_info = FighterResultDTO(fighter=fighter, result=fm.result)
        fighters.append(fighter_info)

        # 승부 결과에 따라 분류
        if fm.result and fm.result.lower() == "win":
            winner = fighter_info
        elif fm.result and fm.result.lower() == "loss":
            loser = fighter_info
        elif fm.result and fm.result.lower() == "draw":
            draw_fighters.append(fighter_info)

    return MatchWithResultDTO(
        match=match,
        fighters=fighters,
        winner=winner,
        loser=loser,
        draw_fighters=draw_fighters if draw_fighters else None
    )


async def get_match_with_participants(session: AsyncSession, match_id: int) -> Optional[MatchWithFightersDTO]:
    """
    특정 매치의 정보와 참여 파이터들의 기본 정보를 조회합니다.
    """
    # 매치 기본 정보 조회
    match = await get_match_by_id(session, match_id)
    if not match:
        return None

    # 매치에 참여한 파이터들 조회
    fighter_matches = await get_fighter_match_by_match_id(session, match_id)

    fighters = []
    for fm in fighter_matches:
        fighter = await get_fighter_by_id(session, fm.fighter_id)
        if fighter:
            fighters.append(FighterResultDTO(fighter=fighter, result=fm.result))

    return MatchWithFightersDTO(match=match, fighters=fighters)


async def get_match_statistics(session: AsyncSession, match_id: int) -> Optional[MatchStatisticsDTO]:
    """
    특정 매치의 전체 통계 정보를 조회합니다.
    """
    # 매치에 참여한 파이터들 조회
    fighter_matches = await get_fighter_match_by_match_id(session, match_id)

    if not fighter_matches:
        return None

    fighter_stats = []
    combined_stats = CombinedMatchStatsDTO()

    for fm in fighter_matches:
        # 각 파이터의 기본 통계 조회
        basic_stats = await get_basic_match_stats(session, fm.fighter_id, match_id)
        sig_str_stats = await get_sig_str_match_stats(session, fm.fighter_id, match_id)

        fighter_stat = FighterMatchStatDTO(
            fighter_id=fm.fighter_id,
            result=fm.result,
            basic_stats=basic_stats,
            sig_str_stats=sig_str_stats
        )
        fighter_stats.append(fighter_stat)

        # 합계 통계 계산
        if basic_stats:
            combined_stats.total_strikes_attempted += basic_stats.total_str_attempted or 0
            combined_stats.total_strikes_landed += basic_stats.total_str_landed or 0
            combined_stats.total_sig_str_attempted += basic_stats.sig_str_attempted or 0
            combined_stats.total_sig_str_landed += basic_stats.sig_str_landed or 0
            combined_stats.total_takedowns_attempted += basic_stats.td_attempted or 0
            combined_stats.total_takedowns_landed += basic_stats.td_landed or 0
            combined_stats.total_control_time += basic_stats.control_time_seconds or 0
            combined_stats.total_knockdowns += basic_stats.knockdowns or 0
            combined_stats.total_submission_attempts += basic_stats.submission_attempts or 0

    return MatchStatisticsDTO(
        match_id=match_id,
        fighter_stats=fighter_stats,
        combined_stats=combined_stats
    )

