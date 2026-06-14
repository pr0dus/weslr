from __future__ import annotations

import json
from copy import deepcopy

import weslr.source_ingestion_authorization_boundary as boundary
from weslr.source_ingestion_authorization_boundary import (
    build_initial_source_ingestion_authorization_examples_v1,
    build_source_ingestion_authorization_packet_v1,
    render_source_ingestion_authorization_markdown_v1,
    summarize_source_ingestion_authorization_packet_v1,
    to_source_ingestion_authorization_json_safe_v1,
    validate_source_ingestion_authorization_packet_v1,
)


def _public_research() -> dict:
    return build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="public_research_paper_metadata_only",
        requested_by="owner",
        source_ref="https://example.org/paper.pdf",
        source_class="public_research_paper",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        ingestion_purpose="source_metadata_extraction",
        artifact_target="interpretation_packet",
        evidence_role_target="source_selection_reference",
        retention_mode="metadata_only_no_content_retention",
        owner_authorization_required=False,
        owner_authorization_present=False,
        operator_review_required=True,
        expert_review_required=False,
        blocked_claims=("no_authority_escalation", "no_review_gate_break"),
        abort_conditions=("no review gate break", "no accepted evidence"),
        final_judgment="authorization_packet_pending_review",
    )


def _official_standard() -> dict:
    return build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="official_standard_metadata_only",
        requested_by="owner",
        source_ref="https://example.org/standard",
        source_class="official_standard",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        ingestion_purpose="claim_boundary_mapping",
        artifact_target="interpretation_packet",
        evidence_role_target="method_limit_source",
        retention_mode="metadata_only_no_content_retention",
        operator_review_required=True,
        blocked_claims=("no_review_gate_break",),
        abort_conditions=("no review gate break",),
        final_judgment="authorization_packet_pending_review",
    )


def _github_repo() -> dict:
    return build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="github_repo_implementation_reference",
        requested_by="owner",
        source_ref="https://github.com/example/repo",
        source_class="github_repository",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        ingestion_purpose="implementation_reference_mapping",
        artifact_target="interpretation_packet",
        evidence_role_target="implementation_reference",
        retention_mode="derived_summary_only",
        operator_review_required=True,
        blocked_claims=("no_candidate_promotion",),
        abort_conditions=("candidate promotion blocked",),
        final_judgment="authorization_packet_pending_review",
    )


def _owner_uploaded() -> dict:
    return build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="owner_uploaded_file_no_raw_retention",
        requested_by="owner",
        source_ref="file:///authorized/upload.pdf",
        source_class="owner_uploaded_file",
        source_access_level="owner_uploaded",
        license_access_posture="owner_authorized_private",
        privacy_posture="owner_authorized_private",
        ingestion_purpose="evidence_candidate_extraction",
        artifact_target="interpretation_packet",
        evidence_role_target="primary_evidence_candidate",
        retention_mode="full_text_transient_no_retention",
        owner_authorization_required=True,
        owner_authorization_present=True,
        raw_retention_allowed=False,
        derived_metadata_allowed=True,
        quoted_excerpt_allowed=True,
        operator_review_required=True,
        blocked_claims=("no_review_gate_break",),
        abort_conditions=("no review gate break",),
        final_judgment="authorization_packet_pending_review",
    )


def test_public_apis_exist():
    for name in (
        "build_source_ingestion_authorization_packet_v1",
        "validate_source_ingestion_authorization_packet_v1",
        "summarize_source_ingestion_authorization_packet_v1",
        "render_source_ingestion_authorization_markdown_v1",
        "to_source_ingestion_authorization_json_safe_v1",
        "build_initial_source_ingestion_authorization_examples_v1",
    ):
        assert hasattr(boundary, name)
        assert callable(getattr(boundary, name))


def test_valid_public_research_paper_authorization():
    packet = _public_research()
    validation = validate_source_ingestion_authorization_packet_v1(packet)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert packet["source_class"] == "public_research_paper"
    assert packet["owner_authorization_required"] is False
    assert packet["operator_review_required"] is True


def test_valid_official_standard_authorization():
    packet = _official_standard()
    assert validate_source_ingestion_authorization_packet_v1(packet)["valid"] is True
    assert packet["source_class"] == "official_standard"


def test_valid_github_implementation_reference_authorization():
    packet = _github_repo()
    assert validate_source_ingestion_authorization_packet_v1(packet)["valid"] is True
    assert packet["evidence_role_target"] == "implementation_reference"


def test_valid_owner_uploaded_file_authorization_with_no_raw_retention():
    packet = _owner_uploaded()
    validation = validate_source_ingestion_authorization_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["raw_retention_allowed"] is False
    assert packet["owner_authorization_present"] is True


def test_required_fields_validation():
    packet = _public_research()
    del packet["final_judgment"]
    validation = validate_source_ingestion_authorization_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("missing_field:final_judgment") for label in validation["blocked_labels"])


def test_unknown_source_class_without_owner_authorization_rejected():
    packet = _public_research()
    packet["source_class"] = "unknown_source_class"
    packet["owner_authorization_present"] = False
    assert validate_source_ingestion_authorization_packet_v1(packet)["blocked"] is True


def test_blocked_source_class_rejected():
    packet = _public_research()
    packet["source_class"] = "blocked_source_class"
    assert validate_source_ingestion_authorization_packet_v1(packet)["blocked"] is True


def test_unknown_restricted_license_without_authorization_rejected():
    packet = _public_research()
    packet["license_access_posture"] = "restricted_or_paid"
    packet["owner_authorization_present"] = False
    assert validate_source_ingestion_authorization_packet_v1(packet)["blocked"] is True


def test_private_sensitive_privacy_posture_without_authorization_rejected():
    packet = _public_research()
    packet["privacy_posture"] = "contains_sensitive_data"
    packet["owner_authorization_present"] = False
    assert validate_source_ingestion_authorization_packet_v1(packet)["blocked"] is True


def test_weslr_rejected():
    packet = _public_research()
    packet["source_ref"] = ".weslr/private/source"
    assert "weslr_reference_blocked" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_hidden_prompt_private_memory_wording_rejected():
    packet = _public_research()
    packet["safe_metadata_summary"] = "hidden prompt and private memory"
    assert "sensitive_content_wording_present" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_credentials_secrets_tokens_rejected():
    packet = _public_research()
    packet["abort_conditions"] = ["credential", "secret", "token"]
    assert "sensitive_content_wording_present" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_final_answer_wording_rejected():
    packet = _public_research()
    packet["blocked_claims"] = ["final answer authority"]
    assert "forbidden_claim_wording_present" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_accepted_evidence_candidate_wording_rejected():
    packet = _public_research()
    packet["blocked_claims"] = ["accepted evidence authority", "accepted candidate authority"]
    assert "forbidden_claim_wording_present" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_proof_discovery_public_science_product_processediness_rejected():
    packet = _public_research()
    packet["blocked_claims"] = ["proof", "confirmed discovery", "public science claim", "product processedy"]
    assert "forbidden_claim_wording_present" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_autonomous_crawling_rejected():
    packet = _public_research()
    packet["denied_authority_flags"]["autonomous_crawling_authority"] = True
    labels = validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]
    assert any(label.startswith("denied_authority_true:autonomous_crawling_authority") for label in labels)


def test_provider_model_runtime_authority_rejected():
    packet = _public_research()
    packet["denied_authority_flags"]["provider_model_call_authority"] = True
    packet["denied_authority_flags"]["runtime_wiring_authority"] = True
    labels = validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]
    assert any(label.startswith("denied_authority_true:provider_model_call_authority") for label in labels)
    assert any(label.startswith("denied_authority_true:runtime_wiring_authority") for label in labels)


def test_memory_database_mutation_rejected():
    packet = _public_research()
    packet["denied_authority_flags"]["memory_mutation_authority"] = True
    packet["denied_authority_flags"]["database_write_authority"] = True
    labels = validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]
    assert any(label.startswith("denied_authority_true:memory_mutation_authority") for label in labels)
    assert any(label.startswith("denied_authority_true:database_write_authority") for label in labels)


def test_ontology_auto_application_self_modification_rejected():
    packet = _public_research()
    packet["denied_authority_flags"]["ontology_auto_application_authority"] = True
    packet["denied_authority_flags"]["self_modification_authority"] = True
    labels = validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]
    assert any(label.startswith("denied_authority_true:ontology_auto_application_authority") for label in labels)
    assert any(label.startswith("denied_authority_true:self_modification_authority") for label in labels)


def test_any_true_denied_authority_flag_rejected():
    packet = _public_research()
    packet["denied_authority_flags"]["final_answer_authority"] = True
    labels = validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]
    assert any(label.startswith("denied_authority_true:final_answer_authority") for label in labels)


def test_empty_blocked_claims_rejected():
    packet = _public_research()
    packet["blocked_claims"] = []
    assert "blocked_claims_empty" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_empty_abort_conditions_rejected():
    packet = _public_research()
    packet["abort_conditions"] = []
    assert "abort_conditions_empty" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_raw_retention_without_owner_authorization_rejected():
    packet = _public_research()
    packet["raw_retention_allowed"] = True
    packet["retention_mode"] = "full_text_transient_no_retention"
    assert "raw_retention_without_owner_authorization" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_blocked_retention_rejected():
    packet = _public_research()
    packet["retention_mode"] = "blocked_retention"
    assert "blocked_retention_not_allowed" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_unknown_ingestion_purpose_rejected():
    packet = _public_research()
    packet["ingestion_purpose"] = "unknown"
    assert "invalid_ingestion_purpose" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_unknown_evidence_role_rejected():
    packet = _public_research()
    packet["evidence_role_target"] = "unknown"
    assert "invalid_evidence_role_target" in validate_source_ingestion_authorization_packet_v1(packet)["blocked_labels"]


def test_markdown_renderer_safe_and_complete():
    md = render_source_ingestion_authorization_markdown_v1(_public_research())
    assert "Authorization posture" in md
    assert "Blocked claims" in md
    assert "Abort conditions" in md
    assert "Denied authority summary" in md


def test_markdown_renderer_does_not_imply_source_accessed():
    md = render_source_ingestion_authorization_markdown_v1(_public_research()).lower()
    assert "accessed" not in md
    assert "processed" not in md or "source ingestion authorization packet" in md


def test_json_safe_copy_deterministic_and_non_mutating():
    packet = _public_research()
    original = deepcopy(packet)
    first = to_source_ingestion_authorization_json_safe_v1(packet)
    second = to_source_ingestion_authorization_json_safe_v1(packet)
    assert first == second
    assert packet == original
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_summary_compact_and_safe():
    summary = summarize_source_ingestion_authorization_packet_v1(_public_research())
    assert summary["ingestion_request_id"] == "public_research_paper_metadata_only"
    assert summary["source_class"] == "public_research_paper"
    assert summary["blocked"] is False


def test_examples_validate_except_intentionally_unsafe_examples():
    examples = build_initial_source_ingestion_authorization_examples_v1()
    assert validate_source_ingestion_authorization_packet_v1(examples[0])["valid"] is True
    assert validate_source_ingestion_authorization_packet_v1(examples[1])["valid"] is True
    assert validate_source_ingestion_authorization_packet_v1(examples[2])["valid"] is True
    assert validate_source_ingestion_authorization_packet_v1(examples[3])["valid"] is True
    assert validate_source_ingestion_authorization_packet_v1(examples[4])["valid"] is False
    assert validate_source_ingestion_authorization_packet_v1(examples[5])["valid"] is False
