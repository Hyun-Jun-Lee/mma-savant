import logging
import asyncio
import inspect
import random
import httpx
import traceback
from typing import Any, Optional
from urllib.parse import urlparse

from user_agent import generate_user_agent

from data_collector.driver import PlaywrightDriver, Crawl4AIDriver

TAPOLOGY_SCRAPLING_DELAY_RANGE = (4.0, 8.0)


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


async def close_crawl4ai_crawlers() -> None:
    await Crawl4AIDriver.close_all()


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
        return _crawl4ai_result_html(result)
    except Exception as e:
        print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return None


async def crawl_tapology_with_scrapling(url: str) -> str:
    try:
        delay = random.uniform(*TAPOLOGY_SCRAPLING_DELAY_RANGE)
        logging.debug("Tapology Scrapling request delay %.2fs for %s", delay, url)
        await asyncio.sleep(delay)
        return await asyncio.to_thread(_fetch_tapology_with_scrapling, url)
    except Exception as e:
        print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return None


def _fetch_tapology_with_scrapling(url: str) -> str | None:
    from scrapling.fetchers import StealthyFetcher

    response = StealthyFetcher.fetch(
        url,
        **_build_tapology_scrapling_fetch_kwargs(StealthyFetcher),
    )
    return _scrapling_response_html(response)


def _build_tapology_scrapling_fetch_kwargs(fetcher: Any) -> dict[str, Any]:
    kwargs = {
        "headless": True,
        "timeout": 45_000,
        "wait": 1_500,
        "network_idle": False,
        "google_search": True,
        "os_randomize": False,
        "block_webrtc": True,
        "allow_webgl": True,
        "retries": 1,
    }

    fetch_signature = inspect.signature(fetcher.fetch)
    supports_extra_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in fetch_signature.parameters.values()
    )
    if supports_extra_kwargs or "solve_cloudflare" in fetch_signature.parameters:
        kwargs["solve_cloudflare"] = True

    return kwargs


def _crawl4ai_result_html(result: Any) -> str | None:
    if not result:
        return None
    if isinstance(result, str):
        return result
    return getattr(result, "html", None) or getattr(result, "cleaned_html", None)


def _scrapling_response_html(response: Any) -> str | None:
    if not response:
        return None

    for attr in ("body", "html_content", "text"):
        value = getattr(response, attr, None)
        if value is None:
            continue
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        value_text = str(value)
        if value_text and value_text != "None":
            return value_text

    return None
