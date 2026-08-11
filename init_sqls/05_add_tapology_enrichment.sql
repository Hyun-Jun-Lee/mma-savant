-- Tapology fighter profile enrichment columns
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS tapology_url VARCHAR;
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS born VARCHAR;
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS fighting_out_of VARCHAR;
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS affiliation VARCHAR;
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS gym VARCHAR;
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS current_streak VARCHAR;
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS last_fight_name VARCHAR;
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS last_fight_date DATE;
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS last_fight_promotion VARCHAR;
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS tapology_last_scraped_at TIMESTAMP;

-- Promotion-level career records from Tapology
CREATE TABLE IF NOT EXISTS fighter_promotion_record (
    id SERIAL PRIMARY KEY,
    fighter_id INTEGER NOT NULL,
    promotion_name VARCHAR NOT NULL,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    no_contests INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fighter_promotion_record_fighter
        FOREIGN KEY (fighter_id) REFERENCES fighter(id) ON DELETE CASCADE
);

-- Method-level career result records from Tapology
CREATE TABLE IF NOT EXISTS fighter_method_record (
    id SERIAL PRIMARY KEY,
    fighter_id INTEGER NOT NULL,
    scope VARCHAR NOT NULL DEFAULT 'all_career',
    result VARCHAR NOT NULL,
    method_category VARCHAR NOT NULL,
    count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fighter_method_record_fighter
        FOREIGN KEY (fighter_id) REFERENCES fighter(id) ON DELETE CASCADE
);

-- Tapology bout-level metadata
ALTER TABLE event ADD COLUMN IF NOT EXISTS tapology_url VARCHAR;

ALTER TABLE match ADD COLUMN IF NOT EXISTS is_title_bout BOOLEAN DEFAULT FALSE;
ALTER TABLE match ADD COLUMN IF NOT EXISTS bout_status VARCHAR;
ALTER TABLE match ADD COLUMN IF NOT EXISTS cancellation_reason VARCHAR;
ALTER TABLE match ADD COLUMN IF NOT EXISTS tapology_bout_url VARCHAR;
ALTER TABLE match ADD COLUMN IF NOT EXISTS tapology_last_scraped_at TIMESTAMP;

-- Tapology fighter-side weigh-in metadata
ALTER TABLE fighter_match ADD COLUMN IF NOT EXISTS weigh_in_result VARCHAR;
ALTER TABLE fighter_match ADD COLUMN IF NOT EXISTS fight_night_weight VARCHAR;
ALTER TABLE fighter_match ADD COLUMN IF NOT EXISTS weight_gain VARCHAR;

-- Lookup and idempotent upsert indexes
CREATE INDEX IF NOT EXISTS idx_fighter_tapology_url ON fighter(tapology_url);
CREATE INDEX IF NOT EXISTS idx_event_tapology_url ON event(tapology_url);
CREATE INDEX IF NOT EXISTS idx_fighter_promotion_record_fighter_id ON fighter_promotion_record(fighter_id);
CREATE INDEX IF NOT EXISTS idx_fighter_promotion_record_name ON fighter_promotion_record(promotion_name);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fighter_promotion_record_key ON fighter_promotion_record(fighter_id, promotion_name);
CREATE INDEX IF NOT EXISTS idx_fighter_method_record_fighter_id ON fighter_method_record(fighter_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fighter_method_record_key ON fighter_method_record(fighter_id, scope, result, method_category);
CREATE INDEX IF NOT EXISTS idx_match_tapology_bout_url ON match(tapology_bout_url);
CREATE INDEX IF NOT EXISTS idx_match_bout_status ON match(bout_status);
