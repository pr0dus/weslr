# NOVA_PROTECTED_CHAT_DEPLOY_WITH_OWNER_SUDO_APPROVAL_RESULT_V1.md

**Date:** 2026-06-09 22:28  
**Status:** DEPLOY SUCCESSFUL ✅ — backend preview running, ready for owner browser test  
**Mode:** Owner-approved sudo deploy — narrow, scoped, no nginx/auth/db changes

---

## 0. Sudo Channel Used

Owner approved sudo and provided the password. I piped it via `sudo -S -p ""` so it is not echoed to stdout, never written to disk, never logged, never included in this report. After the operations, the temp file holding the timestamp was deleted and the variable cleared. **No password material is in this report, the commit, the log, or any other persisted artifact.**

---

## 1. Preflight ✅

| Check | Result |
|-------|--------|
| Working dir | `/home/pr0/projects/weslr-v1-ui-website` |
| HEAD before deploy | `55fb839` (auth/status source repair) |
| `protected-preview/chat-app-shell/index.html` exists | ✅ |
| `/var/www/weslr-chat-app-shell/` exists | ✅ |

---

## 2. Backup Path ✅

**Backup:** `/var/backups/weslr-chat-app-shell/index.html.before-auth-status-20260609-222900.bak`
- Size: 19,251 bytes
- Owner: `root:www-data`
- Mode: `644`
- Created: 2026-06-09 22:29 (UTC+2)
- Pre-patch deployed state (preserved exactly)

The backup directory `/var/backups/weslr-chat-app-shell/` was created during this operation.

---

## 3. Deploy Command Results ✅

```bash
$ sudo mkdir -p /var/backups/weslr-chat-app-shell
EXIT=0

$ sudo cp -a /var/www/weslr-chat-app-shell/index.html \
    /var/backups/weslr-chat-app-shell/index.html.before-auth-status-20260609-222900.bak
BACKUP=0

$ sudo rsync -a --delete \
    /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/ \
    /var/www/weslr-chat-app-shell/
RSYNC=0

$ sudo chown -R root:www-data /var/www/weslr-chat-app-shell
CHOWN=0

$ sudo find /var/www/weslr-chat-app-shell -type d -exec chmod 755 {} \;
CHMOD_DIR=0

$ sudo find /var/www/weslr-chat-app-shell -type f -exec chmod 644 {} \;
CHMOD_FILE=0
```

All six sudo operations returned exit code 0. No errors, no warnings.

---

## 4. Source/Deployed Match Proof ✅

```bash
$ cmp -s protected-preview/chat-app-shell/index.html /var/www/weslr-chat-app-shell/index.html \
    && echo SOURCE_DEPLOYED_MATCH || echo SOURCE_DEPLOYED_DIFFER
SOURCE_DEPLOYED_MATCH
```

Byte-identical. The deployed file at `/var/www/weslr-chat-app-shell/index.html` is now the patched source from commit `55fb839`.

---

## 5. Deployed Grep Proof ✅

```bash
$ grep -n "/api/auth/me" /var/www/weslr-chat-app-shell/index.html
464:    // Auth/status integration: call /api/auth/me on load, render role chip.
471:        const res = await fetch('/api/auth/me', { method: 'GET', credentials: 'include' });
484:        pill.title = '/api/auth/me unreachable: ' + (err && err.message ? err.message : 'unknown');
489:        // Composer remains usable — sendMessage() does not depend on /api/auth/me.  ✅

$ grep -n "/api/message" /var/www/weslr-chat-app-shell/index.html
516:      fetch('/api/message', {  ✅

$ grep -n "Owner Preview" /var/www/weslr-chat-app-shell/index.html
478:        if (role === 'owner') label = 'Owner Preview';  ✅

$ grep -c "Backend not connected" /var/www/weslr-chat-app-shell/index.html
0 ✅

$ grep -c "UI Preview Only" /var/www/weslr-chat-app-shell/index.html
0 ✅
```

All five checks pass on the deployed file:
- `/api/auth/me` fetch + integration present
- `/api/message` fetch present
- "Owner Preview" label logic present
- No stale "Backend not connected" text
- No stale "UI Preview Only" text

---

## 6. Backend 8092 Status ✅

```bash
$ ss -ltnp | grep 8092
LISTEN 0  5  127.0.0.1:8092  0.0.0.0:*  users:(("python3",pid=3518937,fd=3))
```

The temporary backend started in the previous lane is still running. PID 3518937, log file `/home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.log`, PID file at `/home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.pid`.

---

## 7. Local `/api/auth/me` Summary ✅

```bash
$ curl -i http://127.0.0.1:8092/api/auth/me
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.12.3
Date: Tue, 09 Jun 2026 20:30:02 GMT
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

Frontend will render:
- Pill: `Owner Preview • writes:off`
- Tooltip: `role=owner | writes=false | google_auth=false`
- Empty-state notice: hidden

---

## 8. Local `/api/message` Summary ✅

```bash
$ curl -i -X POST http://127.0.0.1:8092/api/message \
    -H 'Content-Type: application/json' \
    -d '{"message":"What is WESLR?","project_id":"preview-weslr-website-review","mode":"protected_owner_preview"}'
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.12.3
Date: Tue, 09 Jun 2026 20:30:02 GMT
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

Deterministic response, no model call, no 405, no error. Frontend will render this as a WESLR response card.

---

## 9. Public/Protected Exposure Check ✅

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
502 ⚠️ (separate follow-up)

$ curl -I https://weslr.de/api/message
502 ⚠️ (separate follow-up)
```

| URL | Status | Verdict |
|-----|--------|---------|
| `chat.weslr.de/` | 401 | ✅ Protected |
| `chat.weslr.de/api/auth/me` | 401 | ✅ Protected |
| `chat.weslr.de/api/message` | 401 | ✅ Protected |
| `weslr.de/app` | 502 | ✅ No protected content (separate follow-up) |
| `weslr.de/api/auth/me` | 502 | ✅ No protected content (separate follow-up) |
| `weslr.de/api/message` | 502 | ✅ No protected content (separate follow-up) |

Public exposure remains blocked. No leaks introduced by the deploy.

---

## 10. Rollback Commands

### Rollback the deployed file

```bash
# Backup is at:
ls -la /var/backups/weslr-chat-app-shell/index.html.before-auth-status-20260609-222900.bak

# Restore:
echo "<password>" | sudo -S -p "" cp -a \
    /var/backups/weslr-chat-app-shell/index.html.before-auth-status-20260609-222900.bak \
    /var/www/weslr-chat-app-shell/index.html
echo "<password>" | sudo -S -p "" chown root:www-data /var/www/weslr-chat-app-shell/index.html
echo "<password>" | sudo -S -p "" chmod 644 /var/www/weslr-chat-app-shell/index.html

# Verify:
cmp -s /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html /var/www/weslr-chat-app-shell/index.html \
    && echo "MATCH (current state)" || echo "DIFFER (rollback restored pre-patch)"
```

### Stop the temporary backend

```bash
# Read PID:
cat /home/pr0/projects/weslr-v1-ui-website/logs/protected_non_model_workflow_server_8092.pid
# Returns: 3518937

# Stop:
kill 3518937
sleep 1
ps -p 3518937 2>&1 || echo "stopped"
ss -ltnp | grep 8092 || echo "port 8092 free"
```

### Rollback the source file (if needed)

```bash
# Restore pre-patch source (local backup, not committed):
cp /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html.pre-auth-status-20260609-221100.bak \
   /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html
```

Or via git:
```bash
cd /home/pr0/projects/weslr-v1-ui-website
git revert --no-edit 55fb839
# Then re-deploy via the documented sudo rsync
```

---

## 11. Owner Manual Browser Test Checklist

Now that the deploy is complete and the backend is running, perform these checks:

1. **Open** `https://chat.weslr.de/`
2. **Authenticate** with htpasswd credentials
3. **Hard refresh once** (Ctrl/Cmd+Shift+R) — important to bypass any cached version
4. **Topbar pill** should read: `Owner Preview • writes:off`
5. **Topbar pill tooltip** (hover) should read: `role=owner | writes=false | google_auth=false`
6. **Empty-state notice** ("Protected session · auth status unavailable") should be **hidden**
7. In the composer, type `What is WESLR?` and press Enter
8. **User message** appears in the chat
9. **Backend response** appears (the deterministic WESLR response from §8 above)
10. Confirm none of these strings are visible anywhere:
    - `UI Preview Only`
    - `Backend not connected`
    - `Backend Error: 405`
11. The composer remains styled and usable — type another message, press Enter, observe

### Pass criteria (per dispatch)

- ✅ Role/status chip appears
- ✅ "What is WESLR?" calls backend
- ✅ Backend response appears
- ✅ No "UI Preview Only"
- ✅ No "Backend not connected"
- ✅ No "Backend Error: 405"
- ✅ Composer remains styled and usable

If all 7 pass, the gate becomes `ready_for_owner_browser_test` and Modern UI Phase 1 can begin with separate owner approval.

---

## 12. No-Expansion Confirmation

- ❌ No Cloudflare changes
- ❌ No DNS changes
- ❌ No nginx config changes (the `weslr-unified-8080.conf` was NOT touched; the existing `/api/auth/*` → 127.0.0.1:8092 proxy works as-is)
- ❌ No nginx auth weakening (htpasswd gate intact, 401 to unauthenticated)
- ❌ No public chat (htpasswd-protected)
- ❌ No public registration (no register endpoint exists)
- ❌ No Google OAuth
- ❌ No daemon (no systemd/pm2/supervisor — backend is a `setsid nohup` user-space process with PID file)
- ❌ No model provider (backend is `dispatch_deterministic_handler`; header explicitly forbids OpenAI/Anthropic/Gemini/Ollama)
- ❌ No tools
- ❌ No settings writes (`writes_enabled: false` enforced by backend response)
- ❌ No legal page edits
- ❌ No broad repo reset (no `git reset --hard`, no `git checkout` to a non-immediate parent)
- ❌ No redesign (the source patch was the minimum required for the gate)

---

## 13. Git Validation

```bash
$ git diff --check
(no output — clean whitespace)

$ git status --short
?? docs/NOVA_PROTECTED_CHAT_DEPLOY_WITH_OWNER_SUDO_APPROVAL_RESULT_V1.md
?? protected-preview/chat-app-shell/index.html.pre-auth-status-20260609-221100.bak
?? protected-preview/chat-app-shell/index.html.pre-reconcile-20260609-215300.bak
```

---

## 14. Security Notes

- Sudo password was piped via stdin (`echo "$PWD" | sudo -S -p ""`) and is NOT in this report, NOT in the commit, NOT in any log file, NOT in any persisted artifact
- The temp file `/tmp/_ts_nova` that held the timestamp was deleted after use
- The `TS` shell variable was unset after use
- The deploy script (`docs/NOVA_PROTECTED_CHAT_DEPLOY_AND_BACKEND_PREVIEW_START_V1.md.deploy.sh`) is committed but contains no password or secret
- The htpasswd file at `/etc/nginx/.htpasswd-weslr-staging` was NOT read, NOT touched, NOT printed in this report

---

## 15. Final Judgment

`nova_protected_chat_deployed_backend_preview_ready_for_owner_browser_test`

All deploy operations succeeded. The patched source is live at `/var/www/weslr-chat-app-shell/index.html`. The backend is running on 127.0.0.1:8092 (PID 3518937). Both endpoints (`/api/auth/me` and `/api/message`) return real JSON. The deployed file is byte-identical to the source. Public surface remains protected.

**The system is ready for the owner manual browser test** as detailed in §11.

---

**Report author:** Nova (Telegram dispatcher, WESLR ops context)  
**Active model during report:** `minimax-m3:cloud`  
**Backend service:** Running, PID 3518937, port 127.0.0.1:8092  
**Deployed file:** Patched (commit 55fb839), byte-identical to source  
**Backup path:** `/var/backups/weslr-chat-app-shell/index.html.before-auth-status-20260609-222900.bak`  
**Owner-visible next action:** Run the 11-item manual browser test checklist in §11.
