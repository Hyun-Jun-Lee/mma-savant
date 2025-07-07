from typing import List, Optional, Dict

from sqlalchemy import select, func
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

async def get_fighter_basic_stats_aggregate(session: AsyncSession, fighter_id: int) -> Dict:
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
    # None 값을 0으로 변환
    return {
        key: stats[key] or 0 for key in stats.keys()
    } if stats else {
        "knockdowns": 0,
        "control_time_seconds": 0,
        "submission_attempts": 0,
        "sig_str_landed": 0,
        "sig_str_attempted": 0,
        "total_str_landed": 0,
        "total_str_attempted": 0,
        "td_landed": 0,
        "td_attempted": 0,
        "match_count": 0
    }

async def get_fighter_sig_str_stats_aggregate(session: AsyncSession, fighter_id: int) -> Dict:
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
    # None 값을 0으로 변환
    return {
        key: stats[key] or 0 for key in stats.keys()
    } if stats else {
        "head_strikes_landed": 0,
        "head_strikes_attempts": 0,
        "body_strikes_landed": 0,
        "body_strikes_attempts": 0,
        "leg_strikes_landed": 0,
        "leg_strikes_attempts": 0,
        "takedowns_landed": 0,
        "takedowns_attempts": 0,
        "clinch_strikes_landed": 0,
        "clinch_strikes_attempts": 0,
        "ground_strikes_landed": 0,
        "ground_strikes_attempts": 0,
        "match_count": 0
    }

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


async def get_match_with_winner_loser(session: AsyncSession, match_id: int) -> Optional[Dict]:
    """
    특정 매치의 정보와 승자/패자 정보를 조회합니다.
    """
    from fighter.repositories import get_fighter_by_id
    
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
        
        fighter_info = {
            "fighter": fighter,
            "result": fm.result
        }
        fighters.append(fighter_info)
        
        # 승부 결과에 따라 분류
        if fm.result and fm.result.lower() == "win":
            winner = fighter_info
        elif fm.result and fm.result.lower() == "loss":
            loser = fighter_info
        elif fm.result and fm.result.lower() == "draw":
            draw_fighters.append(fighter_info)
    
    result = {
        "match": match,
        "fighters": fighters
    }
    
    if winner:
        result["winner"] = winner
    if loser:
        result["loser"] = loser
    if draw_fighters:
        result["draw_fighters"] = draw_fighters
    
    return result


async def get_match_with_participants(session: AsyncSession, match_id: int) -> Optional[Dict]:
    """
    특정 매치의 정보와 참여 파이터들의 기본 정보를 조회합니다.
    """
    from fighter.repositories import get_fighter_by_id
    
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
            fighters.append({
                "fighter": fighter,
                "result": fm.result
            })
    
    return {
        "match": match,
        "fighters": fighters
    }


async def get_match_statistics(session: AsyncSession, match_id: int) -> Optional[Dict]:
    """
    특정 매치의 전체 통계 정보를 조회합니다.
    """
    # 매치에 참여한 파이터들 조회
    fighter_matches = await get_fighter_match_by_match_id(session, match_id)
    
    if not fighter_matches:
        return None
    
    match_stats = {
        "match_id": match_id,
        "fighter_stats": [],
        "combined_stats": {
            "total_strikes_attempted": 0,
            "total_strikes_landed": 0,
            "total_sig_str_attempted": 0,
            "total_sig_str_landed": 0,
            "total_takedowns_attempted": 0,
            "total_takedowns_landed": 0,
            "total_control_time": 0,
            "total_knockdowns": 0,
            "total_submission_attempts": 0
        }
    }
    
    for fm in fighter_matches:
        # 각 파이터의 기본 통계 조회
        basic_stats = await get_basic_match_stats(session, fm.fighter_id, match_id)
        sig_str_stats = await get_sig_str_match_stats(session, fm.fighter_id, match_id)
        
        fighter_stat = {
            "fighter_id": fm.fighter_id,
            "result": fm.result,
            "basic_stats": basic_stats,
            "sig_str_stats": sig_str_stats
        }
        
        match_stats["fighter_stats"].append(fighter_stat)
        
        # 합계 통계 계산
        if basic_stats:
            match_stats["combined_stats"]["total_strikes_attempted"] += basic_stats.total_str_attempted or 0
            match_stats["combined_stats"]["total_strikes_landed"] += basic_stats.total_str_landed or 0
            match_stats["combined_stats"]["total_sig_str_attempted"] += basic_stats.sig_str_attempted or 0
            match_stats["combined_stats"]["total_sig_str_landed"] += basic_stats.sig_str_landed or 0
            match_stats["combined_stats"]["total_takedowns_attempted"] += basic_stats.td_attempted or 0
            match_stats["combined_stats"]["total_takedowns_landed"] += basic_stats.td_landed or 0
            match_stats["combined_stats"]["total_control_time"] += basic_stats.control_time_seconds or 0
            match_stats["combined_stats"]["total_knockdowns"] += basic_stats.knockdowns or 0
            match_stats["combined_stats"]["total_submission_attempts"] += basic_stats.submission_attempts or 0
    
    return match_stats


async def get_matches_with_high_activity(session: AsyncSession, min_strikes: int = 200, limit: int = 10) -> List[Dict]:
    """
    높은 활동량을 보인 매치들을 조회합니다 (총 타격 시도 수 기준).
    """
    # 매치별 총 타격 시도 수 합계 조회
    result = await session.execute(
        select(
            MatchModel,
            func.sum(BasicMatchStatModel.total_str_attempted).label("total_strikes")
        )
        .join(FighterMatchModel, MatchModel.id == FighterMatchModel.match_id)
        .join(BasicMatchStatModel, BasicMatchStatModel.fighter_match_id == FighterMatchModel.id)
        .group_by(MatchModel.id)
        .having(func.sum(BasicMatchStatModel.total_str_attempted) >= min_strikes)
        .order_by(func.sum(BasicMatchStatModel.total_str_attempted).desc())
        .limit(limit)
    )
    
    matches = result.all()
    
    high_activity_matches = []
    for match, total_strikes in matches:
        high_activity_matches.append({
            "match": match.to_schema(),
            "total_strikes": total_strikes,
            "activity_rating": "very_high" if total_strikes >= 400 else "high"
        })
    
    return high_activity_matches


async def get_matches_by_finish_method(session: AsyncSession, method_pattern: str, limit: int = 20) -> List[MatchSchema]:
    """
    특정 피니시 방법으로 끝난 매치들을 조회합니다.
    """
    result = await session.execute(
        select(MatchModel)
        .where(MatchModel.method.ilike(f"%{method_pattern}%"))
        .order_by(MatchModel.id.desc())
        .limit(limit)
    )
    
    matches = result.scalars().all()
    return [match.to_schema() for match in matches]


async def get_matches_by_duration(
    session: AsyncSession, 
    min_rounds: Optional[int] = None,
    max_rounds: Optional[int] = None,
    limit: int = 20
) -> List[MatchSchema]:
    """
    특정 지속 시간(라운드 수) 조건에 맞는 매치들을 조회합니다.
    """
    query = select(MatchModel)
    
    conditions = []
    if min_rounds is not None:
        conditions.append(MatchModel.result_round >= min_rounds)
    if max_rounds is not None:
        conditions.append(MatchModel.result_round <= max_rounds)
    
    if conditions:
        query = query.where(*conditions)
    
    query = query.order_by(MatchModel.id.desc()).limit(limit)
    
    result = await session.execute(query)
    matches = result.scalars().all()
    return [match.to_schema() for match in matches]