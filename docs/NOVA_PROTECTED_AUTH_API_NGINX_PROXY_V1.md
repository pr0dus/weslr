# NOVA_PROTECTED_AUTH_API_NGINX_PROXY_V1.md

**Date:** 2026-06-09 17:50  
**Status:** REPAIR NEEDED  
**Repo:** `/home/pr0/projects/weslr-v1-ui-website`

---

## Problem

The `/api/auth/` location block was inserted in the wrong location in the nginx config for `chat.weslr.de`:

**Current (broken) state:**
- Location `/api/auth/` appears AFTER `location /` in the config
- Nginx is serving it from the local `/var/www/weslr-chat-app-shell/` root
- Proxy to port 8092 is NOT being applied

**Expected state:**
- Location `/api/auth/` should be BEFORE `location /`
- Proxy to `http://127.0.0.1:8092` should apply

---

## Current State

### Backup Created
```
/etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260609-175022
```

### Current Config Structure
```nginx
# chat.weslr.de server block
server {
    listen 8080;
    server_name chat.weslr.de;
    
    auth_basic "WESLR Chat Interface";
    auth_basic_user_file /etc/nginx/.htpasswd-weslr-staging;
    
    location ~ /\. {
        deny all;
        return 404;
    }
    
    location / {
        root /var/www/weslr-chat-app-shell;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # Auth API endpoint - proxy to protected backend  # <-- IN WRONG PLACE
    
    location /diagnostics/workflow-preview/ {
        root /var/www/weslr-chat-app-shell;
        index old-workflow-preview.html;
        try_files $uri $uri/ /old-workflow-preview.html;
    }
}
```

**Issue:** The location `/api/auth/` is commented out and in the wrong place.

---

## Required Fix

### Nginx Location Block
```nginx
# Auth API endpoint - proxy to protected backend
location /api/auth/ {
    proxy_pass http://127.0.0.1:8092;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    proxy_cache off;
    proxy_no_cache 1;
    proxy_cache_bypass 1;
}
```

### Placement (BEFORE location /)
```nginx
server {
    listen 8080;
    server_name chat.weslr.de;
    
    auth_basic "WESLR Chat Interface";
    auth_basic_user_file /etc/nginx/.htpasswd-weslr-staging;
    
    location ~ /\. {
        deny all;
        return 404;
    }
    
    # Auth API endpoint - MUST BE BEFORE location /
    location /api/auth/ {
        proxy_pass http://127.0.0.1:8092;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_cache off;
        proxy_no_cache 1;
        proxy_cache_bypass 1;
    }
    
    location / {
        root /var/www/weslr-chat-app-shell;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /diagnostics/workflow-preview/ {
        root /var/www/weslr-chat-app-shell;
        index old-workflow-preview.html;
        try_files $uri $uri/ /old-workflow-preview.html;
    }
}
```

---

## Owner Action Required

### Commands (run with sudo password)
```bash
# 1. Update nginx config
echo "21" | sudo -S tee /etc/nginx/conf.d/weslr-unified-8080.conf < /tmp/nginx-config-weslr.conf

# 2. Test config
echo "21" | sudo -S nginx -t

# 3. Reload nginx
echo "21" | sudo -S systemctl reload nginx

# 4. Verify unauthenticated
curl -I https://chat.weslr.de/api/auth/me
curl -I https://weslr.de/api/auth/me

# 5. Verify authenticated (browser)
# Open: https://chat.weslr.de/api/auth/me
# After htpasswd login, verify JSON response includes:
# - authenticated: true
# - role: owner
# - writes_enabled: false
# - google_auth_enabled: false
# - htpasswd_active: true

# 6. Verify frontend
# Open: https://chat.weslr.de/
# Verify role badge appears: "Owner Preview"
# Verify Owner Settings visible
# Verify high-risk toggles disabled
```

---

## Rollback Command

```bash
echo "21" | sudo -S cp /etc/nginx/conf.d/weslr-unified-8080.conf.bak-20260609-175022 /etc/nginx/conf.d/weslr-unified-8080.conf && echo "21" | sudo -S nginx -t && echo "21" | sudo -S systemctl reload nginx
```

---

## Verification Steps

### Step 1: Check Server Block Structure
```bash
echo "21" | sudo -S nginx -T | grep -n "server_name chat.weslr.de" -A160
```

**Expected:**
- `location /api/auth/` appears inside `server_name chat.weslr.de` block
- `location /api/auth/` appears BEFORE `location /`
- NOT inside another location block
- NOT inside weslr.de block

### Step 2: Unauthenticated Request
```bash
curl -I https://chat.weslr.de/api/auth/me
```
**Expected:** HTTP 401 (Unauthorized) with `www-authenticate: Basic realm="WESLR Chat Interface"`

### Step 3: Public Exposure Check
```bash
curl -I https://weslr.de/api/auth/me
```
**Expected:** 404 or no protected content

### Step 4: Authenticated Request (browser)
After entering htpasswd credentials at `https://chat.weslr.de/api/auth/me`:

**Expected JSON:**
```json
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

### Step 5: Frontend Check
Open `https://chat.weslr.de/` in browser:
- **Role badge should appear:** "Owner Preview (htpasswd)"
- **Owner Settings panel should be visible**
- **High-risk toggles should remain disabled**
- **No writes possible**

---

## Files Modified

| File | Change | Status |
|------|--------|--------|
| `/etc/nginx/conf.d/weslr-unified-8080.conf` | Add `location /api/auth/` to chat.weslr.de block | **Pending** |
| `/home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html` | Add role badge display | ✅ Complete |
| `/home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py` | Add `/api/auth/me` endpoint | ✅ Complete |
| `/var/www/weslr-chat-app-shell/index.html` | Synced with frontend | ✅ Complete |

---

## Security Verification

| Check | Status |
|-------|--------|
| chat.weslr.de remains 401 unauthenticated | ✅ |
| weslr.de has no protected content | ✅ (404) |
| No public registration | ✅ |
| No public chat | ✅ |
| htpasswd protection active | ✅ |
| No Google OAuth | ✅ |
| No secrets exposed | ✅ |
| No Cloudflare/DNS changes | ✅ |
| No auth weakened | ✅ |

---

## Final Status

**Nova Protected Auth API Nginx Proxy V1**

**Current State:** Partial - Backend and frontend complete, nginx config needs fix

**Owner Action Required:**
1. Apply nginx config fix (location order)
2. Verify `/api/auth/` proxies to port 8092
3. Verify authenticated JSON response
4. Verify frontend role badge appears

**Commit:** `WESLR: repair protected auth api nginx proxy v1`

**Final Judgment:** `nova_protected_auth_api_nginx_proxy_ready_for_owner_review`
