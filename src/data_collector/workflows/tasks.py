import asyncio
import random
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
from data_collector.scripts.scrape_nationality import (
    slugify_name,
    parse_hometown_from_html,
    extract_nationality,
)

RANDOM_DELAY = random.randint(1, 5)


@task(retries=3, cache_policy=NO_CACHE)
async def scrap_all_fighter_task(crawler_fn: Callable) -> None:
    logger = get_run_logger()
    logger.info("scrap_all_fighter_task started")
    for char in 'abcdefghijklmnopqrstuvwxyz':
        await asyncio.sleep(RANDOM_DELAY)
        logger.info(f"[{char}] fighters scraping started")
        fighters_url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        try:
            fighter_schema_list = await scrap_fighters(crawler_fn, fighters_url)
            logger.info(f"[{char}] fighters scraping completed : {len(fighter_schema_list)} fighters collected")
        except Exception as e:
            logger.error(f"[{char}] fighters scraping failed: {str(e)}")
            logger.error(format_exc())

        try:
            async with get_async_db_context() as session:
                await save_fighters(session, fighter_schema_list)
            logger.info(f"[{char}] fighters scraping completed : {len(fighter_schema_list)} fighters saved")
        except Exception as e:
            logger.error(f"[{char}] fighters scraping failed: {str(e)}")
            logger.error(format_exc())
    logger.info("scrap_all_fighter_task completed")


@task(retries=3, cache_policy=NO_CACHE)
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

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} events)")

        try:
            async with get_async_db_context() as session:
                await save_events(session, batch)
            saved_count += len(batch)
            logger.info(f"Batch {batch_num}/{total_batches} completed: {len(batch)} events saved")
        except Exception as e:
            logger.error(f"Batch {batch_num}/{total_batches} failed: {str(e)}")
            logger.error(format_exc())
            continue

    logger.info(f"scrap_all_events_task completed: {saved_count}/{total_events} events saved")

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
        logger.info(f"[{idx+1}/{total_events}] - event_id: {event.id} event detail scraping started")
        event_url = event.url
        event_id = event.id

        try:
            matches_data = await scrap_event_detail(crawler_fn, event_url, event_id, fighter_name_to_id_map)
        except Exception as e:
            logger.error(f"[{idx+1}/{total_events}] - event_id: {event_id} event detail scraping failed: {str(e)}")
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
                logger.error(f"[{idx+1}/{total_events}] - event_id: {event_id} event detail scraping failed: {str(e)}")
                logger.error(format_exc())
                return
            logger.info(f"[{idx+1}/{total_events}] - event_id: {event_id} event detail scraping completed : {saved_match_count} matches saved")

@task(retries=3, cache_policy=NO_CACHE)
async def scrap_event_detail_task(crawler_fn: Callable) -> None:
    logger = get_run_logger()
    logger.info("scrap_event_detail_task started")
    async with get_async_db_context() as session:
        events_list = await get_events(session)
        all_fighters = await get_all_fighter(session, page_size=None)

    fighter_name_to_id_map = {fighter.name: fighter.id for fighter in all_fighters}

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

        async with get_async_db_context() as session:
            try:
                match_statistics_list = await scrap_match_basic_statistics(
                    crawler_fn, detail_url, fighter_name_to_id_map, fighter_matches
                )
                await save_basic_match_stat(session, match_statistics_list)
                logger.info(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} BasicMatchStat scraping completed")
            except Exception as e:
                logger.error(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} BasicMatchStat scraping failed: {str(e)}")
                logger.error(format_exc())

            try:
                strike_details_list = await scrap_match_significant_strikes(
                    crawler_fn, detail_url, fighter_name_to_id_map, fighter_matches
                )
                await save_sig_str_match_stat(session, strike_details_list)
                logger.info(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} SigStrMatchStat scraping completed")
            except Exception as e:
                logger.error(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} SigStrMatchStat scraping failed: {str(e)}")
                logger.error(format_exc())

        logger.info(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} match detail scraping completed")


@task(retries=3, cache_policy=NO_CACHE)
async def scrap_match_detail_task(crawler_fn: Callable) -> None:
    logger = get_run_logger()
    logger.info("scrap_match_detail_task started")

    async with get_async_db_context() as session:
        all_fighters = await get_all_fighter(session, page_size=None)
        fighter_match_dict = await get_match_fighter_mapping(session)

    fighter_name_to_id_map = {fighter.name: fighter.id for fighter in all_fighters}

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


@task(retries=3, cache_policy=NO_CACHE)
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
            await delete_all_rankings(session)
            await save_rankings(session, rankings)
            logger.info(f"scrap_rankings_task completed : {len(rankings)} rankings saved")
        except Exception as e:
            logger.error(f"scrap_rankings_task failed: {str(e)}")
            logger.error(format_exc())


@task(retries=2, cache_policy=NO_CACHE)
async def enrich_fighter_nationality_task(crawler_fn: Callable) -> None:
    logger = get_run_logger()
    logger.info("enrich_fighter_nationality_task started")

    async with get_async_db_context() as session:
        result = await session.execute(
            select(FighterModel.id, FighterModel.name)
            .where(FighterModel.nationality.is_(None))
            .order_by(FighterModel.id)
        )
        fighters = result.all()

    logger.info(f"Found {len(fighters)} fighters without nationality")
    if not fighters:
        logger.info("Nothing to enrich. Skipping.")
        return

    success_count = 0
    for i, (fighter_id, name) in enumerate(fighters, 1):
        logger.info(f"[{i}/{len(fighters)}] Processing: {name} (id={fighter_id})")
        profile_url = f"https://www.ufc.com/athlete/{slugify_name(name)}"

        try:
            html = await crawler_fn(profile_url)
        except Exception as e:
            logger.warning(f"  -> Request failed for {profile_url}: {e}")
            await asyncio.sleep(random.uniform(1.0, 2.0))
            continue

        if not html:
            logger.warning(f"  -> No response from {profile_url}")
            await asyncio.sleep(random.uniform(1.0, 2.0))
            continue

        hometown = parse_hometown_from_html(html)
        if not hometown:
            logger.warning(f"  -> No hometown found at {profile_url}")
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
        logger.info(f"  -> {nationality} (hometown: {hometown})")

        await asyncio.sleep(random.uniform(1.0, 2.0))

    logger.info(f"enrich_fighter_nationality_task completed: {success_count}/{len(fighters)} updated")


@task(retries=2, cache_policy=NO_CACHE)
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
        logger.info(f"[{i}/{len(locations)}] Geocoding: {loc}")
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
