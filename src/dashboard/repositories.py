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
            f.id AS fighter_id,
            f.name AS fighter_name,
            f.wins, f.losses, f.draws
        FROM ranking r
        JOIN fighter f ON r.fighter_id = f.id
        JOIN weight_class wc ON r.weight_class_id = wc.id
        ORDER BY wc.id, r.ranking
    """))
    return [dict(row) for row in result.mappings().all()]


async def get_event_map(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(text("""
        SELECT
            location,
            latitude,
            longitude,
            COUNT(*) AS event_count,
            MAX(event_date) AS last_event_date,
            (
                SELECT e2.name FROM event e2
                WHERE e2.location = e.location
                ORDER BY e2.event_date DESC
                LIMIT 1
            ) AS last_event_name
        FROM event e
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        GROUP BY location, latitude, longitude
        ORDER BY event_count DESC
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
                WHEN method LIKE 'KO/TKO%' THEN 'KO/TKO'
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
            COUNT(CASE WHEN m.method LIKE 'KO/TKO%' THEN 1 END) AS ko_tko_count,
            COUNT(CASE WHEN m.method LIKE 'SUB-%' THEN 1 END) AS sub_count,
            ROUND(
                COUNT(CASE WHEN m.method LIKE 'KO/TKO%' OR m.method LIKE 'SUB-%' THEN 1 END) * 100.0 / COUNT(*), 1
            ) AS finish_rate,
            ROUND(COUNT(CASE WHEN m.method LIKE 'KO/TKO%' THEN 1 END) * 100.0 / COUNT(*), 1) AS ko_tko_rate,
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
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    limit: int = 10,
    ufc_only: bool = False,
) -> List[Dict[str, Any]]:
    method_cols = """
                COUNT(CASE WHEN fm.result = 'win' AND m.method LIKE 'KO/TKO%' THEN 1 END) AS ko_tko_wins,
                COUNT(CASE WHEN fm.result = 'win' AND m.method LIKE 'SUB-%' THEN 1 END) AS sub_wins,
                COUNT(CASE WHEN fm.result = 'win' THEN 1 END)
                  - COUNT(CASE WHEN fm.result = 'win' AND m.method LIKE 'KO/TKO%' THEN 1 END)
                  - COUNT(CASE WHEN fm.result = 'win' AND m.method LIKE 'SUB-%' THEN 1 END) AS dec_wins
    """

    if weight_class_id is not None:
        result = await session.execute(text(f"""
            SELECT
                f.id AS fighter_id,
                f.name,
                COUNT(CASE WHEN fm.result = 'win' THEN 1 END) AS wins,
                COUNT(CASE WHEN fm.result = 'loss' THEN 1 END) AS losses,
                COUNT(CASE WHEN fm.result = 'draw' THEN 1 END) AS draws,
                {method_cols}
            FROM fighter f
            JOIN fighter_match fm ON f.id = fm.fighter_id
            JOIN match m ON fm.match_id = m.id
            WHERE m.weight_class_id = :weight_class_id
            GROUP BY f.id, f.name
            ORDER BY wins DESC
            LIMIT :limit
        """), {"weight_class_id": weight_class_id, "limit": limit})
    elif ufc_only:
        result = await session.execute(text(f"""
            SELECT
                f.id AS fighter_id,
                f.name,
                COUNT(CASE WHEN fm.result = 'win' THEN 1 END) AS wins,
                COUNT(CASE WHEN fm.result = 'loss' THEN 1 END) AS losses,
                COUNT(CASE WHEN fm.result = 'draw' THEN 1 END) AS draws,
                {method_cols}
            FROM fighter f
            JOIN fighter_match fm ON f.id = fm.fighter_id
            JOIN match m ON fm.match_id = m.id
            GROUP BY f.id, f.name
            ORDER BY wins DESC
            LIMIT :limit
        """), {"limit": limit})
    else:
        result = await session.execute(text(f"""
            SELECT
                f.id AS fighter_id,
                f.name,
                COUNT(CASE WHEN fm.result = 'win' THEN 1 END) AS wins,
                COUNT(CASE WHEN fm.result = 'loss' THEN 1 END) AS losses,
                COUNT(CASE WHEN fm.result = 'draw' THEN 1 END) AS draws,
                {method_cols}
            FROM fighter f
            JOIN fighter_match fm ON f.id = fm.fighter_id
            JOIN match m ON fm.match_id = m.id
            GROUP BY f.id, f.name
            ORDER BY wins DESC
            LIMIT :limit
        """), {"limit": limit})
    return [dict(row) for row in result.mappings().all()]



async def get_win_streak_leaders(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """현재 연승 중인 선수 TOP N (최근 경기부터 역순으로 연승 계산)"""
    wc_clause, params = _wc_filter(weight_class_id)
    params["limit"] = limit
    result = await session.execute(text(f"""
        WITH ordered_fights AS (
            SELECT
                f.id AS fighter_id,
                f.name,
                f.wins, f.losses, f.draws,
                fm.result,
                ROW_NUMBER() OVER (
                    PARTITION BY f.id ORDER BY e.event_date DESC, m.id DESC
                ) AS rn
            FROM fighter f
            JOIN fighter_match fm ON f.id = fm.fighter_id
            JOIN match m ON fm.match_id = m.id
            JOIN event e ON m.event_id = e.id
            WHERE fm.result IN ('win', 'loss')
                AND e.event_date IS NOT NULL
                {wc_clause}
        ),
        first_loss AS (
            SELECT fighter_id, MIN(rn) AS first_loss_rn
            FROM ordered_fights
            WHERE result = 'loss'
            GROUP BY fighter_id
        )
        SELECT
            o.fighter_id,
            o.name,
            o.wins, o.losses, o.draws,
            COUNT(*) AS win_streak
        FROM ordered_fights o
        LEFT JOIN first_loss fl ON o.fighter_id = fl.fighter_id
        WHERE o.result = 'win'
            AND o.rn < COALESCE(fl.first_loss_rn, 999999)
        GROUP BY o.fighter_id, o.name, o.wins, o.losses, o.draws
        ORDER BY win_streak DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_lose_streak_leaders(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """현재 연패 중인 선수 TOP N (최근 경기부터 역순으로 연패 계산)"""
    wc_clause, params = _wc_filter(weight_class_id)
    params["limit"] = limit
    result = await session.execute(text(f"""
        WITH ordered_fights AS (
            SELECT
                f.id AS fighter_id,
                f.name,
                f.wins, f.losses, f.draws,
                fm.result,
                ROW_NUMBER() OVER (
                    PARTITION BY f.id ORDER BY e.event_date DESC, m.id DESC
                ) AS rn
            FROM fighter f
            JOIN fighter_match fm ON f.id = fm.fighter_id
            JOIN match m ON fm.match_id = m.id
            JOIN event e ON m.event_id = e.id
            WHERE fm.result IN ('win', 'loss')
                AND e.event_date IS NOT NULL
                {wc_clause}
        ),
        first_win AS (
            SELECT fighter_id, MIN(rn) AS first_win_rn
            FROM ordered_fights
            WHERE result = 'win'
            GROUP BY fighter_id
        )
        SELECT
            o.fighter_id,
            o.name,
            o.wins, o.losses, o.draws,
            COUNT(*) AS lose_streak
        FROM ordered_fights o
        LEFT JOIN first_win fw ON o.fighter_id = fw.fighter_id
        WHERE o.result = 'loss'
            AND o.rn < COALESCE(fw.first_win_rn, 999999)
        GROUP BY o.fighter_id, o.name, o.wins, o.losses, o.draws
        ORDER BY lose_streak DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_fight_duration_rounds(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id, "weight_class_id")
    result = await session.execute(text(f"""
        SELECT
            result_round,
            COUNT(*) AS fight_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage,
            COUNT(CASE WHEN method LIKE 'KO/TKO%' THEN 1 END) AS ko_tko,
            COUNT(CASE WHEN method LIKE 'SUB-%' THEN 1 END) AS submission,
            COUNT(*) - COUNT(CASE WHEN method LIKE 'KO/TKO%' THEN 1 END)
                     - COUNT(CASE WHEN method LIKE 'SUB-%' THEN 1 END) AS decision_other
        FROM match
        WHERE result_round IS NOT NULL
            {wc_clause}
        GROUP BY result_round
        ORDER BY result_round
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_fight_duration_avg_time(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> Optional[int]:
    """평균 종료 시간(초) 계산. match.time은 'M:SS' 문자열."""
    wc_clause, params = _wc_filter(weight_class_id, "weight_class_id")
    result = await session.execute(text(f"""
        SELECT ROUND(AVG(
            CAST(SPLIT_PART(time, ':', 1) AS INTEGER) * 60 +
            CAST(SPLIT_PART(time, ':', 2) AS INTEGER)
        ))::int AS avg_time_seconds
        FROM match
        WHERE time IS NOT NULL AND result_round IS NOT NULL
            {wc_clause}
    """), params)
    row = result.mappings().one()
    return row["avg_time_seconds"]


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
    session: AsyncSession, weight_class_id: Optional[int] = None, min_fights: int = 10, limit: int = 10
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["min_fights"] = min_fights
    params["limit"] = limit
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            f.id AS fighter_id,
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
        HAVING COUNT(DISTINCT fm.match_id) >= :min_fights AND SUM(ms.sig_str_attempted) > 0
        ORDER BY accuracy DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_ko_tko_leaders(
    session: AsyncSession, weight_class_id: Optional[int] = None, limit: int = 10
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["limit"] = limit
    result = await session.execute(text(f"""
        SELECT
            f.id AS fighter_id,
            f.name,
            COUNT(*) AS ko_tko_finishes
        FROM fighter_match fm
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        WHERE fm.result = 'win'
            AND m.method LIKE 'KO/TKO%'
            {wc_clause}
        GROUP BY f.id, f.name
        ORDER BY ko_tko_finishes DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_sig_strikes_per_fight(
    session: AsyncSession, weight_class_id: Optional[int] = None, min_fights: int = 10, limit: int = 10
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["min_fights"] = min_fights
    params["limit"] = limit
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            f.id AS fighter_id,
            f.name,
            ROUND(SUM(ms.sig_str_landed)::numeric / COUNT(DISTINCT fm.match_id), 2) AS sig_str_per_fight,
            COUNT(DISTINCT fm.match_id) AS total_fights
        FROM match_statistics ms
        JOIN fighter_match fm ON ms.fighter_match_id = fm.id
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        {where_clause}
        GROUP BY f.id, f.name
        HAVING COUNT(DISTINCT fm.match_id) >= :min_fights
        ORDER BY sig_str_per_fight DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


# ===========================
# Tab 4: Grappling
# ===========================

async def get_takedown_accuracy(
    session: AsyncSession, weight_class_id: Optional[int] = None, min_fights: int = 10, limit: int = 10
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["min_fights"] = min_fights
    params["limit"] = limit
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            f.id AS fighter_id,
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
        HAVING COUNT(DISTINCT fm.match_id) >= :min_fights AND SUM(ms.td_attempted) >= :min_fights
        ORDER BY td_accuracy DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_submission_techniques(
    session: AsyncSession, weight_class_id: Optional[int] = None, limit: int = 10
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["limit"] = limit
    result = await session.execute(text(f"""
        SELECT
            REPLACE(m.method, 'SUB-', '') AS technique,
            COUNT(*) AS count
        FROM match m
        WHERE m.method LIKE 'SUB-%'
            {wc_clause}
        GROUP BY technique
        ORDER BY count DESC
        LIMIT :limit
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
    session: AsyncSession, weight_class_id: Optional[int] = None, min_fights: int = 10, limit: int = 10
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["min_fights"] = min_fights
    params["limit"] = limit
    if not wc_clause:
        where_clause = ""
    else:
        where_clause = f"WHERE {wc_clause.lstrip('AND ')}"
    result = await session.execute(text(f"""
        SELECT
            f.id AS fighter_id,
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
        HAVING COUNT(DISTINCT fm.match_id) >= :min_fights AND SUM(sd.ground_strikes_attempts) > 0
        ORDER BY total_ground_landed DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_submission_efficiency_fighters(
    session: AsyncSession, weight_class_id: Optional[int] = None, min_fights: int = 10, limit: int = 10
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["min_fights"] = min_fights
    params["limit"] = limit
    result = await session.execute(text(f"""
        WITH per_fight AS (
            SELECT
                fm.fighter_id,
                fm.match_id,
                SUM(ms.submission_attempts) AS fight_sub_attempts,
                MAX(CASE WHEN m.method LIKE 'SUB-%%' AND fm.result = 'win'
                         THEN 1 ELSE 0 END) AS is_sub_win
            FROM match_statistics ms
            JOIN fighter_match fm ON ms.fighter_match_id = fm.id
            JOIN match m ON fm.match_id = m.id
            WHERE 1=1 {wc_clause}
            GROUP BY fm.fighter_id, fm.match_id
        )
        SELECT
            f.id AS fighter_id,
            f.name,
            GREATEST(SUM(pf.fight_sub_attempts), SUM(pf.is_sub_win))::int AS total_sub_attempts,
            SUM(pf.is_sub_win)::int AS sub_finishes
        FROM per_fight pf
        JOIN fighter f ON pf.fighter_id = f.id
        GROUP BY f.id, f.name
        HAVING COUNT(*) >= :min_fights
        ORDER BY sub_finishes DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


# ===========================
# Tab 1: Home — Category Leaders
# ===========================

async def get_category_leaders(session: AsyncSession) -> List[Dict[str, Any]]:
    """8개 분야별 역대 1위 선수 조회"""
    result = await session.execute(text("""
        WITH
        most_wins AS (
            SELECT 'most_wins' AS category, '최다승' AS label, f.id AS fighter_id, f.name,
                   f.wins::numeric AS value, 'wins' AS unit
            FROM fighter f ORDER BY f.wins DESC LIMIT 1
        ),
        best_winrate AS (
            SELECT 'best_winrate' AS category, '최고 승률' AS label, f.id AS fighter_id, f.name,
                   ROUND(f.wins * 100.0 / NULLIF(f.wins + f.losses + f.draws, 0), 1) AS value, '%' AS unit
            FROM fighter f
            WHERE (f.wins + f.losses + f.draws) >= 10
            ORDER BY value DESC LIMIT 1
        ),
        most_ko_tko AS (
            SELECT 'most_ko_tko' AS category, 'KO/TKO 최다' AS label, f.id AS fighter_id, f.name,
                   COUNT(*)::numeric AS value, 'finishes' AS unit
            FROM fighter_match fm
            JOIN fighter f ON fm.fighter_id = f.id
            JOIN match m ON fm.match_id = m.id
            WHERE fm.result = 'win' AND m.method LIKE 'KO/TKO%'
            GROUP BY f.id, f.name ORDER BY value DESC LIMIT 1
        ),
        most_submissions AS (
            SELECT 'most_submissions' AS category, '서브미션 최다' AS label, f.id AS fighter_id, f.name,
                   COUNT(*)::numeric AS value, 'finishes' AS unit
            FROM fighter_match fm
            JOIN fighter f ON fm.fighter_id = f.id
            JOIN match m ON fm.match_id = m.id
            WHERE fm.result = 'win' AND m.method LIKE 'SUB-%'
            GROUP BY f.id, f.name ORDER BY value DESC LIMIT 1
        ),
        best_striking_acc AS (
            SELECT 'best_striking_acc' AS category, '타격 정확도' AS label, f.id AS fighter_id, f.name,
                   ROUND(SUM(ms.sig_str_landed) * 100.0 / NULLIF(SUM(ms.sig_str_attempted), 0), 1) AS value,
                   '%' AS unit
            FROM match_statistics ms
            JOIN fighter_match fm ON ms.fighter_match_id = fm.id
            JOIN fighter f ON fm.fighter_id = f.id
            GROUP BY f.id, f.name
            HAVING COUNT(DISTINCT fm.match_id) >= 10 AND SUM(ms.sig_str_attempted) > 0
            ORDER BY value DESC LIMIT 1
        ),
        most_sig_str AS (
            SELECT 'most_sig_str' AS category, '경기당 유효타격' AS label, f.id AS fighter_id, f.name,
                   ROUND(SUM(ms.sig_str_landed)::numeric / COUNT(DISTINCT fm.match_id), 2) AS value,
                   'per fight' AS unit
            FROM match_statistics ms
            JOIN fighter_match fm ON ms.fighter_match_id = fm.id
            JOIN fighter f ON fm.fighter_id = f.id
            GROUP BY f.id, f.name
            HAVING COUNT(DISTINCT fm.match_id) >= 10
            ORDER BY value DESC LIMIT 1
        ),
        best_td_acc AS (
            SELECT 'best_td_acc' AS category, '테이크다운 성공률' AS label, f.id AS fighter_id, f.name,
                   ROUND(SUM(ms.td_landed) * 100.0 / NULLIF(SUM(ms.td_attempted), 0), 1) AS value,
                   '%' AS unit
            FROM match_statistics ms
            JOIN fighter_match fm ON ms.fighter_match_id = fm.id
            JOIN fighter f ON fm.fighter_id = f.id
            GROUP BY f.id, f.name
            HAVING COUNT(DISTINCT fm.match_id) >= 10 AND SUM(ms.td_attempted) >= 10
            ORDER BY value DESC LIMIT 1
        ),
        most_knockdowns AS (
            SELECT 'most_knockdowns' AS category, '넉다운 최다' AS label, f.id AS fighter_id, f.name,
                   SUM(ms.knockdowns)::numeric AS value, 'knockdowns' AS unit
            FROM match_statistics ms
            JOIN fighter_match fm ON ms.fighter_match_id = fm.id
            JOIN fighter f ON fm.fighter_id = f.id
            GROUP BY f.id, f.name
            ORDER BY value DESC LIMIT 1
        )
        SELECT * FROM most_wins
        UNION ALL SELECT * FROM best_winrate
        UNION ALL SELECT * FROM most_ko_tko
        UNION ALL SELECT * FROM most_submissions
        UNION ALL SELECT * FROM best_striking_acc
        UNION ALL SELECT * FROM most_sig_str
        UNION ALL SELECT * FROM best_td_acc
        UNION ALL SELECT * FROM most_knockdowns
    """))
    return [dict(row) for row in result.mappings().all()]


# ===========================
# Tab 2: Overview — New charts
# ===========================

async def get_finish_rate_trend(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    result = await session.execute(text(f"""
        SELECT
            EXTRACT(YEAR FROM e.event_date)::int AS year,
            COUNT(*) AS total_fights,
            ROUND(COUNT(CASE WHEN m.method LIKE 'KO/TKO%' OR m.method LIKE 'KO-%' OR m.method LIKE 'TKO-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS ko_tko_rate,
            ROUND(COUNT(CASE WHEN m.method LIKE 'SUB-%' THEN 1 END) * 100.0 / COUNT(*), 1) AS sub_rate,
            ROUND(COUNT(CASE WHEN m.method LIKE '%-DEC%' THEN 1 END) * 100.0 / COUNT(*), 1) AS dec_rate
        FROM match m
        JOIN event e ON m.event_id = e.id
        WHERE e.event_date IS NOT NULL
            AND m.method IS NOT NULL
            {wc_clause}
        GROUP BY year
        HAVING COUNT(*) >= 10
        ORDER BY year
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_nationality_distribution(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    if weight_class_id is not None:
        result = await session.execute(text("""
            SELECT
                f.nationality,
                COUNT(DISTINCT f.id) AS fighter_count
            FROM fighter f
            JOIN fighter_match fm ON f.id = fm.fighter_id
            JOIN match m ON fm.match_id = m.id
            WHERE f.nationality IS NOT NULL
                AND m.weight_class_id = :weight_class_id
            GROUP BY f.nationality
            ORDER BY fighter_count DESC
        """), {"weight_class_id": weight_class_id})
    else:
        result = await session.execute(text("""
            SELECT
                f.nationality,
                COUNT(*) AS fighter_count
            FROM fighter f
            WHERE f.nationality IS NOT NULL
            GROUP BY f.nationality
            ORDER BY fighter_count DESC
        """))
    return [dict(row) for row in result.mappings().all()]


# ===========================
# Tab 3: Striking — New charts
# ===========================

async def get_knockdown_leaders(
    session: AsyncSession, weight_class_id: Optional[int] = None, limit: int = 10
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["limit"] = limit
    result = await session.execute(text(f"""
        SELECT
            f.id AS fighter_id,
            f.name,
            SUM(ms.knockdowns) AS total_knockdowns,
            COUNT(DISTINCT fm.match_id) AS total_fights,
            ROUND(SUM(ms.knockdowns)::numeric / COUNT(DISTINCT fm.match_id), 2) AS kd_per_fight
        FROM match_statistics ms
        JOIN fighter_match fm ON ms.fighter_match_id = fm.id
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        WHERE ms.knockdowns > 0
            {wc_clause}
        GROUP BY f.id, f.name
        HAVING SUM(ms.knockdowns) > 0
        ORDER BY total_knockdowns DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_sig_strikes_by_weight_class(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(text("""
        SELECT
            wc.name AS weight_class,
            ROUND(
                SUM(ms.sig_str_landed)::numeric / COUNT(DISTINCT fm.match_id), 2
            ) AS avg_sig_str_per_fight,
            COUNT(DISTINCT fm.match_id) AS total_fights
        FROM match_statistics ms
        JOIN fighter_match fm ON ms.fighter_match_id = fm.id
        JOIN match m ON fm.match_id = m.id
        JOIN weight_class wc ON m.weight_class_id = wc.id
        GROUP BY wc.id, wc.name
        ORDER BY avg_sig_str_per_fight DESC
    """))
    return [dict(row) for row in result.mappings().all()]


async def get_strike_exchange_ratio(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["min_fights"] = min_fights
    params["limit"] = limit
    result = await session.execute(text(f"""
        SELECT
            f.id AS fighter_id,
            f.name,
            COUNT(DISTINCT fm_mine.match_id) AS total_fights,
            ROUND(SUM(ms_mine.sig_str_landed)::numeric / COUNT(DISTINCT fm_mine.match_id), 2) AS sig_landed_per_fight,
            ROUND(SUM(ms_opp.sig_str_landed)::numeric / COUNT(DISTINCT fm_mine.match_id), 2) AS sig_absorbed_per_fight,
            ROUND(
                (SUM(ms_mine.sig_str_landed) - SUM(ms_opp.sig_str_landed))::numeric
                / COUNT(DISTINCT fm_mine.match_id), 2
            ) AS differential_per_fight
        FROM fighter_match fm_mine
        JOIN fighter_match fm_opp
            ON fm_mine.match_id = fm_opp.match_id AND fm_mine.id != fm_opp.id
        JOIN match_statistics ms_mine ON fm_mine.id = ms_mine.fighter_match_id
        JOIN match_statistics ms_opp ON fm_opp.id = ms_opp.fighter_match_id
        JOIN fighter f ON fm_mine.fighter_id = f.id
        JOIN match m ON fm_mine.match_id = m.id
        WHERE ms_mine.round = ms_opp.round
            {wc_clause}
        GROUP BY f.id, f.name
        HAVING COUNT(DISTINCT fm_mine.match_id) >= :min_fights
        ORDER BY differential_per_fight DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_stance_winrate(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    result = await session.execute(text(f"""
        SELECT
            f_w.stance AS winner_stance,
            f_l.stance AS loser_stance,
            COUNT(*) AS wins,
            ROUND(
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY
                    LEAST(f_w.stance, f_l.stance), GREATEST(f_w.stance, f_l.stance)
                ), 1
            ) AS win_rate
        FROM fighter_match fm_w
        JOIN fighter_match fm_l
            ON fm_w.match_id = fm_l.match_id AND fm_w.id != fm_l.id
        JOIN fighter f_w ON fm_w.fighter_id = f_w.id
        JOIN fighter f_l ON fm_l.fighter_id = f_l.id
        JOIN match m ON fm_w.match_id = m.id
        WHERE fm_w.result = 'win'
            AND f_w.stance IN ('Orthodox', 'Southpaw', 'Switch')
            AND f_l.stance IN ('Orthodox', 'Southpaw', 'Switch')
            {wc_clause}
        GROUP BY f_w.stance, f_l.stance
        ORDER BY f_w.stance, f_l.stance
    """), params)
    return [dict(row) for row in result.mappings().all()]


# ===========================
# Tab 4: Grappling — New charts
# ===========================

async def get_td_attempts_leaders(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
) -> Dict[str, Any]:
    """경기당 TD 시도 TOP + 평균값"""
    wc_clause, params = _wc_filter(weight_class_id)
    params["min_fights"] = min_fights
    params["limit"] = limit

    leaders_result = await session.execute(text(f"""
        SELECT
            f.id AS fighter_id,
            f.name,
            ROUND(SUM(ms.td_attempted)::numeric / COUNT(DISTINCT fm.match_id), 2) AS td_attempts_per_fight,
            SUM(ms.td_attempted) AS total_td_attempted,
            SUM(ms.td_landed) AS total_td_landed,
            COUNT(DISTINCT fm.match_id) AS total_fights
        FROM match_statistics ms
        JOIN fighter_match fm ON ms.fighter_match_id = fm.id
        JOIN fighter f ON fm.fighter_id = f.id
        JOIN match m ON fm.match_id = m.id
        WHERE 1=1
            {wc_clause}
        GROUP BY f.id, f.name
        HAVING COUNT(DISTINCT fm.match_id) >= :min_fights
        ORDER BY td_attempts_per_fight DESC
        LIMIT :limit
    """), params)
    leaders = [dict(row) for row in leaders_result.mappings().all()]

    avg_params = {k: v for k, v in params.items() if k != "limit"}
    avg_result = await session.execute(text(f"""
        SELECT ROUND(AVG(td_attempts_per_fight)::numeric, 2) AS avg_td_attempts
        FROM (
            SELECT SUM(ms.td_attempted)::numeric / COUNT(DISTINCT fm.match_id) AS td_attempts_per_fight
            FROM match_statistics ms
            JOIN fighter_match fm ON ms.fighter_match_id = fm.id
            JOIN match m ON fm.match_id = m.id
            WHERE 1=1
                {wc_clause}
            GROUP BY fm.fighter_id
            HAVING COUNT(DISTINCT fm.match_id) >= :min_fights
        ) sub
    """), avg_params)
    avg_row = avg_result.mappings().one()

    return {
        "leaders": leaders,
        "avg_td_attempts": float(avg_row["avg_td_attempts"]) if avg_row["avg_td_attempts"] else 0.0,
    }


async def get_td_sub_correlation(
    session: AsyncSession, weight_class_id: Optional[int] = None, limit: int = 3
) -> Dict[str, Any]:
    """TD vs SUB 사분면 그리드 — 전체 평균 기준으로 4개 사분면별 top N 반환"""
    wc_clause, params = _wc_filter(weight_class_id)
    params["limit"] = limit
    result = await session.execute(text(f"""
        WITH base AS (
            SELECT
                f.id AS fighter_id,
                f.name,
                SUM(ms.td_landed) AS total_td_landed,
                COUNT(CASE WHEN m.method LIKE 'SUB-%%' AND fm.result = 'win'
                      THEN 1 END) AS sub_finishes,
                COUNT(DISTINCT fm.match_id) AS total_fights,
                SUM(ms.td_landed)::float
                    / NULLIF(COUNT(DISTINCT fm.match_id), 0) AS td_per_fight,
                COUNT(CASE WHEN m.method LIKE 'SUB-%%' AND fm.result = 'win'
                      THEN 1 END)::float
                    / NULLIF(COUNT(DISTINCT fm.match_id), 0) AS sub_per_fight
            FROM match_statistics ms
            JOIN fighter_match fm ON ms.fighter_match_id = fm.id
            JOIN fighter f ON fm.fighter_id = f.id
            JOIN match m ON fm.match_id = m.id
            WHERE 1=1
                {wc_clause}
            GROUP BY f.id, f.name
            HAVING COUNT(DISTINCT fm.match_id) >= 5
        ),
        avgs AS (
            SELECT
                AVG(td_per_fight) AS avg_td_rate,
                AVG(sub_per_fight) AS avg_sub_rate
            FROM base
        ),
        classified AS (
            SELECT
                b.*,
                a.avg_td_rate,
                a.avg_sub_rate,
                CASE
                    WHEN b.td_per_fight >= a.avg_td_rate
                     AND b.sub_per_fight >= a.avg_sub_rate THEN 'high_td_high_sub'
                    WHEN b.td_per_fight >= a.avg_td_rate   THEN 'high_td_low_sub'
                    WHEN b.sub_per_fight >= a.avg_sub_rate  THEN 'low_td_high_sub'
                    ELSE 'low_td_low_sub'
                END AS quadrant
            FROM base b
            CROSS JOIN avgs a
        ),
        top_ranked AS (
            SELECT
                c.*,
                ROW_NUMBER() OVER (
                    PARTITION BY c.quadrant
                    ORDER BY (c.td_per_fight / NULLIF(c.avg_td_rate, 0))
                           + (c.sub_per_fight / NULLIF(c.avg_sub_rate, 0)) DESC
                ) AS rn
            FROM classified c
        )
        SELECT
            fighter_id, name, total_td_landed, sub_finishes, total_fights,
            ROUND(td_per_fight::numeric, 2) AS td_per_fight,
            ROUND(sub_per_fight::numeric, 2) AS sub_per_fight,
            quadrant,
            ROUND(avg_td_rate::numeric, 2) AS avg_td_rate,
            ROUND(avg_sub_rate::numeric, 2) AS avg_sub_rate,
            rn,
            COUNT(*) OVER (PARTITION BY quadrant) AS quadrant_count
        FROM top_ranked
        WHERE rn <= :limit
        ORDER BY quadrant, rn
    """), params)
    rows = [dict(r) for r in result.mappings().all()]

    avg_td = float(rows[0]["avg_td_rate"]) if rows else 0
    avg_sub = float(rows[0]["avg_sub_rate"]) if rows else 0

    quadrants: Dict[str, Any] = {}
    for row in rows:
        q = row["quadrant"]
        if q not in quadrants:
            quadrants[q] = {"fighters": [], "count": int(row["quadrant_count"])}
        quadrants[q]["fighters"].append({
            "fighter_id": row["fighter_id"],
            "name": row["name"],
            "total_td_landed": int(row["total_td_landed"]),
            "sub_finishes": int(row["sub_finishes"]),
            "total_fights": int(row["total_fights"]),
            "td_per_fight": float(row["td_per_fight"]),
            "sub_per_fight": float(row["sub_per_fight"]),
        })

    return {
        "quadrants": quadrants,
        "avg_td": round(float(avg_td), 1),
        "avg_sub": round(float(avg_sub), 1),
    }


async def get_td_defense_leaders(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    wc_clause, params = _wc_filter(weight_class_id)
    params["min_fights"] = min_fights
    params["limit"] = limit
    result = await session.execute(text(f"""
        SELECT
            f.id AS fighter_id,
            f.name,
            SUM(ms_opp.td_attempted) AS opp_td_attempted,
            SUM(ms_opp.td_landed) AS opp_td_landed,
            SUM(ms_opp.td_attempted) - SUM(ms_opp.td_landed) AS td_defended,
            ROUND(
                (SUM(ms_opp.td_attempted) - SUM(ms_opp.td_landed)) * 100.0
                / NULLIF(SUM(ms_opp.td_attempted), 0), 1
            ) AS td_defense_rate
        FROM fighter_match fm_mine
        JOIN fighter_match fm_opp
            ON fm_mine.match_id = fm_opp.match_id AND fm_mine.id != fm_opp.id
        JOIN match_statistics ms_opp ON fm_opp.id = ms_opp.fighter_match_id
        JOIN fighter f ON fm_mine.fighter_id = f.id
        JOIN match m ON fm_mine.match_id = m.id
        WHERE ms_opp.round > 0
            {wc_clause}
        GROUP BY f.id, f.name
        HAVING COUNT(DISTINCT fm_mine.match_id) >= :min_fights
            AND SUM(ms_opp.td_attempted) >= 5
        ORDER BY td_defense_rate DESC
        LIMIT :limit
    """), params)
    return [dict(row) for row in result.mappings().all()]


async def get_submission_efficiency_avg_ratio(
    session: AsyncSession, weight_class_id: Optional[int] = None, min_fights: int = 10
) -> float:
    wc_clause, params = _wc_filter(weight_class_id)
    params["min_fights"] = min_fights
    result = await session.execute(text(f"""
        WITH per_fight AS (
            SELECT
                fm.fighter_id,
                fm.match_id,
                SUM(ms.submission_attempts) AS fight_sub_attempts,
                MAX(CASE WHEN m.method LIKE 'SUB-%%' AND fm.result = 'win'
                         THEN 1 ELSE 0 END) AS is_sub_win
            FROM match_statistics ms
            JOIN fighter_match fm ON ms.fighter_match_id = fm.id
            JOIN match m ON fm.match_id = m.id
            WHERE 1=1 {wc_clause}
            GROUP BY fm.fighter_id, fm.match_id
        ),
        per_fighter AS (
            SELECT
                fighter_id,
                GREATEST(SUM(fight_sub_attempts), SUM(is_sub_win)) AS total_sub_attempts,
                SUM(is_sub_win) AS sub_finishes
            FROM per_fight
            GROUP BY fighter_id
            HAVING COUNT(*) >= :min_fights
        )
        SELECT
            ROUND(
                SUM(sub_finishes)::numeric / NULLIF(SUM(total_sub_attempts), 0), 3
            ) AS avg_efficiency_ratio
        FROM per_fighter
    """), params)
    row = result.mappings().one()
    return float(row["avg_efficiency_ratio"]) if row["avg_efficiency_ratio"] is not None else 0.0
