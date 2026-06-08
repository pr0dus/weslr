# chat.weslr.de 500 Rollback and Routing Diagnostic V1

**Date:** 2026-06-08  
**Author:** Nova (MAIN_DISPATCHER)  
**Status:** Rolled Back to Safe State  
**Problem:** 500 Internal Server Error after nginx routing deployment

---

## Current Status

### After Rollback

| URL | Status | Behavior |
|-----|--------|----------|
| `https://chat.weslr.de/` | **401** | Protected (requires auth) |
| `https://chat.weslr.de/app/` | **401** | Protected (requires auth) |
| `https://weslr.de/app/` | **404** | No protected content exposed |

### Rollback Executed

- **Backup:** `/etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260608-0452`
- **Restored:** `/etc/nginx/conf.d/weslr-unified-8080.conf`
- **Verification:** `nginx -t` passed, reload successful

---

## Root Cause Analysis

### Error Log Summary

```
stat() "/home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/" failed (13: Permission denied)
stat() "/home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html" failed (13: Permission denied)
rewrite or internal redirection cycle while internally redirecting to "/index.html"
```

### Primary Issue

**Permission Denied (EACCES 13)**

- **Nginx worker user:** `www-data`
- **File owner:** `pr0:pr0`
- **Directory permissions:** `drwxrwxr-x` (755) - readable but not by www-data

**Root cause:** The `/home/pr0/projects/` directory tree is owned by `pr0` user, but nginx runs as `www-data`. While the directory has 755 permissions, the user-specific ownership means `www-data` cannot access files inside.

### Secondary Issue

**Redirect Cycle**

- `try_files $uri $uri/ /index.html` tried to serve `/index.html` as directory
- Since `/index.html` was not accessible, nginx tried to redirect to `/index.html`
- This caused an infinite loop until nginx gave up with 500 error

---

## Files Affected

| Path | Status | Reason |
|------|--------|--------|
| `/etc/nginx/conf.d/weslr-unified-8080.conf` | Rolled back | Reverted to backup |
| `/etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260608-0452` | Created | Rollback source |
| `/home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/` | Unchanged | Permission issue remains |
| `/home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html` | Unchanged | Permission issue remains |

---

## Verification

### Nginx Configuration

```bash
$ sudo nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### curl Tests (After Rollback)

```bash
$ curl -I https://chat.weslr.de/
HTTP/2 401
www-authenticate: Basic realm="WESLR Chat Interface"

$ curl -I https://weslr.de/app/
HTTP/2 404
```

### Expected Behavior Restored

- [x] chat.weslr.de/ returns 401 unauthenticated
- [x] chat.weslr.de/app/ returns 401 unauthenticated
- [x] weslr.de/app/ returns 404 (no protected content)
- [x] Password authentication preserved
- [x] No public exposure

---

## Next Safe Routing Options

### Option 1: Copy to Nginx-Accessible Path (Recommended)

```bash
# Create accessible path
mkdir -p /var/www/chat-app-shell
cp -r /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/* /var/www/chat-app-shell/

# Set permissions for www-data
chown -R www-data:www-data /var/www/chat-app-shell
chmod -R 755 /var/www/chat-app-shell

# Update nginx config to use /var/www/chat-app-shell instead of /home/pr0/projects/...
```

### Option 2: Fix Permissions on Existing Path

```bash
# Add www-data to pr0 group (requires owner approval)
usermod -a -G pr0 www-data

# Or make directory readable by others (less secure)
chmod -R o+rx /home/pr0/projects/weslr-v1-ui-website/protected-preview/
```

### Option 3: Use Alias Instead of try_files

If file permissions fixed, use explicit alias with `try_files` removed:

```nginx
location / {
    alias /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/;
    index index.html;
    # Remove try_files to avoid redirect cycle
}
```

---

## Rollback Commands Used

```
[Owner executed:]
sudo cp /etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260608-0452 /etc/nginx/conf.d/weslr-unified-8080.conf
sudo nginx -t
sudo systemctl reload nginx
```

---

## Report Validation

### Git Status

```
?? nginx-chat-weslr-de.conf
```

### Files Created in Report

| File | Purpose |
|------|---------|
| `/etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260608-0452` | Backup |
| `docs/NOVA_CHAT_WESLR_500_ROLLBACK_AND_ROUTING_DIAGNOSTIC_V1.md` | This report |

---

## Final Judgment

**chat_weslr_500_rolled_back_or_diagnosed_auth_preserved_ready_for_safe_redeploy_plan**

**Status:** Rollback complete, diagnosis documented, safe redeploy plan identified.

**Owner Action Required:**

1. Choose one of the 3 safe fix options above
2. Apply the fix
3. Test with `curl -I https://chat.weslr.de/` before and after authentication
4. Verify public weslr.de/app/ remains 404
5. Request redeploy approval with test results

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-08  
**Rollback Status:** Complete  
**Auth Status:** Preserved  
**Next Action:** Safe redeploy plan approval
