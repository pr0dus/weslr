# WESLR Artifact Writer Boundary V1

## 1. Executive doctrine

The artifact writer boundary is the first gate before WESLR may create or modify real files.

Scaffold generation is not file writing.

A scaffold packet is only proposed content. The artifact writer boundary decides whether that content may become files.

No hidden writes. No silent overwrites. No protected-file edits. No `.weslr` writes. No deployment. No dependency install. No test execution. No public publishing.

## 2. Current capability baseline

WESLR can now produce a full artifact/code chain:

- project brief builder
- project architecture planner
- project stack decision helper
- file manifest builder
- code scaffold generator

WESLR can now produce scaffold content packets, but not write them.

## 3. Boundary position

Pipeline:

project brief
→ architecture
→ stack decision
→ file manifest
→ code scaffold packet
→ artifact writer boundary
→ future sandbox writer
→ validation runner
→ patch loop
→ export

This design covers only the artifact writer boundary.

## 4. Future helper design

Recommended future helper:

`weslr/artifact_writer_boundary.py`

Future public APIs:

- `build_artifact_write_request_v1(...)`
- `evaluate_artifact_write_boundary_v1(write_request)`
- `validate_artifact_write_request_v1(request)`
- `validate_artifact_write_decision_v1(decision)`
- `summarize_artifact_write_decision_v1(decision)`
- `to_artifact_write_json_safe_v1(value)`
- `build_initial_artifact_write_boundary_examples_v1()`

## 5. Write request packet

Fields:

- `write_request_id`
- `source_scaffold_id`
- `source_manifest_id`
- `project_title`
- `requested_root`
- `allowed_root`
- `requested_entries`
- `write_mode`
- `overwrite_policy`
- `create_directories_requested`
- `edit_existing_files_requested`
- `delete_requested`
- `executable_files_requested`
- `dependency_install_requested`
- `test_execution_requested`
- `deployment_requested`
- `public_publish_requested`
- `owner_approval_present`
- `operator_approval_present`
- `sandbox_only`
- `dry_run_only`
- `risk_labels`
- `boundary_requirements`
- `public_claim_allowed`
- `iss_internal_reference_allowed`
- `learning_claimed`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `safe_metadata`

## 6. Write decision packet

Fields:

- `write_decision_id`
- `write_request_id`
- `decision`
- `allowed_entries`
- `blocked_entries`
- `requires_owner_approval_entries`
- `requires_operator_approval_entries`
- `selected_root`
- `effective_write_mode`
- `effective_overwrite_policy`
- `dry_run_required`
- `sandbox_required`
- `directory_creation_allowed`
- `file_creation_allowed`
- `file_edit_allowed`
- `file_delete_allowed`
- `executable_creation_allowed`
- `dependency_install_allowed`
- `test_execution_allowed`
- `deployment_allowed`
- `public_publish_allowed`
- `blocked_reasons`
- `required_approvals`
- `path_safety_result`
- `protected_file_result`
- `secret_scan_result`
- `private_data_scan_result`
- `recommended_next_step`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 7. Decision values

- `allow_dry_run_only`
- `allow_sandbox_create`
- `allow_owner_approved_create`
- `allow_owner_approved_edit`
- `requires_owner_approval`
- `requires_operator_approval`
- `blocked_path_violation`
- `blocked_protected_file`
- `blocked_secret_or_private_data`
- `blocked_executable`
- `blocked_dependency_install`
- `blocked_deployment`
- `blocked_public_publish`
- `blocked_runtime_authority`
- `blocked_unknown`

Default should be conservative:
- dry-run only or blocked
- sandbox create only after approval
- no edit/delete by default

## 8. Write modes

- `dry_run`
- `sandbox_create_only`
- `sandbox_edit_generated_only`
- `owner_approved_create`
- `owner_approved_edit`
- `owner_approved_delete`
- `blocked`

Rules:
- V1 implementation later should begin with dry-run decisions only or metadata-only decisions.
- Real writing requires a separate writer/executor lane.

## 9. Root and path policy

- all paths must be relative to an allowed root
- no absolute paths
- no `..`
- no `~`
- no symlink assumptions
- no writing outside allowed root
- no protected runtime files
- no `.weslr`
- no `.env`
- no secrets/key/token paths
- no hidden credential directories
- no deployment config by default

Protected paths include:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `dialogue.py`
- `chat_ui.py`
- `.weslr`
- `.env`
- secret/key/token-like paths
- deployment/Cloudflare/nginx paths unless separately approved

## 10. Entry policy

Each requested entry must be checked for:

- safe relative path
- known file type
- content kind
- no secrets
- no private data
- no hidden prompt
- no raw transcript
- no executable risk
- owner approval marker
- overwrite marker
- validation marker

## 11. Authority levels

- `no_write_authority`
- `dry_run_authority`
- `sandbox_create_authority`
- `sandbox_edit_generated_authority`
- `owner_create_authority`
- `owner_edit_authority`
- `owner_delete_authority`
- `operator_runtime_authority`
- `deployment_authority`

Rules:
- boundary may require authority but must not grant it silently
- deployment authority is never default
- delete authority is never default
- protected-file authority requires separate owner/operator review

## 12. Sandbox doctrine

All first writing should happen in a controlled sandbox root, not live repo/runtime paths.

Suggested future sandbox concepts:
- `generated_artifacts/`
- `sandbox_artifacts/`
- owner-provided project root
- temporary export bundle

Do not create these now.

Sandbox write rules:
- create-only first
- no overwrite unless generated-only marker exists
- no executable files unless approved
- no dependency install
- no deployment

## 13. Overwrite/edit/delete doctrine

Default:
- create new files only
- no overwrite existing files
- no edit existing files
- no delete files

Edit existing files requires:
- explicit owner approval
- manifest match
- prior generated marker or review
- diff preview
- rollback plan

Delete requires:
- separate deletion boundary
- explicit approval
- never automatic

## 14. Dependency/test/deployment boundary

Artifact writer boundary must block:
- dependency installation
- test execution
- deployment
- public publishing

Those belong to later helpers:
- code validation runner
- dependency policy helper
- deployment/release boundary

## 15. Examples

1. WiFi/RF scaffold dry-run
- decision: allow dry-run only
- sandbox required
- privacy docs allowed as proposed entries
- no sensor implementation authority
- no covert tracking

2. Static website scaffold
- decision: sandbox create may be allowed after owner approval
- no deployment/Cloudflare/nginx edits

3. Medical software scaffold
- decision: requires owner approval
- no diagnosis/treatment implementation
- medical boundary docs allowed in dry run

4. Protected runtime edit request
- request to edit `weslr/chat_responder.py`
- decision: `blocked_protected_file`

5. `.env` write request
- decision: `blocked_secret_or_private_data`

6. `.weslr` write request
- decision: `blocked_path_violation` or protected private state

7. Delete request
- decision: blocked unless separate deletion boundary

## 16. Relationship to validation runner

After artifact writer boundary, next layer should be:
- actual sandbox writer or
- code validation runner design

Recommended order:
1. implement artifact writer boundary as metadata-only evaluator
2. design sandbox artifact writer executor
3. implement sandbox artifact writer executor
4. design code validation runner
5. implement code validation runner

## 17. Relationship to artifact provenance

Every future written artifact should eventually carry:

- source scaffold id
- source manifest id
- project brief/architecture/stack lineage
- timestamp
- hash
- writer decision id
- owner approval id if present
- validation report id later

Recommended future lane:
`DESIGN_WESLR_ARTIFACT_PROVENANCE_AND_TAMPER_EVIDENCE_BOUNDARY_V1`

## 18. Safety boundaries

Forbid:

- hidden file writes
- protected-file edits
- `.weslr` writes
- secret/credential creation
- raw private data writes
- hidden prompt writes
- executable creation without approval
- dependency install
- test execution
- deployment
- public publishing
- public ISS wording
- AGI/consciousness/sentience/Turing/certification claims
- runtime mutation
- model/provider/search calls

## 19. Future implementation lane

Recommend:
`IMPLEMENT_WESLR_ARTIFACT_WRITER_BOUNDARY_V1`

Implementation should be metadata-only evaluator first.
It should not actually write files.

## 20. Boundaries

Confirmed:
- design only
- no implementation
- no file writes
- no artifact directory creation
- no runtime/chat route changes
- no model/provider/search/advisor calls
- no `.weslr` access
- no protected files touched

## 21. Final judgment

`artifact_writer_boundary_design_ready_for_metadata_evaluator_implementation`
