from __future__ import annotations

import ast
import inspect
import json
from functools import lru_cache
from typing import Any

from weslr.arc_style_grid_schema_helpers import build_arc_style_grid_metadata_v1
from weslr.arc_unknown_engine_level_ladder_generator import (
    LEVEL_FAMILY_CATALOG_V1,
    LEVEL_TIERS_V1,
    PREVIOUS_HELDOUT_FAMILIES_V1,
    SCHEMA_VERSION_V1,
    build_arc_unknown_engine_failure_forecast_v1,
    generate_arc_unknown_engine_level_ladder_v1,
    recommend_arc_unknown_engine_next_step_v1,
    summarize_arc_unknown_engine_level_ladder_v1,
    to_arc_unknown_engine_level_ladder_json_safe_v1,
    validate_arc_unknown_engine_level_ladder_v1,
    validate_evaluator_packet_v1,
    validate_level_v1,
    validate_solver_visible_packet_v1,
)

FORBIDDEN_IMPORT_FRAGMENTS = (
    "provider",
    "payment",
    "chat_responder",
    "respond_chat",
    "openai",
    "anthropic",
    "google",
    "ollama",
    "requests",
)


@lru_cache(maxsize=4)
def _suite(seed: int = 20260626) -> dict[str, Any]:
    return generate_arc_unknown_engine_level_ladder_v1(seed=seed)


def _json_safe(value: Any) -> Any:
    safe = to_arc_unknown_engine_level_ladder_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def test_generator_creates_minimum_bounded_suite_and_summary() -> None:
    suite = _suite()
    summary = summarize_arc_unknown_engine_level_ladder_v1(suite)
    validation = validate_arc_unknown_engine_level_ladder_v1(suite)
    assert suite["schema_version"] == SCHEMA_VERSION_V1
    assert validation["valid"] is True
    assert summary["level_count"] >= 12
    assert summary["family_count"] >= 6
    assert summary["represented_tier_count"] == 6
    assert summary["concrete_tier_count"] >= 2
    assert summary["concrete_tiers"] == [0, 1]
    assert all(count >= 2 for count in summary["variants_by_family"].values())


def test_all_catalog_families_are_new_and_not_previous_heldout_names() -> None:
    family_ids = {entry["family_id"] for entry in LEVEL_FAMILY_CATALOG_V1}
    assert len(family_ids) >= 6
    assert family_ids.isdisjoint(set(PREVIOUS_HELDOUT_FAMILIES_V1))


def test_all_grids_validate_and_levels_are_json_safe() -> None:
    suite = _suite()
    for level in suite["levels"]:
        assert validate_level_v1(level)["valid"] is True
        for pair in level["train"]:
            for grid in (pair["input"], pair["output"]):
                meta = build_arc_style_grid_metadata_v1(grid)
                assert meta["trace"]["rectangular"] is True
                assert not meta["invalid_cells"]
                assert 1 <= meta["width"] <= 30
                assert 1 <= meta["height"] <= 30
        for grid in (level["test_input"], level["evaluator_packet"]["expected_output"]):
            meta = build_arc_style_grid_metadata_v1(grid)
            assert meta["trace"]["rectangular"] is True
            assert not meta["invalid_cells"]
    assert json.dumps(_json_safe(suite), ensure_ascii=False)


def test_deterministic_regeneration_produces_identical_json_safe_summary() -> None:
    first = summarize_arc_unknown_engine_level_ladder_v1(generate_arc_unknown_engine_level_ladder_v1(seed=20260626))
    second = summarize_arc_unknown_engine_level_ladder_v1(generate_arc_unknown_engine_level_ladder_v1(seed=20260626))
    assert _json_safe(first) == _json_safe(second)
    assert json.dumps(_json_safe(first), ensure_ascii=False)


def test_solver_visible_packets_exclude_answer_keys_expected_outputs_and_family_ids() -> None:
    suite = _suite()
    for level in suite["levels"]:
        packet = level["solver_visible_packet"]
        validation = validate_solver_visible_packet_v1(packet)
        assert validation["valid"] is True
        dumped = json.dumps(packet, ensure_ascii=False, sort_keys=True)
        assert '"expected_output"' not in dumped
        assert '"family_id"' not in dumped
        assert '"answer_key":' not in dumped
        assert '"generator_metadata"' not in dumped
        assert packet["synthetic_only"] is True
        assert packet["non_claim_safe"] is True
        assert packet["public_boundary_flags"]["solver_visible_answer_key"] is False


def test_evaluator_packets_include_expected_outputs_and_boundary_flags() -> None:
    suite = _suite()
    for level in suite["levels"]:
        packet = level["evaluator_packet"]
        validation = validate_evaluator_packet_v1(packet)
        assert validation["valid"] is True
        assert packet["expected_output"]
        assert packet["family_id"] == level["family_id"]
        assert packet["tier"] == level["tier"]
        assert packet["synthetic_only"] is True
        assert packet["non_claim_safe"] is True
        assert packet["public_boundary_flags"]["uses_public_arc_data"] is False


def test_dynamic_curriculum_scaffold_returns_expected_recommendations() -> None:
    assert recommend_arc_unknown_engine_next_step_v1([
        {"solver_result": "exact", "tier": 0},
        {"solver_result": "exact", "tier": 0},
    ])["recommendation_mode"] == "unlock_next_tier"
    assert recommend_arc_unknown_engine_next_step_v1([
        {"solver_result": "partial", "tier": 1},
        {"solver_result": "partial", "tier": 1},
    ])["recommendation_mode"] == "neighbor_levels"
    assert recommend_arc_unknown_engine_next_step_v1([
        {"solver_result": "unsupported", "tier": 1},
    ])["recommendation_mode"] == "minimal_repro"
    assert recommend_arc_unknown_engine_next_step_v1([
        {"solver_result": "invalid", "tier": 1},
    ])["recommendation_mode"] == "boundary_diagnostics"
    assert recommend_arc_unknown_engine_next_step_v1([
        {"solver_result": "exact", "tier": 1, "small_variation_collapse": True},
    ])["recommendation_mode"] == "overfit_frontier"
    assert recommend_arc_unknown_engine_next_step_v1([
        {"solver_result": "exact", "tier": 1},
    ])["recommendation_mode"] == "increase_strangeness"


def test_failure_forecast_packet_is_json_safe_and_non_claim_safe() -> None:
    packet = build_arc_unknown_engine_failure_forecast_v1(
        forecast_run_id="forecast-001",
        tier=1,
        level_family_id="role_color_binding",
        pressure_axes=["relation_dependency", "decoy_regularity"],
        prior_results=[
            {"level_id": "a", "solver_result": "partial", "tier": 1},
            {"level_id": "b", "solver_result": "partial", "tier": 1},
        ],
    )
    assert packet["forecast_run_id"] == "forecast-001"
    assert packet["recommendation_mode"] == "neighbor_levels"
    assert packet["failure_cause"] == "mismatch_frontier_detected"
    assert packet["synthetic_only"] is True
    assert packet["non_claim_safe"] is True
    assert json.dumps(_json_safe(packet), ensure_ascii=False)


def test_public_boundary_flags_are_present_everywhere() -> None:
    suite = _suite()
    assert suite["boundary_flags"]["synthetic_only"] is True
    assert suite["boundary_flags"]["non_claim_safe"] is True
    assert suite["boundary_flags"]["uses_public_arc_data"] is False
    for level in suite["levels"]:
        assert level["public_boundary_flags"]["uses_kaggle_data"] is False
        assert level["solver_visible_packet"]["public_boundary_flags"]["runtime_wiring_touched"] is False
        assert level["evaluator_packet"]["public_boundary_flags"]["provider_model_api_called"] is False


def test_module_source_has_no_weslr_writes_protected_file_touches_or_forbidden_calls() -> None:
    module = __import__("weslr.arc_unknown_engine_level_ladder_generator", fromlist=["*"])
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    forbidden = {
        fragment
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS
        if fragment in imported_modules or any(fragment in mod for mod in imported_modules)
    }
    assert forbidden == set()
    assert ".weslr" in source
    assert "write(" not in source
    assert "open(" not in source
    assert "respond_chat(" not in source
    assert "weslr/main.py" not in source
    assert "dialogue.py" not in source
    assert "chat_ui.py" not in source


def test_tier_metadata_contains_all_six_tiers_with_only_zero_and_one_concrete() -> None:
    assert len(LEVEL_TIERS_V1) == 6
    concrete = [entry["tier"] for entry in LEVEL_TIERS_V1 if entry["concrete_in_v1"] is True]
    assert concrete == [0, 1]
