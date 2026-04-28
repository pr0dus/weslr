# WESLR Safe Public Demo Architecture — V1

**Version:** 1.0
**Status:** DESIGN ONLY — not approved for deployment
**Created:** 2026-04-28
**Canonical commit:** `b9d14b36159d5f5d2b1bffcc48c134608954c352`
**Owner:** operator + lead architect

---

## SECTION 1 — Purpose

This document is the **canonical architecture design** for the WESLR public read-only demo. It defines what is allowed, what is blocked, how sessions are structured, and what OCW may and may not do during deployment.

This is **design only**. No deployment, no nginx changes, no endpoint exposure, no production code changes have been made or authorized as part of this document.

---

## SECTION 2 — Deployment Principles

| # | Principle |
|---|-----------|
| 1 | **Read-only first** — No write handler is dispatched regardless of user input |
| 2 | **No onboarding** — No user account creation, no email, no invite flow for phase 1 |
| 3 | **Anonymous session only** — Session cookie with UUIDv4; no identity linkage |
| 4 | **No raw prompt storage** — User input is never written to disk |
| 5 | **No write handlers** — `dispatch_write_handler` is unreachable in `public_demo_readonly` mode |
| 6 | **No LLM by default** — LLM disabled; cost guard active in demo mode |
| 7 | **Rate-limited** — Per-session and per-IP rate limits enforced at the application layer |
| 8 | **Off-switch required** — Operator can stop the service and remove the public route instantly |

---

## SECTION 3 — Runtime Mode

**Mode flag:** `WESLR_MODE=public_demo_readonly`

| Property | Value |
|----------|-------|
| `execution_allowed` | `False` — execution path never entered |
| `fallback_safe` | `True` — unrecognized commands return safe fallback, not errors |
| `write_handlers` | Blocked — dispatch table filtered to read-only |
| `LLM` | Disabled unless explicitly budget-guarded |
| `rate_limit` | Enforced — 10 req/min/session, 20 req/min/IP |
| `mode` | Set via `set_weslr_mode("public_demo_readonly")` at server startup |

The mode is set once at initialization. It cannot be toggled via user input.

---

## SECTION 4 — Request Flow

```
Browser
  ↓
nginx (public route → localhost:PORT)
  ↓
WESLR local demo server (interpretation.py)
  ↓
interpret_human_turn(message)
  ↓
[public_demo_readonly enforcement]
  ├─ Route matched? → return response
  ├─ Write handler attempted? → blocked, fallback_safe returned
  ├─ Rate limit exceeded? → 429 returned
  └─ Unrecognized command? → fallback_safe response
  ↓
Response (JSON, safe schema only)
  ↓
nginx → Browser
```

No intermediate agents, no LLM calls, no write paths activated.

---

## SECTION 5 — Allowed Public Routes

These routes are tested, deterministic, and safe to expose:

| Command | Path Returned | Notes |
|---------|--------------|-------|
| `show system overview` | `operator_overview` | Layer count, mode, flags |
| `show weslr status` | `weslr_status` | execution_allowed, autonomous_changes |
| `show diagnostics` | `diagnostics` | System health snapshot |
| `show iss probes` | `ISS_probe_registry_query` | Probe registry, no internal state |
| `show implementation plans` | `implementation_plan_list` | Plans available, no execution |
| `explain plan iss.not_integrated` | `plan_explanation` | Plan text only |
| `explain proposal iss.not_integrated` | `proposal_explanation` | Proposal text only |
| `plan probe probe.front_door.chat` | `ISS_probe_plan` | Probe plan, no execution |

All routes return structured JSON. No side effects. No execution.

---

## SECTION 6 — Blocked Routes

These routes must not be reachable in public demo mode:

| Blocked Command | Reason |
|-----------------|--------|
| `convert iss suggestion` | Write handler — proposal creation |
| `create proposal from iss` | Write handler — proposal submission |
| `execute probe` | Execution path — may trigger side effects |
| Any write handler | All write paths blocked in read-only mode |
| Arbitrary file/path requests | Path traversal risk; not registered as routes |
| Raw system inspection (`cat /data/...`) | Internal path leak risk |
| `execution_allowed=True` in user input | Capability mutation attack; sanitized at intake |

Route registry is filtered at dispatch time: only `read_only: True` handlers are callable.

---

## SECTION 7 — Session Model

**Phase 1 implementation:** Anonymous session cookie only

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | UUIDv4 | Generated on first request; HTTP-only cookie |
| `created_at` | ISO-8601 | Session creation time |
| `last_seen` | ISO-8601 | Last request timestamp |
| `request_count` | int | Total requests in session |
| `route_counts` | dict | `{route_name: N}` — which routes called |
| `failed_route_count` | int | Requests returning no handler match |
| `latency_stats` | dict | `p50_ms`, `p95_ms`, `p99_ms` (rolling window) |
| `rate_limit_hits` | int | Times rate limit triggered for this session |
| `abuse_flags` | list | Anomalous patterns detected (operator-visible only) |

**Forbidden:** Name, email, IP (transient only in memory), raw prompts, personal data, passwords.

Session data is **append-only**. No updates to historical records.

---

## SECTION 8 — Rate Limits

Recommended limits for first public demo:

| Limit | Value |
|-------|-------|
| Requests per session | 10 / minute |
| Requests per IP | 20 / minute |
| Max input length | 10 KB |
| Request timeout | 5 seconds |
| Max concurrent requests per IP | 5 |
| Rate limit response | HTTP 429 |

Rate limits are enforced in `interpretation.py` via `_check_rate_limit()`. If exceeded, a safe 429 response is returned with no error detail exposed.

---

## SECTION 9 — Logging

### Allowed Log Fields

| Field | Example |
|-------|---------|
| `timestamp` | `2026-04-28T07:00:00Z` |
| `route_path` | `ISS_probe_registry_query` |
| `latency_ms` | `43` |
| `status_code` | `200` |
| `session_id_hash` | SHA-256 of session_id (not the raw ID) |

### Forbidden Log Fields

- ❌ Raw user prompts or command text
- ❌ Personal data (name, email, IP stored to disk)
- ❌ Secrets, tokens, API keys
- ❌ Internal absolute paths (`/data/data/com.termux/...`)

Logs are **operational only**. They exist to diagnose service health, not to reconstruct user sessions.

---

## SECTION 10 — OCW Deployment Responsibilities

OCW (Ubuntu server / weslr.de deployment agent) may:

| Action | Notes |
|--------|-------|
| Pull from GitHub | Only reviewed commits; `--ff-only` |
| Run validation tests | `release_gate_v1.py`, `public_readiness_tests.py` |
| Inspect weslr.de config | Read-only inspection of runtime configuration |
| Prepare staging service | Setup without public exposure |
| Follow OCW_HANDOFF_V1.md | Strict adherence to handoff protocol |

OCW may **NOT**:

| Forbidden Action | Reason |
|-----------------|--------|
| Touch `e-qubs.de` | Completely off-limits, no exceptions |
| Expose production public endpoint | Until all pre-deployment gates pass |
| Edit WESLR core logic | Architecture decisions belong to OCC |
| Bypass tests | Release gate must pass before any deployment action |
| Touch TIA bridge / private commercial IP | Separate repository; not in scope |
| Run arbitrary shell commands from handoff | OCW executes only documented, reviewed scripts |

---

## SECTION 11 — Pre-Deployment Checklist

All items must pass before public exposure:

| # | Check | Validated By |
|---|-------|-------------|
| 1 | `release_gate_v1.py` passes | OCC: `python3 weslr/tests/release_gate_v1.py` |
| 2 | `public_readiness_tests.py` passes | OCC: `python3 weslr/tests/public_readiness_tests.py` |
| 3 | `public_demo_readonly` mode confirmed | `_WESLR_MODE == "public_demo_readonly"` at startup |
| 4 | Write handlers blocked | Dispatch table filtered; confirmed in test |
| 5 | Rate limiter active | `_check_rate_limit()` enforced; tested under load |
| 6 | Off-switch defined | `kill` / `systemctl stop` procedure documented |
| 7 | nginx dry-run | OCW validates route config without activating |
| 8 | Rollback procedure tested | Stop → remove route → restore nginx config |
| 9 | `e-qubs.de` untouched | OCW confirms no changes to e-qubs.de paths |
| 10 | Commit hash recorded | `git rev-parse HEAD` logged in handoff |

Until all 10 items are green, the public endpoint remains disabled.

---

## SECTION 12 — Rollback / Off Switch

If anything goes wrong:

| Step | Action |
|------|--------|
| 1 | `systemctl stop weslr-demo` (or kill the process) |
| 2 | Remove nginx public route config (`nginx -s reload`) |
| 3 | Set `WESLR_MODE` back to `private_dev` or `local_demo` |
| 4 | Confirm rollback: `curl localhost:PORT/show weslr status` returns `200` |
| 5 | Restore previous nginx config from backup |

Rollback must be executable by the operator in under 2 minutes without external help.

---

## SECTION 13 — Website Messaging

### Safe Claims

- **Continuity-first** — state traces back to governed proposals
- **Governed evolution** — changes require operator review and approval
- **Traceable state** — every significant state change is documented
- **Deterministic core paths** — same command returns same structure every time
- **Public demo is read-only** — no writes, no execution, no learning from users

### Forbidden Claims

- ❌ AGI, ASI, or any general intelligence claim
- ❌ Autonomous self-improving
- ❌ Unhackable / fully safe
- ❌ consciousness (unless used in a technically precise, governed sense)
- ❌ Replaces X or does Y better than humans (specific capability claims)
- ❌ Learns from you / adapts to you (violates learning boundary)

All website copy must be reviewed against this list before publishing.

---

## SECTION 14 — Recommended Next Implementation

Based on the implementation order from other design documents:

| # | Step | Component | Rationale |
|---|------|-----------|-----------|
| A | **demo server implementation** | `interpretation.py` as HTTP server on staging port | Core requirement — nothing else works without this |
| B | **nginx staging config** | Public route in nginx, disabled by default | Enables OCW to validate routing without exposure |
| C | **website copy** | weslr.de landing page with safe claims only | Public-facing; must be reviewed against Section 13 |
| D | **rate limiter hardening** | Per-session + per-IP limits in `interpretation.py` | Currently soft; needs stress-tested defaults |

**Recommended order:** A → B → C → D

Each step is a prerequisite for the next. The demo server (A) must work before nginx routing (B) can be tested. nginx routing (B) must be validated before website copy (C) is worth publishing. Rate limiter hardening (D) is the final hardening step.

---

## SECTION 15 — Verdict

**SAFE_PUBLIC_DEMO_ARCHITECTURE_DEFINED**

This document establishes the complete design for the WESLR public read-only demo. It covers runtime mode, request flow, allowed/blocked routes, session model, rate limits, logging, OCW responsibilities, pre-deployment checklist, rollback procedure, website messaging constraints, and the recommended implementation sequence.

All design claims are grounded in existing documents:
- `PUBLIC_READINESS_PLAN_V1.md` — mode definitions
- `PUBLIC_LEARNING_BOUNDARY_V1.md` — learning constraints
- `PUBLIC_USER_SESSION_MODEL_V1.md` — session structure
- `MULTI_AGENT_WORKFLOW_V1.md` — agent responsibilities
- `OCW_HANDOFF_V1.md` — deployment protocol

No deployment has occurred. No production systems are affected.
