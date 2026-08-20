from datetime import date
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text

from data_collector.workflows.data_store import save_fighter_match, save_match
from match.models import MatchSchema


BONUS_METADATA_SQL_PATH = (
    Path(__file__).resolve().parents[3] / "init_sqls" / "06_add_ufcstats_bonus_metadata.sql"
)
TAPOLOGY_ENRICHMENT_SQL_PATH = (
    Path(__file__).resolve().parents[3] / "init_sqls" / "05_add_tapology_enrichment.sql"
)


async def _apply_bonus_metadata_sql(session):
    for path in (TAPOLOGY_ENRICHMENT_SQL_PATH, BONUS_METADATA_SQL_PATH):
        sql = path.read_text(encoding="utf-8")
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                await session.execute(text(statement))


async def _scalar_id(session, statement: str, **params):
    result = await session.execute(text(statement), params)
    return result.scalar_one()


async def _cleanup_bonus_data_store_rows(session):
    await session.execute(
        text(
            """
            DELETE FROM fighter_match
            WHERE match_id IN (
                SELECT id FROM match
                WHERE detail_url IN (
                    'http://ufcstats.com/fight-details/bonus',
                    'http://ufcstats.com/fight-details/performance'
                )
            )
            """
        )
    )
    await session.execute(
        text(
            """
            DELETE FROM match
            WHERE detail_url IN (
                'http://ufcstats.com/fight-details/bonus',
                'http://ufcstats.com/fight-details/performance'
            )
            """
        )
    )
    await session.execute(text("DELETE FROM fighter WHERE name = 'Bonus Winner'"))
    await session.execute(text("DELETE FROM event WHERE name = 'UFC Bonus Test'"))
    await session.commit()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_bonus_data_store_rows(clean_test_session):
    await _cleanup_bonus_data_store_rows(clean_test_session)
    yield
    await _cleanup_bonus_data_store_rows(clean_test_session)


@pytest.mark.asyncio
async def test_save_match_preserves_existing_true_bonus_flags(clean_test_session):
    await _apply_bonus_metadata_sql(clean_test_session)
    event_id = await _scalar_id(
        clean_test_session,
        "INSERT INTO event (name, event_date) VALUES (:name, :event_date) RETURNING id",
        name="UFC Bonus Test",
        event_date=date(2024, 1, 1),
    )

    saved = await save_match(
        clean_test_session,
        MatchSchema(
            event_id=event_id,
            detail_url="http://ufcstats.com/fight-details/bonus",
            is_title_bout=True,
            has_fight_of_the_night_bonus=True,
        ),
    )

    refreshed = await save_match(
        clean_test_session,
        MatchSchema(
            event_id=event_id,
            detail_url=saved.detail_url,
            is_title_bout=False,
            has_fight_of_the_night_bonus=False,
        ),
    )

    assert refreshed.is_title_bout is True
    assert refreshed.has_fight_of_the_night_bonus is True


@pytest.mark.asyncio
async def test_save_fighter_match_preserves_existing_performance_bonus(clean_test_session):
    await _apply_bonus_metadata_sql(clean_test_session)
    fighter_id = await _scalar_id(
        clean_test_session,
        "INSERT INTO fighter (name) VALUES (:name) RETURNING id",
        name="Bonus Winner",
    )
    event_id = await _scalar_id(
        clean_test_session,
        "INSERT INTO event (name, event_date) VALUES (:name, :event_date) RETURNING id",
        name="UFC Bonus Test",
        event_date=date(2024, 1, 1),
    )

    saved_match = await save_match(
        clean_test_session,
        MatchSchema(
            event_id=event_id,
            detail_url="http://ufcstats.com/fight-details/performance",
        ),
    )

    saved = await save_fighter_match(
        clean_test_session,
        fighter_id,
        saved_match.id,
        "win",
        has_performance_of_the_night_bonus=True,
    )
    assert saved.has_performance_of_the_night_bonus is True

    refreshed = await save_fighter_match(
        clean_test_session,
        fighter_id,
        saved_match.id,
        "win",
        has_performance_of_the_night_bonus=False,
    )

    assert refreshed.has_performance_of_the_night_bonus is True
