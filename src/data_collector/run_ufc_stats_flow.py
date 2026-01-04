import asyncio
import time
import os
import argparse
from typing import Callable, List, Optional
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

# 태스크 매핑
TASK_MAP = {
    "fighters": ("Fighters", scrap_all_fighter_task),
    "events": ("Events", scrap_all_events_task),
    "event-detail": ("Event details", scrap_event_detail_task),
    "match-detail": ("Match details", scrap_match_detail_task),
    "rankings": ("Rankings", scrap_rankings_task),
}

# 전체 실행 순서
ALL_TASKS = ["fighters", "events", "event-detail", "match-detail", "rankings"]


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


async def run_ufc_stats_flow(tasks: Optional[List[str]] = None):
    """
    UFC 통계 크롤링 실행

    Args:
        tasks: 실행할 태스크 목록. None이면 전체 실행
    """
    tasks_to_run = tasks or ALL_TASKS

    LOGGER.info(f"UFC 통계 크롤링 시작 - 태스크: {tasks_to_run}")
    start_time = time.time()

    for task_name in tasks_to_run:
        if task_name not in TASK_MAP:
            LOGGER.warning(f"Unknown task: {task_name}, skipping...")
            continue

        display_name, task_fn = TASK_MAP[task_name]
        LOGGER.info(f"{display_name} scraping started")
        await task_fn(crawl_with_httpx)
        LOGGER.info(f"{display_name} scraping completed")

    end_time = time.time()
    LOGGER.info(f"UFC 통계 크롤링 완료 - Total time: {end_time - start_time:.2f} seconds")


def parse_args():
    parser = argparse.ArgumentParser(
        description="UFC Stats Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ufc_stats_flow.py                     # 전체 실행
  python run_ufc_stats_flow.py -t event-detail     # event-detail만 실행
  python run_ufc_stats_flow.py -t fighters events  # fighters, events 실행
  python run_ufc_stats_flow.py --list              # 사용 가능한 태스크 목록

Available tasks:
  fighters      - 파이터 정보 크롤링
  events        - 이벤트 목록 크롤링
  event-detail  - 이벤트 상세 정보 크롤링
  match-detail  - 매치 상세 정보 크롤링
  rankings      - 랭킹 정보 크롤링
        """
    )
    parser.add_argument(
        "-t", "--tasks",
        nargs="+",
        choices=list(TASK_MAP.keys()),
        help="실행할 태스크 (여러 개 지정 가능)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="사용 가능한 태스크 목록 출력"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.list:
        print("Available tasks:")
        for task_name, (display_name, _) in TASK_MAP.items():
            print(f"  {task_name:15} - {display_name} scraping")
        exit(0)

    # 로깅 설정
    all_log, error_log = setup_logging()
    LOGGER.info(f"Log files: {all_log}")
    LOGGER.info(f"Error log: {error_log}")

    # 비동기 이벤트 루프에서 메인 함수 실행
    asyncio.run(run_ufc_stats_flow(args.tasks))