"""ARC-AGI-2 universal family runner V1.

Synthetic-only top-2 runner that connects task signatures, primitive discovery,
family discovery, and the existing capability candidate aggregator.

It does not ingest public ARC data, does not score, does not submit, and does
not implement compositional execution beyond discovery metadata in V1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_capability_candidate_aggregator_v1 import build_arc_agi2_capability_candidate_top2_attempt_packet_v1
from weslr.arc_family_discovery_engine_v1 import (
    ALLOWED_COMPOSITION_TEMPLATES_V1,
    COMPOSITION_FAMILY_ORDER_V1,
    FAMILY_PRIORITY_V1,
    FamilyDiscoveryResult,
    FamilyHypothesis,
    discover_families_for_task,
    SOLVER_FAMILY_TO_PRIMITIVE_V1,
)
from weslr.arc_primitive_discovery_engine_v1 import PrimitiveDiscoveryResult, discover_primitives_for_task
from weslr.arc_primitive_registry_v1 import build_arc_primitive_registry_v1
from weslr.arc_task_feature_signature_v1 import build_arc_task_feature_signature_v1

SCHEMA_VERSION_V1 = "ArcUniversalFamilyRunnerV1"
DEFAULT_TASK_ID_V1 = "arc_universal_family_runner_task"
HIGH_CONFIDENCE_UNCERTAIN_THRESHOLD_V1 = 0.8

EXECUTABLE_FAMILY_ORDER_V1 = (
    "object_bbox",
    "shape_geometry",
    "color_role",
    "resize_tile",
    "count_quantity",
)

FALLBACK_FAMILY_V1 = "fallback"


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
    if family_name in FAMILY_PRIORITY_V1:
        return FAMILY_PRIORITY_V1[family_name]
    if family_name in COMPOSITION_FAMILY_ORDER_V1:
        return 100 + COMPOSITION_FAMILY_ORDER_V1.index(family_name)
    if family_name == FALLBACK_FAMILY_V1:
        return 999
    return 500


def _primitive_for_solver_family(solver_family: str) -> str:
    return _safe_text(SOLVER_FAMILY_TO_PRIMITIVE_V1.get(_safe_text(solver_family), solver_family))


def _selected_single_step_families(
    family_result: FamilyDiscoveryResult,
    *,
    enabled_families: Sequence[str] | None,
) -> tuple[list[str], list[str]]:
    allowed = {_safe_text(item) for item in enabled_families} if enabled_families is not None else None
    selected: list[str] = []
    discovered_not_executable: list[str] = []

    hypotheses: list[FamilyHypothesis] = list(family_result.accepted_families) + list(family_result.uncertain_families)
    hypotheses.sort(key=lambda hyp: (_family_rank(_safe_text(hyp.family_name)), -float(hyp.confidence), len(hyp.primitive_chain), _safe_text(hyp.family_name), tuple(_safe_text(name) for name in hyp.primitive_chain)))

    for hypothesis in hypotheses:
        family_name = _safe_text(hypothesis.family_name)
        if family_name in ALLOWED_COMPOSITION_TEMPLATES_V1:
            if family_name not in discovered_not_executable:
                discovered_not_executable.append(family_name)
            continue
        if family_name not in EXECUTABLE_FAMILY_ORDER_V1:
            continue
        if allowed is not None and family_name not in allowed:
            continue
        if hypothesis.status == "uncertain" and float(hypothesis.confidence) < HIGH_CONFIDENCE_UNCERTAIN_THRESHOLD_V1 and allowed is None:
            continue
        if family_name not in selected:
            selected.append(family_name)

    selected.sort(key=lambda name: (_family_rank(name), name))
    discovered_not_executable.sort(key=lambda name: (_family_rank(name), name))
    return selected, discovered_not_executable


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
    solver_family = _safe_text(metadata.get("solver_family") or metadata.get("source_family_label") or family_name)
    primitive_chain = (_primitive_for_solver_family(solver_family),)
    source = _safe_text(metadata.get("source_adapter") or metadata.get("adapter_name") or metadata.get("source_kind") or "aggregator")
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
    }
    confidence = metadata.get("candidate_score")
    try:
        confidence_value = float(confidence)
    except Exception:
        confidence_value = float(rank)
    return UniversalRunnerCandidate(
        family_name=family_name,
        primitive_chain=primitive_chain,
        output=attempt.get("grid"),
        confidence=confidence_value,
        rank=int(rank),
        source=source,
        trace=trace,
    )


def _build_safe_fallback_attempts(test_input: Any) -> list[dict[str, Any]]:
    grid = _json_safe(test_input)
    if not isinstance(grid, list):
        grid = [[0]]
    if not grid or not isinstance(grid[0], list):
        grid = [[0]]
    fallback = {
        "attempt_id": f"{DEFAULT_TASK_ID_V1}:fallback",
        "grid": grid,
        "source_candidate_id": f"{DEFAULT_TASK_ID_V1}:fallback",
        "rank": 1,
        "confidence_label": "low",
        "evidence_labels": ["fallback"],
        "leakage_flags": {},
        "metadata": {
            "adapter_name": "arc_universal_family_runner_v1",
            "schema_version": SCHEMA_VERSION_V1,
            "source_kind": "safe_deterministic_fallback",
            "source_family": FALLBACK_FAMILY_V1,
            "source_family_label": FALLBACK_FAMILY_V1,
            "source_adapter": "arc_universal_family_runner_v1",
            "confidence_label": "low",
            "candidate_score": 0,
            "train_fit": False,
            "synthetic_only": True,
        },
    }
    return [fallback, {**fallback, "attempt_id": f"{DEFAULT_TASK_ID_V1}:fallback_2", "source_candidate_id": f"{DEFAULT_TASK_ID_V1}:fallback_2", "rank": 2}]


def _ensure_two_attempts(packet: Mapping[str, Any], test_input: Any) -> tuple[list[dict[str, Any]], bool]:
    attempts = [dict(attempt) for attempt in packet.get("attempts", []) if isinstance(attempt, Mapping)]
    fallback_used = bool(packet.get("metadata", {}).get("used_fallback", False)) if isinstance(packet.get("metadata"), Mapping) else False
    if len(attempts) >= 2:
        return attempts[:2], fallback_used
    fallback_attempts = _build_safe_fallback_attempts(test_input)
    attempts.extend(fallback_attempts[: 2 - len(attempts)])
    return attempts[:2], True


def _dedupe_attempts(attempts: Sequence[Mapping[str, Any]], test_input: Any) -> tuple[list[dict[str, Any]], int, bool]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    dedupe_count = 0
    fallback_used = False
    for attempt in attempts:
        grid = attempt.get("grid") if isinstance(attempt, Mapping) else None
        signature = repr(_json_safe(grid))
        if signature in seen:
            dedupe_count += 1
            continue
        seen.add(signature)
        unique.append(dict(attempt))
    if len(unique) < 2:
        fallback_used = True
        for fallback_attempt in _build_safe_fallback_attempts(test_input):
            signature = repr(_json_safe(fallback_attempt.get("grid")))
            if signature in seen:
                continue
            unique.append(fallback_attempt)
            seen.add(signature)
            if len(unique) >= 2:
                break
    return unique[:2], dedupe_count, fallback_used


def run_universal_family_solver(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    enabled_families: Sequence[str] | None = None,
) -> UniversalRunnerResult:
    registry = build_arc_primitive_registry_v1()
    task_signature = build_arc_task_feature_signature_v1(train_pairs, test_input)
    primitive_result = discover_primitives_for_task(train_pairs, test_input, registry=registry)
    family_result = discover_families_for_task(train_pairs, test_input, primitive_result=primitive_result, registry=registry)

    selected_family_names, discovered_not_executable = _selected_single_step_families(family_result, enabled_families=enabled_families)
    aggregator_enabled_families = list(selected_family_names)
    if not aggregator_enabled_families:
        aggregator_enabled_families = [FALLBACK_FAMILY_V1]
    elif FALLBACK_FAMILY_V1 not in aggregator_enabled_families:
        aggregator_enabled_families.append(FALLBACK_FAMILY_V1)

    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(
        train_pairs,
        test_input,
        task_id=DEFAULT_TASK_ID_V1,
        enabled_families=aggregator_enabled_families,
        metadata={
            "adapter_name": "arc_universal_family_runner_v1",
            "schema_version": SCHEMA_VERSION_V1,
            "synthetic_only": True,
            "discovered_not_executable_v1": discovered_not_executable,
            "selected_family_names": selected_family_names,
            "task_feature_summary": {
                "pair_count": len(train_pairs),
                "task_signature_labels": task_signature.get("task_level_signature", {}).get("possible_primitive_hint_intersection", []),
            },
            "primitive_result_summary": primitive_result.to_json_safe_dict(),
            "family_result_summary": family_result.to_json_safe_dict(),
        },
    )

    attempts, fallback_used = _ensure_two_attempts(packet, test_input)
    attempts, extra_dedupe_count, extra_fallback_used = _dedupe_attempts(attempts, test_input)
    attempt_candidates = [_candidate_from_attempt(attempt, rank=index + 1) for index, attempt in enumerate(attempts)]
    fallback_used = all(candidate.family_name == FALLBACK_FAMILY_V1 for candidate in attempt_candidates)
    result_trace = {
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
            "discovered_not_executable_v1": discovered_not_executable,
        },
        "aggregator_metadata": {
            "dedupe_count": (packet.get("metadata", {}).get("dedupe_count", 0) if isinstance(packet.get("metadata"), Mapping) else 0) + extra_dedupe_count,
            "used_fallback": fallback_used,
            "enabled_families": packet.get("metadata", {}).get("enabled_families", aggregator_enabled_families) if isinstance(packet.get("metadata"), Mapping) else aggregator_enabled_families,
        },
    }
    return UniversalRunnerResult(
        attempt_1=attempt_candidates[0],
        attempt_2=attempt_candidates[1],
        candidate_count=len(attempt_candidates),
        family_discovery_summary=family_result.to_json_safe_dict(),
        selected_family_names=tuple(selected_family_names),
        dedupe_count=(int(packet.get("metadata", {}).get("dedupe_count", 0)) if isinstance(packet.get("metadata"), Mapping) else 0) + extra_dedupe_count,
        fallback_used=fallback_used,
        exact_two_output=len(attempt_candidates) == 2,
        trace=result_trace,
    )


__all__ = [
    "SCHEMA_VERSION_V1",
    "UniversalRunnerCandidate",
    "UniversalRunnerResult",
    "run_universal_family_solver",
]
