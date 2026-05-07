# Relationship Depth Model — WESLR

## Purpose

Relationship depth is an **evidence-based signal** of shared interaction history between a WESLR entity (person, project, company, institution, team, family) and the WESLR system.

Relationship depth is **NOT**:
- Identity verification
- Memory access permission
- Emotional attachment
- Trust authority
- Neural weight training

Relationship depth **may** influence:
- Tone and warmth
- Greeting style
- Verbosity
- Proactive initiative
- Explanatory depth

Relationship depth must **never** bypass:
- Identity verification requirements
- Memory access control
- Privacy boundaries
- Governance gates

---

## Model

### RelationshipObservation

One record of a single interaction event.

| Field | Type | Purpose |
|---|---|---|
| `observation_id` | str | Unique ID (16 hex chars) |
| `timestamp` | str | ISO 8601 UTC |
| `subject_entity_type` | str | person / company / project / etc. |
| `subject_entity_id` | str | Entity identifier |
| `target_entity_type` | str | system / project / company / etc. |
| `target_entity_id` | str | Target identifier |
| `channel_id` | str | Channel/session ID |
| `interaction_signal` | str | Signal name (see below) |
| `weight` | float | Manual override; defaults to signal weight |
| `confidence` | float | 0.0–1.0 confidence in observation |
| `verified` | bool | Whether this observation is verified |
| `source` | str | "explicit" / "memory" / "correction" / etc. |
| `metadata` | dict | Optional extra context |
| `limitations` | list | Limitations on how to interpret this obs |

### RelationshipState

Computed state for a subject↔target entity pair.

| Field | Type | Purpose |
|---|---|---|
| `relationship_depth` | float | 0.0–1.0, capped by identity status |
| `relationship_stage` | str | unknown / first_contact / early / developing / established / deep |
| `confidence` | float | 0.0–1.0 confidence in the depth score |
| `verified_interaction_count` | int | Number of verified observations |
| `positive_signal_count` | int | Positive signal count |
| `negative_signal_count` | int | Negative signal count |
| `last_interaction_at` | str | ISO timestamp of last observation |
| `first_interaction_at` | str | ISO timestamp of first observation |
| `evidence` | list | Signal names used in computation |
| `limitations` | list | Always includes "relationship_depth is NOT identity verification" etc. |

---

## Interaction Signals

### Positive / Depth-Building

| Signal | Default Weight | Description |
|---|---|---|
| `verified_session_interaction` | +0.02 | Verified session interaction |
| `shared_work_completed` | +0.05 | Shared work successfully completed |
| `user_preference_saved` | +0.03 | User preference successfully saved |
| `successful_followup` | +0.03 | Successful follow-up interaction |
| `correction_resolved` | +0.02 | User correction acknowledged and resolved |
| `correction_acknowledged` | +0.01 | Correction acknowledged |
| `memory_confirmed` | +0.04 | WESLR memory claim confirmed by user |
| `user_positive_feedback` | +0.03 | Explicit positive feedback |
| `repeated_return` | +0.04 | User returned after previous interaction |
| `identity_verified_this_session` | +0.01 | Identity verification occurred this session |

### Neutral

| Signal | Default Weight | Description |
|---|---|---|
| `simple_question` | +0.005 | Simple informational question |
| `one_off_task` | +0.005 | One-off task request |
| `system_status` | +0.002 | System status check |
| `unknown_signal` | 0.0 | Unknown signal type |

### Negative / Restraint-Building

| Signal | Default Weight | Description |
|---|---|---|
| `user_negative_feedback` | -0.03 | Explicit negative feedback |
| `user_correction` | -0.02 | User correction (may also improve if resolved) |
| `user_ignored_proactive` | -0.02 | User ignored WESLR proactive message |
| `user_requested_quiet` | 0.0 | User requested reduced initiative (restraint, not depth loss) |
| `user_rejected_memory_claim` | -0.10 | WESLR made false memory claim |
| `identity_uncertain` | -0.05 | Identity uncertainty detected |
| `privacy_boundary` | -0.01 | Privacy boundary encountered |
| `false_memory_claim` | -0.10 | WESLR made factually false claim |

---

## Relationship Stages

| Stage | Depth Range | Description |
|---|---|---|
| `unknown` | 0.00–0.05 | No evidence or very low confidence |
| `first_contact` | 0.05–0.15 | First interactions, onboarding stage |
| `early` | 0.15–0.30 | Early relationship, warming up |
| `developing` | 0.30–0.55 | Active relationship, some shared context |
| `established` | 0.55–0.80 | Established relationship, efficient communication |
| `deep` | 0.80–1.00 | Deep context, significant shared history |

---

## Identity Caps

Relationship depth is **capped** by identity verification status:

| Identity Status | Max Depth |
|---|---|
| `unknown` | 0.05 |
| `claimed` | 0.10 |
| `onboarded_unverified` | 0.20 |
| `profile_only` | 0.20 |
| `channel_verified` | 1.00 |
| `device_verified` | 1.00 |
| `test_verified` | 1.00 |

---

## Entity Scoping

Relationship states are **scoped by entity pair**. The following are independent:

- `person:alice` ↔ `system:weslr`
- `person:alice` ↔ `project:weslr`
- `person:alice` ↔ `company:acme`
- `person:bob` ↔ `system:weslr`

A verified `CEO` role at `company:acme` does **not** automatically grant personal relationship depth with WESLR.

---

## Tone Mapping

Relationship depth drives expression parameters only (never truth or access):

| Stage | Warmth | Verbosity | Explanatory | Greeting Style |
|---|---|---|---|---|
| unknown | reserved | brief | always | cautious |
| first_contact | warm | medium | always | introductory |
| early | warm | medium | always | friendly |
| developing | warm | medium | always | familiar |
| established | familiar | concise | not required | established |
| deep | familiar | concise | not required | established |

---

## Inactivity Decay

If no interaction is recorded for more than **60 days**, relationship depth decays at a rate of **0.005/day**.

---

## Storage

Observations are stored append-only in:

```
~/.weslr/relationships/relationship_observations.jsonl
```

Each line is one JSON `RelationshipObservation` object.

---

## Limitations

- Relationship depth is computed from stored observations, not from live interaction capture
- No daemon auto-capture; observations must be recorded explicitly via `record_interaction_outcome()` or CLI
- Relationship depth does not model emotional state or trust in the human sense
- Inactivity decay is simple linear decay; no adaptive decay rate
- Relationship depth is scoped per target entity; cross-entity generalization is intentional non-transfer
