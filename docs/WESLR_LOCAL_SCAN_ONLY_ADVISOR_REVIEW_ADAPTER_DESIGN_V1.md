# WESLR Local Scan Only Advisor Review Adapter Design V1

## Status

- design_only
- local_scan_only_advisor_review_adapter
- one-shot local scan
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_persistence
- no_daemon
- no_cron_job
- no_external_model_calls

## Purpose

Design a future one-shot local scan adapter that can detect advisor-review needs and create advisor review queue suggestions without calling external models.

The adapter is a detection-and-suggestion surface only. It inspects local WESLR metadata and emits operator-visible queue suggestions. It does not review with an advisor model, mutate prompt templates, activate providers, or change runtime state.

## Future Local Inputs

A future implementation may inspect local artifacts such as:

- advisor prompt template library
- advisor provider registry records, when implemented
- advisor review queue items
- recent WESLR capability checkpoints
- canon notes
- diagnostics
- release gate/check results
- unsupported-gap trends
- stale prompt-template versions
- provider health notes, if locally recorded

The local scan must treat these inputs as local evidence for whether an operator review is needed. It must not treat any input as proof of truth, soundness, answer correctness, or official score.

## Review Need Detection

The local scan may detect signals such as:

- prompt templates do not cover a new WESLR capability
- provider registry has stale or missing data policy
- advisor provider has repeated timeout/rate-limit notes
- new domain module lacks advisor prompt coverage
- unsupported-gap taxonomy changed
- safety policy changed
- prompt template review date is stale
- a monthly/quarterly/manual review is due

Detected signals should become suggested review needs, not automatic changes.

## Output

The local scan may produce:

- AdvisorReviewQueueItem
- suggested action
- affected template IDs
- affected provider IDs
- capability scope
- risk level
- notes
- recommended operator decision

The output should be queue-safe, redacted/count-only where possible, and suitable for operator review.

## Required Non-Behavior

The local scan must not do any of the following:

- no external model calls
- no automatic advisor calls
- no automatic implementation
- no automatic prompt mutation
- no provider activation
- no automatic provider activation
- no runtime/config changes
- no memory mutation
- no governance override
- no answer selection
- no truth/soundness claim
- no official score
- no answer-key use
- no benchmark text use

## Queue Integration

A future implementation should create queue suggestions using AdvisorReviewQueueItem and safe AdvisorReviewQueueSafetyFlags.

Defaults must be:

- advisor_call_mode = local_scan_only
- advisor_call_allowed = false
- requires_operator_approval = true
- safe AdvisorReviewQueueSafetyFlags

The adapter should populate trigger_reason, affected_templates, affected_providers, capability_scope, risk_level, recommended_action, and notes with local-scan metadata only. AdvisorReviewQueueItem remains a suggestion schema, not an execution instruction.

## Operator Flow

local scan → queue suggestion → operator review → optional advisor call approval → advisor records/proposals/tests later

The optional advisor-call step is outside this design. It requires separate operator/institution approval and a separately approved operator_approved_advisor_call flow.

## Institution and Client Policy

The local scan can run in manual-only, monthly, or quarterly mode later, after separate cadence approval.

Institution/client policy:

- local scan can support manual-only review
- local scan can support monthly review after scheduling approval
- local scan can support quarterly review after scheduling approval
- on-prem deployments can use local scan without external calls
- air-gapped deployments can use local scan without external calls
- client and institution deployments can restrict review suggestions to internal policy
- external advisor calls require separate operator/institution approval

This design supports institution/client/on-prem/air-gapped use because it requires no external model calls.

## Agentic Next-Step Review Principle

After completing a local-scan design or implementation phase, OCC should provide an agentic next-step review that identifies:

1. the next bottleneck,
2. the safest next operator decision,
3. what should explicitly not be done yet.

This review is advisory only. OCC must not implement the suggestion without operator approval.

## Safety Boundaries

The local-scan-only adapter preserves the advisor authority boundary:

- queue suggestions are non-authoritative
- queue suggestions are proposal input only
- operator/institution approval is required before any advisor call or change
- validation is required before action
- no runtime truth authority
- no score authority
- no implementation authority

The adapter must preserve traceability from local signal to queue item to operator decision.

## Non-Goals

- no implementation in this phase
- no file persistence design beyond conceptual queue item creation
- no scheduler/cron/daemon
- no model calls
- no runtime integration
- no OpenClaw config changes
- no automatic prompt edits
- no automatic provider edits
- no answer selection
- no truth/soundness claim
- no official score claim

## Future Phases

- APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_SCHEMA_ONLY
- APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_HELPERS_ONLY
- APPROVE_ADVISOR_REVIEW_QUEUE_PERSISTENCE_DESIGN_ONLY
- APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY
- APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
