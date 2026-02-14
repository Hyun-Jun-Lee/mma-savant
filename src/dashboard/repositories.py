"""
Dashboard 도메인 Repository
복잡한 집계 쿼리를 raw SQL(text)로 실행
"""
from typing import Optional, List, Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _wc_filter(
    weight_class_id: Optional[int], column: str = "m.weight_class_id"
) -> tuple[str, dict]:
    """체급 필터 SQL 조각과 파라미터를 동적으로 생성 (asyncpg 호환)"""
    if weight_class_id is not None:
        return f"AND {column} = :weight_class_id", {"weight_class_id": weight_class_id}
    return "", {}


# ===========================
# Tab 1: Home
# ===========================

async def get_summary(session: AsyncSession) -> Dict[str, int]:
    result = await session.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM fighter) AS total_fighters,
            (SELECT COUNT(*) FROM match) AS total_matches,
            (SELECT COUNT(*) FROM event) AS total_events
    """))
    row = result.mappings().one()
    return dict(row)


async def get_recent_events(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(text("""
        SELECT
            e.id,
            e.name,
            e.location,
            e.event_date,
            COUNT(m.id) AS total_fights,
            (
                SELECT f1.name || ' vs ' || f2.name
                FROM match main_m
                JOIN fighter_match fm1 ON main_m.id = fm1.match_id
                JOIN fighter_match fm2 ON main_m.id = fm2.match_id AND fm1.id < fm2.id
                JOIN fighter f1 ON fm1.fighter_id = f1.id
                JOIN fighter f2 ON fm2.fighter_id = f2.id
                WHERE main_m.event_id = e.id AND main_m.is_main_event = true
                LIMIT 1
            ) AS main_event
        FROM event e
        LEFT JOIN match m ON e.id = m.event_id
        WHERE e.event_date <= CURRENT_DATE
            AND e.event_date IS NOT NULL
        GROUP BY e.id, e.name, e.location, e.event_date
        ORDER BY e.event_date DESC
        LIMIT 5
    """))
    return [dict(row) for row in result.mappings().all()]


async def get_upcoming_events(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(text("""
        SELECT
            e.id,
            e.name,
            e.location,
            e.event_date,
            e.event_date - CURRENT_DATE AS days_until
        FROM event e
        WHERE e.event_date > CURRENT_DATE
            AND e.event_date IS NOT NULL
        ORDER BY e.event_date ASC
        LIMIT 5
    """))
    return [dict(row) for row in result.mappings().all()]


async def get_rankings(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(text("""
        SELECT
            wc.id AS weight_class_id,
            wc.name AS weight_class,
            r.ranking,
            f.name AS fighter_name,
            f.wins, f.losses, f.draws
        FROM ranking r
        JOIN fighter f ON r.fighter_id = f.id
        JOIN weight_class wc ON r.weight_class_id = wc.id
        ORDER BY wc.id, r.ranking
    """))
    return [dict(row) for row in result.mappings().all()]


# ===========================
# Tab 2: Overview
# ===========================

async def get_finish_methods(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    result = await session.execute(text(f"""
        SELECT
            CASE
                WHEN method LIKE 'KO-%' THEN 'KO'
                WHEN method LIKE 'TKO-%' THEN 'TKO'
                WHEN method LIKE 'SUB-%' THEN 'SUB'
                WHEN method LIKE 'U-DEC%' THEN 'U-DEC'
                WHEN method LIKE 'S-DEC%' THEN 'S-DEC'
                WHEN method LIKE 'M-DEC%' THEN 'M-DEC'
                ELSE 'Other'
            END AS method_category,
            COUNT(*) AS count
        FROM match m
        WHERE m.method IS NOT NULL
            {wc_clause}
        GROUP BY method_category
        ORDER BY count DESC
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_weight_class_activity(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(text("""
        SELECT
            wc.name AS weight_class,
            COUNT(*) AS total_fights,
            COUNT(CASE WHEN m.method LIKE 'KO-%' THEN 1 END) AS ko_count,
            COUNT(CASE WHEN m.method LIKE 'TKO-%' THEN 1 END) AS tko_count,
            COUNT(CASE WHEN m.method LIKE 'SUB-%' THEN 1 END) AS sub_count,
            ROUND(
                COUNT(CASE WHEN m.method LIKE 'KO-%' OR m.method LIKE 'TKO-%' OR m.method LIKE 'SUB-%' THEN 1 END) * 100.0 / COUNT(*), 1
            ) AS finish_rate,
            ROUND(COUNT(CASE WHEN m.method LIKE 'KO-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS ko_rate,
            ROUND(COUNT(CASE WHEN m.method LIKE 'TKO-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS tko_rate,
            ROUND(COUNT(CASE WHEN m.method LIKE 'SUB-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS sub_rate
        FROM match m
        JOIN weight_class wc ON m.weight_class_id = wc.id
        WHERE m.method IS NOT NULL
        GROUP BY wc.name
        ORDER BY total_fights DESC
    """))
    return [dict(row) for row in result.mappings().all()]


async def get_events_timeline(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(text("""
        SELECT
            EXTRACT(YEAR FROM event_date)::int AS year,
            COUNT(*) AS event_count
        FROM event
        WHERE event_date IS NOT NULL
        GROUP BY year
        ORDER BY year
    """))
    return [dict(row) for row in result.mappings().all()]


async def get_leaderboard_wins(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    if weight_class_id is not None:
        result = await session.execute(text("""
            SELECT
                f.name,
                COUNT(CASE WHEN fm.result = 'win' THEN 1 END) AS wins,
                COUNT(CASE WHEN fm.result = 'loss' THEN 1 END) AS losses,
                COUNT(CASE WHEN fm.result = 'draw' THEN 1 END) AS draws,
                ROUND(
                    COUNT(CASE WHEN fm.result = 'win' THEN 1 END) * 100.0 /
                    NULLIF(COUNT(*), 0), 1
                ) AS win_rate
            FROM fighter f
            JOIN fighter_match fm ON f.id = fm.fighter_id
            JOIN match m ON fm.match_id = m.id
            WHERE m.weight_class_id = :weight_class_id
            GROUP BY f.id, f.name
            ORDER BY wins DESC
            LIMIT 10
        """), {"weight_class_id": weight_class_id})
    else:
        result = await session.execute(text("""
            SELECT name, wins, losses, draws,
                ROUND(wins * 100.0 / NULLIF(wins + losses + draws, 0), 1) AS win_rate
            FROM fighter
            ORDER BY wins DESC
            LIMIT 10
        """))
    return [dict(row) for row in result.mappings().all()]


async def get_leaderboard_winrate(
    session: AsyncSession,
    min_fights: int,
    weight_class_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if weight_class_id is not None:
        result = await session.execute(text("""
            SELECT
                f.name,
                COUNT(CASE WHEN fm.result = 'win' THEN 1 END) AS wins,
                COUNT(CASE WHEN fm.result = 'loss' THEN 1 END) AS losses,
                COUNT(CASE WHEN fm.result = 'draw' THEN 1 END) AS draws,
                ROUND(
                    COUNT(CASE WHEN fm.result = 'win' THEN 1 END) * 100.0 /
                    NULLIF(COUNT(*), 0), 1
                ) AS win_rate
            FROM fighter f
            JOIN fighter_match fm ON f.id = fm.fighter_id
            JOIN match m ON fm.match_id = m.id
            WHERE m.weight_class_id = :weight_class_id
            GROUP BY f.id, f.name
            HAVING COUNT(*) >= :min_fights
            ORDER BY win_rate DESC
            LIMIT 10
        """), {"weight_class_id": weight_class_id, "min_fights": min_fights})
    else:
        result = await session.execute(text("""
            SELECT
                name, wins, losses, draws,
                ROUND(wins * 100.0 / NULLIF(wins + losses + draws, 0), 1) AS win_rate
            FROM fighter
            WHERE (wins + losses + draws) >= :min_fights
            ORDER BY win_rate DESC
            LIMIT 10
        """), {"min_fights": min_fights})
    return [dict(row) for row in result.mappings().all()]


async def get_fight_duration_rounds(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id, "weight_class_id")
    result = await session.execute(text(f"""
        SELECT
            result_round,
            COUNT(*) AS fight_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage
        FROM match
        WHERE result_round IS NOT NULL
            {wc_clause}
        GROUP BY result_round
        ORDER BY result_round
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_fight_duration_avg_round(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> float:
    wc_clause, params = _wc_filter(weight_class_id, "weight_class_id")
    result = await session.execute(text(f"""
        SELECT ROUND(AVG(result_round)::numeric, 1) AS avg_round
        FROM match
        WHERE result_round IS NOT NULL
            {wc_clause}
    """), params)
    row = result.mappings().one()
    return float(row["avg_round"]) if row["avg_round"] is not None else 0.0


# ===========================
# Tab 3: Striking
# ===========================

async def get_strike_targets(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            SUM(sd.head_strikes_landed) AS head,
            SUM(sd.body_strikes_landed) AS body,
            SUM(sd.leg_strikes_landed) AS leg,
            SUM(sd.clinch_strikes_landed) AS clinch,
            SUM(sd.ground_strikes_landed) AS ground
        FROM strike_detail sd
        JOIN fighter_match fm ON sd.fighter_match_id = fm.id
        JOIN match m ON fm.match_id = m.id
        {where_clause}
    """), params)
    row = result.mappings().one()
    return [
        {"target": "Head", "landed": row["head"] or 0},
        {"target": "Body", "landed": row["body"] or 0},
        {"target": "Leg", "landed": row["leg"] or 0},
        {"target": "Clinch", "landed": row["clinch"] or 0},
        {"target": "Ground", "landed": row["ground"] or 0},
    ]


async def get_striking_accuracy(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            f.name,
            SUM(ms.sig_str_landed) AS total_sig_landed,
            SUM(ms.sig_str_attempted) AS total_sig_attempted,
            ROUND(SUM(ms.sig_str_landed) * 100.0 / NULLIF(SUM(ms.sig_str_attempted), 0), 1) AS accuracy
        FROM match_statistics ms
        JOIN fighter_match fm ON ms.fighter_match_id = fm.id
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        {where_clause}
        GROUP BY f.id, f.name
        HAVING COUNT(DISTINCT fm.match_id) >= 5 AND SUM(ms.sig_str_attempted) > 0
        ORDER BY accuracy DESC
        LIMIT 10
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_ko_tko_leaders(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    result = await session.execute(text(f"""
        SELECT
            f.name,
            COUNT(CASE WHEN m.method LIKE 'KO-%' THEN 1 END) AS ko_finishes,
            COUNT(CASE WHEN m.method LIKE 'TKO-%' THEN 1 END) AS tko_finishes,
            COUNT(*) AS total_ko_tko
        FROM fighter_match fm
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        WHERE fm.result = 'win'
            AND (m.method LIKE 'KO-%' OR m.method LIKE 'TKO-%')
            {wc_clause}
        GROUP BY f.id, f.name
        ORDER BY total_ko_tko DESC
        LIMIT 10
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_sig_strikes_per_fight(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            f.name,
            ROUND(SUM(ms.sig_str_landed)::numeric / COUNT(DISTINCT fm.match_id), 2) AS sig_str_per_fight,
            COUNT(DISTINCT fm.match_id) AS total_fights
        FROM match_statistics ms
        JOIN fighter_match fm ON ms.fighter_match_id = fm.id
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        {where_clause}
        GROUP BY f.id, f.name
        HAVING COUNT(DISTINCT fm.match_id) >= 5
        ORDER BY sig_str_per_fight DESC
        LIMIT 10
    """), params)
    return [dict(row) for row in result.mappings().all()]


# ===========================
# Tab 4: Grappling
# ===========================

async def get_takedown_accuracy(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            f.name,
            SUM(ms.td_landed) AS total_td_landed,
            SUM(ms.td_attempted) AS total_td_attempted,
            ROUND(SUM(ms.td_landed) * 100.0 / NULLIF(SUM(ms.td_attempted), 0), 1) AS td_accuracy
        FROM match_statistics ms
        JOIN fighter_match fm ON ms.fighter_match_id = fm.id
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        {where_clause}
        GROUP BY f.id, f.name
        HAVING COUNT(DISTINCT fm.match_id) >= 5 AND SUM(ms.td_attempted) >= 10
        ORDER BY td_accuracy DESC
        LIMIT 10
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_submission_techniques(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    result = await session.execute(text(f"""
        SELECT
            REPLACE(m.method, 'SUB-', '') AS technique,
            COUNT(*) AS count
        FROM match m
        WHERE m.method LIKE 'SUB-%'
            {wc_clause}
        GROUP BY technique
        ORDER BY count DESC
        LIMIT 10
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_control_time(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(text("""
        SELECT
            wc.name AS weight_class,
            ROUND(AVG(ms.control_time_seconds), 0)::int AS avg_control_seconds,
            COUNT(DISTINCT fm.match_id) AS total_fights
        FROM match_statistics ms
        JOIN fighter_match fm ON ms.fighter_match_id = fm.id
        JOIN match m ON fm.match_id = m.id
        JOIN weight_class wc ON m.weight_class_id = wc.id
        WHERE ms.control_time_seconds > 0
        GROUP BY wc.name
        ORDER BY avg_control_seconds DESC
    """))
    return [dict(row) for row in result.mappings().all()]


async def get_ground_strikes(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            f.name,
            SUM(sd.ground_strikes_landed) AS total_ground_landed,
            SUM(sd.ground_strikes_attempts) AS total_ground_attempted,
            ROUND(SUM(sd.ground_strikes_landed) * 100.0 / NULLIF(SUM(sd.ground_strikes_attempts), 0), 1) AS accuracy
        FROM strike_detail sd
        JOIN fighter_match fm ON sd.fighter_match_id = fm.id
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        {where_clause}
        GROUP BY f.id, f.name
        HAVING COUNT(DISTINCT fm.match_id) >= 5 AND SUM(sd.ground_strikes_attempts) > 0
        ORDER BY total_ground_landed DESC
        LIMIT 10
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_submission_efficiency_fighters(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            f.name,
            SUM(ms.submission_attempts) AS total_sub_attempts,
            COUNT(CASE WHEN m.method LIKE 'SUB-%' AND fm.result = 'win' THEN 1 END) AS sub_finishes
        FROM match_statistics ms
        JOIN fighter_match fm ON ms.fighter_match_id = fm.id
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        {where_clause}
        GROUP BY f.id, f.name
        HAVING SUM(ms.submission_attempts) >= 5
            AND COUNT(DISTINCT fm.match_id) >= 5
        ORDER BY sub_finishes DESC
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_submission_efficiency_avg_ratio(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> float:
    wc_clause, params = _wc_filter(weight_class_id)
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            ROUND(
                SUM(sub_finishes)::numeric / NULLIF(SUM(total_sub_attempts), 0), 3
            ) AS avg_efficiency_ratio
        FROM (
            SELECT
                SUM(ms.submission_attempts) AS total_sub_attempts,
                COUNT(CASE WHEN m.method LIKE 'SUB-%' AND fm.result = 'win' THEN 1 END) AS sub_finishes
            FROM match_statistics ms
            JOIN fighter_match fm ON ms.fighter_match_id = fm.id
            JOIN fighter f ON fm.fighter_id = f.id
            JOIN match m ON fm.match_id = m.id
            {where_clause}
            GROUP BY f.id, f.name
            HAVING SUM(ms.submission_attempts) >= 5
                AND COUNT(DISTINCT fm.match_id) >= 5
        ) sub
    """), params)
    row = result.mappings().one()
    return float(row["avg_efficiency_ratio"]) if row["avg_efficiency_ratio"] is not None else 0.0
