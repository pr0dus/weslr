# WESLR Local Scan Advisor Queue Mapping Helpers Design V1

## Status

- design_only
- helper_mapping_design
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_queue_writes
- no_external_model_calls
- no_runtime_integration
- no_persistence

## Purpose

Design future helper functions that convert local-scan findings into queue-safe advisor review suggestions.

The helpers are a future in-memory mapping surface only. They should preview candidate queue proposals for operator review, not write queues, create persistence, run scans, call models, mutate runtime state, or activate providers.

## Source and Target

LocalScanFinding / LocalScanReport → AdvisorReviewQueueItem proposal

The future helper boundary is:

1. validate source LocalScanFinding or LocalScanReport,
2. map safe fields into an in-memory AdvisorReviewQueueItem proposal,
3. validate the target AdvisorReviewQueueItem,
4. return the proposal or validation errors,
5. perform no writes or side effects.

## Mapping Rules

Future helpers may use these mapping rules:

- finding_id can become linked note/source reference or suggestion_id if an explicit ID strategy is approved
- finding_type maps to suggestion_type through a safe taxonomy, not raw copy
- trigger_reason maps to trigger_reason
- affected_templates maps to affected_templates
- affected_providers maps to affected_providers
- capability_scope maps to capability_scope
- risk_level maps to risk_level
- recommended_action maps to recommended_action
- advisor_call_mode maps only if safe
- advisor_call_allowed must remain false unless separately approved
- requires_operator_approval must remain true
- notes may map to notes after redaction/safety validation

Suggested finding_type taxonomy:

- stale_prompt_template → prompt_template_review
- missing_template_coverage → prompt_template_review
- provider_health_note → provider_registry_review
- provider_registry_gap → provider_registry_review
- capability_scope_gap → capability_scope_review
- safety_policy_drift → safety_policy_review
- unsupported_gap_trend → gap_taxonomy_review
- review_due → advisor_review
- unknown → unknown or advisor_review by conservative policy

## Fields That Must Not Map Directly

The helpers must not directly copy fields that can carry unsafe or local-only content:

- source_artifact must not map directly; it may be counted or redacted in notes only
- evidence_summary must not map directly; it may be summarized/redacted only
- suggested_queue_type must not blindly become suggestion_type
- schema_version must not be inherited from the local scan schema
- true LocalScanSafetyFlags must block mapping rather than become queue data
- local execution flags such as external_model_call_attempted, advisor_call_attempted, queue_item_created, prompt mutation, provider activation, runtime action, runtime/config, memory, governance, answer, truth, soundness, official-score, answer-key, raw-benchmark, or secrets flags must block mapping

## Required Safe Defaults

Future helpers must enforce:

- advisor_call_mode = local_scan_only
- advisor_call_allowed = false
- requires_operator_approval = true
- source = local_scan
- review_status = pending_review
- operator_decision = pending_review
- safe AdvisorReviewQueueSafetyFlags
- no external model calls
- no queue persistence
- no runtime/config changes
- no prompt mutation
- no provider activation
- no memory mutation
- no governance override

For high-risk findings, a candidate proposal must include notes before it can validate.

## What Helpers May Produce Later

Future helpers may produce:

- in-memory AdvisorReviewQueueItem proposals
- redacted summaries
- validation errors
- operator-review recommendations
- candidate preview lists derived from LocalScanReport findings

These are candidate queue item previews only, not actual queue creation.

## What Helpers Must Not Do

Future helpers must not do any of the following:

- no file writes
- no persistence
- no queue mutation
- no queue writes
- no model calls
- no external model calls
- no advisor calls
- no cron/daemon scheduling
- no scheduler creation
- no runtime/config changes
- no prompt mutation
- no provider activation
- no memory mutation
- no governance override
- no answer selection
- no truth/soundness claim
- no official score
- no answer-key use
- no benchmark text use

## Safety Validation

Future helpers must validate both:

- source LocalScanFinding
- target AdvisorReviewQueueItem

If either validation fails, helper returns validation errors and creates no queue proposal.

The helper must fail closed when:

- source validation reports unsafe flags or prohibited text
- target validation rejects safety defaults
- advisor_call_allowed would become true
- advisor_call_mode would become anything other than local_scan_only without separate approval
- high-risk findings lack notes
- any mapping would require persistence, queue mutation, model calls, runtime/config changes, prompt mutation, provider activation, memory mutation, or governance override

## Redaction and Summary Requirements

Summaries must be redacted/count-only. They must not expose:

- raw benchmark text
- secrets
- API keys
- tokens
- private user data
- answer keys
- official scores

## Non-Goals

- no helper implementation in this phase
- no file persistence design beyond in-memory candidate previews
- no queue writing behavior
- no local scan execution
- no scheduler/cron/daemon
- no model calls
- no runtime integration
- no OpenClaw config changes
- no prompt/provider mutation
- no operator-approved advisor-call flow

## Future Phases

- APPROVE_LOCAL_SCAN_ADVISOR_QUEUE_MAPPING_HELPERS_ONLY
- APPROVE_ADVISOR_REVIEW_QUEUE_PERSISTENCE_DESIGN_ONLY
- APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_HELPERS_ONLY
- APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
