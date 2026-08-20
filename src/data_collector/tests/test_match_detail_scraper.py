import logging

import pytest

from data_collector.scrapers.match_detail_scraper import (
    scrap_match_basic_statistics,
    scrap_match_significant_strikes,
)


async def none_crawler(url: str) -> None:
    return None


@pytest.mark.asyncio
async def test_basic_statistics_returns_empty_list_when_crawler_returns_none(caplog):
    caplog.set_level(logging.WARNING)

    result = await scrap_match_basic_statistics(none_crawler, "http://ufcstats.com/fight-details/missing")

    assert result == []
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert "HTML content is empty" in caplog.text


@pytest.mark.asyncio
async def test_significant_strikes_returns_empty_list_when_crawler_returns_none(caplog):
    caplog.set_level(logging.WARNING)

    result = await scrap_match_significant_strikes(none_crawler, "http://ufcstats.com/fight-details/missing")

    assert result == []
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert "HTML content is empty" in caplog.text
