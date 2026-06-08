# Protected WESLR Chat App Shell Safe Redeploy V1

**Date:** 2026-06-08  
**Author:** Nova (MAIN_DISPATCHER)  
**Status:** Deployed and Verified ✅

---

## Deployment Directory Used

**Path:** `/var/www/weslr-chat-app-shell/`

**Contents:**
- `index.html` — Protected WESLR chat/project app shell
- `diagnostics/old-workflow-preview.html` — Old workflow preview (diagnostics)

**Permissions:**
- Directory: 755 (root:www-data)
- Files: 644 (root:www-data)
- Verified: `sudo -u www-data test -r` returns success

---

## Nginx File Edited

**File:** `/etc/nginx/conf.d/weslr-unified-8080.conf`

**chat.weslr.de routing changes:**
- Before: `proxy_pass http://127.0.0.1:8092;` (old workflow preview)
- After: `root /var/www/weslr-chat-app-shell;` (static file serving)

**Preserved:**
- `auth_basic "WESLR Chat Interface";`
- `auth_basic_user_file /etc/nginx/.htpasswd-weslr-staging;`

**Added routes:**
- `/` → `/var/www/weslr-chat-app-shell/index.html`
- `/diagnostics/workflow-preview/` → `/var/www/weslr-chat-app-shell/diagnostics/old-workflow-preview.html`

---

## Backup Config Path

**Backup:** `/etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260608-070125`

**When created:** 2026-06-08 07:01:25 (before redeploy)

---

## Auth Preserved Confirmation

| Setting | Status |
|---------|--------|
| `auth_basic` | "WESLR Chat Interface" (unchanged) |
| `auth_basic_user_file` | `/etc/nginx/.htpasswd-weslr-staging` (unchanged) |
| `chat.weslr.de` returns 401 unauthenticated | ✅ Verified |
| `diagnostics/workflow-preview/` returns 401 unauthenticated | ✅ Verified |

---

## Public Exposure Check

| URL | Status | Expected |
|-----|--------|----------|
| `https://weslr.de/app/` | **404** | No protected content |
| `https://weslr.de/` | — | Public site (unchanged) |

**Result:** ✅ Protected app shell NOT exposed on public weslr.de

---

## Authenticated/Browser Result

**Owner browser test (192.168.2.47):**

| Route | Status | Result |
|-------|--------|--------|
| `https://chat.weslr.de/` | 200 | Shows new WESLR project/chat app shell |
| `https://chat.weslr.de/diagnostics/workflow-preview/` | 200 | Shows old workflow preview |

**Verified:**
- ✅ No 500 error after authentication
- ✅ Shows new app shell, NOT old workflow preview as main page
- ✅ Diagnostics route available at `/diagnostics/workflow-preview/`

---

## Nginx Error Log Summary After Authenticated Test

**Command:** `sudo tail -n 80 /var/log/nginx/error.log`

**Result:** No new permission denied, redirect cycle, or file-not-found errors.

**Only errors present are from 06:56 deployment attempt (permission denied on old path):**

```
2026/06/08 06:56:13 [crit] ... stat() "/home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/" failed (13: Permission denied)
2026/06/08 06:56:13 [error] ... rewrite or internal redirection cycle while internally redirecting to "/index.html"
```

**No new errors since 07:02 successful reload.**

---

## Rollback Command (No Password)

```bash
sudo cp /etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260608-070125 /etc/nginx/conf.d/weslr-unified-8080.conf
sudo nginx -t
sudo systemctl reload nginx
```

**To restore old workflow preview without app shell:**

```bash
sudo cp /etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260608-0452 /etc/nginx/conf.d/weslr-unified-8080.conf
sudo nginx -t
sudo systemctl reload nginx
```

---

## Final Judgment

**nova_protected_chat_app_shell_safe_redeploy_verified_after_auth_ready_for_owner_review**

**Status:**
- ✅ Deployment completed
- ✅ Unauthenticated checks passed (401)
- ✅ Authenticated checks passed (no 500, shows new app shell)
- ✅ Diagnostics route available
- ✅ No new nginx errors
- ✅ Public exposure check passed
- ✅ Auth preserved

**Next Action:** Owner can use chat.weslr.de after authentication.

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-08  
**Nginx Status:** Reloaded successfully  
**App Status:** Working after authentication  
**Rollback Ready:** Yes (backup exists)
