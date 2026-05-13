# WESLR Advisor Review Queue Adapter Design V1

## Status

- design_only
- advisor_review_queue_adapter
- one-shot adapter
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_daemon
- no_cron_job

## Purpose

Design a future one-shot advisor-review adapter that reuses WESLR's existing suggestion and review queue patterns instead of creating a new daemon.

Design concept:

advisor review need detected → one-shot local scan → optional operator-approved advisor review request → suggestion/proposal queue item → operator review

This phase is design only. It does not implement adapter behavior, create a daemon, create cron jobs, call advisor models, change runtime state, or mutate configuration.

## Existing Queue Infrastructure to Reuse or Align With

A future adapter should reuse or align with existing WESLR suggestion/review queues and operator surfaces:

- pending_messages_queue
- capability discovery review queue
- review_queue.json
- suggestion box / proposal review surfaces
- continuity/suggestion_box/*
- operator-facing proposal review surfaces

The adapter should follow the existing pattern: local detection produces operator-visible suggestion/proposal records, not automatic changes.

## No-New-Daemon Boundary

V1 must explicitly avoid adding resident background infrastructure:

- no resident advisor daemon in V1
- no new daemon in V1
- no background loop in V1
- no cron job in this design phase
- no new scheduler in this design phase
- future cron may trigger one-shot only after separate approval

The existing proactive and frontier daemons are opt-in/default-disabled and are not a reason to introduce a new advisor daemon. Advisor review cadence should be represented as an approved trigger for a one-shot adapter, not as an always-running WESLR loop.

## Future One-Shot Adapter Behavior

A future adapter may perform a local_scan_only pass that scans local WESLR metadata and docs for review needs. It may:

- scan advisor prompt-template versions
- scan provider registry entries
- detect stale templates
- detect new WESLR capabilities not covered by templates
- detect provider health/rate-limit notes
- create advisor-review suggestion records
- create operator review items

The adapter's output should be queue/proposal records. It should not perform remediation, activation, or hidden review.

## Required Non-Behavior

The future adapter must not do any of the following:

- no automatic model calls unless operator-approved
- no automatic implementation
- no automatic prompt mutation
- no automatic provider activation
- no runtime/config changes
- no memory mutation
- no governance override
- no answer selection
- no truth/soundness claim
- no official score
- no answer-key use
- no benchmark text use

## Advisor Call Modes

The design supports two future call modes:

1. local_scan_only
   - Reads local WESLR design/registry/template metadata.
   - Detects stale or uncovered review needs.
   - Writes suggestion/proposal records only.
   - No external model call.

2. operator_approved_advisor_call
   - Requires explicit operator/institution approval.
   - Uses provider registry and redaction policy.
   - Records provider identity, model identity, prompt template version, failure/timeout status, and review provenance.
   - Produces proposal input only, not WESLR authority.

## Future Queue/Suggestion Fields

Future queue or suggestion records should include fields such as:

- suggestion_id
- suggestion_type
- source
- trigger_reason
- affected_templates
- affected_providers
- capability_scope
- risk_level
- recommended_action
- requires_operator_approval
- advisor_call_allowed
- created_at
- status

The default posture should be requires_operator_approval=true and advisor_call_allowed=false unless a separate approved policy allows escalation.

## Institution and Client Policy

Institutions may choose manual-only, monthly, or quarterly review. Institutions and clients may also restrict reviews to internal, on-premise, or air-gapped advisors.

Institution/client policy requirements:

- institutions may choose manual-only review
- institutions may choose monthly review after scheduling approval
- institutions may choose quarterly review after scheduling approval
- institutions may restrict reviews to internal advisors
- institutions may restrict reviews to on-prem advisors
- institutions may restrict reviews to air-gapped advisors
- all suggestions remain operator/institution review items
- no hidden external calls

Client-owned, institution-owned, and domain-specific advisor output remains proposal input only.

## Connection to Future Cadence

Cadence is not implemented here.

Future OpenClaw cron can trigger the one-shot adapter only after all of the following exist and are approved:

- registry schema exists
- queue schema exists
- operator approval policy exists
- redaction policy exists
- scheduling design is approved

Until then, advisor-review cadence should remain a design concept, not runtime behavior.

## Safety Boundaries

The adapter design preserves the advisor authority boundary:

- advisor output is non-authoritative
- advisor output is proposal input only
- operator/institution approval is required before action
- validation is required before action
- no runtime truth authority
- no score authority
- no implementation authority

The adapter must preserve traceability from trigger reason to queue item to operator decision.

## Non-Goals

- no adapter implementation in this phase
- no daemon
- no background loop
- no cron job
- no scheduler
- no config changes
- no runtime changes
- no external model calls
- no advisor runner
- no automatic prompt edits
- no automatic provider edits
- no answer selection
- no truth/soundness claim
- no official score claim

## Future Phases

- APPROVE_ADVISOR_REVIEW_QUEUE_SCHEMA_ONLY
- APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_ONLY
- APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY
- APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
