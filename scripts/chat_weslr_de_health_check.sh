#!/bin/bash
# WESLR chat.weslr.de read-only health check (Slice 1)
#
# Host-role aware:
# - runtime-host mode: strict checks for the live chat.weslr.de host
# - source-repo mode: metadata/repo checks only; local nginx/backend/static
#   shell checks are skipped instead of failing on the OCC/Termux source repo
# - auto mode: runtime-host if strong runtime markers are present, otherwise
#   source-repo
#
# This script performs a strictly read-only inventory of the
# chat.weslr.de customer-grade wiring state.
#
# It does NOT:
#   - edit any file
#   - reload nginx
#   - restart any backend
#   - touch htpasswd contents (metadata only, never printed)
#   - open raw sessions, hidden prompts, or secrets
#   - claim AGI / sentience / benchmark / production / live runtime
#
# Usage:
#   bash scripts/chat_weslr_de_health_check.sh [--mode auto|runtime-host|source-repo]
#   bash scripts/chat_weslr_de_health_check.sh --json <out_path>
#   bash scripts/chat_weslr_de_health_check.sh --md   <out_path>
#
# Exit code:
#   0 — all mandatory checks passed
#   1 — at least one mandatory check failed
#   2 — usage error

set -u

SCRIPT_PATH=${0}
REPO_ROOT=$(git -C "$(dirname "$SCRIPT_PATH")" rev-parse --show-toplevel 2>/dev/null || git rev-parse --show-toplevel 2>/dev/null || pwd)

# ---------- Configuration ----------
NGINX_CONF="/etc/nginx/conf.d/weslr-unified-8080.conf"
HTPASSWD="/etc/nginx/.htpasswd-weslr-staging"
STATIC_SHELL="/var/www/weslr-chat-app-shell/index.html"
BACKEND_PORT=8092
BACKEND_PROC_NAME="protected_non_model_workflow_server"
PUBLIC_NGINX_PORT=8080
LOCAL_PREVIEW_PORT=8093
PLAN_DOC="docs/WESLR_CHAT_WESLR_DE_CUSTOMER_GRADE_WIRING_PLAN_V1.md"
REVIEW_DOC="docs/WESLR_CHAT_WESLR_DE_CUSTOMER_GRADE_WIRING_PLAN_REVIEW_V1.md"
RELEASE_GATE="weslr/tests/release_gate_v1.py"

# ---------- Output / mode parsing ----------
OUTPUT_MODE="text"
OUTPUT_PATH=""
MODE="auto"

while [ $# -gt 0 ]; do
    case "$1" in
        --mode)
            MODE="${2:-}"
            shift 2
            ;;
        --mode=*)
            MODE="${1#--mode=}"
            shift
            ;;
        --json)
            OUTPUT_MODE="json"
            OUTPUT_PATH="${2:-}"
            shift 2
            ;;
        --md)
            OUTPUT_MODE="md"
            OUTPUT_PATH="${2:-}"
            shift 2
            ;;
        -h|--help)
            cat <<'USAGE'
WESLR chat.weslr.de read-only health check (Slice 1)

Usage:
  bash scripts/chat_weslr_de_health_check.sh [--mode auto|runtime-host|source-repo]
  bash scripts/chat_weslr_de_health_check.sh --json <out.json>
  bash scripts/chat_weslr_de_health_check.sh --md   <out.md>

Modes:
  auto          runtime-host if strong runtime markers are present, otherwise source-repo
  runtime-host  strict live-host checks; local infra must exist
  source-repo   repo/metadata checks only; local infra checks are skipped
USAGE
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

case "$MODE" in
    auto|runtime-host|source-repo) ;;
    *)
        echo "Unknown mode: $MODE" >&2
        exit 2
        ;;
esac

if [ "$OUTPUT_MODE" = "json" ] || [ "$OUTPUT_MODE" = "md" ]; then
    if [ -z "$OUTPUT_PATH" ]; then
        echo "Missing output path for --$OUTPUT_MODE" >&2
        exit 2
    fi
fi

# ---------- Internal state ----------
PASS=0
FAIL=0
WARN=0
SKIP=0
declare -a LINES_TEXT=()
declare -a RESULTS_JSON=()
declare -a MANDATORY_LINES=()
declare -a SKIPPED_LINES=()

_record() {
    # _record <STATUS> <NAME> <DETAIL>
    local status="$1" name="$2" detail="$3"
    case "$status" in
        PASS) PASS=$((PASS+1)) ;;
        FAIL) FAIL=$((FAIL+1)) ;;
        WARN) WARN=$((WARN+1)) ;;
        SKIP) SKIP=$((SKIP+1)) ;;
    esac
    LINES_TEXT+=("$status | $name | $detail")
    local safe_detail safe_name
    safe_detail=$(printf '%s' "$detail" | tr -d '\000-\010\013-\037' | sed 's/"/\\"/g')
    safe_name=$(printf '%s' "$name" | sed 's/"/\\"/g')
    RESULTS_JSON+=("{\"status\":\"$status\",\"name\":\"$safe_name\",\"detail\":\"$safe_detail\"}")
}

_note_mandatory() {
    MANDATORY_LINES+=("$1")
}

_note_skipped() {
    SKIPPED_LINES+=("$1")
}

has_listener_8092() {
    local p=""
    if command -v ss >/dev/null 2>&1; then
        p=$(ss -tlnp 2>/dev/null | awk -v port=":${BACKEND_PORT}" '$4 ~ port {print $0; exit}' | grep -oE 'pid=[0-9]+' | head -1 | sed 's/pid=//')
    fi
    if [ -z "$p" ] && command -v lsof >/dev/null 2>&1; then
        p=$(lsof -nP -iTCP:${BACKEND_PORT} -sTCP:LISTEN 2>/dev/null | awk 'NR==2{print $2; exit}')
    fi
    if [ -z "$p" ] && command -v fuser >/dev/null 2>&1; then
        p=$(fuser -n tcp ${BACKEND_PORT} 2>/dev/null | tr -d ' ' | head -1)
    fi
    if [ -n "$p" ] && [ "$p" != "-" ]; then
        printf '%s' "$p"
        return 0
    fi
    return 1
}

get_port_8080() {
    if command -v ss >/dev/null 2>&1; then
        ss -tln 2>/dev/null | awk '$4 ~ /:8080$/ {print $4; exit}'
    fi
}

get_port_8092() {
    if command -v ss >/dev/null 2>&1; then
        ss -tln 2>/dev/null | awk '$4 ~ /:8092$/ {print $4; exit}'
    fi
}

runtime_marker_count=0
[ -f "$NGINX_CONF" ] && runtime_marker_count=$((runtime_marker_count+1))
[ -f "$STATIC_SHELL" ] && runtime_marker_count=$((runtime_marker_count+1))
if has_listener_8092 >/dev/null 2>&1; then
    runtime_marker_count=$((runtime_marker_count+1))
fi

if [ "$MODE" = "auto" ]; then
    if [ "$runtime_marker_count" -ge 1 ]; then
        MODE="runtime-host"
    else
        MODE="source-repo"
    fi
fi

if [ "$MODE" = "runtime-host" ]; then
    _note_mandatory "runtime-host mandatory checks: chat.weslr.de 401 + realm, weslr.de/status/ 200, staging.weslr.de 401, backend 127.0.0.1:8092 listener + command shape, port 8080, port 8092 loopback, static shell, nginx config, htpasswd metadata, protected files unchanged"
else
    _note_mandatory "source-repo mandatory checks: repo branch/HEAD, plan + review docs, script executable, release-gate path recognition, git diff --check, protected files unchanged"
    _note_skipped "source-repo skips local runtime checks: chat.weslr.de, weslr.de/status/, staging.weslr.de, backend 8092, port 8080, port 8092 loopback, optional 8093, static shell, nginx config, htpasswd metadata"
fi

# ---------- Source / repo checks ----------
REPO_BRANCH=$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null || true)
REPO_HEAD=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)
if [ -n "$REPO_BRANCH" ] && [ -n "$REPO_HEAD" ]; then
    _record PASS "repo branch/HEAD" "branch=$REPO_BRANCH head=$REPO_HEAD root=$REPO_ROOT"
else
    _record FAIL "repo branch/HEAD" "unable to read branch/head for root=$REPO_ROOT"
fi

if [ "$MODE" = "source-repo" ]; then
    if [ -f "$REPO_ROOT/$PLAN_DOC" ]; then
        _record PASS "plan doc exists" "path=$PLAN_DOC"
    else
        _record FAIL "plan doc exists" "path $PLAN_DOC not found"
    fi

    if [ -f "$REPO_ROOT/$REVIEW_DOC" ]; then
        _record PASS "review doc exists" "path=$REVIEW_DOC"
    else
        _record FAIL "review doc exists" "path $REVIEW_DOC not found"
    fi

    if [ -x "$REPO_ROOT/$SCRIPT_PATH" ] || [ -x "$SCRIPT_PATH" ]; then
        _record PASS "script executable" "path=$SCRIPT_PATH mode=executable"
    else
        _record FAIL "script executable" "path=$SCRIPT_PATH is not executable"
    fi

    if grep -qF 'scripts/chat_weslr_de_health_check.sh' "$REPO_ROOT/$RELEASE_GATE" 2>/dev/null; then
        _record PASS "release gate recognizes script path" "exact path allowance present in $RELEASE_GATE"
    else
        _record FAIL "release gate recognizes script path" "exact path allowance missing for scripts/chat_weslr_de_health_check.sh"
    fi

    if git -C "$REPO_ROOT" diff --check >/dev/null 2>&1; then
        _record PASS "git diff --check" "clean"
    else
        _record FAIL "git diff --check" "diff-check reported whitespace or patch issues"
    fi
fi

# ---------- Runtime-host checks ----------
if [ "$MODE" = "runtime-host" ]; then
    CHAT_HEADERS=$(curl -sS -D - -o /dev/null --max-time 10 "http://127.0.0.1:${PUBLIC_NGINX_PORT}/" \
        -H "Host: chat.weslr.de" 2>&1) || true
    CHAT_STATUS=$(printf '%s\n' "$CHAT_HEADERS" | awk 'NR==1{print $2; exit}')
    if [ "$CHAT_STATUS" = "401" ]; then
        _record PASS "chat.weslr.de unauth 401" "status=401"
    else
        _record FAIL "chat.weslr.de unauth 401" "expected 401, got '${CHAT_STATUS:-}'"
    fi

    CHAT_AUTH=$(printf '%s\n' "$CHAT_HEADERS" | awk -F': ' 'tolower($1)=="www-authenticate"{$1=""; print substr($0,2); exit}' | tr -d '\r')
    if printf '%s' "$CHAT_AUTH" | grep -qF 'Basic realm="WESLR Chat Interface"'; then
        _record PASS "chat.weslr.de WWW-Authenticate realm" "realm matches 'WESLR Chat Interface'"
    else
        _record FAIL "chat.weslr.de WWW-Authenticate realm" "got: '${CHAT_AUTH:-}'"
    fi

    WSLR_STATUS=$(curl -sS -D - -o /dev/null --max-time 10 "http://127.0.0.1:${PUBLIC_NGINX_PORT}/status/" \
        -H "Host: weslr.de" 2>&1 | awk 'NR==1{print $2; exit}')
    if [ "$WSLR_STATUS" = "200" ]; then
        _record PASS "weslr.de/status/ 200" "status=200"
    else
        _record FAIL "weslr.de/status/ 200" "expected 200, got '${WSLR_STATUS:-}'"
    fi

    STG_STATUS=$(curl -sS -D - -o /dev/null --max-time 10 "http://127.0.0.1:${PUBLIC_NGINX_PORT}/" \
        -H "Host: staging.weslr.de" 2>&1 | awk 'NR==1{print $2; exit}')
    if [ "$STG_STATUS" = "401" ]; then
        _record PASS "staging.weslr.de/ 401" "status=401"
    else
        _record FAIL "staging.weslr.de/ 401" "expected 401, got '${STG_STATUS:-}'"
    fi

    BACKEND_PID=""
    if BACKEND_PID=$(has_listener_8092); then
        _record PASS "backend :8092 listening" "pid=$BACKEND_PID"
    else
        _record FAIL "backend :8092 listening" "no listener on 127.0.0.1:${BACKEND_PORT}"
    fi

    if [ -n "${BACKEND_PID:-}" ] && [ "$BACKEND_PID" != "-" ]; then
        BACKEND_CMD=$(ps -p "$BACKEND_PID" -o args= 2>/dev/null | tr -d '\n' | tr -s ' ')
        BACKEND_PROC_NAME_FOUND=$(ps -p "$BACKEND_PID" -o comm= 2>/dev/null | tr -d '\n')
        if printf '%s' "$BACKEND_CMD" | grep -qF "$BACKEND_PROC_NAME" || \
           printf '%s' "$BACKEND_PROC_NAME_FOUND" | grep -qF "$BACKEND_PROC_NAME"; then
            _record PASS "backend command shape" "matches '$BACKEND_PROC_NAME' (no source opened)"
        else
            _record FAIL "backend command shape" "expected substring '$BACKEND_PROC_NAME' in '$BACKEND_CMD'"
        fi
    else
        _record FAIL "backend command shape" "no backend pid to inspect"
    fi

    PORT_8080=$(get_port_8080 || true)
    if [ -n "$PORT_8080" ]; then
        _record PASS "port 8080 listening" "addr=$PORT_8080"
    else
        _record FAIL "port 8080 listening" "no listener on :8080"
    fi

    PORT_8092=$(get_port_8092 || true)
    if printf '%s' "$PORT_8092" | grep -qF '127.0.0.1'; then
        _record PASS "port 8092 on loopback" "addr=$PORT_8092"
    else
        _record FAIL "port 8092 on loopback" "expected 127.0.0.1:8092, got '${PORT_8092:-}'"
    fi

    PORT_8093=""
    if command -v ss >/dev/null 2>&1; then
        PORT_8093=$(ss -tln 2>/dev/null | awk '$4 ~ /:8093$/ {print $4; exit}')
    fi
    if [ -n "$PORT_8093" ]; then
        _record PASS "port 8093 (optional) present" "addr=$PORT_8093 (informational only)"
    else
        _record SKIP "port 8093 (optional) absent" "no listener on :8093 (informational only)"
    fi

    if [ -f "$STATIC_SHELL" ]; then
        SHELL_SIZE=$(stat -c '%s' "$STATIC_SHELL" 2>/dev/null)
        SHELL_MODE=$(stat -c '%a' "$STATIC_SHELL" 2>/dev/null)
        SHELL_OWNER=$(stat -c '%U:%G' "$STATIC_SHELL" 2>/dev/null)
        if command -v sha256sum >/dev/null 2>&1; then
            SHELL_SHA=$(sha256sum "$STATIC_SHELL" 2>/dev/null | awk '{print $1}')
        else
            SHELL_SHA="(sha256sum unavailable)"
        fi
        _record PASS "static shell exists" "path=$STATIC_SHELL size=${SHELL_SIZE} mode=${SHELL_MODE} owner=${SHELL_OWNER} sha256=${SHELL_SHA}"
    else
        _record FAIL "static shell exists" "path $STATIC_SHELL not found"
    fi

    if [ -f "$NGINX_CONF" ]; then
        NGX_SIZE=$(stat -c '%s' "$NGINX_CONF" 2>/dev/null)
        NGX_MODE=$(stat -c '%a' "$NGINX_CONF" 2>/dev/null)
        NGX_OWNER=$(stat -c '%U:%G' "$NGINX_CONF" 2>/dev/null)
        if [ -r "$NGINX_CONF" ] && command -v sha256sum >/dev/null 2>&1; then
            NGX_SHA=$(sha256sum "$NGINX_CONF" 2>/dev/null | awk '{print $1}')
            _record PASS "nginx config exists" "path=$NGINX_CONF size=${NGX_SIZE} mode=${NGX_MODE} owner=${NGX_OWNER} sha256=${NGX_SHA}"
        else
            _record WARN "nginx config exists (sha256 not readable)" "path=$NGINX_CONF size=${NGX_SIZE} mode=${NGX_MODE} owner=${NGX_OWNER} — sha256 skipped (file not readable as current user)"
        fi
    else
        _record FAIL "nginx config exists" "path $NGINX_CONF not found"
    fi

    if [ -e "$HTPASSWD" ]; then
        HP_SIZE=$(stat -c '%s' "$HTPASSWD" 2>/dev/null)
        HP_MODE=$(stat -c '%a' "$HTPASSWD" 2>/dev/null)
        HP_OWNER=$(stat -c '%U:%G' "$HTPASSWD" 2>/dev/null)
        if [ -r "$HTPASSWD" ] && command -v sha256sum >/dev/null 2>&1; then
            HP_SHA=$(sha256sum "$HTPASSWD" 2>/dev/null | awk '{print $1}')
            if [ -n "$HP_SHA" ]; then
                _record PASS "htpasswd metadata" "path=$HTPASSWD size=${HP_SIZE} mode=${HP_MODE} owner=${HP_OWNER} sha256=${HP_SHA} (contents never printed)"
            else
                _record WARN "htpasswd metadata (sha256 failed)" "path=$HTPASSWD size=${HP_SIZE} mode=${HP_MODE} owner=${HP_OWNER} — sha256 unavailable, contents never printed"
            fi
        else
            _record WARN "htpasswd metadata (not readable without sudo)" "path=$HTPASSWD size=${HP_SIZE} mode=${HP_MODE} owner=${HP_OWNER} — sha256 skipped (would require sudo); contents never printed"
        fi
    else
        _record FAIL "htpasswd exists" "path $HTPASSWD not found"
    fi

    PROTECTED_OK=1
    PROTECTED_REPORT=""
    for f in weslr/chat_responder.py main.py dialogue.py chat_ui.py; do
        if [ -f "$REPO_ROOT/$f" ]; then
            if ! git -C "$REPO_ROOT" diff --quiet HEAD -- "$f" 2>/dev/null; then
                PROTECTED_OK=0
                PROTECTED_REPORT="$PROTECTED_REPORT $f"
            fi
        fi
    done
    if [ "$PROTECTED_OK" = "1" ]; then
        _record PASS "protected files unchanged" "weslr/chat_responder.py main.py dialogue.py chat_ui.py (and weslr_main.py if present)"
    else
        _record FAIL "protected files unchanged" "modified:$PROTECTED_REPORT"
    fi
fi

# ---------- Optional runtime-host-aware public URL checks ----------
# In source-repo mode these are optional and remain WARN-on-failure instead of FAIL.
check_public_probe() {
    local label="$1" expected="$2" host="$3" path="$4" fail_status="$5"
    local headers status auth
    headers=$(curl -sS -D - -o /dev/null --max-time 10 "http://127.0.0.1:${PUBLIC_NGINX_PORT}${path}" -H "Host: ${host}" 2>&1) || true
    status=$(printf '%s\n' "$headers" | awk 'NR==1{print $2; exit}')
    auth=$(printf '%s\n' "$headers" | awk -F': ' 'tolower($1)=="www-authenticate"{$1=""; print substr($0,2); exit}' | tr -d '\r')
    if [ "$status" = "$expected" ] && [ "$expected" != "401" -o -n "$auth" ]; then
        _record PASS "$label" "status=$status"
        return 0
    fi
    if [ "$MODE" = "runtime-host" ] || [ "$fail_status" = "FAIL" ]; then
        _record FAIL "$label" "expected $expected, got '${status:-}'"
    else
        _record WARN "$label" "optional probe mismatch on non-runtime host: expected $expected, got '${status:-}'"
    fi
}

if [ "$MODE" = "source-repo" ]; then
    check_public_probe "chat.weslr.de unauth 401 (optional)" "401" "chat.weslr.de" "/" "WARN"
    check_public_probe "weslr.de/status/ 200 (optional)" "200" "weslr.de" "/status/" "WARN"
    check_public_probe "staging.weslr.de/ 401 (optional)" "401" "staging.weslr.de" "/" "WARN"
fi

# ---------- Summary metadata ----------
SUMMARY="WESLR chat.weslr.de Slice 1 health check — mode=$MODE PASS=$PASS FAIL=$FAIL WARN=$WARN SKIP=$SKIP"

if [ "$OUTPUT_MODE" = "text" ]; then
    echo "=================================================="
    echo "$SUMMARY"
    echo "=================================================="
    echo "Mode selected: $MODE"
    if [ "$MODE" = "runtime-host" ]; then
        echo "Mandatory checks in this mode: runtime-host live-host checks"
    else
        echo "Mandatory checks in this mode: repo branch/HEAD, plan/review docs, executable script, release-gate path, git diff --check, protected files unchanged"
    fi
    if [ "${#SKIPPED_LINES[@]}" -gt 0 ]; then
        echo "Skipped because current host is not the runtime host:"
        for line in "${SKIPPED_LINES[@]}"; do
            echo "- $line"
        done
    fi
    if [ "${#MANDATORY_LINES[@]}" -gt 0 ]; then
        echo "Mandatory scope:"
        for line in "${MANDATORY_LINES[@]}"; do
            echo "- $line"
        done
    fi
    for line in "${LINES_TEXT[@]}"; do
        echo "$line"
    done
    echo "=================================================="
elif [ "$OUTPUT_MODE" = "json" ]; then
    JSON_RESULTS=$(IFS=,; printf '%s' "${RESULTS_JSON[*]}")
    printf '{\n  "mode": "%s",\n  "summary": {"pass": %d, "fail": %d, "warn": %d, "skip": %d},\n  "mandatory": [%s],\n  "skipped": [%s],\n  "checks": [%s]\n}\n' \
        "$MODE" "$PASS" "$FAIL" "$WARN" "$SKIP" \
        "$(IFS=,; printf '"%s"' "${MANDATORY_LINES[*]}")" \
        "$(IFS=,; printf '"%s"' "${SKIPPED_LINES[*]}")" \
        "$JSON_RESULTS"
elif [ "$OUTPUT_MODE" = "md" ]; then
    {
        echo "# WESLR chat.weslr.de Slice 1 Health Check"
        echo
        echo "**Generated:** $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        echo ""
        echo "**Mode selected:** $MODE"
        echo ""
        echo "## Summary"
        echo ""
        echo "| Metric | Count |"
        echo "|---|---|"
        echo "| PASS | $PASS |"
        echo "| FAIL | $FAIL |"
        echo "| WARN | $WARN |"
        echo "| SKIP | $SKIP |"
        echo ""
        echo "## Mandatory checks in this mode"
        echo ""
        for line in "${MANDATORY_LINES[@]}"; do
            echo "- $line"
        done
        echo ""
        echo "## Skipped because current host is not the runtime host"
        echo ""
        for line in "${SKIPPED_LINES[@]}"; do
            echo "- $line"
        done
        echo ""
        echo "## Checks"
        echo ""
        echo "| Status | Name | Detail |"
        echo "|---|---|---|"
        for line in "${LINES_TEXT[@]}"; do
            status=$(printf '%s' "$line" | awk -F' \| ' '{print $1}')
            name=$(printf '%s' "$line" | awk -F' \| ' '{print $2}')
            detail=$(printf '%s' "$line" | awk -F' \| ' '{print $3}')
            echo "| $status | $name | $detail |"
        done
    } > "$OUTPUT_PATH"
    echo "Markdown snapshot written to: $OUTPUT_PATH"
    echo "$SUMMARY"
fi

# ---------- Exit code ----------
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
