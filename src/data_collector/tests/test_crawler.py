import httpx
import pytest

from data_collector import crawler
from data_collector.crawler import _selector_for_url, crawl_with_httpx


def test_selector_for_ufcstats_pages():
    assert (
        _selector_for_url("http://ufcstats.com/statistics/events/completed?page=all")
        == "table.b-statistics__table-events"
    )
    assert (
        _selector_for_url("http://ufcstats.com/statistics/events/upcoming?page=all")
        == "table.b-statistics__table-events"
    )
    assert (
        _selector_for_url("http://ufcstats.com/statistics/fighters?char=a&page=all")
        == "table.b-statistics__table"
    )
    assert (
        _selector_for_url("http://ufcstats.com/event-details/ca936c67687789e9")
        == "div.b-list__info-box"
    )
    assert (
        _selector_for_url("http://ufcstats.com/fight-details/d13849f49f99bf01")
        == "table.b-fight-details__table"
    )


def test_selector_for_ufc_rankings():
    assert _selector_for_url("https://kr.ufc.com/rankings") == "#rankings-panel-media"
    assert _selector_for_url("https://www.ufc.com/rankings") == "#rankings-panel-media"


def test_detects_ufc_edge_forbidden_html():
    html = "<body>Error 403 Forbidden Details: cache-icn Varnish cache server</body>"

    assert crawler._is_ufc_edge_forbidden_html(html) is True
    assert crawler._is_ufc_edge_forbidden_html("<body>Error 403 Forbidden</body>") is False


@pytest.mark.asyncio
async def test_crawl_with_playwright_retries_ufc_rankings_edge_forbidden(monkeypatch):
    first_html = "<body>Error 403 Forbidden Details: cache-icn Varnish cache server</body>"
    second_html = '<body><div id="rankings-panel-media">rankings</div></body>'

    class FakePage:
        def __init__(self):
            self.html_by_attempt = [first_html, second_html]
            self.goto_calls = 0
            self.wait_selectors = []

        async def goto(self, url, wait_until):
            self.goto_calls += 1

        async def wait_for_selector(self, selector, state, timeout):
            self.wait_selectors.append(selector)
            html = await self.content()
            if selector == "#rankings-panel-media" and 'id="rankings-panel-media"' in html:
                return
            if selector not in html:
                raise RuntimeError("selector timeout")

        async def content(self):
            return self.html_by_attempt[self.goto_calls - 1]

        async def close(self):
            pass

    fake_page = FakePage()

    class FakeDriver:
        async def initialize(self):
            pass

        async def new_page(self):
            return fake_page

    async def fake_sleep(delay):
        pass

    monkeypatch.setattr(crawler, "PlaywrightDriver", FakeDriver)
    monkeypatch.setattr(crawler.asyncio, "sleep", fake_sleep)

    html = await crawler.crawl_with_playwright("https://kr.ufc.com/rankings")

    assert html == second_html
    assert fake_page.goto_calls == 2
    assert fake_page.wait_selectors == ["#rankings-panel-media", "#rankings-panel-media"]


@pytest.mark.asyncio
async def test_crawl_with_playwright_retries_ufcstats_fight_detail_once(monkeypatch):
    first_html = "<body>Checking your browser…</body>"
    second_html = '<body><table class="b-fight-details__table">fight stats</table></body>'

    class FakePage:
        def __init__(self):
            self.html_by_attempt = [first_html, second_html]
            self.goto_calls = 0
            self.wait_selectors = []

        async def goto(self, url, wait_until):
            self.goto_calls += 1

        async def wait_for_selector(self, selector, state, timeout):
            self.wait_selectors.append(selector)
            html = await self.content()
            if selector == "table.b-fight-details__table" and 'class="b-fight-details__table"' in html:
                return
            raise RuntimeError("selector timeout")

        async def content(self):
            return self.html_by_attempt[self.goto_calls - 1]

        async def close(self):
            pass

    fake_page = FakePage()

    class FakeDriver:
        async def initialize(self):
            pass

        async def new_page(self):
            return fake_page

    async def fake_sleep(delay):
        pass

    monkeypatch.setattr(crawler, "PlaywrightDriver", FakeDriver)
    monkeypatch.setattr(crawler.asyncio, "sleep", fake_sleep)

    html = await crawler.crawl_with_playwright("http://ufcstats.com/fight-details/d14fea43712707f0")

    assert html == second_html
    assert fake_page.goto_calls == 2
    assert fake_page.wait_selectors == [
        "table.b-fight-details__table",
        "table.b-fight-details__table",
    ]


@pytest.mark.asyncio
async def test_crawl_with_playwright_stops_ufcstats_fight_detail_after_one_retry(monkeypatch):
    blocked_html = "<body>Checking your browser…</body>"

    class FakePage:
        def __init__(self):
            self.goto_calls = 0
            self.wait_selectors = []

        async def goto(self, url, wait_until):
            self.goto_calls += 1

        async def wait_for_selector(self, selector, state, timeout):
            self.wait_selectors.append(selector)
            raise RuntimeError("selector timeout")

        async def content(self):
            return blocked_html

        async def close(self):
            pass

    fake_page = FakePage()

    class FakeDriver:
        async def initialize(self):
            pass

        async def new_page(self):
            return fake_page

    async def fake_sleep(delay):
        pass

    monkeypatch.setattr(crawler, "PlaywrightDriver", FakeDriver)
    monkeypatch.setattr(crawler.asyncio, "sleep", fake_sleep)

    html = await crawler.crawl_with_playwright("http://ufcstats.com/fight-details/d14fea43712707f0")

    assert html is None
    assert fake_page.goto_calls == 2
    assert fake_page.wait_selectors == [
        "table.b-fight-details__table",
        "table.b-fight-details__table",
    ]


def test_selector_for_unknown_url():
    assert _selector_for_url("https://example.com") is None


class _FakeHttpxClient:
    status_code = 403

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, headers):
        request = httpx.Request("GET", url)
        return httpx.Response(self.status_code, request=request)


@pytest.mark.parametrize("status_code", [403, 404])
@pytest.mark.asyncio
async def test_crawl_with_httpx_warns_without_traceback_for_expected_missing_pages(
    monkeypatch,
    caplog,
    capsys,
    status_code,
):
    class FakeHttpxClient(_FakeHttpxClient):
        pass

    FakeHttpxClient.status_code = status_code
    monkeypatch.setattr("data_collector.crawler.httpx.AsyncClient", FakeHttpxClient)

    with caplog.at_level("WARNING"):
        result = await crawl_with_httpx("https://www.ufc.com/athlete/missing-fighter")

    assert result is None
    assert f"status={status_code}" in caplog.text
    assert "Traceback" not in capsys.readouterr().out


class _FetcherWithCloudflareSolver:
    @staticmethod
    def fetch(url, solve_cloudflare=False):
        return None


class _FetcherWithoutCloudflareSolver:
    @staticmethod
    def fetch(url):
        return None


class _FetcherWithKwargs:
    @staticmethod
    def fetch(url, **kwargs):
        return None


def test_tapology_scrapling_options_enable_cloudflare_solver_when_supported():
    kwargs = crawler._build_tapology_scrapling_fetch_kwargs(_FetcherWithCloudflareSolver)

    assert kwargs["solve_cloudflare"] is True


def test_tapology_scrapling_options_enable_cloudflare_solver_for_kwargs_fetcher():
    kwargs = crawler._build_tapology_scrapling_fetch_kwargs(_FetcherWithKwargs)

    assert kwargs["solve_cloudflare"] is True


def test_tapology_scrapling_options_use_fail_fast_settings():
    kwargs = crawler._build_tapology_scrapling_fetch_kwargs(_FetcherWithKwargs)

    assert kwargs["timeout"] == 45_000
    assert kwargs["wait"] == 1_500
    assert kwargs["retries"] == 1


def test_tapology_scrapling_options_skip_cloudflare_solver_when_unsupported():
    kwargs = crawler._build_tapology_scrapling_fetch_kwargs(_FetcherWithoutCloudflareSolver)

    assert "solve_cloudflare" not in kwargs


@pytest.mark.asyncio
async def test_tapology_scrapling_crawler_waits_before_fetch(monkeypatch):
    calls = []

    async def fake_sleep(delay):
        calls.append(("sleep", delay))

    def fake_fetch(url):
        calls.append(("fetch", url))
        return "<html></html>"

    monkeypatch.setattr(crawler.random, "uniform", lambda start, end: 3.25)
    monkeypatch.setattr(crawler.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(crawler, "_fetch_tapology_with_scrapling", fake_fetch)

    html = await crawler.crawl_tapology_with_scrapling("https://www.tapology.com/search?term=test")

    assert html == "<html></html>"
    assert calls == [
        ("sleep", 3.25),
        ("fetch", "https://www.tapology.com/search?term=test"),
    ]
