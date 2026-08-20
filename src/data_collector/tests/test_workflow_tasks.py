import logging
import asyncio
from types import SimpleNamespace

import pytest

from data_collector.workflows import tasks
from event.models import EventSchema
from match.models import MatchSchema


@pytest.mark.asyncio
async def test_replace_rankings_if_not_empty_preserves_existing_rankings_on_empty_result(monkeypatch):
    calls = []

    async def delete_all_rankings(session):
        calls.append("delete")

    async def save_rankings(session, rankings):
        calls.append(("save", rankings))

    monkeypatch.setattr(tasks, "delete_all_rankings", delete_all_rankings)
    monkeypatch.setattr(tasks, "save_rankings", save_rankings)

    saved = await tasks.replace_rankings_if_not_empty(
        object(),
        [],
        logging.getLogger(__name__),
    )

    assert saved is False
    assert calls == []


@pytest.mark.asyncio
async def test_replace_rankings_if_not_empty_replaces_rankings_when_result_exists(monkeypatch):
    calls = []

    async def delete_all_rankings(session):
        calls.append("delete")

    async def save_rankings(session, rankings):
        calls.append(("save", rankings))

    monkeypatch.setattr(tasks, "delete_all_rankings", delete_all_rankings)
    monkeypatch.setattr(tasks, "save_rankings", save_rankings)

    rankings = [object()]
    saved = await tasks.replace_rankings_if_not_empty(
        object(),
        rankings,
        logging.getLogger(__name__),
    )

    assert saved is True
    assert calls == ["delete", ("save", rankings)]


@pytest.mark.asyncio
async def test_process_event_detail_passes_performance_bonus_to_fighter_match_save(monkeypatch):
    calls = []
    fake_session = object()

    class FakeDbContext:
        async def __aenter__(self):
            return fake_session

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    async def scrap_event_detail(crawler_fn, event_url, event_id, fighter_lookup):
        return [
            {
                "match": MatchSchema(
                    event_id=event_id,
                    detail_url="http://ufcstats.com/fight-details/performance",
                ),
                "fighters": [
                    {
                        "fighter_id": 10,
                        "result": "win",
                        "has_performance_of_the_night_bonus": True,
                    },
                    {
                        "fighter_id": 20,
                        "result": "loss",
                        "has_performance_of_the_night_bonus": False,
                    },
                ],
            }
        ]

    async def save_match(session, match):
        calls.append(("save_match", session, match.detail_url))
        return SimpleNamespace(id=99, detail_url=match.detail_url)

    async def save_fighter_match(
        session,
        fighter_id,
        match_id,
        result,
        has_performance_of_the_night_bonus=False,
    ):
        calls.append(
            (
                "save_fighter_match",
                session,
                fighter_id,
                match_id,
                result,
                has_performance_of_the_night_bonus,
            )
        )

    monkeypatch.setattr(tasks, "RANDOM_DELAY", 0)
    monkeypatch.setattr(tasks, "get_async_db_context", lambda: FakeDbContext())
    monkeypatch.setattr(tasks, "scrap_event_detail", scrap_event_detail)
    monkeypatch.setattr(tasks, "save_match", save_match)
    monkeypatch.setattr(tasks, "save_fighter_match", save_fighter_match)

    await tasks.process_event_detail(
        0,
        EventSchema(id=1, name="UFC Bonus Test", url="http://ufcstats.com/event-details/example"),
        object(),
        {},
        1,
        asyncio.Semaphore(1),
        logging.getLogger(__name__),
    )

    assert calls == [
        ("save_match", fake_session, "http://ufcstats.com/fight-details/performance"),
        ("save_fighter_match", fake_session, 10, 99, "win", True),
        ("save_fighter_match", fake_session, 20, 99, "loss", False),
    ]
