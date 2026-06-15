# WESLR Controlled Source Ingestion Executor Boundary V1 Design

## 1. Boundary Name
controlled_source_ingestion_executor_boundary_v1

## 2. Purpose
To enable WESLR to execute source fetching/reading/extraction only after a valid source-ingestion authorization packet exists and all constraints (retention, provenance, privacy, license, authority, review) are met.

## 3. Architecture Position

- Authorization Packet
- \u27A1 Controlled Source Ingestion Executor Boundary
- \u27A1 Bounded Extracted Material/Source Metadata
- \u27A1 Source Interpretation Packet
- \u27A1 Review
- \u27A1 Later Normalization/Artifacts

## 4. Executor Modes (Future, Not Implemented)

- metadata_only_probe
- bounded_text_extract
- bounded_pdf_extract
- bounded_dataset_metadata_extract
- github_repository_metadata_extract
- owner_uploaded_file_extract
- owner_pasted_text_extract
- transient_full_text_read_no_retention
- blocked_execution

## 5. Allowed Source Types (Post-Authorization)

- public/open URL
- public/open PDF
- public/open dataset metadata
- public/open GitHub repository metadata
- official standard/reference
- official agency/government data
- vendor documentation
- public research paper
- public university/lab artifact
- owner-uploaded file
- owner-pasted text
- authorized local file
- selected metadata-locator results

## 6. Blocked Source Types

- ".weslr"
- hidden prompts
- private memory
- credentials/secrets/tokens
- private data without explicit authorization
- unknown license without explicit owner/operator approval
- restricted, paid, or copyrighted full-text without permission
- private GitHub repositories without explicit authorization
- deception, bypass, or credential misuse
- sources exceeding size/excerpt policy
- sources missing required provenance/citation

## 7. Input Packet Requirements
Executor may run only if authorization packet contains valid schema/version and fields:

- source_ref
- source_class
- source_access_level
- license_access_posture
- privacy_posture
- ingestion_purpose
- retention_mode
- raw_retention_allowed
- quoted_excerpt_allowed
- max_excerpt_policy
- owner_authorization_required/present
- operator_review_required
- expert_review_required
- blocked_claims
- denied_authority_flags (all false)
- abort_conditions
- next_safe_step

## 8. Executor Output Packet: ``source_ingestion_execution_packet_v1``

Required fields:

- schema_name
- schema_version
- execution_packet_id
- ingestion_request_id
- authorization_packet_ref
- source_ref
- source_class
- executor_mode
- execution_status
- access_status
- retention_mode
- bounded_content_policy
- source_metadata
- bounded_extracted_material
- extraction_limits_applied
- provenance_refs
- content_retained
- raw_content_retained
- secrets_detected
- privacy_flags
- license_flags
- abort_conditions_triggered
- blocked_labels
- denied_authority_flags
- review_requirements
- safe_metadata_summary
- next_safe_step
- final_judgment

## 9. Execution Statuses

- not_run
- authorized_ready_to_run
- executed_metadata_only
- executed_bounded_extract
- executed_transient_no_retention
- blocked_by_authorization
- blocked_by_license
- blocked_by_privacy
- blocked_by_retention_policy
- blocked_by_size_limit
- blocked_by_source_type
- blocked_by_secret_detection
- blocked_by_missing_provenance
- blocked_by_operator_review
- failed_safe

## 10. Retention Enforcement

- Metadata-only means no content extraction
- Bounded excerpt requires citation/source location and excerpt limits
- Transient full-text read must not retain raw text
- Raw retention requires explicit owner authorization
- Blocked retention blocks execution
- Source dumps forbidden by default

## 11. Provenance Minimum

At least one safe provenance reference must be present:

- Source URL or reference
- Citation/provenance reference
- Locator record reference
- Owner-uploaded file identifier
- Source location reference for excerpt

## 12. Extraction Limits (Future Configurable)

- Maximum bytes
- Maximum characters
- Maximum number of excerpts
- Maximum excerpt length
- Allowed MIME/source classes
- Timeout
- Redirect policy
- Access/license posture
- No credential use unless authorized

## 13. Safety Scanners (Future)

- ".weslr" detector
- Secret/token detector
- Credential detector
- Hidden prompt detector
- Private data marker detector
- Raw dump detector
- Final-answer/proof/discovery wording detector
- Accepted evidence/candidate wording detector
- Source license/access posture check
- Provenance availability check

## 14. Denied Authority Flags

Executor output must keep explicit false flags for:

- Accepted evidence authority
- Accepted candidate authority
- Final answer authority
- Public claim authority
- Proof claim authority
- Discovery truth claim authority
- Product readiness claim authority
- Runtime wiring authority
- Provider/model call authority
- Memory mutation authority
- Database write authority
- ".weslr" IO authority
- Ontology auto-application authority
- Self-modification authority

## 15. Relationship to Source Interpretation Packet

The executor does not interpret claims; it produces bounded source-access and extraction output for the interpretation helper.

## 16. Relationship to MLCF

The executor does not write to MLCF but may provide provenance, retention, and source-class metadata for later normalization.

## 17. API Implication

Future private/local API endpoint "POST /ingestion/execute" must be packet-based, disabled by default, require authorization packet, no public exposure, no raw dumps, no final answers, and no accepted evidence/candidates.

## 18. Owner/Assistant Workflow

Source or Question
→ Authorization Packet
→ Owner Approval (if needed)
→ Controlled Executor
→ Source Interpretation Packet
→ Review
→ Later Evidence/Artifact Lanes

## 19. Abort Conditions

Abort if:

- Authorization packet invalid
- Denied authority flag true
- Blocked source class/access/license/privacy posture
- Owner authorization missing if required
- Retention mode invalid or blocked
- ".weslr" source detected
- Hidden prompt or private memory detected
- Secrets, credentials, or tokens detected
- Source exceeds size or excerpt policy
- Missing provenance
- Credentials required but not authorized
- Deception or bypass requests
- Raw content beyond policy
- Requests for final answers, accepted evidence, or public claims

## 20. Future Implementation Sequence

- `weslr/source_ingestion_execution_boundary.py`
- `weslr/tests/test_source_ingestion_execution_boundary_v1.py`

Future APIs:

- `build_source_ingestion_execution_packet_v1`
- `validate_source_ingestion_execution_packet_v1`
- `summarize_source_ingestion_execution_packet_v1`
- `render_source_ingestion_execution_markdown_v1`
- `to_source_ingestion_execution_json_safe_v1`
- `build_initial_source_ingestion_execution_examples_v1`


## 21. Examples

- Metadata-only public paper execution packet
- Bounded excerpt public research packet
- Official standard metadata-only packet
- GitHub repository metadata packet
- Owner-uploaded file no raw retention packet
- Blocked ".weslr" source
- Blocked secret/token source
- Blocked missing provenance source
- Blocked final-answer request

## 22. Validation Expectations

- Future validator must fail closed on:
  - Missing authorization packet ref
  - Invalid execution mode
  - Invalid retention mode
  - Raw retention without authorization
  - Content present in metadata-only mode
  - Missing provenance
  - ".weslr"
  - Secrets/tokens/credentials
  - Hidden prompt/private memory
  - Accepted evidence/candidate wording
  - Final answer wording
  - Proof/discovery/public claim wording
  - True denied authority flags
  - Source dump beyond policy
  - Missing blocked claims
  - Missing abort conditions
  - Missing review requirements

## 23. Recommended Next Lane

- REVIEW_WESLR_CONTROLLED_SOURCE_INGESTION_EXECUTOR_BOUNDARY_V1

## 24. Final Judgment

controlled_source_ingestion_executor_boundary_design_ready_for_review
