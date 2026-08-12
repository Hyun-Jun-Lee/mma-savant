#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$SCRIPT_DIR/detect-component-changes.sh"

run_case() {
    local name=$1
    local expected_api=$2
    local expected_web=$3
    local expected_flow=$4
    shift 4

    local output
    output=$("$SCRIPT" "$@")

    grep -q "^api_changed=$expected_api$" <<< "$output"
    grep -q "^web_changed=$expected_web$" <<< "$output"
    grep -q "^flow_changed=$expected_flow$" <<< "$output"
    echo "ok - $name"
}

run_case "frontend only" false true false "frontend/src/app/page.tsx"
run_case "api only" true false false "src/api/dashboard/routes.py"
run_case "flow only" false false true "src/data_collector/workflows/ufc_stats_flow.py"
run_case "shared model" true false true "src/fighter/models.py"
run_case "deployment script" true true true "scripts/deploy-blue-green.sh"
run_case "no impacting files" false false false "docs/plan/example.md"
