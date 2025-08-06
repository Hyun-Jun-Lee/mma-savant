import asyncio
import random
from typing import List, Callable
from traceback import format_exc

from prefect import task
from prefect.logging import get_run_logger
from prefect.cache_policies import NO_CACHE

from fighter.repositories import get_all_fighter, delete_all_rankings
from event.repositories import get_events
from match.repositories import get_match_fighter_mapping
from event.models import EventSchema
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

RANDOM_DELAY = random.randint(1, 5)

try:
    LOGGER = get_run_logger()
except Exception as e:
    import logging
    LOGGER = logging.getLogger(__name__)
    if not LOGGER.handlers:  # 중복 핸들러 추가 방지
        handler = logging.StreamHandler()  # 콘솔 출력 핸들러
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        LOGGER.addHandler(handler)
        LOGGER.setLevel(logging.INFO)  # 로그 레벨 설정

@task(retries=3, cache_policy=NO_CACHE)
async def scrap_all_fighter_task(session, crawler_fn : Callable)-> None:
    LOGGER.info("scrap_all_fighter_task started")
    for char in 'abcdefghijklmnopqrstuvwxyz':
        await asyncio.sleep(RANDOM_DELAY)
        LOGGER.info(f"[{char}] fighters scraping started")
        fighters_url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        try:
            fighter_schema_list = await scrap_fighters(crawler_fn, fighters_url)
            await save_fighters(session, fighter_schema_list)
            LOGGER.info(f"[{char}] fighters scraping completed : {len(fighter_schema_list)} fighters saved")
        except Exception as e:
            LOGGER.error(f"[{char}] fighters scraping failed: {str(e)}")
            LOGGER.error(format_exc())

    LOGGER.info("scrap_all_fighter_task completed")


@task(retries=3, cache_policy=NO_CACHE)
async def scrap_all_events_task(session, crawler_fn : Callable) -> None:
    all_events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    try:
        LOGGER.info("scrap_all_events_task started")
        event_schema_list = await scrap_all_events(crawler_fn, all_events_url)
        await save_events(session, event_schema_list)
        LOGGER.info(f"scrap_all_events_task completed : {len(event_schema_list)} events saved")
    except Exception as e:
        LOGGER.error(f"scrap_all_events_task failed: {str(e)}")
        LOGGER.error(format_exc())

async def process_event_detail(
    idx: int,
    event: EventSchema,
    crawler_fn: Callable,
    fighter_name_to_id_map: dict,
    session,
    total_events: int,
    semaphore: asyncio.Semaphore
) -> None:
    async with semaphore:
        await asyncio.sleep(RANDOM_DELAY)
        LOGGER.info(f"[{idx+1}/{total_events}] - event_id: {event.id} event detail scraping started")
        event_url = event.url
        event_id = event.id

        try:
            matches_data = await scrap_event_detail(crawler_fn, event_url, event_id, fighter_name_to_id_map)
        except Exception as e:
            LOGGER.error(f"[{idx+1}/{total_events}] - event_id: {event_id} event detail scraping failed: {str(e)}")
            LOGGER.error(format_exc())
            return

        saved_match_count = 0
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
            saved_match_count += len(saved_match)
        LOGGER.info(f"[{idx+1}/{total_events}] - event_id: {event_id} event detail scraping completed : {saved_match_count} matches saved")

@task(retries=3, cache_policy=NO_CACHE)
async def scrap_event_detail_task(session, crawler_fn : Callable) -> None:
    LOGGER.info("scrap_event_detail_task started")
    events_list = await get_events(session)
    all_fighters = await get_all_fighter(session)
    fighter_name_to_id_map = {fighter.name: fighter.id for fighter in all_fighters}

    semaphore = asyncio.Semaphore(3)

    tasks = [
        process_event_detail(idx, event, crawler_fn, fighter_name_to_id_map, session, len(events_list), semaphore)
        for idx, event in enumerate(events_list)
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

    LOGGER.info("scrap_event_detail_task completed")


async def process_detail_url(
    idx: int,
    detail_url: str,
    fighter_matches: dict,
    crawler_fn: Callable,
    fighter_name_to_id_map: dict,
    session,
    total_urls: int,
    semaphore: asyncio.Semaphore
) -> None:
    async with semaphore:  # 동시 실행 제한
        await asyncio.sleep(RANDOM_DELAY)
        if not detail_url:
            return

        # 매치 기본 통계 정보 스크랩 및 저장
        try:
            match_statistics_list = await scrap_match_basic_statistics(crawler_fn, detail_url, fighter_name_to_id_map, fighter_matches)
            await save_basic_match_stat(session, match_statistics_list)
            LOGGER.info(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} BasicMatchStat scraping completed")
        except Exception as e:
            LOGGER.error(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} BasicMatchStat scraping failed: {str(e)}")
            LOGGER.error(format_exc())

        # 매치 스트라이크 상세 정보 스크랩 및 저장
        try:
            strike_details_list = await scrap_match_significant_strikes(crawler_fn, detail_url, fighter_name_to_id_map, fighter_matches)
            await save_sig_str_match_stat(session, strike_details_list)
            LOGGER.info(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} SigStrMatchStat scraping completed")
        except Exception as e:
            LOGGER.error(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} SigStrMatchStat scraping failed: {str(e)}")
            LOGGER.error(format_exc())

        LOGGER.info(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} match detail scraping completed")


@task(retries=3, cache_policy=NO_CACHE)
async def scrap_match_detail_task(session, crawler_fn : Callable)-> None:
    """
    매치 상세 정보를 스크랩하는 태스크
    """
    LOGGER.info("scrap_match_detail_task started")
    all_fighters = await get_all_fighter(session)
    fighter_name_to_id_map = {fighter.name: fighter.id for fighter in all_fighters}
    fighter_match_dict = await get_match_fighter_mapping(session)

    # 최대 5개의 동시 요청을 허용하는 Semaphore
    semaphore = asyncio.Semaphore(3)

    # 모든 URL에 대해 비동기 작업 생성
    tasks = [
        process_detail_url(idx, detail_url, fighter_matches, crawler_fn, fighter_name_to_id_map, session, len(fighter_match_dict), semaphore)
        for idx, (detail_url, fighter_matches) in enumerate(fighter_match_dict.items())
    ]

    # 모든 작업을 동시에 실행
    await asyncio.gather(*tasks, return_exceptions=True)

    LOGGER.info("scrap_match_detail_task completed")

@task(retries=3, cache_policy=NO_CACHE)
async def scrap_rankings_task(session, crawler_fn : Callable)-> None:
    """
    UFC 랭킹을 스크랩하는 태스크
    """
    LOGGER.info("scrap_rankings_task started")
    try:
        rankings = await scrap_rankings(session, crawler_fn)
        # ranking은 full clean
        await delete_all_rankings(session)
        await save_rankings(session, rankings)
        LOGGER.info(f"scrap_rankings_task completed : {len(rankings)} rankings saved")
    except Exception as e:
        LOGGER.error(f"scrap_rankings_task failed: {str(e)}")
        LOGGER.error(format_exc())