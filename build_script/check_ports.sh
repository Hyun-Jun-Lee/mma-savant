#!/bin/bash

echo "포트 사용 현황 확인 중..."

# .env 파일 존재 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다!"
    exit 1
fi

echo "✅ .env 파일 존재"

# 환경변수 로드
set -a
source .env
set +a

# .env에서 PORT 관련 환경변수 추출
PORT_VARS=$(grep -E '^[A-Z_]*PORT=' .env | cut -d'=' -f1)

if [ -z "$PORT_VARS" ]; then
    echo "⚠️  .env에서 PORT 관련 환경변수를 찾을 수 없습니다"
    exit 0
fi

echo "발견된 PORT 환경변수:"
for var in $PORT_VARS; do
    echo "  - $var"
done
echo ""

# 포트 사용 여부 확인 함수
check_port() {
    port=$1
    var_name=$2
    
    if [ -z "$port" ] || [ "$port" = "" ]; then
        echo "⚠️  $var_name: 포트가 설정되지 않음"
        return
    fi
    
    # 포트 번호 유효성 검사
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        echo "❌ $var_name: 잘못된 포트 번호 ($port)"
        return
    fi
    
    # 포트 사용 여부 확인
    if command -v lsof >/dev/null 2>&1; then
        # macOS/Linux with lsof
        if lsof -i :$port >/dev/null 2>&1; then
            process_info=$(lsof -i :$port | tail -n +2 | head -1 | awk '{print $1, $2}')
            echo "❌ $var_name ($port): 사용 중 - $process_info"
        else
            echo "✅ $var_name ($port): 사용 가능"
        fi
    elif command -v netstat >/dev/null 2>&1; then
        # Linux with netstat
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo "❌ $var_name ($port): 사용 중"
        else
            echo "✅ $var_name ($port): 사용 가능"
        fi
    elif command -v ss >/dev/null 2>&1; then
        # Modern Linux with ss
        if ss -tuln 2>/dev/null | grep -q ":$port "; then
            echo "❌ $var_name ($port): 사용 중"
        else
            echo "✅ $var_name ($port): 사용 가능"
        fi
    else
        echo "⚠️  $var_name ($port): 포트 확인 도구를 찾을 수 없음"
    fi
}

echo "포트 사용 현황 확인:"
echo "----------------------------------------"

# 각 PORT 환경변수 확인
for var in $PORT_VARS; do
    port_value=$(eval echo \$$var)
    check_port "$port_value" "$var"
done

echo "----------------------------------------"

# 요약 정보
echo ""
echo "포트 확인 완료"
echo "사용 중인 포트가 있다면 다음 명령어로 프로세스를 확인하세요:"
echo "  lsof -i :<포트번호>"
echo "  kill -9 <PID>  # 프로세스 종료"