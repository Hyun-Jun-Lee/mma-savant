from typing import Optional, Callable
import logging

from user_agent import generate_user_agent

from playwright.async_api import async_playwright, Browser, Page

class PlaywrightDriver:
    _browser: Optional[Browser] = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlaywrightDriver, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'playwright'):
            self.playwright = None

    async def initialize(self, headless: bool = True) -> None:
        """비동기적으로 Playwright 브라우저를 초기화합니다"""
        if self._browser is None:
            self.playwright = await async_playwright().start()
            
            # 봇 감지 방지를 위한 브라우저 실행 옵션
            browser_options = {
                "headless": headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--disable-extensions",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            }
            
            self._browser = await self.playwright.chromium.launch(**browser_options)
            logging.info("Playwright browser initialized with anti-bot detection")

    async def new_page(self) -> Page:
        """스텔스 설정으로 새 페이지를 생성합니다"""
        if self._browser is None:
            await self.initialize()

        page = await self._browser.new_page()
        
        # 감지 방지를 위한 추가 설정 적용
        await page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': generate_user_agent(os=('mac', 'linux'), device_type='desktop')
        })
        
        await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});  
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)
        
        return page

    async def close(self) -> None:
        """브라우저와 playwright를 종료합니다"""
        if self._browser is not None:
            await self._browser.close()
            self._browser = None

        if hasattr(self, 'playwright') and self.playwright is not None:
            await self.playwright.stop()
            self.playwright = None
            logging.info("Playwright browser closed")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()