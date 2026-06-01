from __future__ import annotations

import sys
from pathlib import Path

import pytest

from weslr.capability_maturity_registry import (
    CapabilityMaturityRecord,
    CapabilityMaturityRegistry,
    CapabilityMaturitySummary,
    ValidationError,
    build_capability_maturity_record_v1,
    build_capability_maturity_registry_v1,
    build_initial_capability_maturity_examples_v1,
    summarize_capability_maturity_registry_v1,
    to_capability_maturity_json_safe_v1,
    validate_capability_maturity_record_v1,
    validate_capability_maturity_registry_v1,
)


BASE_RECORD_KWARGS = dict(
    capability_id="time_anchor_resolver",
    capability_name="Time Anchor Resolver",
    capability_family="memory_and_context",
    current_maturity="validated",
    current_authority="read_only",
    implemented_files=["weslr/time_anchor_resolver.py"],
    design_docs=["docs/WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1.md"],
    review_docs=["docs/WESLR_SIGNAL_PROVENANCE_AND_SOURCE_FRESHNESS_MODEL_V1.md"],
    test_files=["weslr/tests/test_time_anchor_resolver_v1.py"],
    latest_commit="static_reference_v1",
    latest_judgment="validated",
    owner_approval_required=False,
    runtime_wiring_allowed=False,
    public_claim_allowed=False,
    data_sensitivity="low",
    action_risk="low",
    required_boundaries=["safe_memory_retrieval_executor"],
    missing_prerequisites=["memory_answer_formation_boundary"],
    blocked_next_steps=["runtime_authority"],
    recommended_next_lane="DESIGN_WESLR_MEMORY_ANSWER_FORMATION_BOUNDARY_V1",
    rollback_or_reversal_path="disable consumer references and keep metadata-only use",
    safe_metadata={"example_name": "time_anchor_resolver"},
)


BASE_REGISTRY_KWARGS = dict(
    registry_id="capability_maturity_registry_v1",
    registry_version="v1",
    created_from_commit="static_reference_v1",
)


PUBLIC_SAFE_RECORD_KWARGS = dict(
    capability_id="public_release_feature",
    capability_name="Public Release Feature",
    capability_family="public_product_and_claims",
    current_maturity="public_safe",
    current_authority="public_release_authority",
    implemented_files=["weslr/public_release_feature.py"],
    design_docs=["docs/WESLR_CAPABILITY_MATURITY_REGISTRY_V1.md"],
    review_docs=["docs/WESLR_CAPABILITY_MATURITY_REGISTRY_V1.md"],
    test_files=["weslr/tests/test_capability_maturity_registry_v1.py"],
    latest_commit="static_reference_v1",
    latest_judgment="public_safe",
    owner_approval_required=True,
    runtime_wiring_allowed=True,
    public_claim_allowed=True,
    data_sensitivity="low",
    action_risk="low",
    required_boundaries=["source_evidence_graph"],
    missing_prerequisites=[],
    blocked_next_steps=[],
    recommended_next_lane="DESIGN_WESLR_PUBLIC_CLAIM_LIFECYCLE_TRACKER_V1",
    rollback_or_reversal_path="retract public wording and fall back to metadata only",
    safe_metadata={"example_name": "public_release_feature"},
)


OWNER_RUNTIME_RECORD_KWARGS = dict(
    capability_id="owner_runtime_feature",
    capability_name="Owner Runtime Feature",
    capability_family="operator_workflow",
    current_maturity="owner_approved_runtime",
    current_authority="owner_approved_action",
    implemented_files=["weslr/owner_runtime_feature.py"],
    design_docs=["docs/WESLR_CAPABILITY_MATURITY_REGISTRY_V1.md"],
    review_docs=["docs/WESLR_CAPABILITY_MATURITY_REGISTRY_V1.md"],
    test_files=["weslr/tests/test_capability_maturity_registry_v1.py"],
    latest_commit="static_reference_v1",
    latest_judgment="owner_runtime_ready",
    owner_approval_required=True,
    runtime_wiring_allowed=True,
    public_claim_allowed=False,
    data_sensitivity="low",
    action_risk="medium",
    required_boundaries=["maturity_registry"],
    missing_prerequisites=[],
    blocked_next_steps=[],
    recommended_next_lane="DESIGN_WESLR_OWNER_OPERATOR_WORKFLOW_ENGINE_V1",
    rollback_or_reversal_path="disable runtime wiring and keep metadata only",
    safe_metadata={"example_name": "owner_runtime_feature"},
)


def _record(**overrides):
    payload = dict(BASE_RECORD_KWARGS)
    payload.update(overrides)
    return build_capability_maturity_record_v1(**payload)


def _registry(**overrides):
    payload = dict(BASE_REGISTRY_KWARGS)
    payload.update(overrides)
    return build_capability_maturity_registry_v1(**payload)


def _example_ids():
    return {item.capability_id for item in build_initial_capability_maturity_examples_v1()}


def test_module_imports_safely():
    import weslr.capability_maturity_registry as mod

    assert mod.HELPER_TYPE_V1 == "capability_maturity_registry_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_capability_record():
    first = _record()
    second = _record()

    assert first == second
    assert isinstance(first, CapabilityMaturityRecord)
    assert first.runtime_wiring_allowed is False
    assert first.public_claim_allowed is False


def test_builds_deterministic_registry():
    first = _registry()
    second = _registry()

    assert first == second
    assert isinstance(first, CapabilityMaturityRegistry)
    assert first.capability_count == len(first.capabilities)


def test_validates_normal_record():
    assert validate_capability_maturity_record_v1(_record()) is True


def test_validates_normal_registry():
    assert validate_capability_maturity_registry_v1(_registry()) is True


def test_json_safe_export_works():
    payload = to_capability_maturity_json_safe_v1(_record())
    assert isinstance(payload, dict)
    assert payload["capability_id"] == "time_anchor_resolver"
    assert payload["safe_metadata"]["example_name"] == "time_anchor_resolver"


def test_summary_includes_maturity_counts_authority_counts_and_next_lanes():
    registry = _registry()
    summary = summarize_capability_maturity_registry_v1(registry)

    assert isinstance(summary, CapabilityMaturitySummary)
    assert summary.capability_count == 21
    assert summary.maturity_counts["validated"] >= 1
    assert summary.authority_counts["read_only"] >= 1
    assert "DESIGN_WESLR_CODE_VALIDATION_RUNNER_V1" in summary.recommended_next_lanes


def test_all_initial_examples_exist():
    ids = _example_ids()
    assert ids == {
        "time_anchor_resolver",
        "safe_memory_retrieval_executor",
        "poison_shield_helpers",
        "project_brief_builder",
        "code_scaffold_generator",
        "artifact_writer_boundary",
        "sandbox_artifact_writer_dry_run_executor",
        "artifact_provenance_boundary",
        "future_state_forecasting_engine",
        "scenario_simulation_engine",
        "home_assistant_signal_intake_boundary",
        "signal_provenance_freshness_model",
        "energy_signal_conflict_resolution_policy",
        "energy_grid_signal_intelligence",
        "forecast_error_ledger",
        "wifi_rf_sensing_program",
        "governed_llm_provider_boundary",
        "code_validation_runner",
        "source_evidence_graph",
        "public_claim_lifecycle_tracker",
        "owner_operator_workflow_engine",
    }


def test_design_only_capability_is_not_treated_as_implemented():
    record = next(item for item in build_initial_capability_maturity_examples_v1() if item.capability_id == "energy_grid_signal_intelligence")
    assert record.current_maturity == "design_only"
    assert record.implemented_files == []
    assert record.runtime_wiring_allowed is False


def test_metadata_helper_is_not_runtime_wired():
    record = next(item for item in build_initial_capability_maturity_examples_v1() if item.capability_id == "artifact_provenance_boundary")
    assert record.current_authority in {"validation_only", "read_only", "metadata_only"}
    assert record.runtime_wiring_allowed is False


def test_dry_run_helper_is_not_real_world_authority():
    record = next(item for item in build_initial_capability_maturity_examples_v1() if item.capability_id == "sandbox_artifact_writer_dry_run_executor")
    assert record.current_maturity == "dry_run"
    assert record.current_authority == "dry_run_only"
    assert record.runtime_wiring_allowed is False


def test_public_claim_allowed_only_for_public_safe():
    allowed = _record(**PUBLIC_SAFE_RECORD_KWARGS)
    assert validate_capability_maturity_record_v1(allowed) is True
    assert allowed.public_claim_allowed is True

    blocked = to_capability_maturity_json_safe_v1(_record())
    blocked["public_claim_allowed"] = True
    with pytest.raises(ValidationError, match="public_claim_allowed_must_be_false_for_non_public_safe"):
        validate_capability_maturity_record_v1(blocked)


def test_runtime_wiring_allowed_only_for_owner_approved_or_later():
    allowed = _record(**OWNER_RUNTIME_RECORD_KWARGS)
    assert validate_capability_maturity_record_v1(allowed) is True
    assert allowed.runtime_wiring_allowed is True

    blocked = to_capability_maturity_json_safe_v1(_record())
    blocked["runtime_wiring_allowed"] = True
    with pytest.raises(ValidationError, match="runtime_wiring_allowed_must_be_false_for_non_owner_approved_maturity"):
        validate_capability_maturity_record_v1(blocked)


def test_blocked_or_deprecated_uses_blocked_authority():
    record = next(item for item in build_initial_capability_maturity_examples_v1() if item.capability_id == "public_claim_lifecycle_tracker")
    assert record.current_maturity == "blocked_or_deprecated"
    assert record.current_authority == "blocked"
    assert record.public_claim_allowed is False


def test_validation_fails_unknown_maturity():
    with pytest.raises(ValidationError, match="unknown_maturity"):
        validate_capability_maturity_record_v1(_record(current_maturity="mystery_maturity"))


def test_validation_fails_unknown_authority():
    with pytest.raises(ValidationError, match="unknown_authority"):
        validate_capability_maturity_record_v1(_record(current_authority="mystery_authority"))


def test_validation_fails_unknown_family():
    with pytest.raises(ValidationError, match="unknown_family"):
        validate_capability_maturity_record_v1(_record(capability_family="alien_ops"))


def test_validation_fails_public_claim_below_public_safe():
    with pytest.raises(ValidationError, match="public_claim_allowed_must_be_false_for_non_public_safe"):
        validate_capability_maturity_record_v1(_record(public_claim_allowed=True, current_maturity="validated"))


def test_validation_fails_runtime_wiring_below_owner_approved_runtime():
    with pytest.raises(ValidationError, match="runtime_wiring_allowed_must_be_false_for_non_owner_approved_maturity"):
        validate_capability_maturity_record_v1(_record(runtime_wiring_allowed=True, current_maturity="validated"))


def test_validation_fails_metadata_helper_with_public_release_authority():
    with pytest.raises(ValidationError, match="public_release_authority_requires_public_safe|authority_not_allowed_for_maturity"):
        validate_capability_maturity_record_v1(
            _record(current_maturity="metadata_helper", current_authority="public_release_authority")
        )


def test_validation_fails_agi_consciousness_turing_certification_marker():
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_capability_maturity_record_v1(_record(safe_metadata={"notes": "AGI consciousness sentience Turing certification"}))


def test_validation_fails_public_readiness_claim():
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_capability_maturity_record_v1(_record(safe_metadata={"notes": "public readiness claim"}))


def test_validation_fails_weslr_write_claim():
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_capability_maturity_record_v1(_record(safe_metadata={"notes": "write to .weslr"}))


def test_validation_fails_hidden_prompt_or_raw_private_field():
    payload = to_capability_maturity_json_safe_v1(_record())
    payload["hidden_prompt"] = "secret hidden prompt"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_capability_maturity_record_v1(payload)

    payload = to_capability_maturity_json_safe_v1(_record())
    payload["raw_private_text"] = "secret raw private text"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_capability_maturity_record_v1(payload)


def test_validation_fails_secret_token_or_key_field():
    payload = to_capability_maturity_json_safe_v1(_record())
    payload["secret_token"] = "tok_123"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_capability_maturity_record_v1(payload)

    payload = to_capability_maturity_json_safe_v1(_record())
    payload["api_key"] = "key_123"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_capability_maturity_record_v1(payload)


def test_module_does_not_import_or_call_chat_responder():
    source = Path(__file__).resolve().parents[1] / "capability_maturity_registry.py"
    text = source.read_text()
    assert "chat_responder" not in text
    assert "weslr.chat_responder" not in sys.modules


def test_module_does_not_import_or_call_main():
    source = Path(__file__).resolve().parents[1] / "capability_maturity_registry.py"
    text = source.read_text()
    assert "main.py" not in text
    assert "weslr.main" not in sys.modules


def test_module_does_not_import_or_call_dialogue():
    source = Path(__file__).resolve().parents[1] / "capability_maturity_registry.py"
    text = source.read_text()
    assert "dialogue" not in text
    assert "dialogue" not in sys.modules


def test_module_does_not_import_or_call_chat_ui():
    source = Path(__file__).resolve().parents[1] / "capability_maturity_registry.py"
    text = source.read_text()
    assert "chat_ui" not in text
    assert "chat_ui" not in sys.modules
