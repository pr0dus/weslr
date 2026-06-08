# Protected WESLR Chat App Shell - Responsive UX & Backend Wiring Map V1

**Date:** 2026-06-08  
**Author:** Nova (MAIN_DISPATCHER)  
**Status:** Report Draft - Mobile UX Patch Pending, Backend Discovery Complete

---

## PART A: RESPONSIVE MOBILE UX PATCH

### Current Mobile Issues Observed

| Issue | Impact | Severity |
|-------|--------|----------|
| Too much empty vertical space | Low content density | Medium |
| Header/status area too tall | Less room for chat | Medium |
| Center preview block too large | Crowded composer | Medium |
| Composer/action buttons crowd bottom | Hard to tap buttons | Medium |
| Bottom tabs/buttons partly cut off | Inaccessible controls | High |
| Layout not responsive to device height | Poor mobile experience | High |
| UI not adapting to keyboard-open | Input obscured | High |

### Required Patch Strategy

#### 1. Modern Viewport Handling

**Current:** `min-height: 100vh`  
**Target:** `min-height: 100dvh` + safe-area handling

```css
/* Safe area for mobile */
body {
  min-height: 100dvh;
  padding-bottom: env(safe-area-inset-bottom);
  padding-top: env(safe-area-inset-top);
}

/* Mobile-specific header */
@media (max-width: 768px) {
  .app-header {
    height: 48px;
    padding: 0 0.75rem;
  }
}
```

#### 2. Compact Header

- Reduce height from 56px to 48px on mobile
- Keep logo + title + status pill readable
- Project title row should be compact (14px font)

#### 3. Flexible Chat Area

```css
.app-shell {
  display: flex;
  flex-direction: column; /* Mobile default */
  height: calc(100dvh - 48px);
}

.center-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
```

#### 4. Chat Composer Safety

```css
.bottom-composer {
  padding-bottom: calc(1rem + env(safe-area-inset-bottom));
}

@media (max-width: 480px) {
  .composer-actions {
    flex-wrap: wrap;
  }
  .icon-btn {
    width: 40px;
    height: 40px;
  }
}
```

#### 5. Font Size Clamp

```css
@media (max-width: 768px) {
  .app-title { font-size: clamp(0.85rem, 1.2vw, 1rem); }
  .project-title { font-size: clamp(0.95rem, 1.3vw, 1.1rem); }
  .empty-state h2 { font-size: clamp(1.5rem, 2.5vw, 1.8rem); }
  body { font-size: clamp(0.9rem, 1.4vw, 1.05rem); }
}
```

#### 6. Touch Targets

- Minimum: 44px tap target
- Action buttons: 40px x 40px (mobile)
- Send button: At least 48px width

### Implementation Plan

1. Update `protected-preview/chat-app-shell/index.html`
2. Add responsive CSS media queries
3. Test on multiple device sizes
4. Verify no desktop regression

### Files Likely Changed

| File | Change Type |
|------|-------------|
| `protected-preview/chat-app-shell/index.html` | CSS media queries, responsive layout |
| `/var/www/weslr-chat-app-shell/index.html` | Synced after testing |

### Validation Steps

- [ ] Mobile browser test after auth
- [ ] Test `chat.weslr.de/` and `chat.weslr.de/app`
- [ ] Test keyboard focus in composer
- [ ] Test tab/panel buttons
- [ ] Confirm no 500 errors
- [ ] Confirm no console errors
- [ ] Confirm `weslr.de/app` still 404

---

## PART B: BACKEND WIRING MAP

### Backend Discovery

#### Current Protected Backend

**File:** `/home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py`  
**Port:** 8092 (running on `chat.weslr.de`)  
**Endpoint:** `/api/message`  
**Handler:** `dispatch_deterministic_handler` (from `weslr/deterministic_handlers.py`)

**Current Behavior:**
- POST `/api/message` → Deterministic response only
- NO model provider calls
- NO external API calls
- NO file uploads
- NO learning from users

#### Speak Command (CLI)

**File:** `/home/pr0/projects/weslr/commands/speak.py`  
**Purpose:** Chat with Weslr as primary entity  
**Command:** `weslr speak --message "..."`

**Features:**
- Entity graph lookup
- Context-aware answers
- Tax knowledge integration
- Distance calculation (Entfernungspauschale)

#### Protected Project Chat Entrypoint

**Status:** NOT FOUND - No dedicated project/chat API endpoint

**Available Endpoints:**
| Endpoint | Purpose | Protected | Notes |
|----------|---------|-----------|-------|
| `/api/message` | Deterministic chat | ✅ Yes | Port 8092 |
| `/api/state` | System state | ✅ Yes | Port 8092 |
| `/health` | Health check | ✅ Yes | Port 8092 |
| `/api/chat` | Mocked API | ✅ Yes | `weslr-ui/api.ts` |

### Wiring Map

| UI Action | Backend Target | Source | Status | Risk | Next Action |
|-----------|----------------|--------|--------|------|-------------|
| Create project | `weslr_cli.py` | `/home/pr0/projects/weslr/weslr_cli.py` | ✅ Available CLI | Low | Create wrapper endpoint |
| Select project | Entity graph lookup | `/home/pr0/projects/weslr/entity_graph.py` | ✅ Available | Low | No backend needed (client-side) |
| Send message | `/api/message` → `dispatch_deterministic_handler` | `/home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py` | ✅ Available | Low | Wire to existing endpoint |
| Load chat history | None | - | ❌ Not available | N/A | Build history storage |
| Save/retrieve context | None | - | ❌ Not available | N/A | Build context storage |
| Open artifacts | None | - | ❌ Not available | N/A | Build artifact API |
| Create artifact | None | - | ❌ Not available | N/A | Build artifact API |
| Open evidence/context | None | - | ❌ Not available | N/A | Build evidence API |
| Open memory/continuity | None | - | ❌ Not available | N/A | Build continuity API |
| Operator review/status | `/api/state` | `/home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py` | ✅ Available | Low | Show state in panel |

### Backend Safety Boundaries

**Allowed (Protected):**
- `/api/message` → Deterministic handlers only
- `/api/state` → System status (no secrets)
- `/health` → Health check

**Blocked (Public):**
- No public registration
- No public chat
- No open backend endpoints
- No user data exposure

**Protected (Behind htpasswd):**
- All `/api/*` endpoints
- All project operations
- All chat operations

### Recommended Backend Wiring Path

#### Option A: Protected Local Adapter (Recommended)

**Approach:** Create `/home/pr0/projects/weslr/tools/protected_project_chat_adapter.py`

**Features:**
- Local-only, no network exposure
- Behind existing `chat.weslr.de` auth
- Calls `dispatch_deterministic_handler`
- Returns JSON with project context
- No external API calls

**Implementation:**
```python
# protected_project_chat_adapter.py
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from weslr.deterministic_handlers import dispatch_deterministic_handler
from entity_graph import get_entity_graph

class ProtectedProjectChatHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/project/chat':
            # Parse message, find project context, dispatch
            result = dispatch_deterministic_handler(...)
            self.send_json(result)
```

#### Option B: Use Existing Protected Workflow Server

**Approach:** Extend `/home/pr0/projects/weslr/tools/protected_non_model_workflow_server.py`

**Pros:** Already running, already protected  
**Cons:** Limited to current message format

### What Nova Can Implement Now

| Feature | Status | Notes |
|---------|--------|-------|
| Responsive mobile CSS | ✅ Ready | Media queries, safe-area, clamp() |
| Compact header | ✅ Ready | 48px mobile height |
| Flexible chat layout | ✅ Ready | Flexbox, min-height |
| Touch targets | ✅ Ready | 40px+ tap targets |
| Font size clamp | ✅ Ready | clamp() on text |
| Send to `/api/message` | ✅ Ready | Existing endpoint |
| Show state in panel | ✅ Ready | `/api/state` call |

### What Requires Backend Adapter

| Feature | Required Backend | Status |
|---------|------------------|--------|
| Project creation | New endpoint | Needs implementation |
| Project list persistence | New endpoint | Needs implementation |
| Chat history storage | New endpoint | Needs implementation |
| Context/evidence saving | New endpoint | Needs implementation |
| Artifact operations | New endpoint | Needs implementation |

### What Requires OCC Backend Clarification

| Feature | Blocked On | Clarification Needed |
|---------|------------|---------------------|
| Project metadata | Backend design | Schema, auth, rate limits |
| Message persistence | Backend design | Storage, retrieval, pagination |
| Context updates | Backend design | Data model, versioning |
| Evidence accumulation | Backend design | Audit trail, source tracking |

---

## FINAL VERIFICATION

### Protected Route Status

| Route | Status | Auth |
|-------|--------|------|
| `https://chat.weslr.de/` | ✅ 401 | htpasswd |
| `https://chat.weslr.de/app` | ✅ 401 | htpasswd |
| `https://chat.weslr.de/diagnostics/workflow-preview/` | ✅ 401 | htpasswd |

### Public Exposure Check

| URL | Status | Expected |
|-----|--------|----------|
| `https://weslr.de/app` | ✅ 404 | No protected content |

### Next Recommended Lane

**Immediate (Nova):**
1. Implement responsive mobile CSS
2. Update protected app shell
3. Test on mobile browser
4. Deploy after owner visual review

**After Owner Approval:**
1. Create protected project chat adapter
2. Implement project creation endpoint
3. Implement project list endpoint
4. Wire frontend to backend

---

## FINAL JUDGMENT

**nova_protected_chat_responsive_ux_and_backend_wiring_map_ready_for_owner_review**

**Status:**
- ✅ Backend discovery complete
- ✅ Wiring map documented
- ✅ Mobile UX strategy defined
- ⏸️ Mobile UX implementation pending owner approval
- ⏸️ Backend adapter pending owner approval

**Owner Action Required:**
1. Review responsive UX plan
2. Approve backend adapter design (if needed)
3. Test mobile behavior after UX patch
4. Approve backend implementation (if needed)

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-08  
**Mobile Status:** Design complete, implementation pending  
**Backend Status:** Discovery complete, adapter pending  
**Wiring Map:** Complete (available/safe/available_safe_endpoint)  
