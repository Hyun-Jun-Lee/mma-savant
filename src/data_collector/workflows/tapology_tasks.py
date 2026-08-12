import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus

from prefect import task
from prefect.cache_policies import NO_CACHE
from prefect.logging import get_run_logger
from sqlalchemy import func, or_, select

from common.utils import utc_now
from data_collector.clients import TapologyClient
from data_collector.scrapers.tapology_scraper import (
    TapologyBoutMetadata,
    TapologyFighterProfile,
    parse_tapology_bout_metadata,
    parse_tapology_fighter_profile,
)
from data_collector.workflows.data_store import (
    save_tapology_event_url,
    save_tapology_fighter_enrichment,
    save_tapology_match_enrichment,
)
from data_collector.workflows.progress import format_progress
from data_collector.workflows.tapology_matcher import (
    MatchState,
    match_tapology_bout,
    match_tapology_event_candidates,
    parse_tapology_bout_candidates,
    parse_tapology_event_candidates,
    parse_tapology_fighter_candidates,
    match_tapology_fighter_candidates,
)
from database.connection.postgres_conn import get_async_db_context
from event.models import EventModel
from fighter.models import FighterModel, FighterSchema
from match.models import FighterMatchModel, MatchModel

ProfileSaver = Callable[[int, str | None, TapologyFighterProfile, datetime], Awaitable[object]]
BoutSaver = Callable[[int, str | None, TapologyBoutMetadata, datetime], Awaitable[object]]
EventUrlSaver = Callable[[int, str], Awaitable[object]]

_TAPOLOGY_CHALLENGE_MARKERS = (
    "just a moment...",
    "checking if the site connection is secure",
    "cf-challenge",
    "challenge-platform",
    "/cdn-cgi/challenge-platform/",
    "cf-browser-verification",
    "cloudflare ray id",
)


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
    event_id: int | None = None
    event_tapology_url: str | None = None


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


@task(
    name="tapology-profiles",
    task_run_name="tapology-profiles",
    retries=2,
    cache_policy=NO_CACHE,
)
async def enrich_fighter_tapology_profile_task(
    crawler_fn: Callable | None = None,
    batch_size: int = 20,
    stale_days: int = 30,
) -> None:
    logger = get_run_logger()
    logger.info("enrich_fighter_tapology_profile_task started")

    stats = TapologyProfileEnrichmentStats()
    last_seen_id: int | None = None
    batch_index = 0
    client = TapologyClient()
    try:
        async with get_async_db_context() as session:
            overall_total = await count_fighters_for_tapology_profile_enrichment(
                session,
                stale_days=stale_days,
            )
        total_batches = _total_batches(overall_total, batch_size)
        logger.info("Found %d fighters total for Tapology profile enrichment", overall_total)

        while True:
            async with get_async_db_context() as session:
                fighters = await select_fighters_for_tapology_profile_enrichment(
                    session,
                    batch_size=batch_size,
                    stale_days=stale_days,
                    after_id=last_seen_id,
                )

            if not fighters:
                break

            batch_index += 1
            processed_before = stats.total
            logger.info(
                "%s Found %d fighters for Tapology profile enrichment after id=%s",
                format_progress(
                    batch_index=batch_index,
                    batch_total=total_batches,
                    overall_index=min(processed_before + len(fighters), overall_total),
                    overall_total=overall_total,
                ),
                len(fighters),
                last_seen_id,
            )

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

            batch_stats = await enrich_fighter_tapology_profile_batch(
                fighters,
                client,
                save_profile,
                logger,
                crawler_fn=crawler_fn,
                batch_index=batch_index,
                batch_total=total_batches,
                processed_before=processed_before,
                overall_total=overall_total,
            )
            stats.total += batch_stats.total
            stats.matched += batch_stats.matched
            stats.updated += batch_stats.updated
            stats.skipped += batch_stats.skipped
            stats.failed += batch_stats.failed
            last_seen_id = fighters[-1].id
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


@task(
    name="tapology-bouts",
    task_run_name="tapology-bouts",
    retries=2,
    cache_policy=NO_CACHE,
)
async def enrich_match_tapology_metadata_task(
    crawler_fn: Callable | None = None,
    batch_size: int = 50,
    stale_days: int = 30,
) -> None:
    logger = get_run_logger()
    logger.info("enrich_match_tapology_metadata_task started")

    stats = TapologyBoutEnrichmentStats()
    last_seen_id: int | None = None
    batch_index = 0
    client = TapologyClient()
    try:
        async with get_async_db_context() as session:
            overall_total = await count_matches_for_tapology_bout_enrichment(
                session,
                stale_days=stale_days,
            )
        total_batches = _total_batches(overall_total, batch_size)
        logger.info("Found %d matches total for Tapology bout enrichment", overall_total)

        while True:
            async with get_async_db_context() as session:
                bouts = await select_matches_for_tapology_bout_enrichment(
                    session,
                    batch_size=batch_size,
                    stale_days=stale_days,
                    after_id=last_seen_id,
                )

            if not bouts:
                break

            batch_index += 1
            processed_before = stats.total
            logger.info(
                "%s Found %d matches for Tapology bout enrichment after id=%s",
                format_progress(
                    batch_index=batch_index,
                    batch_total=total_batches,
                    overall_index=min(processed_before + len(bouts), overall_total),
                    overall_total=overall_total,
                ),
                len(bouts),
                last_seen_id,
            )

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

            async def save_event_url(event_id: int, tapology_url: str) -> object:
                async with get_async_db_context() as session:
                    return await save_tapology_event_url(session, event_id, tapology_url)

            batch_stats = await enrich_match_tapology_metadata_batch(
                bouts,
                client,
                save_bout,
                logger,
                crawler_fn=crawler_fn,
                save_event_url=save_event_url,
                batch_index=batch_index,
                batch_total=total_batches,
                processed_before=processed_before,
                overall_total=overall_total,
            )
            stats.total += batch_stats.total
            stats.matched += batch_stats.matched
            stats.updated += batch_stats.updated
            stats.skipped += batch_stats.skipped
            stats.failed += batch_stats.failed
            last_seen_id = bouts[-1].match_id
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
    after_id: int | None = None,
) -> list[FighterSchema]:
    query = (
        select(FighterModel)
        .where(*_fighter_tapology_profile_conditions(stale_days, after_id))
        .order_by(FighterModel.id)
        .limit(batch_size)
    )

    result = await session.execute(query)
    return [fighter.to_schema() for fighter in result.scalars().all()]


async def count_fighters_for_tapology_profile_enrichment(
    session,
    *,
    stale_days: int = 30,
) -> int:
    result = await session.execute(
        select(func.count(FighterModel.id)).where(*_fighter_tapology_profile_conditions(stale_days))
    )
    return int(result.scalar_one() or 0)


async def select_matches_for_tapology_bout_enrichment(
    session,
    *,
    batch_size: int = 50,
    stale_days: int = 30,
    after_id: int | None = None,
) -> list[TapologyLocalBout]:
    query = (
        select(MatchModel, EventModel)
        .join(EventModel, EventModel.id == MatchModel.event_id)
        .where(*_match_tapology_bout_conditions(stale_days, after_id))
        .order_by(MatchModel.id)
        .limit(batch_size)
    )

    result = await session.execute(query)

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
                event_id=event.id,
                event_tapology_url=event.tapology_url,
            )
        )

    return bouts


async def count_matches_for_tapology_bout_enrichment(
    session,
    *,
    stale_days: int = 30,
) -> int:
    result = await session.execute(
        select(func.count(MatchModel.id)).where(*_match_tapology_bout_conditions(stale_days))
    )
    return int(result.scalar_one() or 0)


def _fighter_tapology_profile_conditions(stale_days: int, after_id: int | None = None):
    cutoff = utc_now() - timedelta(days=stale_days)
    conditions = [
        or_(
            FighterModel.tapology_url.is_(None),
            FighterModel.tapology_last_scraped_at.is_(None),
            FighterModel.tapology_last_scraped_at < cutoff,
        )
    ]
    if after_id is not None:
        conditions.append(FighterModel.id > after_id)
    return conditions


def _match_tapology_bout_conditions(stale_days: int, after_id: int | None = None):
    cutoff = utc_now() - timedelta(days=stale_days)
    conditions = [
        or_(
            MatchModel.tapology_bout_url.is_(None),
            MatchModel.tapology_last_scraped_at.is_(None),
            MatchModel.tapology_last_scraped_at < cutoff,
        )
    ]
    if after_id is not None:
        conditions.append(MatchModel.id > after_id)
    return conditions


def _total_batches(total_items: int, batch_size: int) -> int:
    if total_items <= 0:
        return 0
    return (total_items + batch_size - 1) // batch_size


async def enrich_fighter_tapology_profile_batch(
    fighters: list[FighterSchema],
    client: TapologyClient,
    save_profile: ProfileSaver,
    logger: logging.Logger,
    crawler_fn: Callable | None = None,
    batch_index: int | None = None,
    batch_total: int | None = None,
    processed_before: int = 0,
    overall_total: int | None = None,
) -> TapologyProfileEnrichmentStats:
    stats = TapologyProfileEnrichmentStats(total=len(fighters))
    scraped_at = utc_now()

    for index, fighter in enumerate(fighters, 1):
        logger.info(
            "%s Tapology profile enrichment: %s",
            format_progress(
                batch_index=batch_index,
                batch_total=batch_total,
                item_index=index,
                item_total=len(fighters),
                overall_index=processed_before + index,
                overall_total=overall_total,
            ),
            fighter.name,
        )

        try:
            if fighter.tapology_url:
                match_result = match_tapology_fighter_candidates(fighter, [])
            else:
                search_html = await _fetch_tapology_search_page(client, crawler_fn, fighter.name)
                if not search_html:
                    stats.failed += 1
                    logger.warning(
                        "Tapology profile search fetch failed for fighter_id=%s name=%s",
                        fighter.id,
                        fighter.name,
                    )
                    continue
                if _is_tapology_challenge_page(search_html):
                    stats.failed += 1
                    logger.warning(
                        "Tapology profile search blocked by challenge for fighter_id=%s name=%s title=%s",
                        fighter.id,
                        fighter.name,
                        _extract_html_title(search_html),
                    )
                    continue
                candidates = parse_tapology_fighter_candidates(search_html)
                if not candidates:
                    stats.skipped += 1
                    logger.warning(
                        "Skipping Tapology profile enrichment for fighter_id=%s name=%s "
                        "state=%s reason=no_candidates title=%s excerpt=%s",
                        fighter.id,
                        fighter.name,
                        MatchState.NOT_FOUND,
                        _extract_html_title(search_html),
                        _compact_html_excerpt(search_html),
                    )
                    continue
                match_result = match_tapology_fighter_candidates(
                    fighter,
                    candidates,
                )
            if match_result.state != MatchState.MATCHED or not match_result.url:
                stats.skipped += 1
                logger.warning(
                    "Skipping Tapology profile enrichment for fighter_id=%s name=%s "
                    "state=%s reason=%s candidate_count=%d candidates=%s",
                    fighter.id,
                    fighter.name,
                    match_result.state,
                    match_result.reason,
                    len(match_result.candidates),
                    _format_candidate_preview(match_result.candidates),
                )
                continue

            stats.matched += 1
            html = await _fetch_tapology_fighter_detail_page(client, crawler_fn, match_result.url)
            if not html:
                stats.failed += 1
                logger.warning("Tapology profile page fetch failed for %s", match_result.url)
                continue
            if _is_tapology_challenge_page(html):
                stats.failed += 1
                logger.warning(
                    "Tapology profile page blocked by challenge for fighter_id=%s url=%s title=%s",
                    fighter.id,
                    match_result.url,
                    _extract_html_title(html),
                )
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
    save_event_url: EventUrlSaver | None = None,
    batch_index: int | None = None,
    batch_total: int | None = None,
    processed_before: int = 0,
    overall_total: int | None = None,
) -> TapologyBoutEnrichmentStats:
    stats = TapologyBoutEnrichmentStats(total=len(bouts))
    scraped_at = utc_now()
    event_url_cache: dict[tuple[int | None, str | None, date | None], str | None] = {}
    event_page_cache: dict[str, str | None] = {}

    for index, bout in enumerate(bouts, 1):
        fighter_names = [fighter.name for fighter in bout.fighters]
        logger.info(
            "%s Tapology bout enrichment: match_id=%s fighters=%s",
            format_progress(
                batch_index=batch_index,
                batch_total=batch_total,
                item_index=index,
                item_total=len(bouts),
                overall_index=processed_before + index,
                overall_total=overall_total,
            ),
            bout.match_id,
            fighter_names,
        )

        try:
            bout_url = bout.tapology_bout_url
            if not bout_url:
                bout_url = await _resolve_tapology_bout_url_from_event_page(
                    bout,
                    client,
                    logger,
                    crawler_fn,
                    save_event_url,
                    event_url_cache,
                    event_page_cache,
                )
                if not bout_url:
                    bout_url, direct_search_failed = await _resolve_tapology_bout_url_from_direct_search(
                        bout,
                        client,
                        logger,
                        crawler_fn,
                    )
                if not bout_url:
                    if direct_search_failed:
                        stats.failed += 1
                    else:
                        stats.skipped += 1
                    continue

            stats.matched += 1
            html = await _fetch_tapology_bout_detail_page(client, crawler_fn, bout_url)
            if not html:
                stats.failed += 1
                logger.warning("Tapology bout page fetch failed for %s", bout_url)
                continue
            if _is_tapology_challenge_page(html):
                stats.failed += 1
                logger.warning(
                    "Tapology bout page blocked by challenge for match_id=%s url=%s title=%s",
                    bout.match_id,
                    bout_url,
                    _extract_html_title(html),
                )
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


async def _resolve_tapology_bout_url_from_event_page(
    bout: TapologyLocalBout,
    client: TapologyClient,
    logger: logging.Logger,
    crawler_fn: Callable | None,
    save_event_url: EventUrlSaver | None,
    event_url_cache: dict[tuple[int | None, str | None, date | None], str | None],
    event_page_cache: dict[str, str | None],
) -> str | None:
    fighter_names = [fighter.name for fighter in bout.fighters]
    event_url = await _resolve_tapology_event_url(
        bout,
        client,
        logger,
        crawler_fn,
        save_event_url,
        event_url_cache,
    )
    if not event_url:
        return None

    if event_url in event_page_cache:
        event_html = event_page_cache[event_url]
    else:
        event_html = await _fetch_tapology_event_detail_page(client, crawler_fn, event_url)
        event_page_cache[event_url] = event_html

    if not event_html:
        logger.warning(
            "Tapology event page fetch failed for match_id=%s event=%s event_url=%s",
            bout.match_id,
            bout.event_name,
            event_url,
        )
        return None
    if _is_tapology_challenge_page(event_html):
        logger.warning(
            "Tapology event page blocked by challenge for match_id=%s event=%s event_url=%s title=%s",
            bout.match_id,
            bout.event_name,
            event_url,
            _extract_html_title(event_html),
        )
        return None

    candidates = parse_tapology_bout_candidates(event_html)
    for candidate in candidates:
        if candidate.parsed_date is None:
            candidate.parsed_date = bout.event_date
    match_result = match_tapology_bout(
        candidates,
        fighter_names=fighter_names,
        event_date=bout.event_date,
        event_name=bout.event_name,
    )
    if match_result.state == MatchState.MATCHED and match_result.url:
        logger.info(
            "Tapology bout matched from event page match_id=%s event_url=%s bout_url=%s",
            bout.match_id,
            event_url,
            match_result.url,
        )
        return match_result.url

    logger.warning(
        "Skipping Tapology event-page bout match for match_id=%s state=%s reason=%s "
        "event_url=%s candidate_count=%d candidates=%s",
        bout.match_id,
        match_result.state,
        match_result.reason,
        event_url,
        len(match_result.candidates),
        _format_candidate_preview(match_result.candidates),
    )
    return None


async def _resolve_tapology_event_url(
    bout: TapologyLocalBout,
    client: TapologyClient,
    logger: logging.Logger,
    crawler_fn: Callable | None,
    save_event_url: EventUrlSaver | None,
    event_url_cache: dict[tuple[int | None, str | None, date | None], str | None],
) -> str | None:
    if bout.event_tapology_url:
        return bout.event_tapology_url
    if not bout.event_name:
        return None

    cache_key = (bout.event_id, bout.event_name, bout.event_date)
    if cache_key in event_url_cache:
        return event_url_cache[cache_key]

    search_html = await _fetch_tapology_search_page(client, crawler_fn, bout.event_name)
    if not search_html:
        logger.warning(
            "Tapology event search fetch failed for match_id=%s event=%s",
            bout.match_id,
            bout.event_name,
        )
        event_url_cache[cache_key] = None
        return None
    if _is_tapology_challenge_page(search_html):
        logger.warning(
            "Tapology event search blocked by challenge for match_id=%s event=%s title=%s",
            bout.match_id,
            bout.event_name,
            _extract_html_title(search_html),
        )
        event_url_cache[cache_key] = None
        return None

    candidates = parse_tapology_event_candidates(search_html)
    match_result = match_tapology_event_candidates(
        candidates,
        event_name=bout.event_name,
        event_date=bout.event_date,
    )
    if match_result.state == MatchState.MATCHED and match_result.url:
        event_url_cache[cache_key] = match_result.url
        if bout.event_id is not None and save_event_url is not None:
            await save_event_url(bout.event_id, match_result.url)
        logger.info(
            "Tapology event matched for match_id=%s event=%s event_url=%s",
            bout.match_id,
            bout.event_name,
            match_result.url,
        )
        return match_result.url

    logger.warning(
        "Tapology event match skipped for match_id=%s event=%s state=%s reason=%s "
        "candidate_count=%d candidates=%s",
        bout.match_id,
        bout.event_name,
        match_result.state,
        match_result.reason,
        len(match_result.candidates),
        _format_candidate_preview(match_result.candidates),
    )
    event_url_cache[cache_key] = None
    return None


async def _resolve_tapology_bout_url_from_direct_search(
    bout: TapologyLocalBout,
    client: TapologyClient,
    logger: logging.Logger,
    crawler_fn: Callable | None,
) -> tuple[str | None, bool]:
    fighter_names = [fighter.name for fighter in bout.fighters]
    search_term = _build_bout_search_term(bout)
    search_html = await _fetch_tapology_search_page(client, crawler_fn, search_term)
    if not search_html:
        logger.warning(
            "Tapology bout search fetch failed for match_id=%s fighters=%s event=%s search_term=%s",
            bout.match_id,
            fighter_names,
            bout.event_name,
            search_term,
        )
        return None, True
    if _is_tapology_challenge_page(search_html):
        logger.warning(
            "Tapology bout search blocked by challenge for match_id=%s fighters=%s event=%s "
            "search_term=%s title=%s",
            bout.match_id,
            fighter_names,
            bout.event_name,
            search_term,
            _extract_html_title(search_html),
        )
        return None, True

    candidates = parse_tapology_bout_candidates(search_html)
    if not candidates:
        logger.warning(
            "Skipping Tapology direct bout search for match_id=%s state=%s reason=no_candidates "
            "search_term=%s title=%s excerpt=%s",
            bout.match_id,
            MatchState.NOT_FOUND,
            search_term,
            _extract_html_title(search_html),
            _compact_html_excerpt(search_html),
        )
        return None, False

    match_result = match_tapology_bout(
        candidates,
        fighter_names=fighter_names,
        event_date=bout.event_date,
        event_name=bout.event_name,
    )
    if match_result.state == MatchState.MATCHED and match_result.url:
        logger.info(
            "Tapology bout matched from direct search match_id=%s search_term=%s bout_url=%s",
            bout.match_id,
            search_term,
            match_result.url,
        )
        return match_result.url, False

    logger.warning(
        "Skipping Tapology direct bout match for match_id=%s state=%s reason=%s "
        "search_term=%s candidate_count=%d candidates=%s",
        bout.match_id,
        match_result.state,
        match_result.reason,
        search_term,
        len(match_result.candidates),
        _format_candidate_preview(match_result.candidates),
    )
    return None, False


def _is_tapology_challenge_page(html: str | None) -> bool:
    if not html:
        return False
    normalized = html.lower()
    return any(marker in normalized for marker in _TAPOLOGY_CHALLENGE_MARKERS)


def _extract_html_title(html: str | None) -> str | None:
    if not html:
        return None
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip() or None


def _compact_html_excerpt(html: str, *, limit: int = 160) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _format_candidate_preview(candidates: list | tuple) -> str:
    preview = []
    for candidate in candidates[:3]:
        text = (
            getattr(candidate, "display_name", None)
            or getattr(candidate, "text", None)
            or getattr(candidate, "url", "")
        )
        preview.append(str(text))
    return " | ".join(preview)


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


async def _fetch_tapology_event_detail_page(
    client: TapologyClient,
    crawler_fn: Callable | None,
    path_or_url: str,
) -> str | None:
    if crawler_fn:
        return await crawler_fn(path_or_url)
    return await asyncio.to_thread(client.fetch_event_detail_page, path_or_url)
