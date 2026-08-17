import pytest

from data_collector.workflows import ufc_stats_flow


class _DummyLogger:
    def info(self, *args, **kwargs):
        pass


@pytest.mark.asyncio
async def test_scheduled_flow_runs_tapology_profiles_with_scrapling(monkeypatch):
    calls = []
    playwright_crawler = object()
    tapology_crawler = object()

    def make_task(name):
        async def task(crawler_fn):
            calls.append((name, crawler_fn))

        return task

    async def geocoding_task():
        calls.append(("geocoding", None))

    async def close_playwright():
        calls.append(("close", None))

    monkeypatch.setattr(ufc_stats_flow, "get_run_logger", lambda: _DummyLogger())
    monkeypatch.setattr(ufc_stats_flow, "crawl_with_playwright", playwright_crawler)
    monkeypatch.setattr(ufc_stats_flow, "crawl_tapology_with_scrapling", tapology_crawler)
    monkeypatch.setattr(ufc_stats_flow, "invalidate_all_cache", lambda: 0)
    monkeypatch.setattr(ufc_stats_flow, "close_playwright_crawler", close_playwright)

    monkeypatch.setattr(ufc_stats_flow, "scrap_all_fighter_task", make_task("fighters"))
    monkeypatch.setattr(ufc_stats_flow, "enrich_fighter_nationality_task", make_task("nationality"))
    monkeypatch.setattr(
        ufc_stats_flow,
        "enrich_fighter_tapology_profile_task",
        make_task("tapology-profiles"),
    )
    monkeypatch.setattr(ufc_stats_flow, "scrap_all_events_task", make_task("events"))
    monkeypatch.setattr(ufc_stats_flow, "scrap_upcoming_events_task", make_task("upcoming-events"))
    monkeypatch.setattr(ufc_stats_flow, "enrich_event_geocoding_task", geocoding_task)
    monkeypatch.setattr(ufc_stats_flow, "scrap_event_detail_task", make_task("event-detail"))
    monkeypatch.setattr(ufc_stats_flow, "scrap_match_detail_task", make_task("match-detail"))
    monkeypatch.setattr(ufc_stats_flow, "scrap_rankings_task", make_task("rankings"))

    await ufc_stats_flow.run_ufc_stats_flow.fn()

    assert calls == [
        ("fighters", playwright_crawler),
        ("nationality", playwright_crawler),
        ("tapology-profiles", tapology_crawler),
        ("events", playwright_crawler),
        ("upcoming-events", playwright_crawler),
        ("geocoding", None),
        ("event-detail", playwright_crawler),
        ("match-detail", playwright_crawler),
        ("rankings", playwright_crawler),
        ("close", None),
    ]
