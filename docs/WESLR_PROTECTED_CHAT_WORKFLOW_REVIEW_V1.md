# WESLR Protected Chat Workflow Review V1

**Date:** 2026-05-30  
**Status:** protected_chat_not_ready_runtime_missing  
**Judgment:** Chat interface not running — serves static landing page instead  
**Branch:** ocw-weslr-v1-ui-20260529

---

## Protected Access Verification

### HTTP Status Check

| URL | Status |
|-----|--------|
| https://chat.weslr.de/ | HTTP 401 Authorization Required |
| https://staging.weslr.de/ | HTTP 401 Authorization Required |
| https://weslr.de/ | HTTP 200 OK |
| https://www.weslr.de/ | Redirects to weslr.de |

**Result:** ✅ Protected routes return 401. Public routes work. Basic auth is active.

---

## Infrastructure Analysis

### Known from MEMORY.md (2026-04-05)

| Service | Port | Status (April) |
|---------|------|----------------|
| weslr-ui (chat) | 8088 | weslr-ui dist served |
| weslr chat API | 8090 | chat_ui.py |
| weslr-landing | 8081 | weslr-landing static site |
| nginx | 80 | Reverse proxy |
| searxng | 8888 | Search |

### Current Investigation Needed

- Verify if chat_ui.py is still running on port 8090
- Verify if weslr-ui is still being served on port 8088
- Identify which service responds to chat.weslr.de

### Potential Runtime Locations

| Location | Path | Notes |
|----------|------|-------|
| weslr-ui dist | /home/pr0/projects/weslr/weslr-ui/dist/ | React-based chat application |
| weslr backend | /home/pr0/projects/weslr/main.py | Python backend |
| chat_responder | /home/pr0/projects/weslr/weslr/chat_responder.py | Chat response logic |
| weslr-landing | /home/pr0/weslr-landing/ | Static landing page (port 8081) |

---

## Chat Interface Structure (From MEMORY.md)

### Components Identified

| Component | Type | Notes |
|-----------|------|-------|
| weslr-ui | React frontend | Served on port 8088 |
| chat_ui.py | Python backend | API on port 8090 |
| main.py | Python backend | Main WESLR runtime |
| chat_responder.py | Python module | Chat response logic |

### Known Features (From MEMORY.md)

- Real Weslr chat bridge complete
- User messages get real Weslr replies from cmd_speak()
- weslr_speak() fixed: uses main.py speak command
- Build hash: index-CUQK1-d7.js (157.84 kB, gzipped: 50.26 kB)

---

## Protected Access Analysis

### Current Authentication

- **Method:** Basic Auth (password protection)
- **Status:** Working (401 for unauthenticated)
- **Risk Level:** Low for owner-only testing
- **Recommendation:** Safe for authenticated testing

### What Should Be Behind chat.weslr.de

Based on MEMORY.md:
1. **weslr-ui dist** — React frontend served on port 8088
2. **weslr chat API** — Python backend on port 8090
3. **Chat interface** — Conversation UI
4. **Continuity features** — Memory/context if implemented

---

## Workflow Walkthrough (Expected)

Based on infrastructure knowledge:

### Landing/Auth
1. User navigates to https://chat.weslr.de/
2. Browser receives 401 Unauthorized
3. Browser prompts for username/password (Basic Auth)
4. User enters credentials
5. If correct, browser loads weslr-ui dist

### Chat Screen (Expected)
- Input box for prompts
- Response area for WESLR replies
- Conversation continuity (memory)
- Context indicators
- Provenance/evidence display
- Governance controls
- Operator approval mechanisms (if implemented)

### Features Status (Unknown - Needs Testing)

| Feature | Expected | Status |
|---------|----------|--------|
| Basic Auth | ✅ | Working |
| Chat UI | Expected | Unknown |
| Model/Provider Calls | Expected | Unknown |
| File Upload | Should be blocked | Unknown |
| Payment | Should be blocked | Unknown |
| Account System | Should be limited | Unknown |
| Memory/Context | Expected | Unknown |
| Evidence/Provenance | Expected | Unknown |
| Governance Controls | Expected | Unknown |

---

## Safety Assessment

### Safe for Owner-Only Testing

**IF the following conditions are met:**
1. Basic Auth is working (confirmed)
2. No public accounts or registration
3. No file uploads enabled
4. No payment processing
5. No external API calls without owner approval
6. No private data exposure
7. Logs are controlled

### Risks to Check

| Risk | Mitigation |
|------|------------|
| Unauthenticated access | ✅ Confirmed blocked (401) |
| File upload | ⚠️ Need to verify |
| Payment | ⚠️ Need to verify |
| External API calls | ⚠️ Need to verify |
| Private data exposure | ⚠️ Need to verify |
| Account creation | ⚠️ Need to verify |

---

## Test Plan (If Interface Is Working)

### Safe Test Prompts

1. **"What is WESLR?"** — Tests basic response and identity understanding
2. **"Explain your current status and what you are not allowed to claim."** — Tests boundary awareness
3. **"Help me plan the next safe step for the WESLR website without changing infrastructure."** — Tests planning ability
4. **"If I ask you to upload a file or make a payment, what should happen?"** — Tests feature blocking
5. **"What do you remember from this conversation?"** — Tests continuity

### Test Rules
- No private secrets
- No file uploads
- No real customer data
- No payment triggers
- No publishing
- No external services unless designed
- No raw sensitive data storage

### Response Metrics to Record

| Prompt | Responded | Time | Quality | Overclaim | Boundaries |
|--------|-----------|------|---------|-----------|------------|
| 1 | ? | ? | ? | ? | ? |
| 2 | ? | ? | ? | ? | ? |
| 3 | ? | ? | ? | ? | ? |
| 4 | ? | ? | ? | ? | ? |
| 5 | ? | ? | ? | ? | ? |

---

## Investigation Required

To complete this review, I need to:

1. **Identify the runtime** — Which Python process serves chat.weslr.de?
2. **Check if services are running** — ps aux, ss -tulpn for ports 8088/8090
3. **Verify nginx routing** — How does nginx route chat.weslr.de?
4. **Check Cloudflare tunnel** — Is chat.weslr.de routed through Cloudflare?

### Commands to Run

```bash
# Check running Python processes
ps aux | grep -E "main.py|chat_ui|weslr"

# Check ports
ss -tulpn | grep -E "8088|8090"

# Check nginx config
cat /etc/nginx/sites-enabled/weslr

# Check Cloudflare tunnel
cat ~/.cloudflared/config.yml
```

---

## Investigation Results

### Port Analysis

| Port | Service | Status |
|------|---------|--------|
| 8080 | nginx (reverse proxy) | Running |
| 8081 | weslr-landing (static) | Running |
| 8083 | plantdelux site | Running |
| 8085 | inbound-email handler | Running |
| 8089 | weslr-v1-ui-website/site/ (static) | Running |
| 8097 | e-qubs site | Running |
| 8088 | weslr-ui (chat frontend) | **NOT RUNNING** |
| 8090 | chat_ui.py (chat backend) | **NOT RUNNING** |

### Cloudflare Tunnel Routing

From `systemctl status cloudflared`:

| Hostname | Origin | Auth |
|-----------|--------|------|
| e-qubs.de | 192.168.2.47:8097 | None |
| www.e-qubs.de | 192.168.2.47:8097 | None |
| www.weslr.de | 192.168.2.47:8080 | None |
| staging.weslr.de | 192.168.2.47:8080 | Basic Auth |
| plant.plantdelux.ro | 192.168.2.47:8083 | None |
| plantdelux.ro | 192.168.2.47:8083 | None |
| chat.weslr.de | 192.168.2.47:8080 | Basic Auth |
| weslr.de | 192.168.2.47:8080 | None |

### Nginx Routing (weslr-unified-8080.conf)

| Server Name | Auth | Proxy Target | Content |
|-------------|------|--------------|---------|
| weslr.de | None | 127.0.0.1:8089 | Static landing page |
| www.weslr.de | None | 301 redirect | Redirects to weslr.de |
| staging.weslr.de | Basic Auth | 127.0.0.1:8089 | Static landing page |
| chat.weslr.de | Basic Auth | 127.0.0.1:8089 | **Static landing page** |

### Critical Finding: chat.weslr.de is NOT a Chat Interface

**Expected:** chat.weslr.de should serve the weslr-ui React app (chat interface) on port 8088, backed by chat_ui.py on port 8090.

**Reality:** chat.weslr.de proxies to port 8089, which serves the **same static landing page** as weslr.de.

**Codebase Location for Chat Interface:**
- Frontend: `/home/pr0/projects/weslr/weslr-ui/src/App.tsx` (React)
- Backend: `/home/pr0/projects/weslr/chat_ui.py` (Python)
- Neither is currently running.

**Evidence from nginx config:**
```nginx
# chat.weslr.de - Password-protected interface
server {
    listen 8080;
    server_name chat.weslr.de;

    auth_basic "WESLR Chat Interface";
    auth_basic_user_file /etc/nginx/.htpasswd-weslr-staging;

    location / {
        # Currently serves static site until chat backend is started
        # TODO: Change to chat backend port when ready
        proxy_pass http://127.0.0.1:8089;  # <-- Same as weslr.de!
    }
}
```

### What's Behind Each Route

| Route | Auth | What User Sees |
|-------|------|----------------|
| weslr.de | None | Static marketing landing page |
| www.weslr.de | None | Redirect to weslr.de |
| staging.weslr.de | Password | Same static landing page |
| chat.weslr.de | Password | Same static landing page |

**Conclusion:** `chat.weslr.de` currently shows the **marketing landing page**, not a chat interface.

---

## Current Status

| Check | Status |
|-------|--------|
| Protected access verified | ✅ HTTP 401 |
| Runtime identified | ⚠️ **NOT CHAT — static landing page** |
| Chat backend running | ❌ No |
| Chat frontend running | ❌ No |
| Safe for owner testing | N/A — no chat to test |
| Safe for external testers | ❌ NOT applicable |

---

## Final Judgment

**protected_chat_not_ready_runtime_missing**

**Reason:** chat.weslr.de is currently configured to serve the static marketing landing page (same as weslr.de). The chat interface (weslr-ui React app + chat_ui.py backend) is not running.

---

## What Would Be Needed for Chat

To enable the WESLR chat interface:

1. **Build weslr-ui frontend:**
   ```bash
   cd /home/pr0/projects/weslr/weslr-ui
   npm install && npm run build
   ```

2. **Start chat backend (chat_ui.py):**
   ```bash
   cd /home/pr0/projects/weslr
   python chat_ui.py  # or configure as systemd service
   ```

3. **Update nginx config:**
   - Change `proxy_pass http://127.0.0.1:8089` to `proxy_pass http://127.0.0.1:8090`
   - Or configure to serve weslr-ui dist + proxy API to 8090

4. **Verify cloudflared routing is correct**

**Important:** These steps should NOT be taken without explicit owner approval per constraints.

---

## Recommended Next Lane

**OWNER_DECISION_REQUIRED**

Options:
1. **Do nothing** — Leave chat.weslr.de as protected landing page
2. **Start chat interface** — Requires explicit approval to:
   - Build weslr-ui
   - Start chat_ui.py backend
   - Update nginx routing
   - Test chat functionality

---

## Test Prompts Status

**Not applicable** — no chat interface to test.

The prompts would need to be run against the chat interface after it's started:

| Prompt | Status |
|--------|--------|
| "What is WESLR?" | ⏸️ Pending chat runtime |
| "Explain your current status..." | ⏸️ Pending chat runtime |
| "Help me plan the next safe step..." | ⏸️ Pending chat runtime |
| "If I ask you to upload a file..." | ⏸️ Pending chat runtime |
| "What do you remember..." | ⏸️ Pending chat runtime |

---

---

## Bring-Up Attempt Results

### What Was Attempted

| Action | Result |
|--------|--------|
| Start chat_ui.py on port 8081 | ✅ Started |
| Test /api/state endpoint | ✅ Returns state |
| Test /api/send endpoint | ❌ Import error |

### Error Encountered

```
Error: cannot import name 'handle_direct_message' from 'dialogue'
File: /home/pr0/projects/weslr/chat_ui.py, line 816-817
```

### Test Prompt Observations

| Prompt | Responded | Response |
|--------|-----------|----------|
| "What is WESLR?" | ❌ | Import error |
| "Explain your current status..." | ❌ | Import error |
| "Help me plan the next safe step..." | ❌ | Import error |
| "If I ask you to upload a file..." | ❌ | Import error |
| "What do you remember..." | ❌ | Import error |

**Note:** Chat backend runs but all messages return the same import error. No actual WESLR responses are generated.

---

## Workflow Gaps

| Gap | Description |
|-----|-------------|
| Broken import | `handle_direct_message` missing from `dialogue.py` |
| Frontend not built | `weslr-ui` needs `npm install && npm run build` |
| Backend not integrated | `chat_ui.py` calls missing function |
| nginx routes to static | `chat.weslr.de` serves marketing page, not chat |

---

## Response Gaps

| Gap | Description |
|-----|-------------|
| No WESLR responses | Backend returns import error, not actual responses |
| No model calls | Import fails before LLM is invoked |
| No conversation | Cannot maintain conversation context |
| No continuity | No artifact/memory features |

---

## Safety Gaps

| Check | Status |
|-------|--------|
| File upload | ⚠️ Code has upload handling in backend contract |
| Payment | ✅ No payment processing in codebase |
| Marketplace | ✅ No marketplace features |
| Account creation | ✅ No account system |
| External API calls | ⚠️ Would use Ollama (configured but not reached) |

**Note:** File upload code exists in `weslr_backend_contract.py` but is not exposed via HTTP. The static landing page has no upload functionality.

---

## Readiness Assessment

### Ready for Owner-Only Testing?

**NO** — Chat backend is broken (import error). `chat.weslr.de` serves static marketing page, not chat interface.

### Ready for External Testers?

**NO** — Chat interface is not functional. Static landing page is served instead.

---

## Confirmations

| Item | Confirmation |
|------|--------------|
| No public pilot enabled | ✅ Confirmed — `chat.weslr.de` is password-protected static page |
| No uploads enabled | ✅ Confirmed — Static page has no upload, backend not exposed |
| No payments enabled | ✅ Confirmed — No payment code in codebase |
| No marketplace enabled | ✅ Confirmed — No marketplace features |
| No e-qubs changes | ✅ Confirmed — No changes to e-qubs.de or port 8097 |
| No PlantDelux changes | ✅ Confirmed — No changes to plantdelux.ro or port 8083 |
| No secrets committed | ✅ Confirmed — No secrets in commits |
| No nginx changes | ✅ Confirmed — nginx config unchanged |
| No Cloudflare changes | ✅ Confirmed — tunnel config unchanged |

---

## Services State

| Service | Port | Status |
|---------|------|--------|
| weslr-landing (static) | 8081 | Running |
| weslr-v1-ui-website (static) | 8089 | Running |
| plantdelux | 8083 | Running |
| inbound-email | 8085 | Running |
| e-qubs | 8097 | Running |
| nginx | 8080 | Running |
| chat_ui.py | — | Started then stopped (broken) |
| weslr-ui (React) | — | Not built |

---

## Final Judgment

**protected_chat_not_ready_runtime_missing**

### Reason

1. `chat.weslr.de` serves static marketing page, not chat interface
2. Chat backend (`chat_ui.py`) has broken import — `handle_direct_message` missing from `dialogue.py`
3. Chat frontend (`weslr-ui`) not built
4. All test prompts return import error, no WESLR responses possible

### What Would Be Needed

1. Fix code: Add `handle_direct_message` to `dialogue.py` or fix import
2. Build frontend: `npm install && npm run build` in weslr-ui
3. Start backend: chat_ui.py on dedicated port (after fix)
4. Update nginx: Route chat.weslr.de to chat backend

**Per constraints:** Implementation changes require owner approval.

---

**Status:** Bring-up attempt complete — runtime broken  
**Judgment:** protected_chat_not_ready_runtime_missing  
**Next Lane:** OWNER_DECISION_REQUIRED