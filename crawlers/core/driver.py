from playwright.sync_api import sync_playwright, Browser, Page
from typing import Optional, Callable
import logging

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

    def initialize(self, headless: bool = True) -> None:
        """Initialize the Playwright browser if not already initialized"""
        if self._browser is None:
            self.playwright = sync_playwright().start()
            
            # Browser launch options for avoiding bot detection
            browser_options = {
                "headless": headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-site-isolation-trials"
                ],
                "firefox_user_prefs": {
                    "dom.webdriver.enabled": False,
                    "media.navigator.permission.disabled": True,
                    "media.navigator.streams.fake": True
                },
                "chromium_sandbox": False
            }
            
            self._browser = self.playwright.chromium.launch(**browser_options)
            logging.info("Playwright browser initialized with anti-bot detection")

    def new_page(self) -> Page:
        """Create and return a new page with anti-bot detection settings"""
        if self._browser is None:
            self.initialize()
        
        page = self._browser.new_page()
        
        # Add anti-bot detection settings
        page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Modify navigator properties
        js_script = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        """
        page.add_init_script(js_script)
        
        return page

    def close(self) -> None:
        """Close the browser and playwright instance"""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
            logging.info("Playwright browser closed")

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()