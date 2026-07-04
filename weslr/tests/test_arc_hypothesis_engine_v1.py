from __future__ import annotations

import json

from weslr.arc_hypothesis_engine_v1 import HypothesisCandidate, rank_hypotheses, score_train_consistency


def _train_pairs() -> list[dict[str, object]]:
    return [
        {"input": [[1, 0], [0, 0]], "output": [[1, 0], [0, 0]]},
        {"input": [[0, 1], [0, 0]], "output": [[0, 1], [0, 0]]},
    ]


def test_accepts_exact_match_candidate() -> None:
    candidate = score_train_consistency(
        _train_pairs(),
        lambda pair: pair["input"],
        family="copy",
        confidence=1.0,
        trace={"family": "copy"},
    )
    assert candidate.train_fit is True
    assert candidate.rejection_reason is None
    assert candidate.family == "copy"


def test_rejects_train_mismatch() -> None:
    candidate = score_train_consistency(
        _train_pairs(),
        lambda pair: [[0, 0], [0, 0]],
        family="bad_copy",
        confidence=0.5,
        trace={"family": "bad_copy"},
    )
    assert candidate.train_fit is False
    assert candidate.rejection_reason is not None
    assert candidate.trace["failure_kind"] == "train_mismatch"


def test_ranks_accepted_before_rejected() -> None:
    accepted = HypothesisCandidate(family="alpha", confidence=0.4, output=[[1]], train_fit=True)
    rejected = HypothesisCandidate(family="beta", confidence=1.0, output=[[2]], train_fit=False, rejection_reason="nope")
    ranked = rank_hypotheses([rejected, accepted])
    assert [candidate.family for candidate in ranked] == ["alpha", "beta"]


def test_deterministic_order_across_repeated_runs() -> None:
    candidates = [
        HypothesisCandidate(family="zeta", confidence=0.5, output=[[1]], train_fit=True, candidate_id="z"),
        HypothesisCandidate(family="alpha", confidence=0.5, output=[[1]], train_fit=True, candidate_id="a"),
        HypothesisCandidate(family="beta", confidence=0.3, output=[[1]], train_fit=False, rejection_reason="bad", candidate_id="b"),
    ]
    first = [candidate.family for candidate in rank_hypotheses(candidates)]
    second = [candidate.family for candidate in rank_hypotheses(candidates)]
    assert first == second == ["alpha", "zeta", "beta"]


def test_trace_does_not_include_expected_output_grids() -> None:
    candidate = score_train_consistency(
        _train_pairs(),
        lambda pair: pair["input"],
        family="copy",
        confidence=1.0,
        trace={"labels": ["safe"]},
    )
    blob = json.dumps(candidate.trace, sort_keys=True).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob
    assert "answer_key" not in blob
