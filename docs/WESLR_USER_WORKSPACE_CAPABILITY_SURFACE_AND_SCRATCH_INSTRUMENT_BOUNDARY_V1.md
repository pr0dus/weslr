# WESLR User Workspace Capability Surface And Scratch Instrument Boundary V1

## 1. Status

- Lane name: `DESIGN_WESLR_USER_WORKSPACE_CAPABILITY_SURFACE_AND_SCRATCH_INSTRUMENT_BOUNDARY_V1`
- Lane type: design-only
- Design path: `docs/WESLR_USER_WORKSPACE_CAPABILITY_SURFACE_AND_SCRATCH_INSTRUMENT_BOUNDARY_V1.md`
- Implementation changes: none
- Workspace creation: none
- Scratch script creation: none
- Runtime wiring: none
- Chat wiring: none
- UI/voice wiring: none
- Provider/model/search/advisor calls: none
- `.weslr` read/write: none
- Source/helper/runtime edits: none
- Final-answer generation: none
- Proof/public/intelligence/Turing/certification/product-readiness claims: none
- Authority grant: none

This document is a boundary design only. It does not implement workspace code, create a user workspace, create scratch scripts, execute scratch tools, wire runtime/chat/UI/voice behavior, call providers/models/search/advisors, read or write `.weslr`, modify WESLR helper/source/runtime files, generate final answers, or grant proof, public, intelligence, Turing, certification, product-readiness, runtime, workspace-creation, scratch-execution, or official-core-promotion authority.

## 2. Purpose

`WeslrUserWorkspaceCapabilitySurfaceV1` is WESLR's human-facing operating layer design.

WESLR is not only a chatbot and not only formal proof tooling. The workspace/capability surface is the general substrate through which a human can work with WESLR across projects, theories, hypotheses, artifacts, sources, memory/context, formal-proof metadata, UNKNOWN ENGINE/Cognitive Gym work, industrial/materials/business workflows, future voice interaction, and small scratch instruments.

The purpose is to keep these surfaces separate:

- official WESLR core
- user workspace artifacts
- scratch instruments
- memory/context
- sources and artifacts
- capability-family metadata
- promotion gates

The workspace surface can coordinate these domains without making every workspace action official WESLR behavior and without promoting provisional artifacts or scratch outputs into truth, runtime, product, proof, or final-answer authority.

## 3. Core Human Workflow

The intended simple user flow is:

1. Human expresses intention.
2. WESLR creates or selects a scoped workspace only in a later authorized implementation; this design creates none.
3. WESLR records goals, sources, assumptions, artifacts, hypotheses, and next safe steps as scoped metadata.
4. WESLR may propose scratch instruments, but this design creates or executes none.
5. WESLR may create metadata cards for specialized capability families.
6. Human approves important transitions.
7. Only reviewed/promoted material affects official WESLR.

Important transitions include content access, private context use, source reads, artifact reads, scratch instrument creation, scratch execution, persistent writes, provider/model/search/advisor use, runtime wiring, official-core promotion, public claims, proof claims, production claims, and final-answer behavior.

## 4. Workspace Boundary Overview

Future concept:

`WeslrUserWorkspaceCapabilitySurfaceV1`

The future workspace boundary is:

- user-facing
- project-scoped
- source-scoped
- artifact-scoped
- memory/context-scoped
- capability-aware
- scratch-instrument-aware
- promotion-gated
- privacy-preserving
- fail-closed
- raw-content-controlled
- authority-denying by default

The workspace boundary is an organizing and metadata layer. It is not official WESLR core, not a runtime/chat layer, not a provider/model/search/advisor layer, not a filesystem scanner, not a `.weslr` reader, not a proof engine, not a production workflow engine, and not final-answer authority.

## 5. Required Workspace Fields

`WeslrUserWorkspaceCapabilitySurfaceV1` requires these fields:

- `workspace_id`
- `workspace_kind`
- `created_at_label`
- `updated_at_label`
- `freshness_label`
- `owner_scope`
- `requester_scope`
- `target_scope`
- `project_scope`
- `session_scope`
- `source_scope`
- `artifact_scope`
- `memory_context_scope`
- `capability_surface_metadata`
- `workspace_artifact_metadata`
- `scratch_instrument_metadata`
- `promotion_gate_metadata`
- `privacy_policy_metadata`
- `execution_policy_metadata`
- `authority_policy_metadata`
- `validation_status`
- `blocked_reason_labels`
- `next_safe_steps`
- `denied_authority`

All fields are metadata-only in this design. Missing scope, missing policy metadata, missing denied-authority fields, true denied-authority values, non-JSON-safe metadata, or authority-bearing claims must fail closed.

## 6. Capability Surface Metadata

`capability_surface_metadata` may represent these capability families without making them active, executed, or runtime-wired:

- general reasoning/project work
- theory/hypothesis work
- UNKNOWN ENGINE
- Cognitive Gym
- formal proof-search metadata
- materials/science exploration
- industrial/TIA/automation workflows
- business/PlantDelux-style workflows
- artifact/upload analysis
- memory/context review
- future voice/live interaction
- future tool/scratch execution
- future advisor/model/provider integrations

Capability presence does not mean capability execution, provider availability, runtime wiring, official behavior, truth authority, final-answer authority, product readiness, proof authority, benchmark authority, intelligence authority, or certification authority.

Capability adapters must remain metadata-only unless a future separately reviewed and authorized lane implements them with source scope, denied-authority fields, privacy boundaries, execution boundaries, and promotion gates.

## 7. Workspace Artifact Types

Possible workspace artifact types include:

- intent cards
- source cards
- assumption cards
- hypothesis cards
- theory cards
- evidence cards
- experiment cards
- failed-path cards
- decision cards
- review cards
- promotion request cards
- formal problem sketch cards
- verifier envelope cards
- misformalization review cards
- scratch instrument cards
- workspace report cards

Workspace artifacts are scoped project/user metadata. They are not global truth, not official WESLR core, not public claims, not final answers, not proof claims, not product-readiness evidence, and not runtime behavior by default.

## 8. Scratch Instrument Boundary

Scratch instruments are small, workspace-local helper scripts/tools proposed by WESLR for a specific user workspace.

Rules:

- not WESLR core
- not official behavior
- workspace-local only
- source-scoped
- approval-gated
- no hidden execution
- no provider/network access unless separately authorized
- no `.weslr` access
- no source-tree writes
- no runtime/chat wiring
- no promotion without review
- no proof/final-answer/public authority

Examples:

- sequence checker
- CSV cleaner
- CIF/materials parser
- industrial JSON normalizer preview
- simple plotting helper
- local consistency checker
- toy theorem fixture helper
- business lead filtering preview

This design creates no scratch instruments and authorizes no scratch execution. A future scratch instrument may only exist after separate design/review/authorization and must remain scoped, reviewable, bounded, and disposable unless promoted through explicit gates.

## 9. Official Core vs Workspace vs Scratch

Strict separation is required.

Official WESLR core:

- reviewed source code
- committed helper/runtime/doc files
- release-gated
- promotion-required

WESLR workspace:

- user/project artifacts
- scoped notes
- sources
- theories
- decisions
- metadata envelopes

Scratch instruments:

- local workspace tools
- disposable/provisional
- not official WESLR
- never promoted automatically

A workspace artifact or scratch output can inform review, but it cannot modify official WESLR core, runtime behavior, final-answer behavior, proof authority, public claims, product behavior, or certification claims unless it passes a later reviewed promotion lane.

## 10. Promotion Gate Metadata

`promotion_gate_metadata` defines:

- `promotion_request_id`
- `promotion_kind`
- `source_workspace_id`
- `artifact_ids`
- `scratch_instrument_ids`
- `promotion_reason_label`
- `promotion_risk_labels`
- `review_required: true`
- `operator_approval_required: true`
- `release_gate_required: true`
- `promotion_grants_runtime_authority: false`
- `promotion_grants_final_answer_authority: false`

Promotion is a request, not a grant. A promotion request cannot bypass review, operator approval, release gates, denied-authority fields, source scope, read authorization, privacy boundaries, or runtime/final-answer restrictions.

## 11. Privacy and Memory Context Boundary

Privacy and memory/context boundaries require:

- user workspace content is not global truth
- memory/context requires scoped read authorization
- raw private content should not leak into reports by default
- cross-user reuse is blocked by default
- private artifacts remain scoped
- workspace summaries are metadata unless explicitly promoted
- workspace memory is not official canon by default

Workspace summaries can support continuity and review, but they must not become automatic evidence, truth, official WESLR canon, public output, final-answer text, product-readiness evidence, or cross-user reusable context unless a later lane explicitly authorizes a bounded promotion.

## 12. Execution Policy Metadata

`execution_policy_metadata` defines:

- `execution_allowed_by_workspace_design: false`
- `scratch_execution_requires_approval: true`
- `network_access_default: false`
- `provider_calls_default: false`
- `filesystem_scope_required: true`
- `persistent_write_requires_approval: true`
- `runtime_wiring_allowed: false`
- `source_tree_write_allowed: false`
- `final_answer_generation_allowed: false`

This design authorizes no execution. Any future workspace or scratch execution requires separate approval, explicit filesystem scope, no hidden execution, no default network/provider access, bounded outputs, and fail-closed behavior.

## 13. Authority Policy Metadata

Authority policy states:

- workspace artifacts do not grant truth
- scratch outputs do not grant truth
- model/advisor outputs do not grant authority
- formal proof metadata does not grant proof claims
- business/materials/industrial artifacts do not grant production readiness
- ranking/scoring does not grant intelligence or benchmark claims
- voice/live interaction does not grant runtime authority without separate wiring review
- promotion is required for official behavior

Authority remains evidence/review/promotion dependent. Workspace material can be useful and still non-authoritative.

## 14. Relationship To Implemented WESLR Helpers

The workspace surface coordinates existing and future WESLR helpers; it does not replace or bypass them.

Relationships:

- `source_scope` validates scope metadata; the workspace surface must not treat scope as permission.
- `read_authorization` gates reads; the workspace surface must not read private memory/context/artifact/cache/log/trace content without authorization.
- Scoped memory/context read adapter remains the boundary for memory/context metadata and future authorized reads.
- Scoped artifact/upload registry remains the boundary for artifact/upload identity and access envelopes.
- Cache/log/trace scoping remains the boundary for diagnostic/cache/log/trace surfaces.
- UNKNOWN ENGINE metadata shadow runner remains separate and metadata-only.
- Cognitive Gym remains separate and metadata-only unless separately authorized for a specific lane.
- Formal proof-search metadata chain remains separate: Lean sketch schema, population registry, verifier envelope, misformalization workflow, rater/critic boundary, global cache boundary, and synthetic Lean dry-run boundary cannot be overridden by a workspace card.
- Safe final response assembly boundaries remain separate and do not become active through workspace artifacts.
- Implemented reasoning-chain gap audits remain blockers before runtime/chat wiring.
- Future voice layer must be separately designed, reviewed, authorized, and wired; workspace voice capability metadata does not create voice runtime.

The workspace surface coordinates these boundaries as metadata. It does not collapse them into a global reader, global tool executor, runtime answer engine, proof engine, or official behavior promotion path.

## 15. Capability Expansion Rule

Future WESLR capabilities attach to the workspace surface only by capability adapter metadata, with:

- source scope
- denied-authority fields
- privacy boundaries
- execution boundaries
- promotion gates
- no automatic runtime authority
- no official claims without evidence/review

Every new capability must state what it can represent, what it cannot execute, what it cannot claim, what scopes it requires, what reads it needs, what privacy boundary applies, what execution gates apply, and what promotion path is required for official behavior.

## 16. Validation Status

`validation_status` may use these labels:

- `design_only`
- `workspace_not_created`
- `scratch_instruments_not_created`
- `blocked_missing_scope`
- `blocked_missing_authorization`
- `blocked_raw_private_content`
- `blocked_unapproved_execution`
- `blocked_source_tree_write`
- `blocked_runtime_wiring`
- `blocked_promotion_without_review`
- `blocked_claim_authority`
- `ready_for_boundary_review`

These labels are metadata only. They do not mean workspace creation, scratch creation, scratch execution, runtime readiness, final-answer readiness, public readiness, proof authority, product readiness, intelligence evidence, or certification authority.

## 17. Denied Authority Fields

`denied_authority` requires all fields below to be present and false:

- `permits_workspace_creation: false`
- `permits_scratch_script_creation: false`
- `permits_scratch_execution: false`
- `permits_source_tree_writes: false`
- `permits_runtime_chat_wiring: false`
- `permits_voice_runtime_wiring: false`
- `permits_provider_calls: false`
- `permits_model_calls: false`
- `permits_search_calls: false`
- `permits_advisor_calls: false`
- `permits_dot_weslr_reads: false`
- `permits_dot_weslr_writes: false`
- `permits_private_context_reads: false`
- `permits_artifact_content_reads: false`
- `permits_cross_user_reuse: false`
- `permits_cache_log_trace_reads: false`
- `permits_cache_log_trace_writes: false`
- `permits_final_answer_generation: false`
- `permits_official_core_promotion: false`
- `permits_proof_claims: false`
- `permits_public_claims: false`
- `permits_benchmark_claims: false`
- `permits_intelligence_claims: false`
- `permits_turing_claims: false`
- `permits_certification_claims: false`
- `permits_product_readiness_claims: false`

Missing denied-authority fields or true values must fail closed.

## 18. Fail-Closed Rules

Future validation must block if:

- workspace/project/source/owner/requester/target scope is missing
- capability metadata is missing
- privacy policy is missing
- execution policy is missing
- promotion policy is missing
- scratch instrument tries to write source tree
- scratch instrument tries to access `.weslr`
- scratch instrument tries network/provider/search/advisor access without approval
- workspace content implies official WESLR behavior
- workspace artifact implies proof/public/product/intelligence authority
- promotion requested without review
- cross-user reuse is implied
- runtime/chat/voice wiring is implied
- final-answer authority is implied
- non-JSON-safe metadata appears

Fail-closed behavior must return metadata-only blocked status. It must not create workspaces, create scripts, execute tools, read private context, read artifacts, scan filesystems, read or write `.weslr`, call providers/models/search/advisors, write source trees, wire runtime/chat/voice/UI, generate final answers, or promote official WESLR behavior.

## 19. Example Human Workflows

Examples of future human workflows:

### Help me explore a theorem

WESLR may create scoped intent/source/assumption/hypothesis/formal-problem-sketch metadata and propose a toy theorem fixture helper. It must not run Lean, attempt real open problems, make proof claims, or promote proof authority without separate lanes.

### Help me investigate a material

WESLR may organize source cards, CIF/materials parser scratch-instrument proposals, experiment cards, evidence cards, and review cards. Scratch parsing is not production or scientific authority and requires approval before execution.

### Help me inspect an industrial project export

WESLR may create artifact metadata, industrial JSON normalizer preview proposals, source cards, assumption cards, and review cards. It must not touch TIA/C#/Siemens bridge files, production systems, private exports, or provider/network tools without separate authorization.

### Help me build a business outreach plan

WESLR may organize intent, source, hypothesis, lead-filtering preview, decision, and review cards. It must not send outreach, scrape the web, call providers/search/advisors, or claim business readiness without explicit authorization.

### Help me understand my own project history

WESLR may request scoped memory/context review metadata and summarize authorized continuity anchors. It must not treat memory as global truth or leak raw private context by default.

### Help me create a scratch script for this workspace

WESLR may propose a scratch instrument card with purpose, scope, risks, filesystem boundary, approval requirement, and denied-authority fields. It must not create or run the script in this design lane.

### Promote this workspace result into official WESLR after review

WESLR may create a promotion request card requiring review, operator approval, release gate, risk labels, and explicit non-runtime/non-final-answer authority defaults. Promotion is not automatic.

## 20. Relationship To OCC

- OCC builds WESLR.
- WESLR workspace is for humans using WESLR.
- OCC context alignment does not equal WESLR runtime behavior.
- WESLR workspace artifacts do not modify WESLR core unless promoted through reviewed lanes.

OCC may design, review, implement, and validate WESLR artifacts when instructed. OCC must not treat workspace design metadata as permission to create WESLR runtime behavior, create user workspaces, create scratch scripts, execute tools, or modify official core outside reviewed lanes.

## 21. Future Negative Tests Required

Future synthetic-only tests must cover:

- missing workspace scope
- missing source scope
- missing privacy policy
- missing execution policy
- missing promotion policy
- scratch instrument writes source tree
- scratch instrument accesses `.weslr`
- scratch instrument uses network/provider/search/advisor without approval
- workspace artifact claims official authority
- workspace artifact claims proof/public/product/intelligence authority
- cross-user reuse marker
- runtime/chat/voice wiring marker
- final-answer authority marker
- official promotion without review
- non-JSON-safe metadata
- valid metadata-only workspace boundary

Tests must be synthetic-only and must not create real workspaces, create or execute scratch scripts, read `.weslr`, read private memory/context/artifacts/cache/log/trace content, call providers/models/search/advisors, wire runtime/chat/voice/UI, generate final answers, promote official core, or make proof/public/product/intelligence/Turing/certification claims.

## 22. Decision

`weslr_user_workspace_capability_surface_scratch_instrument_boundary_design_ready_for_review`

## 23. Next Lane

`REVIEW_WESLR_USER_WORKSPACE_CAPABILITY_SURFACE_AND_SCRATCH_INSTRUMENT_BOUNDARY_V1`
