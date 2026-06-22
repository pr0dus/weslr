# WESLR Chat Customer-Grade Wiring Plan V1

**Author:** Nova
**Date:** 2026-06-22
**Status:** PLANNING ONLY — design lane; no implementation; no runtime execution
**Scope:** Customer-grade wiring plan for `chat.weslr.de` (the protected WESLR interface)
**Out of scope:** Runtime code edits, ChatResponder edits/execution, `respond_chat` invocation, real shadow calls, public runtime enablement, public signup, public OAuth, AGI/sentience/consciousness/benchmark/public-science/autonomous-self-improvement/production-ready/live-public-runtime claims

---

## 1. Purpose and Scope

This plan specifies the **design** for a customer-grade protected `chat.weslr.de` environment that can be tested like a real customer environment, while preserving the operator-authority, evidence-boundary, source-access-discipline, runtime-separation, memory-safety, and public-claim-discipline framing already established for `weslr.de`.

**Lane:** Architecture / design / planning. No code changes tonight. No runtime execution tonight.

**Customer-grade means:**
- Auth-gated, identity-bound access (htpasswd at minimum; structured operator-owned identity preferred for customer-style accounts)
- Session boundaries that prevent cross-talk, with explicit per-session audit trails
- Runtime wrapper that gates `respond_chat`, `cmd_speak`, and any ChatResponder entry points behind operator authority and capability discovery
- Logging model that captures what is safe and necessary, and never captures what is private or sensitive
- Backup/rollback plan so any wiring change is reversible
- Health checks and monitoring that detect failures before customers do
- Pilot-user flow that is reproducible and operator-controlled
- Admin/operator controls that remain under operator authority
- Public/private separation that does not leak protected surfaces to `weslr.de`

**Customer-grade does not mean:**
- Production SLA, public uptime guarantee, or general-public signup
- Live autonomous runtime, live AGI, live benchmark certification, live public-science claim
- Anything that bypasses operator authority

---

## 2. Repo Root, Branch, Start HEAD, Current HEAD

**Operator-supplied path:** `/data/data/com.termux/files/home/weslr-pr47-clean` (not present on this host)
**Actual worktree used:** `/home/pr0/projects/weslr-run-first-live-searxng-sample-20260613`

| Field | Value |
|---|---|
| Repo root | `/home/pr0/projects/weslr` (multi-worktree layout) |
| Worktree | `/home/pr0/projects/weslr-run-first-live-searxng-sample-20260613` |
| Branch | `nova-occ-discovery-doctrine-implementation-20260613` |
| Tracking remote | `origin/occ-discovery-doctrine-implementation-20260613` |
| Start HEAD (operator-supplied) | (not specified; current branch HEAD at plan start) |
| Current HEAD (at plan start) | `81bb72b2` "WESLR: review second controlled true run result after discovery registry repair v1" |

**Note on path mismatch:** The operator-supplied path `/data/data/com.termux/files/home/weslr-pr47-clean` is not present on this host. The correct worktree is `/home/pr0/projects/weslr-run-first-live-searxng-sample-20260613`, which carries the requested branch. The plan proceeds against the correct worktree. Operator can re-supply the correct path if a different worktree was intended.

**Note on `weslr/main.py`:** Operator's protected-files list includes `weslr/main.py`, but this file does not exist on the branch (the protected runtime entry is `main.py` at repo root, plus `weslr_main.py` which is a different file). The plan treats `main.py`, `weslr_main.py`, `weslr/chat_responder.py`, `dialogue.py`, and `chat_ui.py` as protected. `weslr/main.py` is recorded as N/A.

---

## 3. Current Domain Role Map

| Domain | Role | Auth | Current behavior |
|---|---|---|---|
| `weslr.de` | Public WESLR website + project/status tracker | None | Static `/home/pr0/projects/weslr-v1-ui-website/site/`, 200 OK |
| `www.weslr.de` | Apex redirect | None | 301 → `https://weslr.de` |
| `chat.weslr.de` | WESLR protected chat/runtime interface | htpasswd | Static shell + `/api/*` → protected backend on `127.0.0.1:8092` |
| `staging.weslr.de` | Reserved for future marketplace/artifact staging | htpasswd | Currently serves `staging-preview-20260622/` (legacy preview) |
| `preview.weslr.de` | Future protected website-copy preview | (planned) | Not deployed yet |

**Boundaries reaffirmed:**
- `weslr.de` is read-only public; it must never serve chat responses, expose session state, expose protected workflow internals, or accept input
- `chat.weslr.de` is read-write protected; it accepts input only from authenticated sessions and only through the `/api/*` proxy boundary
- `staging.weslr.de` is reserved for future marketplace use; it is not part of this plan

---

## 4. Current `chat.weslr.de` State

**Nginx block** (`/etc/nginx/conf.d/weslr-unified-8080.conf`, lines ~46–98):
- `listen 8080; server_name chat.weslr.de;`
- `auth_basic "WESLR Chat Interface"; auth_basic_user_file /etc/nginx/.htpasswd-weslr-staging;`
- Cache-Control: no-store
- Hidden-file block (`location ~ /\. { deny all; return 404; }`)
- `location ^~ /api/auth/` → `proxy_pass http://127.0.0.1:8092;`
- `location = /api/message` → `proxy_pass http://127.0.0.1:8092;` (exact-match POST)
- `location /` → `root /var/www/weslr-chat-app-shell;` (static shell)

**Static shell:** `/var/www/weslr-chat-app-shell/index.html` (and `old-workflow-preview.html` under `/diagnostics/workflow-preview/`)

**Backend:** `tools/protected_non_model_workflow_server.py` running on `127.0.0.1:8092` (PID 3529476 since 2026-06-10)
- Bound to loopback only; not publicly exposed directly
- Fronted by nginx auth_basic at the public boundary

**Auth:** htpasswd file `/etc/nginx/.htpasswd-weslr-staging` (mode 640, group www-data)
- Username: `weslr` (per earlier inspection)
- Password: not in Nova's hands (operator-controlled)

**Public path:** `https://chat.weslr.de/`
- Unauthenticated → 401 with `WWW-Authenticate: Basic realm="WESLR Chat Interface"`
- Authenticated → static shell at `/var/www/weslr-chat-app-shell/index.html`
- Authenticated → `/api/auth/*` and `/api/message` proxy to `:8092`

**What is currently wired:**
- ✅ Public tunnel (Cloudflare → port 8080)
- ✅ Nginx auth gate
- ✅ Static chat shell
- ✅ Backend proxy for `/api/auth/*` and `/api/message`
- ✅ Backend process running and bound to loopback
- ✅ htpasswd credential file in place

**What is NOT yet wired (customer-grade gaps):**
- ❌ Structured per-session audit trail (current backend logs are basic)
- ❌ Runtime wrapper that gates `respond_chat` / `cmd_speak` behind capability discovery + operator authority
- ❌ Health checks (HTTP, backend loopback, DB if any)
- ❌ Monitoring (uptime, error rate, latency, capacity)
- ❌ Pilot-user flow (request → review → approve → credential → first test message)
- ❌ Admin/operator control surface (pause, replay, audit, rotate credentials)
- ❌ Rollback plan (no documented procedure to revert any wiring change)
- ❌ Backup plan (no documented procedure to back up state before wiring change)
- ❌ Privacy boundary (what is logged vs. what is redacted is not codified)
- ❌ Forbidden-exposure enforcement (no explicit deny-list of what must never appear in any customer-visible artifact)

---

## 5. Customer-Grade Target Definition

A `chat.weslr.de` environment is **customer-grade** when all of the following are true:

| # | Property | Evidence |
|---|---|---|
| 1 | Public auth boundary is enforced | htpasswd (or stronger) at nginx; 401 unauthenticated |
| 2 | Backend is loopback-only | `:8092` bound to `127.0.0.1`; not publicly reachable |
| 3 | Every protected-file entry is wrapped | `respond_chat`, `cmd_speak`, `interpret_human_turn`, `format_reply` are gated by a runtime wrapper that checks capability + operator authority |
| 4 | Every customer message has a session id | Session is created on first message, persists across messages, expires or rotates per policy |
| 5 | Every session has a bounded lifetime | Idle timeout + max lifetime; configurable |
| 6 | Logging captures operator-authorized metadata only | Never raw prompts, never raw replies, never credentials, never PII without explicit operator action |
| 7 | Backup exists before any wiring change | Snapshot of backend state + nginx config + htpasswd + relevant scripts |
| 8 | Rollback path is documented and tested | One-command revert to last known-good state |
| 9 | Health checks exist and are runnable | HTTP 200 on `/health` (loopback), backend loopback check, log freshness check |
| 10 | Monitoring exists at minimum to detect failure | Periodic ping + alert to operator on degradation |
| 11 | Pilot-user flow is reproducible | Operator can onboard a pilot user in ≤5 minutes without runtime code edits |
| 12 | Operator controls exist for pause/audit/rotate | Documented CLI or HTTP endpoint, all behind operator auth |
| 13 | Public/private separation is enforced at the HTTP boundary | No protected routes leak to `weslr.de`; no public routes leak to `chat.weslr.de` |
| 14 | Forbidden exposures are denied at multiple layers | nginx deny-list + backend deny-list + log-scrubber + audit |
| 15 | Forbidden claims are not present in any customer-visible artifact | AGI, sentience, consciousness, benchmark, public-science, autonomous-self-improvement, production-ready, live-public-runtime are not claimed anywhere customer-visible |

**Customer-grade does not include:**
- Multi-tenant isolation
- Public OAuth / public signup
- Public marketplace
- Live shadow calls (real provider/LLM execution)
- AGI / sentience / consciousness / public-science claims

---

## 6. Required Authentication Boundary

**Goal:** Every request to `chat.weslr.de` (and `/api/*`) is bound to an authenticated identity.

**Layer 1 — Edge (nginx)**
- ✅ Already in place: `auth_basic "WESLR Chat Interface"; auth_basic_user_file /etc/nginx/.htpasswd-weslr-staging;`
- Keep htpasswd for the **operator and pilot users** in the same file, with comment-style prefixes per user (e.g., `operator:hash`, `pilot_<n>:hash`)
- **Forbidden:** moving the htpasswd outside `/etc/nginx/`, weakening the file mode (must stay 640 root:www-data or stricter), or sharing the same htpasswd with `staging.weslr.de` (different realms; consider splitting later)

**Layer 2 — Application (backend on `:8092`)**
- The backend must NOT trust the nginx auth_basic as identity; it must re-bind the identity per request using a session token issued at `/api/auth/login`
- Each `/api/message` call must carry a valid session token; otherwise 401
- Session tokens are signed, time-limited, and bound to one identity

**Layer 3 — Operator override**
- Operator must retain a master credential path that can pause any session, force-logout any identity, or rotate all credentials
- This is the kill switch

**Auth model recommendation for V1:** htpasswd at nginx + signed-cookie session at backend. OAuth/OIDC is out of scope until the operator decides to introduce public identity.

---

## 7. Required Runtime Wrapper Boundary

**Goal:** No protected-file entry can be called without an explicit wrapper that checks capability + operator authority.

**Pattern (recommended):**

```
HTTP /api/message (with session token)
    ↓
backend.api.dispatch(request)
    ↓
weslr.runtime_wrapper.authorize(action="respond_chat", session=..., capability_set=...)
    ↓
[authorized] → weslr.chat_responder.respond_chat(...)
[denied]    → return operator-gated fallback or 403
```

**Wrapper responsibilities (must exist before any `respond_chat` call):**
- Identity check: is the session bound to a known operator or pilot user?
- Capability check: is `respond_chat` in the session's authorized capability set?
- Operator-authority check: if the request is "red-zone" (e.g., self-modification, daemon start, OAuth), require an explicit operator approval token
- Audit capture: log the authorized action with identity + timestamp + capability + outcome
- Denial fallback: return operator-gated fallback content (never crash, never leak reason)
- Forbidden-action deny-list: hard-deny any action matching the forbidden list (e.g., autonomous-self-modification, public-runtime exposure)

**Files that must wrap:**
- `weslr/chat_responder.py::respond_chat` (and any helper it calls)
- `main.py::cmd_speak` (operator voice channel)
- `dialogue.py::interpret_human_turn`
- `weslr/omnichat/response_expander.py::format_reply`

**Wrapper must live in a NEW file**, e.g., `weslr/runtime_wrapper.py`, so that the protected files themselves are not modified. This preserves the boundary.

---

## 8. Required Session Boundary

**Session record (minimum fields):**
- `session_id` (UUID, signed)
- `identity_id` (operator or pilot user id)
- `created_at`, `last_seen_at`, `expires_at`
- `capability_set` (allowed actions)
- `red_zone_acknowledged_at` (timestamp of last operator approval, if any)
- `state_snapshot_ref` (pointer to persistent state, if any)
- `audit_log_ref` (pointer to audit entries)

**Session lifecycle:**
- Created on first authenticated message
- Persists for the duration of the session lifetime (default: 24h idle, 7d absolute — configurable)
- Expired sessions are not silently renewed; they require re-auth
- One identity can have multiple sessions; sessions do not share state by default

**Session storage:**
- Local JSON or SQLite file at a known path (e.g., `/home/pr0/weslr_state/sessions/`)
- NOT in the website repo
- NOT in the runtime repo
- Backup as part of the wiring-change backup step

---

## 9. Required Logging / Privacy Boundary

**Safe to log (operator-authorized metadata only):**
- Timestamp
- Session id
- Identity id (operator or `pilot_<n>`)
- Requested action (capability name)
- Outcome (authorized / denied / fallback / error)
- Latency
- Health-check result
- Wrapper denial reason category (not full reason — to avoid leaking internals)

**Forbidden to log (never, under any circumstance):**
- Raw user prompt text
- Raw assistant reply text
- Credentials (htpasswd values, session signing keys, OAuth secrets)
- PII without explicit operator action (full name, email, phone, address)
- Internal file paths that reveal implementation (e.g., `/home/pr0/projects/weslr/weslr/chat_responder.py`)
- Internal PIDs / session tokens in plaintext
- Hidden prompts, system prompts, or chain-of-thought traces
- Source bodies fetched by evidence RAG (only source IDs and trust scores)
- Provider/LLM API responses
- Any text that contains a forbidden claim (AGI, sentience, etc.) — log-scrubber must redact

**Log access:**
- Logs are written to `/home/pr0/weslr_state/logs/`
- Read access is operator-only (file mode 640, group operator)
- Logs are rotated daily; rotation is automated if cron is available, manual otherwise
- Log retention: 30 days default; configurable

---

## 10. Required Backup / Rollback Plan

**Before any wiring change:**
1. Snapshot the current backend process state (PID, port, command line)
2. Snapshot the current nginx config: `cp /etc/nginx/conf.d/weslr-unified-8080.conf /home/pr0/backups/weslr-chat-pre-<date>-<slug>.conf`
3. Snapshot htpasswd: `cp /etc/nginx/.htpasswd-weslr-staging /home/pr0/backups/weslr-chat-pre-<date>-<slug>-htpasswd` (mode preserved)
4. Snapshot any new wrapper file(s) from prior versions, if applicable
5. Snapshot session state directory, if it exists
6. Verify each snapshot is readable and timestamped

**Rollback procedure (documented):**
1. Stop the backend: `kill <pid>` (or via supervisor if one exists)
2. Restore nginx config from snapshot
3. `sudo nginx -t && sudo systemctl reload nginx`
4. Restore htpasswd from snapshot (mode 640 root:www-data)
5. Restart backend with the previous command line
6. Smoke-test: `curl -sI https://chat.weslr.de/` returns 401 unauthenticated

**Rollback target time:** <5 minutes from operator decision to fully restored state.

---

## 11. Required Health Checks

**Layer 1 — Edge (external HTTP)**
- `curl -sI https://chat.weslr.de/` → 401 (auth-gated, expected)
- `curl -sI -u <pilot>:<pw> https://chat.weslr.de/` → 200 (auth-gated, static shell)
- `curl -sI -u <pilot>:<pw> https://chat.weslr.de/api/health` → 200 (backend health endpoint must exist)

**Layer 2 — Backend (loopback)**
- `curl -s http://127.0.0.1:8092/health` → 200 (must exist; if missing, add it without editing protected files — see first implementation slice)
- `curl -s http://127.0.0.1:8092/api/auth/whoami` → returns identity
- Backend PID exists: `ps -p <pid>` returns the running process

**Layer 3 — Static shell**
- `curl -sI http://127.0.0.1:8080/var/www/weslr-chat-app-shell/` (loopback direct) → 200
- Or via nginx: `curl -s -u <pilot>:<pw> -H "Host: chat.weslr.de" http://127.0.0.1:8080/`

**Health check script:** `scripts/chat_weslr_de_health_check.sh` (proposed) — runs all three layers and exits non-zero on any failure.

---

## 12. Required Monitoring

**Minimum viable monitoring (manual cron or operator-triggered):**
- Every 5 minutes: HTTP 401 unauthenticated check (proves auth gate is up)
- Every 5 minutes: HTTP 200 authenticated static-shell check (proves shell serves)
- Every 5 minutes: backend `/health` check on `:8092`
- Every 1 minute: backend PID exists check

**Alerting:** No public alerting in V1. Operator is alerted via their own heartbeat/automation pipeline if a check fails. (Out of scope for this plan; mentioned for future implementation.)

**What is NOT monitored (forbidden in customer-grade V1):**
- Customer message content (privacy boundary)
- LLM/provider latency (no live shadow calls)
- Customer satisfaction scores
- Any metric that would require capturing customer text

---

## 13. Required Admin / Operator Controls

**Operator control surface (minimum):**
- **Pause:** stop accepting new messages without killing the backend; existing sessions can finish
- **Force-logout:** invalidate one or all sessions
- **Rotate credentials:** rotate htpasswd for any identity; rotate session signing key
- **Audit query:** list sessions for an identity, list actions in a time range (metadata only)
- **Replay (dry):** for a given session, list the capabilities that were used (metadata only — no replay of content)
- **Rollback:** execute the documented rollback procedure
- **Backup:** execute the documented backup procedure

**Controls must:**
- Be reachable only from loopback or operator-authenticated paths
- Never expose raw content
- Never accept unauthenticated commands
- Be logged as operator actions (audit trail)

**Operator controls are NOT customer-facing.** Customers (pilot users) cannot pause, rotate, or audit. They can only send messages and receive operator-gated replies.

---

## 14. Required Pilot-User Flow

**Onboarding (operator-controlled):**
1. Operator receives pilot request via `/pilot/` form on `weslr.de`
2. Operator reviews; if approved, operator generates an htpasswd entry for a new `pilot_<n>` identity
3. Operator shares credentials with pilot user out-of-band (never via the protected chat itself)
4. Pilot user navigates to `https://chat.weslr.de/`
5. Browser prompts for htpasswd; pilot enters `pilot_<n>:<pw>`
6. Static shell loads
7. Pilot sends first message via `/api/message`
8. Backend creates a session, binds it to `pilot_<n>`, records audit metadata
9. Backend authorizes via runtime wrapper; if denied, returns operator-gated fallback
10. If authorized, `weslr.chat_responder.respond_chat` runs in a sandboxed context; reply is filtered through the operator-gated fallback path before returning to the pilot

**Offboarding:**
1. Operator deletes the htpasswd entry for `pilot_<n>`
2. Operator invalidates any active sessions for that identity
3. Operator retains audit metadata for the configured retention period

**Pilot user must NOT have:**
- Operator powers (pause, audit, rotate)
- Access to other pilots' sessions
- Access to source code, hidden prompts, or runtime internals
- A way to escalate capabilities without operator action

---

## 15. Required Public / Private Separation

**Public (`weslr.de`):**
- Read-only static
- No `/api/*` paths exposed
- No session cookies accepted
- No form submissions that hit protected backends
- All references to `chat.weslr.de` are informational only (link, no embed, no iframe)

**Private (`chat.weslr.de`):**
- Auth-gated
- `/api/*` paths route only to loopback backend on `:8092`
- No link from public pages into protected chat content (only into the auth-gated entry page)
- No tracking pixel, no analytics, no third-party script that could leak session data

**Boundary enforcement (defense in depth):**
- **nginx:** server_name separation (`weslr.de` vs `chat.weslr.de`); static root separation; API paths only on `chat.weslr.de`
- **backend:** identity check + capability check before any action
- **runtime wrapper:** deny-list of forbidden actions
- **log scrubber:** redacts forbidden exposures from any log line before write

---

## 16. Forbidden Claims and Forbidden Exposures

**Forbidden claims (must never appear in any customer-visible artifact on `chat.weslr.de`):**
- AGI
- Sentience, consciousness, self-awareness, autonomous self-improvement
- Benchmark proof, certification, public-science proof
- Production-ready, live public runtime, public marketplace
- Any claim that WESLR is generally available to the public

**Forbidden exposures (must never be returned, logged, or displayed):**
- Raw user prompt text (in logs or in error messages)
- Raw assistant reply text (in logs)
- Credentials (htpasswd values, session keys, OAuth secrets)
- PII without explicit operator action
- Internal file paths (`/home/pr0/...`, `/var/www/...`, `/etc/nginx/...`)
- Internal PIDs, session tokens in plaintext
- Hidden prompts, system prompts, chain-of-thought traces
- Source bodies (only IDs and trust scores)
- Provider/LLM API responses
- Real shadow-call outputs

**Enforcement layers:**
1. nginx location deny rules
2. Backend request validation
3. Runtime wrapper deny-list
4. Log scrubber
5. Operator audit (manual review)

---

## 17. Allowed Future Files

These are NEW files that future implementation slices may create. None of them modify protected files.

**Backend wrapper (V1 priority):**
- `weslr/runtime_wrapper.py` — gate for `respond_chat`, `cmd_speak`, etc.
- `weslr/session_manager.py` — session lifecycle
- `weslr/audit_log.py` — safe audit capture
- `weslr/forbidden_exposure_filter.py` — output-side filter

**Operator control surface:**
- `tools/operator_control_server.py` — loopback-only admin HTTP (port 8093 or similar; never publicly exposed)
- `scripts/chat_weslr_de_health_check.sh` — three-layer health check
- `scripts/chat_weslr_de_backup.sh` — backup procedure
- `scripts/chat_weslr_de_rollback.sh` — rollback procedure

**State directory (outside the repo):**
- `/home/pr0/weslr_state/sessions/` — session storage
- `/home/pr0/weslr_state/logs/` — audit logs
- `/home/pr0/weslr_state/health/` — health-check snapshots
- `/home/pr0/weslr_state/backups/` — wiring-change backups

**Documentation:**
- `docs/CHAT_WESLR_DE_OPERATOR_RUNBOOK_V1.md` — operator procedures (pause, rotate, audit, rollback)
- `docs/CHAT_WESLR_DE_PILOT_USER_GUIDE_V1.md` — what a pilot user can and cannot do

---

## 18. Forbidden Files

**Protected runtime files (must not be edited by wiring work):**
- `weslr/chat_responder.py`
- `weslr/main.py` (does not exist on this branch — recorded as N/A)
- `main.py`
- `weslr_main.py` (recorded as additional protection; not in operator's list but functionally similar)
- `dialogue.py`
- `chat_ui.py`

**Other files that must remain untouched by this plan's future implementation:**
- `tools/protected_non_model_workflow_server.py` — the existing `:8092` backend. Wiring work must adapt around it; not edit it.
- `/etc/nginx/.htpasswd-weslr-staging` — credentials are operator-managed, not edited by wiring scripts.
- `/var/www/weslr-chat-app-shell/index.html` and any other file in `/var/www/weslr-chat-app-shell/` — the chat shell. May need updates for UX, but only as a separate, operator-approved slice.
- Anything in `weslr/protected_*` directories (if they exist) — protected by name.

**Forbidden operations:**
- Editing any protected file to "add a wrapper" inside it. The wrapper is a NEW file; protected files are not modified.
- Enabling live shadow calls or `respond_chat` execution against any LLM provider as part of this plan.
- Exposing any protected file path, hash, or import chain in any public or customer-visible artifact.
- Removing or weakening any existing deny rule (`location ~ /\. { deny all; }`).
- Disabling htpasswd or weakening file permissions.

---

## 19. Implementation Sequence (Safest Order)

Each slice is a separate, operator-approved, reversible unit. No slice is committed until the previous slice is validated.

**Slice 0 — Backup baseline (pre-flight, no code changes)**
- Snapshot nginx config, htpasswd, backend process state
- Document current PID, port, command line
- Output: `chat_weslr_de_backup_<timestamp>/` directory with all snapshots

**Slice 1 — Read-only health check (no code changes to protected files)**
- Add `/health` endpoint to a NEW file or to a non-protected module
- If the existing `:8092` backend already has a health endpoint, document it; if not, add one in a way that does not edit protected files
- Wire `scripts/chat_weslr_de_health_check.sh` to call all three layers
- Validate: all checks return success without touching protected files
- **Validation gate:** `git diff --quiet HEAD -- weslr/chat_responder.py main.py dialogue.py chat_ui.py`

**Slice 2 — Runtime wrapper skeleton (no protected-file edits)**
- Create `weslr/runtime_wrapper.py` with `authorize(action, session, capability_set)` returning `Authorized | Denied | Fallback`
- No calls to protected files yet; wrapper is standalone
- Unit test: wrapper denies every action by default; allows only actions in the capability set; returns Fallback for unknown actions
- **Validation gate:** `git diff --quiet HEAD -- weslr/chat_responder.py main.py dialogue.py chat_ui.py`

**Slice 3 — Session manager (no protected-file edits)**
- Create `weslr/session_manager.py` with create / get / expire / force-logout
- Storage: `/home/pr0/weslr_state/sessions/`
- Unit test: sessions are bound, expire correctly, can be force-logged-out
- **Validation gate:** same as above

**Slice 4 — Audit log (no protected-file edits)**
- Create `weslr/audit_log.py` with safe-metadata-only write
- Log scrubber denies any line containing forbidden exposure patterns
- Test: scrubber redacts AGI, raw prompts, file paths
- **Validation gate:** same as above

**Slice 5 — Forbidden-exposure filter (output side)**
- Create `weslr/forbidden_exposure_filter.py` with deny-list patterns for forbidden claims and exposures
- Applied to any text before returning to customer or before logging
- **Validation gate:** same as above

**Slice 6 — Pilot-user onboarding (no protected-file edits; uses htpasswd + new session manager)**
- Operator generates htpasswd entry for `pilot_<n>` via documented procedure
- Operator runs onboarding script that creates the session
- Pilot sends first message via static shell
- Backend creates session via session manager
- **Validation gate:** protected files unchanged; pilot flow documented and reproducible

**Slice 7 — Operator control surface (loopback only)**
- Create `tools/operator_control_server.py` bound to `127.0.0.1:8093`
- Endpoints: pause / force-logout / rotate / audit / rollback / backup
- All endpoints require an operator session token
- **Validation gate:** protected files unchanged; control surface bound to loopback only

**Slice 8 — Monitoring (read-only cron or operator-triggered)**
- Wire `scripts/chat_weslr_de_health_check.sh` into a cron job at 5-minute intervals
- Output: snapshot to `/home/pr0/weslr_state/health/`
- No alerting in V1
- **Validation gate:** protected files unchanged

**Slice 9 — Runbook and pilot user guide**
- Write `docs/CHAT_WESLR_DE_OPERATOR_RUNBOOK_V1.md`
- Write `docs/CHAT_WESLR_DE_PILOT_USER_GUIDE_V1.md`
- Operator reviews; pilot user reviews
- **Validation gate:** docs only; no code

**Slice 10 — End-to-end pilot test (no LLM execution)**
- Operator + one pilot user run through full flow
- Every action is logged via audit_log
- Every reply is filtered through forbidden_exposure_filter
- Every protected-file call goes through runtime_wrapper
- Outcome: documented pass/fail
- **Validation gate:** protected files unchanged

**Each slice is independent and reversible.** Rollback at any slice is "delete the new files, restore the snapshot."

---

## 20. First Implementation Slice Recommendation

**Recommended first slice: Slice 1 (Read-only health check).**

**Why first:**
- Zero protected-file risk
- Establishes the three-layer health baseline immediately
- Produces a runnable artifact (`scripts/chat_weslr_de_health_check.sh`)
- Validates the boundary (protected files unchanged) using the operator's exact validation commands

**Acceptance criteria for Slice 1:**
- `scripts/chat_weslr_de_health_check.sh` exists, executable, returns 0 on a healthy `chat.weslr.de`
- All three layers report green
- `git diff --quiet HEAD -- weslr/chat_responder.py main.py dialogue.py chat_ui.py` returns empty
- `python3 weslr/tests/release_gate_v1.py` passes (or is documented why it doesn't apply to this slice)
- `bash scripts/weslr_release_check.sh` passes (or is documented why it doesn't apply)
- Output: `chat_weslr_de_health_v1_<timestamp>.json` snapshot

**No code in protected files. No LLM execution. No public OAuth. No public signup. No claim leakage.**

---

## 21. Validation Plan

**Per-slice validation (mandatory):**
1. `git diff --check` — whitespace / conflict sanity
2. `python3 weslr/tests/release_gate_v1.py` — release gate (T1–T6 harness)
3. `bash scripts/weslr_release_check.sh` — release-check shell wrapper (calls release gate + self_test)
4. Protected-file integrity:
   - `git diff --quiet HEAD -- weslr/chat_responder.py`
   - `git diff --quiet HEAD -- weslr/main.py` (N/A on this branch)
   - `git diff --quiet HEAD -- main.py`
   - `git diff --quiet HEAD -- dialogue.py`
   - `git diff --quiet HEAD -- chat_ui.py`
5. Health check: `bash scripts/chat_weslr_de_health_check.sh`
6. Forbidden-claim scan: search the new files for AGI / sentience / consciousness / benchmark / public-science / autonomous-self-improvement / production-ready / live-public-runtime / public-marketplace; any match must be in "not claimed" framing only
7. Forbidden-exposure scan: search the new files for raw prompt patterns, credential patterns, internal path patterns; any match is a fail

**End-to-end validation (Slice 10 only):**
- Operator runs full pilot flow
- Audit log captures every action
- Every reply passes through filter
- Outcome documented

**Abort conditions (any of):**
- Validation gate fails
- Protected file diff is non-empty
- Health check fails after change
- Forbidden-claim or forbidden-exposure scan finds a match in "claimed" framing
- Operator aborts

---

## 22. Abort Conditions

The plan aborts (rolls back, no commit) if any of the following occur at any slice:

1. **Protected file modified.** Detected by `git diff --quiet HEAD -- <protected>`. Rollback: revert the protected file change; abort the slice; investigate how the wrapper attempted to modify protected code.
2. **Release gate fails.** Detected by `python3 weslr/tests/release_gate_v1.py` exit non-zero. Rollback: revert all changes in the slice; re-run release gate; if it passes on HEAD without the slice, the slice introduced the failure.
3. **`git diff --check` reports whitespace or conflict.** Detected by exit non-zero. Rollback: fix the whitespace; if conflict is real, abort the slice.
4. **Health check fails after change.** Rollback: restore snapshot; re-run health check; if it passes on the snapshot, the slice introduced the failure.
5. **Forbidden-claim scan finds an "affirmative" match.** Rollback: remove the claim; re-scan.
6. **Forbidden-exposure scan finds any match.** Rollback: scrub; re-scan.
7. **Operator aborts.** Operator-initiated; no questions asked; immediate rollback.
8. **Wrapper enters a deny-then-allow cycle (oscillation).** Detected by audit log showing repeated Denied → Allowed transitions for the same action in the same session. Rollback: force-logout the session; investigate.

---

## 23. Recommended Next Lane

**Lane recommendation:** Continue with **Slice 1** (read-only health check) as the immediate next implementation. Slice 1 is the safest starting point: zero protected-file risk, runnable artifact, baseline established.

**After Slice 1 is green:**
- Slice 2 (runtime wrapper skeleton)
- Slice 3 (session manager)
- Slice 4 (audit log + scrubber)
- Slice 5 (forbidden-exposure filter)

**After Slices 2–5 are green:**
- Slice 6 (pilot-user onboarding — first time a real customer-style identity interacts with the protected chat)
- Slice 7 (operator control surface)
- Slice 8 (monitoring cron)
- Slice 9 (runbook + pilot guide)
- Slice 10 (end-to-end pilot test)

**Out-of-scope until operator decides otherwise:**
- Live shadow calls or `respond_chat` execution against any LLM provider
- Public OAuth or public signup
- Multi-tenant isolation
- Public marketplace
- Any forbidden claim in customer-visible artifacts

---

## 24. Final Judgment

**`chat_weslr_de_customer_grade_wiring_plan_valid_ready_for_review`**

The plan is complete. It answers all 20 planning questions, defines the customer-grade target concretely, identifies the 15 customer-grade properties as the acceptance bar, and proposes a 10-slice implementation sequence with Slice 1 (read-only health check) as the safest first step. Protected files are listed and will be untouched by every slice in the sequence. Validation, rollback, abort conditions, and forbidden-claim/exposure enforcement are specified at every layer.

**Path note for the record:** The operator-supplied path `/data/data/com.termux/files/home/weslr-pr47-clean` was not present; the plan was written against the correct worktree at `/home/pr0/projects/weslr-run-first-live-searxng-sample-20260613` on branch `nova-occ-discovery-doctrine-implementation-20260613` (which tracks `origin/occ-discovery-doctrine-implementation-20260613`).

**`weslr/main.py` note:** Operator's protected-file list includes `weslr/main.py`, but this file does not exist on the branch. The plan treats `main.py` (repo root), `weslr_main.py` (also protected), `weslr/chat_responder.py`, `dialogue.py`, and `chat_ui.py` as protected.

---

## Appendix A — Validation Run Output

(to be appended after running `git diff --check`, `python3 weslr/tests/release_gate_v1.py`, `bash scripts/weslr_release_check.sh`, and the protected-file diff checks; plan-write lane stops after the plan file is created; actual runs are part of the validation section of the report, not part of the plan content)