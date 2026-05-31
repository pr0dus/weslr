from __future__ import annotations

import ast
import importlib
import inspect
from functools import lru_cache

import pytest

from weslr.behavior_pack_promotion_policy import (
    BehaviorPackPromotionDecision,
    BehaviorPackPromotionPacket,
    ValidationError,
    build_behavior_pack_promotion_decision_v1,
    build_initial_behavior_pack_promotion_policy_v1,
    evaluate_behavior_pack_promotion_v1,
    evaluate_behavior_pack_registry_promotion_v1,
    summarize_behavior_pack_promotion_packet_v1,
    to_behavior_pack_promotion_json_safe_v1,
    validate_behavior_pack_promotion_decision_v1,
    validate_behavior_pack_promotion_packet_v1,
)
from weslr.behavior_pack_registry import build_initial_behavior_pack_registry_v1

MODULE_NAME = "weslr.behavior_pack_promotion_policy"
PROHIBITED_MODULES = ["chat_responder", "main", "dialogue", "chat_ui"]


@lru_cache(maxsize=1)
def _module():
    return importlib.import_module(MODULE_NAME)


@lru_cache(maxsize=1)
def _packet():
    return build_initial_behavior_pack_promotion_policy_v1()


@lru_cache(maxsize=1)
def _packet_json():
    return to_behavior_pack_promotion_json_safe_v1(_packet())


@lru_cache(maxsize=1)
def _decision_json(pack_id: str):
    for decision in _packet_json()["decisions"]:
        if decision["pack_id"] == pack_id:
            return dict(decision)
    raise AssertionError(pack_id)


@lru_cache(maxsize=1)
def _module_imports() -> set[str]:
    module = _module()
    tree = ast.parse(inspect.getsource(module))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


@pytest.mark.parametrize("_", [0])
def test_01_module_imports_safely(_) -> None:
    assert hasattr(_module(), "build_behavior_pack_promotion_decision_v1")


@pytest.mark.parametrize("pack_id", ["weslr_identity_capability_behavior_pack"])
def test_02_builds_deterministic_promotion_decision(pack_id) -> None:
    payload = _decision_json(pack_id)
    one = build_behavior_pack_promotion_decision_v1(**payload)
    two = build_behavior_pack_promotion_decision_v1(**payload)
    assert one == two


@pytest.mark.parametrize("_", [0])
def test_03_evaluates_deterministic_initial_registry(_) -> None:
    assert evaluate_behavior_pack_registry_promotion_v1(build_initial_behavior_pack_registry_v1()) == _packet()


@pytest.mark.parametrize("pack_id", ["weslr_identity_capability_behavior_pack"])
def test_04_validates_normal_decision(pack_id) -> None:
    assert validate_behavior_pack_promotion_decision_v1(_decision_json(pack_id)) is True


@pytest.mark.parametrize("_", [0])
def test_05_validates_normal_packet(_) -> None:
    assert validate_behavior_pack_promotion_packet_v1(_packet_json()) is True


@pytest.mark.parametrize("_", [0])
def test_06_json_safe_export_works(_) -> None:
    safe = to_behavior_pack_promotion_json_safe_v1(_packet())
    assert safe["decision_count"] == 4
    assert isinstance(safe["decisions"], list)


@pytest.mark.parametrize("_", [0])
def test_07_summary_includes_eligibility_and_status_counts(_) -> None:
    summary = summarize_behavior_pack_promotion_packet_v1(_packet())
    assert summary["eligibility_counts"]["eligible_internal_use_only"] == 3
    assert summary["eligibility_counts"]["candidate_only_not_ready"] == 1
    assert summary["recommended_status_counts"]["approved_for_internal_use"] == 3
    assert summary["recommended_status_counts"]["keep_candidate"] == 1


@pytest.mark.parametrize("_", [0])
def test_08_initial_packet_has_four_decisions(_) -> None:
    assert _packet().decision_count == 4


@pytest.mark.parametrize("pack_id", [
    "weslr_identity_capability_behavior_pack",
    "unknown_term_discovery_behavior_pack",
    "inactive_capability_boundary_behavior_pack",
    "weslr_owner_workflow_behavior_pack",
])
def test_09_12_expected_decisions_exist(pack_id) -> None:
    decision = next(d for d in _packet().decisions if d.pack_id == pack_id)
    assert decision.pack_id == pack_id


@pytest.mark.parametrize("pack_id", [
    "weslr_identity_capability_behavior_pack",
    "unknown_term_discovery_behavior_pack",
    "inactive_capability_boundary_behavior_pack",
])
def test_13_replay_proof_supported_packs_are_internal_only_eligible(pack_id) -> None:
    decision = next(d for d in _packet().decisions if d.pack_id == pack_id)
    assert decision.promotion_eligibility == "eligible_internal_use_only"
    assert decision.safe_for_internal_use is True
    assert decision.recommended_promotion_status == "approved_for_internal_use"


@pytest.mark.parametrize("_", [0])
def test_14_candidate_only_pack_is_not_falsely_promoted(_) -> None:
    decision = next(d for d in _packet().decisions if d.pack_id == "weslr_owner_workflow_behavior_pack")
    assert decision.promotion_eligibility == "candidate_only_not_ready"
    assert decision.recommended_promotion_status == "keep_candidate"
    assert decision.safe_for_internal_use is False


@pytest.mark.parametrize("field_name", ["safe_to_route_live", "safe_to_apply_automatically", "public_label_allowed"])
def test_15_17_no_decision_routes_or_public_labels(field_name) -> None:
    assert all(getattr(d, field_name) is False for d in _packet().decisions)


@pytest.mark.parametrize("_", [0])
def test_18_no_decision_claims_learning(_) -> None:
    assert all(d.learning_claimed is False for d in _packet().decisions)


@pytest.mark.parametrize("_", [0])
def test_19_no_decision_performs_promotion(_) -> None:
    assert all(d.promotion_performed is False for d in _packet().decisions)


@pytest.mark.parametrize("_", [0])
def test_20_iss_reference_remains_internal_only(_) -> None:
    assert _packet().iss_internal_reference_allowed is True


@pytest.mark.parametrize(
    "field_name",
    ["agi_claimed", "consciousness_claimed", "official_turing_claimed", "certification_claimed", "public_ready_claimed"],
)
def test_21_24_risk_block_fields_true_fail_validation(field_name) -> None:
    payload = _decision_json("weslr_identity_capability_behavior_pack")
    payload[field_name] = True
    with pytest.raises(ValidationError):
        validate_behavior_pack_promotion_decision_v1(payload)


@pytest.mark.parametrize("field_name", ["runtime_authority", "writes_state", "model_provider_used", "promotion_performed"])
def test_25_28_authority_flags_true_fail_validation(field_name) -> None:
    payload = _decision_json("weslr_identity_capability_behavior_pack")
    payload[field_name] = True
    with pytest.raises(ValidationError):
        validate_behavior_pack_promotion_decision_v1(payload)


@pytest.mark.parametrize("field_name", ["public_label_allowed", "safe_to_route_live", "safe_to_apply_automatically"])
def test_29_31_public_and_live_flags_true_fail_validation(field_name) -> None:
    payload = _decision_json("weslr_identity_capability_behavior_pack")
    payload[field_name] = True
    with pytest.raises(ValidationError):
        validate_behavior_pack_promotion_decision_v1(payload)


@pytest.mark.parametrize("field_name", ["raw_prompt", "raw_answer", "transcript"])
def test_32_34_raw_fields_fail_validation(field_name) -> None:
    payload = _decision_json("weslr_identity_capability_behavior_pack")
    payload[field_name] = "secret"
    with pytest.raises(ValidationError):
        validate_behavior_pack_promotion_decision_v1(payload)


@pytest.mark.parametrize("field_name", ["promotion_eligibility", "recommended_promotion_status"])
def test_35_36_unknown_enums_fail_validation(field_name) -> None:
    payload = _decision_json("weslr_identity_capability_behavior_pack")
    payload[field_name] = "unknown_value"
    with pytest.raises(ValidationError):
        validate_behavior_pack_promotion_decision_v1(payload)


@pytest.mark.parametrize("_", [0])
def test_37_duplicate_decision_ids_fail_validation(_) -> None:
    payload = _packet_json()
    payload["decisions"] = [dict(payload["decisions"][0]), dict(payload["decisions"][0])]
    payload["decision_count"] = 2
    with pytest.raises(ValidationError):
        validate_behavior_pack_promotion_packet_v1(payload)


@pytest.mark.parametrize("_", [0])
def test_38_count_mismatch_fail_validation(_) -> None:
    payload = _packet_json()
    payload["decision_count"] = 99
    with pytest.raises(ValidationError):
        validate_behavior_pack_promotion_packet_v1(payload)


@pytest.mark.parametrize("module_name", ["chat_responder", "main", "dialogue", "chat_ui"])
def test_39_42_module_does_not_import_prohibited_modules(module_name) -> None:
    imports = _module_imports()
    assert not any(module_name == imported or imported.endswith(f".{module_name}") for imported in imports)
