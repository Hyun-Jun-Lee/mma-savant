-- Add UFCStats event-row bonus metadata columns to an existing operating DB.
-- Safe to run repeatedly. Run this before refreshing 06_create_sql_agent_views.sql.

ALTER TABLE match
    ADD COLUMN IF NOT EXISTS has_fight_of_the_night_bonus BOOLEAN DEFAULT FALSE;

ALTER TABLE fighter_match
    ADD COLUMN IF NOT EXISTS has_performance_of_the_night_bonus BOOLEAN DEFAULT FALSE;

UPDATE match
SET has_fight_of_the_night_bonus = FALSE
WHERE has_fight_of_the_night_bonus IS NULL;

UPDATE fighter_match
SET has_performance_of_the_night_bonus = FALSE
WHERE has_performance_of_the_night_bonus IS NULL;

ALTER TABLE match
    ALTER COLUMN has_fight_of_the_night_bonus SET DEFAULT FALSE,
    ALTER COLUMN has_fight_of_the_night_bonus SET NOT NULL;

ALTER TABLE fighter_match
    ALTER COLUMN has_performance_of_the_night_bonus SET DEFAULT FALSE,
    ALTER COLUMN has_performance_of_the_night_bonus SET NOT NULL;
