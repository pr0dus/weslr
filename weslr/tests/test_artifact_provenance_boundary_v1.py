from __future__ import annotations

import sys

import pytest

from weslr.artifact_provenance_boundary import (
    ArtifactProvenanceBundle,
    ArtifactProvenanceRecord,
    ArtifactProvenanceSummary,
    ValidationError,
    build_artifact_provenance_bundle_v1,
    build_artifact_provenance_record_v1,
    build_initial_artifact_provenance_examples_v1,
    summarize_artifact_provenance_bundle_v1,
    to_artifact_provenance_json_safe_v1,
    validate_artifact_provenance_bundle_v1,
    validate_artifact_provenance_record_v1,
)


BASE_RECORD_KWARGS = dict(
    provenance_record_id="base_record_v1",
    artifact_path="docs/example.md",
    artifact_type="markdown",
    content_hash="sha256:placeholder-base-v1",
    hash_algorithm="sha256",
    source_project_brief_id="project_brief_base_v1",
    source_architecture_id="architecture_base_v1",
    source_stack_decision_id="stack_base_v1",
    source_manifest_id="manifest_base_v1",
    source_scaffold_id="scaffold_base_v1",
    source_write_request_id="write_request_base_v1",
    source_write_decision_id="write_decision_base_v1",
    source_write_result_id="write_result_base_v1",
    owner_approval_id="no_owner_approval_v1",
    operator_approval_id="no_operator_approval_v1",
    validation_report_id="validation_report_base_v1",
    created_timestamp="2026-06-01T20:40:00+02:00",
    modified_timestamp="2026-06-01T20:40:00+02:00",
    generator_type="deterministic_template",
    model_provider_used=False,
    provider_trace_id="none",
    authority_level_used="none",
    sandbox_root="sandbox/base",
    write_mode="dry_run",
    tamper_evidence_status="not_yet_hashed",
    verification_status="verification_not_run",
    public_claim_allowed=False,
    runtime_authority=False,
    writes_state=False,
    safe_metadata={"example_name": "base_record_v1"},
)


def _example_by_name(name: str):
    for item in build_initial_artifact_provenance_examples_v1():
        payload = to_artifact_provenance_json_safe_v1(item)
        if payload["provenance_record_id"] == name or (payload.get("safe_metadata") or {}).get("example_name") == name:
            return item
    raise AssertionError(f"missing example: {name}")


def test_module_imports_safely():
    import weslr.artifact_provenance_boundary as mod

    assert mod.HELPER_TYPE_V1 == "artifact_provenance_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_provenance_record():
    first = build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS)
    second = build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS)
    assert first == second
    assert isinstance(first, ArtifactProvenanceRecord)


def test_builds_provenance_bundle():
    records = build_initial_artifact_provenance_examples_v1()[:2]
    bundle = build_artifact_provenance_bundle_v1(provenance_bundle_id="bundle_v1", records=records)
    assert isinstance(bundle, ArtifactProvenanceBundle)
    assert len(bundle.records) == 2


def test_validates_normal_record():
    record = build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS)
    assert validate_artifact_provenance_record_v1(record) is True


def test_validates_normal_bundle():
    records = build_initial_artifact_provenance_examples_v1()[:3]
    bundle = build_artifact_provenance_bundle_v1(provenance_bundle_id="bundle_normal_v1", records=records)
    assert validate_artifact_provenance_bundle_v1(bundle) is True


def test_json_safe_export_works():
    record = build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS)
    payload = to_artifact_provenance_json_safe_v1(record)
    assert isinstance(payload, dict)
    assert payload["provenance_record_id"] == "base_record_v1"


def test_summary_includes_record_count_generator_types_and_tamper_statuses():
    bundle = build_artifact_provenance_bundle_v1(
        provenance_bundle_id="summary_bundle_v1",
        records=build_initial_artifact_provenance_examples_v1(),
    )
    summary = summarize_artifact_provenance_bundle_v1(bundle)
    assert isinstance(summary, ArtifactProvenanceSummary)
    assert summary.record_count == 7
    assert "llm_candidate" in summary.generator_types
    assert "hash_mismatch" in summary.tamper_evidence_statuses


def test_all_initial_examples_exist():
    names = {to_artifact_provenance_json_safe_v1(item)["provenance_record_id"] for item in build_initial_artifact_provenance_examples_v1()}
    assert names == {
        "static_website_scaffold_provenance",
        "wifi_rf_self_care_scaffold_provenance",
        "medical_software_boundary_docs_provenance",
        "ai_system_research_scaffold_provenance",
        "hash_mismatch_example",
        "llm_candidate_provenance_example",
        "owner_manual_edit_provenance_example",
    }


def test_static_website_example_has_scaffold_write_lineage():
    record = _example_by_name("static_website_scaffold_provenance")
    payload = to_artifact_provenance_json_safe_v1(record)
    assert payload["source_scaffold_id"]
    assert payload["source_write_result_id"]
    assert payload["tamper_evidence_status"] in {"hash_recorded", "not_yet_hashed", "hash_verified"}


def test_wifi_rf_example_preserves_privacy_sensitive_provenance_without_unsafe_claims():
    payload = to_artifact_provenance_json_safe_v1(_example_by_name("wifi_rf_self_care_scaffold_provenance"))
    blob = str(payload).lower()
    assert payload["public_claim_allowed"] is False
    assert payload["safe_metadata"]["privacy_sensitive"] is True
    assert "agi" not in blob
    assert "consciousness" not in blob
    assert "sentience" not in blob
    assert "turing" not in blob
    assert "certification" not in blob


def test_medical_example_has_boundary_doc_provenance_and_no_diagnosis_or_treatment_claim():
    payload = to_artifact_provenance_json_safe_v1(_example_by_name("medical_software_boundary_docs_provenance"))
    assert payload["artifact_path"] == "docs/MEDICAL_BOUNDARY.md"
    assert "diagnosis" not in str(payload).lower()
    assert "treatment" not in str(payload).lower()


def test_ai_system_example_has_no_agi_or_certification_claim():
    payload = to_artifact_provenance_json_safe_v1(_example_by_name("ai_system_research_scaffold_provenance"))
    assert "agi" not in str(payload).lower()
    assert "certification" not in str(payload).lower()
    assert payload["public_claim_allowed"] is False


def test_hash_mismatch_example_validates_as_mismatch_status_but_not_public_claim():
    record = _example_by_name("hash_mismatch_example")
    payload = to_artifact_provenance_json_safe_v1(record)
    assert payload["tamper_evidence_status"] == "hash_mismatch"
    assert payload["public_claim_allowed"] is False
    assert validate_artifact_provenance_record_v1(record) is True


def test_llm_candidate_example_records_provider_use_but_no_authority_grant():
    payload = to_artifact_provenance_json_safe_v1(_example_by_name("llm_candidate_provenance_example"))
    assert payload["model_provider_used"] is True
    assert payload["authority_level_used"] == "candidate_only"


def test_owner_manual_edit_example_records_owner_supplied_manual_lineage():
    payload = to_artifact_provenance_json_safe_v1(_example_by_name("owner_manual_edit_provenance_example"))
    assert payload["generator_type"] == "owner_supplied"
    assert payload["safe_metadata"]["edit_source"] == "owner"


@pytest.mark.parametrize(
    "field_name,value,expected_error",
    [
        ("generator_type", "mystery_generator", "unknown_generator_type"),
        ("tamper_evidence_status", "mystery_status", "unknown_tamper_evidence_status"),
    ],
)
def test_validation_fails_on_unknown_generator_or_tamper_status(field_name, value, expected_error):
    payload = to_artifact_provenance_json_safe_v1(build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS))
    payload[field_name] = value
    with pytest.raises(ValidationError, match=expected_error):
        validate_artifact_provenance_record_v1(payload)


@pytest.mark.parametrize(
    "field_name,value,expected_error",
    [
        ("public_claim_allowed", True, "public_claim_allowed_must_be_false"),
        ("runtime_authority", True, "runtime_authority_must_be_false"),
        ("writes_state", True, "writes_state_must_be_false"),
    ],
)
def test_validation_fails_on_forbidden_true_flags(field_name, value, expected_error):
    payload = to_artifact_provenance_json_safe_v1(build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS))
    payload[field_name] = value
    with pytest.raises(ValidationError, match=expected_error):
        validate_artifact_provenance_record_v1(payload)


@pytest.mark.parametrize(
    "field_name,value,expected_error",
    [
        ("hidden_prompt", "secret hidden prompt", "forbidden_field_detected"),
        ("raw_private_content", "secret raw private content", "forbidden_field_detected"),
        ("secret_token", "tok_123", "forbidden_field_detected"),
    ],
)
def test_validation_fails_on_hidden_or_private_or_secret_fields(field_name, value, expected_error):
    payload = to_artifact_provenance_json_safe_v1(build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS))
    payload[field_name] = value
    with pytest.raises(ValidationError, match=expected_error):
        validate_artifact_provenance_record_v1(payload)


@pytest.mark.parametrize(
    "notes,expected_error",
    [
        ("official validation and certification claim", "forbidden_claim_marker_detected"),
        ("AGI consciousness sentience Turing certification", "forbidden_claim_marker_detected"),
        ("production safety claim", "forbidden_claim_marker_detected"),
    ],
)
def test_validation_fails_on_official_or_agency_claim_markers(notes, expected_error):
    payload = to_artifact_provenance_json_safe_v1(build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS))
    payload["safe_metadata"] = {"notes": notes}
    with pytest.raises(ValidationError, match=expected_error):
        validate_artifact_provenance_record_v1(payload)


def test_validation_fails_when_provider_output_grants_authority():
    payload = to_artifact_provenance_json_safe_v1(build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS))
    payload["model_provider_used"] = True
    payload["provider_trace_id"] = "provider-trace-1"
    payload["authority_level_used"] = "provider_grants_write_authority"
    with pytest.raises(ValidationError, match="unknown_authority_level_used|provider_must_not_grant_authority"):
        validate_artifact_provenance_record_v1(payload)


def test_validation_fails_when_approval_is_treated_as_validation():
    payload = to_artifact_provenance_json_safe_v1(build_artifact_provenance_record_v1(**BASE_RECORD_KWARGS))
    payload["validation_report_id"] = payload["owner_approval_id"]
    with pytest.raises(ValidationError, match="approval_treated_as_validation"):
        validate_artifact_provenance_record_v1(payload)


def test_module_does_not_import_or_call_protected_files():
    import weslr.artifact_provenance_boundary as mod

    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules
    assert hasattr(mod, "build_artifact_provenance_record_v1")
    assert hasattr(mod, "build_artifact_provenance_bundle_v1")
    assert hasattr(mod, "validate_artifact_provenance_record_v1")
    assert hasattr(mod, "validate_artifact_provenance_bundle_v1")
