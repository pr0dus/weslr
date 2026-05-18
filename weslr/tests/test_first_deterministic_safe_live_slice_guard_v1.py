"""Tests for first deterministic-safe live slice guard V1.

Metadata-only guard tests. No runtime chat path execution, no provider calls, no
feature flag enablement outside scoped env dictionaries, and no persistence.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from weslr.first_deterministic_safe_live_slice_guard_v1 import (  # noqa: E402
    CANDIDATE_FAMILY_V1,
    CANDIDATE_PROMPT_ID_V1,
    CANDIDATE_ROUTE_CLASS_V1,
    FEATURE_FLAG_ENV_V1,
    FORBIDDEN_OUTPUT_KEYS_V1,
    evaluate_first_deterministic_safe_live_slice_guard_v1,
)


ENABLED_ENV = {FEATURE_FLAG_ENV_V1: "1"}


def _candidate_item(**overrides):
    item = {
        "prompt_id": CANDIDATE_PROMPT_ID_V1,
        "family": CANDIDATE_FAMILY_V1,
        "requires_model_call": False,
        "requires_search": False,
        "requires_memory_write": False,
    }
    item.update(overrides)
    return item


def _validator_result(**overrides):
    result = {
        "route_class": CANDIDATE_ROUTE_CLASS_V1,
        "routing_validator_applied": True,
        "alignment_status": "aligned",
        "safe_to_call": True,
        "requires_mock": False,
        "blocked_by_boundary": False,
        "model_calls": False,
        "search_calls": False,
        "advisor_calls": False,
        "writes": False,
        "raw_text_retained": False,
        "reason_labels": [],
    }
    result.update(overrides)
    return result


def _evaluate(item=None, validator=None, env=None):
    return evaluate_first_deterministic_safe_live_slice_guard_v1(
        _candidate_item() if item is None else item,
        _validator_result() if validator is None else validator,
        ENABLED_ENV if env is None else env,
    )


def _assert_blocked(result, reason):
    assert result["allowed"] is False
    assert reason in result["block_reason_labels"]


class TestFeatureFlagBehavior:
    def test_flag_absent_blocks(self):
        result = _evaluate(env={})
        _assert_blocked(result, "feature_flag_disabled")
        assert result["feature_flag_enabled"] is False

    def test_flag_empty_blocks(self):
        result = _evaluate(env={FEATURE_FLAG_ENV_V1: ""})
        _assert_blocked(result, "feature_flag_disabled")

    def test_false_like_flags_block(self):
        for value in ["0", "false", "False", "FALSE", "no", "off"]:
            result = _evaluate(env={FEATURE_FLAG_ENV_V1: value})
            _assert_blocked(result, "feature_flag_disabled")

    def test_non_exact_flag_blocks(self):
        result = _evaluate(env={FEATURE_FLAG_ENV_V1: "true"})
        _assert_blocked(result, "feature_flag_not_exact_1")

    def test_exact_flag_allows_only_exact_candidate(self):
        result = _evaluate()
        assert result["allowed"] is True
        assert result["feature_flag_enabled"] is True
        assert result["prompt_id"] == CANDIDATE_PROMPT_ID_V1
        assert result["family"] == CANDIDATE_FAMILY_V1
        assert result["route_class"] == CANDIDATE_ROUTE_CLASS_V1
        assert result["block_reason_labels"] == []


class TestCandidateMismatchBlocks:
    def test_wrong_prompt_blocks(self):
        result = _evaluate(item=_candidate_item(prompt_id="ordinary_task_behavior_002"))
        _assert_blocked(result, "prompt_id_mismatch")

    def test_wrong_family_blocks(self):
        result = _evaluate(item=_candidate_item(family="conduct_alignment"))
        _assert_blocked(result, "family_mismatch")

    def test_wrong_route_blocks(self):
        result = _evaluate(validator=_validator_result(route_class="safe_limited_ordinary_task"))
        _assert_blocked(result, "route_class_mismatch")


class TestUnsafeRouteBlocks:
    def test_requires_mock_route_blocks(self):
        result = _evaluate(
            validator=_validator_result(
                route_class="requires_generate_chat_mock",
                requires_mock=True,
            )
        )
        _assert_blocked(result, "requires_mock_true")
        assert "forbidden_route_class:requires_generate_chat_mock" in result["block_reason_labels"]
        assert "generate_path_reachable" in result["block_reason_labels"]

    def test_forbidden_model_path_blocks(self):
        result = _evaluate(
            validator=_validator_result(
                route_class="forbidden_model_path",
                alignment_status="mismatch",
                safe_to_call=False,
                reason_labels=["model_path_blocked"],
            )
        )
        _assert_blocked(result, "forbidden_route_class:forbidden_model_path")
        assert "model_path_reachable" in result["block_reason_labels"]

    def test_forbidden_search_or_advisor_path_blocks(self):
        result = _evaluate(
            validator=_validator_result(
                route_class="forbidden_search_or_advisor_path",
                alignment_status="blocked_by_boundary",
                safe_to_call=False,
                search_calls=True,
                reason_labels=["search_path_blocked"],
            )
        )
        _assert_blocked(result, "forbidden_route_class:forbidden_search_or_advisor_path")
        assert "source_currentness_search_status_or_advisor_path_detected" in result["block_reason_labels"]

    def test_ambiguous_needs_review_blocks(self):
        result = _evaluate(validator=_validator_result(route_class="ambiguous_needs_review"))
        _assert_blocked(result, "route_class_mismatch")
        assert "forbidden_route_class:ambiguous_needs_review" in result["block_reason_labels"]

    def test_blocked_family_blocks(self):
        result = _evaluate(
            item=_candidate_item(family="memory_honesty"),
            validator=_validator_result(
                alignment_status="blocked_by_boundary",
                safe_to_call=False,
                blocked_by_boundary=True,
                reason_labels=["unsupported_family_blocked"],
            ),
        )
        _assert_blocked(result, "family_mismatch")
        assert "blocked_family_or_boundary_detected" in result["block_reason_labels"]


class TestRequiredGuardChecks:
    def test_routing_validator_missing_blocks(self):
        result = _evaluate(validator=_validator_result(routing_validator_applied=False))
        _assert_blocked(result, "routing_validator_not_applied_first")

    def test_alignment_not_aligned_blocks(self):
        result = _evaluate(validator=_validator_result(alignment_status="mismatch"))
        _assert_blocked(result, "alignment_not_aligned")

    def test_safe_to_call_false_blocks(self):
        result = _evaluate(validator=_validator_result(safe_to_call=False))
        _assert_blocked(result, "safe_to_call_false")

    def test_model_path_reachable_marker_blocks(self):
        result = _evaluate(validator=_validator_result(model_calls=True))
        _assert_blocked(result, "model_path_reachable")

    def test_generate_path_reachable_marker_blocks(self):
        result = _evaluate(validator=_validator_result(generate_chat_reachable=True))
        _assert_blocked(result, "generate_path_reachable")

    def test_write_risk_blocks(self):
        result = _evaluate(validator=_validator_result(writes=True))
        _assert_blocked(result, "write_path_risk_detected")

    def test_raw_retention_risk_blocks(self):
        result = _evaluate(validator=_validator_result(raw_text_retained=True))
        _assert_blocked(result, "raw_retention_risk_detected")

    def test_dot_weslr_write_risk_blocks(self):
        result = _evaluate(validator=_validator_result(dot_weslr_write_risk=True))
        _assert_blocked(result, "dot_weslr_write_risk_detected")


class TestMetadataOnlyReturn:
    def test_return_is_metadata_only(self):
        result = _evaluate()
        assert result["first_deterministic_safe_live_slice_guard_applied"] is True
        assert result["model_calls"] is False
        assert result["search_calls"] is False
        assert result["advisor_calls"] is False
        assert result["writes"] is False
        assert result["raw_text_retained"] is False

    def test_forbidden_keys_absent(self):
        result = _evaluate()
        assert not (set(result) & FORBIDDEN_OUTPUT_KEYS_V1)

    def test_forbidden_validator_keys_block_but_are_not_returned(self):
        result = _evaluate(validator=_validator_result(response_text="not returned"))
        _assert_blocked(result, "raw_retention_risk_detected")
        assert "response_text" not in result


class TestSourceSafety:
    def test_helper_source_does_not_import_or_call_forbidden_runtime_paths(self):
        helper_path = _repo_root / "weslr" / "first_deterministic_safe_live_slice_guard_v1.py"
        source = helper_path.read_text(encoding="utf-8")
        forbidden_patterns = [
            r"^\s*from\s+.*chat_responder\s+import",
            r"^\s*import\s+.*chat_responder",
            r"^\s*from\s+.*llm_runtime\s+import",
            r"^\s*import\s+.*llm_runtime",
            r"\bChatResponder\s*\(",
            r"\brespond_chat\s*\(",
            r"\bgenerate_chat\s*\(",
        ]
        for pattern in forbidden_patterns:
            assert re.search(pattern, source, flags=re.MULTILINE) is None

    def test_no_dot_weslr_writes(self):
        before = set((_repo_root / ".weslr").rglob("*")) if (_repo_root / ".weslr").exists() else set()
        result = _evaluate()
        after = set((_repo_root / ".weslr").rglob("*")) if (_repo_root / ".weslr").exists() else set()
        assert result["writes"] is False
        assert before == after
