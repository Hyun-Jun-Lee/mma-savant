import httpx
import pytest

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
