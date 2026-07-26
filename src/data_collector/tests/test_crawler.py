from data_collector.crawler import _selector_for_url


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
