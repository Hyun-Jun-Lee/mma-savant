#!/bin/bash
# =============================================================================
# Blue-Green 배포 스크립트
# Usage:
#   ./scripts/deploy-blue-green.sh <VERSION> [REGISTRY]
#   ./scripts/deploy-blue-green.sh --api-version <VERSION> --web-version <VERSION> --registry <REGISTRY>
# =============================================================================

set -euo pipefail

PROJECT_DIR=${PROJECT_DIR:-"$HOME/mma-savant"}
NGINX_TEMPLATE=$PROJECT_DIR/nginx/nginx.conf.template
NGINX_CONF=$PROJECT_DIR/nginx/nginx.conf
ACTIVE_ENV_FILE=$PROJECT_DIR/.active-env
COMPOSE_FILE=$PROJECT_DIR/docker-compose.prod.yml

API_VERSION=${API_VERSION:-}
WEB_VERSION=${WEB_VERSION:-}
RELEASE_VERSION=${RELEASE_VERSION:-}
REGISTRY=${REGISTRY:-"ghcr.io/your-username/mma-savant"}

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

show_usage() {
    cat <<'EOF'
Usage:
  deploy-blue-green.sh <VERSION> [REGISTRY]
  deploy-blue-green.sh --api-version <VERSION> --web-version <VERSION> --registry <REGISTRY> [--release-version <VERSION>]

Examples:
  ./scripts/deploy-blue-green.sh v0.18.0 ghcr.io/hyun-jun-lee/mma-savant
  ./scripts/deploy-blue-green.sh --api-version v0.17.3 --web-version v0.18.0 --registry ghcr.io/hyun-jun-lee/mma-savant

Environment fallback:
  API_VERSION, WEB_VERSION, RELEASE_VERSION, REGISTRY, PROJECT_DIR, COMPOSE_FILE
EOF
}

read_version_file() {
    local component=$1
    local component_file="$PROJECT_DIR/.deployed-${component}-version"
    local legacy_file="$PROJECT_DIR/.deployed-version"

    if [ -f "$component_file" ]; then
        tr -d '[:space:]' < "$component_file"
        return
    fi

    if [ -f "$legacy_file" ]; then
        tr -d '[:space:]' < "$legacy_file"
        return
    fi
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --api-version)
            API_VERSION=${2:-}
            shift 2
            ;;
        --web-version)
            WEB_VERSION=${2:-}
            shift 2
            ;;
        --release-version)
            RELEASE_VERSION=${2:-}
            shift 2
            ;;
        --registry)
            REGISTRY=${2:-}
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        --*)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [ -z "$API_VERSION" ] && [ -z "$WEB_VERSION" ] && [ -z "$RELEASE_VERSION" ]; then
                API_VERSION=$1
                WEB_VERSION=$1
                RELEASE_VERSION=$1
                shift
                if [ "$#" -gt 0 ]; then
                    REGISTRY=$1
                    shift
                fi
            else
                log_error "Unexpected positional argument: $1"
                show_usage
                exit 1
            fi
            ;;
    esac
done

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose file not found: $COMPOSE_FILE"
    log_warn "Set PROJECT_DIR or COMPOSE_FILE if the production checkout is in a different path."
    exit 1
fi

if [ -z "$API_VERSION" ]; then
    API_VERSION=$(read_version_file "api" || true)
fi

if [ -z "$WEB_VERSION" ]; then
    WEB_VERSION=$(read_version_file "web" || true)
fi

if [ -z "$RELEASE_VERSION" ]; then
    if [ "$API_VERSION" = "$WEB_VERSION" ]; then
        RELEASE_VERSION=$API_VERSION
    else
        RELEASE_VERSION="api-${API_VERSION}_web-${WEB_VERSION}"
    fi
fi

if [ -z "$API_VERSION" ] || [ -z "$WEB_VERSION" ] || [ -z "$REGISTRY" ]; then
    log_error "API_VERSION, WEB_VERSION, and REGISTRY are required."
    show_usage
    exit 1
fi

export REGISTRY
export API_IMAGE_VERSION="$API_VERSION"
export WEB_IMAGE_VERSION="$WEB_VERSION"
export IMAGE_VERSION="$RELEASE_VERSION"

if [ -f "$ACTIVE_ENV_FILE" ]; then
    CURRENT=$(cat "$ACTIVE_ENV_FILE")
else
    CURRENT="blue"
    echo "blue" > "$ACTIVE_ENV_FILE"
fi

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
log_info "Release: $RELEASE_VERSION"
log_info "API Version: $API_VERSION"
log_info "Web Version: $WEB_VERSION"
log_info "Registry: $REGISTRY"
log_info "Current: $CURRENT -> New: $NEW"
log_info "==================================="

cd "$PROJECT_DIR"

log_info "Generating initial Nginx configuration..."
if [ -f "$NGINX_TEMPLATE" ]; then
    export ACTIVE_API=api-$NEW
    export ACTIVE_WEB=web-$NEW
    SERVER_PORT=$(grep -E "^SERVER_PORT=" "$PROJECT_DIR/.env" | cut -d'=' -f2 || true)
    DOMAIN_NAME=$(grep -E "^DOMAIN_NAME=" "$PROJECT_DIR/.env" | cut -d'=' -f2 || true)
    export SERVER_PORT=${SERVER_PORT:-8000}
    export DOMAIN_NAME=${DOMAIN_NAME:-_}
    envsubst '${ACTIVE_API} ${ACTIVE_WEB} ${SERVER_PORT} ${DOMAIN_NAME}' < "$NGINX_TEMPLATE" > "$NGINX_CONF"
    log_success "Nginx configuration generated for $NEW environment"
else
    log_error "Nginx template not found at $NGINX_TEMPLATE"
    exit 1
fi

log_info "Starting infrastructure services (DB, Redis)..."
docker compose -f "$COMPOSE_FILE" up -d savant_db redis

log_info "Waiting for DB and Redis to be healthy..."
MAX_INFRA_RETRIES=30
INFRA_RETRY=0

while [ "$INFRA_RETRY" -lt "$MAX_INFRA_RETRIES" ]; do
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

if [ "$INFRA_RETRY" -ge "$MAX_INFRA_RETRIES" ]; then
    log_error "Infrastructure services failed to become healthy"
    exit 1
fi

log_info "Pulling images..."
docker pull "$REGISTRY/api:$API_VERSION"
docker pull "$REGISTRY/web:$WEB_VERSION"
log_success "Images pulled successfully"

log_info "Starting $NEW environment (API, Web)..."
docker compose -f "$COMPOSE_FILE" --profile "$NEW" up -d

log_info "Waiting for API health check..."
MAX_RETRIES=30
RETRY=0

while [ "$RETRY" -lt "$MAX_RETRIES" ]; do
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "api-$NEW" 2>/dev/null || echo "starting")

    if [ "$HEALTH_STATUS" = "healthy" ]; then
        log_success "API health check passed!"
        break
    fi

    RETRY=$((RETRY + 1))
    log_info "  Retry $RETRY/$MAX_RETRIES (status: $HEALTH_STATUS)..."
    sleep 2
done

if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
    log_error "API health check failed after $MAX_RETRIES attempts"
    log_warn "Rolling back..."
    docker stop "api-$NEW" "web-$NEW" 2>/dev/null || true
    exit 1
fi

log_info "Waiting for web-$NEW to be healthy..."
MAX_WEB_RETRIES=30
WEB_RETRY=0

while [ "$WEB_RETRY" -lt "$MAX_WEB_RETRIES" ]; do
    WEB_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "web-$NEW" 2>/dev/null || echo "starting")

    if [ "$WEB_STATUS" = "healthy" ]; then
        log_success "Web health check passed!"
        break
    fi

    WEB_RETRY=$((WEB_RETRY + 1))
    log_info "  Retry $WEB_RETRY/$MAX_WEB_RETRIES (status: $WEB_STATUS)..."
    sleep 2
done

if [ "$WEB_RETRY" -ge "$MAX_WEB_RETRIES" ]; then
    log_error "Web health check failed after $MAX_WEB_RETRIES attempts"
    log_warn "Rolling back..."
    docker stop "api-$NEW" "web-$NEW" 2>/dev/null || true
    exit 1
fi

log_info "Starting Nginx (force recreate)..."
docker compose -f "$COMPOSE_FILE" up -d --force-recreate nginx

sleep 5
if docker ps --filter "name=nginx" --filter "status=running" | grep -q nginx; then
    log_success "Nginx started successfully"
else
    log_error "Nginx failed to start!"
    docker logs nginx --tail 30
    exit 1
fi

log_info "Waiting for Nginx to be ready..."
NGINX_RETRY=0
MAX_NGINX_RETRIES=10

while [ "$NGINX_RETRY" -lt "$MAX_NGINX_RETRIES" ]; do
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        log_success "Nginx is responding to health checks!"
        break
    fi

    NGINX_RETRY=$((NGINX_RETRY + 1))
    log_info "  Retry $NGINX_RETRY/$MAX_NGINX_RETRIES..."
    sleep 2
done

if [ "$NGINX_RETRY" -ge "$MAX_NGINX_RETRIES" ]; then
    log_error "Nginx health check failed"
    docker logs nginx --tail 30
    exit 1
fi

echo "$NEW" > "$ACTIVE_ENV_FILE"
log_success "Active environment updated: $NEW"

echo "$API_VERSION" > "$PROJECT_DIR/.deployed-api-version"
echo "$WEB_VERSION" > "$PROJECT_DIR/.deployed-web-version"
echo "$RELEASE_VERSION" > "$PROJECT_DIR/.deployed-version"
log_success "Deployed versions recorded: api=$API_VERSION web=$WEB_VERSION release=$RELEASE_VERSION"

log_info "Stopping $OLD environment..."
docker stop "api-$OLD" "web-$OLD" 2>/dev/null || true

log_info "Cleaning up old images..."
docker image prune -f > /dev/null 2>&1 || true

log_success "==================================="
log_success "Deployment completed!"
log_success "==================================="
log_success "Active: $NEW"
log_success "API: $API_VERSION"
log_success "Web: $WEB_VERSION"
log_success "==================================="
