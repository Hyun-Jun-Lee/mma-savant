#!/bin/bash

# 로컬 CI 테스트 스크립트 (GitHub Actions와 동일한 검증)
# Usage:
#   ./scripts/ci_local.sh              # 전체 실행
#   ./scripts/ci_local.sh --frontend   # Frontend만
#   ./scripts/ci_local.sh --backend    # Backend만
#   ./scripts/ci_local.sh --help       # 도움말

# 스크립트 경로 설정 (source와 직접 실행 모두 지원)
if [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 경로가 유효하지 않으면 현재 디렉토리 기준으로 설정
if [ ! -d "$PROJECT_ROOT/scripts" ]; then
    if [ -d "./scripts" ]; then
        PROJECT_ROOT="$(pwd)"
        SCRIPT_DIR="$PROJECT_ROOT/scripts"
    else
        echo "Error: Cannot find project root. Run from project root directory."
    fi
fi

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 기본값
RUN_FRONTEND=false
RUN_BACKEND=false
CONTINUE_ON_FAILURE=false

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "로컬에서 GitHub Actions CI와 동일한 검증을 수행합니다."
    echo ""
    echo "Options:"
    echo "  --frontend, -f     Frontend CI만 실행 (lint, typecheck, build)"
    echo "  --backend, -b      Backend CI만 실행 (pytest)"
    echo "  --continue, -c     실패해도 계속 진행"
    echo "  --help, -h         도움말 표시"
    echo ""
    echo "Examples:"
    echo "  $0                 # 전체 CI 실행"
    echo "  $0 --frontend      # Frontend만"
    echo "  $0 --backend       # Backend만"
    echo "  $0 -f -b           # Frontend + Backend (전체와 동일)"
    echo "  $0 --continue      # 실패해도 계속 진행"
}

print_header() {
    echo -e "\n${BOLD}${BLUE}######################################${NC}"
    echo -e "${BOLD}${BLUE}#  $1${NC}"
    echo -e "${BOLD}${BLUE}######################################${NC}\n"
}

print_result() {
    local name=$1
    local status=$2
    local duration=$3

    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓ $name passed${NC} ${YELLOW}(${duration}s)${NC}"
    else
        echo -e "${RED}✗ $name failed${NC} ${YELLOW}(${duration}s)${NC}"
    fi
}

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend|-f)
            RUN_FRONTEND=true
            shift
            ;;
        --backend|-b)
            RUN_BACKEND=true
            shift
            ;;
        --continue|-c)
            CONTINUE_ON_FAILURE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# 옵션이 없으면 전체 실행
if [ "$RUN_FRONTEND" = false ] && [ "$RUN_BACKEND" = false ]; then
    RUN_FRONTEND=true
    RUN_BACKEND=true
fi

TOTAL_START=$(date +%s)
FRONTEND_STATUS=0
BACKEND_STATUS=0

echo -e "${BOLD}${BLUE}"
echo "  _     ___   ____    _    _       ____ ___ "
echo " | |   / _ \ / ___|  / \  | |     / ___|_ _|"
echo " | |  | | | | |     / _ \ | |    | |    | | "
echo " | |__| |_| | |___ / ___ \| |___ | |___ | | "
echo " |_____\___/ \____/_/   \_\_____|  \____|___|"
echo -e "${NC}"
echo -e "${YELLOW}GitHub Actions CI - Local Runner${NC}\n"

# Frontend CI
if [ "$RUN_FRONTEND" = true ]; then
    print_header "Frontend CI (Lint & Build)"

    FRONTEND_START=$(date +%s)

    if "$SCRIPT_DIR/ci_frontend.sh"; then
        FRONTEND_STATUS=0
    else
        FRONTEND_STATUS=1
    fi

    FRONTEND_END=$(date +%s)
    FRONTEND_DURATION=$((FRONTEND_END - FRONTEND_START))
fi

# Backend CI
if [ "$RUN_BACKEND" = true ]; then
    print_header "Backend CI (Test)"

    BACKEND_START=$(date +%s)

    if "$SCRIPT_DIR/ci_backend.sh"; then
        BACKEND_STATUS=0
    else
        BACKEND_STATUS=1
    fi

    BACKEND_END=$(date +%s)
    BACKEND_DURATION=$((BACKEND_END - BACKEND_START))
fi

TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - TOTAL_START))

# 최종 결과 출력
echo -e "\n${BOLD}${BLUE}======================================${NC}"
echo -e "${BOLD}${BLUE}         Final Results${NC}"
echo -e "${BOLD}${BLUE}======================================${NC}\n"

if [ "$RUN_FRONTEND" = true ]; then
    print_result "Frontend" $FRONTEND_STATUS $FRONTEND_DURATION
fi

if [ "$RUN_BACKEND" = true ]; then
    print_result "Backend" $BACKEND_STATUS $BACKEND_DURATION
fi

echo -e "\n${YELLOW}Total duration: ${TOTAL_DURATION}s${NC}"

# 최종 상태 반환
if [ $FRONTEND_STATUS -ne 0 ] || [ $BACKEND_STATUS -ne 0 ]; then
    echo -e "\n${RED}${BOLD}CI Failed${NC}"
else
    echo -e "\n${GREEN}${BOLD}CI Passed${NC}"
fi
