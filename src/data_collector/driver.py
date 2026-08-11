import asyncio
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import logging

from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
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
            self._init_lock = asyncio.Lock()

    async def initialize(self, headless: bool = True) -> None:
        """비동기적으로 Playwright 브라우저를 초기화합니다"""
        if self._browser is None:
            async with self._init_lock:
                if self._browser is not None:
                    return

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


class Crawl4AIDriver:
    _instances = {}
    
    def __new__(cls, *args, **kwargs):
        key = (
            kwargs.get("headless", True),
            kwargs.get("enable_stealth", False),
            kwargs.get("use_persistent_context", False),
            kwargs.get("user_data_dir"),
            kwargs.get("undetected", False),
            kwargs.get("delay_before_return_html", 0.1),
            kwargs.get("simulate_user", False),
            kwargs.get("override_navigator", False),
        )
        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
        return cls._instances[key]
    
    def __init__(
        self,
        headless: bool = True,
        *,
        enable_stealth: bool = False,
        use_persistent_context: bool = False,
        user_data_dir: str | None = None,
        undetected: bool = False,
        delay_before_return_html: float = 0.1,
        simulate_user: bool = False,
        override_navigator: bool = False,
    ) -> None:
        if hasattr(self, '_initialized'):
            return
        
        self.browser_config: Optional[BrowserConfig] = None
        self.run_config: Optional[CrawlerRunConfig] = None
        self.driver_type = "crawl4ai"
        self.headless = headless
        self.enable_stealth = enable_stealth
        self.use_persistent_context = use_persistent_context
        self.user_data_dir = user_data_dir
        self.undetected = undetected
        self.delay_before_return_html = delay_before_return_html
        self.simulate_user = simulate_user
        self.override_navigator = override_navigator
        self.crawler: Optional[AsyncWebCrawler] = None
        self._initialized = True
        
        self._set_driver()
        
    def _set_driver(self) -> None:
        """Crawl4AI 드라이버 초기화"""
        try:
            extra_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--disable-extensions",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
            
            js_code = """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
                Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """
            
            self.browser_config = BrowserConfig(
                user_agent=generate_user_agent(os=('mac', 'linux'), device_type='desktop'),
                extra_args=extra_args,
                headless=self.headless,
                enable_stealth=self.enable_stealth,
                use_persistent_context=self.use_persistent_context,
                user_data_dir=self.user_data_dir,
            )
            
            self.run_config = CrawlerRunConfig(
                remove_overlay_elements=True,
                process_iframes=True,
                screenshot=True,
                capture_network_requests=False,
                js_code=js_code,
                delay_before_return_html=self.delay_before_return_html,
                simulate_user=self.simulate_user,
                override_navigator=self.override_navigator,
                magic=self.simulate_user or self.override_navigator,
            )
            
            logging.info("Crawl4AIDriver initialized with optimized settings")
        except Exception as e:
            logging.error(f"Crawl4AIDriver initialization error: {e}")
            raise

    async def get_driver(self) -> AsyncWebCrawler:
        if not self.crawler:
            if self.undetected:
                adapter = UndetectedAdapter()
                crawler_strategy = AsyncPlaywrightCrawlerStrategy(
                    browser_config=self.browser_config,
                    browser_adapter=adapter,
                )
                self.crawler = AsyncWebCrawler(
                    crawler_strategy=crawler_strategy,
                    config=self.browser_config,
                )
            else:
                self.crawler = AsyncWebCrawler(config=self.browser_config)
        return self.crawler

    async def run_crawl(self, url: str, run_config: Any = None) -> Dict[str, Any]:
        """
        페이지 크롤링 실행
        """
        crawler = await self.get_driver()
        
        try:
            result = await crawler.arun(
                url=url,
                config=run_config or self.run_config,
            )
            return result
            
        except Exception as e:
            logging.error(f"Crawling failed for {url}: {e}")
            raise

    async def close(self):
        """브라우저 정리"""
        if self.crawler:
            await self.crawler.close()
            self.crawler = None
            logging.info("Crawl4AI driver closed")

    @classmethod
    async def close_all(cls) -> None:
        for driver in cls._instances.values():
            await driver.close()


def tapology_user_data_dir() -> str:
    path = Path(".crawl4ai") / "tapology-profile"
    path.mkdir(parents=True, exist_ok=True)
    return str(path.resolve())
