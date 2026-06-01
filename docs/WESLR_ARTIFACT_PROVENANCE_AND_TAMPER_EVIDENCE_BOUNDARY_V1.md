# WESLR Artifact Provenance and Tamper Evidence Boundary V1

## SECTION 1 — Executive doctrine

Artifact trust must rely on provenance chains, validation records, hashes, owner approvals, and source lineage — not watermarking alone.

## SECTION 2 — Why this matters

External watermarking and detection can be attacked, stripped, bypassed, or misinterpreted.
WESLR should know:
- what it generated
- when
- from which plan
- under which authority
- with what validation
- what cannot be proven anymore

## SECTION 3 — Boundary position

Pipeline:

project brief
→ architecture
→ stack
→ file manifest
→ scaffold packet
→ artifact writer boundary
→ sandbox writer result
→ provenance record
→ validation report
→ export/package

This boundary sits before real sandbox writes and defines the metadata chain that later write executors should preserve.

## SECTION 4 — Future helper design

Recommend future helper module:

`weslr/artifact_provenance_boundary.py`

Future APIs:
- `build_artifact_provenance_record_v1(...)`
- `build_artifact_provenance_bundle_v1(...)`
- `validate_artifact_provenance_record_v1(record)`
- `validate_artifact_provenance_bundle_v1(bundle)`
- `summarize_artifact_provenance_bundle_v1(bundle)`
- `to_artifact_provenance_json_safe_v1(value)`
- `build_initial_artifact_provenance_examples_v1()`

## SECTION 5 — Provenance record fields

Define:
- `provenance_record_id`
- `artifact_path`
- `artifact_type`
- `content_hash`
- `hash_algorithm`
- `source_project_brief_id`
- `source_architecture_id`
- `source_stack_decision_id`
- `source_manifest_id`
- `source_scaffold_id`
- `source_write_request_id`
- `source_write_decision_id`
- `source_write_result_id`
- `owner_approval_id`
- `operator_approval_id`
- `validation_report_id`
- `created_timestamp`
- `modified_timestamp`
- `generator_type`
- `model_provider_used`
- `provider_trace_id`
- `authority_level_used`
- `sandbox_root`
- `write_mode`
- `tamper_evidence_status`
- `verification_status`
- `public_claim_allowed`
- `runtime_authority`
- `writes_state`
- `safe_metadata`

## SECTION 6 — Tamper evidence statuses

Define:
- `not_yet_hashed`
- `hash_recorded`
- `hash_verified`
- `hash_mismatch`
- `missing_artifact`
- `provenance_incomplete`
- `verification_not_run`

## SECTION 7 — Generator types

Define:
- `deterministic_template`
- `pattern_library`
- `schema_generated`
- `llm_candidate`
- `owner_supplied`
- `manual_edit`
- `unknown_generator`

LLM output is candidate material, not trusted material.

## SECTION 8 — Hashing doctrine

Future implementation may hash artifact content only after write or dry-run content materialization.

Rules:
- use deterministic hash algorithm
- never hash secrets or private raw data into public reports
- record hash metadata separately from raw content
- hash mismatch means artifact changed or provenance incomplete

## SECTION 9 — Approval lineage

Record:
- no approval
- owner approval
- operator approval
- deployment approval
- deletion approval

Approval metadata does not replace validation.

## SECTION 10 — Public claim boundary

Provenance must not become public certification.
Do not claim:
- official validation
- AGI
- Turing result
- consciousness
- sentience
- certified intelligence
- production safety
unless separately authorized and true.

## SECTION 11 — Examples

Include:
1. static website scaffold provenance
2. WiFi/RF self-care scaffold provenance
3. medical software boundary docs provenance
4. AI system research scaffold provenance
5. hash mismatch example
6. LLM candidate provenance example
7. owner manual edit provenance example

## SECTION 12 — Relationship to future LLM wiring

When LLM is wired:
- provider output gets generator_type `llm_candidate`
- provider use is recorded
- model cannot grant authority
- WESLR validates, scopes, hashes, and gates output
- no direct write from model

## SECTION 13 — Relationship to real sandbox writer

Before real sandbox writing:
- provenance plan should exist
- write result should include provenance hooks
- later write executor should produce provenance records

## SECTION 14 — Boundaries

Confirm:
- design only
- no hashing implementation
- no file writes
- no file reads
- no `.weslr` access
- no runtime/chat changes
- no model/provider calls
- protected files untouched

## SECTION 15 — Final judgment

artifact_provenance_tamper_evidence_design_ready_for_metadata_helper_implementation