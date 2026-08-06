import logging
import random
import time
from collections.abc import Callable
from urllib.parse import quote_plus, urljoin

import requests as http_requests
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

TAPOLOGY_BASE_URL = "https://www.tapology.com"
TAPOLOGY_BASE_DELAY = (2.0, 4.0)
TAPOLOGY_CIRCUIT_BREAKER_THRESHOLD = 5
TAPOLOGY_CIRCUIT_BREAKER_COOLDOWN = 60

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class TapologyClient:
    """Shared Tapology HTTP client.

    Keeps Tapology access policy in one place: session reuse, user-agent
    rotation, random delays, timeouts, and circuit breaker handling.
    """

    def __init__(
        self,
        *,
        session: http_requests.Session | None = None,
        base_url: str = TAPOLOGY_BASE_URL,
        delay_range: tuple[float, float] = TAPOLOGY_BASE_DELAY,
        timeout: int = 10,
        circuit_breaker_threshold: int = TAPOLOGY_CIRCUIT_BREAKER_THRESHOLD,
        circuit_breaker_cooldown: int = TAPOLOGY_CIRCUIT_BREAKER_COOLDOWN,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._session = session or http_requests.Session()
        self._owns_session = session is None
        self._base_url = base_url.rstrip("/")
        self._delay_range = delay_range
        self._timeout = timeout
        self._circuit_breaker_threshold = circuit_breaker_threshold
        self._circuit_breaker_cooldown = circuit_breaker_cooldown
        self._sleeper = sleeper
        self._ua = UserAgent()
        self._consecutive_failures = 0

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    def _get_headers(self) -> dict[str, str]:
        try:
            user_agent = self._ua.random
        except Exception:
            user_agent = DEFAULT_USER_AGENT
        return {"User-Agent": user_agent}

    def _absolute_url(self, path_or_url: str) -> str:
        return urljoin(f"{self._base_url}/", path_or_url)

    def wait_between_requests(self) -> None:
        self._sleeper(random.uniform(*self._delay_range))

    def _request(self, url: str) -> http_requests.Response | None:
        if self._consecutive_failures >= self._circuit_breaker_threshold:
            logger.warning(
                "Tapology circuit breaker open (%d consecutive failures), cooling down %ds",
                self._consecutive_failures,
                self._circuit_breaker_cooldown,
            )
            self._sleeper(self._circuit_breaker_cooldown)
            self._consecutive_failures = 0

        try:
            response = self._session.get(
                url,
                headers=self._get_headers(),
                timeout=self._timeout,
            )
        except Exception as exc:
            logger.warning("Tapology request error for %s: %s", url, exc)
            self._consecutive_failures += 1
            return None

        if response.status_code == 200:
            self._consecutive_failures = 0
            return response

        logger.warning("Tapology %d for %s", response.status_code, url)
        self._consecutive_failures += 1
        return None

    def fetch_url(self, path_or_url: str, *, delay_before: bool = False) -> str | None:
        if delay_before:
            self.wait_between_requests()

        response = self._request(self._absolute_url(path_or_url))
        if response is None:
            return None
        return response.text

    def fetch_search_page(self, term: str) -> str | None:
        return self.fetch_url(f"/search?term={quote_plus(term)}")

    def fetch_fighter_detail_page(
        self,
        path_or_url: str,
        *,
        delay_before: bool = True,
    ) -> str | None:
        return self.fetch_url(path_or_url, delay_before=delay_before)

    def fetch_bout_detail_page(
        self,
        path_or_url: str,
        *,
        delay_before: bool = True,
    ) -> str | None:
        return self.fetch_url(path_or_url, delay_before=delay_before)

    def fetch_event_detail_page(
        self,
        path_or_url: str,
        *,
        delay_before: bool = True,
    ) -> str | None:
        return self.fetch_url(path_or_url, delay_before=delay_before)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()
