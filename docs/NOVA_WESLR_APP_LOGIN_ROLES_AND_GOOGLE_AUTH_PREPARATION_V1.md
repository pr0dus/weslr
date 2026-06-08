# NOVA_WESLR_APP_LOGIN_ROLES_AND_GOOGLE_AUTH_PREPARATION_V1.md

**Date:** 2026-06-08  
**Status:** DESIGN COMPLETE  
**Repo:** `/home/pr0/projects/weslr-v1-ui-website`

---

## Executive Summary

**Design-only proposal** for WESLR internal role-based access control with Google OAuth preparation.

**Decision:** Use internal WESLR role system with Google as identity provider only.

**Rules:**
- Backend must enforce all permissions (frontend hiding is not enough)
- Google OAuth for identity only, roles defined in WESLR internal tables
- htpasswd remains active until replacement auth is ready and approved
- No public registration, no public chat, no exposed secrets

---

## PART A — Role Model

### Role Hierarchy

```
owner (highest)
 ├── admin/operator
 │   ├── tester
 │   └── viewer
 └── tester
     └── viewer
```

### Role Definitions

#### 1. Owner

**Allowed:**
- ✅ View all protected panels
- ✅ Owner environment settings (read/write)
- ✅ Runtime mode overview
- ✅ Approve future setting changes
- ✅ See daemon/model/tool controls
- ✅ See project/admin state
- ✅ Manage testers later
- ✅ Export/delete projects
- ✅ View diagnostics

**NOT allowed without separate approval:**
- ❌ Enabling daemon (requires explicit owner action)
- ❌ Enabling model provider (requires explicit owner action)
- ❌ Enabling tool execution (requires explicit owner action)
- ❌ Enabling self-improvement writes (requires explicit owner action)

**Note:** Owner must perform explicit actions to enable daemon/models/tools.

---

#### 2. Admin / Operator

**Allowed:**
- ✅ Manage projects (create, delete, modify)
- ✅ View diagnostics
- ✅ View runtime state
- ✅ Perform approved maintenance actions
- ✅ View chat history
- ✅ View artifacts
- ✅ Send messages
- ✅ View evidence/context

**Not allowed:**
- ❌ Owner-only runtime activation (unless delegated)
- ❌ View owner settings
- ❌ Change owner settings
- ❌ Manage users
- ❌ Export projects (owner-only)

---

#### 3. Tester

**Allowed:**
- ✅ Use assigned projects
- ✅ Use protected chat if enabled for project
- ✅ Create/use project artifacts if enabled for project
- ✅ View own project context
- ✅ View chat history for assigned projects
- ✅ Send messages in assigned projects

**Not allowed:**
- ❌ Owner settings
- ❌ Daemon/model/tool controls
- ❌ System diagnostics
- ❌ Other users' projects
- ❌ Create projects
- ❌ Manage users

---

#### 4. Viewer

**Allowed:**
- ✅ Read-only access to assigned project/page
- ❌ No chat send (unless explicitly enabled)
- ❌ No project creation
- ❌ No project management

---

#### 5. Unauthenticated

**Allowed:**
- ❌ Nothing inside chat app
- ✅ Redirect/login prompt only

---

## PART B — Permission Matrix

| Permission | owner | admin/operator | tester | viewer | unauthenticated |
|------------|-------|----------------|--------|--------|-----------------|
| **Login** | ✅ | ✅ | ✅ | ✅ | 🔒 redirect |
| **View dashboard** | ✅ | ✅ | ✅ | ✅ | 🔒 redirect |
| **Create project** | ✅ | ✅ | ❌ | ❌ | 🔒 redirect |
| **Select project** | ✅ | ✅ | ✅ | ✅ | 🔒 redirect |
| **Send message** | ✅ | ✅ | ✅ | ❌ | 🔒 redirect |
| **View chat history** | ✅ | ✅ | ✅ | ✅ | 🔒 redirect |
| **View artifacts** | ✅ | ✅ | ✅ | ❌ | 🔒 redirect |
| **Create artifacts** | ✅ | ✅ | ✅ | ❌ | 🔒 redirect |
| **View evidence/context** | ✅ | ✅ | ✅ | ✅ | 🔒 redirect |
| **View memory/continuity** | ✅ | ✅ | ✅ | ✅ | 🔒 redirect |
| **View owner settings** | ✅ | ❌ | ❌ | ❌ | 🔒 redirect |
| **Change owner settings** | ✅ | ❌ | ❌ | ❌ | 🔒 redirect |
| **View diagnostics** | ✅ | ✅ | ❌ | ❌ | 🔒 redirect |
| **View daemon status** | ✅ | ✅ | ❌ | ❌ | 🔒 redirect |
| **Toggle daemon** | ✅ | ❌ | ❌ | ❌ | 🔒 redirect |
| **Configure model provider** | ✅ | ❌ | ❌ | ❌ | 🔒 redirect |
| **Tool execution** | ✅ | ✅* | ❌ | ❌ | 🔒 redirect |
| **Self-improvement controls** | ✅ | ❌ | ❌ | ❌ | 🔒 redirect |
| **Manage users** | ✅ | ❌ | ❌ | ❌ | 🔒 redirect |
| **Export project** | ✅ | ❌ | ❌ | ❌ | 🔒 redirect |
| **Delete project** | ✅ | ✅* | ❌ | ❌ | 🔒 redirect |

**Notes:**
- `*` = Requires separate owner approval for admin/operator
- `🔒 redirect` = Redirect to login or show 401

---

## PART C — Google Login Preparation

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     chat.weslr.de (protected)                   │
├─────────────────────────────────────────────────────────────────┤
│  1. User visits chat.weslr.de                                   │
│  2. Backend checks session cookie / token                       │
│  3a. No valid session → Google OAuth redirect                  │
│  3b. Valid session → Check internal account + role             │
│  4. Google verifies identity (OAuth/OpenID Connect)            │
│  5. Backend receives verified Google email                      │
│  6. WESLR looks up internal account by Google email            │
│  7. WESLR assigns role from internal role table                 │
│  8. UI shows capabilities based on role                         │
│  9. Backend enforces permissions server-side                    │
└─────────────────────────────────────────────────────────────────┘
```

### Required Concepts

| Concept | Description | Status |
|---------|-------------|--------|
| Google OAuth/OpenID Connect | Identity provider | **Config only** |
| Accepted Google email | Email allowlist (Phase 1) | **Config only** |
| WESLR internal account table | Maps Google email → internal account | **Design** |
| Role assignment table | Maps account → role | **Design** |
| Session cookie | Authenticated session token | **Design** |
| CSRF protection | For future forms/actions | **Future** |
| Logout route | Session termination | **Future** |
| Account disabled flag | Suspend accounts without deletion | **Design** |
| Audit log | Login attempts + owner setting changes | **Design** |

### Configuration Placeholders (NOT IMPLEMENTED)

**Important:** These are design placeholders only. Do NOT create real OAuth files or store secrets.

```json
// config/google-auth-config.json (DESIGN ONLY - NOT IMPLEMENTED)
{
  "oauth": {
    "provider": "google",
    "client_id_placeholder": "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com",
    "client_secret_placeholder": "YOUR_GOOGLE_CLIENT_SECRET",
    "redirect_uri_placeholder": "https://chat.weslr.de/api/auth/callback",
    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "user_info_url": "https://openidconnect.googleapis.com/v1/userinfo",
    "scopes": ["openid", "email", "profile"]
  },
  "email_allowlist": [
    "arthrobert@gmail.com",
    "placeholder@example.com"
  ],
  "domain_allowlist": [
    "gmail.com",
    "example.com"
  ]
}
```

### Database Schema (Design Only)

#### accounts Table

```sql
CREATE TABLE accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  google_email TEXT UNIQUE NOT NULL,
  google_id TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL DEFAULT 'viewer',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  disabled INTEGER DEFAULT 0,  -- 0 = active, 1 = disabled
  last_login DATETIME,
  login_count INTEGER DEFAULT 0
);
```

#### roles Table

```sql
CREATE TABLE roles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  role_name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Seed data
INSERT INTO roles (role_name, description) VALUES 
('owner', 'Full access to all features and settings'),
('admin', 'Project management and diagnostics access'),
('tester', 'Project usage and chat access'),
('viewer', 'Read-only access to assigned projects');
```

#### permissions Table

```sql
CREATE TABLE permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL,
  permission TEXT NOT NULL,
  value TEXT DEFAULT 'allow',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (account_id) REFERENCES accounts(id)
);
```

### Endpoints (Design Only)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/login` | GET | None | Redirect to Google OAuth |
| `/api/auth/callback` | GET | None | OAuth callback (handles Google response) |
| `/api/auth/logout` | POST | Authenticated | Logout and clear session |
| `/api/auth/status` | GET | None | Check auth status |
| `/api/auth/verify` | GET | Authenticated | Verify current user role |

### Session Management (Design Only)

```javascript
// Session token format
{
  "token": "jwt_or_session_id",
  "google_email": "user@example.com",
  "role": "owner",
  "created_at": "2026-06-08T23:00:00Z",
  "expires_at": "2026-06-09T23:00:00Z"
}
```

### Logout Route (Design Only)

```javascript
// DELETE /api/auth/logout
// - Clear session cookie
// - Update audit log
// - Return success message
```

---

## PART D — Backend Source Discovery

### Repository Inspected
`/home/pr0/projects/weslr/` (main WESLR core)

### What Exists

| Component | Status | Notes |
|-----------|--------|-------|
| **User/Session models** | ⚠️ Partial | `session_id` used in `dialogue.py`, not persistent user accounts |
| **Role/Permission helpers** | ❌ None | No internal role system exists |
| **Auth/session code** | ❌ None | No auth middleware or session management |
| **Tenant/user isolation** | ⚠️ Partial | `continuity/` folder exists but not for user isolation |
| **Source scope/read authorization** | ❌ None | No read authorization system |
| **Project state models** | ✅ Yes | `workspace_state.json`, `projects.json`, `continuity/` folder |
| **Owner/operator concepts** | ⚠️ Contextual | "operator" appears in logs/continuity but not as role |
| **Settings/config helpers** | ✅ Yes | `config.py`, settings JSON files |
| **Audit log helpers** | ❌ None | No audit logging system |

### What Can Be Reused

- **Project models:** `projects.json`, `workspace_state.json` can be extended
- **Continuity system:** Can map to user sessions
- **Settings structure:** JSON config can be role-gated
- **Entity graph:** Can track user-project relationships

### What Is Missing

| Missing Component | Required Implementation |
|-------------------|------------------------|
| User account table | `accounts` table with Google email mapping |
| Role table | `roles` table (owner, admin, tester, viewer) |
| Session management | Cookie/session handling |
| Audit logging | `audit_log` table for login attempts |
| Permission checks | Backend middleware to enforce permissions |
| Google OAuth handler | `/api/auth/callback` endpoint |

### What Nova Can Implement in Website/App Layer

| Component | Website Layer |
|-----------|---------------|
| UI role-based panels | ✅ Can implement |
| Settings visibility | ✅ Can implement |
| Project filtering by role | ✅ Can implement |
| Login button/Google redirect | ✅ Can implement (UI only) |
| Session cookie (if backend provides) | ✅ Can use |
| Logout UI | ✅ Can implement |

### What Needs Backend/Core Implementation

| Component | Backend Required |
|-----------|-----------------|
| Google OAuth handler | `/api/auth/login`, `/api/auth/callback` |
| Account creation/linking | `/api/auth/link` |
| Role assignment | `/api/roles/update` |
| Session management | `/api/session/create`, `/api/session/verify` |
| Permission enforcement | `/api/auth/verify` middleware |
| Audit logging | `/api/audit/log` |
| htpasswd to app auth transition | Backend role check middleware |

### What Needs OCC Clarification

| Question | Clarification Needed |
|----------|---------------------|
| Existing Google login? | No existing Google login found in source |
| htpasswd location? | Not in weslr/ repo (likely in nginx config) |
| Session storage? | Redis/Memory/DB? Not specified |
| Email allowlist? | No allowlist config found |
| Owner email? | Must be configured in environment variables |

### Source Code Files Examined

- `chat_ui.py` - Frontend contract, UI messages
- `config.py` - Configuration variables
- `continuity/` - Session continuity (not user isolation)
- `dialogue.py` - Session ID handling, not user accounts
- `main.py` - Core runtime, no auth
- `weslr/` module - Core modules, no auth system

### Key Finding

**No existing auth/session system found.**
- WESLR uses context-based continuity but not user accounts
- No role/permission system exists
- No Google OAuth integration
- No audit logging
- htpasswd protection applied at nginx level (external to WESLR)

### Conclusion

**Fresh implementation required:**
- Backend: Create accounts, roles, sessions, audit tables
- Backend: Implement Google OAuth callback handler
- Backend: Implement permission enforcement middleware
- Frontend: UI role-based panels (can be implemented now)
- Frontend: Login button/Google redirect (UI only, backend handles OAuth)

---

## PART E — Owner Environment Settings Access

### Update Design for Role-Gated Settings

### Visibility Rules

| Role | Owner Settings | Status |
|------|---------------|--------|
| **owner** | ✅ Full view | Visible |
| **admin/operator** | ⚠️ Partial view, no dangerous writes unless delegated | Hidden/Read-only |
| **tester** | ❌ Hidden | Not visible |
| **viewer** | ❌ Hidden | Not visible |
| **unauthenticated** | ❌ Denied | Redirect to login |

### Write Access Rules

| Action | Allowed By | Requirement |
|--------|------------|-------------|
| View settings | owner only | ✅ |
| Read-only settings | admin/operator | ✅ (if delegated) |
| Write settings | owner only | ✅ |
| Owner-only settings writes | owner only | ✅ |
| Admin writes to owner settings | admin/operator | ❌ (unless delegated) |
| High-risk settings writes | owner only | ✅ |

### High-Risk Settings (Require Explicit Approval)

| Setting | Current State | Owner Action Required |
|---------|--------------|----------------------|
| Model provider | Disabled | Enable → owner action |
| Tools | Disabled | Enable → owner action |
| Daemon/proactive mode | Disabled | Enable → owner action |
| Self-improvement | Disabled | Enable → owner action |
| Memory writes | Disabled | Enable → owner action |
| Evidence/RAG live retrieval | Disabled | Enable → owner action |
| Artifact creation | Disabled | Enable → owner action |

### UI Implementation (Website Layer)

```typescript
// Frontend check before showing Owner Settings
function canViewOwnerSettings(role: string): boolean {
  return role === 'owner';
}

function canWriteOwnerSettings(role: string): boolean {
  // Only owner can write, admin can write only if delegated
  if (role === 'owner') return true;
  if (role === 'admin') return getDelegationStatus(); // Backend check
  return false;
}

// Role check for settings
function renderOwnerSettings(role: string): JSX.Element {
  if (canViewOwnerSettings(role)) {
    return <OwnerSettingsPanel role={role} />;
  }
  return <ProtectedContent role={role} />;
}
```

### Backend Requirements

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/settings/list` | GET | Authenticated | List settings with visibility flags |
| `/api/settings/write` | POST | Authenticated (owner only) | Write settings (backend enforces role) |

### Owner Settings Panel Role Gating

```typescript
// Settings panel render logic
function SettingsPanel({ role }: { role: string }) {
  return (
    <div className="settings-panel">
      {canViewOwnerSettings(role) && (
        <SettingsSection title="Owner Settings">
          {/* Owner-only settings */}
        </SettingsSection>
      )}
      
      {role === 'owner' && (
        <SettingsSection title="High-Risk Controls">
          {/* Model provider, tools, daemon controls */}
          {/* All require explicit owner action */}
        </SettingsSection>
      )}
      
      {role === 'admin' && (
        <SettingsSection title="Operator Controls">
          {/* Read-only or delegated write settings */}
        </SettingsSection>
      )}
    </div>
  );
}
```

---

## Phase 0-5 Transition Plan

| Phase | Status | Description | Current State |
|-------|--------|-------------|---------------|
| **Phase 0** | ✅ Current | htpasswd remains active | `chat.weslr.de` protected by htpasswd |
| **Phase 1** | ✅ Design | UI role model and read-only owner settings | ✅ Complete |
| **Phase 2** | ⏳ Next | Backend `/api/auth/me` mock/static role behind htpasswd | Not implemented |
| **Phase 3** | ⏳ Next | Google login in protected backend, still behind htpasswd during test | Not implemented |
| **Phase 4** | ⏳ Next | Owner tests Google login with owner email | Not implemented |
| **Phase 5** | ⏳ Next | Migrate from htpasswd to app login after owner approval | Not implemented |

---

## Mobile UI Implication

| Role | Mobile Panel Visibility |
|------|------------------------|
| **owner** | Show Owner Settings |
| **admin/operator** | Show Diagnostics/Operator panel |
| **tester** | Show Projects/Chat/Artifacts |
| **viewer** | Show read-only project view |
| **unauthenticated** | Show login only |

**Note:** If no backend role API exists, UI shows "Role: Owner Preview (htpasswd-protected)" with clear indication that "Role enforcement backend not connected yet"

---

## Environment Variables Required (Phase 3+)

| Variable | Purpose | Current State |
|----------|---------|---------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Not set |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Not set |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL | Not set |
| `WESLR_AUTH_ALLOWED_EMAILS` | Email allowlist | Not set |
| `WESLR_OWNER_EMAILS` | Owner email list | Not set |
| `WESLR_AUTH_COOKIE_SECRET` | Session cookie encryption | Not set |

---

## Final Judgment

**nova_app_login_roles_and_google_auth_preparation_ready_for_owner_review**

**Status:**
- ✅ Role model designed (5 roles)
- ✅ Permission matrix complete
- ✅ Google login preparation designed
- ✅ No real OAuth implemented
- ✅ No public exposure
- ✅ Backend source discovery complete
- ✅ Owner settings role gating designed
- ✅ Transition plan documented

**Next Steps:**
1. Owner approval for Phase 1-5 implementation
2. Create Google OAuth credentials (secure config)
3. Implement database schema
4. Create initial accounts table
5. Implement role-based access control middleware

**Owner Decision Required:**
- ✅ Approve Phase 1-5 transition plan
- ✅ Approve implementation timeline
- ✅ Provide Google OAuth credentials (if approved for Phase 3)
- ✅ Decide on email/domain allowlist
- ✅ Approve htpasswd removal timing (Phase 5)
