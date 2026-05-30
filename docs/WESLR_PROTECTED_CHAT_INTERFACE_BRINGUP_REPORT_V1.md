# WESLR Protected Chat Interface Bring-Up Report V1

**Date:** 2026-05-30  
**Status:** protected_chat_not_ready_runtime_broken  
**Judgment:** Chat backend runs but has broken import — `handle_direct_message` missing from `dialogue.py`

---

## Executive Summary

| Item | Status |
|------|--------|
| Protected access (Basic Auth) | ✅ Working |
| Chat backend (`chat_ui.py`) | ⚠️ Runs but broken |
| Frontend (weslr-ui React) | ❌ Not built/deployed |
| Nginx routing | ⚠️ Configured but points to static site |
| Model/Provider | ✅ Ollama configured |
| Code path for responses | ❌ Broken import |

---

## Phase A: Preflight Discovery

### Repository State

| Item | Value |
|------|-------|
| Repo path | `/home/pr0/projects/weslr` |
| Branch | `scatti-audit-bundle-v2` |
| Git status | Dirty (scatti files) |
| Chat backend | `chat_ui.py` — standalone Python HTTP server |
| Frontend | `weslr-ui/` — React app (needs npm build) |

### Port Allocation

| Port | Service | Status |
|------|---------|--------|
| 8080 | nginx (Cloudflare tunnel) | Running |
| 8081 | chat_ui.py (chat backend) | Started then stopped (broken) |
| 8083 | plantdelux site | Running |
| 8085 | inbound-email handler | Running |
| 8089 | weslr-v1-ui-website (static) | Running |
| 8097 | e-qubs site | Running |

### Nginx Configuration

**File:** `/etc/nginx/conf.d/weslr-unified-8080.conf`

| Server Name | Auth | Proxy Target | Content |
|-------------|------|--------------|---------|
| weslr.de | None | 127.0.0.1:8089 | Static landing page |
| www.weslr.de | None | 301 redirect | Redirects to weslr.de |
| staging.weslr.de | Basic Auth | 127.0.0.1:8089 | Static landing page |
| chat.weslr.de | Basic Auth | 127.0.0.1:8089 | **Static landing page** |

**Critical Note:** `chat.weslr.de` currently proxies to port 8089 (static site), NOT the chat backend.

### Model/Provider Configuration

| Item | Value |
|------|-------|
| Provider config | `/home/pr0/projects/weslr/provider_config.json` |
| Active provider | `ollama` |
| Active model | `qwen3-coder-next:cloud` |
| Ollama host | `http://127.0.0.1:11434` |
| Ollama status | Running, models available |

### Dependencies

| Item | Status |
|------|--------|
| Python stdlib modules | ✅ Available |
| WESLR modules | ✅ Available |
| dialogue.py | ❌ Missing `handle_direct_message` function |
| weslr/providers.py | ✅ Available |
| Ollama API | ✅ Responding |

### Secrets/Env Files

| File | Contents |
|------|----------|
| `weslr.env` | Template only (no secrets) |
| No `.env` files found | — |

---

## Phase B: Start Existing Services

### Attempted: Start chat_ui.py

**Command:**
```bash
cd /home/pr0/projects/weslr && python3 chat_ui.py
```

**Result:** Started successfully on port 8081

**Test Request:**
```bash
curl -s -X POST http://127.0.0.1:8081/api/send -H "Content-Type: application/json" -d '{"message":"What is WESLR?"}'
```

**Response:**
```json
{
    "reply": "I'm Weslr. (Error: cannot import name 'handle_direct_message' from 'dialogue' (/home/pr0/projects/weslr/dialogue.py))",
    "status": "Message processed."
}
```

### Root Cause

**File:** `/home/pr0/projects/weslr/chat_ui.py`  
**Line 816-817:**
```python
from dialogue import handle_direct_message
canon_result = handle_direct_message(message)
```

**Issue:** `handle_direct_message` function does NOT exist in `dialogue.py`

**Verified:**
```bash
grep -n "def handle_direct_message" /home/pr0/projects/weslr/dialogue.py
# No matches found
```

### Alternative Paths Tested

| Command | Result |
|---------|--------|
| `entity list` command | EOF error (requires stdin) |
| `capability list` command | "No suggestions found" (but no error) |
| `entity stats` command | EOF error (requires stdin) |
| `speak` command | EOF error (requires stdin) |

### Backend Contract Status

**File:** `weslr_backend_contract.py`  
**Status:** Exists but not exposed as HTTP server  
**Issue:** Would need to be wrapped in a Flask/HTTP server

---

## Phase C: Protect and Route

### Current State

| Route | Auth | Actual Content |
|-------|------|----------------|
| weslr.de | None | ✅ Static marketing page |
| www.weslr.de | None | ✅ Redirect to weslr.de |
| staging.weslr.de | Basic Auth | ✅ Static marketing page |
| chat.weslr.de | Basic Auth | ⚠️ Static marketing page (NOT chat) |

### What Would Need to Change

1. **Fix broken import** — `handle_direct_message` missing from `dialogue.py`
2. **Build frontend** — `cd weslr-ui && npm install && npm run build`
3. **Start backend** — `chat_ui.py` on port 8081 (after fix)
4. **Update nginx** — Route `chat.weslr.de` to chat backend or serve frontend

**NOT DONE:** Per constraints, no new runtime implementation without owner approval.

---

## Phase D: Controlled Behavior Test

**Status:** NOT RUN — Chat backend broken

The following test prompts could NOT be executed:

| Prompt | Status |
|--------|--------|
| "What is WESLR?" | ❌ Backend returns import error |
| "Explain your current status..." | ❌ Backend returns import error |
| "Help me plan the next safe step..." | ❌ Backend returns import error |
| "If I ask you to upload a file..." | ❌ Backend returns import error |
| "What do you remember..." | ❌ Backend returns import error |

### Sample Error Response

```json
{
    "reply": "I'm Weslr. (Error: cannot import name 'handle_direct_message' from 'dialogue' (/home/pr0/projects/weslr/dialogue.py))",
    "meta": "{...}",
    "status": "Message processed."
}
```

---

## Code-Level Findings

### Files Examined

| File | Purpose | Issue |
|------|---------|-------|
| `chat_ui.py` | HTTP server + HTML chat UI | Calls missing `handle_direct_message` |
| `dialogue.py` | Dialogue processing | Missing `handle_direct_message` function |
| `commands/speak.py` | CLI speak command | Requires stdin (EOF error) |
| `weslr_backend_contract.py` | Backend API contract | Not exposed as HTTP server |
| `main.py` | Main CLI entry point | Working but requires TTY |
| `weslr_main.py` | Weslr CLI | Working but requires TTY |
| `weslr/providers.py` | LLM provider abstraction | Working |
| `provider_config.json` | Provider configuration | Working |

### Import Chain

```
chat_ui.py
  └── from dialogue import handle_direct_message  # ← MISSING
       └── dialogue.py
            └── (no handle_direct_message function)
```

### Available Functions in dialogue.py

- `_attach_lineage_inspection`
- `_compute_context_selection`
- `_compute_boundary_hints`
- `_attach_context_selection`
- `_build_contamination_metadata`
- `_resolve_active_artifact`
- `translate_theme`
- `translate_self_description`
- `generate_from_self_state`
- `synthesize_concept_or_self_reply`
- `synthesize_research_answer`
- ... (many more)

**Missing:** `handle_direct_message`

---

## Safety Assessment

| Check | Status |
|-------|--------|
| Basic Auth working | ✅ Verified (HTTP 401 without credentials) |
| No public accounts | ✅ Confirmed |
| No file uploads | ⚠️ UI has file drop, backend has upload handling |
| No payments | ✅ Confirmed |
| No external API keys exposed | ✅ Confirmed |
| Model calls | ⚠️ Would use Ollama (qwen3-coder-next:cloud) |

---

## Final Judgment

**`protected_chat_not_ready_runtime_broken`**

### Reason

1. Chat backend runs but returns import errors
2. Core dialogue function (`handle_direct_message`) is missing from codebase
3. Frontend not built/deployed
4. nginx routes `chat.weslr.de` to static landing page, not chat backend

### What Would Be Needed

1. **Code fix:** Add `handle_direct_message` to `dialogue.py` or fix import in `chat_ui.py`
2. **Code fix:** Make `commands/speak.py` work without stdin
3. **Build:** `cd weslr-ui && npm install && npm run build`
4. **Deploy:** Serve frontend from port 8088 or route through nginx
5. **Start:** Backend on port 8090 (or use existing 8081)
6. **Route:** Update nginx to proxy `chat.weslr.de` to chat backend

**Per constraints:** These are implementation changes requiring owner approval.

---

## Services Started/Stopped

| Action | Details |
|--------|---------|
| Started | `chat_ui.py` on port 8081 (PID 2729204) |
| Stopped | `chat_ui.py` (killed after testing) |
| Not started | `weslr-ui` frontend (needs npm build) |
| Not modified | nginx config |
| Not modified | Cloudflare tunnel |

---

## Commands Used (No Secrets)

```bash
# Preflight
cd /home/pr0/projects/weslr && git status
ss -tulpn | grep -E "8081|8088|8090"
python3 -c "from dialogue import handle_direct_message"

# Start backend
nohup python3 chat_ui.py > /tmp/weslr-chat-ui.log 2>&1 &

# Test
curl -s http://127.0.0.1:8081/
curl -s -X POST http://127.0.0.1:8081/api/send -H "Content-Type: application/json" -d '{"message":"What is WESLR?"}'

# Stop
kill <PID>
```

---

## Backup Files Created

| File | Purpose |
|------|---------|
| `/etc/nginx/conf.d/weslr-staging-8080.conf.bak.20260530` | Pre-existing backup |
| None created by this session | (No changes made) |

---

## Model/Provider Behavior

If chat were working:
- **Provider:** Ollama
- **Model:** qwen3-coder-next:cloud
- **Host:** http://127.0.0.1:11434
- **API calls:** Would occur via `weslr/providers.py`

**Status:** Ollama running, models available, but chat pipeline broken before model calls.

---

## Recommended Next Lane

**OWNER_DECISION_REQUIRED**

Options:
1. **Fix code** — Add `handle_direct_message` to `dialogue.py` (requires development)
2. **Alternative backend** — Use different WESLR entry point (requires development)
3. **Leave as-is** — `chat.weslr.de` remains protected static landing page

---

**Report saved:** `/home/pr0/projects/weslr-v1-ui-website/docs/WESLR_PROTECTED_CHAT_INTERFACE_BRINGUP_REPORT_V1.md`