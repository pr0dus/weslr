# WESLR Synthetic Teaching Lane Canon V1

## Status

- canon_note
- synthetic_internal_lane
- execution_allowed = false
- official_score_claimed = false
- no_runtime_behavior_change

## Milestone

WESLR now has a governed internal synthetic teaching lane:

synthetic curriculum → proof step → teaching explanation

This lane records how synthetic curriculum fixtures can be transformed into governed proof-step artifacts and then into bounded teaching-style explanations.

## Metrics

- fixtures: 14
- proof steps: 14
- teaching explanations: 70
- modes: beginner, technical, academic, spock, operator_audit
- all 70 generated: yes
- forbidden phrase count: 0

## Safety

- no answer selection
- no truth/soundness claim
- no official score
- no answer-key use
- no item-ID authority
- no benchmark-specific tuning
- no runtime integration
- no benchmark text

## Current Scope

- synthetic/offline only
- internal lane only
- not public/runtime ready
- not benchmark scoring
- not a final proof engine

## Why This Matters

WESLR can now produce controlled teaching-style explanations from governed proof artifacts without relying on an LLM as runtime authority.

The teaching lane varies tone/register across modes while preserving the same evidence contract and safety boundary. It does not select answers, does not claim final truth, and does not claim an official score.

## Caveats

- synthetic only
- unsupported gaps still exist
- runtime integration requires separate audit
- public teaching behavior requires separate safety gates
- future work needed for real user-facing logic tutoring

## Recommended Next Phases

- APPROVE_SYNTHETIC_TEACHING_LANE_READINESS_REVIEW_ONLY
- APPROVE_LLM_ADVISOR_MODE_DESIGN_ONLY
- APPROVE_UNSUPPORTED_GAP_FOLLOWUP_DESIGN_ONLY
- KEEP_SYNTHETIC_TEACHING_INTERNAL_ONLY
