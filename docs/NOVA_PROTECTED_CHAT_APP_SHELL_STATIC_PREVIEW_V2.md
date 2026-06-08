# Protected WESLR Chat App Shell Static Preview V2

**Date:** 2026-06-08  
**Author:** Nova (MAIN_DISPATCHER)  
**Status:** Report Draft (Nginx Changes Pending)  
**Target:** `chat.weslr.de/` (protected workspace)

---

## Current Protected URL State

| URL | Backend | Auth | Status |
|-----|---------|------|--------|
| `https://chat.weslr.de/` | Port 8092 | Password (htpasswd) | Old workflow preview |
| `https://chat.weslr.de/app/` | Port 8092 | Password (htpasswd) | 404 (no content) |
| `https://weslr.de/` | Port 8089 | None | PlantDelux site |
| `https://weslr.de/app/` | Port 8089 | None | 404 (no content) |

---

## Current Backend Content

### Port 8092 (chat.weslr.de/)

**Content:** "WESLR Protected Workflow Preview"  
**Features:**
- "No Model Provider Active" warning
- Prompt list (8 prompts)
- Textarea + Send/Clear buttons
- Response display with path/confidence badges

**This is the main page served by `chat.weslr.de/`**

---

## Required Changes

### 1. Replace Main Protected Page

**Current:** Old workflow preview at `chat.weslr.de/`  
**Target:** New app shell (protected workspace layout)

**New Features:**
- Desktop layout: sidebar + center + right panel + bottom composer
- Mobile layout: drawer + top bar + fixed composer
- Project list + New Project button
- Protected status badges
- Backend-not-connected labels
- Empty state with starter prompts

### 2. Move Old Workflow to Diagnostics

**Old workflow preview path:** `chat.weslr.de/diagnostics/workflow-preview/`  
**Purpose:** Internal testing/diagnostic reference  
**Auth:** Same password protection (htpasswd)

### 3. Nginx Configuration Changes Required

**File:** `/etc/nginx/conf.d/weslr-unified-8080.conf`

**Current:**
```nginx
location / {
    proxy_pass http://127.0.0.1:8092;
}
```

**Proposed:**
```nginx
location / {
    # New app shell
    alias /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html;
    index index.html;
}

location /diagnostics/workflow-preview/ {
    # Old workflow preview (diagnostics)
    alias /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/diagnostics/old-workflow-preview.html;
    index old-workflow-preview.html;
}
```

**Alternative (if proxy_pass required):**
```nginx
location / {
    proxy_pass http://127.0.0.1:8090;  # New port for app shell
}

location /diagnostics/workflow-preview/ {
    proxy_pass http://127.0.0.1:8091;  # Port for diagnostics
}
```

---

## Security Verification

### Public weslr.de/app/
**Status:** `404 Not Found`  
**Security:** ✅ No protected content exposed

### Protected chat.weslr.de/
**Status:** `401 Authorization Required` (unauthenticated)  
**Security:** ✅ Protected by htpasswd

### Protected chat.weslr.de/diagnostics/
**Status:** `401 Authorization Required` (unauthenticated)  
**Security:** ✅ Protected by same htpasswd

---

## Desktop Layout Summary

### Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  App Header (Protected)                                                    │
│  - WESLR logo, "Protected Workspace" title                                 │
│  - Status pill: "Protected • Internal"                                     │
├──────────────┬──────────────────────────────────────────────────────────────┤
│  Sidebar     │  Center                                                      │
│  - Projects  │  Active Project Header                                       │
│  - New proj  │  Empty State / Chat Messages                                 │
│  - Project   │  Bottom Composer (fixed)                                     │
│    list      │                                                              │
├──────────────┴──────────────────────────────────────────────────────────────┤
│  Right Panel (Options/Artifacts/Evidence)                                  │
│  - Project Options                                                         │
│  - Artifacts                                                               │
│  - Evidence/Context                                                        │
│  - Memory/Continuity                                                       │
│  - Settings                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Status Labels

| Component | Label |
|-----------|-------|
| App header | Protected • Internal |
| Active project | UI Preview |
| Project options | Protected • Backend blocked |
| Artifacts | Requires approval |
| Evidence | Available |
| Memory | UI Preview |
| Settings | Backend blocked |
| Chat composer | Preview only — backend not connected |

---

## Mobile Layout Summary

| Component | Mobile Adaptation |
|-----------|-------------------|
| Sidebar | Slide-out drawer |
| Right panel | Hidden (bottom sheet if needed) |
| Top bar | Project name + menu button |
| Center | Full-width chat area |
| Composer | Fixed bottom, full-width textarea |
| Send button | Visible |
| Options | Bottom sheet/drawer |

---

## Backend Connection Status

### Backend-Connected

| Component | Endpoint | Status |
|-----------|----------|--------|
| **NONE** | — | Backend not connected |

### UI-Only (Mock Data)

| Component | Status |
|-----------|--------|
| Project list | Mock data |
| Project creation | UI-only |
| Chat messages | Mock welcome |
| Composer inputs | Disabled |
| Right panel content | Labels only |

---

## Owner Approval Items

| Action | Approval Required |
|--------|------------------|
| Update nginx config | ✅ Yes |
| Serve new app shell from chat.weslr.de/ | ✅ Yes |
| Add `/diagnostics/workflow-preview/` route | ✅ Yes |
| Test protected routes after changes | ✅ Yes |
| Production deployment | ✅ Yes |

---

## Backend Clarification Needed

| Endpoint | Missing Component | Clarification Needed |
|----------|-------------------|---------------------|
| `/api/project/create` | Backend handler | Schema, auth, rate limits |
| `/api/project/list` | Backend handler | Pagination, filters |
| `/api/project/:id/chat` | Backend handler | Message format, errors |
| `/api/project/:id/artifacts` | Backend handler | File types, size limits |
| `/api/project/:id/context` | Backend handler | Data schema, persistence |

---

## Final Validation Commands

### Git Status

```bash
cd /home/pr0/projects/weslr-v1-ui-website
git status --short
git diff --check
```

### Protected Route Check

```bash
curl -I https://chat.weslr.de/ || true
curl -I https://chat.weslr.de/app/ || true
curl -I https://weslr.de/app/ || true
```

### Expected Results

| URL | Expected Status |
|-----|-----------------|
| `https://weslr.de/app/` | 404 (no protected content) |
| `https://chat.weslr.de/` | 401 (protected, requires auth) |
| `https://chat.weslr.de/diagnostics/` | 401 (protected, requires auth) |

---

## Commit Message

```
WESLR: update protected chat app shell v2, add diagnostics route
```

---

## Final Judgment

**nova_protected_chat_app_shell_static_preview_v2_report_ready_for_owner_review**

**Note:** Nginx configuration changes required before deploying new app shell to `chat.weslr.de/`.

---

**Document Version:** 2.0  
**Last Updated:** 2026-06-08  
**Backend Status:** Not Connected (Mock Only)  
**Nginx Status:** Pending Owner Approval
