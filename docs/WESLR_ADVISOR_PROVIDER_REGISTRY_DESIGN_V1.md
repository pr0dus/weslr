# WESLR Advisor Provider Registry Design V1

## Status

- design_only
- advisor_provider_registry
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration

## Purpose

Design a provider-neutral registry for WESLR advisor providers and models, including client-owned and institution-owned LLMs, without making any advisor a runtime authority or truth source.

The registry is a future governance surface for describing which advisor providers may be used for which review tasks, under which data policies, with which prompt-template versions, and with which approval requirements. This phase does not implement registry behavior.

## Provider-Neutral Registry

The registry must support provider categories without making any provider authoritative:

- OpenAI / OpenAI-Codex
- Ollama local
- Ollama cloud
- OpenRouter
- GitHub Copilot
- institution-owned LLMs
- local private models
- on-premise models
- air-gapped models
- domain-specific expert models

Provider identity must remain visible for audit. The registry should use provider-neutral language such as advisor provider, advisor model, deployment type, institution owner, and capability scope. It must not assume OpenAI, cloud-hosted models, or any single vendor as the default authority.

## Advisor Output Authority Boundary

Every provider and model registered for advisor use must be treated as:

- non-authoritative
- proposal source only
- requires validation
- requires operator/institution approval
- not runtime truth

Client-owned advisor output, institution-owned advisor output, and company-owned advisor output remain proposal input only. They do not become WESLR authority, proof authority, memory authority, runtime authority, answer authority, or score authority.

## Future Provider Registration Fields

A future registry record should include fields such as:

- provider_id
- provider_type
- model_name
- deployment_type
- institution_owner
- allowed_tasks
- forbidden_tasks
- data_policy
- redaction_policy
- audit_logging_required
- operator_approval_required
- allowed_prompt_template_versions
- last_prompt_template_review
- capability_scope
- safety_profile
- rate_limit_notes
- failure_policy

These fields should support provider-neutral governance and institution-specific constraints without encoding vendor-specific authority.

## Prompt-Template Lifecycle

Advisor prompt templates are versioned. Prompts must be revisited as WESLR gains capabilities.

Prompt-template review is required when:

- WESLR adds a new reasoning lane
- WESLR adds a new domain module
- WESLR adds new memory/governance behavior
- WESLR adds new runtime actions
- WESLR changes safety policy
- a client/institution adds a domain-specific advisor
- diagnostics show advisor prompts are stale or incomplete

The registry should record allowed prompt template versions and last_prompt_template_review so provider use can be audited against the current WESLR capability boundary.

## Registry Safety Policy

The registry must forbid:

- answer selection
- truth/soundness authority
- official score claims
- answer-key use
- benchmark-specific tuning
- hidden memory mutation
- runtime/config mutation
- governance override
- raw benchmark text by default
- secrets/API keys/tokens
- private user data by default
- model-internal extraction

No provider registration may weaken these boundaries. Provider-specific capability claims are advisory metadata only.

## Provider Task Scopes

Provider task scopes may include:

- architecture review
- failure diagnosis
- style review
- test suggestion
- synthetic example suggestion
- reasoning-pattern review
- gap taxonomy review
- wording-risk review
- alternative design proposal
- provider capability review
- institution-domain review

Task scope is permission metadata, not authority. A provider allowed to perform a task still produces only non-authoritative proposal input requiring validation and approval.

## Multi-Provider Policy

Important reviews should use 2–5 advisor models when available.

The registry should:

- record model identity
- record provider identity
- record failures/timeouts
- avoid long fallback chains
- avoid auto-routing when traceability is required
- record failed advisors without treating failure as fatal
- treat weaker/free models as secondary/noise checks, not final authority

Governed reviews should prefer explicit provider selection over opaque routing. Auto-routing is inappropriate when traceability is required unless explicitly allowed by an operator/institution policy.

## Client and Institution Support

Institutions may register their own advisor LLMs.

The registry must support bring your own advisor model patterns, including:

- client-owned advisor models
- institution-owned advisor models
- company-owned advisor models
- on-premise advisor models
- air-gapped advisor models
- domain-specific expert advisor models

Institution-owned advisors can have stricter data policies. On-premise and air-gapped advisors may be required for sensitive domains. WESLR must support bring your own advisor model while preserving the boundary that advisor output remains proposal input, not WESLR authority.

## Non-Goals

- no registry implementation in this phase
- no config changes
- no live model calls
- no advisor runner
- no runtime integration
- no public behavior
- no automatic model fallback changes

## Future Phases

- APPROVE_ADVISOR_PROVIDER_REGISTRY_SCHEMA_ONLY
- APPROVE_ADVISOR_PROMPT_TEMPLATE_REVIEW_CADENCE_ONLY
- APPROVE_OFFLINE_ADVISOR_REVIEW_RUNNER_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
