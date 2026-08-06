import logging
import httpx
import traceback
from typing import Any, Optional
from urllib.parse import urlparse

from user_agent import generate_user_agent

from data_collector.driver import PlaywrightDriver, Crawl4AIDriver


def _selector_for_url(url: str) -> Optional[str]:
    parsed_url = urlparse(url)
    host = parsed_url.netloc.lower()
    path = parsed_url.path.rstrip("/")

    if host.endswith("ufcstats.com"):
        if path.startswith("/statistics/events/"):
            return "table.b-statistics__table-events"
        if path.startswith("/statistics/fighters"):
            return "table.b-statistics__table"
        if path.startswith("/event-details/"):
            return "div.b-list__info-box"
        if path.startswith("/fight-details/"):
            return "table.b-fight-details__table"

    if host.endswith("ufc.com") and path.endswith("/rankings"):
        return "div.view-grouping"

    return None


async def crawl_with_playwright(url: str) -> str:
    driver = PlaywrightDriver()
    page = None
    try:
        await driver.initialize()
        page = await driver.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        wait_selector = _selector_for_url(url)
        if wait_selector:
            await page.wait_for_selector(wait_selector, state="attached", timeout=15000)

        html_content = await page.content()
        return html_content
    except Exception as e:
        print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return None
    finally:
        if page:
            await page.close()


async def close_playwright_crawler() -> None:
    await PlaywrightDriver().close()


async def crawl_with_httpx(url: str) -> str:
    headers = {
        "User-Agent": generate_user_agent(os=('mac', 'linux'), device_type='desktop')
    }
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code in {403, 404}:
                logging.warning(
                    "크롤링 대상 페이지 접근 불가 또는 없음(status=%s): %s",
                    status_code,
                    e.response.url,
                )
                return None

            print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
            return None
        except Exception as e:
            print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
            return None


async def crawl_with_crawl4ai(url: str, run_config: Any = None) -> str:
    try:
        driver = Crawl4AIDriver()
        result = await driver.run_crawl(url, run_config)
        return result
    except Exception as e:
        print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return None
