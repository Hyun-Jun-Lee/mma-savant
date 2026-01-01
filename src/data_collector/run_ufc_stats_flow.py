import asyncio
import time
import os
from typing import Callable
import logging
from datetime import datetime

from data_collector.crawler import crawl_with_crawl4ai, crawl_with_httpx
from data_collector.workflows.tasks import (
    scrap_all_events_task,
    scrap_all_fighter_task,
    scrap_event_detail_task,
    scrap_match_detail_task,
    scrap_rankings_task
)


def setup_logging():
    """로깅 설정: 일반 로그와 warning/error 로그를 분리하여 파일로 저장"""
    # 로그 디렉토리 생성
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # 날짜별 로그 파일명 생성 (하루에 하나, 덮어쓰기)
    date_str = datetime.now().strftime("%Y%m%d")

    # 로그 포맷 설정
    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 1. 콘솔 핸들러 (INFO 이상)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)

    # 2. 일반 로그 파일 핸들러 (DEBUG 이상, 모든 로그, 덮어쓰기 mode='w')
    all_log_path = os.path.join(log_dir, f"ufc_stats_{date_str}.log")
    all_file_handler = logging.FileHandler(all_log_path, mode="w", encoding="utf-8")
    all_file_handler.setLevel(logging.DEBUG)
    all_file_handler.setFormatter(log_format)
    root_logger.addHandler(all_file_handler)

    # 3. Warning/Error 전용 파일 핸들러 (WARNING 이상, 덮어쓰기 mode='w')
    error_log_path = os.path.join(log_dir, f"ufc_stats_{date_str}_errors.log")
    error_file_handler = logging.FileHandler(error_log_path, mode="w", encoding="utf-8")
    error_file_handler.setLevel(logging.WARNING)
    error_file_handler.setFormatter(log_format)
    root_logger.addHandler(error_file_handler)

    return all_log_path, error_log_path


LOGGER = logging.getLogger(__name__)

async def run_ufc_stats_flow():
    LOGGER.info("UFC 통계 크롤링 시작")
    start_time = time.time()
    
    # # 파이터 크롤링
    LOGGER.info("Fighters scraping started")
    await scrap_all_fighter_task(crawl_with_httpx)
    LOGGER.info("Fighters scraping completed")

    # # 이벤트 크롤링
    LOGGER.info("Events scraping started")
    await scrap_all_events_task(crawl_with_httpx)
    LOGGER.info("Events scraping completed")

    # # 이벤트 세부 정보 크롤링
    LOGGER.info("Event details scraping started")
    await scrap_event_detail_task(crawl_with_httpx)
    LOGGER.info("Event details scraping completed")

    # 매치 세부 정보 크롤링
    LOGGER.info("Match details scraping started")
    await scrap_match_detail_task(crawl_with_httpx)
    LOGGER.info("Match details scraping completed")

    LOGGER.info("Rankings scraping started")
    await scrap_rankings_task(crawl_with_httpx)
    LOGGER.info("Rankings scraping completed")
    
    LOGGER.info("UFC 통계 크롤링 완료")
    end_time = time.time()
    LOGGER.info(f"Total time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    # 로깅 설정
    all_log, error_log = setup_logging()
    LOGGER.info(f"Log files: {all_log}")
    LOGGER.info(f"Error log: {error_log}")

    # 비동기 이벤트 루프에서 메인 함수 실행
    asyncio.run(run_ufc_stats_flow())