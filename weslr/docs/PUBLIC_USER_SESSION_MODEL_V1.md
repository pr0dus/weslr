# WESLR Public User Session Model V1

**Status:** DESIGN ONLY — not implemented
**Created:** 2026-04-28

---

## 1. Purpose

WESLR public demo needs operational user/session tracking for:
- **Safety:** detect and block abusive patterns before they affect system stability
- **Rate limiting:** prevent any single session from consuming disproportionate resources
- **Continuity tests:** validate that public-facing routes behave consistently across sessions
- **Abuse prevention:** identify and disable sessions exhibiting anomalous behavior
- **Operational visibility:** confirm public demo is functioning without exposing private data

This model is scoped to anonymous operational signals only. It does not create user accounts, collect personal data, or enable surveillance.

---

## 2. User Model

### Roles

| Role | Description |
|------|-------------|
| `anonymous_session` | Unidentified visitor with ephemeral session cookie |
| `invited_beta_user` | Early adopter with invite code, limited feature access |
| `operator` | Full access; identity verified |
| `admin` | System-level control; internal only |

### Session vs. Identity

- **Session** = operational token tied to browser/client, not to a person
- **Identity** = stored separately, never mixed into operational logs

---

## 3. Public Demo Session

### Allowed Fields

```json
{
  "session_id": "uuid-v4",
  "created_at": "ISO-8601",
  "last_seen": "ISO-8601",
  "request_count": 0,
  "route_counts": { "route_name": N },
  "failed_route_count": 0,
  "latency_stats": { "p50_ms": 0, "p95_ms": 0, "p99_ms": 0 },
  "rate_limit_hits": 0,
  "abuse_flags": []
}
```

### Forbidden Fields

- ❌ `raw_prompts` — user input is never stored
- ❌ `passwords` — authentication data must never appear
- ❌ `personal_profile_data` — name, email, phone, address, etc.
- ❌ `private_user_memory` — user-provided facts, preferences, or learnable details
- ❌ `hidden_learning` — any derived model updates from user content

### Rationale

Only counters, timestamps, and aggregate statistics are stored. These are operationally useful for safety and rate limiting without exposing what users actually submitted.

---

## 4. Login Options

### Option A: Anonymous Session Cookie

- Session ID generated on first visit, stored as HTTP-only cookie
- No information collected beyond operational signals
- **Pros:** zero friction, privacy-preserving
- **Cons:** no continuity across devices/cleared cookies

### Option B: Invite Code

- Operator generates codes; beta users redeem one
- Enables light continuity without full accounts
- **Pros:** separates trusted early adopters from anonymous traffic
- **Cons:** requires code distribution overhead

### Option C: Email Login (Later)

- Proper user accounts with email/password
- Enables full feature access, history, preferences
- **Pros:** real accounts, continuity, feature depth
- **Cons:** significant implementation cost, privacy surface, moderation burden

### Recommendation

| Phase | Approach |
|-------|----------|
| Phase 1 | Anonymous session cookie (immediate, minimal) |
| Phase 2 | Invite code beta (trusted early adopters) |
| Phase 3 | Full email user accounts (post-beta, if demand exists) |

**Recommended for immediate deployment:** Phase 1 — anonymous session cookie.

---

## 5. Learning Boundary

Public users generate **anonymous operational signals only**.

Rules:
- **No direct memory writes** — user prompts are not stored or learned from
- **No automatic proposals** — public sessions cannot trigger ISS proposals
- **No behavior changes** — WESLR does not adapt to individual public users
- **Route consistency only** — same command always returns same structure

This mirrors the existing `public_learning_boundary` principle: public users are transient operational load, not learning subjects.

---

## 6. Security Rules

| Rule | Rationale |
|------|----------|
| Session IDs are cryptographically random UUIDv4 | Unpredictable; no enumeration |
| No raw input storage | User content never hits disk in identifiable form |
| Rate limits per session | Prevent resource exhaustion by any single session |
| IP retained only transiently in memory | Logged for abuse detection, dropped after session |
| Operator can disable sessions | Manual kill switch for abusive or anomalous sessions |
| All session data is append-only | No modification of historical operational records |

---

## 7. Data Storage

### Recommended: Append-Only Operational Log

```
weslr/public_sessions.jsonl
```

Each line = one session record as JSON. New sessions append; no updates to existing records.

### Status: Implementation Future

This document is design only. The file path and schema are defined here for future reference but not implemented in this version.

---

## 8. Public Mode Integration

The public user session model composes with existing WESLR public safety infrastructure:

| Component | Integration |
|-----------|-------------|
| `public_demo_readonly` | Sessions verified as anonymous; no identity linkage |
| `rate_limiter` | Per-session counters enable granular rate limits |
| `public_readiness_tests` | Session-level assertions validate consistency across runs |
| `public_learning_boundary` | Sessions confirmed as transient; no learnable artifacts |

All components operate independently; session tracking enhances safety without coupling to routing logic.

---

## 9. Implementation Order

| Step | Component | Priority |
|------|-----------|----------|
| A | This design doc | ✅ (complete) |
| B | Session middleware — anonymous cookie + session_id generation | Future |
| C | Rate limiter per session — request_count, route_counts, rate_limit_hits | Future |
| D | Operational dashboard — session stats for operator review | Future |
| E | Invite login — Phase 2 beta access with invite codes | Future |

No implementation in this document. Steps B–E are sequential: each depends on the previous.

---

## 10. Verdict

**PUBLIC_USER_SESSION_MODEL_DEFINED**

This document establishes the conceptual foundation for public user session tracking in WESLR. It defines what is allowed, what is forbidden, how sessions are structured, and the phased rollout strategy — without implementing any authentication, storage, or middleware code.

All future implementation must comply with the field constraints and learning boundaries defined here.
