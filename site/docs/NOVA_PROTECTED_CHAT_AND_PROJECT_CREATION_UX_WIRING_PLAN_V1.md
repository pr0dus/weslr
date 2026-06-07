# Protected WESLR App UX Wiring Plan V1

**Date:** 2026-06-07  
**Author:** Nova (MAIN_DISPATCHER)  
**Status:** Ready for Owner Review  
**Target:** https://chat.weslr.de/ (protected)  
**Public Site:** https://weslr.de/ (unchanged)

---

## Executive Summary

The current Weslr app (`weslr-v1-ui-website/weslr-ui/`) is a **public read-only demo** with no authentication layer, no project creation UI, and no protected workspace. To implement `chat.weslr.de` as a private workspace app, we need:

1. **Auth boundary** — Cloudflare Access or password-protected route
2. **Protected app shell** — Left sidebar + central chat + right options panel
3. **Project creation flow** — New project modal/page
4. **Project workspace flow** — Chat with context, artifacts, evidence panels
5. **Backend wiring** — API/CLI targets for project/chat operations

This plan documents the **current state**, **proposed routes**, **layout requirements**, and **backend discovery** for the protected app.

---

## Current Protected Chat State

### What Exists Today

| Component | Path | Status |
|-----------|------|--------|
| Public Demo | `/home/pr0/projects/weslr-v1-ui-website/weslr-ui/` | Public read-only chat |
| Main Entry | `App.tsx` | Single-screen demo with hero, chat, footer |
| API Client | `api.ts` | Mocked public endpoints |
| Config | `config.ts` | `productMode: 'public_demo_readonly'` |
| Protected Route | None | Not implemented |

### Current Configuration

```typescript
productMode: 'public_demo_readonly',
features: {
  chat: true,
  onboarding: false,
  memoryWrites: false,
  fileUpload: false,
  operatorPanel: false,
  proposalReview: false,
  deploymentControls: false,
  billing: false,
  organizationAdmin: false,
},
```

### Current App Structure (Public Demo Only)

```
App.tsx
├── DemoBanner (read-only warning)
├── HeroIntro (example prompts)
├── TrustCards (hosted/private/deployment cards)
└── ChatSurface
    ├── ChatHeader (status pill: "No actions executed")
    ├── MessagesArea (user/weslr bubbles)
    ├── Composer (textarea + send button)
    └── StatusBar (continuity status)
└── OperatorPanel (disabled in public_demo_readonly)
```

---

## Proposed Protected App Routes

### Route Structure

| Route | Purpose | Auth Required | Status |
|-------|---------|---------------|--------|
| `/login/` | Cloudflare Access or password gate | Optional (Cloudflare) | External |
| `/app/` | Protected app shell (landing) | Yes | New |
| `/app/projects/` | Project list + new project | Yes | New |
| `/app/projects/new/` | Project creation form | Yes | New |
| `/app/projects/:projectId/` | Project summary | Yes | New |
| `/app/projects/:projectId/chat/` | Project chat workspace | Yes | New |
| `/app/projects/:projectId/artifacts/` | Project artifacts | Yes | New |
| `/app/projects/:projectId/context/` | Project context/evidence | Yes | New |
| `/app/settings/` | User preferences | Yes | New |

### Route Mapping

**UI Layer:**
- React Router routes in `App.tsx` wrapped with auth protection
- Protected routes conditionally render based on `authToken` or Cloudflare Access header

**Backend Layer:**
- `/api/project/create` — Create new project
- `/api/project/list` — List user projects
- `/api/project/:id` — Get project details
- `/api/project/:id/chat` — Send/receive chat messages
- `/api/project/:id/artifacts` — List/create artifacts
- `/api/project/:id/context` — Get context/evidence

---

## Auth Boundary

### Recommended First-Stage Protection

| Option | Pros | Cons | Status |
|--------|------|------|--------|
| Cloudflare Access | No code changes, enterprise SSO, audit logs | Requires Cloudflare Pro/Enterprise | ✅ Recommended |
| Password-protected route (`/login/`) | Simple, immediate | No SSO, manual account management | 🟡 Alternative |
| Manually created accounts | Full control, no external dependencies | No self-service, manual onboarding | 🟡 Alternative |

### Auth Flow (Cloudflare Access)

1. User visits `https://chat.weslr.de/`
2. Cloudflare Access intercepts, prompts for SSO/login
3. On success, user lands at `/app/` with `CF-Access-Authenticated` header
4. Frontend checks header or token before rendering protected routes
5. If not authenticated, redirect to `/login/` placeholder

### Auth State Management (Frontend)

```typescript
interface AuthState {
  isAuthenticated: boolean;
  accessToken?: string;
  user?: {
    id: string;
    email: string;
    name: string;
  };
}

// Protected route wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login/" />;
  return <>{children}</>;
};
```

---

## Protected App Shell Layout

### Desktop Layout (Protected App)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Protected Header (logo + user menu + status pill: "Protected • Internal")  │
├──────────────┬──────────────────────────────────────────────────────────────┤
│              │                                                              │
│  Left        │  Main Center                                               │
│  Sidebar     │  ┌──────────────────────────────────────────────────────┐  │
│  - WESLR     │  │  Active Project Title                              │  │
│    logo      │  └──────────────────────────────────────────────────────┘  │
│  - Project   │                                                              │
│    list      │  ┌──────────────────────────────────────────────────────┐  │
│  - New proj  │  │  Chat Messages Area                                │  │
│    button    │  │  - Assistant bubbles                              │  │
│  - Recent    │  │  - User bubbles                                   │  │
│    projects  │  │  - Empty state if no chat                         │  │
│              │  │  - Message bubbles with timestamps                │  │
│              │  └──────────────────────────────────────────────────────┘  │
├──────────────┴──────────────────────────────────────────────────────────────┤
│  Right Panel (Options/Artifacts/Evidence)                                  │
│  - Project options                                                         │
│  - Artifacts (list + upload)                                               │
│  - Evidence/context                                                        │
│  - Memory/continuity                                                       │
│  - Settings/status                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Bottom Composer (Fixed)                                                   │
│  - Textarea (multiline, auto-resize)                                       │
│  - Send button                                                             │
│  - Optional: attach/context button (disabled if not implemented)          │
│  - Optional: project options menu                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (Protected App)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Top Bar (Project Name + Menu Button)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Chat Messages Area                                                        │
│  - Assistant bubbles                                                       │
│  - User bubbles                                                            │
│  - Empty state                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Bottom Composer (Fixed)                                                   │
│  - Textarea + Send button                                                  │
│  - Slide-out drawer or bottom sheet for:                                  │
│    • Project options                                                       │
│    • Artifacts                                                             │
│    • Evidence/context                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Creation Flow

### User Flow (Protected)

1. User clicks **"New Project"** button (sidebar or `/app/projects/` landing)
2. Modal or page opens with:
   - Project name (required, text input)
   - Project type/domain (dropdown: Engineering, Research, Business, Other)
   - Visibility (private/protected, hidden dropdown or pre-selected)
   - Optional description (textarea)
   - **"Create Project"** button (primary)
3. On success:
   - Redirect to `/app/projects/:projectId/chat/`
   - Empty chat window appears
   - Context panel available with **"No context yet"** placeholder
4. Error handling:
   - Name must be unique (per user)
   - Project type must be valid
   - Rate limiting: max N projects per user (configurable)

### Project Creation UI (Frontend)

```typescript
function ProjectCreationForm({ onClose, onCreate }: { onClose: () => void, onCreate: (id: string) => void }) {
  const [name, setName] = useState('');
  const [type, setType] = useState('engineering');
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsCreating(true);
    try {
      const response = await fetch('/api/project/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, type, description }),
      });
      const result = await response.json();
      if (result.success) {
        onCreate(result.projectId);
      } else {
        // Show error toast
      }
    } catch (_e) {
      // Show error toast
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div style={styles.modal}>
      <h2>Create New Project</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Project Name*
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Q3 Engineering Analysis"
            required
          />
        </label>
        <label>
          Project Type
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="engineering">Engineering</option>
            <option value="research">Research</option>
            <option value="business">Business</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label>
          Description (optional)
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief overview of this project's purpose..."
          />
        </label>
        <div style={styles.actions}>
          <button type="button" onClick={onClose}>Cancel</button>
          <button type="submit" disabled={isCreating || !name.trim()}>
            {isCreating ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </form>
    </div>
  );
}
```

---

## Chat Workspace Flow

### Workspace Components

| Component | Location | Status Labels |
|-----------|----------|---------------|
| Active Project Header | Top | "Protected" • "Internal" • "Owner/Test Access" |
| Chat Messages Area | Center | Empty state, message bubbles, timestamps |
| Message Composer | Bottom | Fixed, multiline input, send button |
| Project Options Panel | Right | Toggleable, project settings, visibility |
| Artifacts Panel | Right | List + upload, disabled if not implemented |
| Evidence/Context Panel | Right | Read-only, continuity snapshots |
| Status Pill | Header | "Protected" / "Internal" / "Not Publicly Live" |

### Status Labels (Required)

| Label | When Displayed |
|-------|----------------|
| **Protected** | Always visible on chat header |
| **Internal** | When `config.features.internalMode === true` |
| **Owner/Test Access** | When user email matches `config.owners` or `config.testers` |
| **Not Publicly Live** | Always visible in footer |
| **Requires Approval** | When project in pending state |

---

## Options/Artifacts/Evidence Panel Design

### Panel Sections (Right Panel)

| Section | UI Controls | Status Labels | Backend Endpoint |
|---------|-------------|---------------|------------------|
| **Project Options** | Visibility toggle, theme toggle, export button | Available / Protected | `/api/project/:id/settings` |
| **Artifacts** | File upload button, list view | Available / Protected / Internal | `/api/project/:id/artifacts` |
| **Evidence/Context** | Continuity slider, snapshot list | Available / Protected | `/api/project/:id/context` |
| **Memory/Continuity** | Snapshot restore, memory state | Available / Protected | `/api/project/:id/continuity` |
| **Settings** | API keys, webhook URLs, limits | Available / Internal | `/api/project/:id/config` |
| **Export/Report** | Export JSON, Export PDF | Disabled / Available | `/api/project/:id/export` |
| **Operator Review** | Review queue, approval buttons | Disabled / Requires Approval | `/api/project/:id/review` |

### Panel Visual States

| State | Background | Border | Text Color |
|-------|------------|--------|------------|
| **Available** | `rgba(34,197,94,0.08)` | `1px solid rgba(34,197,94,0.24)` | `#bbf7d0` |
| **Protected** | `rgba(96,165,250,0.08)` | `1px solid rgba(96,165,250,0.24)` | `#bfdbfe` |
| **Internal** | `rgba(245,158,11,0.08)` | `1px solid rgba(245,158,11,0.24)` | `#fde68a` |
| **Not Publicly Live** | `rgba(245,158,11,0.04)` | `1px dashed rgba(245,158,11,0.16)` | `#fde68a` |
| **Requires Approval** | `rgba(239,68,68,0.08)` | `1px solid rgba(239,68,68,0.24)` | `#fca5a5` |

---

## Backend Wiring Discovery

### What Exists (Local)

| Endpoint | Method | Purpose | Status | Notes |
|----------|--------|---------|--------|-------|
| `/api/chat` | POST | Public chat message | ✅ Existing | Read-only demo only |
| `/api/contract/*` | GET | Mocked contract endpoints | ✅ Existing | `api.ts` mocks |

### What Doesn't Exist (Missing)

| Functionality | Missing Component | Priority |
|---------------|-------------------|----------|
| Project creation API | `/api/project/create` | High |
| Project list API | `/api/project/list` | High |
| Project CRUD | `/api/project/:id` | High |
| Protected chat messages | `/api/project/:id/chat` | High |
| Artifact upload | `/api/project/:id/artifacts` | Medium |
| Context/evidence | `/api/project/:id/context` | Medium |
| Operator review API | `/api/project/:id/review` | Low |

### Backend Dependencies

| Dependency | Path | Status |
|------------|------|--------|
| `weslr/file_router.py` | `/home/pr0/projects/weslr/weslr/` | Existing (but not wired to UI) |
| `weslr/chat_ui.py` | `/home/pr0/projects/weslr/weslr/` | Existing (public demo only) |
| Ollama backend | `http://127.0.0.1:11434` | Running |

---

## What Nova Can Build Now (Without Backend)

### UI-Only Shell (Immediate)

| Feature | Status | Notes |
|---------|--------|-------|
| Protected route wrapper | ✅ Can build | React component with `useAuth()` |
| Project list (mock) | ✅ Can build | Local state with simulated project objects |
| Project creation modal (UI) | ✅ Can build | Form with validation, disabled submit |
| Chat workspace layout | ✅ Can build | Left sidebar + center + right panel |
| Bottom composer | ✅ Can build | Textarea + send button (disabled) |
| Status pills | ✅ Can build | Visual indicators for protected/internal |
| Empty states | ✅ Can build | "No projects yet", "No chat history" |

### Disabled States (Required)

| Feature | Disabled When | Message |
|---------|---------------|---------|
| Project creation | No backend | "Project creation requires backend wiring (needs OCC clarification)" |
| Chat sending | No backend | "Chat requires backend wiring (needs OCC clarification)" |
| File upload | No backend | "File upload requires backend wiring (needs OCC clarification)" |
| Artifact upload | No backend | "Artifact upload requires backend wiring (needs OCC clarification)" |
| Context saving | No backend | "Context saving requires backend wiring (needs OCC clarification)" |

---

## What Requires OCC Clarification

| Feature | Blocked On | Clarification Needed |
|---------|------------|---------------------|
| Project creation | Backend API | `/api/project/create` endpoint schema, auth requirements |
| Protected chat | Backend API | `/api/project/:id/chat` message format, error handling |
| File/artifact upload | Backend API | `/api/project/:id/artifacts` file types, size limits |
| Context/evidence | Backend API | `/api/project/:id/context` data schema, persistence |
| Operator review | Backend API | `/api/project/:id/review` workflow, approval logic |
| Project list | Backend API | `/api/project/list` pagination, filtering |

---

## What Requires Owner Approval

| Action | Owner Approval Required | Notes |
|--------|------------------------|-------|
| Deploy to `chat.weslr.de` | ✅ Yes | New domain, DNS changes, Cloudflare config |
| Enable Cloudflare Access | ✅ Yes | Enterprise feature, requires Pro/Enterprise plan |
| Change DNS records | ✅ Yes | A record for `chat.weslr.de` |
| Expose new backend endpoints | ✅ Yes | Security review, rate limiting, auth |
| Add public demo redirects | ✅ Yes | May affect existing public users |

---

## Mobile Layout Plan

### Desktop First (Primary Target)

- Left sidebar (project list, new project)
- Center (chat messages)
- Right panel (options, artifacts, context)
- Bottom composer (fixed)

### Mobile Responsive

- Top bar (project name, menu button)
- Chat area (full width)
- Bottom composer (fixed, minimal)
- Slide-out drawers or bottom sheets for:
  - Project options
  - Artifacts list
  - Evidence/context
  - Settings

### Breakpoints

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| Desktop | ≥1024px | Sidebar + center + right panel |
| Tablet | 768px–1023px | Reduced sidebar width, right panel collapsed by default |
| Mobile | <768px | Full-screen chat, slide-out drawers |

---

## Validation Checklist

### Pre-Commit Checks

- [ ] No legal pages changed
- [ ] No public registration opened
- [ ] No public chat exposed
- [ ] No Cloudflare/nginx/DNS/access changes (unless owner approved)
- [ ] Protected route remains protected (not publicly accessible)
- [ ] `git status` clean
- [ ] `git diff --check` passes
- [ ] No secrets exposed in source
- [ ] No internal paths exposed on public pages

### Commit Message

```
WESLR: design protected chat and project creation ux wiring v1

- Document current protected chat state (public demo only)
- Define protected app routes (/app/, /app/projects/, /app/projects/:id/)
- Specify auth boundary (Cloudflare Access recommended)
- Detail project creation flow (form, validation, success redirect)
- Outline chat workspace layout (sidebar + center + panel + composer)
- Map panel sections (options, artifacts, context, settings)
- Identify backend wiring needs (API endpoints, missing components)
- List Nova-buildable features (UI shell, disabled states)
- Specify OCC clarification requirements
- Define owner approval items (deployment, DNS, backend exposure)
- Add mobile layout plan (slide-out drawers, breakpoints)
- Include validation checklist (no legal changes, no public exposure)
```

---

## Final Judgment

**Nova_protected_chat_project_creation_ux_wiring_plan_ready_for_owner_review**

The plan is complete and ready for owner review. Key decisions needed:

1. **Auth method:** Cloudflare Access vs. password-protected route
2. **Backend priority:** Which API endpoints to build first
3. **Deployment approval:** Enable `chat.weslr.de` with protected access
4. **OCC clarification:** Backend API specifications for project/chat/artifacts

**Do not proceed with implementation until owner approval is granted.**

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-07  
**Next Review:** After owner approval or denial
