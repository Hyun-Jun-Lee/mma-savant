import pytest

from data_collector import run_ufc_stats_flow
from data_collector.workflows import tapology_tasks
from data_collector.workflows import tasks as workflow_tasks


@pytest.mark.asyncio
async def test_default_cli_flow_includes_tapology_profiles_only(monkeypatch):
    calls = []
    playwright_crawler = object()
    tapology_crawler = object()

    def make_task(name):
        async def task(crawler_fn):
            calls.append((name, crawler_fn))

        return task

    async def geocoding_task():
        calls.append(("event-geocoding", None))

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
            if task_name != "event-geocoding"
        },
    )
    run_ufc_stats_flow.TASK_MAP["event-geocoding"] = ("event-geocoding", geocoding_task)

    await run_ufc_stats_flow.run_ufc_stats_flow()

    assert calls == [
        ("fighters", playwright_crawler),
        ("nationality", playwright_crawler),
        ("tapology-profiles", tapology_crawler),
        ("events", playwright_crawler),
        ("upcoming-events", playwright_crawler),
        ("event-geocoding", None),
        ("event-detail", playwright_crawler),
        ("match-detail", playwright_crawler),
        ("rankings", playwright_crawler),
        ("close", None),
    ]


def test_prefect_task_names_match_cli_aliases():
    task_by_alias = {
        "fighters": workflow_tasks.scrap_all_fighter_task,
        "events": workflow_tasks.scrap_all_events_task,
        "upcoming-events": workflow_tasks.scrap_upcoming_events_task,
        "event-detail": workflow_tasks.scrap_event_detail_task,
        "match-detail": workflow_tasks.scrap_match_detail_task,
        "rankings": workflow_tasks.scrap_rankings_task,
        "nationality": workflow_tasks.enrich_fighter_nationality_task,
        "event-geocoding": workflow_tasks.enrich_event_geocoding_task,
        "tapology-profiles": tapology_tasks.enrich_fighter_tapology_profile_task,
        "tapology-bouts": tapology_tasks.enrich_match_tapology_metadata_task,
    }

    assert set(task_by_alias) == set(run_ufc_stats_flow.TASK_MAP)
    for alias, task in task_by_alias.items():
        assert task.name == alias
        assert task.task_run_name == alias
