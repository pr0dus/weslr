from __future__ import annotations

from dataclasses import asdict
import sys

import pytest

from weslr.artifact_writer_boundary import (
    ArtifactWriteRequest,
    build_artifact_write_request_v1,
    evaluate_artifact_write_boundary_v1,
    to_artifact_write_json_safe_v1,
)
from weslr.code_scaffold_generator import build_initial_code_scaffold_examples_v1
from weslr.sandbox_artifact_writer_executor import (
    SandboxArtifactWriteExecutionRequest,
    SandboxArtifactWriteResult,
    SandboxArtifactWriteSummary,
    ValidationError,
    build_initial_sandbox_artifact_writer_examples_v1,
    build_sandbox_artifact_write_execution_request_v1,
    execute_sandbox_artifact_write_v1,
    summarize_sandbox_artifact_write_result_v1,
    to_sandbox_artifact_write_json_safe_v1,
    validate_sandbox_artifact_write_execution_request_v1,
    validate_sandbox_artifact_write_result_v1,
)


def _find_example(examples, name):
    for item in examples:
        metadata = getattr(item, "safe_metadata", None) or {}
        if getattr(item, "write_result_id", None) == name or metadata.get("example_name") == name:
            return item
    raise AssertionError(f"missing example {name}")


def _result_map(result):
    return to_sandbox_artifact_write_json_safe_v1(result)


def _exec_request_map(request):
    return to_sandbox_artifact_write_json_safe_v1(request)


def _manual_unsafe_boundary_request(scaffold, *, path, write_request_id, dry_run_only=True, extra_fields=None):
    scaffold_map = to_artifact_write_json_safe_v1(scaffold)
    entries = [
        {
            "path": path,
            "file_type": "python" if path.endswith(".py") else "markdown",
            "content_kind": "python_module_template" if path.endswith(".py") else "markdown_template",
            "content": "# placeholder\n",
            "generation_method": "validated_template",
            "overwrite_allowed": False,
            "executable": False,
            "contains_secret": False,
            "contains_private_data": False,
            "validation_command": "validation",
            "owner_approval_required": True,
            "safe_metadata": {"source_path": path},
        }
    ]
    fields = {
        "write_request_id": write_request_id,
        "source_scaffold_id": scaffold_map["scaffold_id"],
        "source_manifest_id": scaffold_map["source_manifest_id"],
        "project_title": scaffold_map["project_title"],
        "requested_root": "sandbox_artifacts/manual_blocked",
        "allowed_root": "sandbox_artifacts/manual_blocked",
        "requested_entries": entries,
        "write_mode": "dry_run",
        "overwrite_policy": "no_overwrite",
        "create_directories_requested": False,
        "edit_existing_files_requested": False,
        "delete_requested": False,
        "executable_files_requested": False,
        "dependency_install_requested": False,
        "test_execution_requested": False,
        "deployment_requested": False,
        "public_publish_requested": False,
        "owner_approval_present": False,
        "operator_approval_present": False,
        "sandbox_only": False,
        "dry_run_only": dry_run_only,
        "risk_labels": ["blocked_path"],
        "boundary_requirements": ["manual blocked example"],
        "capability_class": "prepare_scaffold",
        "requested_file_count": 1,
        "requested_total_size_estimate": len("# placeholder\n"),
        "quality_preservation_notes": ["preserve manifest lineage"],
        "public_claim_allowed": False,
        "iss_internal_reference_allowed": True,
        "learning_claimed": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "safe_metadata": {"example_name": write_request_id},
    }
    if extra_fields:
        fields.update(extra_fields)
    return ArtifactWriteRequest(**fields)


def _normal_request_and_decision(scaffold=None):
    scaffold = scaffold or build_initial_code_scaffold_examples_v1()[0]
    request = build_artifact_write_request_v1(scaffold)
    decision = evaluate_artifact_write_boundary_v1(request)
    return request, decision, scaffold


def test_module_imports_safely():
    import weslr.sandbox_artifact_writer_executor as mod

    assert mod.HELPER_TYPE_V1 == "sandbox_artifact_writer_executor_v1"
    assert mod.SANDBOX_ARTIFACT_WRITE_EXECUTION_REQUEST_TYPE_V1 == "sandbox_artifact_write_execution_request_v1"
    assert mod.SANDBOX_ARTIFACT_WRITE_RESULT_TYPE_V1 == "sandbox_artifact_write_result_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_execution_request():
    request, decision, scaffold = _normal_request_and_decision()
    first = build_sandbox_artifact_write_execution_request_v1(request, decision, scaffold)
    second = build_sandbox_artifact_write_execution_request_v1(request, decision, scaffold)
    assert first == second
    assert isinstance(first, SandboxArtifactWriteExecutionRequest)


def test_validates_normal_execution_request():
    request, decision, scaffold = _normal_request_and_decision(build_initial_code_scaffold_examples_v1()[1])
    execution_request = build_sandbox_artifact_write_execution_request_v1(request, decision, scaffold)
    assert validate_sandbox_artifact_write_execution_request_v1(execution_request) is True


def test_dry_run_execution_returns_would_create_files():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result")
    assert isinstance(result, SandboxArtifactWriteResult)
    assert result.executed is False
    assert result.dry_run is True
    assert result.would_create_files
    assert result.result_file_count == len(result.would_create_files)


def test_dry_run_does_not_create_files_or_directories():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "missing_sandbox_root_dry_run_allowed_result")
    assert result.created_files == []
    assert result.created_directories == []


def test_real_write_request_is_blocked():
    scaffold = build_initial_code_scaffold_examples_v1()[0]
    request = build_artifact_write_request_v1(scaffold, dry_run_only=False, sandbox_only=True, owner_approval_present=True, create_directories_requested=True)
    decision = evaluate_artifact_write_boundary_v1(request)
    result = execute_sandbox_artifact_write_v1(request, decision, scaffold, sandbox_root="sandbox_artifacts/real_write")
    assert result.blocked is True
    assert "real_write_requested" in result.blocked_reason or result.blocked_reason
    assert result.executed is False


def test_missing_sandbox_root_still_allows_dry_run_only():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "missing_sandbox_root_dry_run_allowed_result")
    assert result.dry_run is True
    assert result.sandbox_root_used == ""
    assert result.blocked is False


def test_wifi_rf_dry_run_preserves_safe_scaffold_entries():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "wifi_rf_dry_run_write_result")
    paths = {item.path for item in result.would_create_files}
    assert {"README.md", "docs/ARCHITECTURE.md", "docs/PRIVACY_BOUNDARY.md", "config.example.yaml"}.issubset(paths)
    assert any(token in result.blocked_reason.lower() for token in ["covert", "diagnosis", "deployment"])
    assert result.result_file_count == len(result.would_create_files)


def test_static_website_dry_run_includes_html_css_js_planned_files():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result")
    paths = {item.path for item in result.would_create_files}
    assert {"site/index.html", "site/styles.css", "site/app.js"}.issubset(paths)
    assert result.blocked is False


def test_large_scaffold_triggers_chunking_not_capability_denial():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "large_scaffold_chunking_dry_run_result")
    assert result.chunking_required is True
    assert result.would_create_files
    assert result.blocked is False


def test_env_entry_blocked():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "env_entry_blocked_dry_run_result")
    assert result.blocked is True
    assert any(item.path == ".env" for item in result.blocked_files)


def test_weslr_state_entry_blocked():
    scaffold = build_initial_code_scaffold_examples_v1()[0]
    request = _manual_unsafe_boundary_request(scaffold, path=".weslr/state.json", write_request_id="weslr_state_write_blocked_request")
    decision = evaluate_artifact_write_boundary_v1(request)
    result = execute_sandbox_artifact_write_v1(request, decision, scaffold, sandbox_root="sandbox_artifacts/weslr_state")
    assert result.blocked is True
    assert any(item.path.startswith(".weslr") for item in result.blocked_files)


def test_protected_runtime_path_blocked():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "protected_runtime_path_blocked_result")
    assert result.blocked is True
    assert any(item.path == "weslr/chat_responder.py" for item in result.blocked_files)


def test_delete_request_blocked():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "delete_request_blocked_result")
    assert result.blocked is True
    assert result.delete_result["status"] == "blocked"


@pytest.mark.parametrize(
    "field_name,result_field",
    [
        ("dependency_install_requested", "dependency_install_result"),
        ("test_execution_requested", "test_execution_result"),
        ("deployment_requested", "deployment_result"),
        ("public_publish_requested", "public_publish_result"),
    ],
)
def test_request_flags_block_dependency_test_deployment_publish(field_name, result_field):
    scaffold = build_initial_code_scaffold_examples_v1()[1]
    request = build_artifact_write_request_v1(scaffold, **{field_name: True})
    decision = evaluate_artifact_write_boundary_v1(request)
    result = execute_sandbox_artifact_write_v1(request, decision, scaffold, sandbox_root="sandbox_artifacts/blocked_ops")
    assert getattr(result, result_field)["status"] == "blocked"
    assert result.blocked is True


def test_json_safe_export_works():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result")
    exported = to_sandbox_artifact_write_json_safe_v1(result)
    assert isinstance(exported, dict)
    assert isinstance(exported["would_create_files"], list)
    assert isinstance(exported["would_create_files"][0], dict)


def test_summary_includes_dry_run_would_create_and_blocked_counts():
    result = _find_example(build_initial_sandbox_artifact_writer_examples_v1(), "wifi_rf_dry_run_write_result")
    summary = summarize_sandbox_artifact_write_result_v1(result)
    assert isinstance(summary, SandboxArtifactWriteSummary)
    assert summary.dry_run is True
    assert summary.would_create_count == len(result.would_create_files)
    assert summary.blocked_count >= 1


def test_initial_examples_exist():
    assert len(build_initial_sandbox_artifact_writer_examples_v1()) >= 8


@pytest.mark.parametrize(
    "field_name",
    ["executed", "runtime_authority", "writes_state", "model_provider_used", "public_claim_allowed", "learning_claimed"],
)
def test_no_initial_example_allows_forbidden_request_authority(field_name):
    for result in build_initial_sandbox_artifact_writer_examples_v1():
        assert getattr(result, field_name) is False


@pytest.mark.parametrize(
    "field_name",
    ["runtime_authority", "writes_state", "model_provider_used", "public_claim_allowed", "learning_claimed"],
)
def test_no_initial_example_allows_forbidden_result_authority(field_name):
    for result in build_initial_sandbox_artifact_writer_examples_v1():
        assert getattr(result, field_name) is False


@pytest.mark.parametrize(
    "field_name,value,expected_error",
    [
        ("executed", True, "executed_must_be_false"),
        ("runtime_authority", True, "runtime_authority_must_be_false"),
        ("writes_state", True, "writes_state_must_be_false"),
        ("model_provider_used", True, "model_provider_used_must_be_false"),
        ("public_claim_allowed", True, "public_claim_allowed_must_be_false"),
        ("learning_claimed", True, "learning_claimed_must_be_false"),
    ],
)
def test_result_validation_fails_on_forbidden_true_flags(field_name, value, expected_error):
    result = _result_map(_find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result"))
    result[field_name] = value
    with pytest.raises(ValidationError, match=expected_error):
        validate_sandbox_artifact_write_result_v1(result)


@pytest.mark.parametrize(
    "field_name,value,expected_error",
    [
        ("created_files", [{"path": "x", "file_type": "python", "content_kind": "python_module_template", "bytes_estimate": 1, "action": "would_create", "status": "would_create", "blocked_reason": "", "created": True, "would_create": False, "skipped": False, "overwrite_performed": False, "secret_detected": False, "private_data_detected": False, "protected_path": False, "source_entry_id": "e", "source_manifest_id": "m", "source_scaffold_id": "s", "safe_metadata": {}}], "created_files_must_be_empty"),
        ("created_directories", [{"path": "x", "action": "would_create", "status": "would_create", "blocked_reason": "", "created": True, "would_create": False, "skipped": False, "safe_metadata": {}}], "created_directories_must_be_empty"),
    ],
)
def test_result_validation_fails_on_created_artifacts(field_name, value, expected_error):
    result = _result_map(_find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result"))
    result[field_name] = value
    with pytest.raises(ValidationError, match=expected_error):
        validate_sandbox_artifact_write_result_v1(result)


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
def test_execution_request_validation_fails_on_forbidden_true_flags(field_name, value, expected_error):
    request, decision, scaffold = _normal_request_and_decision()
    execution_request = _exec_request_map(build_sandbox_artifact_write_execution_request_v1(request, decision, scaffold))
    execution_request[field_name] = value
    with pytest.raises(ValidationError, match=expected_error):
        validate_sandbox_artifact_write_execution_request_v1(execution_request)


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
def test_execution_request_validation_fails_on_public_iss_or_claim_markers(bad_text):
    request, decision, scaffold = _normal_request_and_decision()
    execution_request = _exec_request_map(build_sandbox_artifact_write_execution_request_v1(request, decision, scaffold))
    execution_request["safe_metadata"] = {"notes": bad_text}
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_sandbox_artifact_write_execution_request_v1(execution_request)

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
def test_result_validation_fails_on_public_iss_or_claim_markers(bad_text):
    result = _result_map(_find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result"))
    result["safe_metadata"] = {"notes": bad_text}
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_sandbox_artifact_write_result_v1(result)


@pytest.mark.parametrize(
    "field_name,value,expected_error",
    [
        ("raw_prompt", "secret prompt", "forbidden_field_detected"),
    ],
)
def test_result_validation_fails_on_raw_or_private_fields(field_name, value, expected_error):
    result = _result_map(_find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result"))
    result[field_name] = value
    with pytest.raises(ValidationError, match=expected_error):
        validate_sandbox_artifact_write_result_v1(result)


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
def test_result_validation_fails_on_public_iss_and_claim_markers_in_safe_metadata(bad_text):
    result = _result_map(_find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result"))
    result["safe_metadata"] = {"notes": bad_text}
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_sandbox_artifact_write_result_v1(result)


@pytest.mark.parametrize(
    "field_name",
    ["dependency_install_result", "test_execution_result", "deployment_result", "public_publish_result"],
)
def test_result_validation_fails_when_operation_allowed(field_name):
    result = _result_map(_find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result"))
    result[field_name] = {"status": "allowed", "requested": True, "allowed": True, "blocked_reason": ""}
    with pytest.raises(ValidationError):
        validate_sandbox_artifact_write_result_v1(result)


def test_result_validation_fails_on_overwrite_performed_true():
    result = _result_map(_find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result"))
    result["would_create_files"][0]["overwrite_performed"] = True
    with pytest.raises(ValidationError, match="overwrite_performed_must_be_false"):
        validate_sandbox_artifact_write_result_v1(result)


def test_result_validation_fails_on_protected_path_allowed():
    result = _result_map(_find_example(build_initial_sandbox_artifact_writer_examples_v1(), "static_website_dry_run_write_result"))
    result["would_create_files"][0]["path"] = "weslr/chat_responder.py"
    result["would_create_files"][0]["protected_path"] = True
    result["would_create_files"][0]["blocked_reason"] = "protected_path"
    with pytest.raises(ValidationError, match="protected_path_allowed"):
        validate_sandbox_artifact_write_result_v1(result)


def test_module_does_not_import_or_call_protected_files():
    import weslr.sandbox_artifact_writer_executor as mod

    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules
    assert hasattr(mod, "build_sandbox_artifact_write_execution_request_v1")
    assert hasattr(mod, "execute_sandbox_artifact_write_v1")
    assert hasattr(mod, "validate_sandbox_artifact_write_execution_request_v1")
    assert hasattr(mod, "validate_sandbox_artifact_write_result_v1")
