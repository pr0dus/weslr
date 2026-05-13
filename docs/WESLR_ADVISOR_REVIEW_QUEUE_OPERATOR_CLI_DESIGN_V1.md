# WESLR Advisor Review Queue Operator CLI Design V1

## Status

- design_only
- operator_cli_design
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_queue_writes
- no_external_model_calls

## Purpose

Design a future operator-facing CLI for safely reviewing advisor-review queue items created by local-scan/advisor workflows.

This document is a design boundary only. It does not implement CLI behavior, create queue files, call models, activate providers, select answers, or claim truth, soundness, or an official score.

## CLI scope

A future CLI may support operator review actions over persisted advisor-review queue items:

- list queue items
- show one item by id
- summarize pending items
- filter by status/type/risk
- mark item accepted/rejected/deferred/archived
- record operator decision
- export redacted summary

## CLI must not

A future CLI must not:

- call external models
- call advisor providers
- implement suggestions automatically
- mutate prompts automatically
- activate providers
- change runtime/config
- mutate memory
- override governance
- select answers
- claim truth/soundness
- claim official score
- store raw benchmark text
- store secrets/API keys/tokens

## Command design

Possible future command shapes:

- `advisor-queue list`
- `advisor-queue show <id>`
- `advisor-queue summary`
- `advisor-queue decide <id> --decision accepted|rejected|deferred`
- `advisor-queue archive <id>`
- `advisor-queue export --redacted`

The command names are proposed interface shapes only. They are not implemented in this phase.

## Safety defaults

Future CLI safety defaults should be:

- redacted output by default
- operator approval required
- no external calls
- no automatic implementation
- no direct runtime/config mutation
- append-only status update events
- original queue item content never silently modified

## Persistence interaction

A future CLI should interact only with existing advisor-review queue persistence concepts:

- `AdvisorReviewQueueItem`
- `AdvisorQueuePersistenceEvent`
- append-only JSONL persistence helpers
- status update events
- redacted summaries

The future CLI should record decisions as append-only status update events instead of rewriting original queue item content. Original queue item content should never be silently modified.

## Institution/client policy

- institution deployments may restrict CLI decisions by role
- air-gapped/on-prem deployments keep queue local
- export must be redacted by default
- retention policy is future work

## Non-goals

This phase explicitly does not include:

- no implementation in this phase
- no real CLI commands
- no queue file creation
- no queue mutation
- no model calls
- no runtime integration
- no OpenClaw config changes

## Future phases

Possible future operator decisions:

- APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_SCHEMA_ONLY
- APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_HELPERS_ONLY
- APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_COMMANDS_ONLY
- APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY
- APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
