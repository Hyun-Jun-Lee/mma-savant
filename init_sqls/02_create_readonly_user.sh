#!/bin/bash
# ======================================================================
# MMA Savant 읽기 전용 사용자 생성 스크립트 (Docker 환경용)
#
# Docker 컨테이너 초기화 시 자동 실행됩니다.
# 환경 변수에서 사용자명과 비밀번호를 읽어와서 동적으로 SQL을 실행합니다.
# ======================================================================

set -e

# 환경 변수에서 읽기 전용 계정 정보 가져오기
READONLY_USER="${DB_READONLY_USER:-mma_readonly}"
READONLY_PASSWORD="${DB_READONLY_PASSWORD:-readonly_secure_password_2024}"

# PostgreSQL 접속 정보 설정
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-savant_db}"

echo "🔧 [INIT] Creating readonly user: $READONLY_USER"
echo "🔧 [INIT] Using PostgreSQL user: $POSTGRES_USER"
echo "🔧 [INIT] Database: $POSTGRES_DB"

# PostgreSQL에 SQL 실행
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

	-- 1. 기존 사용자가 있다면 삭제 (개발 환경용)
	DO \$\$
	BEGIN
	    IF EXISTS (SELECT 1 FROM pg_user WHERE usename = '$READONLY_USER') THEN
	        -- 기존 권한 회수
	        REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM $READONLY_USER;
	        REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM $READONLY_USER;
	        REVOKE USAGE ON SCHEMA public FROM $READONLY_USER;

	        -- 사용자 삭제
	        DROP USER $READONLY_USER;
	        RAISE NOTICE 'Existing user % has been dropped', '$READONLY_USER';
	    END IF;
	END
	\$\$;

	-- 2. 읽기 전용 사용자 생성
	CREATE USER $READONLY_USER WITH PASSWORD '$READONLY_PASSWORD';

	-- 사용자 설정
	ALTER USER $READONLY_USER SET statement_timeout = '30s';
	ALTER USER $READONLY_USER SET lock_timeout = '10s';
	ALTER USER $READONLY_USER SET idle_in_transaction_session_timeout = '60s';

	-- 3. 스키마 접근 권한 부여
	GRANT USAGE ON SCHEMA public TO $READONLY_USER;

	-- 4. MMA 도메인 테이블에 대한 SELECT 권한만 부여
	-- Fighter 관련 테이블
	GRANT SELECT ON fighter TO $READONLY_USER;
	GRANT SELECT ON fighter_match TO $READONLY_USER;

	-- Event & Match 관련 테이블
	GRANT SELECT ON event TO $READONLY_USER;
	GRANT SELECT ON match TO $READONLY_USER;

	-- 통계 및 상세 정보 테이블
	GRANT SELECT ON match_statistics TO $READONLY_USER;
	GRANT SELECT ON strike_detail TO $READONLY_USER;

	-- 랭킹 및 체급 테이블
	GRANT SELECT ON ranking TO $READONLY_USER;
	GRANT SELECT ON weight_class TO $READONLY_USER;

	-- 5. 시퀀스 사용 권한 (필요한 경우)
	GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO $READONLY_USER;

	-- 6. 생성 완료 메시지
	DO \$\$
	BEGIN
	    RAISE NOTICE '=== 읽기 전용 사용자 생성 완료 ===';
	    RAISE NOTICE 'Username: %', '$READONLY_USER';
	    RAISE NOTICE 'Database: %', '$POSTGRES_DB';
	    RAISE NOTICE 'Environment: Docker Container';
	END
	\$\$;

EOSQL

echo "✅ [INIT] Readonly user '$READONLY_USER' created successfully"

# 권한 확인
echo "🔍 [INIT] Checking granted privileges..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	SELECT
	    table_schema,
	    table_name,
	    privilege_type
	FROM
	    information_schema.table_privileges
	WHERE
	    grantee = '$READONLY_USER'
	    AND table_schema = 'public'
	ORDER BY
	    table_name;
EOSQL

echo "🎯 [INIT] Readonly user setup completed!"