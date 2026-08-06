import requests
import pytest

from data_collector.clients.tapology import TapologyClient
from data_collector.scripts.scrape_nationality import fetch_nationality_from_tapology


class FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


class FakeSession:
    def __init__(self, responses=None, exception: Exception | None = None) -> None:
        self.responses = list(responses or [])
        self.exception = exception
        self.closed = False
        self.requests = []

    def get(self, url, headers, timeout):
        self.requests.append((url, headers, timeout))
        if self.exception:
            raise self.exception
        return self.responses.pop(0)

    def close(self):
        self.closed = True


def test_fetch_url_resets_failure_count_on_success():
    session = FakeSession([FakeResponse(200, "ok")])
    client = TapologyClient(session=session, sleeper=lambda _: None)
    client._consecutive_failures = 2

    assert client.fetch_url("/search?term=Alex+Pereira") == "ok"
    assert client.consecutive_failures == 0
    assert session.requests[0][0] == "https://www.tapology.com/search?term=Alex+Pereira"
    assert session.requests[0][2] == 10


def test_fetch_url_increments_failure_count_on_non_200():
    session = FakeSession([FakeResponse(429, "slow down")])
    client = TapologyClient(session=session, sleeper=lambda _: None)

    assert client.fetch_url("https://www.tapology.com/search?term=Nope") is None
    assert client.consecutive_failures == 1


def test_fetch_url_increments_failure_count_on_request_exception():
    session = FakeSession(exception=requests.Timeout("timeout"))
    client = TapologyClient(session=session, sleeper=lambda _: None)

    assert client.fetch_url("/search?term=Nope") is None
    assert client.consecutive_failures == 1


def test_fetch_search_page_url_encodes_search_term():
    session = FakeSession([FakeResponse(200, "search")])
    client = TapologyClient(session=session, sleeper=lambda _: None)

    assert client.fetch_search_page("Georges St-Pierre") == "search"
    assert session.requests[0][0] == "https://www.tapology.com/search?term=Georges+St-Pierre"


@pytest.mark.asyncio
async def test_fetch_nationality_from_tapology_uses_shared_client():
    search_html = """
    <a href="/fightcenter/fighters/alex-pereira">Alex "Poatan" Pereira</a>
    """
    detail_html = '<img src="/assets/flags/BR.png">'
    session = FakeSession([
        FakeResponse(200, search_html),
        FakeResponse(200, detail_html),
    ])
    client = TapologyClient(session=session, sleeper=lambda _: None)

    result = await fetch_nationality_from_tapology(
        "Alex Pereira",
        "Poatan",
        client=client,
    )

    assert result == "Brazil"
    assert session.requests[0][0] == "https://www.tapology.com/search?term=Alex+Pereira"
    assert session.requests[1][0] == "https://www.tapology.com/fightcenter/fighters/alex-pereira"


@pytest.mark.asyncio
async def test_fetch_nationality_from_tapology_uses_crawler_fn_when_provided():
    search_html = """
    <a href="/fightcenter/fighters/alex-pereira">Alex "Poatan" Pereira</a>
    """
    detail_html = '<img src="/assets/flags/BR.png">'
    responses = {
        "https://www.tapology.com/search?term=Alex+Pereira": search_html,
        "https://www.tapology.com/fightcenter/fighters/alex-pereira": detail_html,
    }
    requested_urls = []

    async def crawler_fn(url):
        requested_urls.append(url)
        return responses[url]

    result = await fetch_nationality_from_tapology(
        "Alex Pereira",
        "Poatan",
        crawler_fn=crawler_fn,
    )

    assert result == "Brazil"
    assert requested_urls == [
        "https://www.tapology.com/search?term=Alex+Pereira",
        "https://www.tapology.com/fightcenter/fighters/alex-pereira",
    ]
