# Protected Owner Environment Settings UI and Mobile Patch V1

**Date:** 2026-06-08  
**Author:** Nova (MAIN_DISPATCHER)  
**Status:** Built and Deployed ✅  
**Target:** `https://chat.weslr.de/` (protected)

---

## Executive Summary

Built Phase 1 implementation:
1. Owner Environment Settings UI panel
2. Responsive mobile UX patch
3. All high-risk controls disabled (read-only preview)

**Goal:** Show WESLR's full capability structure behind auth, with clear owner-controlled settings, but all toggles disabled until backend approval.

---

## Files Changed

| File | Change |
|------|--------|
| `protected-preview/chat-app-shell/index.html` | Complete rewrite with settings panel + responsive UX |
| `/var/www/weslr-chat-app-shell/index.html` | Synced from repo |
| `docs/NOVA_PROTECTED_OWNER_ENVIRONMENT_SETTINGS_UI_AND_MOBILE_PATCH_V1.md` | This report |

---

## UI Settings Implemented

### Settings Panel Route

- **Path:** `/settings/environment/`
- **Access:** Click Settings icon in mobile bottom bar or Settings tab

### Capability Settings (All Read-Only)

| # | Setting | Current State | Risk | Toggle | Backend Status |
|---|---------|---------------|------|--------|----------------|
| 1 | UI Preview Mode | Active | LOW | Enabled (read-only) | UI only |
| 2 | Deterministic Chat | Active | LOW/MEDIUM | Enabled (read-only) | Protected route |
| 3 | Project Chat Runtime | Off | MEDIUM | Disabled | Backend adapter required |
| 4 | Memory / Continuity | Off | MEDIUM/HIGH | Disabled | Scoped approval required |
| 5 | Evidence / RAG | Off | MEDIUM/HIGH | Disabled | Protected retrieval required |
| 6 | Artifacts | Off | MEDIUM | Disabled | Backend wiring required |
| 7 | Model Provider | Off | HIGH | Disabled | Owner-configured required |
| 8 | Tool Use | Off | HIGH | Disabled | Approval-gated only |
| 9 | Daemon / Proactive Mode | Off | HIGH | Disabled | Separate approval required |
| 10 | Self-Improvement Loop | Off | VERY HIGH | Disabled | Proposal-only only |

### Disabled Controls

| Control | Reason |
|---------|--------|
| All toggles | Backend not connected (UI only preview) |
| Project creation | Backend adapter required |
| Chat history | Backend adapter required |
| Context/Artifact/Evidence | Backend adapter required |
| Settings changes | Owner approval required |

### Status Labels Used

| Label | When |
|-------|------|
| **Active** | Setting enabled (only UI Preview Mode, Deterministic Chat) |
| **Off** | Setting disabled (all others) |
| **UI only** | Frontend only, no backend |
| **Backend not connected** | Feature needs backend |
| **Backend adapter required** | New adapter needed |
| **Scoped approval required** | Context-specific approval |
| **Protected retrieval required** | Evidence adapter needed |
| **Owner-configured required** | Model provider config needed |
| **Approval-gated only** | Requires approval flow |
| **Separate approval required** | High-risk, separate review |

---

## Responsive Mobile Changes

### Viewport Handling

- **Desktop:** `min-height: 100vh`
- **Mobile:** `min-height: 100dvh` + `padding-bottom: env(safe-area-inset-bottom)`

### Header Height

| Device | Height |
|--------|--------|
| Desktop | 56px |
| Mobile | 48px |

### Layout Improvements

| Area | Before | After |
|------|--------|-------|
| Mobile header | 56px | 48px |
| App shell | Fixed 100vh - 56px | Flexible with safe-area |
| Empty state | Large center | Compact, above composer |
| Composer | Fixed at bottom | Protected by safe-area |
| Action buttons | Crowded | Wrapped, compact 40px |
| Bottom tabs | Clipped | Scrollable, compact |

### Mobile-Specific Features

| Feature | Implementation |
|---------|----------------|
| Settings panel | Full-screen overlay |
| Mobile tabs | Scrollable bottom tabs |
| Mobile drawer | Slide-out drawer (toggle button) |
| Main chat | Shows/hidden by settings state |
| Composer | Hidden in settings mode |

---

## Safe Defaults Used

| Setting | Value | Rationale |
|---------|-------|-----------|
| UI Preview Mode | ON | Current behavior |
| Deterministic Chat | ON | Existing protected `/api/message` |
| Project Chat Runtime | OFF | No backend yet |
| Memory/Continuity | OFF | No backend yet |
| Evidence/RAG | OFF | No backend yet |
| Artifacts | OFF | No backend yet |
| Model Provider | OFF | Prevent model calls |
| Tool Use | OFF | Prevent tool execution |
| Daemon | OFF | Prevent autonomous behavior |
| Self-Improvement | OFF | Prevent self-modification |

---

## Daemon Status

| Aspect | Status |
|--------|--------|
| Daemon enabled | ❌ NO |
| Daemon toggle | OFF (disabled) |
| Daemon label | "requires separate approval" |
| Daemon auto-start | ❌ NO |
| Daemon exposed | ❌ Only after approval |

---

## Backend Not Connected Statement

**Current State:** Backend not connected.

**What Works:**
- UI shell (settings cards, toggles, layout)
- Project list (mock data)
- Chat composer (UI-only, local preview only)
- Toast notifications
- Responsive mobile layout

**What Doesn't Work (Yet):**
- Project creation (requires `/api/project/create`)
- Chat history (requires `/api/project/:id/chat`)
- Context/Artifact/Evidence (requires adapters)
- Settings persistence (requires `/api/settings/write`)
- Backend adapter for settings (requires new API)

---

## Public Exposure Check

| URL | Status | Result |
|-----|--------|--------|
| `https://chat.weslr.de/` | 401 | Protected (requires auth) |
| `https://chat.weslr.de/settings/environment/` | 401 | Protected (requires auth) |
| `https://weslr.de/app` | 404 | No protected content |
| `https://weslr.de/` | 200 | Public site (unchanged) |

---

## Protected Route Check

| Check | Status |
|-------|--------|
| `auth_basic` active | ✅ Yes |
| `htpasswd` protection | ✅ Yes |
| `chat.weslr.de` protected | ✅ Yes |
| `weslr.de/app` protected | ✅ Yes (404) |
| No public registration | ✅ Yes |
| No public chat | ✅ Yes |

---

## Next Recommended Backend Lanes

| # | Lane | Purpose | Priority |
|---|------|---------|----------|
| 1 | Wire `/api/message` to chat | Deterministic chat integration | HIGH |
| 2 | Add project list/create adapter | Project management API | HIGH |
| 3 | Add project chat history/context adapter | Chat history with context | MEDIUM |
| 4 | Add artifacts/evidence/memory adapters | Storage and retrieval | MEDIUM |
| 5 | Add settings read API | Read current WESLR config | LOW |
| 6 | Add settings write API | Write settings (owner approval only) | HIGH (after approval) |

### Backend Adapter Requirements

**File:** `/home/pr0/projects/weslr/tools/protected_owner_settings_adapter.py`

**Endpoints Needed:**
- `GET /api/settings/list` - List all settings and states
- `GET /api/settings/{key}/read` - Read specific setting
- `POST /api/settings/{key}/write` - Write specific setting (owner only)
- `POST /api/settings/reload` - Reload WESLR config (restart)

**Safe for UI Control:**
- `WESLR_LLM_ENABLED` - Read/Write (restart required)
- `WESLR_PROACTIVE_DAEMON_ENABLED` - Read/Write (restart required)
- `WESLR_SEARXNG_ENABLED` - Read/Write (restart required)

---

## Validation Checklist

| Check | Status |
|-------|--------|
| `git diff --check` | ✅ Pass |
| `git status --short` | ✅ Clean |
| `https://chat.weslr.de/` returns 401 | ✅ Yes |
| After auth, app loads | ✅ Yes (owner verified) |
| Mobile layout improved | ✅ Yes |
| Settings panel visible | ✅ Yes |
| High-risk toggles disabled | ✅ Yes |
| Daemon shown as OFF | ✅ Yes |
| `https://weslr.de/app` returns 404 | ✅ Yes |
| No legal pages changed | ✅ Yes |
| No Cloudflare/DNS changes | ✅ Yes |
| No public registration | ✅ Yes |
| No public chat | ✅ Yes |
| No daemon started | ✅ Yes |
| No model provider enabled | ✅ Yes |
| No settings written | ✅ Yes |

---

## Commit Message

```
WESLR: build protected owner environment settings ui and mobile patch v1
```

---

## Delivery

| Item | Status |
|------|--------|
| Protected URL | `https://chat.weslr.de/` |
| Settings panel | `/settings/environment/` |
| Mobile layout | Compact, safe-area aware |
| Command proof | Nginx reload confirmed |
| No loose files | ✅ Clean |

---

## Final Judgment

**nova_owner_environment_settings_ui_and_mobile_patch_ready_for_owner_review**

**Status:**
- ✅ Settings panel UI built
- ✅ Responsive mobile UX applied
- ✅ All toggles disabled (read-only preview)
- ✅ Backend not connected labels shown
- ✅ Daemon shown as OFF
- ✅ Public exposure check passed
- ⏸️ Backend wiring pending owner approval

**Owner Action Required:**
1. Review settings panel at `chat.weslr.de/settings/environment/`
2. Review responsive mobile layout
3. Approve backend adapter design
4. Approve backend wiring for enabled features

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-08  
**UI Status:** Built and deployed  
**Mobile Status:** Optimized  
**Backend Status:** Not connected (UI only)  
**Daemon Status:** OFF (disabled)  
