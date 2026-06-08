# WESLR Owner Environment Settings and Full Capability Activation Panel V1

**Date:** 2026-06-08  
**Author:** Nova (MAIN_DISPATCHER)  
**Status:** Design Complete - Backend Discovery Pending  
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

## Required Settings Panel Structure

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

**Layout per setting card:**

```
┌─────────────────────────────────────────────────────────────┐
│  Setting Title + Toggle (or Button)                        │
│                                                             │
│  Current State: OFF / Preview / Protected Live             │
│                                                             │
│  What it enables:                                          │
│  - Brief description                                       │
│                                                             │
│  Risk Level: [LOW] / [MEDIUM] / [HIGH] / [VERY HIGH]      │
│                                                             │
│  Public Exposure Risk:                                      │
│  - [NONE] / [LOW] / [MEDIUM] / [HIGH]                     │
│                                                             │
│  Requires Restart/Reload: [YES] / [NO]                     │
│                                                             │
│  Owner Approval Required: [YES] / [NO]                     │
│                                                             │
│  Last Changed: [timestamp placeholder]                     │
│                                                             │
│  Rollback Status: [placeholder]                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Required Capability Controls

### 1. UI Preview Mode

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_UI_PREVIEW_MODE` |
| **Default** | `true` (ON) |
| **Description** | Local frontend preview behavior only |
| **Risk** | LOW |
| **Public Exposure** | NONE |
| **Restart Required** | NO |
| **Owner Approval** | NO |
| **Status** | Implemented (current state) |

**Controls:**
- Toggle: ON / OFF
- ON → Show protected app shell with UI-only behavior
- OFF → Show documentation-only fallback

---

### 2. Deterministic Protected Chat

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_PROTECTED_CHAT_ENABLED` |
| **Default** | `true` (ON) |
| **Description** | Routes messages to deterministic protected handler |
| **Backend** | `/api/message` → `dispatch_deterministic_handler` |
| **Risk** | LOW/MEDIUM |
| **Public Exposure** | NONE (protected route only) |
| **Restart Required** | NO |
| **Owner Approval** | NO |
| **Status** | Implemented (port 8092) |

**Controls:**
- Toggle: ON / OFF
- ON → Messages go to deterministic handler
- OFF → Show "protected chat disabled" message

**Backend Endpoint:**
- `POST /api/message` → Deterministic response
- NO model calls
- NO external API calls

---

### 3. Project Chat Runtime

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_PROJECT_CHAT_ENABLED` |
| **Default** | `false` (OFF) |
| **Description** | Project creation, selection, chat history, context |
| **Status** | NOT YET IMPLEMENTED |
| **Risk** | MEDIUM |
| **Public Exposure** | NONE (protected only) |
| **Restart Required** | NO |
| **Owner Approval** | YES |
| **Backend Needed** | New API endpoints |

**Controls:**
- Toggle: OFF / Preview / Protected Live
- OFF → No project operations
- Preview → Mock project creation, UI-only
- Protected Live → Full project ops (requires backend)

**Backend Needed:**
- `/api/project/create`
- `/api/project/list`
- `/api/project/:id/chat`
- `/api/project/:id/context`

**Status:** Backend wiring required before Protected Live

---

### 4. Memory / Continuity

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_MEMORY_ENABLED` |
| **Default** | `false` (OFF) |
| **Description** | Project/user continuity state |
| **Status** | NOT YET IMPLEMENTED IN UI |
| **Risk** | MEDIUM/HIGH |
| **Public Exposure** | NONE |
| **Restart Required** | YES |
| **Owner Approval** | YES |
| **Backend Needed** | Continuity API |

**Controls:**
- Toggle: OFF / Read-only / Protected write
- OFF → No continuity
- Read-only → View continuity snapshots
- Protected write → Save/restore continuity (requires backend)

**Backend Needed:**
- `/api/project/:id/continuity`
- `/api/project/:id/context/save`
- `/api/project/:id/context/restore`

**Status:** Backend wiring required

---

### 5. Evidence / RAG

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_EVIDENCE_ROUTING_ENABLED` |
| **Default** | `true` (ON) |
| **Description** | Source-grounded retrieval/evidence packets |
| **Backend** | `WESLR_EVIDENCE_ROUTING_ENABLED` env var |
| **Status** | Implemented (backend) |
| **Risk** | MEDIUM/HIGH |
| **Public Exposure** | NONE |
| **Restart Required** | YES |
| **Owner Approval** | YES |
| **Backend Needed** | Evidence API for UI |

**Controls:**
- Toggle: OFF / Metadata-only / Protected retrieval
- OFF → No evidence routing
- Metadata-only → Show evidence metadata
- Protected retrieval → Retrieve evidence (requires backend)

**Backend Needed:**
- `/api/project/:id/evidence`
- `/api/project/:id/evidence/search`

**Status:** Backend API needed for UI control

---

### 6. Artifacts

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_ARTIFACTS_ENABLED` |
| **Default** | `false` (OFF) |
| **Description** | Structured outputs, artifact metadata, owner preview, validation |
| **Status** | NOT YET IMPLEMENTED IN UI |
| **Risk** | MEDIUM |
| **Public Exposure** | NONE |
| **Restart Required** | NO |
| **Owner Approval** | YES |
| **Backend Needed** | Artifacts API |

**Controls:**
- Toggle: OFF / Preview / Protected creation
- OFF → No artifact operations
- Preview → Mock artifact upload, UI-only
- Protected Live → Full artifacts (requires backend)

**Backend Needed:**
- `/api/project/:id/artifacts`
- `/api/project/:id/artifacts/upload`
- `/api/project/:id/artifacts/list`

**Status:** Backend wiring required

---

### 7. Model Provider

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_LLM_ENABLED` |
| **Default** | `true` (ON) |
| **Description** | Optional external/local model provider |
| **Backend** | `WESLR_LLM_ENABLED`, `WESLR_LLM_PROVIDER`, `WESLR_LLM_MODEL` env vars |
| **Status** | Implemented |
| **Risk** | HIGH |
| **Public Exposure** | NONE |
| **Restart Required** | YES |
| **Owner Approval** | YES |
| **Backend Needed** | Model provider configuration UI |

**Controls:**
- Toggle: OFF / Owner-configured
- OFF → Deterministic only (no LLM)
- Owner-configured → Choose provider (Ollama/OpenAI/etc.)

**Environment Variables:**
- `WESLR_LLM_ENABLED=true/false`
- `WESLR_LLM_PROVIDER=ollama/openai/embedded`
- `WESLR_LLM_MODEL=...`
- `OLLAMA_HOST=http://127.0.0.1:11434`

**UI Requirements:**
- Show current provider state
- Show "no provider configured" if OFF
- Configure provider details (URL, model, key if external)

**Status:** Backend exists, UI needed

---

### 8. Tool Use

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_TOOLS_ENABLED` |
| **Default** | `false` (OFF) |
| **Description** | Tool execution lanes |
| **Status** | NOT YET IMPLEMENTED IN UI |
| **Risk** | HIGH |
| **Public Exposure** | NONE |
| **Restart Required** | YES |
| **Owner Approval** | YES |
| **Backend Needed** | Tools API |

**Controls:**
- Toggle: OFF / Approval required / Protected live
- OFF → No tool execution
- Approval required → Show tools, require approval
- Protected live → Execute tools automatically (requires backend)

**Backend Needed:**
- `/api/project/:id/tools`
- `/api/project/:id/tools/execute`

**Status:** Backend wiring required

---

### 9. Daemon / Proactive Mode

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_PROACTIVE_DAEMON_ENABLED` |
| **Default** | `false` (OFF) |
| **Description** | Background observation/suggestion loop |
| **Backend** | `WESLR_PROACTIVE_DAEMON_ENABLED`, `WESLR_PROACTIVE_INTERVAL_MINUTES` |
| **Status** | Implemented (backend) |
| **Risk** | HIGH |
| **Public Exposure** | NONE |
| **Restart Required** | YES |
| **Owner Approval** | YES |
| **Backend Needed** | Daemon control UI |

**Controls:**
- Toggle: OFF / Observe only / Suggest only / Approved actions
- OFF → No daemon
- Observe only → See daemon status
- Suggest only → Daemon suggests, owner decides
- Approved actions → Daemon executes (requires backend)

**Environment Variables:**
- `WESLR_PROACTIVE_DAEMON_ENABLED=true/false`
- `WESLR_PROACTIVE_INTERVAL_MINUTES=60`
- `WESLR_OPERATOR_ID=operator`

**Status:** Backend exists, UI needed

---

### 10. Self-Improvement Loop

| Field | Value |
|-------|-------|
| **Setting** | `WESLR_SELF_IMPROVEMENT_ENABLED` |
| **Default** | `false` (OFF) |
| **Description** | WESLR proposes improvements; implementation approval-gated |
| **Backend** | `SELF_MOD_PROPOSALS_PATH` (file) |
| **Status** | Implemented (backend) |
| **Risk** | VERY HIGH |
| **Public Exposure** | NONE |
| **Restart Required** | NO |
| **Owner Approval** | YES (for any enabled state) |
| **Backend Needed** | Self-improvement UI |

**Controls:**
- Toggle: OFF / Proposal only / Approval-gated
- OFF → No self-improvement
- Proposal only → Show proposals, no auto-apply
- Approval-gated → Proposals require owner approval

**File:** `/home/pr0/projects/weslr/self_mod_proposals.json`

**Status:** Backend exists, UI needed

---

## Backend Wiring Discovery Summary

### Already Available Endpoints (Protected)

| Endpoint | Purpose | Auth | Status |
|----------|---------|------|--------|
| `/api/message` | Deterministic chat | Protected | ✅ Live |
| `/api/state` | System state | Protected | ✅ Live |
| `/health` | Health check | Protected | ✅ Live |

### Missing Endpoints (Backend Wiring Required)

| Feature | Endpoint Needed | Risk | Priority |
|---------|-----------------|------|----------|
| Project creation | `/api/project/create` | MEDIUM | HIGH |
| Project list | `/api/project/list` | MEDIUM | HIGH |
| Project chat | `/api/project/:id/chat` | MEDIUM | HIGH |
| Project context | `/api/project/:id/context` | MEDIUM | HIGH |
| Continuity save/restore | `/api/project/:id/continuity` | MEDIUM | MEDIUM |
| Evidence retrieval | `/api/project/:id/evidence` | MEDIUM | MEDIUM |
| Artifact upload | `/api/project/:id/artifacts` | MEDIUM | MEDIUM |
| Tool execution | `/api/project/:id/tools` | HIGH | LOW |
| Self-improvement | `/api/project/:id/improvements` | VERY HIGH | LOW |
| Daemon control | `/api/project/:id/daemon` | HIGH | LOW |

### Configuration Variables

| Variable | Default | Description | Risk |
|----------|---------|-------------|------|
| `WESLR_LLM_ENABLED` | `true` | Enable LLM providers | HIGH |
| `WESLR_PROACTIVE_DAEMON_ENABLED` | `false` | Enable proactive daemon | HIGH |
| `WESLR_EVIDENCE_ROUTING_ENABLED` | `true` | Enable evidence routing | MEDIUM |
| `WESLR_TOOLS_ENABLED` | `false` | Enable tool execution | HIGH |

---

## Owner Decision Points

### Immediate (UI Only)

| Setting | Status | Owner Action Required |
|---------|--------|----------------------|
| UI Preview Mode | ON | None (current state) |
| Deterministic Chat | ON | None (current state) |
| Project Chat | OFF | **APPROVE** to enable Preview/Live |
| Memory/Continuity | OFF | **APPROVE** to enable |
| Evidence | ON (backend only) | **APPROVE** to enable UI |
| Artifacts | OFF | **APPROVE** to enable |
| Model Provider | ON | **APPROVE** to enable UI controls |
| Tool Use | OFF | **APPROVE** to enable |
| Daemon | OFF | **APPROVE** to enable UI controls |
| Self-Improvement | OFF | **APPROVE** to enable UI controls |

### Backend Required (Owner Approval Needed)

| Setting | Backend Needed | Owner Approval Required |
|---------|----------------|------------------------|
| Project Chat Live | New API | ✅ YES |
| Memory Live | New API | ✅ YES |
| Artifacts Live | New API | ✅ YES |
| Evidence Live | New API | ✅ YES |
| Tool Use Live | New API | ✅ YES |
| Daemon Live | New API | ✅ YES |
| Self-Improvement Live | New API | ✅ YES |

---

## Visual Design Mockup (Text Description)

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

## Implementation Priority

### Phase 1: UI Shell (Immediate)

| Task | Priority |
|------|----------|
| Settings panel layout (desktop) | HIGH |
| Settings panel layout (mobile) | HIGH |
| Setting cards with risk badges | HIGH |
| Toggle buttons (disabled state) | HIGH |
| "UI only — not connected" labels | HIGH |
| No backend wiring | - |

### Phase 2: Backend Wiring (Owner Approval Required)

| Setting | Backend Needed | Priority |
|---------|----------------|----------|
| Deterministic Chat | None (already live) | - |
| Project Chat | `/api/project/*` | HIGH |
| Memory/Continuity | `/api/project/:id/continuity` | MEDIUM |
| Evidence | `/api/project/:id/evidence` | MEDIUM |
| Artifacts | `/api/project/:id/artifacts` | MEDIUM |
| Tool Use | `/api/project/:id/tools` | LOW |
| Daemon | `/api/project/:id/daemon` | LOW |
| Self-Improvement | `/api/project/:id/improvements` | LOW |

### Phase 3: Model Provider UI (Owner Approval Required)

| Task | Priority |
|------|----------|
| Model provider selection UI | HIGH |
| Provider configuration form | HIGH |
| Current provider status display | HIGH |
| Ollama/OpenAI/etc. options | HIGH |

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

---

## Final Judgment

**nova_weslr_owner_environment_settings_design_ready_for_owner_review**

**Status:**
- ✅ Environment settings design complete
- ✅ Backend discovery complete
- ✅ Risk levels assigned
- ✅ Owner approval points identified
- ⏸️ Implementation pending owner approval

**Owner Action Required:**
1. Review settings panel design
2. Approve Phase 1 (UI shell, no backend)
3. Review Phase 2 backend requirements
4. Approve Phase 2 backend wiring
5. Review Phase 3 model provider UI

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-08  
**Design Status:** Complete  
**Implementation Status:** Pending owner approval  
**Backend Status:** Discovery complete  
**Risk Assessment:** Complete
