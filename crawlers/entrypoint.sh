#!/bin/bash
set -e

# 데이터베이스 연결 대기
echo "데이터베이스 연결 대기 중..."
sleep 5  # 데이터베이스가 완전히 시작될 때까지 대기

# Alembic 마이그레이션 실행
echo "Alembic 마이그레이션 실행 중..."
cd /app/crawlers
alembic upgrade head
alembic revision --autogenerate -m "init"
alembic upgrade head

# 체급 클래스 초기화
echo "체급 클래스 초기화 중..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U postgres -d $DB_NAME -f ./init_weight_classes.sql

# 메인 애플리케이션 실행
echo "메인 애플리케이션 실행 중..."
python main.py

# 컨테이너가 계속 실행되도록 유지
exec "$@"
