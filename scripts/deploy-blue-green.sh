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

# 0. 초기 Nginx 설정 생성
log_info "Generating initial Nginx configuration..."
if [ -f "$NGINX_TEMPLATE" ]; then
    export ACTIVE_API=api-$NEW
    export ACTIVE_WEB=web-$NEW
    export SERVER_PORT=$(grep -E "^SERVER_PORT=" $PROJECT_DIR/.env | cut -d'=' -f2)
    envsubst '${ACTIVE_API} ${ACTIVE_WEB} ${SERVER_PORT}' < $NGINX_TEMPLATE > $NGINX_CONF
    log_success "Nginx configuration generated for $NEW environment"
else
    log_error "Nginx template not found at $NGINX_TEMPLATE"
    exit 1
fi

# 1. 인프라 서비스 확인 및 시작 (DB, Redis만 먼저)
log_info "Starting infrastructure services (DB, Redis)..."
docker compose -f $COMPOSE_FILE up -d savant_db redis

# DB/Redis Health Check 대기
log_info "Waiting for DB and Redis to be healthy..."
MAX_INFRA_RETRIES=30
INFRA_RETRY=0

while [ $INFRA_RETRY -lt $MAX_INFRA_RETRIES ]; do
    DB_STATUS=$(docker inspect --format='{{.State.Health.Status}}' savant_db 2>/dev/null || echo "starting")
    REDIS_STATUS=$(docker inspect --format='{{.State.Health.Status}}' savant_redis 2>/dev/null || echo "starting")

    if [ "$DB_STATUS" = "healthy" ] && [ "$REDIS_STATUS" = "healthy" ]; then
        log_success "Infrastructure services are healthy!"
        break
    fi

    INFRA_RETRY=$((INFRA_RETRY + 1))
    log_info "  Retry $INFRA_RETRY/$MAX_INFRA_RETRIES (DB: $DB_STATUS, Redis: $REDIS_STATUS)..."
    sleep 2
done

if [ $INFRA_RETRY -ge $MAX_INFRA_RETRIES ]; then
    log_error "Infrastructure services failed to become healthy"
    exit 1
fi

# 2. 이미지 Pull
log_info "Pulling images..."
docker pull $REGISTRY/api:$VERSION
docker pull $REGISTRY/web:$VERSION

log_success "Images pulled successfully"

# 3. 환경변수 설정 및 새 환경 시작 (API, Web)
log_info "Starting $NEW environment (API, Web)..."
export REGISTRY=$REGISTRY
export IMAGE_VERSION=$VERSION
docker compose -f $COMPOSE_FILE --profile $NEW up -d

# 4. Health Check 대기
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

# 5. Web Health Check 대기
log_info "Waiting for web-$NEW to be healthy..."
MAX_WEB_RETRIES=30
WEB_RETRY=0

while [ $WEB_RETRY -lt $MAX_WEB_RETRIES ]; do
    WEB_STATUS=$(docker inspect --format='{{.State.Health.Status}}' web-$NEW 2>/dev/null || echo "starting")

    if [ "$WEB_STATUS" = "healthy" ]; then
        log_success "Web health check passed!"
        break
    fi

    WEB_RETRY=$((WEB_RETRY + 1))
    log_info "  Retry $WEB_RETRY/$MAX_WEB_RETRIES (status: $WEB_STATUS)..."
    sleep 2
done

if [ $WEB_RETRY -ge $MAX_WEB_RETRIES ]; then
    log_error "Web health check failed after $MAX_WEB_RETRIES attempts"
    log_warn "Rolling back..."
    docker compose -f $COMPOSE_FILE --profile $NEW stop
    exit 1
fi

# 6. Nginx 시작 (강제 재생성으로 새 설정 적용)
log_info "Starting Nginx (force recreate)..."
docker compose -f $COMPOSE_FILE up -d --force-recreate nginx

# Nginx 상태 확인
sleep 5
if docker ps --filter "name=nginx" --filter "status=running" | grep -q nginx; then
    log_success "Nginx started successfully"
else
    log_error "Nginx failed to start!"
    docker logs nginx --tail 30
    exit 1
fi

# Nginx health check 대기
log_info "Waiting for Nginx to be ready..."
NGINX_RETRY=0
MAX_NGINX_RETRIES=10

while [ $NGINX_RETRY -lt $MAX_NGINX_RETRIES ]; do
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        log_success "Nginx is responding to health checks!"
        break
    fi

    NGINX_RETRY=$((NGINX_RETRY + 1))
    log_info "  Retry $NGINX_RETRY/$MAX_NGINX_RETRIES..."
    sleep 2
done

if [ $NGINX_RETRY -ge $MAX_NGINX_RETRIES ]; then
    log_error "Nginx health check failed"
    docker logs nginx --tail 30
    exit 1
fi

# 7. 활성 환경 기록
echo "$NEW" > $ACTIVE_ENV_FILE
log_success "Active environment updated: $NEW"

# 8. 배포 버전 기록
echo "$VERSION" > $PROJECT_DIR/.deployed-version
log_success "Deployed version recorded: $VERSION"

# 9. 구 환경 종료
log_info "Stopping $OLD environment..."
docker compose -f $COMPOSE_FILE --profile $OLD stop 2>/dev/null || true

# 10. 이전 이미지 정리
log_info "Cleaning up old images..."
docker image prune -f > /dev/null 2>&1 || true

# 완료
log_success "==================================="
log_success "Deployment completed!"
log_success "==================================="
log_success "Active: $NEW"
log_success "Version: $VERSION"
log_success "==================================="
