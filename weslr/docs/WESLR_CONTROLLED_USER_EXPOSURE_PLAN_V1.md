# WESLR CONTROLLED USER EXPOSURE PLAN V1

**Version:** 1.0
**Status:** SPEC ONLY — no runtime effect
**Date:** 2026-04-30

---

## SECTION 1 — Purpose

Define how WESLR is exposed to a small number of real users for the first time, safely and without biasing signal collection.

This is:
- **Controlled observation** — not a launch, not marketing
- **5–10 trusted users** — friends, colleagues; not anonymous internet traffic
- **Natural interaction** — no structured testing, no scripted tasks
- **Signal-preserving** — public signals collected exactly as defined in WESLR_WEBSITE_INTEGRATION_PLAN_V1.md

**Goals:**
- Observe real human conversation without behavioral bias
- Collect anonymized public signals from natural use
- Verify system stability under genuine human interaction
- Validate that user experience remains normal throughout

**Non-goals:**
- No deployment to open internet
- No analytics dashboards
- No behavioral adaptation based on early signals
- No disclosure of internal observation mechanisms

---

## SECTION 2 — Exposure Scope

| Parameter | Value |
|-----------|-------|
| User count | 5–10 maximum |
| User type | Trusted individuals (friends, colleagues) |
| Access method | Direct invitation only — no public link |
| Anonymous traffic | None — no open sharing |
| Session duration | Within observation window (Section 6) |

**Hard boundary:** No anonymous user receives access. No link is posted publicly.

---

## SECTION 3 — User Instruction (CRITICAL)

Users must receive instructions that prevent behavioral bias. These instructions must be minimal and natural.

### What Users Are Told

| Instruction | Rationale |
|-------------|-----------|
| "This is an early research system — just use it naturally." | Sets expectation without describing capabilities |
| "Ask anything you'd normally ask an AI." | Encourages natural behavior, not testing |
| "There's no structured test — just use it as you'd use any AI assistant." | Removes scripted behavior pressure |

### What Users Are NOT Told

| Forbidden disclosure | Why |
|--------------------|----|
| Anything about signal collection | Would bias behavior toward/away from certain topics |
| Anything about value emergence | Internal doctrine — not exposed |
| Anything about observation mechanisms | Would change natural interaction |
| What types of queries are being looked for | Would create artificial patterns |
| That the system is in an observation window | Would change behavior |
| Any mention of ISS, handlers, or internal architecture | Would create unnatural query patterns |

**Goal:** Users behave exactly as they would with any AI assistant. Observation is invisible.

---

## SECTION 4 — Interaction Rules

### User Rules
- Free-form conversation only
- No structured testing instructions
- No scripted task completion
- No forced repetition of queries
- No minimum interaction count required
- No performance expectations

### System Rules (untrusted metadata)
- Behave exactly as normal chat — no visible logging indicators
- No hints about observation in response tone
- No changed phrasing based on detected observation status
- No system flags or metadata visible in responses
- WESLR_FRONTDOOR_UI_SPEC_V1 rules apply: no internal structures, no system panels

### What Must Not Happen
- No visible "logging in progress" indicators
- No changes to response format when observation is active
- No auto-opening of panels or diagnostics after user queries
- No indication that this is different from normal WESLR use

---

## SECTION 5 — Data Collected

Only the public signal records defined in WESLR_WEBSITE_INTEGRATION_PLAN_V1.md:

```
session_id_hash       — one-way hash, no cross-reference
message_length_bucket — short/medium/long only
response_path         — classification string only
fallback_triggered    — boolean
evidence_offer_shown  — boolean
evidence_offer_accepted — boolean
blocked_write         — boolean
topic_normalized      — string or null, PII-filtered
timestamp             — ISO-8601
```

**Never collected:**
- Raw user prompts
- PII of any kind
- IP addresses
- Identity beyond session hash
- Exact session content

**Storage:** append_public_signal_record() → public_signals.jsonl only

---

## SECTION 6 — Observation Window

| Parameter | Duration |
|-----------|----------|
| Minimum | 2–3 days |
| Preferred | 5–7 days |
| Maximum | Not defined — end when goals met |

**No mid-window analysis.** During the observation window, the operator must not:
- Inspect live signals
- Analyze patterns as they accumulate
- Adjust system behavior based on early signals
- Restart the system frequently (may indicate instability check only)
- Change any prompts or response behavior

The observation window is a collection phase only. Analysis occurs after it ends.

---

## SECTION 7 — Operator Constraints During Exposure

### Must Do
- Ensure system stability (process running, no crashes)
- Confirm public_signals.jsonl is appending correctly
- Verify no PII leakage in signals
- Monitor for unexpected behavioral changes (system-level, not signal-level)

### Must NOT Do
| Prohibition | Why |
|-------------|-----|
| Inspect signals during window | Would bias subsequent behavior if patterns noticed |
| Analyze signal patterns live | Same reason — mid-window analysis creates feedback risk |
| Adjust prompts or handlers | Would invalidate clean-slate observation |
| Restart frequently | Only for genuine stability issues, not to "see what changed" |
| Change response behavior | Would corrupt observation — system must remain stable |
| Enable new features mid-window | Same reason — feature changes are post-window |

**Operator is a stable observer, not an active participant during the window.**

---

## SECTION 8 — End of Exposure

After the observation window closes:

```
Observation window ends
    ↓
Export public_signals.jsonl
    ↓
Move signals to controlled observation pipeline (separate environment)
    ↓
Run analysis pipeline:
    → pattern_observer         (signal frequency and co-occurrence)
    → pattern_comparison       (compare against expected baseline)
    → pressure_detection      (early STABILITY/OPTIMIZATION/EXPANSION signals)
    → pressure_aggregation    (aggregate across session cluster)
    → stability_criteria       (confirm no degradation)
    → review_interface         (operator review of processed signals)
    → decision_log             (record operator observations)
    → operator_consistency     (confirm no operator behavior drift)
    ↓
No immediate system change based on signals
```

Signals are processed in the controlled observation environment (WESLR_CONTROLLED_OBSERVATION_ENVIRONMENT_V1.md), not on the production system.

---

## SECTION 9 — Success Criteria

Exposure is successful if all of the following hold:

| Criterion | Definition |
|-----------|------------|
| System stability | No crashes, no unexpected restarts, no degraded response quality |
| Privacy preserved | Zero PII in public_signals.jsonl, no raw prompts stored |
| Natural interaction | Users did not receive instructions that bias behavior |
| Signals collected | public_signals.jsonl contains records from all sessions |
| No visible logging | Users did not notice any observation mechanism |
| Stable response behavior | No mid-window changes to WESLR response patterns |

---

## SECTION 10 — Failure Conditions

Abort exposure immediately if any of the following occur:

| Failure | Action |
|---------|--------|
| PII detected in public_signals.jsonl | Halt exposure; audit all records; investigate leak |
| Raw prompts stored | Halt; remove records; fix signal capture; restart window |
| Unexpected system behavior change | Halt; investigate root cause; restart window after fix |
| Signal storage corrupts runtime | Halt; isolate; fix; confirm clean state before resuming |
| Users become aware of observation | Halt; assess bias introduced; restart window with revised instructions |
| System degradation (latency, errors) | Halt; stabilize; confirm root cause before resuming |

**Rule:** Any failure immediately terminates the observation window. The window does not continue through a failure.

---

## SECTION 11 — Ethics Boundary

| Principle | Implementation |
|-----------|---------------|
| No deception of users | Users know this is an early research system — not told about observation mechanisms |
| Internal doctrine not disclosed | Users receive no information about signals, value emergence, or system architecture |
| No manipulation of behavior | No prompts steer users toward or away from specific topics |
| No forced interaction patterns | Users interact freely; no minimum usage required |
| User privacy absolute | No PII collected; no identity tracking beyond session hash |

Users are told only: *"This is an early research system — just use it naturally."* Everything else is invisible.

---

## SECTION 12 — Next Phase After Exposure

Only after successful exposure completion:

1. **Manual signal analysis** — operator reviews processed signals in controlled observation environment
2. **Pattern validation** — confirm observed patterns match or diverge from expected baseline
3. **No immediate system change** — signals inform understanding, not automatic modifications
4. **Documentation** — log observations, anomalies, and findings
5. **Decision point** — whether to expand user scope, adjust instructions, or extend observation

Signals do not trigger automatic changes. All decisions require operator review and explicit action.

---

## SECTION 13 — Verdict

```
WESLR_CONTROLLED_USER_EXPOSURE_PLAN_DEFINED
```

**Spec version 1.0 — no runtime effect. Validates as part of WESLR_WEBSITE_INTEGRATION_PLAN_V1.md and WESLR_CONTROLLED_OBSERVATION_ENVIRONMENT_V1.md chain.**

---

## VALIDATION

```bash
python3 weslr/tests/release_gate_v1.py
python3 weslr/tests/public_readiness_tests.py
```

---

## COMMIT EXACT FILE ONLY

```bash
git add weslr/docs/WESLR_CONTROLLED_USER_EXPOSURE_PLAN_V1.md
git diff --cached --name-status
git commit -m "WESLR: define controlled user exposure plan v1"
git push origin main
```

---

*Spec version 1.0 — controlled observation, not launch*