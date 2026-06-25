from __future__ import annotations

import ast
import inspect
import json
from copy import deepcopy
from functools import lru_cache
from typing import Any

import pytest

from weslr.arc_style_depth2_compositional_program_search import (
    SEARCH_DEPTH_V1,
    SEARCH_TYPE_V1,
    run_arc_style_depth2_compositional_program_search_v1,
    summarize_arc_style_depth2_compositional_program_search_result_v1,
    to_arc_style_depth2_compositional_program_search_json_safe_v1,
    validate_arc_style_depth2_compositional_program_search_result_v1,
)
from weslr.arc_style_heldout_compositional_baseline import run_arc_style_heldout_compositional_baseline_v1
from weslr.arc_style_heldout_compositional_synthetic_generator import (
    HELDOUT_RECIPE_FAMILIES_V1,
    generate_arc_style_heldout_compositional_suite_v1,
)
from weslr.arc_style_synthetic_solver_suite import run_arc_style_synthetic_solver_suite_v1, summarize_arc_style_synthetic_solver_suite_result_v1
from weslr.arc_style_typed_primitive_signatures import (
    EXPECTED_PRIMITIVE_NAMES_V1,
    build_arc_style_typed_primitive_signature_catalog_v1,
    validate_arc_style_typed_primitive_signature_v1,
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
    "pathlib",
    "subprocess",
)


def _json_safe(value: Any) -> Any:
    safe = to_arc_style_depth2_compositional_program_search_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


@lru_cache(maxsize=4)
def _search_result(seed: int = 20260625) -> dict[str, Any]:
    return run_arc_style_depth2_compositional_program_search_v1(seed=seed)


@lru_cache(maxsize=4)
def _baseline_result(seed: int = 20260625) -> dict[str, Any]:
    return run_arc_style_heldout_compositional_baseline_v1(seed=seed)


@lru_cache(maxsize=4)
def _solver_suite_result() -> dict[str, Any]:
    return run_arc_style_synthetic_solver_suite_v1()


def test_depth2_search_is_deterministic_and_beats_baseline() -> None:
    first = run_arc_style_depth2_compositional_program_search_v1(seed=20260625)
    second = _search_result(seed=20260625)
    assert _json_safe(first) == _json_safe(second)
    assert json.dumps(_json_safe(first), ensure_ascii=False)
    validation = validate_arc_style_depth2_compositional_program_search_result_v1(first)
    summary = summarize_arc_style_depth2_compositional_program_search_result_v1(first)
    assert validation["valid"] is True
    assert summary["valid"] is True
    assert first["search_type"] == SEARCH_TYPE_V1
    assert first["depth"] == SEARCH_DEPTH_V1 == 2
    assert first["heldout_baseline_before"]["exact_count"] == 1
    assert first["heldout_baseline_before"]["partial_count"] == 2
    assert first["heldout_baseline_before"]["unsupported_count"] == 11
    assert first["heldout_search_after"]["exact_count"] == 5
    assert first["heldout_search_after"]["partial_count"] == 5
    assert first["heldout_search_after"]["unsupported_count"] == 4
    assert first["comparison_report"]["exact_improvement"] == 4
    assert first["comparison_report"]["unsupported_reduction"] == 7
    assert first["top2_program_packet_count"] == 14
    assert first["top2_program_packet_valid_count"] == 14
    assert first["top2_program_packet_invalid_count"] == 0
    assert first["comparison_report"]["known_family_baseline_before"] == first["comparison_report"]["known_family_baseline_after"]
    assert first["comparison_report"]["known_family_baseline_before"]["synthetic_exact_count"] == 41
    assert first["comparison_report"]["known_family_baseline_before"]["synthetic_partial_count"] == 3
    assert first["comparison_report"]["known_family_baseline_before"]["synthetic_unsupported_count"] == 4
    assert first["comparison_report"]["known_family_baseline_before"]["synthetic_failed_count"] == 0


def test_top2_packets_validate_are_distinct_and_train_only_is_enforced() -> None:
    result = _search_result(seed=20260625)
    assert result["solver_visible_expected_outputs_absent"] is True
    assert result["evaluation_outputs_separated"] is True
    for task_result in result["heldout_task_results"]:
        assert task_result["task_packet"].get("expected_outputs") is None
        assert task_result["task_packet"].get("answer_key") is None
        assert task_result["task_packet"].get("solution") is None
        assert task_result["task_packet"].get("test_output") is None
        assert task_result["search_trace"]["heldout_evaluation_delay"] is True
        assert task_result["selected_top2_program_packet_validation"]["valid"] is True
        attempts = task_result["selected_top2_program_packet"]["attempts"]
        assert attempts[0]["metadata"]["program_signature_key"] != attempts[1]["metadata"]["program_signature_key"]
        assert attempts[0]["metadata"]["candidate_program_id"] != attempts[1]["metadata"]["candidate_program_id"]
        assert attempts[0]["metadata"]["selected_rank"] == 1
        assert attempts[1]["metadata"]["selected_rank"] == 2
        assert attempts[0]["metadata"]["program_signature_key"]
        assert attempts[1]["metadata"]["program_signature_key"]


def test_only_validated_typed_signatures_are_used_and_unsafe_signatures_reject() -> None:
    catalog = build_arc_style_typed_primitive_signature_catalog_v1()
    assert set(catalog.keys()) == set(EXPECTED_PRIMITIVE_NAMES_V1)
    assert all(validate_arc_style_typed_primitive_signature_v1(signature)["valid"] for signature in catalog.values())
    mutated = deepcopy(catalog["copy_grid"])
    mutated["leakage_flags"]["uses_public_arc_kaggle_data"] = True
    validation = validate_arc_style_typed_primitive_signature_v1(mutated)
    assert validation["valid"] is False
    assert "unsafe_leakage_flag" in " ".join(validation["blocked_reason_labels"])
    result = _search_result(seed=20260625)
    primitive_names = set()
    for packet in result["candidate_program_packets"]:
        for step in packet.get("program_steps", []):
            primitive_names.add(step["primitive_name"])
    assert primitive_names.issubset(set(EXPECTED_PRIMITIVE_NAMES_V1))


def test_failure_ledger_is_deterministic_and_json_safe() -> None:
    result = _search_result(seed=20260625)
    again = _search_result(seed=20260625)
    assert _json_safe(result["failure_ledger"]) == _json_safe(again["failure_ledger"])
    assert json.dumps(_json_safe(result["failure_ledger"]), ensure_ascii=False)
    assert result["comparison_report"]["heldout_baseline_before"]["unsupported_count"] == 11
    assert result["comparison_report"]["search_failure_ledger"]["status_counts"]["exact"] == 5


def test_known_family_baseline_remains_stable_and_summary_json_safe() -> None:
    baseline = _baseline_result(seed=20260625)
    solver_suite = _solver_suite_result()
    solver_summary = summarize_arc_style_synthetic_solver_suite_result_v1(solver_suite)
    assert baseline["known_family_baseline_summary"]["synthetic_exact_count"] == 41
    assert baseline["known_family_baseline_summary"]["synthetic_partial_count"] == 3
    assert baseline["known_family_baseline_summary"]["synthetic_unsupported_count"] == 4
    assert baseline["known_family_baseline_summary"]["synthetic_failed_count"] == 0
    assert solver_summary["synthetic_exact_count"] == 41
    assert solver_summary["synthetic_partial_count"] == 3
    assert solver_summary["synthetic_unsupported_count"] == 4
    assert solver_summary["synthetic_failed_count"] == 0
    assert json.dumps(_json_safe(_search_result(seed=20260625)["comparison_report"]), ensure_ascii=False)


def test_invalid_grids_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    from weslr import arc_style_depth2_compositional_program_search as search_module

    suite = generate_arc_style_heldout_compositional_suite_v1(seed=20260625)
    broken_suite = deepcopy(suite)
    broken_suite["tasks"][0]["task_packet"]["train_pairs"][0]["input_grid"][0][0] = True
    monkeypatch.setattr(search_module, "generate_arc_style_heldout_compositional_suite_v1", lambda seed=None: broken_suite)
    result = search_module.run_arc_style_depth2_compositional_program_search_v1(seed=20260625)
    assert result["heldout_task_results"][0]["heldout_fit_status"] == "failed"
    assert "invalid_task_packet_or_train_pairs" in result["heldout_task_results"][0]["failure_notes"]


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.arc_style_depth2_compositional_program_search", fromlist=["*"])
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
    assert "respond_chat(" not in source
    assert "chat_responder." not in source
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()
    assert "requests." not in source
