#!/bin/bash

# 테스트 유저 생성 스크립트
# 사용법: ./scripts/create_test_user.sh [daily_limit]
# 예시: ./scripts/create_test_user.sh 3  (일일 제한 3회로 설정)

# 기본값 설정
DAILY_LIMIT=${1:-3}
TEST_EMAIL="test_user_$(date +%s)@test.com"
TEST_NAME="Test User"

# 환경 변수 로드
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
elif [ -f "../.env" ]; then
    export $(grep -v '^#' ../.env | xargs)
fi

# DB 연결 정보
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-savant_db}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-guswns95}

echo "=========================================="
echo "🧪 테스트 유저 생성 스크립트"
echo "=========================================="
echo ""
echo "📧 이메일: $TEST_EMAIL"
echo "👤 이름: $TEST_NAME"
echo "📊 일일 제한: $DAILY_LIMIT 회"
echo ""

# PostgreSQL에 테스트 유저 생성
echo "🔄 데이터베이스에 유저 생성 중..."

PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << EOF
INSERT INTO "user" (email, name, provider, is_active, is_admin, daily_request_limit, total_requests, daily_requests, created_at, updated_at)
VALUES ('$TEST_EMAIL', '$TEST_NAME', 'test', true, false, $DAILY_LIMIT, 0, 0, NOW(), NOW())
RETURNING id, email, name, daily_request_limit;
EOF

if [ $? -ne 0 ]; then
    echo "❌ 유저 생성 실패"
    exit 1
fi

echo ""
echo "✅ 유저가 성공적으로 생성되었습니다!"
echo ""

# JWT 토큰 생성 (Python 사용)
echo "🔑 JWT 토큰 생성 중..."

JWT_SECRET=${NEXTAUTH_SECRET:-"G=T5iE\$lUwMmr5VZth=xYI/~tKCLF.y>*IWXSD9z8nH2kR?G*.^nicEYsY3BhyAD"}

TOKEN=$(python3 << PYTHON
import jwt
import datetime
import os

secret = os.environ.get('NEXTAUTH_SECRET', '$JWT_SECRET')
now = datetime.datetime.now(datetime.timezone.utc)

payload = {
    "sub": "$TEST_EMAIL",
    "email": "$TEST_EMAIL",
    "name": "$TEST_NAME",
    "picture": None,
    "iat": int(now.timestamp()),
    "exp": int((now + datetime.timedelta(hours=24)).timestamp()),
}

token = jwt.encode(payload, secret, algorithm="HS256")
print(token)
PYTHON
)

if [ $? -ne 0 ]; then
    echo "❌ JWT 토큰 생성 실패"
    exit 1
fi

echo ""
echo "=========================================="
echo "🎉 테스트 준비 완료!"
echo "=========================================="
echo ""
echo "📧 이메일: $TEST_EMAIL"
echo "📊 일일 제한: $DAILY_LIMIT 회"
echo ""
echo "🔑 JWT 토큰 (24시간 유효):"
echo ""
echo "$TOKEN"
echo ""
echo "=========================================="
echo ""
echo "📝 WebSocket 테스트 방법:"
echo ""
echo "1. 브라우저 개발자 도구 콘솔에서:"
echo ""
echo "   const ws = new WebSocket('ws://localhost:8000/ws/chat?token=$TOKEN');"
echo "   ws.onmessage = (e) => console.log(JSON.parse(e.data));"
echo "   ws.onopen = () => ws.send(JSON.stringify({type: 'message', content: '테스트 메시지'}));"
echo ""
echo "2. 또는 wscat 사용:"
echo ""
echo "   wscat -c 'ws://localhost:8000/ws/chat?token=$TOKEN'"
echo ""
echo "=========================================="
