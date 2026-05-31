from __future__ import annotations

import ast
import importlib
import inspect
from functools import lru_cache

import pytest

from weslr.behavior_pack_registry import (
    BehaviorPack,
    BehaviorPackRegistry,
    ValidationError,
    build_behavior_pack_registry_v1,
    build_behavior_pack_v1,
    build_initial_behavior_pack_registry_v1,
    summarize_behavior_pack_registry_v1,
    to_behavior_pack_registry_json_safe_v1,
    validate_behavior_pack_registry_v1,
    validate_behavior_pack_v1,
)

MODULE_NAME = "weslr.behavior_pack_registry"

PROHIBITED_MODULES = ["chat_responder", "main", "dialogue", "chat_ui"]

EXPECTED_PACK_IDS = [
    "weslr_identity_capability_behavior_pack",
    "unknown_term_discovery_behavior_pack",
    "inactive_capability_boundary_behavior_pack",
    "weslr_owner_workflow_behavior_pack",
]


@lru_cache(maxsize=1)
def _module():
    return importlib.import_module(MODULE_NAME)


@lru_cache(maxsize=1)
def _registry():
    return build_initial_behavior_pack_registry_v1()


@lru_cache(maxsize=1)
def _registry_json():
    return to_behavior_pack_registry_json_safe_v1(_registry())


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


@lru_cache(maxsize=1)
def _pack_payload(pack_id: str) -> dict[str, object]:
    registry = _registry_json()
    for pack in registry["packs"]:
        if pack["pack_id"] == pack_id:
            return dict(pack)
    raise AssertionError(f"missing pack: {pack_id}")


@lru_cache(maxsize=1)
def _registry_payload() -> dict[str, object]:
    return dict(_registry_json())


@pytest.mark.parametrize("pack_id", EXPECTED_PACK_IDS)
def test_01_module_imports_safely(pack_id) -> None:
    assert isinstance(_module(), object)
    assert pack_id in EXPECTED_PACK_IDS


@pytest.mark.parametrize("pack_id", EXPECTED_PACK_IDS)
def test_02_builds_deterministic_behavior_pack(pack_id) -> None:
    payload = _pack_payload(pack_id)
    one = build_behavior_pack_v1(**payload)
    two = build_behavior_pack_v1(**payload)
    assert one == two


@pytest.mark.parametrize("_", [0])
def test_03_builds_deterministic_registry(_) -> None:
    assert build_initial_behavior_pack_registry_v1() == build_initial_behavior_pack_registry_v1()


@pytest.mark.parametrize("pack_id", EXPECTED_PACK_IDS)
def test_04_validates_normal_behavior_pack(pack_id) -> None:
    assert validate_behavior_pack_v1(_pack_payload(pack_id)) is True


@pytest.mark.parametrize("_", [0])
def test_05_validates_normal_registry(_) -> None:
    assert validate_behavior_pack_registry_v1(_registry_payload()) is True


@pytest.mark.parametrize("_", [0])
def test_06_json_safe_export_works(_) -> None:
    safe = to_behavior_pack_registry_json_safe_v1(_registry())
    assert safe["pack_count"] == 4
    assert isinstance(safe["packs"], list)
    assert isinstance(safe["packs"][0]["source_pattern_ids"], list)


@pytest.mark.parametrize("_", [0])
def test_07_summary_includes_pack_counts_status_counts(_) -> None:
    summary = summarize_behavior_pack_registry_v1(_registry())
    assert summary["pack_count"] == 4
    assert summary["status_counts"]["candidate_only"] == 1
    assert summary["status_counts"]["replay_supported"] == 2
    assert summary["status_counts"]["proof_reviewed_internal"] == 1


@pytest.mark.parametrize("_", [0])
def test_08_initial_registry_exists(_) -> None:
    registry = _registry()
    assert registry.registry_id == "weslr_behavior_pack_registry_v1"
    assert registry.pack_count == 4


@pytest.mark.parametrize("_", [0])
def test_09_identity_capability_behavior_pack_exists(_) -> None:
    pack = next(pack for pack in _registry().packs if pack.pack_id == "weslr_identity_capability_behavior_pack")
    assert pack.pack_type == "core_identity_capability_pack"


@pytest.mark.parametrize("_", [0])
def test_10_unknown_term_discovery_behavior_pack_exists(_) -> None:
    pack = next(pack for pack in _registry().packs if pack.pack_id == "unknown_term_discovery_behavior_pack")
    assert pack.pack_type == "unknown_term_discovery_pack"


@pytest.mark.parametrize("_", [0])
def test_11_inactive_capability_boundary_behavior_pack_exists(_) -> None:
    pack = next(pack for pack in _registry().packs if pack.pack_id == "inactive_capability_boundary_behavior_pack")
    assert pack.pack_type == "inactive_capability_boundary_pack"


@pytest.mark.parametrize("_", [0])
def test_12_owner_workflow_behavior_pack_exists(_) -> None:
    pack = next(pack for pack in _registry().packs if pack.pack_id == "weslr_owner_workflow_behavior_pack")
    assert pack.pack_type == "owner_workflow_pack"
    assert pack.status == "candidate_only"


@pytest.mark.parametrize("_", [0])
def test_13_candidate_only_domain_packs_are_not_replay_supported(_) -> None:
    candidate_only_packs = [pack for pack in _registry().packs if pack.status == "candidate_only"]
    assert candidate_only_packs
    assert all(pack.status != "replay_supported" for pack in candidate_only_packs)


@pytest.mark.parametrize("_", [0])
def test_14_no_initial_pack_is_live_routable(_) -> None:
    assert all(pack.safe_to_route_live is False for pack in _registry().packs)


@pytest.mark.parametrize("_", [0])
def test_15_no_initial_pack_is_public_label_allowed(_) -> None:
    assert all(pack.public_label_allowed is False for pack in _registry().packs)


@pytest.mark.parametrize("_", [0])
def test_16_no_initial_pack_auto_applies(_) -> None:
    assert all(pack.safe_to_apply_automatically is False for pack in _registry().packs)


@pytest.mark.parametrize("_", [0])
def test_17_all_initial_packs_are_internal_only(_) -> None:
    assert all(pack.internal_only is True for pack in _registry().packs)


@pytest.mark.parametrize("_", [0])
def test_18_iss_reference_is_internal_only(_) -> None:
    registry = _registry()
    assert registry.iss_internal_reference_allowed is True
    assert all(pack.iss_internal_reference_allowed is True for pack in registry.packs)


@pytest.mark.parametrize("_", [0])
def test_19_identity_pack_references_identity_capability_patterns(_) -> None:
    pack = next(pack for pack in _registry().packs if pack.pack_id == "weslr_identity_capability_behavior_pack")
    assert "identity_status_directness_pattern" in pack.source_pattern_ids
    assert "capability_orientation_directness_pattern" in pack.source_pattern_ids


@pytest.mark.parametrize("_", [0])
def test_20_unknown_pack_references_unknown_term_pattern(_) -> None:
    pack = next(pack for pack in _registry().packs if pack.pack_id == "unknown_term_discovery_behavior_pack")
    assert pack.source_pattern_ids == ("unknown_term_friction_preference_pattern",)


@pytest.mark.parametrize("_", [0])
def test_21_boundary_pack_references_inactive_capability_boundary_pattern(_) -> None:
    pack = next(pack for pack in _registry().packs if pack.pack_id == "inactive_capability_boundary_behavior_pack")
    assert pack.source_pattern_ids == ("inactive_capability_boundary_pattern",)


@pytest.mark.parametrize("_", [0])
def test_22_replay_supported_packs_reference_replay_suites(_) -> None:
    packs = [pack for pack in _registry().packs if pack.status == "replay_supported"]
    assert packs
    assert all(pack.source_replay_suite_ids for pack in packs)


@pytest.mark.parametrize(
    "claim_field",
    [
        "agi_claimed",
        "consciousness_claimed",
        "sentience_claimed",
        "official_turing_claimed",
        "certification_claimed",
        "public_ready_claimed",
    ],
)
def test_23_26_no_pack_claims_flags_are_true(claim_field) -> None:
    assert all(getattr(pack, claim_field) is False for pack in _registry().packs)


@pytest.mark.parametrize("_", [0])
def test_27_no_pack_writes_state(_) -> None:
    assert all(pack.writes_state is False for pack in _registry().packs)


@pytest.mark.parametrize("_", [0])
def test_28_no_pack_uses_model_provider(_) -> None:
    assert all(pack.model_provider_used is False for pack in _registry().packs)


@pytest.mark.parametrize(
    "field_name",
    ["raw_prompt", "raw_answer", "transcript"],
)
def test_29_31_raw_fields_fail_validation(field_name) -> None:
    payload = _pack_payload("weslr_identity_capability_behavior_pack")
    payload[field_name] = "secret"
    with pytest.raises(ValidationError):
        validate_behavior_pack_v1(payload)


@pytest.mark.parametrize("field_name", ["pack_type", "status", "promotion_status"])
def test_32_34_unknown_enum_values_fail_validation(field_name) -> None:
    payload = _pack_payload("weslr_identity_capability_behavior_pack")
    payload[field_name] = "unknown_value"
    with pytest.raises(ValidationError):
        validate_behavior_pack_v1(payload)


@pytest.mark.parametrize("field_name", ["agi_claimed", "consciousness_claimed", "official_turing_claimed", "certification_claimed", "public_ready_claimed", "sentience_claimed", "learning_claimed", "runtime_authority", "writes_state", "model_provider_used", "safe_to_route_live", "safe_to_apply_automatically"])
def test_35_40_flags_true_fail_validation(field_name) -> None:
    payload = _pack_payload("weslr_identity_capability_behavior_pack")
    payload[field_name] = True
    with pytest.raises(ValidationError):
        validate_behavior_pack_v1(payload)


@pytest.mark.parametrize("field_name", ["chat_responder", "main", "dialogue", "chat_ui"])
def test_41_44_module_does_not_import_prohibited_modules(field_name) -> None:
    imports = _module_imports()
    assert not any(field_name == imported or imported.endswith(f".{field_name}") for imported in imports)
