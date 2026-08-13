#!/bin/bash
# =============================================================================
# Prefect Flow Serve 컨테이너 업데이트/재시작 스크립트
# Usage:
#   ./scripts/restart-flow-serve.sh <VERSION> [REGISTRY]
#   ./scripts/restart-flow-serve.sh --flow-version <VERSION> --registry <REGISTRY>
# =============================================================================

set -euo pipefail

FLOW_VERSION=${FLOW_VERSION:-${IMAGE_VERSION:-}}
RELEASE_VERSION=${RELEASE_VERSION:-}
REGISTRY=${REGISTRY:-"ghcr.io/hyun-jun-lee/mma-savant"}
PROJECT_DIR=${PROJECT_DIR:-"$HOME/mma-savant"}
COMPOSE_FILE=${COMPOSE_FILE:-"$PROJECT_DIR/docker-compose.prod.yml"}

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
  restart-flow-serve.sh <VERSION> [REGISTRY]
  restart-flow-serve.sh --flow-version <VERSION> --registry <REGISTRY> [--release-version <VERSION>]

Examples:
  ./scripts/restart-flow-serve.sh v0.18.0 ghcr.io/hyun-jun-lee/mma-savant
  ./scripts/restart-flow-serve.sh --flow-version v0.18.0 --registry ghcr.io/hyun-jun-lee/mma-savant

Environment fallback:
  FLOW_VERSION, IMAGE_VERSION, RELEASE_VERSION, REGISTRY, PROJECT_DIR, COMPOSE_FILE
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --flow-version)
            FLOW_VERSION=${2:-}
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
            if [ -z "$FLOW_VERSION" ]; then
                FLOW_VERSION=$1
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

if [ -z "$RELEASE_VERSION" ]; then
    RELEASE_VERSION=$FLOW_VERSION
fi

if [ -z "$FLOW_VERSION" ] || [ -z "$REGISTRY" ]; then
    log_error "FLOW_VERSION and REGISTRY are required."
    show_usage
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose file not found: $COMPOSE_FILE"
    log_warn "Set PROJECT_DIR or COMPOSE_FILE if the production checkout is in a different path."
    exit 1
fi

export REGISTRY
export FLOW_IMAGE_VERSION="$FLOW_VERSION"
export IMAGE_VERSION="$RELEASE_VERSION"

log_info "==================================="
log_info "Prefect Flow Serve Restart"
log_info "==================================="
log_info "Release: $RELEASE_VERSION"
log_info "Flow Version: $FLOW_VERSION"
log_info "Registry: $REGISTRY"
log_info "Project:  $PROJECT_DIR"
log_info "==================================="

cd "$PROJECT_DIR"

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

log_info "Pulling flow_serve image..."
docker compose -f "$COMPOSE_FILE" --profile manual pull flow_serve

log_info "Recreating flow_serve container..."
docker compose -f "$COMPOSE_FILE" --profile manual up -d --no-deps --force-recreate flow_serve

if docker ps --filter "name=flow_serve" --filter "status=running" | grep -q flow_serve; then
    log_success "flow_serve is running."
else
    log_error "flow_serve is not running after recreate."
    docker compose -f "$COMPOSE_FILE" --profile manual logs --tail 80 flow_serve
    exit 1
fi

echo "$FLOW_VERSION" > "$PROJECT_DIR/.deployed-flow-version"
log_success "Deployed flow version recorded: $FLOW_VERSION"

log_success "==================================="
log_success "flow_serve restart completed!"
log_success "==================================="
log_info "View logs:"
log_info "  docker compose -f $COMPOSE_FILE --profile manual logs -f flow_serve"
