from pathlib import Path
from decimal import Decimal

import pytest
from sqlalchemy import text


VIEW_SQL_PATH = Path(__file__).resolve().parents[3] / "init_sqls" / "06_create_sql_agent_views.sql"
BONUS_METADATA_SQL_PATH = (
    Path(__file__).resolve().parents[3] / "init_sqls" / "06_add_ufcstats_bonus_metadata.sql"
)


async def _apply_sql_file(session, path: Path):
    sql = path.read_text(encoding="utf-8")
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            if "\\set" in statement or "GRANT " in statement.upper():
                continue
            await session.execute(text(statement))


async def _apply_sql_agent_views(session):
    await _apply_sql_file(session, VIEW_SQL_PATH)


def test_sql_agent_view_script_refreshes_readonly_grants():
    sql = VIEW_SQL_PATH.read_text(encoding="utf-8")

    assert 'GRANT USAGE ON SCHEMA public TO :"sql_agent_readonly_user"' in sql
    assert "fighter_match" in sql
    assert "v_fighter_opponents" in sql
    assert sql.count("GRANT SELECT ON") >= 2


async def _scalar_id(session, statement: str, **params):
    result = await session.execute(text(statement), params)
    return result.scalar_one()


@pytest.mark.asyncio
async def test_priority_one_sql_agent_views(clean_test_session):
    await _apply_sql_file(clean_test_session, BONUS_METADATA_SQL_PATH)
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
            event_id, weight_class_id, method, result_round, time, "order", is_main_event,
            is_title_bout, has_fight_of_the_night_bonus, bout_status
        )
        VALUES (:event_id, 4, 'KO/TKO-Punch', 2, '3:12', 12, true, true, true, NULL)
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
            INSERT INTO fighter_match (
                fighter_id, match_id, result, has_performance_of_the_night_bonus
            ) VALUES
            (:alpha_id, :completed_match_id, 'win', true),
            (:beta_id, :completed_match_id, 'loss', false),
            (:alpha_id, :cancelled_match_id, NULL, false),
            (:gamma_id, :cancelled_match_id, NULL, false),
            (:alpha_id, :future_match_id, NULL, false),
            (:gamma_id, :future_match_id, NULL, false)
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
            text(
                """
                SELECT
                    fighter_id,
                    result,
                    is_title_bout,
                    has_fight_of_the_night_bonus,
                    has_performance_of_the_night_bonus,
                    is_ko_tko,
                    is_finish
                FROM v_completed_fighter_fights
                WHERE event_name = 'UFC Completed'
                ORDER BY fighter_id
                """
            )
        )
    ).mappings().all()
    assert completed_rows == [
        {
            "fighter_id": alpha_id,
            "result": "win",
            "is_title_bout": True,
            "has_fight_of_the_night_bonus": True,
            "has_performance_of_the_night_bonus": True,
            "is_ko_tko": True,
            "is_finish": True,
        },
        {
            "fighter_id": beta_id,
            "result": "loss",
            "is_title_bout": True,
            "has_fight_of_the_night_bonus": True,
            "has_performance_of_the_night_bonus": False,
            "is_ko_tko": True,
            "is_finish": True,
        },
    ]

    opponent = (
        await clean_test_session.execute(
            text(
                """
                SELECT
                    opponent_id,
                    opponent_name,
                    is_title_bout,
                    has_fight_of_the_night_bonus,
                    has_performance_of_the_night_bonus
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
        "has_fight_of_the_night_bonus": True,
        "has_performance_of_the_night_bonus": True,
    }

    method_summary = (
        await clean_test_session.execute(
            text(
                """
                SELECT ko_tko_wins, finish_wins, finish_rate
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
        "finish_rate": Decimal("100.00"),
    }

    record_summary = (
        await clean_test_session.execute(
            text(
                """
                SELECT wins, losses, draws, no_contests, win_rate
                FROM v_fighter_record_summary
                WHERE fighter_id = :fighter_id
                """
            ),
            {"fighter_id": alpha_id},
        )
    ).mappings().one()
    assert record_summary == {
        "wins": 1,
        "losses": 0,
        "draws": 0,
        "no_contests": 0,
        "win_rate": Decimal("100.00"),
    }

    champion = (
        await clean_test_session.execute(
            text("SELECT is_champion, display_rank FROM v_current_rankings WHERE fighter_id = :fighter_id"),
            {"fighter_id": alpha_id},
        )
    ).mappings().one()
    assert champion == {"is_champion": True, "display_rank": "champion"}
