#!/bin/bash
# =============================================================================
# 운영 PostgreSQL 컨테이너 DB를 로컬 PostgreSQL 컨테이너로 동기화합니다.
#
# Usage:
#   ./scripts/sync-prod-db-to-local.sh [user@prod-server]
#
# .env 또는 shell environment에서 읽는 값:
#   PROD_SSH_HOST=user@prod-server
#   PROD_SSH_KEY=~/.ssh/mma_deploy
#   PROD_PROJECT_DIR=~/mma-savant
#   PROD_DB_CONTAINER=savant_db
#   LOCAL_DB_CONTAINER=savant_db
#   DB_USER=<.env DB_USER>
#   DB_NAME=<.env DB_NAME>
#   LOCAL_DUMP_PATH=/tmp/mma-savant-prod.dump
#   LOCAL_DEPENDENT_CONTAINERS=savant_api
#   STOP_LOCAL_DEPENDENTS=true
#   SKIP_CONFIRM=true
#   SSH_DEBUG=true
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    echo "Usage: $0 [user@prod-server]"
    echo ""
    echo "운영 서버의 Docker PostgreSQL 컨테이너에서 dump를 만들고,"
    echo "scp로 로컬에 가져온 뒤 로컬 Docker PostgreSQL 컨테이너에 복원합니다."
    echo ""
    echo "Options:"
    echo "  -h, --help         도움말 표시"
    echo ""
    echo "Environment variables:"
    echo "  PROD_SSH_HOST      운영 서버 SSH 대상 (예: deploy@1.2.3.4)"
    echo "  PROD_SSH_KEY       SSH key path (default: ~/.ssh/mma_deploy)"
    echo "  PROD_PROJECT_DIR   운영 서버 프로젝트 경로 (default: ~/mma-savant)"
    echo "  PROD_DB_CONTAINER  운영 DB 컨테이너명 (default: savant_db)"
    echo "  LOCAL_DB_CONTAINER 로컬 DB 컨테이너명 (default: savant_db)"
    echo "  DB_USER            DB 사용자 (.env에서 자동 감지)"
    echo "  DB_NAME            DB 이름 (.env에서 자동 감지)"
    echo "  LOCAL_DUMP_PATH    로컬 dump 저장 경로 (default: /tmp/mma-savant-prod.dump)"
    echo "  LOCAL_DEPENDENT_CONTAINERS 복원 중 잠시 멈출 컨테이너 목록 (default: savant_api)"
    echo "  STOP_LOCAL_DEPENDENTS=false 로컬 의존 컨테이너 중지 생략"
    echo "  SKIP_CONFIRM=true  로컬 DB 덮어쓰기 확인 생략"
    echo "  SSH_DEBUG=true     SSH 인증 디버그 로그 출력"
    echo ""
    echo "Example:"
    echo "  $0 deploy@1.2.3.4"
    echo "  PROD_SSH_HOST=deploy@1.2.3.4 를 .env에 넣고 $0"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOCAL_ENV_FILE="${LOCAL_ENV_FILE:-$PROJECT_ROOT/.env}"

trim() {
    local value=$1
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

strip_quotes() {
    local value=$1
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
        value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
        value="${value:1:${#value}-2}"
    fi
    printf '%s' "$value"
}

load_env_file() {
    local file=$1
    local line key value

    if [ ! -f "$file" ]; then
        return 0
    fi

    while IFS= read -r line || [ -n "$line" ]; do
        line="$(trim "$line")"

        if [ -z "$line" ] || [[ "$line" == \#* ]]; then
            continue
        fi

        if [[ "$line" == export\ * ]]; then
            line="$(trim "${line#export }")"
        fi

        if [[ ! "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
            continue
        fi

        key="$(trim "${line%%=*}")"
        value="$(trim "${line#*=}")"
        value="$(strip_quotes "$value")"

        if [ -z "${!key+x}" ]; then
            export "$key=$value"
        fi
    done < "$file"
}

expand_local_path() {
    local path=$1

    if [[ "$path" == '$HOME' ]]; then
        path="$HOME"
    elif [[ "$path" == '$HOME/'* ]]; then
        path="$HOME/${path#\$HOME/}"
    elif [[ "$path" == '${HOME}' ]]; then
        path="$HOME"
    elif [[ "$path" == '${HOME}/'* ]]; then
        path="$HOME/${path#\$\{HOME\}/}"
    elif [[ "$path" == "$HOME/~" ]]; then
        path="$HOME"
    elif [[ "$path" == "$HOME/~/"* ]]; then
        path="$HOME/${path#"$HOME/~/"}"
    fi

    case "$path" in
        "~")
            printf '%s' "$HOME"
            ;;
        "~/"*)
            printf '%s/%s' "$HOME" "${path#\~/}"
            ;;
        *)
            printf '%s' "$path"
            ;;
    esac
}

load_env_file "$LOCAL_ENV_FILE"

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    show_help
    exit 0
fi

PROD_SSH_HOST="${1:-${PROD_SSH_HOST:-}}"
if [ -z "$PROD_SSH_HOST" ]; then
    log_error "운영 서버 SSH 대상이 필요합니다. 예: $0 deploy@1.2.3.4"
    log_error "또는 .env에 PROD_SSH_HOST=deploy@1.2.3.4 형태로 지정하세요."
    exit 1
fi

PROD_SSH_KEY="${PROD_SSH_KEY:-$HOME/.ssh/mma_deploy}"
PROD_SSH_KEY="$(expand_local_path "$PROD_SSH_KEY")"
PROD_PROJECT_DIR="${PROD_PROJECT_DIR:-~/mma-savant}"
PROD_DB_CONTAINER="${PROD_DB_CONTAINER:-savant_db}"
LOCAL_DB_CONTAINER="${LOCAL_DB_CONTAINER:-savant_db}"
DB_USER="${DB_USER:-}"
DB_NAME="${DB_NAME:-}"
LOCAL_DUMP_PATH="${LOCAL_DUMP_PATH:-/tmp/mma-savant-prod.dump}"
LOCAL_DEPENDENT_CONTAINERS="${LOCAL_DEPENDENT_CONTAINERS:-savant_api}"
STOP_LOCAL_DEPENDENTS="${STOP_LOCAL_DEPENDENTS:-true}"
REMOTE_DUMP_PATH="/tmp/mma-savant-prod-$(date +%Y%m%d%H%M%S).dump"

SSH_OPTS=(
    -i "$PROD_SSH_KEY"
    -o IdentitiesOnly=yes
    -o PreferredAuthentications=publickey
    -o PasswordAuthentication=no
)

if [ "${SSH_DEBUG:-false}" = "true" ]; then
    SSH_OPTS=(-v "${SSH_OPTS[@]}")
fi

if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
    log_error "DB_USER 또는 DB_NAME을 찾을 수 없습니다. .env를 확인하거나 환경변수로 지정하세요."
    exit 1
fi

if [ ! -f "$PROD_SSH_KEY" ]; then
    log_error "SSH key를 찾을 수 없습니다: $PROD_SSH_KEY"
    exit 1
fi

if ! command -v docker > /dev/null 2>&1; then
    log_error "로컬에서 docker 명령을 찾을 수 없습니다."
    exit 1
fi

if ! command -v ssh > /dev/null 2>&1 || ! command -v scp > /dev/null 2>&1; then
    log_error "ssh/scp 명령을 찾을 수 없습니다."
    exit 1
fi

log_info "==================================="
log_info "Prod DB -> Local DB Sync"
log_info "==================================="
log_info "Prod SSH: $PROD_SSH_HOST"
log_info "SSH key: $PROD_SSH_KEY"
log_info "Prod project: $PROD_PROJECT_DIR"
log_info "Prod container: $PROD_DB_CONTAINER"
log_info "Local container: $LOCAL_DB_CONTAINER"
log_info "Database: $DB_NAME"
log_info "User: $DB_USER"
log_info "Local dump: $LOCAL_DUMP_PATH"
log_info "Stop local dependents: $STOP_LOCAL_DEPENDENTS"
log_info "==================================="

if [ "${SKIP_CONFIRM:-false}" != "true" ]; then
    echo -e "${BOLD}${YELLOW}주의: 로컬 DB '$DB_NAME'이 운영 DB 내용으로 덮어써집니다.${NC}"
    read -r -p "계속할까요? [y/N] " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log_warn "취소했습니다."
        exit 0
    fi
fi

log_info "로컬 DB 컨테이너 실행 상태 확인 중..."
if ! docker inspect "$LOCAL_DB_CONTAINER" > /dev/null 2>&1; then
    log_error "로컬 DB 컨테이너를 찾을 수 없습니다: $LOCAL_DB_CONTAINER"
    log_error "먼저 docker compose up -d savant_db 를 실행하세요."
    exit 1
fi

if [ "$(docker inspect --format='{{.State.Running}}' "$LOCAL_DB_CONTAINER")" != "true" ]; then
    log_error "로컬 DB 컨테이너가 실행 중이 아닙니다: $LOCAL_DB_CONTAINER"
    log_error "먼저 docker compose up -d savant_db 를 실행하세요."
    exit 1
fi

RESTART_LOCAL_CONTAINERS=()
cleanup_local_containers() {
    if [ ${#RESTART_LOCAL_CONTAINERS[@]} -gt 0 ]; then
        log_warn "스크립트 종료 전 중지했던 로컬 컨테이너를 재시작합니다: ${RESTART_LOCAL_CONTAINERS[*]}"
        docker start "${RESTART_LOCAL_CONTAINERS[@]}" > /dev/null 2>&1 || true
    fi
}
trap cleanup_local_containers EXIT

if [ "$STOP_LOCAL_DEPENDENTS" = "true" ]; then
    for container in $LOCAL_DEPENDENT_CONTAINERS; do
        if docker inspect "$container" > /dev/null 2>&1 \
            && [ "$(docker inspect --format='{{.State.Running}}' "$container")" = "true" ]; then
            log_info "복원 중 DB 재접속을 막기 위해 로컬 컨테이너 중지: $container"
            docker stop "$container" > /dev/null
            RESTART_LOCAL_CONTAINERS+=("$container")
        fi
    done
fi

log_info "운영 서버에서 dump 생성 중..."
ssh "${SSH_OPTS[@]}" "$PROD_SSH_HOST" \
    "cd $PROD_PROJECT_DIR && docker exec $PROD_DB_CONTAINER pg_dump -U '$DB_USER' -d '$DB_NAME' --format=custom --no-owner --no-acl > '$REMOTE_DUMP_PATH'"

log_info "dump 파일을 로컬로 복사 중..."
scp "${SSH_OPTS[@]}" "$PROD_SSH_HOST:$REMOTE_DUMP_PATH" "$LOCAL_DUMP_PATH"

log_info "운영 서버 임시 dump 파일 정리 중..."
ssh "${SSH_OPTS[@]}" "$PROD_SSH_HOST" "rm -f '$REMOTE_DUMP_PATH'"

log_info "로컬 DB 연결 세션 종료 및 DB 재생성 중..."
docker exec -i "$LOCAL_DB_CONTAINER" dropdb -U "$DB_USER" --if-exists --force "$DB_NAME"
docker exec -i "$LOCAL_DB_CONTAINER" createdb -U "$DB_USER" "$DB_NAME"

log_info "로컬 DB에 dump 복원 중..."
docker exec -i "$LOCAL_DB_CONTAINER" pg_restore \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    < "$LOCAL_DUMP_PATH"

if [ ${#RESTART_LOCAL_CONTAINERS[@]} -gt 0 ]; then
    log_info "중지했던 로컬 컨테이너 재시작 중: ${RESTART_LOCAL_CONTAINERS[*]}"
    docker start "${RESTART_LOCAL_CONTAINERS[@]}" > /dev/null
    RESTART_LOCAL_CONTAINERS=()
    trap - EXIT
fi

log_success "운영 DB를 로컬 DB에 반영했습니다."
