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
    nationality VARCHAR,
    tapology_url VARCHAR,
    born VARCHAR,
    fighting_out_of VARCHAR,
    affiliation VARCHAR,
    gym VARCHAR,
    current_streak VARCHAR,
    last_fight_name VARCHAR,
    last_fight_date DATE,
    last_fight_promotion VARCHAR,
    tapology_last_scraped_at TIMESTAMP,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- fighter_promotion_record 테이블
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

    -- 외래키 제약조건
    CONSTRAINT fk_fighter_promotion_record_fighter
        FOREIGN KEY (fighter_id) REFERENCES fighter(id) ON DELETE CASCADE
);

-- fighter_method_record 테이블
CREATE TABLE IF NOT EXISTS fighter_method_record (
    id SERIAL PRIMARY KEY,
    fighter_id INTEGER NOT NULL,
    scope VARCHAR NOT NULL DEFAULT 'all_career',
    result VARCHAR NOT NULL,
    method_category VARCHAR NOT NULL,
    count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 외래키 제약조건
    CONSTRAINT fk_fighter_method_record_fighter
        FOREIGN KEY (fighter_id) REFERENCES fighter(id) ON DELETE CASCADE
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
    latitude FLOAT,
    longitude FLOAT,
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
    is_title_bout BOOLEAN DEFAULT FALSE,
    bout_status VARCHAR,
    cancellation_reason VARCHAR,
    tapology_bout_url VARCHAR,
    tapology_last_scraped_at TIMESTAMP,
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
    weigh_in_result VARCHAR,
    fight_night_weight VARCHAR,
    weight_gain VARCHAR,
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

-- user 테이블 (사용자 관리)
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE,
    password_hash VARCHAR,
    email VARCHAR UNIQUE,
    name VARCHAR,
    picture TEXT,
    provider_id VARCHAR,
    provider VARCHAR,
    total_requests INTEGER DEFAULT 0 NOT NULL,
    daily_requests INTEGER DEFAULT 0 NOT NULL,
    daily_request_limit INTEGER DEFAULT 100 NOT NULL,
    last_request_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- conversation 테이블 (채팅 세션 관리)
CREATE TABLE IF NOT EXISTS conversation (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 외래키 제약조건
    CONSTRAINT fk_conversation_user
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

-- message 테이블 (개별 메시지 관리)
CREATE TABLE IF NOT EXISTS message (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR NOT NULL UNIQUE,
    conversation_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    role VARCHAR NOT NULL CHECK (role IN ('user', 'assistant')),
    tool_results JSONB,
    visualization JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 외래키 제약조건
    CONSTRAINT fk_message_conversation
        FOREIGN KEY (conversation_id) REFERENCES conversation(id) ON DELETE CASCADE
);

-- 성능을 위한 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_fighter_name ON fighter(name);
CREATE INDEX IF NOT EXISTS idx_fighter_tapology_url ON fighter(tapology_url);
CREATE INDEX IF NOT EXISTS idx_fighter_promotion_record_fighter_id ON fighter_promotion_record(fighter_id);
CREATE INDEX IF NOT EXISTS idx_fighter_promotion_record_name ON fighter_promotion_record(promotion_name);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fighter_promotion_record_key ON fighter_promotion_record(fighter_id, promotion_name);
CREATE INDEX IF NOT EXISTS idx_fighter_method_record_fighter_id ON fighter_method_record(fighter_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fighter_method_record_key ON fighter_method_record(fighter_id, scope, result, method_category);
CREATE INDEX IF NOT EXISTS idx_match_event_id ON match(event_id);
CREATE INDEX IF NOT EXISTS idx_match_weight_class_id ON match(weight_class_id);
CREATE INDEX IF NOT EXISTS idx_match_tapology_bout_url ON match(tapology_bout_url);
CREATE INDEX IF NOT EXISTS idx_match_bout_status ON match(bout_status);
CREATE INDEX IF NOT EXISTS idx_fighter_match_fighter_id ON fighter_match(fighter_id);
CREATE INDEX IF NOT EXISTS idx_fighter_match_match_id ON fighter_match(match_id);
CREATE INDEX IF NOT EXISTS idx_ranking_fighter_id ON ranking(fighter_id);
CREATE INDEX IF NOT EXISTS idx_strike_detail_fighter_match_id ON strike_detail(fighter_match_id);
CREATE INDEX IF NOT EXISTS idx_match_statistics_fighter_match_id ON match_statistics(fighter_match_id);

-- 새로 추가된 테이블의 인덱스
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_provider_id ON "user"(provider_id);
CREATE INDEX IF NOT EXISTS idx_conversation_user_id ON conversation(user_id);

-- message 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_message_conversation_id ON message(conversation_id);
CREATE INDEX IF NOT EXISTS idx_message_message_id ON message(message_id);
CREATE INDEX IF NOT EXISTS idx_message_created_at ON message(created_at);
CREATE INDEX IF NOT EXISTS idx_message_role ON message(role);

-- 대화 압축 영속화 (Persistent Conversation Compression)
ALTER TABLE conversation ADD COLUMN IF NOT EXISTS compressed_context TEXT;
ALTER TABLE conversation ADD COLUMN IF NOT EXISTS compressed_sql_context JSONB;
ALTER TABLE conversation ADD COLUMN IF NOT EXISTS compressed_until_message_id VARCHAR;
