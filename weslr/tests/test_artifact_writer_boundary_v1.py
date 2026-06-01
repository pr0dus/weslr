from __future__ import annotations

from dataclasses import asdict
import sys

import pytest

from weslr.artifact_writer_boundary import (
    ArtifactWriteDecision,
    ArtifactWriteDecisionSummary,
    ArtifactWriteRequest,
    ValidationError,
    build_artifact_write_request_v1,
    build_initial_artifact_write_boundary_examples_v1,
    evaluate_artifact_write_boundary_v1,
    summarize_artifact_write_decision_v1,
    to_artifact_write_json_safe_v1,
    validate_artifact_write_decision_v1,
    validate_artifact_write_request_v1,
)
from weslr.code_scaffold_generator import build_initial_code_scaffold_examples_v1


def _find_example(examples, name):
    for item in examples:
        metadata = getattr(item, "safe_metadata", None) or {}
        if getattr(item, "write_decision_id", None) == name or metadata.get("example_name") == name:
            return item
    raise AssertionError(f"missing example {name}")


def _request_map(request):
    return to_artifact_write_json_safe_v1(request)


def _decision_map(decision):
    return to_artifact_write_json_safe_v1(decision)


def test_module_imports_safely():
    import weslr.artifact_writer_boundary as mod

    assert mod.HELPER_TYPE_V1 == "artifact_writer_boundary_v1"
    assert mod.ARTIFACT_WRITE_REQUEST_TYPE_V1 == "artifact_write_request_v1"
    assert mod.ARTIFACT_WRITE_DECISION_TYPE_V1 == "artifact_write_decision_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_write_request():
    scaffold = build_initial_code_scaffold_examples_v1()[0]
    first = build_artifact_write_request_v1(scaffold)
    second = build_artifact_write_request_v1(scaffold)
    assert first == second
    assert isinstance(first, ArtifactWriteRequest)


def test_evaluates_dry_run_request():
    scaffold = build_initial_code_scaffold_examples_v1()[0]
    request = build_artifact_write_request_v1(scaffold)
    decision = evaluate_artifact_write_boundary_v1(request)
    assert decision.decision == "allow_dry_run_only"
    assert decision.artifact_generation_allowed is True
    assert decision.can_generate_packet is True


def test_validates_normal_request():
    request = build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[1])
    assert validate_artifact_write_request_v1(request) is True


def test_validates_normal_decision():
    decision = evaluate_artifact_write_boundary_v1(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[2]))
    assert validate_artifact_write_decision_v1(decision) is True


def test_json_safe_export_works():
    request = build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[3])
    exported = to_artifact_write_json_safe_v1(request)
    assert isinstance(exported, dict)
    assert isinstance(exported["requested_entries"], list)
    assert exported["write_request_id"] == request.write_request_id


def test_summary_includes_decision_and_blocked_reasons_and_capability_preservation():
    decision = evaluate_artifact_write_boundary_v1(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[4]))
    summary = summarize_artifact_write_decision_v1(decision)
    assert isinstance(summary, ArtifactWriteDecisionSummary)
    assert summary.decision == decision.decision
    assert summary.blocked_reasons == decision.blocked_reasons
    assert summary.capability_not_denied is True


def test_initial_examples_exist():
    assert len(build_initial_artifact_write_boundary_examples_v1()) >= 10


@pytest.mark.parametrize(
    "name",
    [
        "wifi_rf_scaffold_dry_run_decision",
        "large_scaffold_chunking_preserved_decision",
        "static_website_sandbox_create_decision",
        "medical_software_boundary_docs_decision",
        "protected_runtime_edit_blocked_decision",
        "env_secret_write_blocked_decision",
        "weslr_state_write_blocked_decision",
        "delete_request_blocked_decision",
        "deployment_request_blocked_decision",
        "safe_config_example_allowed_decision",
    ],
)
def test_named_initial_examples_exist(name):
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), name)
    assert decision.write_decision_id == name or decision.safe_metadata["example_name"] == name


def test_large_scaffold_uses_chunking_not_denial():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "large_scaffold_chunking_preserved_decision")
    assert decision.chunking_required is True
    assert decision.capability_not_denied is True
    assert decision.decision in {"requires_owner_approval", "allow_sandbox_create", "allow_owner_approved_create"}
    assert decision.requested_file_count >= 24


def test_blocked_action_still_preserves_capability():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "protected_runtime_edit_blocked_decision")
    assert decision.decision == "blocked_protected_file"
    assert decision.capability_not_denied is True
    assert decision.safe_alternative_available is True


def test_static_website_sandbox_create_preserves_generation_capability():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "static_website_sandbox_create_decision")
    assert decision.decision in {"allow_sandbox_create", "allow_owner_approved_create"}
    assert decision.artifact_generation_allowed is True
    assert decision.can_generate_packet is True


def test_wifi_rf_dry_run_blocks_covert_diagnosis_and_deploy_but_preserves_scaffold():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "wifi_rf_scaffold_dry_run_decision")
    blob = " ".join(decision.blocked_reasons).lower()
    assert "covert" in blob or "diagnosis" in blob or "deployment" in blob
    assert decision.decision == "allow_dry_run_only"
    assert decision.artifact_generation_allowed is True


def test_medical_software_allows_boundary_docs_dry_run_and_blocks_diagnosis_implementation():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "medical_software_boundary_docs_decision")
    assert decision.decision == "allow_dry_run_only"
    assert decision.artifact_generation_allowed is True
    assert any("diagnosis" in reason for reason in decision.blocked_reasons)


def test_protected_runtime_edit_is_blocked():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "protected_runtime_edit_blocked_decision")
    assert decision.decision == "blocked_protected_file"
    assert decision.blocked_entries


def test_env_secret_write_is_blocked():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "env_secret_write_blocked_decision")
    assert decision.decision in {"blocked_protected_file", "blocked_secret_or_private_data"}
    assert decision.blocked_entries


def test_weslr_state_write_is_blocked():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "weslr_state_write_blocked_decision")
    assert decision.decision in {"blocked_path_violation", "blocked_protected_file"}


def test_delete_request_is_blocked():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "delete_request_blocked_decision")
    assert decision.decision == "blocked_unknown"
    assert decision.blocked_reasons


def test_deployment_request_is_blocked():
    decision = _find_example(build_initial_artifact_write_boundary_examples_v1(), "deployment_request_blocked_decision")
    assert decision.decision == "blocked_deployment"


def test_public_publish_request_is_blocked():
    request = build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0], public_publish_requested=True)
    decision = evaluate_artifact_write_boundary_v1(request)
    assert decision.decision == "blocked_public_publish"


def test_dependency_install_request_is_blocked():
    request = build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0], dependency_install_requested=True)
    decision = evaluate_artifact_write_boundary_v1(request)
    assert decision.decision == "blocked_dependency_install"


@pytest.mark.parametrize(
    "field_name",
    [
        "public_claim_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "learning_claimed",
    ],
)
def test_no_initial_example_allows_forbidden_request_authority(field_name):
    for request in [build_artifact_write_request_v1(packet) for packet in build_initial_code_scaffold_examples_v1()]:
        assert getattr(request, field_name) is False


@pytest.mark.parametrize(
    "field_name",
    [
        "public_claim_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "learning_claimed",
    ],
)
def test_no_initial_example_allows_forbidden_decision_authority(field_name):
    for decision in build_initial_artifact_write_boundary_examples_v1():
        assert getattr(decision, field_name) is False


@pytest.mark.parametrize(
    "field_name,value,expected_error",
    [
        ("public_claim_allowed", True, "public_claim_allowed_must_be_false"),
        ("runtime_authority", True, "runtime_authority_must_be_false"),
        ("writes_state", True, "writes_state_must_be_false"),
        ("model_provider_used", True, "model_provider_used_must_be_false"),
        ("learning_claimed", True, "learning_claimed_must_be_false"),
    ],
)
def test_request_validation_fails_on_forbidden_true_flags(field_name, value, expected_error):
    request = _request_map(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0]))
    request[field_name] = value
    with pytest.raises(ValidationError, match=expected_error):
        validate_artifact_write_request_v1(request)


@pytest.mark.parametrize(
    "field_name,value,expected_error",
    [
        ("deployment_allowed", True, "deployment_allowed_must_be_false"),
        ("public_publish_allowed", True, "public_publish_allowed_must_be_false"),
        ("dependency_install_allowed", True, "dependency_install_allowed_must_be_false"),
        ("file_delete_allowed", True, "file_delete_allowed_must_be_false"),
        ("runtime_authority", True, "runtime_authority_must_be_false"),
        ("writes_state", True, "writes_state_must_be_false"),
        ("model_provider_used", True, "model_provider_used_must_be_false"),
        ("learning_claimed", True, "learning_claimed_must_be_false"),
        ("public_claim_allowed", True, "public_claim_allowed_must_be_false"),
    ],
)
def test_decision_validation_fails_on_forbidden_true_flags(field_name, value, expected_error):
    decision = _decision_map(build_initial_artifact_write_boundary_examples_v1()[0])
    decision[field_name] = value
    with pytest.raises(ValidationError, match=expected_error):
        validate_artifact_write_decision_v1(decision)


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("raw_prompt", "secret prompt"),
        ("raw_answer", "secret answer"),
        ("transcript", "secret transcript"),
        ("hidden_prompt", "secret hidden prompt"),
        ("private_data", "secret private data"),
    ],
)
def test_request_validation_fails_on_raw_or_private_fields(field_name, value):
    request = _request_map(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0]))
    request[field_name] = value
    with pytest.raises(ValidationError):
        validate_artifact_write_request_v1(request)


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("raw_prompt", "secret prompt"),
        ("raw_answer", "secret answer"),
        ("transcript", "secret transcript"),
        ("hidden_prompt", "secret hidden prompt"),
        ("private_data", "secret private data"),
    ],
)
def test_decision_validation_fails_on_raw_or_private_fields(field_name, value):
    decision = _decision_map(build_initial_artifact_write_boundary_examples_v1()[0])
    decision[field_name] = value
    with pytest.raises(ValidationError):
        validate_artifact_write_decision_v1(decision)


@pytest.mark.parametrize(
    "bad_text",
    [
        "public ISS wording",
        "AGI claim",
        "consciousness claim",
        "sentience claim",
        "Turing test claim",
        "certification claim",
    ],
)
def test_request_validation_fails_on_public_iss_or_claim_markers(bad_text):
    request = _request_map(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0]))
    request["safe_metadata"] = {"notes": bad_text}
    with pytest.raises(ValidationError):
        validate_artifact_write_request_v1(request)


@pytest.mark.parametrize(
    "bad_text",
    [
        "public ISS wording",
        "AGI claim",
        "consciousness claim",
        "sentience claim",
        "Turing test claim",
        "certification claim",
    ],
)
def test_decision_validation_fails_on_public_iss_or_claim_markers(bad_text):
    decision = _decision_map(build_initial_artifact_write_boundary_examples_v1()[0])
    decision["safe_metadata"] = {"notes": bad_text}
    with pytest.raises(ValidationError):
        validate_artifact_write_decision_v1(decision)


def test_request_validation_fails_on_unknown_write_mode():
    request = _request_map(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0]))
    request["write_mode"] = "mystery_mode"
    with pytest.raises(ValidationError, match="unknown_write_mode"):
        validate_artifact_write_request_v1(request)


def test_decision_validation_fails_on_unknown_write_mode():
    decision = _decision_map(build_initial_artifact_write_boundary_examples_v1()[0])
    decision["effective_write_mode"] = "mystery_mode"
    with pytest.raises(ValidationError, match="unknown_write_mode"):
        validate_artifact_write_decision_v1(decision)


def test_request_validation_fails_on_unknown_capability_class():
    request = _request_map(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0]))
    request["capability_class"] = "mystery_capability"
    with pytest.raises(ValidationError, match="unknown_capability_class"):
        validate_artifact_write_request_v1(request)


def test_decision_validation_fails_on_unknown_capability_class():
    decision = _decision_map(build_initial_artifact_write_boundary_examples_v1()[0])
    decision["capability_class"] = "mystery_capability"
    with pytest.raises(ValidationError, match="unknown_capability_class"):
        validate_artifact_write_decision_v1(decision)


def test_request_validation_fails_on_protected_path():
    request = _request_map(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0]))
    request["requested_entries"][0]["path"] = "weslr/chat_responder.py"
    with pytest.raises(ValidationError, match="protected_path_allowed"):
        validate_artifact_write_request_v1(request)


def test_request_validation_fails_on_secret_path():
    request = _request_map(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0]))
    request["requested_entries"][0]["path"] = ".env"
    with pytest.raises(ValidationError, match="protected_path_allowed"):
        validate_artifact_write_request_v1(request)


def test_request_validation_fails_on_absolute_or_traversal_paths():
    request = _request_map(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0]))
    request["requested_entries"][0]["path"] = "/etc/passwd"
    with pytest.raises(ValidationError, match="unsafe_entry_path"):
        validate_artifact_write_request_v1(request)
    request = _request_map(build_artifact_write_request_v1(build_initial_code_scaffold_examples_v1()[0]))
    request["requested_entries"][0]["path"] = "../escape.py"
    with pytest.raises(ValidationError, match="unsafe_entry_path"):
        validate_artifact_write_request_v1(request)


def test_decision_validation_fails_on_protected_or_secret_allowed_paths():
    decision = _decision_map(build_initial_artifact_write_boundary_examples_v1()[0])
    decision["allowed_entries"] = [{"path": "weslr/chat_responder.py", "file_type": "python", "content_kind": "python_module_template", "generation_method": "validated_template", "owner_approval_required": True}]
    with pytest.raises(ValidationError, match="protected_path_allowed"):
        validate_artifact_write_decision_v1(decision)
    decision = _decision_map(build_initial_artifact_write_boundary_examples_v1()[0])
    decision["allowed_entries"] = [{"path": ".env", "file_type": "yaml", "content_kind": "yaml_template", "generation_method": "validated_template", "owner_approval_required": True}]
    with pytest.raises(ValidationError, match="protected_path_allowed"):
        validate_artifact_write_decision_v1(decision)


def test_decision_validation_fails_on_raw_request_like_fields():
    decision = _decision_map(build_initial_artifact_write_boundary_examples_v1()[0])
    decision["raw_prompt"] = "secret prompt"
    with pytest.raises(ValidationError):
        validate_artifact_write_decision_v1(decision)


def test_module_does_not_import_or_call_protected_files():
    import weslr.artifact_writer_boundary as mod

    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules
    assert hasattr(mod, "build_artifact_write_request_v1")
    assert hasattr(mod, "evaluate_artifact_write_boundary_v1")
    assert hasattr(mod, "validate_artifact_write_request_v1")
    assert hasattr(mod, "validate_artifact_write_decision_v1")
