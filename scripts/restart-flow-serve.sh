#!/bin/bash
# =============================================================================
# Prefect Flow Serve 컨테이너 업데이트/재시작 스크립트
# Usage: ./scripts/restart-flow-serve.sh <VERSION> [REGISTRY]
# Example: ./scripts/restart-flow-serve.sh v0.15.2 ghcr.io/hyun-jun-lee/mma-savant
# =============================================================================

set -euo pipefail

VERSION=${1:-${IMAGE_VERSION:-}}
REGISTRY=${2:-${REGISTRY:-"ghcr.io/hyun-jun-lee/mma-savant"}}
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
    echo "Usage: $0 <VERSION> [REGISTRY]"
    echo "Example: $0 v0.15.3 ghcr.io/hyun-jun-lee/mma-savant"
    echo ""
    echo "You can also set IMAGE_VERSION and REGISTRY as environment variables."
}

if [ -z "$VERSION" ]; then
    log_error "VERSION is required."
    show_usage
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose file not found: $COMPOSE_FILE"
    log_warn "Set PROJECT_DIR or COMPOSE_FILE if the production checkout is in a different path."
    exit 1
fi

log_info "==================================="
log_info "Prefect Flow Serve Restart"
log_info "==================================="
log_info "Version: $VERSION"
log_info "Registry: $REGISTRY"
log_info "Project:  $PROJECT_DIR"
log_info "==================================="

cd "$PROJECT_DIR"

export REGISTRY
export IMAGE_VERSION="$VERSION"

log_info "Pulling flow_serve image..."
docker compose -f "$COMPOSE_FILE" --profile manual pull flow_serve

log_info "Recreating flow_serve container..."
docker compose -f "$COMPOSE_FILE" --profile manual up -d --force-recreate flow_serve

if docker ps --filter "name=flow_serve" --filter "status=running" | grep -q flow_serve; then
    log_success "flow_serve is running."
else
    log_error "flow_serve is not running after recreate."
    docker compose -f "$COMPOSE_FILE" --profile manual logs --tail 80 flow_serve
    exit 1
fi

log_success "==================================="
log_success "flow_serve restart completed!"
log_success "==================================="
log_info "View logs:"
log_info "  docker compose -f $COMPOSE_FILE --profile manual logs -f flow_serve"
