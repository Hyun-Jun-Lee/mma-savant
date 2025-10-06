import asyncio
import random
from typing import List, Callable
from traceback import format_exc

from prefect import task
from prefect.logging import get_run_logger
from prefect.cache_policies import NO_CACHE

from database.connection.postgres_conn import get_async_db_context
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
async def scrap_all_fighter_task(crawler_fn : Callable)-> None:
    LOGGER.info("scrap_all_fighter_task started")
    for char in 'abcdefghijklmnopqrstuvwxyz':
        await asyncio.sleep(RANDOM_DELAY)
        LOGGER.info(f"[{char}] fighters scraping started")
        fighters_url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        try:
            fighter_schema_list = await scrap_fighters(crawler_fn, fighters_url)
            LOGGER.info(f"[{char}] fighters scraping completed : {len(fighter_schema_list)} fighters collected")
        except Exception as e:
            LOGGER.error(f"[{char}] fighters scraping failed: {str(e)}")
            LOGGER.error(format_exc())

        try:
            async with get_async_db_context() as session:
                await save_fighters(session, fighter_schema_list)
            LOGGER.info(f"[{char}] fighters scraping completed : {len(fighter_schema_list)} fighters saved")
        except Exception as e:
            LOGGER.error(f"[{char}] fighters scraping failed: {str(e)}")
            LOGGER.error(format_exc())
    LOGGER.info("scrap_all_fighter_task completed")


@task(retries=3, cache_policy=NO_CACHE)
async def scrap_all_events_task(crawler_fn : Callable, batch_size: int = 30) -> None:
    all_events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    try:
        LOGGER.info("scrap_all_events_task started")
        event_schema_list = await scrap_all_events(crawler_fn, all_events_url)
    except Exception as e:
        LOGGER.error(f"scrap_all_events_task failed: {str(e)}")
        LOGGER.error(format_exc())
        return

    total_events = len(event_schema_list)
    saved_count = 0
    
    for i in range(0, total_events, batch_size):
        batch = event_schema_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_events + batch_size - 1) // batch_size
        
        LOGGER.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} events)")
        
        try:
            async with get_async_db_context() as session:
                await save_events(session, batch)
            saved_count += len(batch)
            LOGGER.info(f"Batch {batch_num}/{total_batches} completed: {len(batch)} events saved")
        except Exception as e:
            LOGGER.error(f"Batch {batch_num}/{total_batches} failed: {str(e)}")
            LOGGER.error(format_exc())
            # 배치 실패 시에도 다음 배치 계속 처리
            continue
    
    LOGGER.info(f"scrap_all_events_task completed: {saved_count}/{total_events} events saved")

async def process_event_detail(
    idx: int,
    event: EventSchema,
    crawler_fn: Callable,
    fighter_name_to_id_map: dict,
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
                LOGGER.error(f"[{idx+1}/{total_events}] - event_id: {event_id} event detail scraping failed: {str(e)}")
                LOGGER.error(format_exc())
                return
            LOGGER.info(f"[{idx+1}/{total_events}] - event_id: {event_id} event detail scraping completed : {saved_match_count} matches saved")

@task(retries=3, cache_policy=NO_CACHE)
async def scrap_event_detail_task(crawler_fn : Callable) -> None:
    LOGGER.info("scrap_event_detail_task started")
    async with get_async_db_context() as session:
        events_list = await get_events(session)
        all_fighters = await get_all_fighter(session)

    fighter_name_to_id_map = {fighter.name: fighter.id for fighter in all_fighters}

    semaphore = asyncio.Semaphore(3)

    tasks = [
        process_event_detail(idx, event, crawler_fn, fighter_name_to_id_map, len(events_list), semaphore)
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
    total_urls: int,
    semaphore: asyncio.Semaphore
    ) -> None:
    async with semaphore:
        await asyncio.sleep(RANDOM_DELAY)
        if not detail_url:
            return

        # 각 코루틴마다 독립적인 세션 생성
        async with get_async_db_context() as session:
            # 매치 기본 통계 정보 스크랩 및 저장
            try:
                match_statistics_list = await scrap_match_basic_statistics(
                    crawler_fn, detail_url, fighter_name_to_id_map, fighter_matches
                )
                await save_basic_match_stat(session, match_statistics_list)
                LOGGER.info(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} BasicMatchStat scraping completed")
            except Exception as e:
                LOGGER.error(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} BasicMatchStat scraping failed: {str(e)}")
                LOGGER.error(format_exc())

            # 매치 스트라이크 상세 정보 스크랩 및 저장
            try:
                strike_details_list = await scrap_match_significant_strikes(
                    crawler_fn, detail_url, fighter_name_to_id_map, fighter_matches
                )
                await save_sig_str_match_stat(session, strike_details_list)
                LOGGER.info(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} SigStrMatchStat scraping completed")
            except Exception as e:
                LOGGER.error(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} SigStrMatchStat scraping failed: {str(e)}")
                LOGGER.error(format_exc())

        LOGGER.info(f"[{idx+1}/{total_urls}] - detail_url: {detail_url} match detail scraping completed")


@task(retries=3, cache_policy=NO_CACHE)
async def scrap_match_detail_task(crawler_fn: Callable) -> None:  # session 파라미터 제거
    """
    매치 상세 정보를 스크랩하는 태스크
    """
    LOGGER.info("scrap_match_detail_task started")
    
    # 공통 데이터는 한 번만 조회
    async with get_async_db_context() as session:
        all_fighters = await get_all_fighter(session)
        fighter_match_dict = await get_match_fighter_mapping(session)
    
    fighter_name_to_id_map = {fighter.name: fighter.id for fighter in all_fighters}
    
    # 최대 3개의 동시 요청을 허용하는 Semaphore
    semaphore = asyncio.Semaphore(3)

    # 모든 URL에 대해 비동기 작업 생성 (session 파라미터 제거)
    tasks = [
        process_detail_url(
            idx, detail_url, fighter_matches, crawler_fn, 
            fighter_name_to_id_map, len(fighter_match_dict), semaphore
        )
        for idx, (detail_url, fighter_matches) in enumerate(fighter_match_dict.items())
    ]

    # 모든 작업을 동시에 실행
    await asyncio.gather(*tasks, return_exceptions=True)

    LOGGER.info("scrap_match_detail_task completed")


@task(retries=3, cache_policy=NO_CACHE)
async def scrap_rankings_task(crawler_fn: Callable) -> None:
    """
    UFC 랭킹을 스크랩하는 태스크
    """
    LOGGER.info("scrap_rankings_task started")

    async with get_async_db_context() as session:
        try:
            rankings = await scrap_rankings(session, crawler_fn)
            LOGGER.info(f"scrap_rankings_task completed : {len(rankings)} rankings collected")
        except Exception as e:
            LOGGER.error(f"scrap_rankings_task failed: {str(e)}")
            LOGGER.error(format_exc())
            return

        try:
            # ranking은 full clean
            await delete_all_rankings(session)
            await save_rankings(session, rankings)
            LOGGER.info(f"scrap_rankings_task completed : {len(rankings)} rankings saved")
        except Exception as e:
            LOGGER.error(f"scrap_rankings_task failed: {str(e)}")
            LOGGER.error(format_exc())
        