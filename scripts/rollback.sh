#!/bin/bash
# =============================================================================
# Blue-Green 롤백 스크립트
# Usage: ./scripts/rollback.sh
# =============================================================================

set -e

# 경로 설정
PROJECT_DIR=~/mma-savant
NGINX_TEMPLATE=$PROJECT_DIR/nginx/nginx.conf.template
NGINX_CONF=$PROJECT_DIR/nginx/nginx.conf
ACTIVE_ENV_FILE=$PROJECT_DIR/.active-env
COMPOSE_FILE=$PROJECT_DIR/docker-compose.prod.yml

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# 현재 활성 환경 확인
if [ ! -f "$ACTIVE_ENV_FILE" ]; then
    log_error "No active environment file found"
    exit 1
fi

CURRENT=$(cat $ACTIVE_ENV_FILE)

# 롤백 대상 결정
if [ "$CURRENT" = "blue" ]; then
    ROLLBACK_TO="green"
else
    ROLLBACK_TO="blue"
fi

log_info "==================================="
log_info "Blue-Green Rollback"
log_info "==================================="
log_info "Current: $CURRENT"
log_info "Rollback to: $ROLLBACK_TO"
log_info "==================================="

cd $PROJECT_DIR

# 1. 롤백 대상 환경이 실행 가능한지 확인
log_info "Checking if $ROLLBACK_TO environment exists..."

if ! docker ps -a --format '{{.Names}}' | grep -q "api-$ROLLBACK_TO"; then
    log_error "Container api-$ROLLBACK_TO not found"
    log_error "Cannot rollback - previous environment doesn't exist"
    exit 1
fi

# 2. 롤백 대상 환경 시작
log_info "Starting $ROLLBACK_TO environment..."
docker compose -f $COMPOSE_FILE --profile $ROLLBACK_TO start

# 3. Health Check
log_info "Waiting for health check..."
MAX_RETRIES=15
RETRY=0

while [ $RETRY -lt $MAX_RETRIES ]; do
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' api-$ROLLBACK_TO 2>/dev/null || echo "starting")

    if [ "$HEALTH_STATUS" = "healthy" ]; then
        log_success "Health check passed!"
        break
    fi

    RETRY=$((RETRY + 1))
    log_info "  Retry $RETRY/$MAX_RETRIES (status: $HEALTH_STATUS)..."
    sleep 2
done

if [ $RETRY -ge $MAX_RETRIES ]; then
    log_error "Rollback failed - $ROLLBACK_TO environment is not healthy"
    exit 1
fi

# 4. Nginx 설정 전환
log_info "Switching Nginx to $ROLLBACK_TO environment..."

if [ -f "$NGINX_TEMPLATE" ]; then
    export ACTIVE_API=api-$ROLLBACK_TO
    export ACTIVE_WEB=web-$ROLLBACK_TO
    export SERVER_PORT=$(grep -E "^SERVER_PORT=" $PROJECT_DIR/.env | cut -d'=' -f2)
    envsubst '${ACTIVE_API} ${ACTIVE_WEB} ${SERVER_PORT}' < $NGINX_TEMPLATE > $NGINX_CONF

    if docker exec nginx nginx -t > /dev/null 2>&1; then
        docker exec nginx nginx -s reload
        log_success "Nginx configuration updated"
    else
        log_error "Nginx configuration test failed!"
        exit 1
    fi
fi

# 5. 활성 환경 기록 업데이트
echo "$ROLLBACK_TO" > $ACTIVE_ENV_FILE

# 6. 이전 환경(문제 있던 환경) 종료
log_info "Stopping $CURRENT environment..."
docker compose -f $COMPOSE_FILE --profile $CURRENT stop 2>/dev/null || true

# 완료
log_success "==================================="
log_success "Rollback completed!"
log_success "==================================="
log_success "Active: $ROLLBACK_TO"
log_success "==================================="
