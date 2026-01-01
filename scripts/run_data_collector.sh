#!/bin/bash

# UFC Stats Data Collector 실행 스크립트
# tmux 세션 'data_collector'에서 실행

SESSION_NAME="data_collector"
PROJECT_DIR="/Users/hj/Documents/GitHub/mma-savant"
SRC_DIR="$PROJECT_DIR/src"

# 인자가 없으면 도움말 표시
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --tasks TASK [TASK...]  실행할 태스크 (fighters, events, event-detail, match-detail, rankings)"
    echo "  -a, --all                   전체 태스크 실행"
    echo "  -l, --list                  사용 가능한 태스크 목록"
    echo "  -k, --kill                  기존 세션 종료"
    echo "  -s, --attach                세션에 접속"
    echo "  -h, --help                  도움말 표시"
    echo ""
    echo "Examples:"
    echo "  $0 -a                       # 전체 실행"
    echo "  $0 -t event-detail          # event-detail만 실행"
    echo "  $0 -t fighters events       # fighters, events 실행"
    echo "  $0 -s                       # 세션에 접속"
    echo "  $0 -k                       # 세션 종료"
}

# 세션 종료
kill_session() {
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        tmux kill-session -t "$SESSION_NAME"
        echo "Session '$SESSION_NAME' killed."
    else
        echo "Session '$SESSION_NAME' does not exist."
    fi
}

# 세션 접속
attach_session() {
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        tmux attach-session -t "$SESSION_NAME"
    else
        echo "Session '$SESSION_NAME' does not exist."
        exit 1
    fi
}

# 데이터 수집 실행
run_collector() {
    local args="$1"

    # 기존 세션이 있으면 종료
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "Killing existing session '$SESSION_NAME'..."
        tmux kill-session -t "$SESSION_NAME"
    fi

    # 새 세션 생성 및 명령 실행
    echo "Creating tmux session '$SESSION_NAME'..."
    tmux new-session -d -s "$SESSION_NAME" -c "$SRC_DIR"
    tmux send-keys -t "$SESSION_NAME" "cd $SRC_DIR && uv run python -m data_collector.run_ufc_stats_flow $args" C-m

    echo "Started in tmux session '$SESSION_NAME'"
    echo "Use '$0 -s' or 'tmux attach -t $SESSION_NAME' to attach"
}

# 인자 파싱
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    -h|--help)
        show_help
        ;;
    -k|--kill)
        kill_session
        ;;
    -s|--attach)
        attach_session
        ;;
    -l|--list)
        cd "$SRC_DIR" && uv run python -m data_collector.run_ufc_stats_flow --list
        ;;
    -a|--all)
        run_collector ""
        ;;
    -t|--tasks)
        shift
        if [ $# -eq 0 ]; then
            echo "Error: --tasks requires at least one task name"
            exit 1
        fi
        run_collector "-t $*"
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
