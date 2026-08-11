import logging

import pytest

from data_collector.workflows import tasks


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
