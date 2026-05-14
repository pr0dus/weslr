#!/usr/bin/env python3
"""WESLR repeated weakness detector helpers V1.

Safe helper-only layer for detecting repeated weakness candidates from in-memory
native learning signal registries. This module does not train models, call
external models, score benchmarks, write files, persist `.weslr` state, wire
runtime/chat/voice, approve proposals, or implement changes.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

from weslr.native_learning_signal_registry import (
    FORBIDDEN_SIGNAL_FIELDS_V1,
    FORBIDDEN_TEXT_MARKERS_V1,
    REGISTRY_TYPE_V1,
    SIGNAL_TYPE_V1,
    _as_list,
    _compact,
    _contains_any,
    _json_safe,
    _stable_id,
    _string_list,
    _walk,
    validate_native_learning_signal_registry_v1,
)

CANDIDATE_TYPE_V1 = "repeated_weakness_candidate_v1"
DETECTOR_TYPE_V1 = "repeated_weakness_detector_v1"
CANDIDATE_VALIDATION_SCHEMA_V1 = "repeated_weakness_candidate_validation_v1"
DETECTOR_VALIDATION_SCHEMA_V1 = "repeated_weakness_detector_validation_v1"
CANDIDATE_EXECUTION_STATUS_V1 = "non_executing_weakness_candidate_only"
DETECTOR_EXECUTION_STATUS_V1 = "non_executing_detector_only"

CONFIDENCE_LABELS_V1 = ("weak", "emerging", "recurring", "review_ready")
CONFIDENCE_RANK_V1 = {label: index for index, label in enumerate(CONFIDENCE_LABELS_V1)}

WEAKNESS_STATUS_V1 = {
    "candidate_only": True,
    "not_truth": True,
    "not_proposal": True,
    "not_approval": True,
    "not_implementation": True,
}

SAFETY_BOUNDARIES_V1 = [
    "repeated_weakness_candidate_is_not_truth",
    "repeated_weakness_candidate_is_not_proposal",
    "repeated_weakness_candidate_is_not_approval",
    "repeated_weakness_candidate_is_not_implementation",
    "proposal_generation_comes_later",
    "implementation_requires_explicit_approval_tests_and_release_gate_check",
    "no_raw_private_text_by_default",
    "no_hidden_prompts",
    "no_answer_keys",
    "no_protected_items",
    "no_model_training_payloads",
    "no_automatic_self_modification",
    "no_runtime_or_voice_wiring",
    "no_persistence_by_default",
]

FORBIDDEN_CANDIDATE_FIELDS_V1 = set(FORBIDDEN_SIGNAL_FIELDS_V1) | {
    "truth_claim",
    "defect_proven",
    "proposal_approved",
    "implementation_authorized",
    "safe_to_wire_runtime",
    "safe_to_replace_live_output",
}


def _violation(category: str, path: str, message: str) -> Dict[str, str]:
    return {"category": category, "path": path or "$", "message": message}


def _confidence_from_count(signal_count: int) -> str:
    if signal_count >= 5:
        return "review_ready"
    if signal_count >= 3:
        return "recurring"
    if signal_count >= 2:
        return "emerging"
    return "weak"


def _highest_confidence(labels: Iterable[str]) -> str:
    best = "weak"
    for label in labels:
        if CONFIDENCE_RANK_V1.get(label, 0) > CONFIDENCE_RANK_V1.get(best, 0):
            best = label
    return best


def _candidate_summary(recurrence_key: str, signal_family: str, signal_count: int) -> str:
    return f"Repeated {signal_family} appears under recurrence key {recurrence_key} across {signal_count} safe learning signals."


def create_repeated_weakness_candidate_v1(
    *,
    recurrence_key: str,
    signal_family: str,
    source_layers: Optional[Iterable[Any]] = None,
    signal_ids: Optional[Iterable[Any]] = None,
    evidence_refs: Optional[Iterable[Any]] = None,
    weakness_summary: Optional[str] = None,
    confidence_label: Optional[str] = None,
    recommended_investigation: str = "review repeated safe signals before proposing any change",
    candidate_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create one JSON-safe repeated weakness candidate record in memory only."""
    ids = sorted(_string_list(signal_ids))
    layers = sorted(set(_string_list(source_layers)))
    refs = sorted(set(_string_list(evidence_refs)))
    count = len(ids)
    confidence = confidence_label if confidence_label in CONFIDENCE_LABELS_V1 else _confidence_from_count(count)
    seed = {
        "recurrence_key": _compact(recurrence_key),
        "signal_family": _compact(signal_family),
        "source_layers": layers,
        "signal_ids": ids,
        "evidence_refs": refs,
    }
    candidate = {
        "candidate_id": _compact(candidate_id, "") or _stable_id("rwcv1", seed),
        "candidate_type": CANDIDATE_TYPE_V1,
        "recurrence_key": _compact(recurrence_key),
        "signal_family": _compact(signal_family),
        "source_layers": layers,
        "signal_ids": ids,
        "signal_count": count,
        "evidence_refs": refs,
        "weakness_summary": _compact(weakness_summary, "") or _candidate_summary(_compact(recurrence_key), _compact(signal_family), count),
        "confidence_label": confidence,
        "learning_status": copy.deepcopy(WEAKNESS_STATUS_V1),
        "recommended_investigation": _compact(recommended_investigation),
        "safety_boundaries": list(SAFETY_BOUNDARIES_V1),
        "execution_status": CANDIDATE_EXECUTION_STATUS_V1,
    }
    return _json_safe(candidate)


def detect_repeated_weakness_candidates_v1(registry: Mapping[str, Any], min_signal_count: int = 2) -> List[Dict[str, Any]]:
    """Detect repeated weakness candidates from registry recurrence groups without mutation or persistence."""
    safe = _json_safe(registry or {})
    if not isinstance(safe, Mapping):
        safe = {}
    threshold = max(2, int(min_signal_count or 2))
    signals = [s for s in _as_list(safe.get("signals")) if isinstance(s, Mapping)]
    by_pair: Dict[tuple[str, str], List[Mapping[str, Any]]] = {}
    for signal in signals:
        if signal.get("signal_type") != SIGNAL_TYPE_V1:
            continue
        recurrence_key = _compact(signal.get("recurrence_key"), "")
        family = _compact(signal.get("signal_family"), "")
        if not recurrence_key or not family:
            continue
        by_pair.setdefault((recurrence_key, family), []).append(signal)

    candidates: List[Dict[str, Any]] = []
    for (recurrence_key, family), grouped in sorted(by_pair.items(), key=lambda item: item[0]):
        if len(grouped) < threshold:
            continue
        signal_ids = [_compact(signal.get("signal_id"), "") for signal in grouped]
        source_layers = [_compact(signal.get("source_layer"), "") for signal in grouped]
        refs: List[str] = []
        for signal in grouped:
            refs.extend(_string_list(signal.get("provenance_refs")))
            refs.append(_compact(signal.get("source_ref"), ""))
        candidates.append(create_repeated_weakness_candidate_v1(
            recurrence_key=recurrence_key,
            signal_family=family,
            source_layers=source_layers,
            signal_ids=signal_ids,
            evidence_refs=refs,
            confidence_label=_confidence_from_count(len(grouped)),
            recommended_investigation=f"investigate recurring {family} under {recurrence_key} before drafting any governed proposal",
        ))
    return _json_safe(candidates)


def validate_repeated_weakness_candidate_v1(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate one repeated weakness candidate remains safe and non-authorizing."""
    safe = _json_safe(candidate or {})
    if not isinstance(safe, Mapping):
        safe = {}
    violations: List[Dict[str, str]] = []

    if safe.get("candidate_type") != CANDIDATE_TYPE_V1:
        violations.append(_violation("invalid_candidate_type", "candidate_type", "candidate_type must be repeated_weakness_candidate_v1"))
    if safe.get("execution_status") != CANDIDATE_EXECUTION_STATUS_V1:
        violations.append(_violation("execution_authorization_drift", "execution_status", "candidate must remain non-executing"))
    if safe.get("confidence_label") not in CONFIDENCE_LABELS_V1:
        violations.append(_violation("invalid_confidence_label", "confidence_label", "confidence_label must be approved non-numeric label"))

    learning = safe.get("learning_status") if isinstance(safe.get("learning_status"), Mapping) else {}
    for key in ("candidate_only", "not_truth", "not_proposal", "not_approval", "not_implementation"):
        if learning.get(key) is not True:
            violations.append(_violation("learning_status_drift", f"learning_status.{key}", "candidate must remain non-authoritative"))

    for required in ("candidate_id", "recurrence_key", "signal_family"):
        if not _compact(safe.get(required), ""):
            violations.append(_violation("missing_required_field", required, f"{required} is required"))
    if int(safe.get("signal_count") or 0) != len(_as_list(safe.get("signal_ids"))):
        violations.append(_violation("signal_count_mismatch", "signal_count", "signal_count must match signal_ids length"))

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_CANDIDATE_FIELDS_V1:
            category = "forbidden_field"
            if terminal == "raw_private_text":
                category = "raw_private_text"
            elif terminal in {"hidden_prompt", "hidden_prompts"}:
                category = "hidden_prompt"
            elif terminal in {"answer_key", "answer_keys", "benchmark_answer", "benchmark_answers"}:
                category = "answer_key_or_benchmark_answer"
            elif terminal in {"protected_item", "protected_items", "protected_test_item", "protected_test_items"}:
                category = "protected_test_material"
            elif terminal in {"official_score", "official_scores", "iq_score", "official_iq_score", "clinical_score", "certification_claim", "benchmark_score"}:
                category = "official_iq_benchmark_or_certification"
            elif terminal in {"score", "scores", "numeric_score", "grade", "grades", "pass_fail", "passed", "failed"}:
                category = "numeric_score_or_pass_fail_grading"
            elif terminal in {"model_weight_update", "fine_tune_payload"}:
                category = "model_training_or_fine_tuning"
            elif terminal in {"auto_approval", "auto_approved", "auto_implementation", "auto_implemented"}:
                category = "auto_approval_or_auto_implementation"
            elif terminal in {"runtime_write", "persistence_target", "safe_to_wire_runtime", "safe_to_replace_live_output"}:
                category = "runtime_or_persistence_authorization_drift"
            elif terminal in {"truth_claim", "defect_proven", "proposal_approved", "implementation_authorized"}:
                category = "unproven_truth_or_authorization_claim"
            violations.append(_violation(category, path, f"forbidden field present: {terminal}"))
        if isinstance(value, (int, float)) and not isinstance(value, bool) and terminal not in {"signal_count"}:
            violations.append(_violation("numeric_score_or_numeric_metric", path, "numeric fields other than counts are not allowed"))
        if isinstance(value, str):
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(value, markers):
                    violations.append(_violation(category, path, f"forbidden text marker detected: {category}"))

    return {
        "validation_schema": CANDIDATE_VALIDATION_SCHEMA_V1,
        "valid": not violations,
        "validation_status": "accepted" if not violations else "rejected",
        "violation_count": len(violations),
        "violations": violations,
    }


def _candidate_counts_by(candidates: Iterable[Mapping[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for candidate in candidates:
        values = _as_list(candidate.get(key)) if key == "source_layers" else [candidate.get(key)]
        for value in values:
            compact = _compact(value, "")
            if compact:
                counts[compact] = counts.get(compact, 0) + 1
    return dict(sorted(counts.items()))


def build_repeated_weakness_detector_result_v1(registry: Mapping[str, Any], min_signal_count: int = 2) -> Dict[str, Any]:
    """Build an in-memory repeated weakness detector result from a learning signal registry."""
    safe_registry = _json_safe(registry or {})
    candidates = detect_repeated_weakness_candidates_v1(safe_registry, min_signal_count=min_signal_count)
    total = len(_as_list(safe_registry.get("signals"))) if isinstance(safe_registry, Mapping) else 0
    seed = {
        "registry_id": safe_registry.get("registry_id") if isinstance(safe_registry, Mapping) else None,
        "candidate_ids": [candidate.get("candidate_id") for candidate in candidates],
        "min_signal_count": max(2, int(min_signal_count or 2)),
    }
    result = {
        "detector_result_id": _stable_id("rwdv1", seed),
        "detector_type": DETECTOR_TYPE_V1,
        "source_registry_type": safe_registry.get("registry_type") if isinstance(safe_registry, Mapping) else None,
        "total_signals_considered": total,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "candidate_counts_by_family": _candidate_counts_by(candidates, "signal_family"),
        "candidate_counts_by_source_layer": _candidate_counts_by(candidates, "source_layers"),
        "min_signal_count": max(2, int(min_signal_count or 2)),
        "safety_boundaries": list(SAFETY_BOUNDARIES_V1),
        "execution_status": DETECTOR_EXECUTION_STATUS_V1,
    }
    result["validation_status"] = validate_repeated_weakness_detector_result_v1(result)
    return _json_safe(result)


def validate_repeated_weakness_detector_result_v1(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate detector result remains non-executing and non-authorizing."""
    safe = _json_safe(result or {})
    if not isinstance(safe, Mapping):
        safe = {}
    violations: List[Dict[str, str]] = []

    if safe.get("detector_type") != DETECTOR_TYPE_V1:
        violations.append(_violation("invalid_detector_type", "detector_type", "detector_type must be repeated_weakness_detector_v1"))
    if safe.get("execution_status") != DETECTOR_EXECUTION_STATUS_V1:
        violations.append(_violation("execution_authorization_drift", "execution_status", "detector must remain non-executing"))
    if safe.get("source_registry_type") not in {REGISTRY_TYPE_V1, None}:
        violations.append(_violation("invalid_source_registry_type", "source_registry_type", "unexpected source registry type"))

    candidates = safe.get("candidates") if isinstance(safe.get("candidates"), list) else []
    if int(safe.get("candidate_count") or 0) != len(candidates):
        violations.append(_violation("candidate_count_mismatch", "candidate_count", "candidate_count must match candidates length"))
    for index, candidate in enumerate(candidates):
        validation = validate_repeated_weakness_candidate_v1(candidate if isinstance(candidate, Mapping) else {})
        for item in validation["violations"]:
            violations.append(_violation(item["category"], f"candidates[{index}].{item['path']}", item["message"]))

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_CANDIDATE_FIELDS_V1:
            violations.append(_violation("forbidden_field", path, f"forbidden field present in detector result: {terminal}"))
        if isinstance(value, str):
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(value, markers):
                    violations.append(_violation(category, path, f"forbidden text marker detected in detector result: {category}"))

    return {
        "validation_schema": DETECTOR_VALIDATION_SCHEMA_V1,
        "valid": not violations,
        "validation_status": "accepted" if not violations else "rejected",
        "violation_count": len(violations),
        "violations": violations,
    }


def summarize_repeated_weakness_detector_result_v1(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a count-only/redacted detector summary."""
    safe = _json_safe(result or {})
    candidates = safe.get("candidates") if isinstance(safe.get("candidates"), list) else []
    validation = validate_repeated_weakness_detector_result_v1(safe)
    return {
        "total_signals_considered": int(safe.get("total_signals_considered") or 0),
        "candidate_count": int(safe.get("candidate_count") or len(candidates)),
        "candidate_families_present": sorted((safe.get("candidate_counts_by_family") or {}).keys()),
        "source_layers_present": sorted((safe.get("candidate_counts_by_source_layer") or {}).keys()),
        "highest_confidence_label": _highest_confidence(candidate.get("confidence_label", "weak") for candidate in candidates if isinstance(candidate, Mapping)),
        "recommended_investigation_count": sum(1 for candidate in candidates if isinstance(candidate, Mapping) and _compact(candidate.get("recommended_investigation"), "")),
        "safety_status": "safe" if validation["valid"] else "review_required",
        "execution_status": safe.get("execution_status", DETECTOR_EXECUTION_STATUS_V1),
    }


def to_repeated_weakness_detector_json_safe_v1(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a JSON-serializable detector result copy without persistence."""
    return _json_safe(result)


def render_repeated_weakness_detector_markdown_v1(result: Mapping[str, Any]) -> str:
    """Render safe Markdown for a repeated weakness detector result."""
    safe = _json_safe(result or {})
    summary = summarize_repeated_weakness_detector_result_v1(safe)
    lines = [
        "# Repeated Weakness Detector",
        "",
        f"- Detector type: `{safe.get('detector_type', DETECTOR_TYPE_V1)}`",
        f"- Total signals considered: {summary['total_signals_considered']}",
        f"- Candidate count: {summary['candidate_count']}",
        f"- Highest confidence label: `{summary['highest_confidence_label']}`",
        f"- Execution status: `{summary['execution_status']}`",
        "",
        "## Candidate Families",
    ]
    for family, count in sorted((safe.get("candidate_counts_by_family") or {}).items()):
        lines.append(f"- `{family}`: {count}")
    lines.extend(["", "## Recurrence Groups"])
    for candidate in safe.get("candidates") or []:
        if isinstance(candidate, Mapping):
            lines.append(f"- `{candidate.get('recurrence_key')}` / `{candidate.get('signal_family')}`: {candidate.get('signal_count')} signal(s)")
    lines.extend(["", "## Recommended Investigations"])
    for candidate in safe.get("candidates") or []:
        if isinstance(candidate, Mapping):
            lines.append(f"- `{candidate.get('candidate_id')}`: review recurring `{candidate.get('signal_family')}` before any governed proposal")
    lines.extend(["", "## Safety Boundaries"])
    for boundary in MARKDOWN_SAFETY_BOUNDARIES_V1:
        lines.append(f"- {boundary}")
    lines.extend([
        "",
        "## Non-Truth / Non-Proposal Disclaimer",
        "Repeated weakness candidates are signal-only investigation candidates. They are not truth, proposals, approvals, implementations, scores, or model-training payloads.",
    ])
    return "\n".join(lines)


MARKDOWN_SAFETY_BOUNDARIES_V1 = [
    "repeated weakness candidate is not truth",
    "repeated weakness candidate is not proposal, approval, or implementation",
    "proposal generation comes later",
    "implementation requires explicit approval, tests, and release gate/check",
    "no raw private text, hidden prompts, answer keys, protected items, model training payloads, runtime writes, or implementation instructions",
]
