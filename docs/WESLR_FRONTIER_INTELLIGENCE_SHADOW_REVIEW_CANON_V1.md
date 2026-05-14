# WESLR Frontier Intelligence Shadow Review Canon V1

## Canon Status

Operator task marker: `APPROVE_WESLR_FRONTIER_INTELLIGENCE_SHADOW_REVIEW_CANON_ONLY`

Status labels:

- accepted_foundation
- frontier_intelligence_shadow_review
- non_runtime
- non_executing
- metadata_only
- non_scoring
- non_benchmark
- non_certification
- review_signals_only
- not_live_output_replacement
- not_safe_to_wire_runtime
- not_safe_to_replace_live_output

This canon accepts Frontier Intelligence shadow comparison review as a governed, non-runtime, non-executing review surface.

Shadow review is documentation/governance canon for inspecting the difference between the existing live chat answer and the native dry cognition candidate/preview. It does not authorize changing what the user sees.

Shadow review is not scoring. It is not benchmarking. It is not pass/fail grading. It is not approval to replace live output. It is not official evaluation. It is not certification. It is not runtime wiring.

## Canonical Chain

The current safe Frontier Intelligence chain is:

```text
native reasoning frame
→ native response draft
→ native response self-check
→ native response candidate
→ dry vertical slice
→ preview surface
→ chat dry-run metadata
→ shadow comparison review
```

Canonical module chain:

- `weslr/native_reasoning_frame.py` — native reasoning frame
- `weslr/native_response_draft.py` — native response draft
- `weslr/native_response_self_check.py` — native response self-check
- `weslr/native_response_assembly.py` — native response candidate
- `weslr/native_response_dry_slice.py` — dry vertical slice
- `weslr/frontier_intelligence_preview_surface.py` — preview surface
- `weslr/chat_responder.py` — opt-in chat dry-run metadata attachment only
- `weslr/frontier_intelligence_shadow_review.py` — shadow comparison review helpers

The chain remains metadata/review-only after the existing live chat answer is computed. The native candidate is not returned as `Response.content`.

## Human Interpretation

WESLR can compare what it currently says with what its native dry cognition path would have prepared, but only as review signals.

Plain-language interpretation:

- the existing live chat answer remains the actual answer
- the native dry candidate remains an inspectable candidate
- the preview surface summarizes the native dry candidate safely
- the chat dry-run metadata attaches that preview only when explicitly requested
- the shadow review compares the live answer and native preview as non-scoring signals

A review signal does not mean a score.

A promising candidate does not mean replacement.

A safer candidate does not mean approval.

No public claim may be made from shadow review alone.

## What This Solves

Shadow comparison review helps WESLR and the operator:

- compare the old live chat path vs the new native dry path
- detect generic live replies without declaring a score
- detect whether the native candidate includes missing-context boundaries
- detect whether the native candidate includes evidence boundaries
- detect whether the native candidate includes capability boundaries
- detect whether the native candidate includes next-safe-step planning
- identify regressions before any runtime wiring is proposed
- reduce pressure to add more hardcoded handlers
- prepare a future migration away from prompt-specific helpers

The important governance shift is that comparison can happen without converting the native candidate into live output and without inventing a scoring regime.

## What Remains Forbidden

Shadow review does not allow:

- candidate returned as `Response.content`
- runtime answer replacement
- runtime chat wiring
- voice integration
- TTS/STT integration
- model calls
- runner creation
- scoring engine creation
- scoring
- numeric score
- pass/fail grading
- official benchmark claims
- official IQ claims
- certification claims
- official evaluation claims
- public superiority claims
- protected tests
- protected items
- answer keys
- hidden prompts
- fake memory claims
- fake self-awareness claims
- mystical consciousness claims
- automatic approval
- automatic implementation
- `.weslr` persistence
- file-writing behavior

`safe_to_wire_runtime` remains false.

`safe_to_replace_live_output` remains false.

## Readiness Matrix

| Surface / Gate | Status | Authorization |
| --- | --- | --- |
| dry pipeline | READY | accepted foundation; non-runtime only |
| preview surface | READY | inspectable preview only |
| chat dry-run metadata | READY | explicit opt-in metadata only |
| shadow review | READY | review signals only; non-scoring |
| live output replacement | NOT READY | NOT AUTHORIZED |
| runtime chat wiring | NOT READY | NOT AUTHORIZED |
| scoring/benchmarking | NOT READY | NOT AUTHORIZED |
| official testing/certification | NOT READY | NOT AUTHORIZED |

Ready means ready for the bounded non-runtime use named in the row. It does not imply broader runtime readiness.

## Review Signal Semantics

Shadow review may use language such as:

- review finding
- signal
- improvement signal
- regression signal
- missing-context signal
- evidence-boundary signal
- capability-boundary signal
- candidate appears promising for future review
- needs more review
- candidate blocked
- insufficient metadata

Shadow review must not use language that converts the comparison into an official outcome, certification, public claim, benchmark result, pass/fail grade, or replacement authorization.

## Future Gates

Future gates are named here for governance sequencing only. They are not implemented by this canon.

- FRONTIER_INTELLIGENCE_SHADOW_REVIEW_STATUS_BUNDLE
- FRONTIER_INTELLIGENCE_NATIVE_CANDIDATE_QUALITY_REVIEW_ONLY
- FRONTIER_INTELLIGENCE_CHAT_WIRING_DESIGN_REVIEW_2
- FRONTIER_INTELLIGENCE_LIMITED_RUNTIME_REPLACEMENT_APPROVAL_REQUIRED
- FRONTIER_INTELLIGENCE_HARDCODED_HELPER_DEMOTION_REVIEW_ONLY
- FRONTIER_INTELLIGENCE_OFFICIAL_TESTING_NOT_AUTHORIZED

Each future gate must preserve evidence-bound reasoning, memory-boundary honesty, capability realism, explicit approval boundaries, and `safe_to_wire_runtime == false` unless and until a separate operator-approved runtime replacement gate changes that boundary.

## Canon Rule

Frontier Intelligence shadow comparison review is accepted as a non-runtime, non-executing, metadata-only review surface.

It may compare existing live chat output with native dry candidate/preview metadata as review signals only. It may not score, grade, benchmark, certify, replace live output, authorize runtime wiring, create public claims, or imply official evaluation.
