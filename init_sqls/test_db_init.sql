-- Test Database 초기화 스크립트
-- Repository Layer 테스트를 위한 전용 테스트 DB 스키마

-- Test 데이터베이스 생성 (이미 존재하면 무시)
SELECT 'CREATE DATABASE test_savant_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test_savant_db')\gexec

-- Test 데이터베이스로 연결 후 실행할 스크립트
\c test_savant_db;

-- 기존 테이블이 있으면 모두 삭제 (테스트 격리를 위해)
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- fighter 테이블
CREATE TABLE IF NOT EXISTS fighter (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    nickname VARCHAR,
    height FLOAT,
    height_cm FLOAT,
    weight FLOAT,
    weight_kg FLOAT,
    reach FLOAT,
    reach_cm FLOAT,
    stance VARCHAR,
    birthdate VARCHAR,
    belt BOOLEAN DEFAULT FALSE,
    detail_url VARCHAR,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- weight_class 테이블
CREATE TABLE IF NOT EXISTS weight_class (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- event 테이블
CREATE TABLE IF NOT EXISTS event (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    location VARCHAR,
    event_date DATE,
    url VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- match 테이블
CREATE TABLE IF NOT EXISTS match (
    id SERIAL PRIMARY KEY,
    event_id INTEGER,
    weight_class_id INTEGER,
    method VARCHAR,
    result_round INTEGER,
    time VARCHAR,
    "order" INTEGER,
    is_main_event BOOLEAN,
    detail_url VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 제약조건
    CONSTRAINT fk_match_event 
        FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE,
    CONSTRAINT fk_match_weight_class 
        FOREIGN KEY (weight_class_id) REFERENCES weight_class(id) ON DELETE SET NULL
);

-- ranking 테이블
CREATE TABLE IF NOT EXISTS ranking (
    id SERIAL PRIMARY KEY,
    fighter_id INTEGER,
    ranking INTEGER,
    weight_class_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 제약조건
    CONSTRAINT fk_ranking_fighter 
        FOREIGN KEY (fighter_id) REFERENCES fighter(id) ON DELETE CASCADE,
    CONSTRAINT fk_ranking_weight_class 
        FOREIGN KEY (weight_class_id) REFERENCES weight_class(id) ON DELETE SET NULL
);

-- fighter_match 테이블
CREATE TABLE IF NOT EXISTS fighter_match (
    id SERIAL PRIMARY KEY,
    fighter_id INTEGER,
    match_id INTEGER,
    result VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 제약조건
    CONSTRAINT fk_fighter_match_fighter 
        FOREIGN KEY (fighter_id) REFERENCES fighter(id) ON DELETE CASCADE,
    CONSTRAINT fk_fighter_match_match 
        FOREIGN KEY (match_id) REFERENCES match(id) ON DELETE CASCADE
);

-- strike_detail 테이블
CREATE TABLE IF NOT EXISTS strike_detail (
    id SERIAL PRIMARY KEY,
    fighter_match_id INTEGER,
    round INTEGER DEFAULT 0,
    head_strikes_landed INTEGER DEFAULT 0,
    head_strikes_attempts INTEGER DEFAULT 0,
    body_strikes_landed INTEGER DEFAULT 0,
    body_strikes_attempts INTEGER DEFAULT 0,
    leg_strikes_landed INTEGER DEFAULT 0,
    leg_strikes_attempts INTEGER DEFAULT 0,
    takedowns_landed INTEGER DEFAULT 0,
    takedowns_attempts INTEGER DEFAULT 0,
    clinch_strikes_landed INTEGER DEFAULT 0,
    clinch_strikes_attempts INTEGER DEFAULT 0,
    ground_strikes_landed INTEGER DEFAULT 0,
    ground_strikes_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 제약조건
    CONSTRAINT fk_strike_detail_fighter_match 
        FOREIGN KEY (fighter_match_id) REFERENCES fighter_match(id) ON DELETE CASCADE
);

-- match_statistics 테이블
CREATE TABLE IF NOT EXISTS match_statistics (
    id SERIAL PRIMARY KEY,
    fighter_match_id INTEGER,
    round INTEGER DEFAULT 0,
    knockdowns INTEGER DEFAULT 0,
    control_time_seconds INTEGER DEFAULT 0,
    submission_attempts INTEGER DEFAULT 0,
    sig_str_landed INTEGER DEFAULT 0,
    sig_str_attempted INTEGER DEFAULT 0,
    total_str_landed INTEGER DEFAULT 0,
    total_str_attempted INTEGER DEFAULT 0,
    td_landed INTEGER DEFAULT 0,
    td_attempted INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 제약조건
    CONSTRAINT fk_match_statistics_fighter_match 
        FOREIGN KEY (fighter_match_id) REFERENCES fighter_match(id) ON DELETE CASCADE
);

-- 성능을 위한 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_fighter_name ON fighter(name);
CREATE INDEX IF NOT EXISTS idx_match_event_id ON match(event_id);
CREATE INDEX IF NOT EXISTS idx_match_weight_class_id ON match(weight_class_id);
CREATE INDEX IF NOT EXISTS idx_fighter_match_fighter_id ON fighter_match(fighter_id);
CREATE INDEX IF NOT EXISTS idx_fighter_match_match_id ON fighter_match(match_id);
CREATE INDEX IF NOT EXISTS idx_ranking_fighter_id ON ranking(fighter_id);
CREATE INDEX IF NOT EXISTS idx_strike_detail_fighter_match_id ON strike_detail(fighter_match_id);
CREATE INDEX IF NOT EXISTS idx_match_statistics_fighter_match_id ON match_statistics(fighter_match_id);

-- 테스트용 체급 데이터 삽입
INSERT INTO weight_class (id, name, created_at, updated_at) VALUES
(1, 'flyweight', NOW(), NOW()),
(2, 'bantamweight', NOW(), NOW()),
(3, 'featherweight', NOW(), NOW()),
(4, 'lightweight', NOW(), NOW()),
(5, 'welterweight', NOW(), NOW()),
(6, 'middleweight', NOW(), NOW()),
(7, 'light heavyweight', NOW(), NOW()),
(8, 'heavyweight', NOW(), NOW()),
(9, 'women''s strawweight', NOW(), NOW()),
(10, 'women''s flyweight', NOW(), NOW()),
(11, 'women''s bantamweight', NOW(), NOW()),
(12, 'women''s featherweight', NOW(), NOW()),
(13, 'catch weight', NOW(), NOW()),
(14, 'open weight', NOW(), NOW()),
(15, 'men''s pound-for-pound', NOW(), NOW()),
(16, 'women''s pound-for-pound', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- ID 시퀀스 재설정
SELECT setval('weight_class_id_seq', 16, true);

-- 테스트 알림
SELECT 'Test database initialized successfully!' as status;