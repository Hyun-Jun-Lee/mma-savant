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
    assert _selector_for_url("https://kr.ufc.com/rankings") == "div.view-grouping"
    assert _selector_for_url("https://www.ufc.com/rankings") == "div.view-grouping"


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
