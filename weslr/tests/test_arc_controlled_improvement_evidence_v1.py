from __future__ import annotations

import ast
import inspect
import json
from functools import lru_cache
from typing import Any

from weslr.arc_controlled_improvement_evidence import (
    CHAIN_TYPE_V1,
    EVIDENCE_TYPE_V1,
    build_arc_controlled_improvement_evidence_chain_v1,
    build_arc_controlled_improvement_evidence_fixtures_v1,
    build_arc_controlled_improvement_evidence_fixture_depth2_compositional_search_v1,
    build_arc_controlled_improvement_evidence_fixture_heldout_baseline_v1,
    build_arc_controlled_improvement_evidence_fixture_partial_to_exact_repair_v1,
    build_arc_controlled_improvement_evidence_fixture_primitive_executor_expansion_v1,
    build_arc_controlled_improvement_evidence_packet_v1,
    summarize_arc_controlled_improvement_evidence_chain_v1,
    summarize_arc_controlled_improvement_evidence_v1,
    summarize_boundary_preservation_v1,
    summarize_heldout_compositional_improvement_v1,
    summarize_known_family_improvement_v1,
    summarize_remaining_gaps_v1,
    to_arc_controlled_improvement_evidence_json_safe_v1,
    validate_arc_controlled_improvement_evidence_chain_v1,
    validate_arc_controlled_improvement_evidence_packet_v1,
)
from weslr.arc_style_depth2_compositional_program_search import run_arc_style_depth2_compositional_program_search_v1
from weslr.arc_style_heldout_compositional_baseline import run_arc_style_heldout_compositional_baseline_v1
from weslr.arc_style_synthetic_solver_suite import run_arc_style_synthetic_solver_suite_v1


@lru_cache(maxsize=2)
def _solver_suite_result() -> dict[str, Any]:
    return run_arc_style_synthetic_solver_suite_v1()


@lru_cache(maxsize=2)
def _baseline_result() -> dict[str, Any]:
    return run_arc_style_heldout_compositional_baseline_v1(seed=20260625)


@lru_cache(maxsize=2)
def _search_result() -> dict[str, Any]:
    return run_arc_style_depth2_compositional_program_search_v1(seed=20260625)


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

FORBIDDEN_DOC_TERMS = (
    "agi",
    "kaggle-ready",
    "public benchmark score",
    "autonomous self-improvement",
    "self-modifying intelligence",
    "guaranteed generalization",
    "sentience",
    "consciousness",
)


def _json_safe(value: Any) -> Any:
    safe = to_arc_controlled_improvement_evidence_json_safe_v1(value)
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


def test_fixtures_validate_and_summarize_correctly() -> None:
    fixtures = build_arc_controlled_improvement_evidence_fixtures_v1()
    assert set(fixtures.keys()) == {
        "known_family_primitive_executor_expansion",
        "known_family_partial_to_exact_repair",
        "heldout_baseline",
        "heldout_depth2_compositional_search",
    }

    primitive_expansion = fixtures["known_family_primitive_executor_expansion"]
    partial_to_exact = fixtures["known_family_partial_to_exact_repair"]
    heldout_baseline = fixtures["heldout_baseline"]
    depth2_search = fixtures["heldout_depth2_compositional_search"]

    for packet in fixtures.values():
        validation = validate_arc_controlled_improvement_evidence_packet_v1(packet)
        summary = summarize_arc_controlled_improvement_evidence_v1(packet)
        assert validation["valid"] is True
        assert summary["valid"] is True
        assert packet["evidence_type"] == EVIDENCE_TYPE_V1
        assert packet["boundary_flags"]["synthetic_only"] is True
        assert packet["non_claim_flags"]["public_arc_data_claimed"] is False

    known_summary = summarize_known_family_improvement_v1(partial_to_exact)
    assert known_summary["summary_type"] == "known_family_improvement_summary_v1"
    assert known_summary["exact_gain"] == 27
    assert known_summary["unsupported_reduction"] == 0

    heldout_summary = summarize_heldout_compositional_improvement_v1(depth2_search)
    assert heldout_summary["summary_type"] == "heldout_compositional_improvement_summary_v1"
    assert heldout_summary["exact_gain"] == 11
    assert heldout_summary["unsupported_reduction"] == 11

    boundary_summary = summarize_boundary_preservation_v1(depth2_search)
    assert boundary_summary["boundary_preserved"] is True
    assert boundary_summary["non_claim_safe"] is True

    gap_summary = summarize_remaining_gaps_v1(depth2_search)
    assert gap_summary["remaining_partial_count"] == 2
    assert gap_summary["remaining_unsupported_count"] == 0

    assert primitive_expansion["evidence_summary"]["unsupported_reduction"] == 24
    assert partial_to_exact["evidence_summary"]["exact_delta"] == 27
    assert heldout_baseline["evidence_summary"]["exact_delta"] == 0
    assert depth2_search["evidence_summary"]["exact_delta"] == 11
    assert depth2_search["delta_metrics"]["unsupported_count"] == -11


def test_chain_summary_and_validation_are_correct() -> None:
    chain = build_arc_controlled_improvement_evidence_chain_v1()
    validation = validate_arc_controlled_improvement_evidence_chain_v1(chain)
    summary = summarize_arc_controlled_improvement_evidence_chain_v1(chain)
    assert chain["chain_type"] == CHAIN_TYPE_V1
    assert validation["valid"] is True
    assert summary["valid"] is True
    assert summary["known_family_exact_gain"] == 27
    assert summary["heldout_exact_gain"] == 11
    assert summary["heldout_unsupported_reduction"] == 11
    assert chain["summary"]["known_family_exact_gain"] == 27
    assert chain["summary"]["heldout_exact_gain"] == 11
    assert chain["summary"]["heldout_unsupported_reduction"] == 11


def test_validator_rejects_missing_metrics_invalid_totals_and_unsafe_flags() -> None:
    packet = build_arc_controlled_improvement_evidence_fixture_depth2_compositional_search_v1()

    missing = _json_safe(packet)
    del missing["after_metrics"]["task_count"]
    validation = validate_arc_controlled_improvement_evidence_packet_v1(missing)
    assert validation["valid"] is False
    assert any(label.startswith("after_metrics_missing") for label in validation["blocked_reason_labels"])

    invalid_total = _json_safe(packet)
    invalid_total["baseline_metrics"]["task_count"] = 99
    validation = validate_arc_controlled_improvement_evidence_packet_v1(invalid_total)
    assert validation["valid"] is False
    assert "baseline_metrics_total_mismatch" in validation["blocked_reason_labels"]

    unsafe_boundary = _json_safe(packet)
    unsafe_boundary["boundary_flags"]["no_runtime_wiring"] = False
    validation = validate_arc_controlled_improvement_evidence_packet_v1(unsafe_boundary)
    assert validation["valid"] is False
    assert "unsafe_boundary_flag:no_runtime_wiring" in validation["blocked_reason_labels"]

    unsafe_claim = _json_safe(packet)
    unsafe_claim["non_claim_flags"]["kaggle_ready_claimed"] = True
    validation = validate_arc_controlled_improvement_evidence_packet_v1(unsafe_claim)
    assert validation["valid"] is False
    assert "unsafe_non_claim_flag:kaggle_ready_claimed" in validation["blocked_reason_labels"]


def test_metric_totals_and_deltas_are_checked() -> None:
    packet = build_arc_controlled_improvement_evidence_packet_v1(
        lane_name="custom_lane_v1",
        intervention_type="measurement_only",
        baseline_metrics={"exact_count": 2, "partial_count": 1, "unsupported_count": 0, "failed_count": 0, "task_count": 3},
        after_metrics={"exact_count": 3, "partial_count": 0, "unsupported_count": 0, "failed_count": 0, "task_count": 3},
        next_lane_recommendation="IMPLEMENT_ARC_DEPTH2_REMAINING_FAILURE_REPAIR_V1",
    )
    validation = validate_arc_controlled_improvement_evidence_packet_v1(packet)
    summary = summarize_arc_controlled_improvement_evidence_v1(packet)
    assert validation["valid"] is True
    assert summary["exact_delta"] == 1
    assert summary["unsupported_delta"] == 0
    assert packet["delta_metrics"]["exact_count"] == 1
    assert packet["delta_metrics"]["task_count"] == 0


def test_json_safe_export_contains_no_callable_objects_and_helpers_are_deterministic() -> None:
    packet = build_arc_controlled_improvement_evidence_fixture_primitive_executor_expansion_v1()
    chain = build_arc_controlled_improvement_evidence_chain_v1()
    safe_packet = _json_safe(packet)
    safe_chain = _json_safe(chain)
    assert _contains_callable(safe_packet) is False
    assert _contains_callable(safe_chain) is False
    assert json.dumps(safe_packet, ensure_ascii=False)
    assert json.dumps(safe_chain, ensure_ascii=False)
    assert safe_packet["evidence_type"] == EVIDENCE_TYPE_V1
    assert safe_chain["chain_type"] == CHAIN_TYPE_V1
    assert build_arc_controlled_improvement_evidence_chain_v1() == build_arc_controlled_improvement_evidence_chain_v1()


def test_helper_does_not_change_solver_behavior() -> None:
    before_suite = _solver_suite_result()
    before_baseline = _baseline_result()
    before_search = _search_result()

    _ = build_arc_controlled_improvement_evidence_chain_v1()
    _ = build_arc_controlled_improvement_evidence_fixtures_v1()

    after_suite = _solver_suite_result()
    after_baseline = _baseline_result()
    after_search = _search_result()

    assert _json_safe(before_suite) == _json_safe(after_suite)
    assert _json_safe(before_baseline) == _json_safe(after_baseline)
    assert _json_safe(before_search) == _json_safe(after_search)


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.arc_controlled_improvement_evidence", fromlist=["*"])
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
    assert "write(" not in source.lower()
    assert "open(" not in source.lower()


def test_document_avoids_forbidden_claim_terms() -> None:
    with open("/data/data/com.termux/files/home/weslr-pr47-clean/docs/WESLR_ARC_CONTROLLED_IMPROVEMENT_EVIDENCE_V1.md", "r", encoding="utf-8") as handle:
        doc = handle.read().lower()
    for term in FORBIDDEN_DOC_TERMS:
        assert term not in doc
