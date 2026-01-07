#!/bin/bash
# =============================================================================
# Blue-Green 배포 스크립트
# Usage: ./scripts/deploy-blue-green.sh <VERSION> <REGISTRY>
# Example: ./scripts/deploy-blue-green.sh v1.0.0 ghcr.io/username/mma-savant
# =============================================================================

set -e

# 인자 확인
VERSION=${1:-latest}
REGISTRY=${2:-"ghcr.io/your-username/mma-savant"}

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
if [ -f "$ACTIVE_ENV_FILE" ]; then
    CURRENT=$(cat $ACTIVE_ENV_FILE)
else
    CURRENT="blue"
    echo "blue" > $ACTIVE_ENV_FILE
fi

# 새 환경 결정
if [ "$CURRENT" = "blue" ]; then
    NEW="green"
    OLD="blue"
else
    NEW="blue"
    OLD="green"
fi

log_info "==================================="
log_info "Blue-Green Deployment"
log_info "==================================="
log_info "Version: $VERSION"
log_info "Registry: $REGISTRY"
log_info "Current: $OLD → New: $NEW"
log_info "==================================="

cd $PROJECT_DIR

# 1. 이미지 Pull
log_info "Pulling images..."
docker pull $REGISTRY/api:$VERSION
docker pull $REGISTRY/web:$VERSION

log_success "Images pulled successfully"

# 2. 환경변수 설정 및 새 환경 시작
log_info "Starting $NEW environment..."
export REGISTRY=$REGISTRY
export IMAGE_VERSION=$VERSION
docker compose -f $COMPOSE_FILE --profile $NEW up -d

# 3. Health Check 대기
log_info "Waiting for health check..."
MAX_RETRIES=30
RETRY=0

while [ $RETRY -lt $MAX_RETRIES ]; do
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' api-$NEW 2>/dev/null || echo "starting")

    if [ "$HEALTH_STATUS" = "healthy" ]; then
        log_success "Health check passed!"
        break
    fi

    RETRY=$((RETRY + 1))
    log_info "  Retry $RETRY/$MAX_RETRIES (status: $HEALTH_STATUS)..."
    sleep 2
done

if [ $RETRY -ge $MAX_RETRIES ]; then
    log_error "Health check failed after $MAX_RETRIES attempts"
    log_warn "Rolling back..."
    docker compose -f $COMPOSE_FILE --profile $NEW stop
    exit 1
fi

# 4. Nginx 설정 전환
log_info "Switching Nginx to $NEW environment..."

if [ -f "$NGINX_TEMPLATE" ]; then
    export ACTIVE_API=api-$NEW
    export ACTIVE_WEB=web-$NEW
    export SERVER_PORT=$(grep -E "^SERVER_PORT=" $PROJECT_DIR/.env | cut -d'=' -f2)
    envsubst '${ACTIVE_API} ${ACTIVE_WEB} ${SERVER_PORT}' < $NGINX_TEMPLATE > $NGINX_CONF

    # Nginx 리로드
    if docker exec nginx nginx -t > /dev/null 2>&1; then
        docker exec nginx nginx -s reload
        log_success "Nginx configuration updated and reloaded"
    else
        log_error "Nginx configuration test failed!"
        exit 1
    fi
else
    log_warn "Nginx template not found, skipping Nginx configuration"
fi

# 5. 활성 환경 기록
echo "$NEW" > $ACTIVE_ENV_FILE
log_success "Active environment updated: $NEW"

# 6. 배포 버전 기록
echo "$VERSION" > $PROJECT_DIR/.deployed-version
log_success "Deployed version recorded: $VERSION"

# 7. 구 환경 종료
log_info "Stopping $OLD environment..."
docker compose -f $COMPOSE_FILE --profile $OLD stop 2>/dev/null || true

# 8. 이전 이미지 정리
log_info "Cleaning up old images..."
docker image prune -f > /dev/null 2>&1 || true

# 완료
log_success "==================================="
log_success "Deployment completed!"
log_success "==================================="
log_success "Active: $NEW"
log_success "Version: $VERSION"
log_success "==================================="
