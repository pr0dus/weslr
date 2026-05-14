# WESLR Phase Test Scope Policy V1

## Purpose

This note defines how WESLR phase-specific changed-file assertions should be scoped so they do not permanently block future approved work.

## Policy

- Phase-specific changed-file assertions are valid only during that phase's final validation.
- They should not be used as permanent regression tests that fail future approved files.
- Future durable tests should validate behavior, schemas, safety flags, boundaries, and forbidden side effects.
- Scope checks for "allowed changed files" belong in operator workflow, release gate staged-scope checks, or temporary phase validation.

## Prior blocked case

During the AI audit synthetic probe inventory phase, the AI audit schema/helper tests failed because they expected previous-step changed files while a new approved inventory phase was staged.

This was a process/test-scope issue, not an implementation failure.

## Durable test guidance

Durable tests may continue to assert safety invariants such as:

- no protected test item copying;
- no answer-key use;
- no official or clinical score claims;
- no benchmark tuning;
- no runtime/chat/voice behavior changes;
- valid schemas and validation failures for unsafe flags;
- redacted/count-only summaries where required.

Temporary phase validation may assert exact changed-file scope for the active phase, but those assertions should be retired, isolated, or converted before becoming long-lived regression tests.
