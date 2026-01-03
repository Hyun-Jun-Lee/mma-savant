#!/bin/bash

# Frontend CI 테스트 스크립트
# Usage: ./scripts/ci_frontend.sh

# 스크립트 경로 설정 (source와 직접 실행 모두 지원)
if [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 경로가 유효하지 않으면 현재 디렉토리 기준으로 설정
if [ ! -d "$FRONTEND_DIR" ]; then
    if [ -d "./frontend" ]; then
        PROJECT_ROOT="$(pwd)"
        FRONTEND_DIR="$PROJECT_ROOT/frontend"
    elif [ -f "./package.json" ]; then
        FRONTEND_DIR="$(pwd)"
        PROJECT_ROOT="$(dirname "$FRONTEND_DIR")"
    else
        echo "Error: Cannot find project root. Run from project root or frontend directory."
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

print_summary() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}Frontend CI Summary${NC}"
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

cd "$FRONTEND_DIR"

START_TIME=$(date +%s)

# 1. Install dependencies
print_step "Installing dependencies (npm ci)"
if npm ci; then
    print_success "Dependencies installed"
else
    print_failure "Dependencies installation"
fi

# 2. ESLint
print_step "Running ESLint"
if npm run lint; then
    print_success "ESLint passed"
else
    print_failure "ESLint"
fi

# 3. TypeScript check
print_step "Running TypeScript check"
if npx tsc --noEmit; then
    print_success "TypeScript check passed"
else
    print_failure "TypeScript check"
fi

# 4. Build
print_step "Building frontend"
if npm run build; then
    print_success "Build completed"
else
    print_failure "Build"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "\n${YELLOW}Duration: ${DURATION}s${NC}"

print_summary
