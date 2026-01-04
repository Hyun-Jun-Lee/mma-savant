#!/bin/bash

# Backend CI 테스트 스크립트
# Usage: ./scripts/ci_backend.sh

# 스크립트 경로 설정 (source와 직접 실행 모두 지원)
if [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"

# 경로가 유효하지 않으면 현재 디렉토리 기준으로 설정
if [ ! -d "$SRC_DIR" ]; then
    # 현재 디렉토리가 프로젝트 루트인지 확인
    if [ -d "./src" ]; then
        PROJECT_ROOT="$(pwd)"
        SRC_DIR="$PROJECT_ROOT/src"
    # 현재 디렉토리가 src인지 확인
    elif [ -f "./pyproject.toml" ]; then
        SRC_DIR="$(pwd)"
        PROJECT_ROOT="$(dirname "$SRC_DIR")"
    else
        echo "Error: Cannot find project root. Run from project root or src directory."
    fi
fi

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 결과 추적
PASSED=0
FAILED=0
FAILED_STEPS=()

print_step() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED++))
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED++))
    FAILED_STEPS+=("$1")
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_summary() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}Backend CI Summary${NC}"
    echo -e "${BLUE}===================================${NC}"
    echo -e "${GREEN}Passed: $PASSED${NC}"
    echo -e "${RED}Failed: $FAILED${NC}"

    if [ $FAILED -gt 0 ]; then
        echo -e "\n${RED}Failed steps:${NC}"
        for step in "${FAILED_STEPS[@]}"; do
            echo -e "  ${RED}- $step${NC}"
        done
    fi
}

check_postgres() {
    print_step "Checking PostgreSQL connection"

    if command -v pg_isready &> /dev/null; then
        if pg_isready -h localhost -p 5432 &> /dev/null; then
            print_success "PostgreSQL is running"
            return 0
        fi
    fi

    # Docker로 확인
    if docker ps --format '{{.Names}}' | grep -q "savant_db"; then
        print_success "PostgreSQL is running (Docker)"
        return 0
    fi

    print_warning "PostgreSQL not detected. Starting with docker-compose..."
    cd "$PROJECT_ROOT"
    docker-compose up -d savant_db

    # DB 준비 대기
    echo "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec savant_db pg_isready -U postgres &> /dev/null; then
            print_success "PostgreSQL is ready"
            return 0
        fi
        sleep 1
    done

    print_failure "PostgreSQL connection"
    return 1
}

cd "$SRC_DIR"

START_TIME=$(date +%s)

# 1. Check PostgreSQL
if ! check_postgres; then
    echo -e "${RED}Cannot proceed without PostgreSQL${NC}"
    print_summary
fi

# 2. Install dependencies
print_step "Installing dependencies (uv sync)"
if uv sync; then
    print_success "Dependencies installed"
else
    print_failure "Dependencies installation"
fi

# 3. Run tests
print_step "Running pytest"
export TESTING=true
if uv run pytest tests -v --tb=short; then
    print_success "All tests passed"
else
    print_failure "Tests"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "\n${YELLOW}Duration: ${DURATION}s${NC}"

print_summary
