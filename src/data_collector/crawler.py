import httpx
import traceback
from typing import Any

from user_agent import generate_user_agent

from data_collector.driver import PlaywrightDriver, Crawl4AIDriver

async def crawl_with_playwright(url: str) -> str:
    try:
        async with PlaywrightDriver() as driver:
            page = await driver.new_page()
            await page.goto(url)
            html_content = await page.content()
        return html_content
    except Exception as e:
        print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return None

async def crawl_with_httpx(url: str) -> str:
    headers = {
        "User-Agent": generate_user_agent(os=('mac', 'linux'), device_type='desktop')
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
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
    