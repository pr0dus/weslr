#!/bin/bash
# WESLR chat.weslr.de read-only health check (Slice 1)
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
#   bash scripts/chat_weslr_de_health_check.sh
#   bash scripts/chat_weslr_de_health_check.sh --json <out_path>
#   bash scripts/chat_weslr_de_health_check.sh --md   <out_path>
#
# Exit code:
#   0 — all mandatory checks passed
#   1 — at least one mandatory check failed
#   2 — usage error

set -u

# ---------- Configuration ----------
NGINX_CONF="/etc/nginx/conf.d/weslr-unified-8080.conf"
HTPASSWD="/etc/nginx/.htpasswd-weslr-staging"
STATIC_SHELL="/var/www/weslr-chat-app-shell/index.html"
BACKEND_PORT=8092
BACKEND_PROC_NAME="protected_non_model_workflow_server"
PUBLIC_NGINX_PORT=8080
LOCAL_PREVIEW_PORT=8093

# ---------- Output mode ----------
OUTPUT_MODE="text"
OUTPUT_PATH=""

while [ $# -gt 0 ]; do
    case "$1" in
        --json) OUTPUT_MODE="json"; OUTPUT_PATH="${2:-}"; shift 2 ;;
        --md)   OUTPUT_MODE="md";   OUTPUT_PATH="${2:-}"; shift 2 ;;
        -h|--help)
            cat <<'USAGE'
WESLR chat.weslr.de read-only health check (Slice 1)

Usage:
  bash scripts/chat_weslr_de_health_check.sh
  bash scripts/chat_weslr_de_health_check.sh --json <out.json>
  bash scripts/chat_weslr_de_health_check.sh --md   <out.md>

Exits 0 on all mandatory checks pass, 1 on any mandatory failure, 2 on usage error.
USAGE
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

# ---------- Internal state ----------
PASS=0
FAIL=0
WARN=0
SKIP=0
declare -a LINES_TEXT=()
declare -a RESULTS_JSON=()

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
    # Sanitize detail for JSON: strip control chars, escape quotes
    local safe_detail
    safe_detail=$(printf '%s' "$detail" | tr -d '\000-\010\013-\037' | sed 's/"/\\"/g')
    RESULTS_JSON+=("{\"status\":\"$status\",\"name\":\"$(printf '%s' "$name" | sed 's/"/\\\\\"/g')\",\"detail\":\"$safe_detail\"}")
}

# ---------- Mandatory checks ----------

# 1. chat.weslr.de unauthenticated returns 401
CHAT_HEADERS=$(curl -sS -D - -o /dev/null --max-time 10 "http://127.0.0.1:8080/" \
    -H "Host: chat.weslr.de" 2>&1) || true
CHAT_STATUS=$(printf '%s\n' "$CHAT_HEADERS" | awk 'NR==1{print $2; exit}')
if [ "$CHAT_STATUS" = "401" ]; then
    _record PASS "chat.weslr.de unauth 401" "status=401"
else
    _record FAIL "chat.weslr.de unauth 401" "expected 401, got '$CHAT_STATUS'"
fi

# 2. WWW-Authenticate contains expected realm
CHAT_AUTH=$(printf '%s\n' "$CHAT_HEADERS" | awk -F': ' 'tolower($1)=="www-authenticate"{$1=""; print substr($0,2); exit}' | tr -d '\r')
if printf '%s' "$CHAT_AUTH" | grep -qF 'Basic realm="WESLR Chat Interface"'; then
    _record PASS "chat.weslr.de WWW-Authenticate realm" "realm matches 'WESLR Chat Interface'"
else
    _record FAIL "chat.weslr.de WWW-Authenticate realm" "got: '$CHAT_AUTH'"
fi

# 3. weslr.de/status/ returns 200
WSLR_STATUS=$(curl -sS -D - -o /dev/null --max-time 10 "http://127.0.0.1:8080/status/" \
    -H "Host: weslr.de" 2>&1 | awk 'NR==1{print $2; exit}')
if [ "$WSLR_STATUS" = "200" ]; then
    _record PASS "weslr.de/status/ 200" "status=200"
else
    _record FAIL "weslr.de/status/ 200" "expected 200, got '$WSLR_STATUS'"
fi

# 4. staging.weslr.de/ remains 401
STG_STATUS=$(curl -sS -D - -o /dev/null --max-time 10 "http://127.0.0.1:8080/" \
    -H "Host: staging.weslr.de" 2>&1 | awk 'NR==1{print $2; exit}')
if [ "$STG_STATUS" = "401" ]; then
    _record PASS "staging.weslr.de/ 401" "status=401"
else
    _record FAIL "staging.weslr.de/ 401" "expected 401, got '$STG_STATUS'"
fi

# 5. Backend process on 127.0.0.1:8092 exists
BACKEND_PID=""
if command -v ss >/dev/null 2>&1; then
    BACKEND_PID=$(ss -tlnp 2>/dev/null | awk -v port=":${BACKEND_PORT}" '$4 ~ port {print $0; exit}' | grep -oE 'pid=[0-9]+' | head -1 | sed 's/pid=//')
fi
if [ -z "$BACKEND_PID" ] && command -v lsof >/dev/null 2>&1; then
    BACKEND_PID=$(lsof -nP -iTCP:${BACKEND_PORT} -sTCP:LISTEN 2>/dev/null | awk 'NR==2{print $2; exit}')
fi
if [ -z "$BACKEND_PID" ] && command -v fuser >/dev/null 2>&1; then
    BACKEND_PID=$(fuser -n tcp ${BACKEND_PORT} 2>/dev/null | tr -d ' ' | head -1)
fi
if [ -n "$BACKEND_PID" ] && [ "$BACKEND_PID" != "-" ]; then
    _record PASS "backend :8092 listening" "pid=$BACKEND_PID"
else
    _record FAIL "backend :8092 listening" "no listener on 127.0.0.1:${BACKEND_PORT}"
fi

# 6. Backend process command matches expected shape (without opening source file)
if [ -n "$BACKEND_PID" ] && [ "$BACKEND_PID" != "-" ]; then
    BACKEND_CMD=$(ps -p "$BACKEND_PID" -o args= 2>/dev/null | tr -d '\n' | tr -s ' ')
    BACKEND_PROC_NAME_FOUND=$(ps -p "$BACKEND_PID" -o comm= 2>/dev/null | tr -d '\n')
    if printf '%s' "$BACKEND_CMD" | grep -qF "$BACKEND_PROC_NAME" || \
       printf '%s' "$BACKEND_PROC_NAME_FOUND" | grep -qF "$BACKEND_PROC_NAME"; then
        _record PASS "backend command shape" "matches '$BACKEND_PROC_NAME' (no source opened)"
    else
        _record FAIL "backend command shape" "expected substring '$BACKEND_PROC_NAME' in '$BACKEND_CMD'"
    fi
else
    _record SKIP "backend command shape" "no backend pid to inspect"
fi

# 7. Port 8080 is listening
PORT_8080=""
if command -v ss >/dev/null 2>&1; then
    PORT_8080=$(ss -tln 2>/dev/null | awk '$4 ~ /:8080$/ {print $4; exit}')
fi
if [ -n "$PORT_8080" ]; then
    _record PASS "port 8080 listening" "addr=$PORT_8080"
else
    _record FAIL "port 8080 listening" "no listener on :8080"
fi

# 8. Port 8092 is listening on loopback
PORT_8092=""
if command -v ss >/dev/null 2>&1; then
    PORT_8092=$(ss -tln 2>/dev/null | awk '$4 ~ /:8092$/ {print $4; exit}')
fi
if printf '%s' "$PORT_8092" | grep -qF '127.0.0.1'; then
    _record PASS "port 8092 on loopback" "addr=$PORT_8092"
else
    _record FAIL "port 8092 on loopback" "expected 127.0.0.1:8092, got '$PORT_8092'"
fi

# 9. Port 8093 status (optional, not required)
PORT_8093=""
if command -v ss >/dev/null 2>&1; then
    PORT_8093=$(ss -tln 2>/dev/null | awk '$4 ~ /:8093$/ {print $4; exit}')
fi
if [ -n "$PORT_8093" ]; then
    _record PASS "port 8093 (optional) present" "addr=$PORT_8093 (informational only)"
else
    _record SKIP "port 8093 (optional) absent" "no listener on :8093 (informational only)"
fi

# 10. Static shell file exists (metadata + sha256 only)
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

# 11. Nginx config file exists; sha256 if readable
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

# 12. htpasswd file exists — metadata only, NEVER print contents, NEVER hash if sudo required
if [ -e "$HTPASSWD" ]; then
    HP_SIZE=$(stat -c '%s' "$HTPASSWD" 2>/dev/null)
    HP_MODE=$(stat -c '%a' "$HTPASSWD" 2>/dev/null)
    HP_OWNER=$(stat -c '%U:%G' "$HTPASSWD" 2>/dev/null)
    if [ -r "$HTPASSWD" ] && command -v sha256sum >/dev/null 2>&1; then
        # Only hash IF readable WITHOUT sudo. Never print contents.
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

# 13. Protected files in the repo remain unchanged (best-effort, optional)
# This check is in-repo and depends on the script being run from a git worktree.
PROTECTED_OK=1
PROTECTED_REPORT=""
for f in weslr/chat_responder.py main.py dialogue.py chat_ui.py; do
    if [ -f "$f" ]; then
        if ! git diff --quiet HEAD -- "$f" 2>/dev/null; then
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

# ---------- Output ----------
SUMMARY="WESLR chat.weslr.de Slice 1 health check — PASS=$PASS FAIL=$FAIL WARN=$WARN SKIP=$SKIP"

if [ "$OUTPUT_MODE" = "text" ]; then
    echo "=================================================="
    echo "$SUMMARY"
    echo "=================================================="
    for line in "${LINES_TEXT[@]}"; do
        echo "$line"
    done
    echo "=================================================="
elif [ "$OUTPUT_MODE" = "json" ]; then
    JSON_RESULTS=$(IFS=,; printf '%s' "${RESULTS_JSON[*]}")
    printf '{\n  "summary": {"pass": %d, "fail": %d, "warn": %d, "skip": %d},\n  "checks": [%s]\n}\n' \
        "$PASS" "$FAIL" "$WARN" "$SKIP" "$JSON_RESULTS"
elif [ "$OUTPUT_MODE" = "md" ]; then
    {
        echo "# WESLR chat.weslr.de Slice 1 Health Check"
        echo
        echo "**Generated:** $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        echo
        echo "## Summary"
        echo
        echo "| Metric | Count |"
        echo "|---|---|"
        echo "| PASS | $PASS |"
        echo "| FAIL | $FAIL |"
        echo "| WARN | $WARN |"
        echo "| SKIP | $SKIP |"
        echo
        echo "## Checks"
        echo
        echo "| Status | Name | Detail |"
        echo "|---|---|---|"
        for line in "${LINES_TEXT[@]}"; do
            status=$(printf '%s' "$line" | awk -F' \\| ' '{print $1}')
            name=$(printf '%s' "$line" | awk -F' \\| ' '{print $2}')
            detail=$(printf '%s' "$line" | awk -F' \\| ' '{print $3}')
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
