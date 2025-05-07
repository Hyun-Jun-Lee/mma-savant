-- UFC 체급 정보를 초기화하는 SQL 스크립트
-- alembic 마이그레이션 후 실행하세요

-- 기존 데이터가 있는지 확인
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM weight_class LIMIT 1) THEN
        RAISE NOTICE '체급 테이블이 이미 초기화되어 있습니다.';
        RETURN;
    END IF;

    -- 체급 정보 삽입
    INSERT INTO weight_class (id, name, created_at, updated_at) VALUES
    (1, 'Flyweight', NOW(), NOW()),
    (2, 'Bantamweight', NOW(), NOW()),
    (3, 'Featherweight', NOW(), NOW()),
    (4, 'Lightweight', NOW(), NOW()),
    (5, 'Welterweight', NOW(), NOW()),
    (6, 'Middleweight', NOW(), NOW()),
    (7, 'Light Heavyweight', NOW(), NOW()),
    (8, 'Heavyweight', NOW(), NOW()),
    (9, 'Women''s Strawweight', NOW(), NOW()),
    (10, 'Women''s Flyweight', NOW(), NOW()),
    (11, 'Women''s Bantamweight', NOW(), NOW()),
    (12, 'Women''s Featherweight', NOW(), NOW()),
    (13, 'Catch Weight', NOW(), NOW());

    -- ID 시퀀스 업데이트 (다음 ID가 14부터 시작하도록)
    PERFORM setval('weight_class_id_seq', 13, true);

    RAISE NOTICE '체급 테이블 초기화 완료: 13개 항목 생성됨';
END $$;
