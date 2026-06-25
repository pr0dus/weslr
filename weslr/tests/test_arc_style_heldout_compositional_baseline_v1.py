from __future__ import annotations

import ast
import inspect
import json
from typing import Any

from weslr.arc_style_heldout_compositional_baseline import (
    BASELINE_TYPE_V1,
    run_arc_style_heldout_compositional_baseline_v1,
    summarize_arc_style_heldout_compositional_baseline_result_v1,
    to_arc_style_heldout_compositional_baseline_json_safe_v1,
    validate_arc_style_heldout_compositional_baseline_result_v1,
)
from weslr.arc_style_heldout_compositional_synthetic_generator import HELDOUT_RECIPE_FAMILIES_V1
from weslr.arc_style_synthetic_solver_suite import run_arc_style_synthetic_solver_suite_v1, summarize_arc_style_synthetic_solver_suite_result_v1

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
    safe = to_arc_style_heldout_compositional_baseline_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def _contains_callable(value: Any) -> bool:
    if callable(value):
        return True
    if isinstance(value, dict):
        return any(_contains_callable(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_callable(item) for item in value)
    return False


def test_baseline_run_is_deterministic_and_json_safe() -> None:
    first = run_arc_style_heldout_compositional_baseline_v1(seed=20260625)
    second = run_arc_style_heldout_compositional_baseline_v1(seed=20260625)
    assert _json_safe(first) == _json_safe(second)
    assert json.dumps(_json_safe(first), ensure_ascii=False)
    validation = validate_arc_style_heldout_compositional_baseline_result_v1(first)
    summary = summarize_arc_style_heldout_compositional_baseline_result_v1(first)
    assert validation["valid"] is True
    assert summary["valid"] is True
    assert first["baseline_type"] == BASELINE_TYPE_V1
    assert first["task_count"] == 14
    assert first["exact_count"] == 1
    assert first["partial_count"] == 2
    assert first["unsupported_count"] == 11
    assert first["failed_count"] == 0
    assert summary["task_count"] == 14
    assert summary["exact_count"] == 1
    assert summary["partial_count"] == 2
    assert summary["unsupported_count"] == 11
    assert summary["failed_count"] == 0
    assert summary["top2_packet_count"] == 14
    assert summary["top2_packet_valid_count"] == 14
    assert summary["top2_packet_invalid_count"] == 0


def test_per_recipe_summary_exists_and_counts_sum_correctly() -> None:
    result = run_arc_style_heldout_compositional_baseline_v1(seed=123)
    per_recipe = result["per_recipe_summary"]
    assert set(per_recipe.keys()) == set(HELDOUT_RECIPE_FAMILIES_V1)
    assert all(summary["task_count"] == 2 for summary in per_recipe.values())
    assert all(summary["top2_packet_count"] == 2 for summary in per_recipe.values())
    assert sum(summary["exact_count"] for summary in per_recipe.values()) == result["exact_count"]
    assert sum(summary["partial_count"] for summary in per_recipe.values()) == result["partial_count"]
    assert sum(summary["unsupported_count"] for summary in per_recipe.values()) == result["unsupported_count"]
    assert sum(summary["failed_count"] for summary in per_recipe.values()) == result["failed_count"]
    assert result["exact_count"] + result["partial_count"] + result["unsupported_count"] + result["failed_count"] == result["task_count"]


def test_top2_packets_validate_and_evaluation_outputs_stay_separate() -> None:
    result = run_arc_style_heldout_compositional_baseline_v1(seed=7)
    assert result["top2_packet_valid_count"] == result["top2_packet_count"] == 14
    for task_result in result["heldout_task_results"]:
        assert task_result["top2_packet_validation"]["valid"] is True
        assert task_result["task_packet"]["trace"]["heldout_compositional"] is True
        assert task_result["task_packet"]["trace"]["solver_visible_expected_outputs_absent"] is True
        assert "expected_outputs" not in task_result["task_packet"]
        assert "answer_key" not in task_result["task_packet"]
        assert "solution" not in task_result["task_packet"]
        assert "test_output" not in task_result["task_packet"]
        assert task_result["evaluation_metadata"]["expected_outputs"]
        assert task_result["evaluation_metadata"]["solver_visible_expected_outputs_absent"] is True
        assert task_result["solver_visible_expected_outputs_absent"] is True
        assert task_result["evaluation_outputs_separated"] is True


def test_failure_ledger_is_json_safe_and_leakage_flags_are_safe() -> None:
    result = run_arc_style_heldout_compositional_baseline_v1(seed=88)
    ledger = result["failure_ledger"]
    assert json.dumps(_json_safe(ledger), ensure_ascii=False)
    assert result["leakage_flags"]["synthetic_only"] is True
    assert result["leakage_flags"]["uses_public_arc_data"] is False
    assert result["leakage_flags"]["uses_kaggle_data"] is False
    assert result["leakage_flags"]["uses_answer_key"] is False
    assert result["boundary_flags"]["metadata_only"] is True
    assert result["boundary_flags"]["no_public_arc_data"] is True
    assert result["boundary_flags"]["no_kaggle_data"] is True
    assert result["known_family_baseline_summary"]["synthetic_exact_count"] == 41
    assert result["known_family_baseline_summary"]["synthetic_partial_count"] == 3
    assert result["known_family_baseline_summary"]["synthetic_unsupported_count"] == 4
    assert result["known_family_baseline_summary"]["synthetic_failed_count"] == 0


def test_known_family_solver_suite_remains_unchanged() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    summary = summarize_arc_style_synthetic_solver_suite_result_v1(result)
    assert summary["synthetic_exact_count"] == 41
    assert summary["synthetic_partial_count"] == 3
    assert summary["synthetic_unsupported_count"] == 4
    assert summary["synthetic_failed_count"] == 0


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.arc_style_heldout_compositional_baseline", fromlist=["*"])
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
    assert "open(" not in source.lower()
