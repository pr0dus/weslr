# WESLR Synthetic Teaching Diagnostic Note V1

## Status

- documentation_only
- diagnostic_note
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Purpose

This note clarifies the difference between two offline synthetic teaching diagnostics.

The earlier teaching helper diagnostic used **6 manually constructed proof steps**. It was a representative helper-only smoke diagnostic, not full curriculum coverage.

The full synthetic teaching diagnostic used `load_synthetic_logic_curriculum_v1()` and covered all **14 fixtures/families** in the synthetic logic curriculum. It produced **70 teaching explanations** across 5 teaching modes.

## Full Diagnostic Summary

- loader fixture count: 14
- teaching diagnostic fixture count: 14
- families covered: all 14 synthetic curriculum families
- proof-step count: 14
- teaching explanation count: 70
- teaching modes: beginner, technical, academic, spock, operator_audit
- teaching mode count: 14 per mode

## Safety Boundaries

The diagnostic remains governed and offline only:

- no answer selection
- no truth/soundness claim
- no official score
- no answer-key use
- no benchmark text
- no runtime integration

This diagnostic is synthetic/offline only. It is not public/runtime teaching behavior yet, and it is not benchmark scoring.

## Caveats

- unsupported gap count remains high: 100
- fallacy explanation count is 0
- this is synthetic/offline only
- this is not public/runtime teaching behavior yet
- this is not benchmark scoring

## Current Milestone

`synthetic curriculum → proof step → teaching explanation` exists as a governed offline lane.

## Recommended Next Review

- inspect unsupported-gap taxonomy
- inspect fallacy explanation coverage
- then decide whether to refine teaching helpers or keep the lane internal-only
