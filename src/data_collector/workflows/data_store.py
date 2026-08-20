import logging
import re
from datetime import datetime
from typing import List

from sqlalchemy import delete, select

from common.utils import normalize_name
from fighter.models import (
    FighterMethodRecordModel,
    FighterSchema,
    FighterPromotionRecordModel,
    RankingSchema,
    FighterModel,
    RankingModel,
)
from event.models import EventSchema, EventModel
from data_collector.scrapers.tapology_scraper import TapologyBoutMetadata, TapologyFighterProfile
from match.models import (
    MatchSchema, 
    FighterMatchSchema, 
    BasicMatchStatSchema, 
    SigStrMatchStatSchema, 
    MatchModel,
    FighterMatchModel,
    BasicMatchStatModel,
    SigStrMatchStatModel
)

TAPOLOGY_MATCH_FIELDS = {
    "bout_status",
    "cancellation_reason",
    "tapology_bout_url",
    "tapology_last_scraped_at",
    "tapology_attempt_status",
    "tapology_last_attempt_at",
    "tapology_failure_stage",
    "tapology_failure_reason",
}

PRESERVE_TRUE_MATCH_FIELDS = {
    "is_title_bout",
    "has_fight_of_the_night_bonus",
}

TAPOLOGY_FIGHTER_PROFILE_FIELDS = {
    "nationality",
    "born",
    "fighting_out_of",
    "affiliation",
    "gym",
}

UFC_PROMOTION_NAMES = {
    "ufc",
    "ultimate fighting championship",
    "ufc ultimate fighting championship",
}

async def save_fighters(session, fighters: List[FighterSchema]):

    for fighter in fighters:
        if not fighter.name:
            continue

        fighter_name = normalize_name(fighter.name)

        # detail_url이 있으면 detail_url 기준으로 조회, 없으면 name 기준
        if fighter.detail_url:
            existing_model_query = await session.execute(
                select(FighterModel).where(FighterModel.detail_url == fighter.detail_url)
            )
        else:
            existing_model_query = await session.execute(
                select(FighterModel).where(FighterModel.name == fighter_name)
            )

        existing_model = existing_model_query.scalar_one_or_none()

        if existing_model:
            # 업데이트 (None 값은 기존 값 유지 — 별도 스크립트로 채운 nationality 등 보호)
            for key, value in fighter.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                if value is None and getattr(existing_model, key, None) is not None:
                    continue
                setattr(existing_model, key, value)
        else:
            # 새로 생성
            new_fighter = FighterModel.from_schema(fighter)
            session.add(new_fighter)

    await session.commit()

async def save_events(session, events: List[EventSchema]):
    
    for event in events:
        if not event.name:
            continue

            
        # 기존 이벤트 조회 (Pydantic 스키마 반환)
        existing_model_query = await session.execute(
            select(EventModel).where(EventModel.url == event.url)
        )
        existing_model = existing_model_query.scalar_one_or_none()
        
        if existing_model:
            # 업데이트 (None 값은 기존 값 유지 — 별도 스크립트로 채운 latitude/longitude 등 보호)
            for key, value in event.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                if value is None and getattr(existing_model, key, None) is not None:
                    continue
                setattr(existing_model, key, value)
        else:
            # 새로 생성
            new_event = EventModel.from_schema(event)
            session.add(new_event)
    
    await session.commit()


async def save_tapology_event_url(session, event_id: int, tapology_url: str) -> EventSchema | None:
    existing_model_query = await session.execute(
        select(EventModel).where(EventModel.id == event_id)
    )
    existing_model = existing_model_query.scalar_one_or_none()
    if existing_model is None:
        return None

    existing_model.tapology_url = tapology_url

    await session.commit()
    await session.refresh(existing_model)
    return existing_model.to_schema()

async def save_match(session, match: MatchSchema) -> MatchSchema:
    existing_model_query = await session.execute(
        select(MatchModel).where(MatchModel.detail_url == match.detail_url)
    )
    existing_model = existing_model_query.scalar_one_or_none()

    if existing_model:
        # 업데이트
        for key, value in match.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
            if key in TAPOLOGY_MATCH_FIELDS and value is None and getattr(existing_model, key, None) is not None:
                continue
            if key in PRESERVE_TRUE_MATCH_FIELDS and value is False and getattr(existing_model, key, None) is True:
                continue
            setattr(existing_model, key, value)
        return_model = existing_model
    else:
        # 새로 생성
        new_match = MatchModel.from_schema(match)
        session.add(new_match)
        return_model = new_match

    await session.commit()
    await session.refresh(return_model)
    return return_model.to_schema()


async def save_tapology_fighter_enrichment(
    session,
    fighter_id: int,
    tapology_url: str | None,
    profile: TapologyFighterProfile,
    scraped_at: datetime,
) -> FighterSchema | None:
    existing_model_query = await session.execute(
        select(FighterModel).where(FighterModel.id == fighter_id)
    )
    existing_model = existing_model_query.scalar_one_or_none()
    if existing_model is None:
        return None

    if tapology_url:
        existing_model.tapology_url = tapology_url

    for key in TAPOLOGY_FIGHTER_PROFILE_FIELDS:
        value = getattr(profile, key, None)
        if value is None and getattr(existing_model, key, None) is not None:
            continue
        setattr(existing_model, key, value)

    existing_model.tapology_last_scraped_at = scraped_at
    existing_model.tapology_attempt_status = "succeeded"
    existing_model.tapology_last_attempt_at = scraped_at
    existing_model.tapology_failure_stage = None
    existing_model.tapology_failure_reason = None
    await _replace_non_ufc_promotion_records(session, fighter_id, profile)
    await _replace_non_ufc_method_records(session, fighter_id, profile)

    await session.commit()
    await session.refresh(existing_model)
    return existing_model.to_schema()


async def save_tapology_fighter_attempt_state(
    session,
    fighter_id: int,
    *,
    status: str,
    attempted_at: datetime,
    failure_stage: str | None = None,
    failure_reason: str | None = None,
) -> FighterSchema | None:
    existing_model_query = await session.execute(
        select(FighterModel).where(FighterModel.id == fighter_id)
    )
    existing_model = existing_model_query.scalar_one_or_none()
    if existing_model is None:
        return None

    existing_model.tapology_attempt_status = status
    existing_model.tapology_last_attempt_at = attempted_at
    existing_model.tapology_failure_stage = failure_stage
    existing_model.tapology_failure_reason = _trim_failure_reason(failure_reason)

    await session.commit()
    await session.refresh(existing_model)
    return existing_model.to_schema()


async def _replace_non_ufc_promotion_records(
    session,
    fighter_id: int,
    profile: TapologyFighterProfile,
) -> None:
    await session.execute(
        delete(FighterPromotionRecordModel).where(
            FighterPromotionRecordModel.fighter_id == fighter_id
        )
    )

    for record in profile.promotion_records:
        if _is_ufc_promotion(record.promotion_name):
            continue
        if not any([record.wins, record.losses, record.draws, record.no_contests]):
            continue
        session.add(
            FighterPromotionRecordModel(
                fighter_id=fighter_id,
                promotion_name=record.promotion_name,
                wins=record.wins,
                losses=record.losses,
                draws=record.draws,
                no_contests=record.no_contests,
            )
        )


async def _replace_non_ufc_method_records(
    session,
    fighter_id: int,
    profile: TapologyFighterProfile,
) -> None:
    await session.execute(
        delete(FighterMethodRecordModel).where(
            FighterMethodRecordModel.fighter_id == fighter_id
        )
    )

    tapology_totals: dict[tuple[str, str], int] = {}
    for record in profile.method_records:
        method_category = _normalize_method_category(record.method_category)
        result = _normalize_result(record.result)
        if not method_category or not result:
            continue
        key = (result, method_category)
        tapology_totals[key] = tapology_totals.get(key, 0) + record.count

    ufc_totals = await _load_ufc_method_totals(session, fighter_id)
    for key, tapology_count in sorted(tapology_totals.items()):
        non_ufc_count = tapology_count - ufc_totals.get(key, 0)
        if non_ufc_count <= 0:
            continue
        result, method_category = key
        session.add(
            FighterMethodRecordModel(
                fighter_id=fighter_id,
                scope="non_ufc",
                result=result,
                method_category=method_category,
                count=non_ufc_count,
            )
        )


async def _load_ufc_method_totals(session, fighter_id: int) -> dict[tuple[str, str], int]:
    rows = await session.execute(
        select(FighterMatchModel.result, MatchModel.method)
        .join(MatchModel, MatchModel.id == FighterMatchModel.match_id)
        .where(
            FighterMatchModel.fighter_id == fighter_id,
            FighterMatchModel.result.is_not(None),
            MatchModel.method.is_not(None),
        )
    )

    totals: dict[tuple[str, str], int] = {}
    for result, method in rows.all():
        normalized_result = _normalize_result(result)
        method_category = _normalize_method_category(method)
        if not normalized_result or not method_category:
            continue
        key = (normalized_result, method_category)
        totals[key] = totals.get(key, 0) + 1
    return totals


def _is_ufc_promotion(promotion_name: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", promotion_name.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized in UFC_PROMOTION_NAMES


def _normalize_result(result: str | None) -> str | None:
    if not result:
        return None
    normalized = result.lower().strip()
    if normalized in {"win", "loss", "draw", "nc"}:
        return normalized
    return None


def _normalize_method_category(method: str | None) -> str | None:
    if not method:
        return None
    normalized = method.upper().strip()
    normalized = normalized.replace("KO / TKO", "KO/TKO")
    if normalized.startswith(("KO/TKO", "KO-", "TKO-", "TKO", "KO")):
        return "KO/TKO"
    if normalized.startswith("SUB"):
        return "SUB"
    if normalized == "DEC" or "-DEC" in normalized:
        return "DEC"
    if normalized.startswith(("DQD", "DQ")):
        return "DQ"
    if normalized in {"NC", "CNC"}:
        return "NC"
    return None


async def save_tapology_match_enrichment(
    session,
    match_id: int,
    tapology_bout_url: str | None,
    metadata: TapologyBoutMetadata,
    scraped_at: datetime,
    logger: logging.Logger | None = None,
) -> MatchSchema | None:
    logger = logger or logging.getLogger(__name__)
    existing_model_query = await session.execute(
        select(MatchModel).where(MatchModel.id == match_id)
    )
    existing_model = existing_model_query.scalar_one_or_none()
    if existing_model is None:
        return None

    fighter_rows = await session.execute(
        select(FighterMatchModel, FighterModel)
        .join(FighterModel, FighterModel.id == FighterMatchModel.fighter_id)
        .where(FighterMatchModel.match_id == match_id)
    )
    fighter_matches = fighter_rows.all()
    has_ufcstats_result = any(fighter_match.result for fighter_match, _ in fighter_matches)
    tapology_cancelled = metadata.bout_status in {"cancelled", "canceled", "postponed"}

    if metadata.is_title_bout or existing_model.is_title_bout is not True:
        existing_model.is_title_bout = metadata.is_title_bout
    if tapology_bout_url:
        existing_model.tapology_bout_url = tapology_bout_url
    existing_model.tapology_last_scraped_at = scraped_at
    existing_model.tapology_attempt_status = "succeeded"
    existing_model.tapology_last_attempt_at = scraped_at
    existing_model.tapology_failure_stage = None
    existing_model.tapology_failure_reason = None

    if tapology_cancelled and has_ufcstats_result:
        logger.warning(
            "Tapology cancellation conflicts with UFCStats result; preserving match status. match_id=%s url=%s",
            match_id,
            tapology_bout_url,
        )
    else:
        if metadata.bout_status is not None:
            existing_model.bout_status = metadata.bout_status
        if metadata.cancellation_reason is not None:
            existing_model.cancellation_reason = metadata.cancellation_reason

    fighter_match_by_name = {
        _normalize_match_name(fighter.name): fighter_match
        for fighter_match, fighter in fighter_matches
    }

    for fighter_metadata in metadata.fighter_metadata:
        if not fighter_metadata.fighter_name:
            continue
        fighter_match = fighter_match_by_name.get(_normalize_match_name(fighter_metadata.fighter_name))
        if fighter_match is None:
            logger.warning(
                "Tapology fighter-side metadata did not match local fighter. match_id=%s fighter=%s",
                match_id,
                fighter_metadata.fighter_name,
            )
            continue

        if fighter_metadata.weigh_in_result is not None:
            fighter_match.weigh_in_result = fighter_metadata.weigh_in_result
        if fighter_metadata.fight_night_weight is not None:
            fighter_match.fight_night_weight = fighter_metadata.fight_night_weight

    await session.commit()
    await session.refresh(existing_model)
    return existing_model.to_schema()


async def save_tapology_match_attempt_state(
    session,
    match_id: int,
    *,
    status: str,
    attempted_at: datetime,
    failure_stage: str | None = None,
    failure_reason: str | None = None,
) -> MatchSchema | None:
    existing_model_query = await session.execute(
        select(MatchModel).where(MatchModel.id == match_id)
    )
    existing_model = existing_model_query.scalar_one_or_none()
    if existing_model is None:
        return None

    existing_model.tapology_attempt_status = status
    existing_model.tapology_last_attempt_at = attempted_at
    existing_model.tapology_failure_stage = failure_stage
    existing_model.tapology_failure_reason = _trim_failure_reason(failure_reason)

    await session.commit()
    await session.refresh(existing_model)
    return existing_model.to_schema()


def _trim_failure_reason(reason: str | None, *, limit: int = 1000) -> str | None:
    if reason is None:
        return None
    normalized = re.sub(r"\s+", " ", str(reason)).strip()
    if not normalized:
        return None
    return normalized[:limit]


def _normalize_match_name(value: str) -> str:
    normalized = normalize_name(value)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()
    

async def save_fighter_match(
    session,
    fighter_id: int,
    match_id: int,
    result: str | None,
    has_performance_of_the_night_bonus: bool = False,
) -> FighterMatchSchema:
    existing_model_query = await session.execute(
        select(FighterMatchModel).where(FighterMatchModel.fighter_id == fighter_id, FighterMatchModel.match_id == match_id)
    )
    existing_model = existing_model_query.scalar_one_or_none()

    if existing_model:
        # 업데이트
        existing_model.result = result
        if has_performance_of_the_night_bonus or existing_model.has_performance_of_the_night_bonus is not True:
            existing_model.has_performance_of_the_night_bonus = has_performance_of_the_night_bonus
        return_model = existing_model
    else:
        # 새로 생성
        new_match = FighterMatchModel(
            fighter_id=fighter_id,
            match_id=match_id,
            result=result,
            has_performance_of_the_night_bonus=has_performance_of_the_night_bonus,
        )
        session.add(new_match)
        return_model = new_match

    await session.commit()
    await session.refresh(return_model)
    return return_model.to_schema()

async def save_basic_match_stat(session, basic_match_stat_list: List[BasicMatchStatSchema]):
    for basic_match_stat in basic_match_stat_list:
        existing_stats = await session.execute(
            select(BasicMatchStatModel)
            .where(
                BasicMatchStatModel.fighter_match_id == basic_match_stat.fighter_match_id,
                BasicMatchStatModel.round == basic_match_stat.round
            )
        )
        existing_stats = existing_stats.scalar_one_or_none()
        
        if existing_stats:            
            # 업데이트
            for key, value in basic_match_stat.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                setattr(existing_stats, key, value)
        else:
            # 새로 생성
            new_stats = BasicMatchStatModel.from_schema(basic_match_stat)
            session.add(new_stats)
    
    await session.commit()

async def save_sig_str_match_stat(session, sig_str_match_stat_list: List[SigStrMatchStatSchema]):
    for sig_str_match_stat in sig_str_match_stat_list:
        existing_stats = await session.execute(
            select(SigStrMatchStatModel)
            .where(
                SigStrMatchStatModel.fighter_match_id == sig_str_match_stat.fighter_match_id,
                SigStrMatchStatModel.round == sig_str_match_stat.round
            )
        )
        existing_stats = existing_stats.scalar_one_or_none()
        
        if existing_stats:            
            # 업데이트
            for key, value in sig_str_match_stat.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                setattr(existing_stats, key, value)
        else:
            # 새로 생성
            new_stats = SigStrMatchStatModel.from_schema(sig_str_match_stat)
            session.add(new_stats)
    
    await session.commit()

async def save_rankings(session, rankings: List[RankingSchema]):
    for ranking in rankings:
        new_stats = RankingModel.from_schema(ranking)
        session.add(new_stats)
    
    await session.commit()
