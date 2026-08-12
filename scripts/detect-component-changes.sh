#!/bin/bash
# =============================================================================
# CD component change detector.
#
# Accepts changed file paths as arguments or stdin and emits:
#   api_changed=true|false
#   web_changed=true|false
#   flow_changed=true|false
#
# When running in GitHub Actions, outputs are also appended to $GITHUB_OUTPUT.
# =============================================================================

set -euo pipefail

api_changed=false
web_changed=false
flow_changed=false

if [ "$#" -gt 0 ]; then
    files=("$@")
else
    files=()
    while IFS= read -r file; do
        [ -n "$file" ] && files+=("$file")
    done
fi

mark_all() {
    api_changed=true
    web_changed=true
    flow_changed=true
}

for file in "${files[@]}"; do
    case "$file" in
        .github/workflows/cd.yml|docker-compose.prod.yml|scripts/deploy-blue-green.sh|scripts/restart-flow-serve.sh|scripts/detect-component-changes.sh|scripts/tests/test_detect_component_changes.sh)
            mark_all
            ;;
        frontend/*|frontend/**)
            web_changed=true
            ;;
        Dockerfile_flow|src/data_collector/*|src/data_collector/**)
            flow_changed=true
            ;;
        Dockerfile_api|src/main_api.py|src/api/*|src/api/**|src/conversation/*|src/conversation/**|src/dashboard/*|src/dashboard/**|src/llm/*|src/llm/**|src/user/*|src/user/**)
            api_changed=true
            ;;
        src/common/*|src/common/**|src/config.py|src/database/*|src/database/**|src/event/*|src/event/**|src/fighter/*|src/fighter/**|src/match/*|src/match/**|src/pyproject.toml|src/requirements.txt|src/uv.lock)
            api_changed=true
            flow_changed=true
            ;;
        nginx/*|nginx/**|scripts/init-server.sh|scripts/rollback.sh)
            api_changed=true
            web_changed=true
            ;;
    esac
done

outputs=$(cat <<EOF
api_changed=$api_changed
web_changed=$web_changed
flow_changed=$flow_changed
EOF
)

printf '%s\n' "$outputs"
if [ -n "${GITHUB_OUTPUT:-}" ]; then
    printf '%s\n' "$outputs" >> "$GITHUB_OUTPUT"
fi
