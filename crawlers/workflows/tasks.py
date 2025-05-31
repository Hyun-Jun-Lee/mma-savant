import asyncio
import random
from typing import List, Dict
from traceback import format_exc

from prefect import task
from prefect.logging import get_run_logger
from prefect.cache_policies import NO_CACHE

from repository import BaseRepository, FighterRepository, EventRepository, MatchRepository, FighterMatchRepository, BasicMatchStatRepository, SigStrMatchStatRepository
from schemas import BaseSchema, Event, Fighter, Match, FighterMatch
from scrapers import scrap_fighters, scrap_all_events, scrap_event_detail, scrape_match_basic_statistics, scrape_match_significant_strikes

random_delay = random.randint(1, 5)
logger = get_run_logger()


def save_data(data : List[BaseSchema], repository: BaseRepository) -> List[BaseSchema]:
    return repository.bulk_upsert(data)

@task(retries=3, cache_policy=NO_CACHE)
async def scrap_all_fighter_task(session)-> None:
    logger.info("scrap_all_fighter_task started")
    for char in 'abcdefghijklmnopqrstuvwxyz':
        await asyncio.sleep(random_delay)
        logger.info(f"[{char}] fighters scraping started")
        fighters_url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        try:
            fighter_schema_list = await scrap_fighters(fighters_url)
            saved_fighter_list = save_data(fighter_schema_list, FighterRepository(session))
            logger.info(f"[{char}] fighters scraping completed : {len(saved_fighter_list)} fighters saved")
        except Exception as e:
            logger.error(f"[{char}] fighters scraping failed: {str(e)}")
            logger.error(format_exc())

    logger.info("scrap_all_fighter_task completed")


@task(retries=3, cache_policy=NO_CACHE)
async def scrap_all_events_task(session) -> None:
    all_events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    try:
        logger.info("scrap_all_events_task started")
        event_schema_list = await scrap_all_events(all_events_url)
        saved_event_list = save_data(event_schema_list, EventRepository(session))
        logger.info(f"scrap_all_events_task completed : {len(saved_event_list)} events saved")
    except Exception as e:
        logger.error(f"scrap_all_events_task failed: {str(e)}")
        logger.error(format_exc())

@task(retries=3, cache_policy=NO_CACHE)
async def scrap_event_detail_task(session) -> None:
    logger.info("scrap_event_detail_task started")
    events_list = EventRepository(session).find_all()
    all_fighters = FighterRepository(session).find_all()
    fighter_dict = {fighter.name: fighter.id for fighter in all_fighters}
    
    for idx, event in enumerate(events_list):
        await asyncio.sleep(random_delay)
        logger.info(f"[{idx+1}/{len(events_list)}] - event_id: {event.id} event detail scraping started")
        event_url = event.url
        event_id = event.id
        try:
            matches_data = await scrap_event_detail(event_url, event_id, fighter_dict)
        except Exception as e:
            logger.error(f"[{idx+1}/{len(events_list)}] - event_id: {event_id} event detail scraping failed: {str(e)}")
            logger.error(format_exc())
            continue

        saved_match_count = 0
        for match_data in matches_data:
            match = match_data["match"]
            saved_match = save_data([match], MatchRepository(session))
            match_id = saved_match[0].id
            detail_url = saved_match[0].detail_url if saved_match[0].detail_url else None
            if not detail_url:
                continue

            for fighter_info in match_data["fighters"]:
                fighter_id = fighter_info["fighter_id"]
                result = fighter_info["result"]
                fighter_match = FighterMatch(fighter_id=fighter_id, match_id=match_id, result=result)
                save_data([fighter_match], FighterMatchRepository(session))
            saved_match_count += len(saved_match)
        logger.info(f"[{idx+1}/{len(events_list)}] - event_id: {event_id} event detail scraping completed : {saved_match_count} matches saved")
    logger.info("scrap_event_detail_task completed")

@task(retries=3, cache_policy=NO_CACHE)
async def scrap_match_detail_task(session)-> None:
    """
    매치 상세 정보를 스크랩하는 태스크
    
    Args:
        session: 데이터베이스 세션
        fighter_match_dict: {detail_url: {fighter_id: fighter_match}} 형태의 딕셔너리
        fighter_dict: {fighter_name: fighter_id} 형태의 딕셔너리
    """
    logger.info("scrap_match_detail_task started")
    all_fighters = FighterRepository(session).find_all()
    fighter_dict = {fighter.name: fighter.id for fighter in all_fighters}
    fighter_match_dict = FighterMatchRepository(session).find_match_fighter_mapping()

    for idx, (detail_url, fighter_matches) in enumerate(fighter_match_dict.items()):
        await asyncio.sleep(random_delay)
        logger.info(f"[{idx+1}/{len(fighter_match_dict)}] - detail_url: {detail_url} match detail scraping started")
        if not detail_url:
            continue
            
        # 매치 기본 통계 정보 스크랩 및 저장
        try:
            match_statistics_list = await scrape_match_basic_statistics(detail_url, fighter_dict, fighter_matches)
            save_data(match_statistics_list, BasicMatchStatRepository(session))
            logger.info(f"[{idx+1}/{len(fighter_match_dict)}] - detail_url: {detail_url} BasicMatchStat scraping completed")
        except Exception as e:
            logger.error(f"[{idx+1}/{len(fighter_match_dict)}] - detail_url: {detail_url} BasicMatchStat scraping failed: {str(e)}")
            logger.error(format_exc())
            continue
        
        # 매치 스트라이크 상세 정보 스크랩 및 저장
        try:
            strike_details_list = await scrape_match_significant_strikes(detail_url, fighter_dict, fighter_matches)
            save_data(strike_details_list, SigStrMatchStatRepository(session))
            logger.info(f"[{idx+1}/{len(fighter_match_dict)}] - detail_url: {detail_url} SigStrMatchStat scraping completed")
        except Exception as e:
            logger.error(f"[{idx+1}/{len(fighter_match_dict)}] - detail_url: {detail_url} SigStrMatchStat scraping failed: {str(e)}")
            logger.error(format_exc())
            continue
        logger.info(f"[{idx+1}/{len(fighter_match_dict)}] - detail_url: {detail_url} match detail scraping completed")
