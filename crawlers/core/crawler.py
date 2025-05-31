import httpx
import traceback

from core.driver import PlaywrightDriver

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
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"크롤링 중 오류 발생: {traceback.format_exc()}")
            return None
    