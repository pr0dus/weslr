# WESLR WEBSITE INTEGRATION PLAN V1

**Version:** 1.0
**Status:** SPEC ONLY — does not affect runtime
**Date:** 2026-04-30

---

## SECTION 1 — Purpose

Define how real user interactions flow through WESLR safely.

The website integration captures anonymized, non-PII interaction signals from real user sessions without storing raw prompts, modifying responses, or creating behavioral feedback loops. The goal is observation without interference — the user experience remains entirely normal while safe signals are collected for later operator review.

---

## SECTION 2 — Chat Flow

User → /chat → WESLR response.

No response behavior changes.
No prompt mutation.
No hidden personalization.

The /chat handler operates normally. Signal capture occurs after response generation, using only response metadata — never the message content itself. The user experiences standard WESLR behavior regardless of signal capture outcome.

---

## SECTION 3 — Signal Capture Point

After response is generated, construct safe event only from response metadata:

```json
{
  "session_id_hash": "string",
  "message_length_bucket": "short | medium | long",
  "response_path": "string",
  "fallback_triggered": "boolean",
  "evidence_offer_shown": "boolean",
  "evidence_offer_accepted": "boolean",
  "blocked_write": "boolean",
  "topic_normalized": "string | null",
  "timestamp": "ISO-8601"
}
```

No raw message text.
No user identity.
No PII fields.

---

## SECTION 4 — Signal Processing Flow

```
event
  → classify_public_signal()     [weslr/user_signal_intake.py]
  → build_public_signal_record() [weslr/user_signal_intake.py]
  → validate_public_signal_record() [weslr/public_signal_store.py]
  → append_public_signal_record() [weslr/public_signal_store.py]
```

Each stage is deterministic. Classification and building are pure functions with no side effects. Validation rejects unsafe records before append. Append is write-once to public_signals.jsonl only.

---

## SECTION 5 — Failure Handling

If unsafe, invalid, or storage fails:
- silently drop record
- do not affect user response
- do not retry aggressively
- optionally log internal non-PII error count only

Failure of signal capture must have zero user-visible impact. The response has already been delivered. No retry queue, no background retry, no blocking behavior on subsequent requests.

---

## SECTION 6 — Privacy Boundary

Guarantees:
- no raw prompts stored
- no PII stored
- no user identity stored
- no IP stored
- no exact location
- no cross-session linking beyond session_id_hash

session_id_hash is a one-way hash of the session identifier. It does not allow cross-referencing with production records or other signals. It permits aggregate pattern analysis within a session cluster only.

---

## SECTION 7 — System Isolation

Public signals:
- stored only in public_signals.jsonl
- not production truth
- not proposal trace
- not implementation plans
- not ISS diagnostics
- not runtime memory

public_signals.jsonl is append-only. It is not read by any runtime component. It does not feed into WESLR's response generation, proposal system, or observation pipeline in real time.

---

## SECTION 8 — Public Behavior Guarantee

User experience remains normal:
- no visible logging
- no changed tone
- no behavior adaptation
- no prompt adaptation
- no internal doctrine exposure

Signal capture is entirely opaque to the user. Nothing surfaces in the chat interface. No indication that observation is occurring.

---

## SECTION 9 — Operator Access Future

Signals may later be inspected manually or copied into controlled observation pipeline after operator review.
They must not be used automatically or in real time.

Real-time signal use is forbidden. Only operator-reviewed, post-hoc inspection is permitted. The observation pipeline (WESLR_OBSERVATION_EXECUTION_PLAN_V1) processes signals only in batch, after collection.

---

## SECTION 10 — Constraints

- append-only storage
- no feedback loop
- no value inference
- no behavior change
- no hidden learning
- no public disclosure of internal value doctrine

---

## SECTION 11 — Minimal Future Implementation Plan

Future implementation must be tiny:

1. build safe event after /chat response
2. call user_signal_intake
3. call public_signal_store
4. ignore failures
5. return original response unchanged

Implementation must not touch /chat handler logic. Signal capture should be a wrapper that observes the response metadata without modifying it. Error handling is fire-and-forget.

---

## SECTION 12 — Tests Needed Later

- /chat response unchanged when storage succeeds
- /chat response unchanged when storage fails
- raw message never stored
- PII rejected
- blocked_write signal stored safely
- public_signals.jsonl append-only

Tests validate that signal capture has zero behavioral side effects. Tests use mocked storage and verify both success and failure paths produce identical user responses.

---

## SECTION 13 — Verdict

```
WESLR_WEBSITE_INTEGRATION_PLAN_DEFINED
```

---

## VALIDATION

```
python3 weslr/tests/release_gate_v1.py
python3 weslr/tests/public_readiness_tests.py
```

---

## COMMIT EXACT FILE ONLY

```
git add weslr/docs/WESLR_WEBSITE_INTEGRATION_PLAN_V1.md
git diff --cached --name-status
git commit -m "WESLR: define website signal integration plan v1"
git push origin main
```

---

*Spec version 1.0 — does not affect runtime behavior*