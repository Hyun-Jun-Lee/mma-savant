import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus

from prefect import task
from prefect.cache_policies import NO_CACHE
from prefect.logging import get_run_logger
from sqlalchemy import or_, select

from common.utils import utc_now
from data_collector.clients import TapologyClient
from data_collector.scrapers.tapology_scraper import (
    TapologyBoutMetadata,
    TapologyFighterProfile,
    parse_tapology_bout_metadata,
    parse_tapology_fighter_profile,
)
from data_collector.workflows.data_store import (
    save_tapology_fighter_enrichment,
    save_tapology_match_enrichment,
)
from data_collector.workflows.tapology_matcher import (
    MatchState,
    match_tapology_bout,
    parse_tapology_bout_candidates,
    parse_tapology_fighter_candidates,
    match_tapology_fighter_candidates,
)
from database.connection.postgres_conn import get_async_db_context
from event.models import EventModel
from fighter.models import FighterModel, FighterSchema
from match.models import FighterMatchModel, MatchModel

ProfileSaver = Callable[[int, str | None, TapologyFighterProfile, datetime], Awaitable[object]]
BoutSaver = Callable[[int, str | None, TapologyBoutMetadata, datetime], Awaitable[object]]


@dataclass
class TapologyLocalBoutFighter:
    fighter_id: int
    fighter_match_id: int
    name: str
    result: str | None = None


@dataclass
class TapologyLocalBout:
    match_id: int
    event_name: str | None
    event_date: date | None
    tapology_bout_url: str | None
    fighters: list[TapologyLocalBoutFighter]


@dataclass
class TapologyProfileEnrichmentStats:
    total: int = 0
    matched: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0


@dataclass
class TapologyBoutEnrichmentStats:
    total: int = 0
    matched: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0


@task(retries=2, cache_policy=NO_CACHE)
async def enrich_fighter_tapology_profile_task(
    crawler_fn: Callable | None = None,
    batch_size: int = 50,
    stale_days: int = 30,
) -> None:
    logger = get_run_logger()
    logger.info("enrich_fighter_tapology_profile_task started")

    async with get_async_db_context() as session:
        fighters = await select_fighters_for_tapology_profile_enrichment(
            session,
            batch_size=batch_size,
            stale_days=stale_days,
        )

    logger.info("Found %d fighters for Tapology profile enrichment", len(fighters))
    if not fighters:
        return

    stats = TapologyProfileEnrichmentStats(total=len(fighters))
    client = TapologyClient()
    try:
        async def save_profile(
            fighter_id: int,
            tapology_url: str | None,
            profile: TapologyFighterProfile,
            scraped_at: datetime,
        ) -> object:
            async with get_async_db_context() as session:
                return await save_tapology_fighter_enrichment(
                    session,
                    fighter_id,
                    tapology_url,
                    profile,
                    scraped_at,
                )

        stats = await enrich_fighter_tapology_profile_batch(
            fighters,
            client,
            save_profile,
            logger,
            crawler_fn=crawler_fn,
        )
    finally:
        client.close()

    logger.info(
        "enrich_fighter_tapology_profile_task completed: "
        "total=%d matched=%d updated=%d skipped=%d failed=%d",
        stats.total,
        stats.matched,
        stats.updated,
        stats.skipped,
        stats.failed,
    )


@task(retries=2, cache_policy=NO_CACHE)
async def enrich_match_tapology_metadata_task(
    crawler_fn: Callable | None = None,
    batch_size: int = 50,
    stale_days: int = 30,
) -> None:
    logger = get_run_logger()
    logger.info("enrich_match_tapology_metadata_task started")

    async with get_async_db_context() as session:
        bouts = await select_matches_for_tapology_bout_enrichment(
            session,
            batch_size=batch_size,
            stale_days=stale_days,
        )

    logger.info("Found %d matches for Tapology bout enrichment", len(bouts))
    if not bouts:
        return

    stats = TapologyBoutEnrichmentStats(total=len(bouts))
    client = TapologyClient()
    try:
        async def save_bout(
            match_id: int,
            tapology_bout_url: str | None,
            metadata: TapologyBoutMetadata,
            scraped_at: datetime,
        ) -> object:
            async with get_async_db_context() as session:
                return await save_tapology_match_enrichment(
                    session,
                    match_id,
                    tapology_bout_url,
                    metadata,
                    scraped_at,
                    logger,
                )

        stats = await enrich_match_tapology_metadata_batch(
            bouts,
            client,
            save_bout,
            logger,
            crawler_fn=crawler_fn,
        )
    finally:
        client.close()

    logger.info(
        "enrich_match_tapology_metadata_task completed: "
        "total=%d matched=%d updated=%d skipped=%d failed=%d",
        stats.total,
        stats.matched,
        stats.updated,
        stats.skipped,
        stats.failed,
    )


async def select_fighters_for_tapology_profile_enrichment(
    session,
    *,
    batch_size: int = 50,
    stale_days: int = 30,
) -> list[FighterSchema]:
    cutoff = utc_now() - timedelta(days=stale_days)
    result = await session.execute(
        select(FighterModel)
        .where(
            or_(
                FighterModel.tapology_url.is_(None),
                FighterModel.tapology_last_scraped_at.is_(None),
                FighterModel.tapology_last_scraped_at < cutoff,
            )
        )
        .order_by(FighterModel.id)
        .limit(batch_size)
    )
    return [fighter.to_schema() for fighter in result.scalars().all()]


async def select_matches_for_tapology_bout_enrichment(
    session,
    *,
    batch_size: int = 50,
    stale_days: int = 30,
) -> list[TapologyLocalBout]:
    cutoff = utc_now() - timedelta(days=stale_days)
    result = await session.execute(
        select(MatchModel, EventModel)
        .join(EventModel, EventModel.id == MatchModel.event_id)
        .where(
            or_(
                MatchModel.tapology_bout_url.is_(None),
                MatchModel.tapology_last_scraped_at.is_(None),
                MatchModel.tapology_last_scraped_at < cutoff,
            )
        )
        .order_by(MatchModel.id)
        .limit(batch_size)
    )

    bouts: list[TapologyLocalBout] = []
    for match, event in result.all():
        fighter_result = await session.execute(
            select(FighterMatchModel, FighterModel)
            .join(FighterModel, FighterModel.id == FighterMatchModel.fighter_id)
            .where(FighterMatchModel.match_id == match.id)
            .order_by(FighterMatchModel.id)
        )
        fighters = [
            TapologyLocalBoutFighter(
                fighter_id=fighter.id,
                fighter_match_id=fighter_match.id,
                name=fighter.name,
                result=fighter_match.result,
            )
            for fighter_match, fighter in fighter_result.all()
        ]
        if len(fighters) < 2:
            continue
        bouts.append(
            TapologyLocalBout(
                match_id=match.id,
                event_name=event.name,
                event_date=event.event_date,
                tapology_bout_url=match.tapology_bout_url,
                fighters=fighters,
            )
        )

    return bouts


async def enrich_fighter_tapology_profile_batch(
    fighters: list[FighterSchema],
    client: TapologyClient,
    save_profile: ProfileSaver,
    logger: logging.Logger,
    crawler_fn: Callable | None = None,
) -> TapologyProfileEnrichmentStats:
    stats = TapologyProfileEnrichmentStats(total=len(fighters))
    scraped_at = utc_now()

    for index, fighter in enumerate(fighters, 1):
        logger.info("[%d/%d] Tapology profile enrichment: %s", index, len(fighters), fighter.name)

        try:
            if fighter.tapology_url:
                match_result = match_tapology_fighter_candidates(fighter, [])
            else:
                search_html = await _fetch_tapology_search_page(client, crawler_fn, fighter.name)
                match_result = match_tapology_fighter_candidates(
                    fighter,
                    parse_tapology_fighter_candidates(search_html or ""),
                )
            if match_result.state != MatchState.MATCHED or not match_result.url:
                stats.skipped += 1
                logger.warning(
                    "Skipping Tapology profile enrichment for fighter_id=%s name=%s state=%s reason=%s",
                    fighter.id,
                    fighter.name,
                    match_result.state,
                    match_result.reason,
                )
                continue

            stats.matched += 1
            html = await _fetch_tapology_fighter_detail_page(client, crawler_fn, match_result.url)
            if not html:
                stats.failed += 1
                logger.warning("Tapology profile page fetch failed for %s", match_result.url)
                continue

            profile = parse_tapology_fighter_profile(html)
            await save_profile(fighter.id, match_result.url, profile, scraped_at)
            stats.updated += 1
        except Exception as exc:
            stats.failed += 1
            logger.exception(
                "Tapology profile enrichment failed for fighter_id=%s name=%s: %s",
                fighter.id,
                fighter.name,
                exc,
            )

    return stats


async def enrich_match_tapology_metadata_batch(
    bouts: list[TapologyLocalBout],
    client: TapologyClient,
    save_bout: BoutSaver,
    logger: logging.Logger,
    crawler_fn: Callable | None = None,
) -> TapologyBoutEnrichmentStats:
    stats = TapologyBoutEnrichmentStats(total=len(bouts))
    scraped_at = utc_now()

    for index, bout in enumerate(bouts, 1):
        fighter_names = [fighter.name for fighter in bout.fighters]
        logger.info(
            "[%d/%d] Tapology bout enrichment: match_id=%s fighters=%s",
            index,
            len(bouts),
            bout.match_id,
            fighter_names,
        )

        try:
            bout_url = bout.tapology_bout_url
            if not bout_url:
                search_html = await _fetch_tapology_search_page(client, crawler_fn, _build_bout_search_term(bout))
                candidates = parse_tapology_bout_candidates(search_html or "")
                match_result = match_tapology_bout(
                    candidates,
                    fighter_names=fighter_names,
                    event_date=bout.event_date,
                    event_name=bout.event_name,
                )
                if match_result.state != MatchState.MATCHED or not match_result.url:
                    stats.skipped += 1
                    logger.warning(
                        "Skipping Tapology bout enrichment for match_id=%s state=%s reason=%s",
                        bout.match_id,
                        match_result.state,
                        match_result.reason,
                    )
                    continue
                bout_url = match_result.url

            stats.matched += 1
            html = await _fetch_tapology_bout_detail_page(client, crawler_fn, bout_url)
            if not html:
                stats.failed += 1
                logger.warning("Tapology bout page fetch failed for %s", bout_url)
                continue

            metadata = parse_tapology_bout_metadata(html, fighter_names=fighter_names)
            await save_bout(bout.match_id, bout_url, metadata, scraped_at)
            stats.updated += 1
        except Exception as exc:
            stats.failed += 1
            logger.exception(
                "Tapology bout enrichment failed for match_id=%s: %s",
                bout.match_id,
                exc,
            )

    return stats


def _build_bout_search_term(bout: TapologyLocalBout) -> str:
    fighter_part = " ".join(fighter.name for fighter in bout.fighters[:2])
    if bout.event_name:
        return f"{fighter_part} {bout.event_name}"
    return fighter_part


async def _fetch_tapology_search_page(
    client: TapologyClient,
    crawler_fn: Callable | None,
    term: str,
) -> str | None:
    if crawler_fn:
        return await crawler_fn(f"https://www.tapology.com/search?term={quote_plus(term)}")
    return await asyncio.to_thread(client.fetch_search_page, term)


async def _fetch_tapology_fighter_detail_page(
    client: TapologyClient,
    crawler_fn: Callable | None,
    path_or_url: str,
) -> str | None:
    if crawler_fn:
        return await crawler_fn(path_or_url)
    return await asyncio.to_thread(client.fetch_fighter_detail_page, path_or_url)


async def _fetch_tapology_bout_detail_page(
    client: TapologyClient,
    crawler_fn: Callable | None,
    path_or_url: str,
) -> str | None:
    if crawler_fn:
        return await crawler_fn(path_or_url)
    return await asyncio.to_thread(client.fetch_bout_detail_page, path_or_url)
