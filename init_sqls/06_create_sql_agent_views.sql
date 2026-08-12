-- Canonical SQL-agent views for common MMA query paths.
-- These views are intentionally read-only fact/summary surfaces for the LLM SQL tool.

CREATE OR REPLACE VIEW v_fighter_fight_results AS
SELECT
    fm.fighter_id,
    f.name AS fighter_name,
    f.nickname,
    fm.id AS fighter_match_id,
    fm.match_id,
    e.id AS event_id,
    e.name AS event_name,
    e.event_date,
    e.location AS event_location,
    wc.id AS weight_class_id,
    wc.name AS weight_class_name,
    fm.result,
    m.method,
    m.result_round,
    m.time,
    COALESCE(m.is_main_event, false) AS is_main_event,
    COALESCE(m.is_title_bout, false) AS is_title_bout,
    m.bout_status,
    m.cancellation_reason,
    m."order" AS fight_order
FROM fighter_match fm
JOIN fighter f ON f.id = fm.fighter_id
JOIN match m ON m.id = fm.match_id
JOIN event e ON e.id = m.event_id
LEFT JOIN weight_class wc ON wc.id = m.weight_class_id;

CREATE OR REPLACE VIEW v_completed_fighter_fights AS
SELECT
    v.*,
    (v.result = 'win') AS is_win,
    (v.result = 'loss') AS is_loss,
    (v.result = 'draw') AS is_draw,
    (v.result = 'nc') AS is_no_contest,
    COALESCE((
        v.method ILIKE 'KO/TKO%'
        OR v.method ILIKE 'KO-%'
        OR v.method ILIKE 'TKO-%'
    ), false) AS is_ko_tko,
    COALESCE((v.method ILIKE 'SUB-%'), false) AS is_submission,
    COALESCE((
        v.method IN ('U-DEC', 'S-DEC', 'M-DEC')
        OR v.method ILIKE '%DEC%'
    ), false) AS is_decision,
    COALESCE((
        v.method ILIKE 'KO/TKO%'
        OR v.method ILIKE 'KO-%'
        OR v.method ILIKE 'TKO-%'
        OR v.method ILIKE 'SUB-%'
    ), false) AS is_finish
FROM v_fighter_fight_results v
WHERE v.event_date <= CURRENT_DATE
  AND v.result IS NOT NULL
  AND COALESCE(v.bout_status, 'completed') NOT IN ('scheduled', 'cancelled', 'postponed');

CREATE OR REPLACE VIEW v_fighter_opponents AS
SELECT
    c.fighter_id,
    c.fighter_name,
    opp_f.id AS opponent_id,
    opp_f.name AS opponent_name,
    c.fighter_match_id,
    c.match_id,
    c.event_id,
    c.event_name,
    c.event_date,
    c.weight_class_id,
    c.weight_class_name,
    c.result,
    c.method,
    c.result_round,
    c.time,
    c.is_title_bout,
    c.fight_order
FROM v_completed_fighter_fights c
JOIN fighter_match opp_fm
  ON opp_fm.match_id = c.match_id
 AND opp_fm.fighter_id <> c.fighter_id
JOIN fighter opp_f ON opp_f.id = opp_fm.fighter_id;

CREATE OR REPLACE VIEW v_current_rankings AS
SELECT
    f.id AS fighter_id,
    f.name AS fighter_name,
    wc.id AS weight_class_id,
    wc.name AS weight_class_name,
    r.ranking,
    (r.ranking = 0) AS is_champion,
    CASE WHEN r.ranking = 0 THEN 'champion' ELSE r.ranking::text END AS display_rank
FROM ranking r
JOIN fighter f ON f.id = r.fighter_id
JOIN weight_class wc ON wc.id = r.weight_class_id;

CREATE OR REPLACE VIEW v_fighter_record_summary AS
SELECT
    fighter_id,
    fighter_name,
    COUNT(*) AS total_completed_fights,
    COUNT(*) FILTER (WHERE result = 'win') AS wins,
    COUNT(*) FILTER (WHERE result = 'loss') AS losses,
    COUNT(*) FILTER (WHERE result = 'draw') AS draws,
    COUNT(*) FILTER (WHERE result = 'nc') AS no_contests,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE result = 'win')
        / NULLIF(COUNT(*) FILTER (WHERE result IN ('win', 'loss', 'draw', 'nc')), 0),
        2
    ) AS win_rate,
    MAX(event_date) AS last_fight_date,
    MIN(event_date) AS first_fight_date
FROM v_completed_fighter_fights
GROUP BY fighter_id, fighter_name;

CREATE OR REPLACE VIEW v_fighter_method_summary AS
SELECT
    fighter_id,
    fighter_name,
    COUNT(*) FILTER (WHERE result = 'win' AND is_ko_tko) AS ko_tko_wins,
    COUNT(*) FILTER (WHERE result = 'win' AND is_submission) AS submission_wins,
    COUNT(*) FILTER (WHERE result = 'win' AND is_decision) AS decision_wins,
    COUNT(*) FILTER (WHERE result = 'win' AND method ILIKE 'DQ%') AS dq_wins,
    COUNT(*) FILTER (
        WHERE result = 'win'
          AND NOT is_ko_tko
          AND NOT is_submission
          AND NOT is_decision
          AND NOT (method ILIKE 'DQ%')
    ) AS other_wins,
    COUNT(*) FILTER (WHERE result = 'loss' AND is_ko_tko) AS ko_tko_losses,
    COUNT(*) FILTER (WHERE result = 'loss' AND is_submission) AS submission_losses,
    COUNT(*) FILTER (WHERE result = 'loss' AND is_decision) AS decision_losses,
    COUNT(*) FILTER (WHERE result = 'win' AND is_finish) AS finish_wins,
    COUNT(*) FILTER (WHERE result = 'loss' AND is_finish) AS finish_losses,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE result = 'win' AND is_finish)
        / NULLIF(COUNT(*), 0),
        2
    ) AS finish_rate
FROM v_completed_fighter_fights
GROUP BY fighter_id, fighter_name;
