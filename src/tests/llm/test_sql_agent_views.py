from pathlib import Path
from decimal import Decimal

import pytest
from sqlalchemy import text


VIEW_SQL_PATH = Path(__file__).resolve().parents[3] / "init_sqls" / "06_create_sql_agent_views.sql"


async def _apply_sql_agent_views(session):
    sql = VIEW_SQL_PATH.read_text(encoding="utf-8")
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            await session.execute(text(statement))


async def _scalar_id(session, statement: str, **params):
    result = await session.execute(text(statement), params)
    return result.scalar_one()


@pytest.mark.asyncio
async def test_priority_one_sql_agent_views(clean_test_session):
    await _apply_sql_agent_views(clean_test_session)

    alpha_id = await _scalar_id(
        clean_test_session,
        "INSERT INTO fighter (name, nickname) VALUES (:name, :nickname) RETURNING id",
        name="Alpha Fighter",
        nickname="Alpha",
    )
    beta_id = await _scalar_id(
        clean_test_session,
        "INSERT INTO fighter (name) VALUES (:name) RETURNING id",
        name="Beta Fighter",
    )
    gamma_id = await _scalar_id(
        clean_test_session,
        "INSERT INTO fighter (name) VALUES (:name) RETURNING id",
        name="Gamma Fighter",
    )

    past_event_id = await _scalar_id(
        clean_test_session,
        "INSERT INTO event (name, event_date, location) VALUES ('UFC Completed', '2024-01-01', 'las vegas, nevada, usa') RETURNING id",
    )
    future_event_id = await _scalar_id(
        clean_test_session,
        "INSERT INTO event (name, event_date, location) VALUES ('UFC Future', CURRENT_DATE + INTERVAL '10 days', 'seoul, south korea') RETURNING id",
    )

    completed_match_id = await _scalar_id(
        clean_test_session,
        """
        INSERT INTO match (
            event_id, weight_class_id, method, result_round, time, "order", is_main_event, is_title_bout, bout_status
        )
        VALUES (:event_id, 4, 'KO/TKO-Punch', 2, '3:12', 12, true, true, NULL)
        RETURNING id
        """,
        event_id=past_event_id,
    )
    cancelled_match_id = await _scalar_id(
        clean_test_session,
        """
        INSERT INTO match (event_id, weight_class_id, method, "order", bout_status)
        VALUES (:event_id, 4, NULL, 1, 'cancelled')
        RETURNING id
        """,
        event_id=past_event_id,
    )
    future_match_id = await _scalar_id(
        clean_test_session,
        """
        INSERT INTO match (event_id, weight_class_id, method, "order", bout_status)
        VALUES (:event_id, 4, NULL, 1, NULL)
        RETURNING id
        """,
        event_id=future_event_id,
    )

    await clean_test_session.execute(
        text(
            """
            INSERT INTO fighter_match (fighter_id, match_id, result) VALUES
            (:alpha_id, :completed_match_id, 'win'),
            (:beta_id, :completed_match_id, 'loss'),
            (:alpha_id, :cancelled_match_id, NULL),
            (:gamma_id, :cancelled_match_id, NULL),
            (:alpha_id, :future_match_id, NULL),
            (:gamma_id, :future_match_id, NULL)
            """
        ),
        {
            "alpha_id": alpha_id,
            "beta_id": beta_id,
            "gamma_id": gamma_id,
            "completed_match_id": completed_match_id,
            "cancelled_match_id": cancelled_match_id,
            "future_match_id": future_match_id,
        },
    )
    await clean_test_session.execute(
        text("INSERT INTO ranking (fighter_id, weight_class_id, ranking) VALUES (:fighter_id, 4, 0)"),
        {"fighter_id": alpha_id},
    )

    completed_rows = (
        await clean_test_session.execute(
            text("SELECT fighter_id, result, is_ko_tko, is_finish FROM v_completed_fighter_fights ORDER BY fighter_id")
        )
    ).mappings().all()
    assert completed_rows == [
        {"fighter_id": alpha_id, "result": "win", "is_ko_tko": True, "is_finish": True},
        {"fighter_id": beta_id, "result": "loss", "is_ko_tko": True, "is_finish": True},
    ]

    opponent = (
        await clean_test_session.execute(
            text(
                """
                SELECT opponent_id, opponent_name, is_title_bout
                FROM v_fighter_opponents
                WHERE fighter_id = :fighter_id
                """
            ),
            {"fighter_id": alpha_id},
        )
    ).mappings().one()
    assert opponent == {
        "opponent_id": beta_id,
        "opponent_name": "Beta Fighter",
        "is_title_bout": True,
    }

    method_summary = (
        await clean_test_session.execute(
            text(
                """
                SELECT ko_tko_wins, finish_wins, finish_win_rate_over_wins, finish_win_rate_over_total_fights
                FROM v_fighter_method_summary
                WHERE fighter_id = :fighter_id
                """
            ),
            {"fighter_id": alpha_id},
        )
    ).mappings().one()
    assert method_summary == {
        "ko_tko_wins": 1,
        "finish_wins": 1,
        "finish_win_rate_over_wins": Decimal("100.00"),
        "finish_win_rate_over_total_fights": Decimal("100.00"),
    }

    champion = (
        await clean_test_session.execute(
            text("SELECT is_champion, display_rank FROM v_current_rankings WHERE fighter_id = :fighter_id"),
            {"fighter_id": alpha_id},
        )
    ).mappings().one()
    assert champion == {"is_champion": True, "display_rank": "champion"}
