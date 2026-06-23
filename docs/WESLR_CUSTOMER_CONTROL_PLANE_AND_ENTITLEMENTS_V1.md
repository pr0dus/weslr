# WESLR Customer Control Plane and Entitlements V1

**Author:** Nova
**Date:** 2026-06-23
**Status:** DESIGN ONLY — no implementation, no infra changes, no push
**Scope:** Customer/operator control plane and entitlement model for `chat.weslr.de`
**Out of scope:** Slice 4 audit logging, `weslr/audit_log.py`, `weslr/forbidden_exposure_filter.py`, dashboard backend/frontend, billing integration, Stripe or any payment provider, real customers, pilot users, real subscriptions, real session persistence, `/home/pr0/weslr_state/` writes, edits to runtime wrapper, session manager, or any protected file, runtime code execution, `respond_chat` invocation, real shadow calls, provider/model calls, nginx changes, backend restarts, htpasswd changes, `weslr.de` / `chat.weslr.de` / `staging.weslr.de` infrastructure changes, remote push

---

## 0. Purpose and Scope

### Why this design now

Slices 1–3 (canonical HEAD `11fdbf76`) provide:
- Slice 1 — host-role-aware read-only health check (`scripts/chat_weslr_de_health_check.sh`)
- Slice 2 — runtime wrapper skeleton (`weslr/runtime_wrapper.py`) with default-deny authorization
- Slice 3 — session manager skeleton (`weslr/session_manager.py`) with bounded lifetime, terminal force-logout, and JSON-safe conversion

These three slices together provide a *boundary*, not a *product*. They do not yet define:
- Who is allowed to do what (entitlements)
- How an operator manages the system (control plane)
- How subscription state maps to runtime capability (payment → entitlement)
- What audit logging must later record (governance evidence)

This document defines the **shape of the customer/operator control plane and the entitlement model** so that Slice 4 (audit log) and later slices can be designed and implemented with the right invariants.

### What this document is NOT

- ❌ Not public product readiness
- ❌ Not a payment launch plan
- ❌ Not runtime activation
- ❌ Not a dashboard implementation spec
- ❌ Not a billing integration spec
- ❌ Not a customer onboarding script
- ❌ Not a pilot user provisioning flow

### What this document IS

- ✅ A **design for the data model** of users, accounts, sessions, entitlements, subscriptions, and operator actions
- ✅ A **design for the entitlement boundary** that maps payment/subscription state → capability set → runtime authorization
- ✅ A **design for the operator control surface** that defines what an operator can do, what they cannot do, and what audit must record
- ✅ A **contract for Slice 4 (audit log)** — i.e. what audit must record, in what shape, with what redactors

---

## 1. Operator Dashboard Model

The operator dashboard is a **read-mostly surface** that aggregates metadata from several control-plane subsystems. It is not a runtime entry point and not a write surface for arbitrary commands.

### 1.1 Data sections

| Section | Source | Purpose |
|---|---|---|
| **User list** | User/account registry (control-plane subsystem, not in runtime) | Operators see who exists, what their status is, when they were last active |
| **Pilot users** | Same registry, filtered by `pilot_*` statuses | Operators see who is in pilot mode, with capability limits |
| **Account state** | Account state machine (see §2) | Operators see `invited`, `pilot_active`, `manual_paid`, etc. |
| **Session state** | Session manager (read-only view) | Operators see active sessions, idle sessions, force-logged-out sessions (metadata only, no content) |
| **Entitlement state** | Entitlement packet (see §4) | Operators see what each user/role is allowed to do |
| **Billing/abo state metadata** | Subscription state (see §3) | Operators see payment status as *metadata* — never as a runtime trigger |
| **Support / escalation queue** | Ticket subsystem (out of scope tonight, but reserved) | Reserved for future |
| **Safety / blocked-status queue** | Safety subsystem (out of scope tonight, but reserved) | Reserved for future |
| **Health status** | Slice 1 health check (read-only) | Operators see green/yellow/red per layer |
| **Operator actions** | Operator action log (Slice 4) | Operators see their own past actions, with metadata only |

### 1.2 Dashboard properties

- **Read-mostly:** the dashboard's primary role is to display state. Mutations (pause, force-logout, rotate) happen through **explicit operator commands**, not through dashboard "click to edit" forms that bypass the operator-action log.
- **Operator-only:** the dashboard is not customer-facing. Customers never see the operator dashboard.
- **Loopback-only at the backend:** the dashboard's backend is bound to `127.0.0.1` (or operator-only ingress), not publicly exposed. A reverse proxy with operator-auth is allowed; a public-internet-facing dashboard is forbidden.
- **No customer PII displayed by default:** PII (full name, email, phone, address) is redacted in dashboard views unless the operator explicitly expands a record. Bulk views show only `pilot_<n>` style IDs.
- **Metadata-only:** the dashboard never displays raw prompts, raw replies, chain-of-thought, hidden prompts, provider responses, or real shadow-call outputs. Forbidden exposures (per `weslr.de` policy and Slice 2 wrapper) are not displayed.

### 1.3 What the dashboard is NOT

- ❌ Not a customer-facing product surface
- ❌ Not a billing/finance interface (that's a separate concern)
- ❌ Not a public status page
- ❌ Not a way to bypass the operator-action log

---

## 2. User / Account Statuses

Every user has an **account state** that determines their eligibility for sessions, capabilities, and operator interventions. Account states are mutually exclusive at any moment; transitions are explicit and audited.

### 2.1 Account status enum

| Status | Description | Eligible for sessions? | Eligible for capabilities? | Operator can transition? |
|---|---|---|---|---|
| `invited` | A pilot or manual user has been invited; credentials not yet issued | ❌ | ❌ | → `pilot_active`, `manual_paid`, `banned` |
| `pilot_free` | A free-pilot user; credentials issued; no manual payment | ✅ (with pilot limits) | ✅ (pilot capability set) | → `pilot_active`, `pilot_paused`, `banned`, `deletion_requested` |
| `pilot_active` | A free-pilot user is currently active | ✅ | ✅ | → `pilot_paused`, `pilot_expired`, `banned`, `deletion_requested` |
| `pilot_paused` | A pilot user is paused by an operator (temporary) | ❌ | ❌ | → `pilot_active`, `pilot_expired`, `banned`, `deletion_requested` |
| `pilot_expired` | A pilot's free period has ended; grace period may apply | ❌ (during grace) → ❌ (after grace) | ❌ | → `invited` (re-pilot), `manual_paid` (upgrade), `deletion_requested` |
| `manual_paid` | A manually-billed user (operator-handled, no Stripe) | ✅ | ✅ (manual capability set) | → `manual_unpaid`, `manual_disabled`, `banned`, `deletion_requested` |
| `manual_unpaid` | A manually-billed user is behind on payment; grace period may apply | ❌ (during grace) → ❌ (after grace) | ❌ | → `manual_paid` (paid), `manual_disabled`, `deletion_requested` |
| `manual_disabled` | A manually-billed user is disabled (post-grace) | ❌ | ❌ | → `manual_paid` (re-enabled), `deletion_requested` |
| `banned` | A user is banned (policy violation, security incident) | ❌ | ❌ | → `deletion_requested` (terminal-ish; not reversible) |
| `deletion_requested` | A user has requested data deletion; in retention period | ❌ | ❌ | → `deleted_or_revoked` (after retention) |
| `deleted_or_revoked` | A user's data has been deleted / access fully revoked | ❌ | ❌ | (terminal) |

### 2.2 Account record fields (metadata only)

```
{
  "account_id": "<opaque, e.g. pilot_42>",
  "account_status": "<one of the statuses above>",
  "account_status_changed_at": "<ISO 8601>",
  "account_status_changed_by": "<operator_ref or system:invite or system:pilot_expired>",
  "account_invited_at": "<ISO 8601>",
  "account_last_active_at": "<ISO 8601, optional>",
  "account_pii_visible_to_operator": false,
  "account_red_zone_acknowledged_at": "<ISO 8601, optional>",
  "raw_content_retained": false,
  "audit_log_ref": "<pointer to operator action log, no content>"
}
```

Notes:
- `account_pii_visible_to_operator` is `false` by default; only operator with explicit redaction-bypass authority (separate operator role) can flip it. This is metadata; PII itself is not in the record by default.
- `raw_content_retained` is always `false` per Slice 2/3 invariants.
- `account_id` is opaque; do not embed PII in the ID.

### 2.3 Status transitions

Every status transition is:
1. **Explicit** — an operator action, a system-internal event, or a time-based event
2. **Audited** — recorded in the operator action log (Slice 4) with reason label, before/after status, operator_ref, timestamp
3. **Validated** — invalid transitions are rejected (e.g., `banned` → `invited` is not allowed; only `banned` → `deletion_requested`)

Invalid transition examples:
- `banned` → `invited` (rejected; bans are non-reversible at the account-state level)
- `deleted_or_revoked` → anything (rejected; terminal)
- `pilot_expired` → `pilot_active` (rejected; must go through `invited` or `manual_paid`)

---

## 3. Subscription / Abo Status Model

This is **metadata only** for now. There is **no real billing provider** in this design. Stripe or any payment provider integration is **out of scope**.

### 3.1 Subscription status enum (metadata only)

| Status | Description | Maps to entitlement |
|---|---|---|
| `no_subscription` | No subscription yet | (none) |
| `free_pilot` | Free pilot period (default for `pilot_free` and `pilot_active` accounts) | pilot capability set |
| `trialing` | A trial period for a future paid tier | trial capability set (slightly wider than free_pilot, time-bounded) |
| `active` | A paid subscription is active (metadata; no real billing) | full capability set per entitlement packet |
| `past_due` | A paid subscription is past due (manual billing) | reduced capability set during grace |
| `unpaid` | A paid subscription is unpaid after grace | (none) |
| `canceled` | A subscription was canceled (manual billing) | pilot capability set during grace, then (none) |
| `refunded` | A subscription was refunded (metadata) | (none) |
| `disputed` | A subscription has a dispute (metadata) | (none; no runtime action) |
| `grace_period` | A subscription is in a manual grace period | reduced capability set |
| `disabled_for_nonpayment` | A subscription is disabled for non-payment (terminal-ish) | (none) |

### 3.2 Critical invariant

**Subscription/abo status must NOT directly call runtime code.** The control plane translates subscription state into an **entitlement packet** (see §4), and the runtime wrapper authorizes based on the entitlement packet, not on the raw subscription state.

```
subscription state ──> entitlement packet (capabilities) ──> runtime wrapper (authorization)
```

The runtime wrapper never asks "what is the user's subscription state?" — it only asks "is this action in the session's capability set?" The capability set comes from the entitlement packet, which is the only place where subscription state is interpreted.

This separation ensures:
- Subscription/billing state can change without affecting runtime behavior in unexpected ways
- The runtime wrapper remains a pure-Python, no-I/O boundary (per Slice 2)
- Payment provider integration (when added later) is a control-plane concern, not a runtime concern

### 3.3 Subscription record fields (metadata only)

```
{
  "subscription_id": "<opaque>",
  "account_id": "<opaque>",
  "subscription_status": "<one of the statuses above>",
  "subscription_status_changed_at": "<ISO 8601>",
  "subscription_status_changed_by": "<operator_ref or system:grace or system:cancel>",
  "subscription_tier": "<opaque, e.g. pilot_v1, manual_v1>",
  "subscription_period_start": "<ISO 8601>",
  "subscription_period_end": "<ISO 8601>",
  "subscription_grace_period_end": "<ISO 8601, optional>",
  "subscription_metadata": {},  # no PII, no payment data
  "raw_content_retained": false
}
```

**Forbidden in subscription records:**
- ❌ No credit card numbers, no bank info, no payment instrument data
- ❌ No real Stripe IDs (use opaque local IDs only)
- ❌ No PII
- ❌ No raw customer prompts or replies

---

## 4. Entitlement Model

The entitlement packet is the **only thing** the runtime wrapper consults (via the session's capability_set). It is a metadata-only struct that is recomputed whenever account state or subscription state changes, and it is signed/attested by the operator or by the control plane.

### 4.1 Entitlement packet fields

```
{
  "entitlement_id": "<opaque>",
  "account_id": "<opaque>",
  "entitlement_version": "<opaque, e.g. v1>",
  "entitlement_computed_at": "<ISO 8601>",
  "entitlement_computed_by": "<operator_ref or system:recompute>",
  "allowed_capabilities": ["<capability name>", ...],
  "max_messages_per_day": <int>,
  "max_sessions": <int>,
  "file_upload_allowed": <bool>,
  "project_memory_allowed": <bool>,
  "marketplace_artifact_access_allowed": <bool>,
  "model_tool_access_allowed": <bool>,
  "chat_access_enabled": <bool>,
  "operator_override_flags": {
    "operator_can_force_logout": <bool>,
    "operator_can_pause": <bool>,
    "operator_can_rotate_credentials": <bool>,
    "operator_can_revoke_capability": <bool>,
    "operator_can_extend_grace": <bool>
  },
  "entitlement_expiry": "<ISO 8601, optional>",
  "entitlement_grace_period_end": "<ISO 8601, optional>",
  "raw_content_retained": false,
  "audit_log_ref": "<pointer>"
}
```

### 4.2 Capability set mapping

The `allowed_capabilities` list is the **only** thing the runtime wrapper sees. It must be a strict subset of the safe actions defined in Slice 2 (`weslr.runtime_wrapper.SAFE_ACTIONS_V1`):

```python
SAFE_ACTIONS_V1 = frozenset({
    "health_check_read",
    "status_read",
    "operator_review_packet_read",
})
```

**Mapping rules (control-plane logic, not runtime):**
- `pilot_free` / `pilot_active` → `["health_check_read", "status_read"]`
- `pilot_paused` → `[]` (no capabilities; cannot even call health_check_read via this account)
- `pilot_expired` (during grace) → `["status_read"]` (read-only status, no health probe)
- `manual_paid` (active) → `["health_check_read", "status_read", "operator_review_packet_read"]` (full read-only set)
- `manual_unpaid` (during grace) → `["status_read"]` (reduced)
- `manual_disabled` → `[]`
- `banned` → `[]`
- `deletion_requested` → `[]`
- `deleted_or_revoked` → `[]`
- Operator role (separate from any of the above) → `["health_check_read", "status_read", "operator_review_packet_read"]` plus operator override flags

These mappings are **policy**, not implementation. They will be codified in a future slice.

### 4.3 Quotas and limits

| Field | Default for `pilot_*` | Default for `manual_paid` | Operator override? |
|---|---|---|---|
| `max_messages_per_day` | 100 | 1000 | yes (operator can raise temporarily) |
| `max_sessions` | 1 (per account_id) | 5 (per account_id) | yes (operator can raise) |
| `file_upload_allowed` | `false` | `true` | yes |
| `project_memory_allowed` | `false` | `true` | yes |
| `marketplace_artifact_access_allowed` | `false` | `true` (later) | yes |
| `model_tool_access_allowed` | `false` | `true` (later) | yes |
| `chat_access_enabled` | `true` (when capability set non-empty) | `true` (when capability set non-empty) | yes |

Note: in this design, the runtime wrapper currently only authorizes metadata-only reads. The other capabilities (`file_upload`, `model_tool_access`, etc.) are placeholders for future slices — they MUST be set to `false` until those slices exist.

### 4.4 Operator override flags

The `operator_override_flags` are per-account flags that allow an operator to act on a specific account outside the normal state-machine flow. Each flag is a metadata-only boolean:

- `operator_can_force_logout`: yes/no — operator can force-logout active sessions
- `operator_can_pause`: yes/no — operator can pause the account
- `operator_can_rotate_credentials`: yes/no — operator can rotate the account's credentials
- `operator_can_revoke_capability`: yes/no — operator can immediately remove a specific capability
- `operator_can_extend_grace`: yes/no — operator can extend a grace period beyond the default

These flags do **not** grant capabilities; they grant **operator actions**. They are recorded in the operator action log (Slice 4) when used.

### 4.5 Expiry and grace

- `entitlement_expiry` is the absolute end of the entitlement period. After this, the entitlement is no longer valid regardless of grace.
- `entitlement_grace_period_end` is the end of an optional grace period. During grace, the entitlement is still valid but at reduced capability (see §4.2).
- The runtime wrapper does NOT consult expiry directly. The control plane recomputes the entitlement packet before the session is created; the session's capability_set is what the wrapper sees.

---

## 5. Operator Control Surface

The operator control surface is the set of actions an operator can take, each of which must be:
- **Explicit** (no implicit transitions)
- **Audited** (recorded in the operator action log)
- **Bounded** (limited to a safe set)

### 5.1 Operator actions (allowed)

| Action | Effect | Audited? | Operator override flag required? |
|---|---|---|---|
| `list_accounts` | Returns a list of account records (PII redacted) | yes (read) | no |
| `view_account` | Returns one account record | yes (read) | no |
| `invite_account` | Creates an `invited` account | yes | no |
| `issue_pilot_credentials` | Transitions `invited` → `pilot_free`; issues htpasswd entry | yes | no |
| `activate_pilot` | Transitions `pilot_free` → `pilot_active` | yes | no |
| `pause_pilot` | Transitions `pilot_active` → `pilot_paused` | yes | no |
| `resume_pilot` | Transitions `pilot_paused` → `pilot_active` | yes | no |
| `expire_pilot` | Transitions `pilot_active` → `pilot_expired` | yes | no |
| `disable_manual` | Transitions `manual_paid` → `manual_disabled` | yes | no |
| `re_enable_manual` | Transitions `manual_disabled` → `manual_paid` | yes | no |
| `force_logout_session` | Force-logout a specific session (Slice 3 op) | yes | `operator_can_force_logout` |
| `pause_account` | Generic pause (any active account) | yes | `operator_can_pause` |
| `rotate_credentials` | Rotate htpasswd entry for an account | yes | `operator_can_rotate_credentials` |
| `revoke_capability` | Remove a specific capability from an account's entitlement | yes | `operator_can_revoke_capability` |
| `extend_grace` | Extend a grace period | yes | `operator_can_extend_grace` |
| `request_deletion` | Transitions `*` → `deletion_requested` | yes | no |
| `confirm_deletion` | Transitions `deletion_requested` → `deleted_or_revoked` | yes | no (operator can confirm) |
| `view_sessions` | Returns session list (metadata only) | yes (read) | no |
| `view_health` | Triggers Slice 1 health check | yes (read) | no |
| `view_audit_log` | Returns operator action log (metadata only) | yes (read) | no |

### 5.2 Operator actions (forbidden)

| Action | Why forbidden |
|---|---|
| `read_raw_prompt` | Forbidden exposure (per Slice 2/3 invariants and `weslr.de` policy) |
| `read_raw_reply` | Forbidden exposure |
| `read_credentials` | Forbidden (htpasswd values, session tokens) |
| `edit_protected_file` | Runtime code, runtime wrapper, session manager, etc. — out of operator control plane |
| `modify_runtime_behavior` | Runtime wrapper is a deterministic boundary; no operator override of its decision logic |
| `claim_agi_status` / `claim_sentience` / `claim_live_runtime` | Forbidden by `weslr.de` policy |
| `bypass_audit_log` | Audit log is mandatory; no operator can opt out |
| `unauthorized_reactivation` | Reactivating a `banned` or `deleted_or_revoked` account is a forbidden transition |

### 5.3 Operator action log fields (Slice 4 contract)

Every operator action records the following in the audit log (Slice 4 will define the storage format):

```
{
  "audit_log_entry_id": "<opaque>",
  "audit_log_version": "weslr-audit-log-v1",
  "audit_log_recorded_at": "<ISO 8601>",
  "audit_log_action_type": "<operator action name>",
  "audit_log_operator_ref": "<opaque, e.g. operator_alice>",
  "audit_log_target_account_id": "<opaque, optional>",
  "audit_log_target_session_id": "<opaque, optional>",
  "audit_log_target_resource": "<opaque, optional>",
  "audit_log_before_state": {},  # metadata only
  "audit_log_after_state": {},   # metadata only
  "audit_log_reason_label": "<machine-readable reason>",
  "audit_log_summary": "<short human-readable summary>",
  "audit_log_raw_content_retained": false,
  "audit_log_never_includes": [
    "raw_prompt", "raw_reply", "credentials", "session_token_plaintext",
    "hidden_prompt", "system_prompt", "chain_of_thought",
    "provider_response", "shadow_call_output", "password", "secret", "api_key"
  ]
}
```

The `audit_log_never_includes` list is a hard contract: Slice 4 (audit log) MUST reject any entry that would expose these keys.

### 5.4 Operator authentication and authorization

- Operator authentication: htpasswd at the operator dashboard boundary (separate from `chat.weslr.de` htpasswd; a different realm/file)
- Operator authorization: an operator's actions are gated by the operator's own role (e.g., `operator_viewer`, `operator_admin`)
- Operator action: every action goes through the operator's session (Slice 3), which has a `operator_*` capability set
- Operator session expiry: shorter than customer sessions (e.g., 1h idle, 8h absolute)

---

## 6. Pilot-User Flow (Operator-Only)

The pilot-user flow is entirely operator-controlled. Customers (pilots) do not self-onboard.

### 6.1 Onboarding (operator-controlled)

1. Operator receives a pilot request via `/pilot/` form on `weslr.de` (or via direct contact)
2. Operator reviews the request; if approved, operator creates an `invited` account
3. Operator issues htpasswd entry for the new `pilot_<n>` identity (operator action: `issue_pilot_credentials`)
4. Operator shares credentials with the pilot user out-of-band (never via the protected chat itself; never via the dashboard)
5. Operator transitions account to `pilot_active` (operator action: `activate_pilot`)
6. Pilot user navigates to `https://chat.weslr.de/`
7. Browser prompts for htpasswd; pilot enters `pilot_<n>:<pw>`
8. Static shell loads
9. Pilot sends first message via `/api/message`
10. Backend creates a session (Slice 3), binds it to `pilot_<n>`, records audit metadata (Slice 4)
11. Backend authorizes via runtime wrapper (Slice 2); if denied, returns operator-gated fallback
12. If authorized, runtime wrapper returns `health_check_read` / `status_read` results (the only safe actions in V1)

### 6.2 Offboarding (operator-controlled)

1. Operator deletes the htpasswd entry for `pilot_<n>` (operator action: `rotate_credentials` with deletion intent)
2. Operator force-logs-out any active sessions (operator action: `force_logout_session`)
3. Operator transitions account to `deletion_requested` (operator action: `request_deletion`)
4. After retention period, operator confirms deletion (operator action: `confirm_deletion`)
5. Operator retains audit metadata for the configured retention period (Slice 4)

### 6.3 Pilot user must NOT have

- ❌ Operator powers (pause, audit, rotate)
- ❌ Access to other pilots' sessions or accounts
- ❌ Access to source code, hidden prompts, or runtime internals
- ❌ A way to escalate capabilities without operator action

---

## 7. Public/Private Separation

The control plane does not change the public/private boundary established for `weslr.de` and `chat.weslr.de`. The new artifact is the **operator dashboard**, which is a third surface:

| Surface | Public? | Auth | Backend |
|---|---|---|---|
| `weslr.de` | yes | none | static |
| `chat.weslr.de` | no | htpasswd | `:8092` (loopback) + nginx |
| Operator dashboard | no | operator-auth | loopback only (new port, never public) |

The operator dashboard's backend is bound to `127.0.0.1` on a new port (e.g., `:8094` or similar). It is **not** publicly exposed. If operator access from outside the host is needed, it goes through a reverse proxy with operator-auth (separate from `chat.weslr.de` htpasswd).

---

## 8. Forbidden Claims and Forbidden Exposures (Reaffirmed)

The control plane does not introduce any new claimable surface. The following remain forbidden (per `weslr.de` policy and Slice 2/3 invariants):

- ❌ AGI, sentience, consciousness, self-awareness
- ❌ Autonomous self-improvement
- ❌ Benchmark certification, public-science proof
- ❌ Production-ready, live public runtime, public marketplace
- ❌ Any general-public availability claim

The control plane does not display, log, or expose:
- ❌ Raw prompts, raw replies, hidden prompts, system prompts, chain-of-thought
- ❌ Provider/LLM API responses
- ❌ Real shadow-call outputs
- ❌ Credentials, PII without explicit operator action
- ❌ Internal file paths that reveal implementation

---

## 9. Slice 4 (Audit Log) Contract

This design is the **upstream contract** for Slice 4. Slice 4 must:

- ✅ Create `weslr/audit_log.py` with a write API that accepts the operator action records defined in §5.3
- ✅ Reject any record that would expose keys in `audit_log_never_includes`
- ✅ Store records to `/home/pr0/weslr_state/logs/` (NEW path; do NOT use the session storage path)
- ✅ Be deterministic, pure-Python, no-I/O on the read path (writes are sequential file appends only)
- ✅ Have a test file `weslr/tests/test_audit_log_v1.py` with the operator action coverage from §5.1
- ✅ Reuse the canonical `weslr/**` allowance (no new gate edit needed)

Slice 4 MUST NOT:
- ❌ Edit any protected file
- ❌ Read or write raw prompts/replies/credentials
- ❌ Make real shadow calls or `respond_chat` invocations
- ❌ Touch nginx, htpasswd, backend, `chat.weslr.de`, or `weslr.de`

---

## 10. Slice 4 is NOT Implemented Tonight

This document is design-only. No `weslr/audit_log.py` was created. No `weslr/forbidden_exposure_filter.py` was created. No operator dashboard backend was created. No billing integration was attempted. No real customers or pilot users were created. No real subscriptions were created. No `/home/pr0/weslr_state/` writes were performed. No remote push was performed.

The work for tonight is the **design artifact** at this path. Slice 4 awaits operator approval.

---

## 11. Files Referenced

**Worktree:** `/home/pr0/projects/weslr-customer-control-plane-design-20260623`
**Branch:** `nova-weslr-customer-control-plane-design-20260623`
**Base HEAD:** `11fdbf76a11f9566f0f243ff36b162cef81cf7dd` (canonical `origin/occ-discovery-doctrine-implementation-20260613`, with Slices 1, 2, 3 cherry-picked by OCC)

**Files inspected (read-only):**
- `docs/WESLR_CHAT_WESLR_DE_CUSTOMER_GRADE_WIRING_PLAN_V1.md` (35,077 bytes)
- `docs/WESLR_CHAT_WESLR_DE_CUSTOMER_GRADE_WIRING_PLAN_REVIEW_V1.md` (32,512 bytes)
- `scripts/chat_weslr_de_health_check.sh` (19,099 bytes, host-role-aware)
- `weslr/runtime_wrapper.py` (12,449 bytes, Slice 2)
- `weslr/session_manager.py` (24,365 bytes, Slice 3)
- `weslr/tests/test_runtime_wrapper_v1.py` (15,740 bytes, 46 tests)
- `weslr/tests/test_session_manager_v1.py` (25,594 bytes, 65 tests)

**Files NOT modified:**
- All protected files (`weslr/chat_responder.py`, `main.py`, `weslr_main.py`, `dialogue.py`, `chat_ui.py`)
- `weslr/runtime_wrapper.py` (Slice 2)
- `weslr/session_manager.py` (Slice 3)
- `weslr/tests/release_gate_v1.py`
- Any nginx config, htpasswd, backend, or infra file
- `/home/pr0/weslr_state/` (not created; metadata-only path in this design)

---

## 12. Final Judgment

**`chat_weslr_de_customer_control_plane_and_entitlements_v1_design_complete`**

The design is complete. It defines the operator dashboard model, the user/account status enum (11 statuses), the subscription/abo status enum (11 statuses, metadata-only), the entitlement packet model (with strict capability-set mapping to Slice 2's `SAFE_ACTIONS_V1`), the operator control surface (20 allowed actions, 8 forbidden actions, audit-log contract for Slice 4), the pilot-user flow (operator-controlled), the public/private separation (introduces a third loopback-only surface for the operator dashboard), and the Slice 4 audit-log contract. All forbidden claims and forbidden exposures are reaffirmed. Slice 4 implementation is explicitly NOT in scope for tonight. No protected file is modified. No runtime code is executed. No infra is changed. No `/home/pr0/weslr_state/` writes are performed. No push is performed. Operator approval is required before any subsequent implementation slice.

---

## Appendix A — Recommended Next Lane

**`OPERATOR_DECIDE_SLICE_4_AUDIT_LOG_DESIGN_APPROVAL`**

The operator reviews this design. If approved, the next lane is `IMPLEMENT_SLICE_4_WESLR_CHAT_AUDIT_LOG_SKELETON` in a fresh clean worktree from canonical `origin/occ-discovery-doctrine-implementation-20260613`, with the audit-log contract from §5.3 as the binding specification.

If the operator wants to revise this design, the next lane is `REVISE_WESLR_CUSTOMER_CONTROL_PLANE_AND_ENTITLEMENTS_V1` with explicit revision instructions.

If the operator wants to defer Slice 4 and move to a different lane (e.g., operator dashboard backend, billing integration design), that decision is taken at the operator's discretion.

---

**End of design document. No implementation. No push. Awaiting operator decision.**
