from __future__ import annotations

import ast
import inspect
from dataclasses import asdict
from pathlib import Path

import pytest

from weslr.artifact_exporter_boundary import (  # noqa: F401
    ALLOWED_ARTIFACT_EXPORT_NEXT_STEP_CLASSES_V1,
    ALLOWED_ARTIFACT_TARGET_CLASSES_V1,
    ALLOWED_EXPORT_READINESS_STATUSES_V1,
    ALLOWED_EXPORT_REQUEST_CLASSES_V1,
    ArtifactExportPacket,
    ArtifactExportSummary,
    ValidationError,
    build_artifact_export_packet_v1,
    build_initial_artifact_export_examples_v1,
    classify_artifact_export_request_v1,
    classify_artifact_export_target_v1,
    evaluate_artifact_export_readiness_v1,
    select_artifact_export_next_step_v1,
    summarize_artifact_export_packet_v1,
    to_artifact_export_json_safe_v1,
    validate_artifact_export_packet_v1,
)

FORBIDDEN_IMPORT_NAMES = {
    "subprocess",
    "os",
    "pathlib",
    "socket",
    "requests",
    "urllib",
    "http",
    "shutil",
}

FORBIDDEN_CALL_NAMES = {
    "open",
    "exec",
    "eval",
    "system",
    "popen",
    "run",
    "call",
    "check_call",
    "check_output",
    "communicate",
    "read_text",
    "write_text",
    "read_bytes",
    "write_bytes",
}


def _packet(**overrides):
    payload = dict(
        artifact_export_packet_id="artifact_export_base_v1",
        export_request_class="report_export_request",
        artifact_target_class="markdown_document",
        artifact_ref="artifact_ref_base_v1",
        artifact_summary="Metadata-only artifact export candidate.",
        artifact_provenance_ref="artifact_provenance_base_v1",
        document_access_packet_ref="",
        claim_grounding_packet_ref="",
        source_evidence_graph_ref="",
        validation_packet_ref="",
        owner_operator_workflow_packet_ref="",
        action_authority_packet_ref="",
        rollback_packet_ref="",
        export_readiness_status="candidate_ready_for_owner_review",
        export_next_step="request_owner_review",
        export_scope_summary="Metadata-only review; no export execution.",
        destination_summary="internal review only",
        owner_review_required=True,
        operator_review_required=False,
        dual_review_required=False,
        validation_required=False,
        provenance_required=True,
        document_access_required=False,
        pii_scrub_required=False,
        secret_review_required=False,
        public_claim_review_required=False,
        rollback_or_retraction_required=False,
        privacy_status="clear",
        pii_risk_status="clear",
        secret_risk_status="clear",
        poison_status="clear",
        public_effect_possible=False,
        external_side_effect_possible=False,
        marketplace_effect_possible=False,
        download_allowed=False,
        local_save_allowed=False,
        share_allowed=False,
        email_attachment_allowed=False,
        public_publish_allowed=False,
        deployment_artifact_allowed=False,
        marketplace_publish_allowed=False,
        export_execution_allowed=False,
        recommended_next_check="request_owner_review",
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        learning_claimed=False,
        safe_metadata={"example_name": "base"},
    )
    payload.update(overrides)
    return build_artifact_export_packet_v1(**payload)


def _raw_packet(**overrides):
    payload = asdict(_packet())
    payload.update(overrides)
    return ArtifactExportPacket(**payload)


def _example_by_id(packet_id: str):
    for item in build_initial_artifact_export_examples_v1():
        if item.artifact_export_packet_id == packet_id:
            return item
    raise AssertionError(f"missing example: {packet_id}")


def test_module_imports_safely():
    import weslr.artifact_exporter_boundary as mod

    assert mod.HELPER_TYPE_V1 == "artifact_exporter_boundary_v1"
    assert inspect.getmodule(mod).__name__ == "weslr.artifact_exporter_boundary"


def test_public_apis_are_available_and_deterministic():
    packet = _packet()
    assert isinstance(packet, ArtifactExportPacket)
    assert isinstance(summarize_artifact_export_packet_v1(packet), ArtifactExportSummary)
    assert evaluate_artifact_export_readiness_v1(packet) == packet
    assert classify_artifact_export_request_v1(export_request_class="owner_handoff_request") == "owner_handoff_request"
    assert classify_artifact_export_target_v1(artifact_target_class="pdf_document") == "pdf_document"
    assert select_artifact_export_next_step_v1(packet) == "request_owner_review"


def test_request_and_target_classification_fails_closed():
    assert classify_artifact_export_request_v1(request_summary="please publish this") == "public_publish_request"
    assert classify_artifact_export_request_v1(request_summary="unknown request") == "unknown_export_request"
    assert classify_artifact_export_request_v1(export_request_class="not_real") == "unknown_export_request"
    assert classify_artifact_export_target_v1(artifact_summary="markdown report") == "markdown_document"
    assert classify_artifact_export_target_v1(artifact_summary="unknown target") == "unknown_artifact_target"
    assert classify_artifact_export_target_v1(artifact_target_class="not_real") == "unknown_artifact_target"


def test_json_safe_conversion_does_not_mutate_input():
    value = {
        "z": {"b": 2, "a": [1, {"c": 3}]},
        "a": {"nested": {"k": "v"}},
    }
    snapshot = asdict(_packet())
    original = {"value": value, "packet": snapshot}
    before = repr(original)
    safe = to_artifact_export_json_safe_v1(original)
    after = repr(original)
    assert before == after
    assert safe["value"]["z"]["a"][1]["c"] == 3
    assert safe["packet"]["artifact_ref"] == "artifact_ref_base_v1"


def test_summary_contains_no_raw_private_or_secret_fields():
    summary = summarize_artifact_export_packet_v1(_packet())
    summary_dict = asdict(summary)
    assert "raw_private" not in summary_dict
    assert "secret_token" not in summary_dict
    assert "password" not in summary_dict
    assert "raw_private" not in repr(summary)
    assert "secret_token" not in repr(summary)


@pytest.mark.parametrize(
    "example_id, should_validate",
    [
        ("metadata_only_markdown_report_candidate_v1", True),
        ("local_save_blocked_v1", True),
        ("owner_handoff_requires_provenance_v1", True),
        ("email_attachment_requires_action_authority_v1", False),
        ("public_publish_requires_review_and_retraction_v1", True),
        ("deployment_artifact_requires_validation_and_rollback_v1", True),
        ("code_patch_export_requires_validation_and_provenance_v1", True),
        ("legal_document_requires_owner_and_privacy_review_v1", True),
        ("dataset_export_requires_pii_scrub_and_document_access_v1", True),
        ("memory_export_blocked_v1", False),
        ("image_asset_requires_provenance_and_rights_summary_v1", True),
        ("configuration_file_requires_validation_and_secret_review_v1", True),
        ("artifact_marketplace_blocked_v1", False),
        ("poison_risk_artifact_blocked_v1", False),
        ("unknown_target_request_fails_closed_v1", False),
    ],
)
def test_initial_examples_validate_or_fail_as_expected(example_id: str, should_validate: bool):
    packet = _example_by_id(example_id)
    if should_validate:
        assert validate_artifact_export_packet_v1(packet) is True
    else:
        with pytest.raises(ValidationError):
            validate_artifact_export_packet_v1(packet)


def test_initial_examples_count_is_15():
    assert len(build_initial_artifact_export_examples_v1()) == 15


def test_unknown_request_and_target_fail_closed():
    packet = _raw_packet(
        export_request_class="unknown_export_request",
        artifact_target_class="unknown_artifact_target",
        export_readiness_status="blocked_unknown_request",
        export_next_step="blocked_no_safe_export",
    )
    with pytest.raises(ValidationError, match="unknown_request_promoted_as_valid"):
        validate_artifact_export_packet_v1(packet)


def test_unknown_readiness_and_next_step_fail_closed():
    packet = _raw_packet(export_readiness_status="unknown_status", export_next_step="unknown_next_step")
    with pytest.raises(ValidationError, match="unknown_status_promoted_as_valid"):
        validate_artifact_export_packet_v1(packet)


def test_export_flags_cannot_be_true():
    for field_name in (
        "download_allowed",
        "local_save_allowed",
        "share_allowed",
        "email_attachment_allowed",
        "public_publish_allowed",
        "deployment_artifact_allowed",
        "marketplace_publish_allowed",
        "export_execution_allowed",
    ):
        packet = _raw_packet(**{field_name: True})
        with pytest.raises(ValidationError, match=f"{field_name}_must_be_false"):
            validate_artifact_export_packet_v1(packet)


def test_runtime_write_model_public_proof_learning_flags_cannot_be_true():
    for field_name in (
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "proof_claim_allowed",
        "learning_claimed",
    ):
        packet = _raw_packet(**{field_name: True})
        with pytest.raises(ValidationError, match=f"{field_name}_must_be_false"):
            validate_artifact_export_packet_v1(packet)


def test_public_publish_requires_public_claim_review_and_rollback_plan():
    packet = _raw_packet(
        export_request_class="public_publish_request",
        artifact_target_class="public_website_asset",
        public_effect_possible=True,
        rollback_or_retraction_required=False,
        public_claim_review_required=False,
        claim_grounding_packet_ref="",
        rollback_packet_ref="",
        export_readiness_status="blocked_missing_rollback_or_retraction",
        export_next_step="request_rollback_or_retraction_plan",
    )
    with pytest.raises(ValidationError, match="public_export_without_public_claim_review"):
        validate_artifact_export_packet_v1(packet)


def test_deployment_code_and_config_require_validation():
    packet = _raw_packet(
        export_request_class="deployment_artifact_request",
        artifact_target_class="configuration_file",
        validation_required=True,
        validation_packet_ref="",
        export_readiness_status="blocked_missing_validation",
        export_next_step="request_validation_packet",
    )
    with pytest.raises(ValidationError, match="missing_validation_when_required"):
        validate_artifact_export_packet_v1(packet)


def test_dataset_memory_and_legal_exports_require_document_access_and_privacy_review():
    dataset_packet = _raw_packet(
        export_request_class="dataset_export_request",
        artifact_target_class="dataset_artifact",
        document_access_required=True,
        pii_scrub_required=True,
        document_access_packet_ref="",
        export_readiness_status="blocked_missing_access_packet",
        export_next_step="request_document_access_packet",
    )
    with pytest.raises(ValidationError, match="missing_document_access_when_required"):
        validate_artifact_export_packet_v1(dataset_packet)

    memory_packet = _raw_packet(
        export_request_class="memory_export_request",
        artifact_target_class="json_metadata",
        document_access_required=True,
        pii_scrub_required=True,
        privacy_status="blocked",
        pii_risk_status="blocked",
        document_access_packet_ref="",
        export_readiness_status="blocked_missing_access_packet",
        export_next_step="request_document_access_packet",
    )
    with pytest.raises(ValidationError, match="missing_document_access_when_required"):
        validate_artifact_export_packet_v1(memory_packet)

    legal_packet = _raw_packet(
        export_request_class="legal_document_export_request",
        artifact_target_class="legal_or_policy_artifact",
        document_access_required=True,
        pii_scrub_required=True,
        privacy_status="blocked",
        pii_risk_status="blocked",
        document_access_packet_ref="document_access_v1",
        export_readiness_status="blocked_pii_or_privacy_risk",
        export_next_step="request_pii_scrub",
    )
    with pytest.raises(ValidationError, match="private_or_pii_risk_blocks_export_progression"):
        validate_artifact_export_packet_v1(legal_packet)


def test_secret_and_poison_risks_block_export_progression():
    secret_packet = _raw_packet(secret_risk_status="blocked", export_readiness_status="blocked_secret_risk", export_next_step="request_secret_review")
    with pytest.raises(ValidationError, match="secret_risk_must_be_clear_for_export_progression"):
        validate_artifact_export_packet_v1(secret_packet)

    poison_packet = _raw_packet(poison_status="poisoned", export_readiness_status="blocked_poison_risk", export_next_step="blocked_no_safe_export")
    with pytest.raises(ValidationError, match="poison_risk_blocks_export_progression"):
        validate_artifact_export_packet_v1(poison_packet)


def test_owner_operator_action_authority_metadata_does_not_execute_export():
    packet = _raw_packet(
        owner_operator_workflow_packet_ref="workflow_v1",
        action_authority_packet_ref="authority_v1",
        export_execution_allowed=False,
    )
    assert validate_artifact_export_packet_v1(packet) is True
    assert packet.export_execution_allowed is False


def test_hidden_prompt_raw_private_secret_like_fields_fail_closed():
    payload = asdict(_packet())
    payload["safe_metadata"] = {"raw_private_blob": "x", "nested": {"hidden_prompt_note": "y"}}
    packet = ArtifactExportPacket(**payload)
    with pytest.raises(ValidationError, match="hidden_private_or_secret_like_fields_not_allowed"):
        validate_artifact_export_packet_v1(packet)


def test_no_subprocess_shell_api_or_file_io_exists_in_helper_implementation():
    import weslr.artifact_exporter_boundary as mod

    source = Path(mod.__file__).read_text()
    tree = ast.parse(source)
    imports = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) and node.names}
    assert not (imports & FORBIDDEN_IMPORT_NAMES)

    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                calls.add(fn.id)
            elif isinstance(fn, ast.Attribute):
                calls.add(fn.attr)
    assert not (calls & FORBIDDEN_CALL_NAMES)
