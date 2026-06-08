# WESLR Owner Environment Settings Panel V1

**Date:** 2026-06-08  
**Author:** Nova (MAIN_DISPATCHER)  
**Status:** Design Complete - Backend Discovery Complete  
**Target:** `https://chat.weslr.de/settings/environment/`

---

## Executive Summary

Design the protected Owner Environment Settings panel for WESLR.

**Goal:** Expose WESLR runtime/capability modes as owner-controlled settings.

**Non-Goal (for now):** Do not wire real backend changes. Design only unless explicitly approved.

**Protection:** All settings behind `chat.weslr.de` auth. Public site `weslr.de` remains marketing/documentation only.

---

## Protected App Targets

| URL | Status | Auth |
|-----|--------|------|
| `https://chat.weslr.de/` | ✅ Protected | htpasswd |
| `https://chat.weslr.de/settings/environment/` | ✅ Planned | htpasswd |
| `https://weslr.de/` | ✅ Public | None |
| `https://weslr.de/app` | ✅ 404 | No protected content |

---

## Proposed Settings Panel Layout

### Route Structure

| Route | Purpose | Auth |
|-------|---------|------|
| `/settings/environment/` | Main environment settings panel | Protected |
| `/settings/environment/{setting}/` | Individual setting details (optional) | Protected |

### Visual Design

**Style:** Protected workspace app (not docs/wiki)

- Compact mobile layout
- Settings cards with toggle/buttons
- Clear colored risk badges
- Disabled/read-only until backend wired
- "UI only — not connected" for settings without backend

### Desktop Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  App Header (Protected)                                                    │
│  - WESLR logo, "Protected Workspace" title                                 │
│  - Status pill: "Protected • Internal"                                     │
├──────────────┬──────────────────────────────────────────────────────────────┤
│              │  Settings Panel                                              │
│  Sidebar     │  ┌──────────────────────────────────────────────────────┐  │
│  - Projects  │  │  Environment Settings                              │  │
│  - New proj  │  │                                                      │  │
│  - Project   │  │  Setting Cards:                                    │  │
│    list      │  │  1. UI Preview Mode (ON/OFF)                       │  │
│              │  │  2. Deterministic Protected Chat (ON/OFF)          │  │
│              │  │  3. Project Chat Runtime (OFF/Preview/Live)        │  │
│              │  │  4. Memory/Continuity (OFF/Read-only/Protected)    │  │
│              │  │  5. Evidence/RAG (OFF/Metadata/Protected)          │  │
│              │  │  6. Artifacts (OFF/Preview/Live)                  │  │
│              │  │  7. Model Provider (OFF/Owner-configured)          │  │
│              │  │  8. Tool Use (OFF/Approval/Live)                   │  │
│              │  │  9. Daemon (OFF/Observe/Suggest/Approved)          │  │
│              │  │  10. Self-Improvement (OFF/Proposal/Approval)      │  │
│              │  └──────────────────────────────────────────────────────┘  │
├──────────────┴──────────────────────────────────────────────────────────────┤
│  Bottom Composer (if chat active)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Top Bar (Project Name + Menu)                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Settings Header                                                           │
│  "Environment Settings"                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Setting Cards (scrollable)                                                │
│  - UI Preview Mode                                                         │
│  - Deterministic Chat                                                      │
│  - Project Chat Runtime                                                    │
│  - Memory/Continuity                                                       │
│  - Evidence/RAG                                                            │
│  - Artifacts                                                               │
│  - Model Provider                                                          │
│  - Tool Use                                                                │
│  - Daemon                                                                  │
│  - Self-Improvement                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Bottom Composer (fixed)                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Capability/Mode Table

| # | Setting | Default | Risk | Status | Owner Approval | Backend |
|---|---------|---------|------|--------|----------------|---------|
| 1 | UI Preview Mode | ON | LOW | ✅ Implemented | NO | - |
| 2 | Deterministic Chat | ON | LOW/MEDIUM | ✅ Implemented | NO | `/api/message` |
| 3 | Project Chat Runtime | OFF | MEDIUM | ❌ Not implemented | YES | New API |
| 4 | Memory/Continuity | OFF | MEDIUM/HIGH | ❌ Not implemented | YES | New API |
| 5 | Evidence/RAG | ON (backend) | MEDIUM/HIGH | ⚠️ Backend only | YES | New API |
| 6 | Artifacts | OFF | MEDIUM | ❌ Not implemented | YES | New API |
| 7 | Model Provider | ON | HIGH | ⚠️ Config only | YES | New UI |
| 8 | Tool Use | OFF | HIGH | ❌ Not implemented | YES | New API |
| 9 | Daemon/Proactive | OFF | HIGH | ⚠️ Backend only | YES | New API |
| 10 | Self-Improvement | OFF | VERY HIGH | ⚠️ Backend only | YES | New API |

---

## Existing Flags Found

### Configuration Variables

| Variable | Default | Description | File |
|----------|---------|-------------|------|
| `WESLR_LLM_ENABLED` | `true` | Enable LLM providers | `config.py` |
| `WESLR_LLM_PROVIDER` | `embedded` | LLM provider choice | `config.py` |
| `WESLR_LLM_MODEL` | `qwen2.5-0.5b-instruct-q5_k_m` | Model name | `config.py` |
| `WESLR_PROACTIVE_DAEMON_ENABLED` | `false` | Enable proactive daemon | `weslr/proactive_daemon.py` |
| `WESLR_PROACTIVE_INTERVAL_MINUTES` | `60` | Daemon interval | `weslr/proactive_daemon.py` |
| `WESLR_OPERATOR_ID` | `operator` | Operator identity | `weslr/proactive_daemon.py` |
| `WESLR_FRONTIER_DAEMON_ENABLED` | `false` | Enable frontier daemon | `weslr/frontier_daemon.py` |
| `WESLR_SEARXNG_ENABLED` | `false` | Enable SearXNG search | `weslr/searxng_search_adapter.py` |
| `WESLR_EVIDENCE_ROUTING_ENABLED` | `true` | Enable evidence routing | `config.py` |
| `WESLR_MEMORY_COMPACTION_COOLDOWN_SECONDS` | `86400` | Memory compaction | `config.py` |

### Autonomy Controls (Owner Workspace)

| File | Content | Purpose |
|------|---------|---------|
| `/home/pr0/plantdelux_lab/autonomy/ALLOW_AI_SESSIONS` | `NO` | Block AI sessions |
| `/home/pr0/plantdelux_lab/autonomy/PAUSE_NOVA` | `NO` | Allow Nova autonomy |
| `/home/pr0/plantdelux_lab/autonomy/ALLOW_OUTREACH` | `NO` | Block outreach |
| `/home/pr0/plantdelux_lab/autonomy/AUTONOMY_INCIDENTS.md` | Log | Autonomy incidents |

### WESLR Flags Analysis

| Flag Category | Status | Notes |
|---------------|--------|-------|
| **Model Provider** | ✅ Configured | LLM enabled, provider set |
| **Daemon** | ⚠️ Backend only | Proactive/Frontier daemons exist, disabled by default |
| **Evidence** | ⚠️ Backend only | Evidence routing enabled in config |
| **Memory** | ⚠️ Backend only | Memory compaction configured, no UI control |
| **Tools** | ❌ Not exposed | Tool execution exists, no UI toggle |
| **Self-Improvement** | ⚠️ Backend only | Proposals exist, no UI control |

---

## Missing Flags

| Setting | Flag Needed | Default | Status |
|---------|-------------|---------|--------|
| UI Preview Mode | `WESLR_UI_PREVIEW_MODE` | `true` | NEW |
| Deterministic Chat | `WESLR_PROTECTED_CHAT_ENABLED` | `true` | NEW |
| Project Chat Runtime | `WESLR_PROJECT_CHAT_ENABLED` | `false` | NEW |
| Memory/Continuity | `WESLR_MEMORY_ENABLED` | `false` | NEW |
| Evidence/RAG | `WESLR_EVIDENCE_UI_ENABLED` | `false` | NEW |
| Artifacts | `WESLR_ARTIFACTS_ENABLED` | `false` | NEW |
| Tool Use | `WESLR_TOOLS_ENABLED` | `false` | NEW |
| Daemon | `WESLR_DAEMON_MODE` | `OFF` | NEW |
| Self-Improvement | `WESLR_SELF_IMPROVEMENT_MODE` | `OFF` | NEW |

---

## Safe Default Settings

### Recommended Current Mode (Owner Review Only)

| Setting | Value | Reason |
|---------|-------|--------|
| UI Preview Mode | ON | Current behavior |
| Deterministic Chat | ON | Existing protected functionality |
| Project Chat Runtime | OFF | No backend yet |
| Memory/Continuity | OFF | No backend yet |
| Evidence/RAG | OFF | No backend UI yet |
| Artifacts | OFF | No backend yet |
| Model Provider | OFF | Prevent model calls |
| Tool Use | OFF | Prevent tool execution |
| Daemon/Proactive | OFF | Prevent autonomous behavior |
| Self-Improvement | OFF | Prevent self-mod |

### Owner Review Only Autonomy State

| Control | Value | Status |
|---------|-------|--------|
| `ALLOW_AI_SESSIONS` | `NO` | ✅ Blocks autonomous sessions |
| `PAUSE_NOVA` | `NO` | ⚠️ Allows owner sessions |
| `ALLOW_OUTREACH` | `NO` | ✅ Blocks outreach |

**Result:** NOVA blocked from autonomous sessions (by design) but owner can use protected features.

---

## Backend Adapter Requirements

### Protected Local Adapter

**File:** `/home/pr0/projects/weslr/tools/protected_owner_settings_adapter.py`

**Purpose:** Owner-only settings management behind `chat.weslr.de`

**Features:**
- Local-only, no network exposure
- Behind existing `chat.weslr.de` auth
- Read/modify config variables safely
- Return JSON with current states

**Endpoints Needed:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/settings/list` | GET | List all settings and states |
| `/api/settings/{key}/read` | GET | Read specific setting |
| `/api/settings/{key}/write` | POST | Write specific setting (owner only) |
| `/api/settings/reload` | POST | Reload WESLR config (restart) |

**Safe Settings for UI Control:**

| Setting | Read | Write | Restart Required | Risk |
|---------|------|-------|------------------|------|
| `WESLR_LLM_ENABLED` | ✅ | ✅ | YES | HIGH |
| `WESLR_PROACTIVE_DAEMON_ENABLED` | ✅ | ✅ | YES | HIGH |
| `WESLR_SEARXNG_ENABLED` | ✅ | ✅ | YES | MEDIUM |
| `WESLR_EVIDENCE_ROUTING_ENABLED` | ✅ | ✅ | YES | MEDIUM |
| `WESLR_MEMORY_COMPACTION_*` | ✅ | ✅ | YES | MEDIUM |

**Blocked from UI (Require Code Changes):**

| Setting | Reason |
|---------|--------|
| `WESLR_LLM_MODEL` | Requires file download |
| `OLLAMA_HOST` | Requires service restart |
| `WESLR_OPERATOR_ID` | Requires daemon restart |

---

## What Nova Can Build as UI Now

| Feature | Status | Notes |
|---------|--------|-------|
| Settings panel layout (desktop) | ✅ Ready | CSS, HTML structure |
| Settings panel layout (mobile) | ✅ Ready | CSS, responsive layout |
| Setting cards with risk badges | ✅ Ready | Visual design complete |
| Toggle buttons (disabled state) | ✅ Ready | Visual state only |
| "UI only — not connected" labels | ✅ Ready | Status indicators |
| Read-only setting display | ✅ Ready | Show config values |
| Owner autonomy status display | ✅ Ready | Show plantdelux autonomy flags |

**What's NOT built yet:**
- Backend wiring (all toggle actions)
- Real-time config reading (requires adapter)
- Real-time config writing (requires adapter)

---

## What Requires OCC/Core Support

| Feature | Backend Required | OCC Clarification Needed |
|---------|------------------|-------------------------|
| Project Chat Live | `/api/project/*` endpoints | API schema, auth, rate limits |
| Memory Live | `/api/project/:id/continuity` | Data model, persistence |
| Evidence Live | `/api/project/:id/evidence` | Retrieval logic |
| Artifacts Live | `/api/project/:id/artifacts` | Upload, storage, access |
| Tool Use Live | `/api/project/:id/tools` | Tool registry, execution |
| Daemon Live | `/api/project/:id/daemon` | Control interface |
| Self-Improvement Live | `/api/project/:id/improvements` | Proposal workflow |

---

## What Requires Explicit Owner Approval

| Feature | Owner Approval Required | Notes |
|---------|------------------------|-------|
| Enable LLM Provider | ✅ YES | Model provider access |
| Enable Tool Execution | ✅ YES | Tool safety review |
| Enable Daemon | ✅ YES | Autonomous behavior |
| Enable Self-Improvement | ✅ YES | Self-modification |
| Enable Project Chat Live | ✅ YES | Project data exposure |
| Enable Memory/Continuity | ✅ YES | Continuity data exposure |
| Enable Evidence/RAG Live | ✅ YES | Evidence data exposure |
| Enable Artifacts Live | ✅ YES | File upload/creation |
| Change Autonomy Flags | ✅ YES | Own workspace control |

---

## Validation Checklist

| Check | Status |
|-------|--------|
| Protected routes return 401 unauthenticated | ✅ |
| Public weslr.de/app returns 404 | ✅ |
| No legal page edits | ✅ |
| No Cloudflare/DNS changes | ✅ |
| No public registration | ✅ |
| No public chat | ✅ |
| No secrets exposed | ✅ |
| No daemon enabled | ✅ |
| No backend connected (except `/api/message`) | ✅ |
| Owner autonomy flags unchanged | ✅ |

---

## Commit Message

```
WESLR: design owner environment settings panel v1
```

---

## Final Judgment

**nova_owner_environment_settings_panel_ready_for_owner_review**

**Status:**
- ✅ Settings panel design complete
- ✅ Existing flags documented
- ✅ Missing flags identified
- ✅ Safe defaults established
- ✅ Backend adapter requirements defined
- ✅ Owner approval points identified
- ⏸️ Implementation pending owner approval

**Owner Action Required:**
1. Review settings panel design
2. Approve safe defaults for current mode
3. Review backend adapter requirements
4. Approve backend wiring for enabled features
5. Confirm autonomy flag values

**Recommended Next Lane:** Owner chooses:
- **UI Implementation** (settings panel, no backend)
- **Backend Adapter** (settings management)
- **Protected Project Chat** (full workspace functionality)
- **Responsive Mobile UX** (if not done yet)

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-08  
**Design Status:** Complete  
**Backend Discovery:** Complete  
**Safe Defaults:** Established  
**Implementation Status:** Pending owner approval  
