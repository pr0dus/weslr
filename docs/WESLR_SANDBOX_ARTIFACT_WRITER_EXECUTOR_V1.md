# WESLR Sandbox Artifact Writer Executor V1

## 1. Executive doctrine

The sandbox artifact writer executor is the first future component that may materialize scaffold packets into real files, but only inside a controlled sandbox root and only after artifact writer boundary approval.

The sandbox writer must preserve WESLR’s artifact-generation capability while preventing:
- hidden writes
- protected-file edits
- path traversal
- `.weslr` writes
- secrets/private data writes
- destructive edits/deletes
- dependency installs
- deployments
- runtime mutation
- public publishing

## 2. Current capability baseline

Current chain:

project brief
→ architecture planner
→ stack decision helper
→ file manifest builder
→ code scaffold generator
→ artifact writer boundary

WESLR can now decide whether a scaffold packet is safe to write, but no executor exists yet.

## 3. Executor position

Pipeline:

scaffold content packet
→ artifact write request
→ artifact writer boundary decision
→ sandbox artifact writer executor
→ write result packet
→ future validation runner
→ patch loop
→ export/provenance

This design covers only the sandbox writer executor.

## 4. Future helper design

Recommended future helper:

`weslr/sandbox_artifact_writer_executor.py`

Future public APIs:

- `build_sandbox_artifact_write_execution_request_v1(...)`
- `execute_sandbox_artifact_write_v1(write_request, write_decision, scaffold_packet, sandbox_root=None)`
- `validate_sandbox_artifact_write_execution_request_v1(request)`
- `validate_sandbox_artifact_write_result_v1(result)`
- `summarize_sandbox_artifact_write_result_v1(result)`
- `to_sandbox_artifact_write_json_safe_v1(value)`
- `build_initial_sandbox_artifact_writer_examples_v1()`

## 5. Execution request packet

Fields:

- `execution_request_id`
- `source_write_request_id`
- `source_write_decision_id`
- `source_scaffold_id`
- `source_manifest_id`
- `project_title`
- `sandbox_root`
- `allowed_root`
- `entries_to_write`
- `dry_run`
- `create_directories`
- `overwrite_existing`
- `edit_existing_files`
- `delete_requested`
- `dependency_install_requested`
- `test_execution_requested`
- `deployment_requested`
- `public_publish_requested`
- `owner_approval_present`
- `operator_approval_present`
- `max_files`
- `max_total_bytes`
- `max_file_bytes`
- `chunking_required`
- `provenance_required`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 6. Write result packet

Fields:

- `write_result_id`
- `execution_request_id`
- `executed`
- `dry_run`
- `blocked`
- `blocked_reason`
- `sandbox_root_used`
- `created_directories`
- `created_files`
- `skipped_files`
- `blocked_files`
- `would_create_files`
- `would_create_directories`
- `result_file_count`
- `result_total_bytes`
- `partial_result`
- `chunking_required`
- `provenance_records`
- `path_safety_result`
- `protected_file_result`
- `secret_scan_result`
- `private_data_scan_result`
- `overwrite_result`
- `delete_result`
- `dependency_install_result`
- `test_execution_result`
- `deployment_result`
- `public_publish_result`
- `recommended_next_step`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 7. File result item shape

Per-file fields:

- `path`
- `file_type`
- `content_kind`
- `bytes_estimate`
- `action`
- `status`
- `blocked_reason`
- `created`
- `would_create`
- `skipped`
- `overwrite_performed`
- `secret_detected`
- `private_data_detected`
- `protected_path`
- `source_entry_id`
- `source_manifest_id`
- `source_scaffold_id`
- `safe_metadata`

## 8. Sandbox root doctrine

First writer executor must write only inside explicitly supplied sandbox root.

Rules:
- no default root guessing
- no home expansion
- no absolute target paths from scaffold entries
- all entries must be joined under sandbox root
- all normalized paths must remain inside sandbox root
- no symlink assumptions
- no parent traversal
- no `.weslr`
- no protected runtime paths
- no `.env`
- no secrets/key/token paths

If sandbox root is missing:
- dry-run may be allowed
- real write blocked

## 9. Dry-run first doctrine

Initial implementation should support dry-run result packets first.

Dry-run:
- validates what would be written
- estimates file count/bytes
- reports blocked/skipped entries
- does not touch disk

Real sandbox create:
- later explicitly authorized mode
- create-only
- no overwrite
- no edit
- no delete

## 10. Capability preservation doctrine

The sandbox writer must not reduce scaffold capability.

If request is too large:
- mark `chunking_required`
- split or recommend chunks later
- do not declare WESLR incapable

If some entries are unsafe:
- block only unsafe entries
- allow safe entries if decision permits
- report safe alternative mode

## 11. Content safety scan

Before writing, scan entry content for:
- secret markers
- private key patterns
- token-like fields
- `.env` content
- raw private data markers
- hidden prompt markers
- public ISS wording
- AGI/consciousness/certification claims
- unsafe deployment commands
- covert tracking indicators
- diagnosis/treatment authority markers

## 12. Operation boundaries

Sandbox writer must block:
- delete
- overwrite
- edit existing files
- executable creation
- dependency install
- test execution
- deployment
- public publish
- runtime mutation
- `.weslr` state writes

Those belong to future separate authority lanes.

## 13. Provenance doctrine

Every written file should eventually have provenance metadata:
- source scaffold id
- source manifest id
- write decision id
- writer result id
- path
- content hash
- timestamp
- generation method
- approval id if present

This can be planned in V1 even if hash/timestamp are implemented later.

## 14. Example cases

1. Dry-run WiFi/RF scaffold
- would create docs/config/src/tests
- no real write
- privacy docs allowed
- covert/diagnosis files blocked

2. Static website sandbox write
- would create site/index.html, styles.css, app.js
- no deployment files
- sandbox required

3. Large scaffold
- chunking required
- capability preserved

4. `.env` entry
- blocked

5. Protected runtime path
- blocked

6. Delete request
- blocked

7. Missing sandbox root
- dry-run allowed, real write blocked

## 15. Future implementation plan

1. metadata-only dry-run executor
2. dry-run with content safety scanning
3. create-only sandbox executor
4. generated-only edit executor
5. validation runner
6. provenance/tamper evidence
7. export bundle

## 16. Boundaries

Confirmed:
- design only
- no implementation
- no file writes
- no directory creation
- no file reads
- no `.weslr` access
- no runtime/chat route changes
- no model/provider/search/advisor calls
- no deployment
- protected files untouched

## 17. Final judgment

`sandbox_artifact_writer_executor_design_ready_for_dry_run_implementation`
