"""Shared hypothesis engine foundation V1.

Small, deterministic, and reusable. This module only provides lightweight
candidate structures plus exact train-consistency scoring and ranking helpers.
It does not know about public ARC data, scoring, or submission writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from weslr.arc_object_extraction_v1 import validate_grid_v1


@dataclass(frozen=True)
class HypothesisCandidate:
    family: str
    confidence: float
    output: Any
    trace: dict[str, Any] = field(default_factory=dict)
    train_fit: bool = False
    rejection_reason: str | None = None
    candidate_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "confidence": float(self.confidence),
            "output": self.output,
            "trace": dict(self.trace),
            "train_fit": bool(self.train_fit),
            "rejection_reason": self.rejection_reason,
            "candidate_id": self.candidate_id,
        }


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _json_safe_trace(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe_trace(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe_trace(item) for item in value]
    if isinstance(value, list):
        return [_json_safe_trace(item) for item in value]
    if isinstance(value, set):
        return [_json_safe_trace(item) for item in sorted(value, key=repr)]
    return _safe_text(value)


def score_train_consistency(
    train_pairs: Sequence[Mapping[str, Any]],
    executor: Callable[[Mapping[str, Any]], Any],
    *,
    family: str,
    confidence: float = 1.0,
    candidate_id: str = "",
    trace: Mapping[str, Any] | None = None,
) -> HypothesisCandidate:
    """Execute a hypothesis against all train pairs and require exact match.

    The executor receives the full train pair and must return the predicted output
    for that pair. The returned candidate keeps trace metadata compact and does
    not include train outputs.
    """
    evaluations: list[dict[str, Any]] = []
    for index, pair in enumerate(train_pairs):
        try:
            predicted = executor(pair)
        except Exception as exc:  # pragma: no cover - explicit failure path
            compact_trace = dict(trace or {})
            compact_trace["train_evaluations"] = evaluations
            compact_trace["failure_index"] = index
            compact_trace["failure_kind"] = type(exc).__name__
            return HypothesisCandidate(
                family=family,
                confidence=float(confidence),
                output=None,
                trace=_json_safe_trace(compact_trace),
                train_fit=False,
                rejection_reason=f"executor_exception:{type(exc).__name__}",
                candidate_id=candidate_id,
            )

        expected = validate_grid_v1(pair.get("output", pair.get("output_grid")))
        predicted_grid = validate_grid_v1(predicted)
        matched = predicted_grid == expected
        evaluations.append(
            {
                "pair_index": index,
                "matched": matched,
                "input_shape": [len(validate_grid_v1(pair.get("input", pair.get("input_grid")))), len(validate_grid_v1(pair.get("input", pair.get("input_grid")))[0])],
                "output_shape": [len(expected), len(expected[0])],
            }
        )
        if not matched:
            compact_trace = dict(trace or {})
            compact_trace["train_evaluations"] = evaluations
            compact_trace["failure_index"] = index
            compact_trace["failure_kind"] = "train_mismatch"
            return HypothesisCandidate(
                family=family,
                confidence=float(confidence),
                output=None,
                trace=_json_safe_trace(compact_trace),
                train_fit=False,
                rejection_reason=f"train_mismatch:{index}",
                candidate_id=candidate_id,
            )

    compact_trace = dict(trace or {})
    compact_trace["train_evaluations"] = evaluations
    compact_trace["train_consistent"] = True
    return HypothesisCandidate(
        family=family,
        confidence=float(confidence),
        output=None,
        trace=_json_safe_trace(compact_trace),
        train_fit=True,
        rejection_reason=None,
        candidate_id=candidate_id,
    )


def rank_hypotheses(candidates: Sequence[HypothesisCandidate | Mapping[str, Any]]) -> list[HypothesisCandidate]:
    """Deterministically rank hypotheses.

    Accepted candidates come first, then higher confidence, then family name,
    then input order for stability.
    """
    normalized: list[HypothesisCandidate] = []
    for index, candidate in enumerate(candidates):
        if isinstance(candidate, HypothesisCandidate):
            normalized.append(candidate)
            continue
        normalized.append(
            HypothesisCandidate(
                family=_safe_text(candidate.get("family"), f"candidate_{index}"),
                confidence=float(candidate.get("confidence", 0.0) or 0.0),
                output=candidate.get("output"),
                trace=dict(candidate.get("trace", {})) if isinstance(candidate.get("trace"), Mapping) else {},
                train_fit=bool(candidate.get("train_fit", False)),
                rejection_reason=candidate.get("rejection_reason"),
                candidate_id=_safe_text(candidate.get("candidate_id"), f"candidate_{index}"),
            )
        )

    indexed = list(enumerate(normalized))
    indexed.sort(
        key=lambda item: (
            0 if item[1].train_fit else 1,
            -float(item[1].confidence),
            _safe_text(item[1].family),
            _safe_text(item[1].candidate_id),
            item[0],
        )
    )
    return [candidate for _, candidate in indexed]


__all__ = ["HypothesisCandidate", "rank_hypotheses", "score_train_consistency"]
