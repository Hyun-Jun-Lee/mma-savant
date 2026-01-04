#!/bin/bash

echo "환경변수 검증 중..."

# .env.sample 파일 존재 확인
if [ ! -f .env.sample ]; then
    echo "❌ .env.sample 파일이 없습니다!"
    exit 1
fi

# .env 파일 존재 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다!"
    echo "🔄 .env.sample에서 .env 파일을 생성합니다..."
    cp .env.sample .env
    echo "✅ .env 파일이 생성되었습니다"
    echo "⚠️  .env 파일을 편집하여 실제 값을 입력하세요"
    echo ""
fi

echo "✅ .env 파일 존재"

# .env.sample에서 환경변수 목록 추출
# 주석(#)이 아니고, 등호(=)를 포함한 라인에서 변수명만 추출
REQUIRED_ENV_VARS=$(grep -E '^[A-Z_]+=' .env.sample | cut -d'=' -f1)

echo ".env.sample에서 발견된 환경변수:"
echo "$REQUIRED_ENV_VARS"
echo ""

# 환경변수 로드
set -a
source .env
set +a

# 필수 환경변수 확인
ENV_CHECK_FAILED=0

check_var() {
    var_name=$1
    var_value=$(eval echo \$$var_name)
    
    if [ -z "$var_value" ]; then
        echo "❌ $var_name 환경변수가 설정되지 않음"
        ENV_CHECK_FAILED=1
    else
        case "$var_name" in
            *PASSWORD*|*SECRET*|*KEY*)
                echo "✅ $var_name 설정됨 (****)"
                ;;
            *)
                echo "✅ $var_name 설정됨: $var_value"
                ;;
        esac
    fi
}

# 각 변수 확인
for var in $REQUIRED_ENV_VARS; do
    check_var "$var"
done

# STORAGE_PATH (LOCAL_STORAGE_PATH 대신) 디렉토리 확인 및 생성
if [ -n "$STORAGE_PATH" ]; then
    if [ ! -d "$STORAGE_PATH" ]; then
        echo "⚠️  STORAGE_PATH 디렉토리가 없습니다. 생성합니다..."
        mkdir -p "$STORAGE_PATH"
        if [ $? -eq 0 ]; then
            echo "✅ STORAGE_PATH 디렉토리 생성됨: $STORAGE_PATH"
        else
            echo "❌ STORAGE_PATH 디렉토리 생성 실패"
            ENV_CHECK_FAILED=1
        fi
    else
        echo "✅ STORAGE_PATH 디렉토리 존재: $STORAGE_PATH"
    fi
fi

if [ $ENV_CHECK_FAILED -eq 1 ]; then
    echo ""
    echo "❌ 환경변수 검증 실패!"
    echo "   누락된 환경변수를 .env 파일에 추가하세요"
    exit 1
fi

echo ""
echo "✅ 환경변수 검증 완료!"