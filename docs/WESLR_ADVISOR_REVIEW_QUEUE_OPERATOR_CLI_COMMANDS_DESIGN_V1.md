# WESLR Advisor Review Queue Operator CLI Commands Design V1

## Status

- design_only
- command_boundary_design
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_command_registration
- no_queue_writes
- no_external_model_calls

## Purpose

Design future operator CLI command boundaries for reviewing advisor-review queue items safely.

This document is design-only. It does not implement real commands, register CLI commands, add command routing, read or write queue files, call models, activate providers, select answers, or claim truth, soundness, or an official score.

## Command-shell principle

Future CLI commands must be thin shells over validated helper functions. Commands must not create new authority, bypass validation, or silently mutate queue records.

A command shell should translate operator input into schema objects, pass those objects through approved validation, and render safe redacted output. The shell itself should not own policy, persistence authority, model authority, runtime authority, or scoring authority.

## Future command set

Design future commands:

- `advisor-queue list`
- `advisor-queue show <id>`
- `advisor-queue summary`
- `advisor-queue filter --status --type --risk`
- `advisor-queue decide <id> --decision accepted|rejected|deferred`
- `advisor-queue archive <id>`
- `advisor-queue export --redacted`

## Command boundary

Each future command must:

- create an `AdvisorQueueCLIRequest`
- validate request
- call only approved CLI/persistence helpers
- return an `AdvisorQueueCLIResult`
- output redacted summaries by default
- never bypass operator approval

## Dry-run first

Initial command implementation, when later approved, should be dry-run/no-I/O first:

- no queue writes
- no status updates
- no advisor calls
- no runtime/config changes
- explicit path required for any test queue file
- no default write to `.weslr/advisor_review_queue.jsonl`

## Queue I/O boundary

Real queue read/write must require a separate phase:

- `APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_COMMANDS_DRY_RUN_ONLY`
- then later, separate approval for real read/list
- then later, separate approval for real status update/write

No command phase should silently expand from dry-run into real queue I/O.

## What commands must not do

Future commands must not:

- no external model calls
- no advisor provider calls
- no automatic implementation
- no prompt mutation
- no provider activation
- no runtime/config changes
- no memory mutation
- no governance override
- no answer selection
- no truth/soundness claim
- no official score
- no raw benchmark text
- no secrets/API keys/tokens

## Safety output

Future command output must:

- be redacted by default
- include count summaries rather than raw sensitive fields
- show item IDs, statuses, risk levels, and recommended actions only when safe
- never display secrets or raw benchmark text
- clearly mark dry-run vs real action

## Institution/client policy

- institution deployments may restrict commands by role
- air-gapped/on-prem deployments keep queue local
- export is redacted by default
- real status changes may require institution admin approval later

## Non-goals

This phase explicitly does not include:

- no implementation in this phase
- no command registration
- no CLI routing
- no queue file read/write
- no status update execution
- no model calls
- no runtime integration
- no OpenClaw config changes

## Future phases

Possible future operator decisions:

- APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_COMMANDS_DRY_RUN_ONLY
- APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_READ_ONLY_COMMANDS_ONLY
- APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_STATUS_UPDATE_COMMANDS_ONLY
- APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY
- APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
