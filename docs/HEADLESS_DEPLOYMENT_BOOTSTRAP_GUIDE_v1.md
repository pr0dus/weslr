# Headless Deployment Bootstrap Guide v1

> Canonical CLI bootstrap flow for WESLR on server, Pi, and SSH-only environments. No browser required.

---

## Prerequisites

- WESLR canonical runtime installed
- Python 3.10+
- Network access for the runtime process (or a configured offline model)

---

## 1. Start the Canonical Runtime

```bash
cd "$WESLR_WORKSPACE_DIR"
python3 main.py serve --host 0.0.0.0 --port 8000
```

The runtime starts with all HTTP endpoints available. No operator profile or bootstrap is required to start — but certain endpoints will report `blocked: true` until initialization completes.

---

## 2. Check Initial State

```bash
# Returns whether this is a first-run installation
curl http://localhost:8000/api/first-run

# Returns operator profile status
curl http://localhost:8000/api/onboarding

# Returns full runtime state summary
curl http://localhost:8000/api/state

# Lightweight health check (no auth required)
curl http://localhost:8000/api/health
```

Expected initial states:

| Endpoint | Before init | After full init |
|---|---|---|
| `/api/first-run` | `{"first_run": true, ...}` | `{"first_run": false, ...}` |
| `/api/onboarding` | `{"phase": null}` | `{"phase": "onboarding", "name": "..."}` |
| `/api/health` | Always 200 | Same |
| `/api/state/trust_posture` | No `bootstrap_timeline_id` | `bootstrap_status: COMPLETED` |

---

## 3. Initialize Operator Profile — `init-operator`

Creates the operator profile in the same canonical format as the browser onboarding flow. Written to `operator_profile.json`.

```bash
python3 main.py init-operator \
  --name "Your Name" \
  --role "SRE" \
  --urgency high \
  --checkin-style daily \
  --adaptation-level propose
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--name` | Yes | Operator display name |
| `--role` | No | Role or title |
| `--urgency` | No | `low`, `normal` (default), `high`, `critical` |
| `--checkin-style` | No | `silent`, `hourly`, `daily` (default), `verbose` |
| `--adaptation-level` | No | `none`, `propose` (default), `low-risk`, `full` |

### JSON output (for scripts)

```bash
python3 main.py init-operator --name "Alice" --role "DevOps" --json
```

```json
{
  "success": true,
  "operator_name": "Alice",
  "role": "DevOps",
  "profile_path": "$WESLR_WORKSPACE_DIR/operator_profile.json"
}
```

---

## 4. Complete Bootstrap Trust — `init-bootstrap`

Creates the durable bootstrap truth anchor. Writes `timeline_id` to `communicator_self.json["bootstrap"]` and registers the timeline in the in-process bootstrap store so `is_verified_timeline()` returns `True`.

```bash
python3 main.py init-bootstrap --user-id alice
```

```bash
python3 main.py init-bootstrap --user-id alice --json
```

```json
{
  "success": true,
  "user_id": "alice",
  "timeline_id": "tl_alice_ZLTFlWkGaq4CGObr1S1RTQ",
  "bootstrap_status": "COMPLETED"
}
```

The `--user-id` is the stable human identifier used to derive the `timeline_id`. It defaults to `"operator"` if not provided.

---

## 5. Configure LLM Provider — `init-provider`

Sets the active LLM provider and persists the configuration to `provider_config.json`. Survives restarts — no env var management required after initial setup.

Supported providers: `fallback`, `ollama`, `openai`, `openai_compatible`.

### Fallback (no external dependency — always available)

```bash
python3 main.py init-provider --provider fallback --json
```

```json
{
  "success": true,
  "provider": "fallback",
  "configured": true,
  "validated": true,
  "validation_detail": "Fallback is always available; no external dependency"
}
```

### Ollama (local daemon)

```bash
python3 main.py init-provider \
  --provider ollama \
  --ollama-host http://127.0.0.1:11434 \
  --json
```

```json
{
  "success": true,
  "provider": "ollama",
  "configured": true,
  "validated": true,
  "validation_detail": "Ollama daemon reachable at http://127.0.0.1:11434"
}
```

### OpenAI / OpenAI-Compatible (cloud)

```bash
# API key must be set in the environment before running init-provider
export OPENAI_API_KEY="sk-..."

python3 main.py init-provider \
  --provider openai \
  --openai-base-url https://api.openai.com/v1 \
  --openai-api-key-env OPENAI_API_KEY \
  --model gpt-4o-mini \
  --json
```

> **No secrets written to disk.** `provider_config.json` records the env var *name* (`OPENAI_API_KEY`), never the key value itself. Set the env var in your shell profile or systemd unit before starting the runtime.

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--provider` | Yes | One of: `fallback`, `ollama`, `openai`, `openai_compatible` |
| `--ollama-host` | No | Ollama host URL (default: `http://127.0.0.1:11434`) |
| `--openai-base-url` | No | OpenAI-compatible base URL |
| `--openai-api-key-env` | No | Env var name holding the API key (e.g. `OPENAI_API_KEY`) |
| `--model` | No | Model name; leave empty for provider default |
| `--json` | No | Machine-readable output |

---

## 6. Verify Initialization — `/api/initialize`

After both CLI commands, `POST /api/initialize` should succeed:

```bash
curl -X POST http://localhost:8000/api/initialize
```

Expected response:

```json
{
  "initialized": true,
  "created_now": false,
  "blocked": false,
  "reasons": []
}
```

`blocked: false` confirms all initialization gates passed:
- Operator profile exists with a name
- Lifecycle state is not `bootstrap_required`
- `get_weslr_state_summary()` returns without error
- `timeline_id` exists in `communicator_self.json["bootstrap"]`

---

## 7. Post-Setup Verification

After all three init commands, verify the runtime is fully operational:

```bash
# Health check — lightweight, no auth
curl http://localhost:8000/api/health

# Full state — confirms bootstrap and operator profile are loaded
curl http://localhost:8000/api/state

# Initialize gate — confirms all required state is present
curl -X POST http://localhost:8000/api/initialize
```

Expected: `health` → 200, `initialize` → `{"initialized": true, "blocked": false, "reasons": []}`

---

## 8. Full Endpoint Reference

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/health` | GET | None | Lightweight health check |
| `/api/first-run` | GET | None | First-run detection |
| `/api/onboarding` | GET | None | Onboarding state |
| `/api/state` | GET | None | Full runtime state summary |
| `/api/initialize` | POST | None | Initialize the runtime (gated) |
| `/chat` | POST | None | Chat interface (template or LLM) |
| `/operator` | GET | None | Operator dashboard |

---

## 9. Fresh Deployment Script — Linux Server

```bash
#!/bin/bash
# weslr-headless-setup.sh — fresh WESLR deployment on Linux server
# Usage: bash weslr-headless-setup.sh [operator-name] [operator-role] [provider]
#
# Examples:
#   bash weslr-headless-setup.sh "Alice" "SRE" ollama
#   OPENAI_API_KEY=sk-... bash weslr-headless-setup.sh "Bob" "DevOps" openai
#
# Provider defaults to "fallback" if not specified.

set -e

HOST="${WESLR_HOST:-0.0.0.0}"
PORT="${WESLR_PORT:-8000}"
OPERATOR_NAME="${1:-}"
OPERATOR_ROLE="${2:-}"
PROVIDER="${3:-fallback}"

if [ -z "$OPERATOR_NAME" ]; then
  echo "Usage: bash weslr-headless-setup.sh <operator-name> [operator-role] [provider]"
  echo "  provider: fallback (default), ollama, openai, openai_compatible"
  exit 1
fi

WORKSPACE_DIR="${WESLR_WORKSPACE_DIR:-$HOME/weslr-workspace}"
cd "$WORKSPACE_DIR"

echo "=== Starting WESLR canonical runtime ==="
python3 main.py serve --host "$HOST" --port "$PORT" &
RUNTIME_PID=$!
echo "Runtime started (PID $RUNTIME_PID)"

echo "=== Waiting for runtime to become ready ==="
sleep 3

# Poll health endpoint until ready
for i in $(seq 1 15); do
  if curl -sf "http://localhost:$PORT/api/health" > /dev/null 2>&1; then
    echo "Runtime is healthy."
    break
  fi
  if [ $i -eq 15 ]; then
    echo "ERROR: Runtime failed to become healthy."
    kill $RUNTIME_PID 2>/dev/null || true
    exit 1
  fi
  sleep 1
done

# Step 1: Create operator profile
echo "=== Creating operator profile ==="
python3 main.py init-operator \
  --name "$OPERATOR_NAME" \
  --role "$OPERATOR_ROLE" \
  --urgency normal \
  --checkin-style daily \
  --adaptation-level propose \
  --json | tee /tmp/weslr_operator.json

# Step 2: Complete bootstrap trust anchor
echo "=== Completing bootstrap trust anchor ==="
USER_ID=$(echo "$OPERATOR_NAME" | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]')
python3 main.py init-bootstrap \
  --user-id "${USER_ID:-operator}" \
  --json | tee /tmp/weslr_bootstrap.json

# Step 3: Configure LLM provider
echo "=== Configuring LLM provider: $PROVIDER ==="
if [ "$PROVIDER" = "ollama" ]; then
  python3 main.py init-provider \
    --provider ollama \
    --ollama-host http://127.0.0.1:11434 \
    --json | tee /tmp/weslr_provider.json
elif [ "$PROVIDER" = "openai" ] || [ "$PROVIDER" = "openai_compatible" ]; then
  python3 main.py init-provider \
    --provider "$PROVIDER" \
    --openai-base-url https://api.openai.com/v1 \
    --model gpt-4o-mini \
    --json | tee /tmp/weslr_provider.json
else
  python3 main.py init-provider \
    --provider fallback \
    --json | tee /tmp/weslr_provider.json
fi

# Step 4: Verify initialization
echo "=== Verifying initialization ==="
INIT_RESULT=$(curl -sf -X POST "http://localhost:$PORT/api/initialize")
echo "$INIT_RESULT" | python3 -m json.tool

BLOCKED=$(echo "$INIT_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('blocked', True))")
if [ "$BLOCKED" = "True" ]; then
  echo "WARNING: Runtime initialization is blocked. Check reasons above."
else
  echo ""
  echo "=== WESLR initialized successfully ==="
  echo "Runtime:  http://localhost:$PORT"
  echo "Health:   http://localhost:$PORT/api/health"
  echo "Operator: http://localhost:$PORT/operator"
  echo "Provider: $PROVIDER"
fi

echo ""
echo "Runtime is running in background (PID $RUNTIME_PID)."
echo "To stop:  kill $RUNTIME_PID"
```

### Run it:

```bash
# Local Ollama setup
bash weslr-headless-setup.sh "Alice" "SRE" ollama

# Cloud OpenAI setup
OPENAI_API_KEY=sk-... bash weslr-headless-setup.sh "Bob" "DevOps" openai

# Fallback only (no external provider)
bash weslr-headless-setup.sh "Carol" "Analyst" fallback
```

Expected final output:

```
=== Configuring LLM provider: ollama ===
{"success": true, "provider": "ollama", "configured": true, "validated": true, ...}
=== Verifying initialization ===
{
  "initialized": true,
  "created_now": false,
  "blocked": false,
  "reasons": []
}
=== WESLR initialized successfully ===
Runtime:  http://localhost:8000
Health:   http://localhost:8000/api/health
Operator: http://localhost:8000/operator
Provider: ollama


## Troubleshooting

**`/api/initialize` returns `blocked: true`**

Check the `reasons` array:
- `operator_profile_name_missing` — run `init-operator` first
- `lifecycle_not_onboarded` — operator profile exists but lifecycle state is wrong (rare in headless flow)
- `no_bootstrap_timeline` — run `init-bootstrap` after `init-operator`
- `bootstrap_check_failed` — the bootstrap record exists but couldn't be read from `communicator_self.json`

**Runtime starts but `/chat` returns 500**

Check whether an LLM provider is configured. If no provider is available, `/chat` uses template-based responses. A raw 500 after initialization typically means the `load_communicator_self` local import scope bug — update to the latest canonical runtime.

**`init-bootstrap` succeeds but `is_verified_timeline()` returns `False`**

The in-process bootstrap store is not persisted across restarts. For durable bootstrap truth across restarts, the `communicator_self.json["bootstrap"]["timeline_id"]` path is the source of truth. The in-process store is repopulated on next `init-bootstrap` call.
