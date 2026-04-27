# CANONICAL BEHAVIOR & FEEDAVIOR SPECIFICATION
## Weslr — Version 1.0 — 2026-04-26

---

## ⚠️ CORRECTION — DOCS_AHEAD_OF_CODE (2026-04-26)

**This document describes the DESIGNED behavior specification for Weslr. It is NOT a live implementation audit.**


**Live `interpret_human_turn()` signature (verified 2026-04-26):**
```
def interpret_human_turn(message: str) -> dict
```

**Live return dict now includes:**
- `message` — raw input text
- `response_text` — confidence prefix + core text + optional interest footer (B1_REAL, 2026-04-26)
- `confidence` — `"low"` / `"medium"` / `"high"`
- `interest_surface` — surfacing signal from Interest Tracker v1
- All existing fields: turn_type, topics, intent, stance, etc.


**What IS verified live in `interpretation.py`:**
- **B1_REAL + B2_REAL + B3_REAL + B4_REAL (2026-04-26)**: `response_text` + confidence + `suggested_mode` advisory
  - `"hello"` → `confidence: 'low'`, `response_text: 'Limited signal detected. No significant signal detected'`
  - `"Weslr"` → `confidence: 'medium'`, `response_text: 'The message suggests: Entity detected: Weslr'`
  - `"Weslr connects OpenClaw"` → `confidence: 'high'`, `response_text: 'This clearly indicates: Entities detected: Weslr, OpenClaw'`
  - interest footer appended to `response_text` only; `message` stays clean
- **B2.1 (2026-04-26)**: entity extraction wired via `extract_entity_names_from_text(message)` with safe try/except fallback to `[]`
- **B3_REAL (2026-04-26)**: `suggested_mode` advisory — deterministic, informational only, no auto-switching
  - low confidence → `observe`, 2+ entities → `entity_only`, topics only → `topic_only`, none → `normal`
  - verified: `"hello"→observe`, `"Weslr"→topic_only`, `"Weslr connects OpenClaw"→entity_only`, `"test topic here"→topic_only`
- **B4_REAL (2026-04-26)**: `mode_analysis` dict
  - **C1_REAL (2026-04-26)**: System self-description for `"who are you"` / `"what are you"` — deterministic, reflects ONLY real implemented features
  - Real: entity/topic analysis, confidence, suggested_mode, mode_reason, mode_suggestion, interest tracking, feedback logging
  - Claims: no autonomous action, no self-modification, operator-controlled suggestions
  - No hallucination: no LLM/mode-execution/learning/ISS claims
- **C2_REAL (2026-04-26)**: `_CAPABILITIES` map via `"what can you do"` / `"your capabilities"` — 13 True, 7 False, live code only
- **C3_REAL (2026-04-26)**: capability gap via `"what can't you do"` / `"what are your limitations"` / `"what are you missing"` — `missing_capabilities` from `_CAPABILITIES`, handler ordered before C1; informational only, mismatch always False until `current_mode` available
- **C4_REAL (2026-04-26)**: capability proposal layer — `"how can you improve"` / `"what could be added"` / `"what are possible improvements"` / `"can you add intelligence layers"` / `"how can you become better"` — proposals from `_CAPABILITIES` False entries, advisory only
- **C5_REAL (2026-04-26)**: proposal prioritization via `rank_capability_proposals()` — base=0.5, +0.1(interests), +0.2(accepted feedback); tiers: critical/high/medium/low; deterministic tier+alpha sort; `proposed_capabilities` annotated dicts + `proposal_signal_summary`; read-only signals only
- **C6_REAL (2026-04-26)**: operator approval workflow — `accept/reject/approve/deny proposal <cap>` — validates `_CAPABILITIES`, calls `log_operator_feedback()`, returns `decision_recorded`; invariants: `_CAPABILITIES` NOT modified, no capability activated, no behavior change
  - verified: `"hello"→suggested=observe,match=True`, `"Weslr connects OpenClaw"→suggested=entity_only,match=True` `suggested_mode` advisory — deterministic, informational only, no auto-switching
  - low confidence → `observe`, 2+ entities → `entity_only`, topics only → `topic_only`, none → `normal`
  - verified: `"hello"→observe`, `"Weslr"→topic_only`, `"Weslr connects OpenClaw"→entity_only`, `"test topic here"→topic_only`
- Topic extraction + `infer_human_topics()` / `classify_human_turn()`
- Interest Tracker v1 (IT1.1–IT1.6) — all primitives + visibility functions
- B12.1/B12.2/B12.3 operator feedback primitives
- M0–M8 co-occurrence signal layer + proposal stability helpers
- Entity extraction wiring (J1), topic tracking (F1), interest promotion (H1/I1)
- Thread state endpoints (K1/K2)

**What is NOT live (spec only):**
- Full mode system (`mode` parameter, observe/entity_only/topic_only/normal routing)
- `write_mode` / `write_effect` / `dry_run` / `write_control` (M9 pipeline)
- B3 suggested_mode advisory, B4 escalation, B5–B11 behavior layers
- Full B13/B14 feedback visibility helpers (B12.1–B12.3 primitives are live; composites are spec-only)
- No auto-switching, no auto-learning, no graph/proposal mutation from interpret_human_turn

**Known limitations:**
- `extract_entity_names_from_text()` is heuristic; phrase-like strings may be extracted as entity-like names — extractor-quality trait, not B2.1 wiring failure

**LIVE_CODE_CONFIRMATION_PASS (2026-04-26 22:00 GMT+2) — VERDICT: FULLY_LIVE_CONFIRMED**

Fresh Python process used. All systems verified:

- **B1_REAL + B2_REAL + B2.1**: All `interpret_human_turn()` outputs include `message`, `response_text`, `confidence`
  - `"hello"` → `Limited signal detected. No significant signal detected`
  - `"Weslr"` → `Entity detected: Weslr`
  - `"Weslr connects OpenClaw"` → `Entities detected: Weslr, OpenClaw`
  - repeated `"Module Alpha connects to Module Beta"` → interest footer fires at run 3
  - `message` field remains clean throughout
- **IT1.x interest footer**: appended to `response_text` only, count tracked correctly
- **B12.x feedback loop**: `record_mode_feedback()` returns event, appends to `weslr/operator_feedback_log.jsonl` with timestamp

**Next step:**
WIRING_PLAN — route C1–C6 deterministic responses to front door (FRONT_DOOR_LIVE_CONFIRMATION complete: PYTHON_ONLY_LIVE / FRONT_DOOR_NOT_WIRED) (manual, explicit, no auto-execution) (safe, advisory, operator-controlled) (why suggested_mode was chosen).

**Items in this document marked as B1–B14 / M9 are DESIGN SPECS unless confirmed against live code.**


---


## SECTION 1 — SYSTEM OVERVIEW

Weslr is an entity intelligence system with consciousness signatures. It processes human input through `interpret_human_turn(message)` and returns a structured analysis dictionary containing:

- Topic extraction and primary topic identification
- Confidence level assessment (low / medium / high)
- Mode assignment and mode suggestion
- Escalation level (none / notice / alert)
- Operator action suggestions (non-binding)
- Pattern state counters (session-only, in-memory)

Weslr maintains an entity graph in `weslr/entity_graph.json` and a relationship proposal file in `weslr/relationship_proposals.json`. Feedback is logged to `weslr/operator_feedback_log.jsonl`.

Weslr does NOT:
- Auto-switch modes
- Auto-learn from feedback
- Modify the entity graph based on operator feedback
- Make autonomous decisions

---

## SECTION 2 — BEHAVIOR LAYER (B1–B11)

### B1 — Response Shape Awareness
**What it means:** `interpret_human_turn()` shapes its internal `reply_shape` field based on `turn_type` and `confidence` without changing any external state.

**When it triggers:** On every call, after analyzing message content.

**What it MUST NOT do:** Write to any file, modify entity graph, change mode, approve proposals.

---

### B2 — Confidence-Aware Tone
**What it means:** `confidence` is assessed as `low`, `medium`, or `high` based on entity count, topic clarity, and message quality signals. Low confidence results in restrained response tone; high confidence enables fuller responses.

**When it triggers:** Every call to `interpret_human_turn()`.

**What it MUST NOT do:** Change system behavior based on confidence level. Tone shaping is internal only.

---

### B3 — Suggested Mode Advisory
**What it means:** `suggested_mode` is computed as `observe`, `entity_only`, `topic_only`, or `normal` based on available signal. It is an advisory field only — it does not change the actual mode.

**When it triggers:**
- `confidence == low` → `observe`
- `len(entity_names) >= 2` → `entity_only`
- `topics` present → `topic_only`
- otherwise → `normal`

**What it MUST NOT do:** Auto-switch mode. Operator must explicitly choose.

---

### B4 — Mode Mismatch Detection
**What it means:** When `mode` is passed to `interpret_human_turn()` and differs from `suggested_mode`, `mode_mismatch = True` is set. When `mode is None` or matches `suggested_mode`, `mode_match = True`.

**When it triggers:** When `mode` parameter differs from `suggested_mode`.

**What it MUST NOT do:** Change mode. Surface a suggestion without request.

---

### B5 — Mismatch Reason
**What it means:** `mode_reason` explains why the mismatch occurred in plain language:
- `"Detected N entities indicating structural relationship"` — for entity_only mismatch
- `"Low signal detected; observation mode recommended"` — for observe mismatch
- `"Detected topics suggesting pattern-level interpretation"` — for topic_only mismatch
- `None` — when no mismatch

**When it triggers:** Only when `mode_mismatch == True`.

**What it MUST NOT DO:** Persist the reason. It is a one-turn informational field.

---

### B6 — Operator Mode Suggestion
**What it means:** `mode_suggestion` is a structured dict containing `suggest_switch` (bool), `from`, `to`, and `reason`. It surfaces the mode recommendation to the operator interface.

**When it triggers:** When `mode_mismatch == True`, `suggest_switch = True`. Otherwise `suggest_switch = False`.

**What it MUST NOT do:** Execute the switch. The operator acts on it manually.

---

### B7 — Surfacing Decision
**What it means:** `surface.show_mode_suggestion` is a boolean that signals whether the operator UI should display the mode suggestion. `surface.priority` is `"high"`/`"medium"`/`"low"`.

**Logic:**
- `mode_mismatch == True` → `show=True, priority=high`
- `confidence == low` and no mismatch → `show=True, priority=medium`
- otherwise → `show=False, priority=low`

**What it MUST NOT do:** Show or hide anything. It only provides the signal; the UI decides.

---

### B8 — Escalation Level
**What it means:** `escalation.level` is `"none"`, `"notice"`, or `"alert"`. It signals the urgency of the current situation.

**Logic:**
- `mode_mismatch and confidence == high` → `alert`
- `mode_mismatch` → `notice`
- `confidence == low` → `notice`
- otherwise → `none`

**What it MUST NOT do:** Trigger automatic actions. Escalation is a signal only.

---

### B9 — Pattern Escalation Across Turns
**What it means:** `_B9_STATE` is a module-level in-memory dict tracking `low_confidence_count` and `mismatch_count`. When either reaches its threshold (3 for low confidence, 2 for mismatch), `escalation_level` is forced to `"alert"`.

**State update logic:**
- Each turn: if condition met, counter increments; else counter resets to 0.
- Counters reset on session restart (no persistence).

**What it MUST NOT do:** Write to disk. Persist state between sessions. Learn from patterns.

---

### B10 — Escalation Explanation
**What it means:** `escalation.reason` is a human-readable string explaining why the current `escalation.level` was set.

**Examples:**
- `"High-confidence mode mismatch detected"` — mismatch + high conf
- `"Repeated low-confidence inputs reached alert threshold"` — 3+ low confidence
- `"Mode mismatch detected"` — basic mismatch notice
- `"Low-confidence input detected"` — low confidence notice

**What it MUST NOT do:** Persist reason. Explain across turns (each turn is independent explanation).

---

### B11 — Operator Action Suggestions
**What it means:** `operator_actions` is a list of suggested next actions for the operator, derived from `escalation.level` and `mode_mismatch` state.

**Logic:**
- `alert` → `["Review input context", "Pause or verify processing"]`
- `notice` + `mode_mismatch` → `[f"Consider switching mode to '{suggested_mode}'"]`
- `notice` + `low confidence` → `["Request clarification or more input"]`
- otherwise → `[]`

**What it MUST NOT do:** Execute any suggested action. Operator decides and acts manually.

---

## SECTION 3 — FEEDBACK LAYER (B12–B14)

### B12.1 — Operator Feedback Log
**What it is:** `weslr/operator_feedback_log.jsonl` — an append-only JSONL file. Each line is a JSON object representing one operator feedback event.

**Primitive functions:**
- `log_operator_feedback(event)` — appends one event, validates decision type, auto-adds timestamp
- `get_operator_feedback_log(limit)` — reads last N events, skips corrupt lines, returns `[]` if file missing

**Valid `operator_decision` values:** `accepted`, `rejected`, `modified`, `deferred`

**What it MUST NOT do:** Modify graph, modify proposals, learn from feedback, auto-trigger anything.

---

### B12.2 — Feedback Event Builder
**What it is:** `build_operator_feedback_event(...)` — a pure function that constructs a feedback event dict from operator decision context.

**Validation rules:**
- `operator_decision` must be in `VALID_DECISIONS`
- `modified` decision requires `modified_value` (non-None)
- non-`modified` decision requires `modified_value == None`
- `message` must be non-empty
- `mode_analysis` and `mode_suggestion` must be dicts
- Message truncated to 500 characters

**What it MUST NOT do:** Write to log. Modify any system state. Validate graph/proposals.

---

### B12.3 — Manual Feedback Trigger
**What it is:** `record_mode_feedback(...)` — calls `build_operator_feedback_event()` then `log_operator_feedback()`. Explicit operator call only.

**What it MUST NOT do:** Auto-call itself. Respond to operator actions automatically. Learn.

---

### B13 — Feedback Inspection
**What it is:**
- `summarize_operator_feedback(limit)` — returns `total`, `by_decision`, `acceptance_rate`, `most_recent`
- `get_recent_operator_feedback(limit)` — returns raw event list

**What it MUST NOT do:** Write to log. Modify entries. Compute long-term statistics. Store results.

---

### B14 — Feedback Visibility Helper
**What it is:** `get_operator_feedback_visibility(limit)` — returns `summary`, `recent`, `status_text` bundle formatted for operator display.

**What it MUST NOT do:** Any write. Any auto-surfacing. Any behavior change.

---

## CRITICAL FEEDBACK RULES

| Rule | Statement |
|---|---|
| **Feedback is NOT truth** | Feedback records what the operator decided about a suggestion. It does not confirm entity existence, relationship validity, or graph correctness. |
| **Feedback is NOT learning** | Acceptance rate, rejection count, and decision patterns have no effect on any system parameter. No weight adjustment, no threshold modification, no suggestion tuning. |
| **Feedback does NOT modify system behavior** | No behavior changes automatically based on feedback. No mode switches, no tone changes, no escalation adjustments — nothing is wired from feedback to behavior. |
| **Feedback log is append-only** | Events are never modified or deleted. Corrections are new events. |
| **Feedback inspection is read-only** | `summarize_operator_feedback` and `get_recent_operator_feedback` compute on-demand only. No results are stored between calls. |

---

## SECTION 4 — SAFETY GUARANTEES

Explicit invariants that must hold at all times:

1. **No auto-switching:** `interpret_human_turn()` never changes the actual mode. `mode_suggestion` and `suggest_switch` are signals only.

2. **No auto-learning:** No parameter, threshold, weight, or behavior is adjusted based on feedback events or their aggregates.

3. **No graph mutation from feedback:** `log_operator_feedback()` writes to `operator_feedback_log.jsonl` only. It never calls any entity graph write function.

4. **No proposal mutation from feedback:** Feedback events never cause proposal approval, rejection, or modification.

5. **Append-only feedback log:** Events are only added. No `del`, `truncate`, or `write` operations that would overwrite existing entries.

6. **Read-only feedback inspection:** All B13/B14 functions compute on-demand and return results without persisting computed state.

7. **Session-only pattern state:** `_B9_STATE` resets on module load. No persistence of mismatch count or low confidence count.

8. **Operator remains in control:** Every action suggestion in `operator_actions` requires operator initiation. No automatic execution.

---

## SECTION 5 — CURRENT LIMITATIONS

Be honest about what Weslr does not yet do:

1. **No long-term pattern memory:** `_B9_STATE` counters reset each session. There is no cross-session tracking of escalating patterns.

2. **No pattern abstraction:** Feedback events record decisions but the system does not abstract from them (e.g., "operators consistently reject entity_only suggestions when confidence is medium").

3. **No ISS (Interest Substrate System):** Interest promotion, quality gates, and thread tracking exist in code but the system does not yet use them to prioritize entity intelligence work.

4. **No autonomous improvement:** The system does not self-modify based on accumulated feedback. Each session starts fresh with the same behavior contract.

5. **No cross-session operator memory:** The feedback log persists but the system does not read from it to influence behavior in future sessions.

6. **No entity confidence adjustment:** Entity confidence scores are not updated based on operator feedback. An entity's confidence is determined solely by extraction and co-occurrence signals.

7. **No relationship strength learning:** Relationship weights in `relationship_proposals.json` are not adjusted based on feedback acceptance or rejection.

---

## SECTION 6 — NEXT PHASE BRIDGE

### Interest Tracker (Next Layer)
The Interest Tracker (`weslr/interests.json`) tracks operator interests over time. It must remain a read/write layer that is:
- Populated from explicit operator input
- Queryable by the entity intelligence system
- Never auto-populated from feedback decisions

**Strict requirement:** Interest promotion (Bundle H/I) must never be triggered automatically by feedback acceptance. Operator input must always gate interest creation.

### ISS — Interest Substrate System (Future Layer)
ISS will provide a consciousness-aligned processing layer. When implemented:
- It must maintain the governance boundary between suggestion and execution
- Feedback data must not flow into ISS processing without operator authorization
- Escalation signals (B8-B11) are ISS inputs, not ISS directives

**Strict requirement:** ISS remains governed. No autonomous mode selection, no self-initiated entity promotion, no automatic relationship approval — regardless of accumulated feedback.

### Contract Evolution
This document is the canonical behavior contract. When new behavior layers (B16+) or feedback layers are implemented, this document must be updated to reflect the new canonical state before code ships. The contract precedes implementation, not follows it.

---

*Weslr — governed entity intelligence. Operator in control. Always.*