import pytest

from data_collector import run_ufc_stats_flow


@pytest.mark.asyncio
async def test_default_cli_flow_includes_tapology_tasks(monkeypatch):
    calls = []
    playwright_crawler = object()
    tapology_crawler = object()

    def make_task(name):
        async def task(crawler_fn):
            calls.append((name, crawler_fn))

        return task

    async def close_playwright():
        calls.append(("close", None))

    monkeypatch.setattr(run_ufc_stats_flow, "crawl_with_playwright", playwright_crawler)
    monkeypatch.setattr(run_ufc_stats_flow, "crawl_tapology_with_scrapling", tapology_crawler)
    monkeypatch.setattr(run_ufc_stats_flow, "close_playwright_crawler", close_playwright)
    monkeypatch.setattr(
        run_ufc_stats_flow,
        "TASK_MAP",
        {
            task_name: (task_name, make_task(task_name))
            for task_name in run_ufc_stats_flow.ALL_TASKS
        },
    )

    await run_ufc_stats_flow.run_ufc_stats_flow()

    assert calls == [
        ("fighters", playwright_crawler),
        ("tapology-profiles", tapology_crawler),
        ("events", playwright_crawler),
        ("upcoming-events", playwright_crawler),
        ("event-detail", playwright_crawler),
        ("match-detail", playwright_crawler),
        ("tapology-bouts", tapology_crawler),
        ("rankings", playwright_crawler),
        ("close", None),
    ]
