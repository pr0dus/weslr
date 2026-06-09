# NOVA_PROTECTED_CHAT_AUTH_ROLE_STATUS_AND_BACKEND_AVAILABILITY_GATE_V1.md

**Date:** 2026-06-09 22:11  
**Status:** STABILITY REPAIR COMPLETE ✅ (with backend-service blocker)  
**Mode:** Source patch only — no redesign, no Phase 1, no runtime expansion

---

## 0. Previous Gate Status — Corrected

The previous stability gate report (`NOVA_PROTECTED_CHAT_STABILITY_GATE_BEFORE_MODERN_UI_PHASE_1_V1.md`) declared the gate as `passed ready for phase 1`. That verdict was **too strong**. The correct status is:

> `nova_protected_chat_stability_gate_partial_pass_blocked_by_auth_role_and_backend_uncertainty`

This repair lane (Option A from the previous report) addresses the two missing criteria:
1. `/api/auth/me` role handling in source
2. Visible role/status badge

The remaining blocker (backend service on 127.0.0.1:8092 not listening) is documented below.

---

## 1. Backend Implementation Findings

### 1.1 Source files

The protected workflow backend is implemented at:
- `/home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py` (18,236 bytes, last modified 2026-06-09 06:53)
- It is NOT in `weslr-v1-ui-website/tools/` — it lives in the sister `weslr/` repo

The `weslr-v1-ui-website` repo has **no** `tools/` directory. All backend references in `docs/` point to the `weslr/` repo.

### 1.2 Endpoints implemented

The server implements:
- `GET /api/auth/me` — returns role, writes_enabled, google_auth_enabled (per `NOVA_PROTECTED_AUTH_ROLE_ADAPTER_MOCK_V1.md`)
- `POST /api/message` — accepts message + project_id + mode, dispatches to `dispatch_deterministic_handler` (no model calls)
- Default port: **8092** (per `if __name__ == "__main__": port = int(sys.argv[1]) if len(sys.argv) > 1 else 8092`)

### 1.3 Service status

```
$ ss -ltnp | grep 8092
NOT LISTENING ❌

$ ps aux | grep -E "protected_non_model_workflow_server|8092|weslr-chat"
NO PROCESS FOUND ❌
```

**The backend service is NOT running.** This is the same blocker identified in the previous gate. Per dispatch rule "Do not start/stop services yet unless clearly safe and already documented," I did not attempt to start the service.

The documented start path is a manual invocation:
```bash
cd /home/pr0/projects/weslr && python3 tools/protected_non_model_workflow_server.py 8092
```

Or via the documented nginx-routed path (`/api/auth/*` → `127.0.0.1:8092` in `/etc/nginx/conf.d/weslr-unified-8080.conf`).

### 1.4 Deployed backend evidence

The chat.weslr.de `/api/auth/me` endpoint returns 401 to unauthenticated requests, which is the htpasswd gate working. The actual `/api/auth/me` JSON response can only be observed via an authenticated request — and that requires the backend service to be running, which it is not.

The `/api/message` endpoint returns 401 for the same reason.

**Conclusion:** The backend implementation exists in source but is not deployed/running on this host. The 401s from public curl are the htpasswd gate, not a backend response.

---

## 2. Port 8092 / Service Findings

| Field | Value |
|-------|-------|
| Port | 8092 (per `__main__` default) |
| Listen address | 127.0.0.1 (per `ThreadingHTTPServer(("127.0.0.1", port), Handler)`) |
| Listening on this host? | **NO** |
| Process | None found |
| Systemd unit | None found (grep did not surface) |
| pm2 / tmux / nohup | None found |
| Documented start | Manual `python3 tools/protected_non_model_workflow_server.py 8092` |

**The 8092 backend is not co-located with this OpenClaw session.** Per dispatch rules I have not started it.

---

## 3. Frontend Auth/Status Changes (Source Patch)

### 3.1 Files modified

- `protected-preview/chat-app-shell/index.html` — patched
- `protected-preview/chat-app-shell/index.html.pre-auth-status-20260609-221100.bak` — pre-patch backup (local, not committed)
- Deployed file `/var/www/weslr-chat-app-shell/index.html` — **NOT YET SYNCED** (requires sudo, see §5.3)

### 3.2 Patches applied

#### (a) Topbar role/status pill
**Before:**
```html
<div class="status-pill">Protected • Internal</div>
```

**After:**
```html
<div class="status-pill" id="authStatusPill">Protected • Internal</div>
```

The pill now has an `id` so it can be updated by JS.

#### (b) Empty-state auth-status notice
**Before:**
```html
<div class="backend-warning">Backend not connected - All messages are local UI preview only.</div>
```

**After:**
```html
<div class="backend-warning" id="authStatusNotice">Protected session · auth status unavailable</div>
```

The misleading "Backend not connected" text is gone. The new text is **honest** — it describes the actual state when /api/auth/me is unreachable.

#### (c) Panel content templates — also cleaned
**Before:**
```
'project-options': '... <p class="status-label status-backend-blocked">Backend not connected</p> ...'
'settings': '... <p class="status-label status-backend-blocked">Backend not connected</p> ...'
```

**After:**
```
'project-options': '... <p class="status-label status-backend-blocked">Auth status unavailable</p> ...'
'settings': '... <p class="status-label status-backend-blocked">Auth status unavailable</p> ...'
```

Per dispatch rule: "No stale 'Backend not connected' banner if composer is wired to '/api/message'." Composer IS wired, so all stale text is replaced.

#### (d) New `initAuthStatus()` function
Added to the script section. Full code:

```js
async function initAuthStatus() {
  const pill = document.getElementById('authStatusPill');
  const notice = document.getElementById('authStatusNotice');
  try {
    const res = await fetch('/api/auth/me', { method: 'GET', credentials: 'include' });
    if (!res.ok) throw new Error('auth-me ' + res.status);
    const data = await res.json();
    const role = (data && data.role) ? data.role : 'unknown';
    const writes = (data && data.writes_enabled === true);
    const googleAuth = (data && data.google_auth_enabled === true);
    let label = 'Role: ' + role;
    if (role === 'owner') label = 'Owner Preview';
    pill.textContent = label + (writes ? ' • writes:on' : ' • writes:off');
    pill.title = 'role=' + role + ' | writes=' + (writes ? 'true' : 'false') + ' | google_auth=' + (googleAuth ? 'true' : 'false');
    if (notice) notice.style.display = 'none';
  } catch (err) {
    pill.textContent = 'Auth status unavailable';
    pill.title = '/api/auth/me unreachable: ' + (err && err.message ? err.message : 'unknown');
    if (notice) {
      notice.textContent = 'Protected session · auth status unavailable';
      notice.style.display = '';
    }
    // Composer remains usable — sendMessage() does not depend on /api/auth/me.
  }
}
```

**Behavior:**
- On load, calls `GET /api/auth/me` with `credentials: 'include'` so htpasswd creds are sent.
- If response OK, parses JSON and renders:
  - Role chip: `Owner Preview` (for role=owner), or `Role: <role>` (for other roles)
  - Writes status: `writes:on` / `writes:off` appended
  - Tooltip: full `role | writes | google_auth` triple
  - Hides the empty-state notice
- If response fails (network error, 4xx, 5xx, JSON parse):
  - Pill shows `Auth status unavailable`
  - Tooltip shows the error message
  - Empty-state notice remains visible
  - **Composer is NOT blocked** — `sendMessage()` runs independently

#### (e) Initial call
Added at end of script:
```js
initAuthStatus();
```

### 3.3 Stale content audit

```bash
$ grep -c "Backend not connected" protected-preview/chat-app-shell/index.html
0 ✅

$ grep -c "UI Preview Only" protected-preview/chat-app-shell/index.html
0 ✅

$ grep -n "fetch.*/api/message" protected-preview/chat-app-shell/index.html
516:      fetch('/api/message', {  ✅ (preserved)

$ grep -n "fetch.*/api/auth/me" protected-preview/chat-app-shell/index.html
471:        const res = await fetch('/api/auth/me', { method: 'GET', credentials: 'include' });  ✅ (new)

$ grep -n "Owner Preview" protected-preview/chat-app-shell/index.html
478:        if (role === 'owner') label = 'Owner Preview';  ✅ (new, logic for role badge)
```

---

## 4. Source/Deployed Sync Status

| Field | Value |
|-------|-------|
| Source patched | ✅ |
| Pre-patch backup | `protected-preview/chat-app-shell/index.html.pre-auth-status-20260609-221100.bak` (19,251 bytes) |
| Deployed file | `/var/www/weslr-chat-app-shell/index.html` |
| Deployed file owner | `root:www-data` mode `644` |
| My user | `pr0` (uid 1000) — not in `www-data` group |
| Sync attempt | `cp protected-preview/.../index.html /var/www/.../index.html` |
| Result | **Permission denied** ❌ |

```bash
$ cp protected-preview/chat-app-shell/index.html /var/www/weslr-chat-app-shell/index.html
cp: cannot create regular file '/var/www/weslr-chat-app-shell/index.html': Permission denied

$ cmp -s protected-preview/chat-app-shell/index.html /var/www/weslr-chat-app-shell/index.html
SOURCE_DEPLOYED_DIFFER ⚠️
```

The deploy requires `sudo` per the documented procedure in `NOVA_CHAT_WESLR_DEPLOYED_V1.md`:

```bash
sudo rsync -a --delete /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/ /var/www/weslr-chat-app-shell/
sudo chown -R root:www-data /var/www/weslr-chat-app-shell
sudo find /var/www/weslr-chat-app-shell -type d -exec chmod 755 {} \;
```

**Per execution policy I will not auto-sudo.** I am requesting owner approval for the deploy command. Until the owner runs the rsync (or grants sudo approval for this session), the deployed file is the pre-patch version.

**Source state is correct and stable.** The deploy is a single `rsync` away.

---

## 5. Public Exposure Check (Post-Patch)

```bash
$ curl -I https://chat.weslr.de/api/auth/me
401 ✅ (htpasswd gate working — no auth leak)

$ curl -I https://chat.weslr.de/api/message
401 ✅ (htpasswd gate working — no auth leak)

$ curl -I https://weslr.de/api/auth/me
502 ⚠️ (upstream error, NOT protected content — was 502 in prior reports)

$ curl -I https://weslr.de/api/message
502 ⚠️ (same as above)

$ curl -I https://weslr.de/app
502 ⚠️ (same as above — should be 404 per accepted work, separate follow-up)
```

| URL | Status | Verdict |
|-----|--------|---------|
| `chat.weslr.de/api/auth/me` | 401 | ✅ Protected as expected |
| `chat.weslr.de/api/message` | 401 | ✅ Protected as expected |
| `weslr.de/api/auth/me` | 502 | ✅ Does NOT expose protected content |
| `weslr.de/api/message` | 502 | ✅ Does NOT expose protected content |
| `weslr.de/app` | 502 | ✅ Does NOT expose protected content (separate follow-up) |

**Public exposure remains blocked.** The 502s on `weslr.de` are an upstream connectivity issue, not a content leak.

---

## 6. Owner Manual Browser Test Checklist

The authenticated browser test cannot be performed from this environment (no htpasswd creds, no headless browser, backend not running on this host). The owner must perform the following checks manually after the source patch is deployed to `/var/www/weslr-chat-app-shell/`.

### Pre-flight

```bash
# Owner runs these on the host that has the htpasswd creds:

# 1. Start the backend service (if not already running)
cd /home/pr0/projects/weslr
python3 tools/protected_non_model_workflow_server.py 8092 &
# OR with sudo / systemd / pm2 per the deployment contract

# 2. Deploy the patched source
sudo rsync -a --delete \
  /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/ \
  /var/www/weslr-chat-app-shell/
sudo chown -R root:www-data /var/www/weslr-chat-app-shell
sudo find /var/www/weslr-chat-app-shell -type d -exec chmod 755 {} \;
```

### Manual browser test steps

1. **Open** `https://chat.weslr.de/`
2. **Authenticate** with the htpasswd credentials when prompted
3. **Topbar pill** — should show either:
   - `Owner Preview • writes:off` (if `/api/auth/me` returns role=owner, writes_enabled=false)
   - `Role: <role> • writes:on/off` (for other roles)
   - `Auth status unavailable` (if backend unreachable)
4. **Send a message:** type `What is WESLR?` and press Enter (or tap Send)
5. **User message** appears in the chat
6. **Backend response** appears (or an exact backend error is visible)
7. **Confirm none of these strings are visible:**
   - `UI Preview Only`
   - `Backend not connected` (the static banner)
   - `Backend Error: 405` (a method-not-allowed error)
8. **Confirm the composer remains styled and usable** — type another message, press Enter, observe behavior
9. **If `Owner Preview` chip is visible** — confirm tooltip on hover shows `role=owner | writes=false | google_auth=false`
10. **Capture** a screenshot of the topbar with the role chip for the design review record

### Expected pass criteria (per dispatch)

- ✅ Role badge appears
- ✅ `What is WESLR?` calls backend
- ✅ Backend response appears
- ✅ No `UI Preview Only`
- ✅ No `Backend not connected`
- ✅ No `Backend Error: 405`
- ✅ Composer is styled and usable

If any item fails, the patch needs iteration. If the backend is the issue (502/500), the workflow server must be started first.

---

## 7. Exact Remaining Blockers

| # | Blocker | Severity | Resolution |
|---|---------|----------|------------|
| 1 | **Backend service on 127.0.0.1:8092 not running** | HIGH | Owner must start the workflow server. Per dispatch I cannot start it. |
| 2 | **Deployed file not synced** | HIGH | Owner must run `sudo rsync` (approval requested in §4). Until then, deployed file is pre-patch. |
| 3 | **Authenticated browser test cannot be performed by Nova** | HIGH | Owner must perform manually (checklist in §6). |
| 4 | **htpasswd creds unavailable to Nova** | HIGH | Stored in `/etc/nginx/.htpasswd-weslr-staging` (root:www-data, mode 640). Nova has no read access. |
| 5 | **`weslr.de/app` returns 502** | LOW (out of scope) | Separate follow-up. Was 502 in prior reports, unchanged. |
| 6 | **No headless browser in env** | MEDIUM | Future work — if owner wants automated regression tests, add Playwright with stored creds. |

---

## 8. No-Runtime-Expansion Confirmation

- ❌ No redesign
- ❌ No new panel system
- ❌ No Modern UI Phase 1
- ❌ No Google OAuth
- ❌ No daemon
- ❌ No model provider
- ❌ No tools
- ❌ No settings writes
- ❌ No public chat
- ❌ No public registration
- ❌ No legal page edits
- ❌ No backend contract changes (frontend reads existing `/api/auth/me` shape: `role`, `writes_enabled`, `google_auth_enabled`)

This repair is **source-patch only**: ~30 lines of HTML/JS added to handle the existing `/api/auth/me` endpoint and render a role chip. The endpoint shape is documented in `NOVA_PROTECTED_AUTH_ROLE_ADAPTER_MOCK_V1.md`.

---

## 9. Git Validation

```bash
$ git diff --check
(no output — clean whitespace)

$ git status --short
M protected-preview/chat-app-shell/index.html
?? docs/NOVA_PROTECTED_CHAT_AUTH_ROLE_STATUS_AND_BACKEND_AVAILABILITY_GATE_V1.md
?? protected-preview/chat-app-shell/index.html.pre-auth-status-20260609-221100.bak
?? protected-preview/chat-app-shell/index.html.pre-reconcile-20260609-215300.bak
```

---

## 10. Final Judgment

`nova_protected_chat_auth_status_backend_gate_blocked_by_backend_service_unavailable`

The frontend source patch is complete and correct. The four sub-criteria from §3.3 all pass:
- `/api/message` preserved
- `/api/auth/me` added
- "Owner Preview" role badge logic added
- 0 stale "Backend not connected" / "UI Preview Only" remaining

But the gate is **blocked** by the backend service not running. Per dispatch rule (one of the three allowed final judgments), this is the correct verdict:

> "nova_protected_chat_auth_status_gate_blocked_by_backend_service_unavailable"

When the owner (a) deploys the patched source via the documented `sudo rsync` and (b) starts the workflow server, the next judgment will be:

> "nova_protected_chat_auth_status_backend_gate_ready_for_owner_browser_test"

---

## 11. Owner Action Items (Priority Order)

1. **APPROVE the deploy command** (or run it manually):
   ```bash
   sudo rsync -a --delete /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/ /var/www/weslr-chat-app-shell/
   sudo chown -R root:www-data /var/www/weslr-chat-app-shell
   sudo find /var/www/weslr-chat-app-shell -type d -exec chmod 755 {} \;
   ```

2. **START the backend service:**
   ```bash
   cd /home/pr0/projects/weslr && python3 tools/protected_non_model_workflow_server.py 8092 &
   ```

3. **RUN the manual browser test** (checklist in §6)

4. **REPORT BACK** the result of each of the 7 pass criteria

After owner confirms pass, the gate becomes `ready_for_owner_browser_test` and Phase 1 can begin.

---

**Report author:** Nova (Telegram dispatcher, WESLR ops context)  
**Active model during report:** `minimax-m3:cloud`  
**Owner-visible next action:** Approve the deploy (item 1) and start the service (item 2) to unblock the gate.
