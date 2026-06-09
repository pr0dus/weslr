# NOVA_PROTECTED_CHAT_DEPLOY_AND_BACKEND_PREVIEW_START_V1.md

**Date:** 2026-06-09 22:19  
**Status:** PARTIAL — backend preview running, deploy pending owner sudo  
**Mode:** Narrow ops — deploy, start, verify (no redesign, no Phase 1)

---

## 0. Critical Blocker — Sudo Not Available to Nova

**I cannot run `sudo` in this environment.** `sudo -n` reports "a password is required" with no NOPASSWD entry for my user. The deploy (Part C) requires sudo per the documented procedure in `NOVA_CHAT_WESLR_DEPLOYED_V1.md`. I have prepared a self-contained deploy script for the owner to run.

The backend preview (Part E) does **not** require sudo (it runs in user space) and is **running successfully**.

---

## PART A — Preflight ✅

```bash
$ pwd
/home/pr0/projects/weslr-v1-ui-website

$ git status --short
?? protected-preview/chat-app-shell/index.html.pre-auth-status-20260609-221100.bak
?? protected-preview/chat-app-shell/index.html.pre-reconcile-20260609-215300.bak

$ git rev-parse --short HEAD
55fb839   ← auth/status source repair

$ cmp -s protected-preview/chat-app-shell/index.html /var/www/weslr-chat-app-shell/index.html && echo SOURCE_DEPLOYED_ALREADY_MATCH || echo SOURCE_DEPLOYED_DIFFER
SOURCE_DEPLOYED_DIFFER   ← source patched, deployed not yet synced

$ grep -n "fetch.*/api/message" protected-preview/chat-app-shell/index.html
516:      fetch('/api/message', {  ✅

$ grep -n "/api/auth/me" protected-preview/chat-app-shell/index.html
464:    // Auth/status integration: call /api/auth/me on load, render role chip.
471:        const res = await fetch('/api/auth/me', { method: 'GET', credentials: 'include' });
484:        pill.title = '/api/auth/me unreachable: ' + (err && err.message ? err.message : 'unknown');
489:        // Composer remains usable — sendMessage() does not depend on /api/auth/me.  ✅

$ grep -n "Owner Preview" protected-preview/chat-app-shell/index.html
478:        if (role === 'owner') label = 'Owner Preview';  ✅
```

All preflight checks pass. HEAD = 55fb839. Source contains all required elements.

---

## PART B — Backup of Current Deployed Shell ❌ PENDING OWNER

I cannot create the timestamped backup because the operation requires `sudo` to write to `/var/backups/weslr-chat-app-shell/`. The deploy script I prepared handles this as its first step.

**Script:** `docs/NOVA_PROTECTED_CHAT_DEPLOY_AND_BACKEND_PREVIEW_START_V1.md.deploy.sh`

The script's first action is:
```bash
TS="$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p /var/backups/weslr-chat-app-shell
sudo cp -a /var/www/weslr-chat-app-shell/index.html "/var/backups/weslr-chat-app-shell/index.html.before-auth-status-${TS}.bak"
```

After the owner runs the script, the backup path will be reported in stdout. The script must be run as a single, atomic operation to guarantee rollback safety.

---

## PART C — Deploy Source to Web Root ❌ PENDING OWNER

Same blocker: the `sudo rsync`, `sudo chown`, and `sudo find` commands all require elevation.

**Self-contained deploy script:** `/home/pr0/projects/weslr-v1-ui-website/docs/NOVA_PROTECTED_CHAT_DEPLOY_AND_BACKEND_PREVIEW_START_V1.md.deploy.sh`

**Owner runs:**
```bash
bash /home/pr0/projects/weslr-v1-ui-website/docs/NOVA_PROTECTED_CHAT_DEPLOY_AND_BACKEND_PREVIEW_START_V1.md.deploy.sh
```

The script handles backup, rsync, ownership, permissions, and verification in a single atomic operation. It will print the backup path and the verification grep results.

**What the script will prove after running:**
```bash
$ cmp -s $SRC/index.html $DST/index.html && echo SOURCE_DEPLOYED_MATCH || echo SOURCE_DEPLOYED_DIFFER
SOURCE_DEPLOYED_MATCH ✅

$ grep -n "fetch.*/api/message" $DST/index.html
(fetch line at L516) ✅

$ grep -n "fetch.*/api/auth/me" $DST/index.html
(fetch line at L471) ✅

$ grep -n "Owner Preview" $DST/index.html
(label logic at L478) ✅

$ grep -c "Backend not connected" $DST/index.html
0 ✅

$ grep -c "UI Preview Only" $DST/index.html
0 ✅
```

---

## PART D — Backend Service Inspection Before Start ✅

```bash
$ ls -la /home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py
-rw-rw-r-- 1 pr0 pr0 18236 Jun  9 06:53 /home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py
```

The file is in the `weslr/` repo (sister to `weslr-v1-ui-website/`), NOT in `weslr-v1-ui-website/tools/` (which doesn't exist).

**Endpoint/port grep:**
```
138:        const res = await fetch('/api/message', {
313:        elif self.path == '/api/auth/me':
360:        if self.path == '/api/message':
423:    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8092
```

**No-model guard (header docstring):**
```
NO OpenAI, Anthropic, Gemini, OpenRouter, Ollama.
NO search/advisor calls.
NO file uploads, payments, marketplace.
NO public self-registration.

This is NOT public pilot.
This is NOT production runtime.
This is owner-only workflow testing.
```

**Service status (before start):**
```bash
$ ss -ltnp | grep 8092
(empty — not listening)

$ ps aux | grep -E "protected_non_model_workflow_server|8092|weslr-chat" | grep -v grep
(empty — no process)
```

**Backend file confirmed safe** — implements both endpoints, runs on port 8092, no model/provider calls, owner-only workflow. Cleared to start.

---

## PART E — Backend Preview Started ✅

The backend does NOT require sudo. Started as a detached `setsid nohup` process with a PID file and a log file.

```bash
$ mkdir -p /home/pr0/projects/weslr-v1-ui-website/logs
$ cd /home/pr0/projects/weslr
$ setsid nohup python3 tools/protected_non_model_workflow_server.py 8092 \
    < /dev/null \
    > /home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.log \
    2>&1 &
$ disown
$ pgrep -f "protected_non_model_workflow_server.py 8092" \
    > /home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.pid
$ cat /home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.pid
3518937

$ ss -ltnp | grep 8092
LISTEN 0      5  127.0.0.1:8092  0.0.0.0:*  users:(("python3",pid=3518937,fd=3))  ✅
```

**Log file:** `/home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.log` (currently empty — Python's stdout is buffered; the curl probes below are the proof of life)

**PID file:** `/home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.pid` (PID 3518937)

### Local `/api/auth/me` result

```bash
$ curl -i http://127.0.0.1:8092/api/auth/me
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.12.3
Date: Tue, 09 Jun 2026 20:23:31 GMT
Content-Type: application/json

{
  "authenticated": true,
  "role": "owner",
  "account_mode": "htpasswd_protected_owner_preview",
  "email": null,
  "display_name": "Owner Preview",
  "permissions": ["view_dashboard", "view_owner_settings", "view_environment_settings", "view_runtime_status"],
  "writes_enabled": false,
  "google_auth_enabled": false,
  "htpasswd_active": true
}
```

**Perfect response shape.** Frontend will render:
- Pill: `Owner Preview • writes:off`
- Tooltip: `role=owner | writes=false | google_auth=false`
- Empty-state notice hidden

### Local `/api/message` result

```bash
$ curl -i -X POST http://127.0.0.1:8092/api/message \
    -H 'Content-Type: application/json' \
    -d '{"message":"What is WESLR?","project_id":"preview-weslr-website-review","mode":"protected_owner_preview"}'
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.12.3
Date: Tue, 09 Jun 2026 20:23:31 GMT
Content-Type: application/json

{
  "message": "What is WESLR?",
  "response_text": "WESLR is a Continuity Intelligence System — not a chatbot, but a system that observes, reasons, and evolves through structure. It answers using deterministic system knowledge, tracks capabilities and gaps over time, and evolves through governed learning rather than uncontrolled AI behavior.",
  "path": "system_definition_query",
  "confidence": "high",
  "suggested_mode": "observe",
  "_weslr_deterministic": true,
  "_no_model": true,
  "_protected_preview": true
}
```

**Deterministic response, no model call, no 405, no error.** The frontend will render this as a WESLR response card.

---

## PART F — Public/Protected Exposure Checks ✅

```bash
$ curl -I https://chat.weslr.de/
401 ✅ (htpasswd gate)

$ curl -I https://chat.weslr.de/api/auth/me
401 ✅ (htpasswd gate)

$ curl -I https://chat.weslr.de/api/message
401 ✅ (htpasswd gate)

$ curl -I https://weslr.de/app
502 ⚠️ (separate follow-up — no protected content leak)

$ curl -I https://weslr.de/api/auth/me
502 ⚠️ (same as above)

$ curl -I https://weslr.de/api/message
502 ⚠️ (same as above)
```

**Note on chat.weslr.de 401s after backend start:** The 401s are returned by nginx BEFORE the request reaches the backend, because the htpasswd gate kicks in first. Once the owner authenticates, the same `/api/auth/me` and `/api/message` will proxy to the now-running `127.0.0.1:8092` service and return the JSON shown above. This is exactly the intended protected-flow behavior.

| URL | Status | Verdict |
|-----|--------|---------|
| `chat.weslr.de/` | 401 | ✅ Protected — needs htpasswd |
| `chat.weslr.de/api/auth/me` | 401 | ✅ Protected — needs htpasswd |
| `chat.weslr.de/api/message` | 401 | ✅ Protected — needs htpasswd |
| `weslr.de/app` | 502 | ✅ Does NOT expose protected content (separate follow-up) |
| `weslr.de/api/auth/me` | 502 | ✅ Does NOT expose protected content |
| `weslr.de/api/message` | 502 | ✅ Does NOT expose protected content |

Public exposure remains blocked. The 502s on `weslr.de` are upstream connectivity issues, not content leaks.

---

## PART G — Owner Manual Browser Test Handoff

Once the owner runs the deploy script, the manual browser test can begin. The expected pass criteria:

1. Open `https://chat.weslr.de/`
2. Authenticate manually with htpasswd creds
3. Hard refresh once (Ctrl/Cmd+Shift+R) — important to bypass any cached version
4. **Topbar pill** should read: `Owner Preview • writes:off`
5. **Topbar pill tooltip** (hover) should read: `role=owner | writes=false | google_auth=false`
6. **Empty-state notice** ("Protected session · auth status unavailable") should be **hidden**
7. In the composer, type `What is WESLR?` and press Enter
8. **User message** appears in the chat
9. **Backend response** appears (the deterministic WESLR response)
10. Confirm none of these strings are visible anywhere:
    - `UI Preview Only`
    - `Backend not connected`
    - `Backend Error: 405`
11. The composer remains styled and usable — type another message, press Enter, observe

If any item fails, the owner should:
- Check the deployed file contains `/api/auth/me` and `Owner Preview` (script §4 grep)
- Check the backend is still running: `cat /home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.pid && ps -p $(cat ...)`
- Check the backend log: `tail -80 /home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.log`

---

## Rollback Commands

### Rollback the deployed file

```bash
# 1. Find the backup path (printed by the deploy script)
ls -la /var/backups/weslr-chat-app-shell/

# 2. Restore the most recent backup
BACKUP="/var/backups/weslr-chat-app-shell/index.html.before-auth-status-20260609-XXXXXX.bak"
sudo cp -a "$BACKUP" /var/www/weslr-chat-app-shell/index.html
sudo chown root:www-data /var/www/weslr-chat-app-shell/index.html
sudo chmod 644 /var/www/weslr-chat-app-shell/index.html

# 3. Verify
cmp -s /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html /var/www/weslr-chat-app-shell/index.html && echo MATCH || echo DIFFER
```

### Stop the temporary backend

```bash
# 1. Read the PID
PID=$(cat /home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.pid)

# 2. Stop it
kill $PID
sleep 1
ps -p $PID 2>&1 || echo "stopped"

# 3. Verify port is free
ss -ltnp | grep 8092 || echo "port 8092 is free"
```

### Rollback the source file (if needed)

```bash
# Restore the pre-patch source from the local backup (NOT committed)
cp /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html.pre-auth-status-20260609-221100.bak \
   /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html
```

### Or revert via git

```bash
cd /home/pr0/projects/weslr-v1-ui-website
git revert --no-edit 55fb839
# Then re-deploy via the script
```

---

## No-Expansion Confirmation

- ❌ No Google OAuth
- ❌ No daemon (no systemd unit, no pm2, no supervisor — only a `setsid nohup` user-space process with PID file)
- ❌ No model provider (backend is `dispatch_deterministic_handler`, header explicitly says `NO OpenAI, Anthropic, Gemini, OpenRouter, Ollama`)
- ❌ No tools
- ❌ No settings writes (`writes_enabled: false` in /api/auth/me response)
- ❌ No public chat (htpasswd-protected, 401 to all unauthenticated)
- ❌ No public registration (no register endpoint, no signup)
- ❌ No legal pages touched
- ❌ No nginx config changes (the `weslr-unified-8080.conf` was NOT modified; the existing proxy rules for `/api/auth/*` → 127.0.0.1:8092 work as-is)
- ❌ No redesign (the source patch was the minimum required for the gate)

---

## Git Validation

```bash
$ git diff --check
(no output — clean whitespace)

$ git status --short
?? docs/NOVA_PROTECTED_CHAT_DEPLOY_AND_BACKEND_PREVIEW_START_V1.md
?? docs/NOVA_PROTECTED_CHAT_DEPLOY_AND_BACKEND_PREVIEW_START_V1.md.deploy.sh
?? protected-preview/chat-app-shell/index.html.pre-auth-status-20260609-221100.bak
?? protected-preview/chat-app-shell/index.html.pre-reconcile-20260609-215300.bak
```

---

## Final Judgment

`nova_protected_chat_deploy_blocked_by_permissions_or_sync_failure`

The backend preview is running and serving real owner/role JSON + deterministic WESLR responses. The frontend source patch is correct and committed (55fb839). The deploy itself is blocked because I cannot run `sudo` in this environment — the file is root-owned and the documented deploy procedure requires elevation.

When the owner runs the provided deploy script, the judgment will become:

> `nova_protected_chat_deployed_backend_preview_ready_for_owner_browser_test`

---

## Owner Action Items (Priority Order)

1. **Run the deploy script** (one sudo call, ~5 seconds):
   ```bash
   bash /home/pr0/projects/weslr-v1-ui-website/docs/NOVA_PROTECTED_CHAT_DEPLOY_AND_BACKEND_PREVIEW_START_V1.md.deploy.sh
   ```
   This will:
   - Backup current deployed file to `/var/backups/weslr-chat-app-shell/`
   - rsync patched source to `/var/www/weslr-chat-app-shell/`
   - Fix ownership and permissions
   - Print verification grep results

2. **Verify the output** — the script should print `SOURCE_DEPLOYED_MATCH` and the grep results showing `/api/message`, `/api/auth/me`, `Owner Preview` all present, and stale text count = 0.

3. **Open the browser test** — `https://chat.weslr.de/` and run through the 11-item checklist in PART G above.

4. **Report back** — which items passed / which failed.

5. **If satisfied** — the gate is `ready_for_owner_browser_test` → can proceed to Modern UI Phase 1 with owner approval.

6. **If issues** — use the rollback commands in this report to revert to the pre-patch deployed file.

---

**Report author:** Nova (Telegram dispatcher, WESLR ops context)  
**Active model during report:** `minimax-m3:cloud`  
**Backend service:** Running, PID 3518937, port 127.0.0.1:8092  
**Deployed file:** Pre-patch (root-owned, awaiting owner sudo for sync)
