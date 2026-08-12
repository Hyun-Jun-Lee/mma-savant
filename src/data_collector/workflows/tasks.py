import asyncio
import random
from collections import defaultdict
from typing import List, Callable
from traceback import format_exc
import logging

from prefect import task
from prefect.logging import get_run_logger
from prefect.cache_policies import NO_CACHE
from sqlalchemy import select, update, distinct

from database.connection.postgres_conn import get_async_db_context
from fighter.repositories import get_all_fighter, delete_all_rankings
from fighter.models import FighterModel
from event.repositories import get_events
from event.models import EventSchema, EventModel
from match.repositories import get_match_fighter_mapping
from data_collector.scrapers import (
    scrap_fighters,
    scrap_all_events,
    scrap_event_detail,
    scrap_match_basic_statistics,
    scrap_match_significant_strikes,
    scrap_rankings
)
from data_collector.workflows.data_store import (
    save_fighters,
    save_events,
    save_match,
    save_fighter_match,
    save_basic_match_stat,
    save_sig_str_match_stat,
    save_rankings
)
from data_collector.workflows.progress import format_progress
from data_collector.workflows.tapology_tasks import (
    enrich_fighter_tapology_profile_task,
    enrich_match_tapology_metadata_task,
)
from data_collector.clients import TapologyClient
from data_collector.scripts.scrape_nationality import (
    slugify_name,
    parse_hometown_from_html,
    extract_nationality,
    fetch_nationality_from_tapology,
)

RANDOM_DELAY = random.randint(1, 5)


def build_fighter_lookup(fighters):
    fighter_lookup = defaultdict(list)
    for fighter in fighters:
        fighter_lookup[fighter.name.lower().strip()].append(fighter)
    return dict(fighter_lookup)


async def replace_rankings_if_not_empty(session, rankings, logger: logging.Logger) -> bool:
    if not rankings:
        logger.warning("No rankings collected; preserving existing ranking table")
        return False

    await delete_all_rankings(session)
    await save_rankings(session, rankings)
    return True


@task(
    name="fighters",
    task_run_name="fighters",
    retries=3,
    cache_policy=NO_CACHE,
)
async def scrap_all_fighter_task(crawler_fn: Callable) -> None:
    logger = get_run_logger()
    logger.info("scrap_all_fighter_task started")
    chars = 'abcdefghijklmnopqrstuvwxyz'
    for index, char in enumerate(chars, 1):
        await asyncio.sleep(RANDOM_DELAY)
        progress = format_progress(overall_index=index, overall_total=len(chars))
        logger.info("%s fighters scraping started: char=%s", progress, char)
        fighters_url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        try:
            fighter_schema_list = await scrap_fighters(crawler_fn, fighters_url)
            logger.info("%s fighters scraping completed: char=%s collected=%d", progress, char, len(fighter_schema_list))
        except Exception as e:
            logger.error("%s fighters scraping failed: char=%s error=%s", progress, char, str(e))
            logger.error(format_exc())

        try:
            async with get_async_db_context() as session:
                await save_fighters(session, fighter_schema_list)
            logger.info("%s fighters scraping saved: char=%s saved=%d", progress, char, len(fighter_schema_list))
        except Exception as e:
            logger.error("%s fighters scraping save failed: char=%s error=%s", progress, char, str(e))
            logger.error(format_exc())
    logger.info("scrap_all_fighter_task completed")


@task(
    name="events",
    task_run_name="events",
    retries=3,
    cache_policy=NO_CACHE,
)
async def scrap_all_events_task(crawler_fn: Callable, batch_size: int = 30) -> None:
    logger = get_run_logger()
    all_events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    try:
        logger.info("scrap_all_events_task started")
        event_schema_list = await scrap_all_events(crawler_fn, all_events_url)
    except Exception as e:
        logger.error(f"scrap_all_events_task failed: {str(e)}")
        logger.error(format_exc())
        return

    total_events = len(event_schema_list)
    saved_count = 0

    for i in range(0, total_events, batch_size):
        batch = event_schema_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_events + batch_size - 1) // batch_size

        progress = format_progress(
            batch_index=batch_num,
            batch_total=total_batches,
            overall_index=min(i + len(batch), total_events),
            overall_total=total_events,
        )
        logger.info("%s Processing events batch: size=%d", progress, len(batch))

        try:
            async with get_async_db_context() as session:
                await save_events(session, batch)
            saved_count += len(batch)
            logger.info("%s Events batch completed: saved=%d", progress, len(batch))
        except Exception as e:
            logger.error("%s Events batch failed: error=%s", progress, str(e))
            logger.error(format_exc())
            continue

    logger.info(f"scrap_all_events_task completed: {saved_count}/{total_events} events saved")


@task(
    name="upcoming-events",
    task_run_name="upcoming-events",
    retries=3,
    cache_policy=NO_CACHE,
)
async def scrap_upcoming_events_task(crawler_fn: Callable, batch_size: int = 30) -> None:
    logger = get_run_logger()
    upcoming_events_url = "http://ufcstats.com/statistics/events/upcoming?page=all"
    try:
        logger.info("scrap_upcoming_events_task started")
        event_schema_list = await scrap_all_events(crawler_fn, upcoming_events_url)
    except Exception as e:
        logger.error(f"scrap_upcoming_events_task failed: {str(e)}")
        logger.error(format_exc())
        return

    total_events = len(event_schema_list)
    saved_count = 0

    for i in range(0, total_events, batch_size):
        batch = event_schema_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_events + batch_size - 1) // batch_size

        progress = format_progress(
            batch_index=batch_num,
            batch_total=total_batches,
            overall_index=min(i + len(batch), total_events),
            overall_total=total_events,
        )
        logger.info("%s Processing upcoming events batch: size=%d", progress, len(batch))

        try:
            async with get_async_db_context() as session:
                await save_events(session, batch)
            saved_count += len(batch)
            logger.info("%s Upcoming events batch completed: saved=%d", progress, len(batch))
        except Exception as e:
            logger.error("%s Upcoming events batch failed: error=%s", progress, str(e))
            logger.error(format_exc())
            continue

    logger.info(f"scrap_upcoming_events_task completed: {saved_count}/{total_events} upcoming events saved")


async def process_event_detail(
    idx: int,
    event: EventSchema,
    crawler_fn: Callable,
    fighter_name_to_id_map: dict,
    total_events: int,
    semaphore: asyncio.Semaphore,
    logger: logging.Logger,
    ) -> None:
    async with semaphore:
        await asyncio.sleep(RANDOM_DELAY)
        progress = format_progress(overall_index=idx + 1, overall_total=total_events)
        logger.info("%s event detail scraping started: event_id=%s", progress, event.id)
        event_url = event.url
        event_id = event.id

        try:
            matches_data = await scrap_event_detail(crawler_fn, event_url, event_id, fighter_name_to_id_map)
        except Exception as e:
            logger.error("%s event detail scraping failed: event_id=%s error=%s", progress, event_id, str(e))
            logger.error(format_exc())
            return

        async with get_async_db_context() as session:
            saved_match_count = 0
            try:
                for match_data in matches_data:
                    match = match_data["match"]
                    saved_match = await save_match(session, match)
                    match_id = saved_match.id
                    detail_url = saved_match.detail_url if saved_match.detail_url else None
                    if not detail_url:
                        continue

                    for fighter_info in match_data["fighters"]:
                        fighter_id = fighter_info["fighter_id"]
                        result = fighter_info["result"]
                        await save_fighter_match(session, fighter_id, match_id, result)
                    saved_match_count += 1
            except Exception as e:
                logger.error("%s event detail scraping failed: event_id=%s error=%s", progress, event_id, str(e))
                logger.error(format_exc())
                return
            logger.info("%s event detail scraping completed: event_id=%s saved_matches=%d", progress, event_id, saved_match_count)

@task(
    name="event-detail",
    task_run_name="event-detail",
    retries=3,
    cache_policy=NO_CACHE,
)
async def scrap_event_detail_task(crawler_fn: Callable) -> None:
    logger = get_run_logger()
    logger.info("scrap_event_detail_task started")
    async with get_async_db_context() as session:
        events_list = await get_events(session)
        all_fighters = await get_all_fighter(session, page_size=None)

    fighter_name_to_id_map = build_fighter_lookup(all_fighters)

    semaphore = asyncio.Semaphore(3)

    tasks = [
        process_event_detail(idx, event, crawler_fn, fighter_name_to_id_map, len(events_list), semaphore, logger)
        for idx, event in enumerate(events_list)
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("scrap_event_detail_task completed")


async def process_detail_url(
    idx: int,
    detail_url: str,
    fighter_matches: dict,
    crawler_fn: Callable,
    fighter_name_to_id_map: dict,
    total_urls: int,
    semaphore: asyncio.Semaphore,
    logger: logging.Logger,
    ) -> None:
    async with semaphore:
        await asyncio.sleep(RANDOM_DELAY)
        if not detail_url:
            return
        progress = format_progress(overall_index=idx + 1, overall_total=total_urls)

        async with get_async_db_context() as session:
            try:
                match_statistics_list = await scrap_match_basic_statistics(
                    crawler_fn, detail_url, fighter_name_to_id_map, fighter_matches
                )
                await save_basic_match_stat(session, match_statistics_list)
                logger.info("%s BasicMatchStat scraping completed: detail_url=%s", progress, detail_url)
            except Exception as e:
                logger.error("%s BasicMatchStat scraping failed: detail_url=%s error=%s", progress, detail_url, str(e))
                logger.error(format_exc())

            try:
                strike_details_list = await scrap_match_significant_strikes(
                    crawler_fn, detail_url, fighter_name_to_id_map, fighter_matches
                )
                await save_sig_str_match_stat(session, strike_details_list)
                logger.info("%s SigStrMatchStat scraping completed: detail_url=%s", progress, detail_url)
            except Exception as e:
                logger.error("%s SigStrMatchStat scraping failed: detail_url=%s error=%s", progress, detail_url, str(e))
                logger.error(format_exc())

        logger.info("%s match detail scraping completed: detail_url=%s", progress, detail_url)


@task(
    name="match-detail",
    task_run_name="match-detail",
    retries=3,
    cache_policy=NO_CACHE,
)
async def scrap_match_detail_task(crawler_fn: Callable) -> None:
    logger = get_run_logger()
    logger.info("scrap_match_detail_task started")

    async with get_async_db_context() as session:
        all_fighters = await get_all_fighter(session, page_size=None)
        fighter_match_dict = await get_match_fighter_mapping(session)

    fighter_name_to_id_map = build_fighter_lookup(all_fighters)

    semaphore = asyncio.Semaphore(3)

    tasks = [
        process_detail_url(
            idx, detail_url, fighter_matches, crawler_fn,
            fighter_name_to_id_map, len(fighter_match_dict), semaphore, logger
        )
        for idx, (detail_url, fighter_matches) in enumerate(fighter_match_dict.items())
    ]

    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("scrap_match_detail_task completed")


@task(
    name="rankings",
    task_run_name="rankings",
    retries=3,
    cache_policy=NO_CACHE,
)
async def scrap_rankings_task(crawler_fn: Callable) -> None:
    logger = get_run_logger()
    logger.info("scrap_rankings_task started")

    async with get_async_db_context() as session:
        try:
            rankings = await scrap_rankings(session, crawler_fn)
            logger.info(f"scrap_rankings_task completed : {len(rankings)} rankings collected")
        except Exception as e:
            logger.error(f"scrap_rankings_task failed: {str(e)}")
            logger.error(format_exc())
            return

        try:
            saved = await replace_rankings_if_not_empty(session, rankings, logger)
            if saved:
                logger.info(f"scrap_rankings_task completed : {len(rankings)} rankings saved")
        except Exception as e:
            logger.error(f"scrap_rankings_task failed: {str(e)}")
            logger.error(format_exc())


@task(
    name="nationality",
    task_run_name="nationality",
    retries=2,
    cache_policy=NO_CACHE,
)
async def enrich_fighter_nationality_task(crawler_fn: Callable) -> None:
    """Tapology를 1차 소스로 사용하고, UFC.com을 fallback으로 사용한다."""
    logger = get_run_logger()
    logger.info("enrich_fighter_nationality_task started")

    async with get_async_db_context() as session:
        result = await session.execute(
            select(FighterModel.id, FighterModel.name, FighterModel.nickname)
            .where(FighterModel.nationality.is_(None))
            .order_by(FighterModel.id)
        )
        fighters = result.all()

    logger.info(f"Found {len(fighters)} fighters without nationality")
    if not fighters:
        logger.info("Nothing to enrich. Skipping.")
        return

    success_count = 0
    tapology_count = 0
    ufc_count = 0

    tapology_client = TapologyClient()
    try:
        for i, (fighter_id, name, nickname) in enumerate(fighters, 1):
            progress = format_progress(overall_index=i, overall_total=len(fighters))
            logger.info("%s Processing fighter nationality: name=%s id=%s", progress, name, fighter_id)

            # 1) Tapology (MMA 전문 DB, 높은 커버리지)
            nationality = await fetch_nationality_from_tapology(
                name, nickname, client=tapology_client, crawler_fn=crawler_fn,
            )
            if nationality:
                async with get_async_db_context() as session:
                    await session.execute(
                        update(FighterModel)
                        .where(FighterModel.id == fighter_id)
                        .values(nationality=nationality)
                    )
                    await session.commit()
                success_count += 1
                tapology_count += 1
                logger.info(f"  -> {nationality} (via Tapology)")
                await asyncio.sleep(random.uniform(2.0, 4.0))
                continue

            # 2) Fallback: UFC.com
            profile_url = f"https://www.ufc.com/athlete/{slugify_name(name)}"
            try:
                html = await crawler_fn(profile_url)
            except Exception as e:
                logger.warning(f"  -> UFC.com request failed for {profile_url}: {e}")
                await asyncio.sleep(random.uniform(1.0, 2.0))
                continue

            if not html:
                logger.warning(f"  -> No response from {profile_url}")
                await asyncio.sleep(random.uniform(1.0, 2.0))
                continue

            hometown = parse_hometown_from_html(html)
            if not hometown:
                logger.warning(f"  -> No data from Tapology or UFC.com")
                await asyncio.sleep(random.uniform(1.0, 2.0))
                continue

            nationality = extract_nationality(hometown)
            if not nationality:
                logger.warning(f"  -> Could not extract nationality from: {hometown}")
                await asyncio.sleep(random.uniform(1.0, 2.0))
                continue

            async with get_async_db_context() as session:
                await session.execute(
                    update(FighterModel)
                    .where(FighterModel.id == fighter_id)
                    .values(nationality=nationality)
                )
                await session.commit()
            success_count += 1
            ufc_count += 1
            logger.info(f"  -> {nationality} (via UFC.com, hometown: {hometown})")

            await asyncio.sleep(random.uniform(1.0, 2.0))

    finally:
        tapology_client.close()

    logger.info(
        f"enrich_fighter_nationality_task completed: {success_count}/{len(fighters)} updated "
        f"(Tapology: {tapology_count}, UFC.com: {ufc_count})"
    )


@task(
    name="event-geocoding",
    task_run_name="event-geocoding",
    retries=2,
    cache_policy=NO_CACHE,
)
async def enrich_event_geocoding_task() -> None:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter

    logger = get_run_logger()
    logger.info("enrich_event_geocoding_task started")

    async with get_async_db_context() as session:
        result = await session.execute(
            select(distinct(EventModel.location))
            .where(EventModel.latitude.is_(None))
            .where(EventModel.location.isnot(None))
        )
        locations = [row[0] for row in result.all()]

    logger.info(f"Found {len(locations)} unique locations to geocode")
    if not locations:
        logger.info("Nothing to geocode. Skipping.")
        return

    geolocator = Nominatim(user_agent="mma-savant-geocoder", timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)

    success_count = 0
    for i, loc in enumerate(locations, 1):
        progress = format_progress(overall_index=i, overall_total=len(locations))
        logger.info("%s Geocoding: location=%s", progress, loc)
        try:
            result = await asyncio.to_thread(geocode, loc)
        except Exception as e:
            logger.error(f"  -> Error: {e}")
            continue

        if not result:
            logger.warning(f"  -> No result found")
            continue

        lat, lng = result.latitude, result.longitude
        async with get_async_db_context() as session:
            await session.execute(
                update(EventModel)
                .where(EventModel.location == loc)
                .values(latitude=lat, longitude=lng)
            )
            await session.commit()
        success_count += 1
        logger.info(f"  -> ({lat:.4f}, {lng:.4f})")

    logger.info(f"enrich_event_geocoding_task completed: {success_count}/{len(locations)} locations geocoded")
