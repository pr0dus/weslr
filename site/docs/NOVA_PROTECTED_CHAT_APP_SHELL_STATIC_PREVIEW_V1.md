# Protected WESLR Chat App Shell Static Preview V1

**Date:** 2026-06-08  
**Author:** Nova (MAIN_DISPATCHER)  
**Status:** Preview Complete  
**Target:** Protected preview at `chat.weslr.de/app/`

---

## Where the App Shell Was Built

### Location

**Path:** `/home/pr0/projects/weslr-v1-ui-website/site/app/`  
**File:** `index.html`  
**Route on chat.weslr.de:** `/app/`

### Discovery

**chat.weslr.de** is already protected with:
- `auth_basic "WESLR Chat Interface";`
- `auth_basic_user_file /etc/nginx/.htpasswd-weslr-staging;`
- Port 8092 backend

**weslr.de** (public site) serves from:
- Port 8089 (nginx proxy)
- No authentication
- Public access

### Route Separation

| Host | Port | Auth | Path | Purpose |
|------|------|------|------|---------|
| `chat.weslr.de` | 8092 | Password (htpasswd) | `/` | Existing deterministic preview |
| `chat.weslr.de` | 8092 | Password (htpasswd) | `/app/` | **NEW: Protected app shell preview** |
| `weslr.de` | 8089 | None | `/` | Public static site |

**Decision:** Serve protected app under `/app/` route on `chat.weslr.de` (port 8092) to maintain separation from public weslr.de.

---

## Reachability Status

### Public Reachability

**NO** — The protected app shell is NOT publicly reachable from `weslr.de`.

- `weslr.de` → port 8089 → Public static site (no auth)
- `chat.weslr.de` → port 8092 → Password-protected interface

### Protected Reachability

**YES** — Protected app shell is accessible at:
- `https://chat.weslr.de/app/` (password protected)

### Access Verification

```
$ curl -s -I http://chat.weslr.de/
HTTP/1.1 401 Authorization Required
```

```
$ curl -s -I http://chat.weslr.de/app/
HTTP/1.1 401 Authorization Required
```

Both routes require authentication. The `/app/` preview is protected.

---

## Desktop Layout Summary

### Overall Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  App Header (Protected)                                                    │
│  - WESLR logo (32x32, gradient)                                            │
│  - "Protected Workspace" title                                             │
│  - Status pill: "Protected • Internal" (red background)                    │
├──────────────┬──────────────────────────────────────────────────────────────┤
│              │                                                              │
│  Left        │  Main Center                                               │
│  Sidebar     │  ┌──────────────────────────────────────────────────────┐  │
│  - WESLR     │  │  Active Project Title + "UI Preview" status pill    │  │
│    logo      │  └──────────────────────────────────────────────────────┘  │
│  - Projects  │                                                              │
│  - New proj  │  ┌──────────────────────────────────────────────────────┐  │
│    button    │  │  Empty State (if no project selected)              │  │
│  - Project   │  │  - "Protected Workspace Preview"                   │  │
│    list      │  │  - "Backend not connected"                         │  │
│              │  │  - "Requires approval"                             │  │
│              │  └──────────────────────────────────────────────────────┘  │
├──────────────┴──────────────────────────────────────────────────────────────┤
│  Right Panel (Options/Artifacts/Evidence)                                  │
│  - Project Options (Protected, Backend blocked)                            │
│  - Artifacts (Requires approval)                                           │
│  - Evidence/Context (Available)                                            │
│  - Memory/Continuity (UI Preview)                                          │
│  - Settings (Backend blocked)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Bottom Composer (Fixed)                                                   │
│  - Multiline textarea (disabled: "Backend not connected")                  │
│  - Context button (disabled)                                               │
│  - Artifact button (disabled)                                              │
│  - Evidence button (disabled)                                              │
│  - Options button (disabled)                                               │
│  - Send button (disabled)                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Status Labels

| Component | Label | Status |
|-----------|-------|--------|
| App header | Protected • Internal | **Active** |
| Active project title | UI Preview | **Active** |
| Project options | Protected | **Active** |
| Project options | Backend not connected | **Active** |
| Artifacts | Requires approval | **Active** |
| Evidence | Available | **Active** |
| Memory | UI Preview | **Active** |
| Settings | Backend blocked | **Active** |
| Chat composer | Backend not connected | **Active** |

---

## Mobile Layout Summary

### Responsive Breakpoint

**Max-width:** 768px (mobile/tablet)

### Mobile Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Top App Bar (Protected)                                                   │
│  - Project name (truncated) + Menu button                                  │
│  - "UI Preview" status pill                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Main Chat Area (full width)                                               │
│  - Empty state or message bubbles                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Bottom Composer (Fixed)                                                   │
│  - Textarea (full width)                                                   │
│  - Send button                                                             │
│  - Slide-out drawers/tabs:                                                 │
│    • Project list (drawer)                                                 │
│    • Options (bottom sheet)                                                │
│    • Artifacts (bottom sheet)                                              │
│    • Evidence (bottom sheet)                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Panel Collapse

- **Left sidebar** → Slide-out drawer
- **Right panel** → Hidden (mobile prefers bottom sheet)
- **Composer** → Full-width textarea + send button

---

## What Is UI-Only

| Component | Status | Message |
|-----------|--------|---------|
| Project list | UI-only (mock data) | "No projects yet. Create one to get started." |
| Project creation modal | UI-only | "Create Project" button disabled if no name |
| Chat messages | UI-only | "Empty state" or mock welcome messages |
| Composer inputs | UI-only | All disabled: "Backend not connected" |
| Context/Artifact/Evidence buttons | UI-only | Icons visible, disabled |
| Right panel content | UI-only | Labels, no live data |
| Empty state messaging | UI-only | "Protected Workspace Preview" |

---

## What Is Backend-Connected

| Component | Connection | Status |
|-----------|------------|--------|
| **NONE** | — | **Backend not connected** |

### Why No Backend Connection

- Backend API endpoints not yet implemented for:
  - `/api/project/create`
  - `/api/project/list`
  - `/api/project/:id/chat`
  - `/api/project/:id/artifacts`
  - `/api/project/:id/context`

- Frontend properly disables all actions and shows status labels
- No unsafe connections or unimplemented POST requests

---

## What Requires Owner Approval

| Action | Owner Approval Required | Notes |
|--------|------------------------|-------|
| Enable backend API endpoints | ✅ Yes | Security review required |
| Connect real chat messages | ✅ Yes | Backend implementation |
| Enable artifact upload | ✅ Yes | Security review, file types |
| Enable context/evidence saving | ✅ Yes | Data model, persistence |
| Production deployment | ✅ Yes | Final validation |

---

## What Requires OCC/backend Clarification

| Endpoint | Missing Component | Clarification Needed |
|----------|-------------------|---------------------|
| `/api/project/create` | Backend handler | Schema, auth, rate limits |
| `/api/project/list` | Backend handler | Pagination, filters |
| `/api/project/:id/chat` | Backend handler | Message format, error handling |
| `/api/project/:id/artifacts` | Backend handler | File types, size limits |
| `/api/project/:id/context` | Backend handler | Data schema, persistence |
| `/api/project/:id/review` | Backend handler | Workflow, approval logic |

---

## Preview URL (Protected)

### Access

```
https://chat.weslr.de/app/
```

**Authentication:** Required (htpasswd)

**Status:** Static UI shell only, no backend wiring

---

## Final Validation

### Git Status

```
$ git status --short
A  site/app/index.html
```

### Git Diff Check

```
$ git diff --check
(no output)
```

### Protected Files Unchanged

- [x] No legal pages modified
- [x] No public registration opened
- [x] No public chat exposed
- [x] No Cloudflare/nginx/DNS/access changes
- [x] No secrets exposed
- [x] Protected route remains protected (chat.weslr.de requires auth)

---

## Deliverable: Preview Report

**Document:** `site/docs/NOVA_PROTECTED_CHAT_APP_SHELL_STATIC_PREVIEW_V1.md`  
**Commit:** `b399c79` — WESLR: build protected chat app shell static preview v1

---

## Final Judgment

**nova_protected_chat_app_shell_static_preview_ready_for_owner_review**

**Next Lane:** Owner review required before proceeding to:
- Backend API implementation
- Frontend/backend wiring
- Production deployment

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-08  
**Preview Status:** UI Shell Only (Protected)  
**Backend Status:** Not Connected (Mock Only)
