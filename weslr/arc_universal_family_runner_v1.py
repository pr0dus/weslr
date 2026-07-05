"""ARC-AGI-2 universal family runner V1.

Synthetic-only top-2 runner that connects task signatures, primitive discovery,
family discovery, compositional execution, and the existing capability candidate
aggregator.

No public ARC ingestion. No scoring claims. No submission writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_capability_candidate_aggregator_v1 import build_arc_agi2_capability_candidate_top2_attempt_packet_v1
from weslr.arc_compositional_executor_v1 import CompositionalExecutorCandidate, execute_compositional_family_hypotheses
from weslr.arc_family_discovery_engine_v1 import (
    COMPOSITION_FAMILY_ORDER_V1,
    FAMILY_PRIORITY_V1,
    FamilyDiscoveryResult,
    FamilyHypothesis,
    discover_families_for_task,
)
from weslr.arc_primitive_discovery_engine_v1 import discover_primitives_for_task
from weslr.arc_primitive_registry_v1 import build_arc_primitive_registry_v1
from weslr.arc_task_feature_signature_v1 import build_arc_task_feature_signature_v1

SCHEMA_VERSION_V1 = "ArcUniversalFamilyRunnerV1"
DEFAULT_TASK_ID_V1 = "arc_universal_family_runner_task"
HIGH_CONFIDENCE_UNCERTAIN_THRESHOLD_V1 = 0.8
FALLBACK_FAMILY_V1 = "fallback"

EXECUTABLE_FAMILY_ORDER_V1 = (
    "object_bbox",
    "shape_geometry",
    "color_role",
    "resize_tile",
    "count_quantity",
)

FAMILY_PRIORITY_WITH_FALLBACK_V1 = dict(FAMILY_PRIORITY_V1)
FAMILY_PRIORITY_WITH_FALLBACK_V1[FALLBACK_FAMILY_V1] = 999

COMPOSITION_TEMPLATES_V1 = set(COMPOSITION_FAMILY_ORDER_V1)


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    return _safe_text(value)


def _pair_input(pair: Mapping[str, Any]) -> Any:
    return pair.get("input", pair.get("input_grid"))


def _pair_output(pair: Mapping[str, Any]) -> Any:
    return pair.get("output", pair.get("output_grid"))


def _family_rank(family_name: str) -> int:
    return FAMILY_PRIORITY_WITH_FALLBACK_V1.get(_safe_text(family_name), 500)


def _train_fit(candidate: Mapping[str, Any] | UniversalRunnerCandidate) -> bool:
    if isinstance(candidate, UniversalRunnerCandidate):
        trace = candidate.trace if isinstance(candidate.trace, Mapping) else {}
        if "train_fit" in trace:
            return bool(trace.get("train_fit"))
        return False
    trace = candidate.get("trace") if isinstance(candidate.get("trace"), Mapping) else {}
    if "train_fit" in trace:
        return bool(trace.get("train_fit"))
    return bool(candidate.get("train_fit", False))


def _candidate_rank_key(candidate: Mapping[str, Any] | UniversalRunnerCandidate) -> tuple[Any, ...]:
    if isinstance(candidate, UniversalRunnerCandidate):
        trace = candidate.trace if isinstance(candidate.trace, Mapping) else {}
        source = _safe_text(candidate.source, "")
        family_name = _safe_text(candidate.family_name, "")
        confidence = float(candidate.confidence or 0.0)
        chain_length = len(candidate.primitive_chain)
        source_candidate_id = _safe_text(trace.get("source_candidate_id"), "")
    else:
        trace = candidate.get("trace") if isinstance(candidate.get("trace"), Mapping) else {}
        source = _safe_text(candidate.get("source"), "")
        family_name = _safe_text(candidate.get("family_name"), "")
        confidence = float(candidate.get("confidence", 0.0) or 0.0)
        chain_length = len(candidate.get("primitive_chain", [])) if isinstance(candidate.get("primitive_chain"), Sequence) else 99
        source_candidate_id = _safe_text(candidate.get("source_candidate_id"), "")
    return (
        0 if _train_fit(candidate if isinstance(candidate, Mapping) else {"trace": candidate.trace, "train_fit": candidate.trace.get("train_fit", False)}) else 1,
        -confidence,
        chain_length,
        _family_rank(family_name),
        0 if source == "compositional_executor" else 1 if source == "capability_aggregator" else 2,
        _safe_text(trace.get("execution_kind"), ""),
        family_name,
        source_candidate_id,
    )


def _candidate_grid_signature(candidate: Mapping[str, Any]) -> str:
    return repr(_json_safe(candidate.get("output")))


@dataclass(frozen=True)
class UniversalRunnerCandidate:
    family_name: str
    primitive_chain: tuple[str, ...]
    output: Any
    confidence: float
    rank: int
    source: str
    trace: dict[str, Any] = field(default_factory=dict)

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "family_name": _safe_text(self.family_name),
            "primitive_chain": [_safe_text(item) for item in self.primitive_chain],
            "output": _json_safe(self.output),
            "confidence": float(self.confidence),
            "rank": int(self.rank),
            "source": _safe_text(self.source),
            "trace": _json_safe(self.trace),
        }


@dataclass(frozen=True)
class UniversalRunnerResult:
    attempt_1: UniversalRunnerCandidate
    attempt_2: UniversalRunnerCandidate
    candidate_count: int
    family_discovery_summary: dict[str, Any]
    selected_family_names: tuple[str, ...]
    dedupe_count: int
    fallback_used: bool
    exact_two_output: bool
    trace: dict[str, Any] = field(default_factory=dict)

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "attempt_1": self.attempt_1.to_json_safe_dict(),
            "attempt_2": self.attempt_2.to_json_safe_dict(),
            "candidate_count": int(self.candidate_count),
            "family_discovery_summary": _json_safe(self.family_discovery_summary),
            "selected_family_names": [_safe_text(item) for item in self.selected_family_names],
            "dedupe_count": int(self.dedupe_count),
            "fallback_used": bool(self.fallback_used),
            "exact_two_output": bool(self.exact_two_output),
            "trace": _json_safe(self.trace),
        }


def _candidate_from_attempt(attempt: Mapping[str, Any], *, rank: int) -> UniversalRunnerCandidate:
    metadata = attempt.get("metadata") if isinstance(attempt.get("metadata"), Mapping) else {}
    family_name = _safe_text(metadata.get("source_family") or metadata.get("source_family_label") or metadata.get("source_kind") or "fallback")
    source = _safe_text(metadata.get("source_adapter") or metadata.get("adapter_name") or metadata.get("source_kind") or "capability_aggregator")
    trace = {
        "source_family": family_name,
        "source_family_label": _safe_text(metadata.get("source_family_label"), family_name),
        "source_adapter": source,
        "source_kind": _safe_text(metadata.get("source_kind"), family_name),
        "candidate_score": metadata.get("candidate_score"),
        "confidence_label": _safe_text(metadata.get("confidence_label"), _safe_text(attempt.get("confidence_label"), "unknown")),
        "rank": int(rank),
        "dedupe_reason": _safe_text(metadata.get("dedupe_reason"), ""),
        "duplicate_family_labels": _json_safe(metadata.get("duplicate_family_labels", [])),
        "duplicate_source_candidate_ids": _json_safe(metadata.get("duplicate_source_candidate_ids", [])),
        "selected_rank": metadata.get("selected_rank"),
        "train_fit": bool(metadata.get("train_fit", False)),
    }
    confidence = metadata.get("candidate_score")
    try:
        confidence_value = float(confidence)
    except Exception:
        confidence_value = 0.0
    return UniversalRunnerCandidate(
        family_name=family_name,
        primitive_chain=(_safe_text(metadata.get("solver_family") or metadata.get("source_family_label") or family_name),),
        output=attempt.get("grid"),
        confidence=confidence_value,
        rank=int(rank),
        source=source,
        trace=trace,
    )


def _candidate_from_compositional(candidate: CompositionalExecutorCandidate, *, rank: int) -> UniversalRunnerCandidate:
    trace = dict(candidate.trace)
    trace.setdefault("train_fit", bool(candidate.train_fit))
    trace.setdefault("execution_kind", "compositional_executor")
    return UniversalRunnerCandidate(
        family_name=_safe_text(candidate.family_name),
        primitive_chain=tuple(_safe_text(item) for item in candidate.primitive_chain),
        output=candidate.output,
        confidence=float(candidate.confidence),
        rank=int(rank),
        source="compositional_executor",
        trace=trace,
    )


def _build_safe_fallback_candidates(test_input: Any) -> list[UniversalRunnerCandidate]:
    grid = _json_safe(test_input)
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        grid = [[0]]
    fallback_trace = {
        "schema_version": SCHEMA_VERSION_V1,
        "family_name": FALLBACK_FAMILY_V1,
        "execution_kind": "safe_deterministic_fallback",
        "train_fit": False,
    }
    first = UniversalRunnerCandidate(
        family_name=FALLBACK_FAMILY_V1,
        primitive_chain=(FALLBACK_FAMILY_V1,),
        output=grid,
        confidence=0.0,
        rank=1,
        source=FALLBACK_FAMILY_V1,
        trace=dict(fallback_trace),
    )
    second = UniversalRunnerCandidate(
        family_name=FALLBACK_FAMILY_V1,
        primitive_chain=(FALLBACK_FAMILY_V1,),
        output=grid,
        confidence=0.0,
        rank=2,
        source=FALLBACK_FAMILY_V1,
        trace={**fallback_trace, "rank": 2},
    )
    return [first, second]


def _dedupe_candidates(candidates: Sequence[UniversalRunnerCandidate]) -> tuple[list[UniversalRunnerCandidate], int]:
    ordered = sorted(candidates, key=_candidate_rank_key)
    kept: list[UniversalRunnerCandidate] = []
    seen: dict[str, UniversalRunnerCandidate] = {}
    dedupe_count = 0
    for candidate in ordered:
        signature = _candidate_grid_signature(candidate.__dict__)
        if signature not in seen:
            seen[signature] = candidate
            kept.append(candidate)
            continue
        dedupe_count += 1
        primary = seen[signature]
        primary_trace = dict(primary.trace)
        duplicate_names = set(primary_trace.get("duplicate_family_names", []))
        duplicate_names.add(_safe_text(candidate.family_name))
        duplicate_names.add(_safe_text(primary.family_name))
        primary_trace["duplicate_family_names"] = sorted(name for name in duplicate_names if name)
        seen[signature] = UniversalRunnerCandidate(
            family_name=primary.family_name,
            primitive_chain=primary.primitive_chain,
            output=primary.output,
            confidence=primary.confidence,
            rank=primary.rank,
            source=primary.source,
            trace=primary_trace,
        )
        kept[kept.index(primary)] = seen[signature]
    return kept, dedupe_count


def _selected_single_step_families(
    family_result: FamilyDiscoveryResult,
    *,
    enabled_families: Sequence[str] | None,
) -> list[FamilyHypothesis]:
    allowed = {_safe_text(item) for item in enabled_families} if enabled_families is not None else None
    hypotheses = list(family_result.accepted_families) + list(family_result.uncertain_families)
    hypotheses.sort(key=lambda hyp: (_family_rank(_safe_text(hyp.family_name)), -float(hyp.confidence), len(hyp.primitive_chain), _safe_text(hyp.family_name), tuple(_safe_text(item) for item in hyp.primitive_chain)))
    selected: list[FamilyHypothesis] = []
    for hypothesis in hypotheses:
        family_name = _safe_text(hypothesis.family_name)
        if family_name in COMPOSITION_TEMPLATES_V1:
            continue
        if family_name not in EXECUTABLE_FAMILY_ORDER_V1:
            continue
        if allowed is not None and family_name not in allowed:
            continue
        if hypothesis.status == "uncertain" and float(hypothesis.confidence) < HIGH_CONFIDENCE_UNCERTAIN_THRESHOLD_V1 and allowed is None:
            continue
        selected.append(hypothesis)
    return selected


def _selected_composition_hypotheses(
    family_result: FamilyDiscoveryResult,
    *,
    enabled_families: Sequence[str] | None,
) -> list[FamilyHypothesis]:
    allowed = {_safe_text(item) for item in enabled_families} if enabled_families is not None else None
    hypotheses = list(family_result.accepted_families)
    hypotheses.sort(key=lambda hyp: (_family_rank(_safe_text(hyp.family_name)), -float(hyp.confidence), len(hyp.primitive_chain), _safe_text(hyp.family_name), tuple(_safe_text(item) for item in hyp.primitive_chain)))
    selected: list[FamilyHypothesis] = []
    for hypothesis in hypotheses:
        family_name = _safe_text(hypothesis.family_name)
        if family_name not in COMPOSITION_TEMPLATES_V1:
            continue
        if allowed is not None and family_name not in allowed:
            continue
        selected.append(hypothesis)
    return selected


def _fallback_status(candidates: Sequence[UniversalRunnerCandidate]) -> bool:
    return all(_safe_text(candidate.family_name) == FALLBACK_FAMILY_V1 for candidate in candidates)


def run_universal_family_solver(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    enabled_families: Sequence[str] | None = None,
) -> UniversalRunnerResult:
    registry = build_arc_primitive_registry_v1()
    task_signature = build_arc_task_feature_signature_v1(train_pairs, test_input)
    primitive_result = discover_primitives_for_task(train_pairs, test_input, registry=registry)
    family_result = discover_families_for_task(train_pairs, test_input, primitive_result=primitive_result, registry=registry)

    composition_hypotheses = _selected_composition_hypotheses(family_result, enabled_families=enabled_families)
    composition_candidates = execute_compositional_family_hypotheses(train_pairs, test_input, composition_hypotheses, trace=True)
    executable_composition_candidates = [candidate for candidate in composition_candidates if candidate.train_fit and candidate.output is not None]
    composition_rejections = [candidate.to_json_safe_dict() for candidate in composition_candidates if not candidate.train_fit or candidate.output is None]

    single_step_hypotheses = _selected_single_step_families(family_result, enabled_families=enabled_families)
    aggregator_enabled_families = [_safe_text(hypothesis.family_name) for hypothesis in single_step_hypotheses]
    if FALLBACK_FAMILY_V1 not in aggregator_enabled_families:
        aggregator_enabled_families.append(FALLBACK_FAMILY_V1)
    aggregator_packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(
        train_pairs,
        test_input,
        task_id=DEFAULT_TASK_ID_V1,
        enabled_families=aggregator_enabled_families,
        metadata={
            "adapter_name": "arc_universal_family_runner_v1",
            "schema_version": SCHEMA_VERSION_V1,
            "synthetic_only": True,
            "selected_single_step_families": [_safe_text(hypothesis.family_name) for hypothesis in single_step_hypotheses],
            "selected_composition_families": [_safe_text(hypothesis.family_name) for hypothesis in composition_hypotheses],
        },
    )
    aggregator_candidates = [
        _candidate_from_attempt(attempt, rank=index + 1)
        for index, attempt in enumerate(aggregator_packet.get("attempts", []))
        if isinstance(attempt, Mapping)
    ]

    all_candidates: list[UniversalRunnerCandidate] = []
    all_candidates.extend(
        _candidate_from_compositional(candidate, rank=index + 1)
        for index, candidate in enumerate(executable_composition_candidates)
    )
    all_candidates.extend(aggregator_candidates)

    deduped_candidates, extra_dedupe_count = _dedupe_candidates(all_candidates)
    if len(deduped_candidates) < 2:
        deduped_candidates.extend(_build_safe_fallback_candidates(test_input)[: 2 - len(deduped_candidates)])

    deduped_candidates, fallback_fill_dedupe = _dedupe_candidates(deduped_candidates)
    dedupe_count = extra_dedupe_count + fallback_fill_dedupe
    if len(deduped_candidates) < 2:
        deduped_candidates.extend(_build_safe_fallback_candidates(test_input)[: 2 - len(deduped_candidates)])

    deduped_candidates = sorted(deduped_candidates, key=_candidate_rank_key)
    attempts = deduped_candidates[:2]
    if len(attempts) < 2:
        attempts = _build_safe_fallback_candidates(test_input)

    fallback_used = _fallback_status(attempts)
    selected_family_names = []
    for candidate in attempts:
        name = _safe_text(candidate.family_name)
        if name and name != FALLBACK_FAMILY_V1 and name not in selected_family_names:
            selected_family_names.append(name)

    trace = {
        "schema_version": SCHEMA_VERSION_V1,
        "task_feature_summary": {
            "pair_count": len(train_pairs),
            "labels": task_signature.get("task_level_signature", {}).get("possible_primitive_hint_intersection", []),
        },
        "primitive_result_summary": {
            "accepted_count": primitive_result.accepted_count,
            "rejected_count": primitive_result.rejected_count,
            "uncertain_count": primitive_result.uncertain_count,
        },
        "family_result_summary": {
            "accepted_count": family_result.accepted_count,
            "rejected_count": family_result.rejected_count,
            "uncertain_count": family_result.uncertain_count,
            "composition_rejections": composition_rejections,
        },
        "aggregator_metadata": aggregator_packet.get("metadata", {}) if isinstance(aggregator_packet.get("metadata"), Mapping) else {},
        "selected_single_step_families": [_safe_text(hypothesis.family_name) for hypothesis in single_step_hypotheses],
        "selected_composition_families": [_safe_text(hypothesis.family_name) for hypothesis in composition_hypotheses],
        "executed_composition_families": [_safe_text(candidate.family_name) for candidate in executable_composition_candidates],
    }
    if composition_rejections:
        trace["composition_execution_rejections"] = composition_rejections

    return UniversalRunnerResult(
        attempt_1=attempts[0],
        attempt_2=attempts[1],
        candidate_count=len(attempts),
        family_discovery_summary=family_result.to_json_safe_dict(),
        selected_family_names=tuple(selected_family_names),
        dedupe_count=dedupe_count,
        fallback_used=fallback_used,
        exact_two_output=len(attempts) == 2,
        trace=trace,
    )


__all__ = [
    "SCHEMA_VERSION_V1",
    "UniversalRunnerCandidate",
    "UniversalRunnerResult",
    "run_universal_family_solver",
]
