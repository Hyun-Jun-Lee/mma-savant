-- UFC 체급 정보를 초기화하는 SQL 스크립트

-- 체급 테이블이 이미 초기화되어 있는지 확인
-- 데이터가 있으면 스크립트를 중단합니다
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM weight_class LIMIT 1) THEN
        RAISE NOTICE '체급 테이블이 이미 초기화되어 있습니다.';
    ELSE
        -- 체급 정보 삽입
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
        (14, 'open weight', NOW(), NOW());
        (15, 'men''s pound-for-pound', NOW(), NOW());
        (16, 'women''s pound-for-pound', NOW(), NOW());
        
        -- ID 시퀀스 재설정 (PostgreSQL 전용)
        PERFORM setval('weight_class_id_seq', 16, true);
        
        RAISE NOTICE '체급 테이블 초기화 완료: 14개 항목 생성됨';
    END IF;
END
$$;