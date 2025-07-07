from typing import List, Literal, Optional, Dict, Any

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc
from datetime import date

from fighter.models import FighterModel, FighterSchema
from event.models import EventModel, EventSchema
from match.models import BasicMatchStatModel, FighterMatchModel, MatchModel, SigStrMatchStatModel, MatchSchema

async def get_all_opponents(session: AsyncSession, fighter_id: int) -> List[FighterSchema]:
    subq = (
        select(FighterMatchModel.match_id)
        .where(FighterMatchModel.fighter_id == fighter_id)
        .subquery()
    )

    result = await session.execute(
        select(FighterModel)
        .join(FighterMatchModel)
        .where(
            FighterMatchModel.match_id.in_(subq),
            FighterModel.id != fighter_id
        )
    )

    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]

async def get_top_fighter_by_stat(session: AsyncSession, stat_model: Literal[BasicMatchStatModel, SigStrMatchStatModel], stat_name: str, limit:int = 10):
    """
    특정 스탯에서 상위 파이터들을 조회
    """

    stat_column = getattr(stat_model, stat_name)

    stmt = (
        select(
            FighterModel, 
            func.sum(stat_column).label("total_stat")
        )
        .join(FighterMatchModel, FighterModel.id == FighterMatchModel.fighter_id)
        .join(stat_model, stat_model.fighter_match_id == FighterMatchModel.id)
        .group_by(FighterModel.id)
        .order_by(desc("total_stat"))
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    rows = result.fetchall()
    return [{"fighter": fighter.to_schema(), "stat": total_stat} for fighter, total_stat in rows]

async def get_upcoming_fighter_match(session: AsyncSession, fighter_id: int) -> Optional[EventSchema]:
    """
    특정 파이터의 다가오는 경기(오늘 이후)가 포함된 가장 가까운 이벤트를 조회합니다.
    """
    result = await session.execute(
        select(EventModel)
        .join(EventModel.matches)
        .join(MatchModel.fighter_matches)
        .where(
            FighterMatchModel.fighter_id == fighter_id,
            EventModel.event_date > date.today()
        )
        .order_by(EventModel.event_date.asc())
        .limit(1)
    )
    event = result.scalar_one_or_none()
    return event.to_schema() if event else None

async def get_matches_between_fighters(session: AsyncSession, fighter_id1: int, fighter_id2: int) -> List[MatchSchema]:
    """
    두 파이터 간의 모든 대전 기록을 조회합니다.
    """
    # 두 파이터가 모두 참여한 매치들을 찾기 위해 서브쿼리 사용
    fighter1_matches = select(FighterMatchModel.match_id).where(FighterMatchModel.fighter_id == fighter_id1).subquery()
    fighter2_matches = select(FighterMatchModel.match_id).where(FighterMatchModel.fighter_id == fighter_id2).subquery()
    
    # 두 서브쿼리의 교집합에 해당하는 매치들 조회
    result = await session.execute(
        select(MatchModel)
        .where(
            and_(
                MatchModel.id.in_(select(fighter1_matches.c.match_id)),
                MatchModel.id.in_(select(fighter2_matches.c.match_id))
            )
        )
        .order_by(MatchModel.id.desc())
    )
    
    matches = result.scalars().all()
    return [match.to_schema() for match in matches]

async def get_event_main_event_match(session: AsyncSession, event_id: int) -> Optional[MatchSchema]:
    """
    특정 이벤트의 메인 이벤트 경기를 조회합니다.
    """
    result = await session.execute(
        select(MatchModel)
        .where(
            and_(
                MatchModel.event_id == event_id,
                MatchModel.is_main_event == True
            )
        )
        .limit(1)
    )
    
    match = result.scalar_one_or_none()
    return match.to_schema() if match else None

async def get_event_with_matches_summary(session: AsyncSession, event_id: int) -> Optional[Dict[str, Any]]:
    """
    이벤트와 해당 이벤트의 모든 매치 요약 정보를 조회합니다.
    """
    # 이벤트 정보 조회
    event_result = await session.execute(
        select(EventModel).where(EventModel.id == event_id)
    )
    event = event_result.scalar_one_or_none()
    
    if not event:
        return None
    
    # 해당 이벤트의 모든 매치 조회
    matches_result = await session.execute(
        select(MatchModel)
        .where(MatchModel.event_id == event_id)
        .order_by(MatchModel.order.desc())  # 메인 이벤트부터 역순으로
    )
    
    matches = matches_result.scalars().all()
    
    # 매치 통계 계산
    total_matches = len(matches)
    main_events = [m for m in matches if m.is_main_event]
    
    # 결승 방식 통계
    finish_methods = {}
    for match in matches:
        if match.method:
            finish_methods[match.method] = finish_methods.get(match.method, 0) + 1
    
    return {
        "event": event.to_schema(),
        "matches": [match.to_schema() for match in matches],
        "summary": {
            "total_matches": total_matches,
            "main_events_count": len(main_events),
            "finish_methods": finish_methods
        }
    }

async def get_fighters_common_opponents(session: AsyncSession, fighter_id1: int, fighter_id2: int) -> List[Dict[str, Any]]:
    """
    두 파이터의 공통 상대들을 조회합니다.
    """
    # 첫 번째 파이터의 상대들
    fighter1_opponents = select(FighterMatchModel.match_id).where(FighterMatchModel.fighter_id == fighter_id1).subquery()
    fighter1_opponent_ids = (
        select(FighterMatchModel.fighter_id)
        .where(
            and_(
                FighterMatchModel.match_id.in_(select(fighter1_opponents.c.match_id)),
                FighterMatchModel.fighter_id != fighter_id1
            )
        )
        .subquery()
    )
    
    # 두 번째 파이터의 상대들
    fighter2_opponents = select(FighterMatchModel.match_id).where(FighterMatchModel.fighter_id == fighter_id2).subquery()
    fighter2_opponent_ids = (
        select(FighterMatchModel.fighter_id)
        .where(
            and_(
                FighterMatchModel.match_id.in_(select(fighter2_opponents.c.match_id)),
                FighterMatchModel.fighter_id != fighter_id2
            )
        )
        .subquery()
    )
    
    # 공통 상대들 조회
    result = await session.execute(
        select(FighterModel)
        .where(
            and_(
                FighterModel.id.in_(select(fighter1_opponent_ids.c.fighter_id)),
                FighterModel.id.in_(select(fighter2_opponent_ids.c.fighter_id))
            )
        )
    )
    
    common_opponents = result.scalars().all()
    
    # 각 공통 상대에 대한 결과 조회
    results = []
    for opponent in common_opponents:
        # Fighter1 vs Opponent 결과
        fighter1_vs_opponent = await session.execute(
            select(FighterMatchModel.result)
            .join(FighterMatchModel.match)
            .join(MatchModel.fighter_matches.and_(FighterMatchModel.fighter_id == opponent.id))
            .where(FighterMatchModel.fighter_id == fighter_id1)
            .limit(1)  # 가장 최근 대결
        )
        
        # Fighter2 vs Opponent 결과
        fighter2_vs_opponent = await session.execute(
            select(FighterMatchModel.result)
            .join(FighterMatchModel.match)
            .join(MatchModel.fighter_matches.and_(FighterMatchModel.fighter_id == opponent.id))
            .where(FighterMatchModel.fighter_id == fighter_id2)
            .limit(1)  # 가장 최근 대결
        )
        
        results.append({
            "opponent": opponent.to_schema(),
            "fighter1_result": fighter1_vs_opponent.scalar_one_or_none(),
            "fighter2_result": fighter2_vs_opponent.scalar_one_or_none()
        })
    
    return results

async def get_top_performers_in_event(session: AsyncSession, event_id: int, stat_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    특정 이벤트에서 특정 스탯의 최고 성과자들을 조회합니다.
    """
    # 통계 모델 결정
    if hasattr(BasicMatchStatModel, stat_name):
        stat_model = BasicMatchStatModel
        stat_column = getattr(BasicMatchStatModel, stat_name)
    elif hasattr(SigStrMatchStatModel, stat_name):
        stat_model = SigStrMatchStatModel
        stat_column = getattr(SigStrMatchStatModel, stat_name)
    else:
        raise ValueError(f"Invalid stat_name: {stat_name}")
    
    result = await session.execute(
        select(
            FighterModel,
            stat_column.label("stat_value")
        )
        .join(FighterMatchModel, FighterModel.id == FighterMatchModel.fighter_id)
        .join(MatchModel, FighterMatchModel.match_id == MatchModel.id)
        .join(stat_model, stat_model.fighter_match_id == FighterMatchModel.id)
        .where(MatchModel.event_id == event_id)
        .order_by(stat_column.desc())
        .limit(limit)
    )
    
    rows = result.all()
    return [
        {
            "fighter": fighter.to_schema(),
            "stat_name": stat_name,
            "stat_value": stat_value
        }
        for fighter, stat_value in rows
    ]

async def get_fighter_performance_trend(session: AsyncSession, fighter_id: int, last_n_fights: int = 5) -> Dict[str, Any]:
    """
    파이터의 최근 N경기 성과 트렌드를 조회합니다.
    """
    # 최근 N경기 조회
    recent_matches_result = await session.execute(
        select(MatchModel, FighterMatchModel.result)
        .join(FighterMatchModel, MatchModel.id == FighterMatchModel.match_id)
        .where(FighterMatchModel.fighter_id == fighter_id)
        .order_by(MatchModel.id.desc())
        .limit(last_n_fights)
    )
    
    recent_matches = recent_matches_result.all()
    
    if not recent_matches:
        return {"trend": "no_data", "matches": []}
    
    # 결과 분석
    wins = sum(1 for _, result in recent_matches if result == "Win")
    losses = sum(1 for _, result in recent_matches if result == "Loss")
    draws = sum(1 for _, result in recent_matches if result == "Draw")
    
    # 트렌드 판단
    win_percentage = wins / len(recent_matches) * 100
    
    if win_percentage >= 80:
        trend = "hot_streak"
    elif win_percentage >= 60:
        trend = "good_form"
    elif win_percentage >= 40:
        trend = "mixed_form"
    else:
        trend = "poor_form"
    
    return {
        "fighter_id": fighter_id,
        "last_n_fights": last_n_fights,
        "trend": trend,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_percentage": round(win_percentage, 2),
        "recent_matches": [
            {
                "match": match.to_schema(),
                "result": result
            }
            for match, result in recent_matches
        ]
    }

async def get_event_attendance_analysis(session: AsyncSession, location_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    이벤트 참석률이나 인기도 분석을 위한 이벤트 데이터를 조회합니다.
    """
    query = select(
        EventModel.location,
        func.count(EventModel.id).label("event_count"),
        func.count(MatchModel.id).label("total_matches")
    ).outerjoin(MatchModel, EventModel.id == MatchModel.event_id)
    
    if location_filter:
        query = query.where(EventModel.location.ilike(f"%{location_filter}%"))
    
    query = query.group_by(EventModel.location).order_by(desc("event_count"))
    
    result = await session.execute(query)
    location_stats = result.all()
    
    return {
        "location_analysis": [
            {
                "location": location,
                "event_count": event_count,
                "total_matches": total_matches,
                "avg_matches_per_event": round(total_matches / event_count, 2) if event_count > 0 else 0
            }
            for location, event_count, total_matches in location_stats
        ]
    }

async def get_weight_class_activity_analysis(session: AsyncSession, year: Optional[int] = None) -> Dict[str, Any]:
    """
    체급별 활동 분석 - 각 체급별 경기 수, 파이터 수 등을 분석합니다.
    """
    query = select(
        MatchModel.weight_class_id,
        func.count(MatchModel.id).label("match_count"),
        func.count(func.distinct(FighterMatchModel.fighter_id)).label("unique_fighters")
    ).join(FighterMatchModel, MatchModel.id == FighterMatchModel.match_id)
    
    if year:
        query = query.join(EventModel, MatchModel.event_id == EventModel.id)\
                    .where(func.extract('year', EventModel.event_date) == year)
    
    query = query.group_by(MatchModel.weight_class_id).order_by(desc("match_count"))
    
    result = await session.execute(query)
    weight_class_stats = result.all()
    
    # WeightClassSchema를 사용하여 체급명 변환
    from common.models import WeightClassSchema
    
    return {
        "year": year or "all_time",
        "weight_class_analysis": [
            {
                "weight_class_id": weight_class_id,
                "weight_class_name": WeightClassSchema.get_name_by_id(weight_class_id),
                "match_count": match_count,
                "unique_fighters": unique_fighters,
                "avg_fights_per_fighter": round(match_count / unique_fighters, 2) if unique_fighters > 0 else 0
            }
            for weight_class_id, match_count, unique_fighters in weight_class_stats
        ]
    }

async def get_finish_rate_by_method(session: AsyncSession, event_id: Optional[int] = None) -> Dict[str, Any]:
    """
    경기 종료 방식별 통계를 조회합니다.
    """
    query = select(
        MatchModel.method,
        func.count(MatchModel.id).label("count")
    )
    
    if event_id:
        query = query.where(MatchModel.event_id == event_id)
    
    query = query.group_by(MatchModel.method).order_by(desc("count"))
    
    result = await session.execute(query)
    method_stats = result.all()
    
    total_matches = sum(count for _, count in method_stats)
    
    return {
        "event_id": event_id,
        "total_matches": total_matches,
        "finish_methods": [
            {
                "method": method or "Unknown",
                "count": count,
                "percentage": round((count / total_matches * 100), 2) if total_matches > 0 else 0
            }
            for method, count in method_stats
        ]
    }