#!/bin/bash
# =============================================================================
# 서버 초기화 스크립트
# Usage: ./scripts/init-server.sh
#
# 이 스크립트는 새 서버에서 최초 1회만 실행합니다.
# - 디렉토리 구조 확인
# - 초기 환경 설정
# - nginx.conf 생성
# - 인프라 서비스 시작 (DB, Redis, Nginx)
# =============================================================================

set -e

# 경로 설정
PROJECT_DIR=~/mma-savant
COMPOSE_FILE=$PROJECT_DIR/docker-compose.prod.yml
NGINX_TEMPLATE=$PROJECT_DIR/nginx/nginx.conf.template
NGINX_CONF=$PROJECT_DIR/nginx/nginx.conf
ENV_FILE=$PROJECT_DIR/.env
ACTIVE_ENV_FILE=$PROJECT_DIR/.active-env

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

echo ""
log_info "==================================="
log_info "MMA Savant Server Initialization"
log_info "==================================="
echo ""

# 1. 필수 파일 확인
log_info "Checking required files..."

MISSING_FILES=()

if [ ! -f "$COMPOSE_FILE" ]; then
    MISSING_FILES+=("docker-compose.prod.yml")
fi

if [ ! -f "$NGINX_TEMPLATE" ]; then
    MISSING_FILES+=("nginx/nginx.conf.template")
fi

if [ ! -f "$ENV_FILE" ]; then
    MISSING_FILES+=(".env")
fi

if [ ! -d "$PROJECT_DIR/init_sqls" ]; then
    MISSING_FILES+=("init_sqls/")
fi

if [ ! -f "$PROJECT_DIR/scripts/deploy-blue-green.sh" ]; then
    MISSING_FILES+=("scripts/deploy-blue-green.sh")
fi

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    log_error "Missing required files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    echo ""
    log_error "Please copy these files to the server first."
    exit 1
fi

log_success "All required files found"

# 2. 스크립트 실행 권한 부여
log_info "Setting script permissions..."
chmod +x $PROJECT_DIR/scripts/*.sh
log_success "Script permissions set"

# 3. 초기 환경 설정 (Blue)
log_info "Setting initial environment to 'blue'..."
echo "blue" > $ACTIVE_ENV_FILE
log_success "Active environment set to 'blue'"

# 4. SERVER_PORT 읽기
SERVER_PORT=$(grep -E "^SERVER_PORT=" $ENV_FILE | cut -d'=' -f2)
if [ -z "$SERVER_PORT" ]; then
    log_warn "SERVER_PORT not found in .env, using default: 8000"
    SERVER_PORT=8000
fi
log_info "Using SERVER_PORT: $SERVER_PORT"

# 5. 초기 nginx.conf 생성
log_info "Generating initial nginx.conf..."
export ACTIVE_API=api-blue
export ACTIVE_WEB=web-blue
export SERVER_PORT=$SERVER_PORT
envsubst '${ACTIVE_API} ${ACTIVE_WEB} ${SERVER_PORT}' < $NGINX_TEMPLATE > $NGINX_CONF
log_success "nginx.conf generated"

# 6. Docker 상태 확인
log_info "Checking Docker..."
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed!"
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker daemon is not running!"
    exit 1
fi
log_success "Docker is ready"

# 7. 기존 컨테이너 정리 (있으면)
log_info "Cleaning up existing containers (if any)..."
cd $PROJECT_DIR
docker compose -f $COMPOSE_FILE down 2>/dev/null || true

# 8. 인프라 서비스 시작
log_info "Starting infrastructure services..."
docker compose -f $COMPOSE_FILE up -d savant_db redis nginx

# 9. 서비스 상태 확인
log_info "Waiting for services to be ready..."
sleep 5

# DB Health Check
log_info "Checking PostgreSQL..."
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if docker exec savant_db pg_isready -U $(grep -E "^DB_USER=" $ENV_FILE | cut -d'=' -f2) > /dev/null 2>&1; then
        log_success "PostgreSQL is ready"
        break
    fi
    RETRY=$((RETRY + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY -ge $MAX_RETRIES ]; then
    log_error "PostgreSQL failed to start"
    exit 1
fi

# Redis Health Check
log_info "Checking Redis..."
REDIS_PASSWORD=$(grep -E "^REDIS_PASSWORD=" $ENV_FILE | cut -d'=' -f2)
if docker exec savant_redis redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
    log_success "Redis is ready"
else
    log_warn "Redis health check failed (may still be starting)"
fi

# Nginx 상태 확인
log_info "Checking Nginx..."
if docker ps --format '{{.Names}}' | grep -q "nginx"; then
    log_success "Nginx is running"
else
    log_warn "Nginx may not be running correctly"
fi

# 10. 최종 상태 출력
echo ""
log_success "==================================="
log_success "Server Initialization Complete!"
log_success "==================================="
echo ""
log_info "Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
log_info "Next steps:"
echo "  1. Push a git tag to trigger CD: git tag v0.1.0 && git push origin v0.1.0"
echo "  2. Or manually deploy: ./scripts/deploy-blue-green.sh <VERSION> <REGISTRY>"
echo ""
log_info "Useful commands:"
echo "  - View logs: docker compose -f docker-compose.prod.yml logs -f"
echo "  - Rollback:  ./scripts/rollback.sh"
echo "  - Status:    docker ps"
echo ""
