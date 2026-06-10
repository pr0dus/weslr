"""WESLR Perspicuity Scorer V1 metadata helpers.

Deterministic, metadata-only scoring and ranking scaffolding for internal
prioritization only. This module does not prove truth, authorize public claims,
authorize runtime behavior, mutate memory or projects, promote behavior packs,
or replace safety validation.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from weslr.cognitive_research_protocol import (
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    build_generated_source_signal_metadata_v1,
    build_perspicuity_score_metadata_v1,
    build_rule_pressure_test_metadata_v1,
    build_source_signal_metadata_v1,
    summarize_cognitive_research_run_v1,
    to_cognitive_research_json_safe_v1,
    validate_cognitive_research_run_v1,
)
from weslr.forecast_calibration_bridge import build_forecast_calibration_record_v1

HELPER_TYPE_V1 = "weslr_perspicuity_scorer_v1"
SCHEMA_VERSION_V1 = "perspicuity_scorer_v1"
ENGINE_NAME_V1 = "perspicuity_scorer"
ENGINE_FAMILY_V1 = "candidate_ranking"

_ALLOWED_RESEARCH_MODES_V1 = (
    "internal_exploration",
    "synthetic_test",
    "calibration_replay",
    "frontier_mapping",
)
_ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = (
    "not_public_claim",
    "internal_candidate_only",
    "public_export_blocked",
)
_ALLOWED_CANDIDATE_TYPES_V1 = (
    "source_signal",
    "generated_source_signal",
    "hidden_rule_candidate",
    "operator_candidate",
    "translation_candidate",
    "structural_match_candidate",
    "motif_candidate",
    "gap_hypothesis",
    "pressure_result",
    "correction_lesson",
    "dialectic_turn",
    "calibration_record",
    "unknown",
)
_ALLOWED_SCORE_DIMENSIONS_V1 = (
    "clarity",
    "signal_density",
    "novelty",
    "testability",
    "pressure_worthiness",
    "calibration_value",
    "cross_domain_resonance",
    "compression_value",
    "risk_of_false_pattern",
    "boundary_sensitivity",
)
_ALLOWED_SCORE_LABELS_V1 = (
    "none",
    "low",
    "medium",
    "high",
    "unknown",
)
_ALLOWED_OVERALL_PRIORITIES_V1 = (
    "drop",
    "archive",
    "watch",
    "probe",
    "pressure_test",
    "calibrate",
    "promote_to_next_internal_step",
    "unknown",
)
_ALLOWED_RANK_BUCKETS_V1 = (
    "top",
    "high",
    "medium",
    "low",
    "blocked",
    "unknown",
)

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw private text",
    "raw private data",
    "private content",
    "hidden prompt",
    "system prompt",
    "developer prompt",
    "secret",
    "password",
    "token=",
    "credential",
    "final answer",
    "final-answer",
    "answer draft",
    "reply output",
    "provider output",
    "model output",
    "tool execution",
    "tool authority",
    "provider authority",
    "runtime authority",
    "llm authority",
    "public discovery",
    "proof",
    "truth",
    "breakthrough",
    "official intelligence",
    "agi",
    "sentience",
    "consciousness",
    "runtime",
    "provider",
    "tool",
    "persistence",
    ".weslr",
    "live ingestion",
    "network",
    "memory mutation",
    "project mutation",
    "behavior-pack promotion",
    "behavior pack",
    "promotion",
    "memory mutation authority",
    "project mutation authority",
    "safety gate replacement",
    "replace safety gate",
    "github rss",
    "lab notebook",
    "executable code-as-action",
)

_FORBIDDEN_KEY_FRAGMENTS_V1 = (
    "raw_private",
    "raw_response",
    "raw_artifact",
    "private_content",
    "hidden_prompt",
    "hidden_system_prompt",
    "system_prompt",
    "developer_prompt",
    "secret",
    "password",
    "token",
    "provider_output",
    "model_output",
    "search_output",
    ".weslr",
    "answer_draft",
)

_SCORE_LABEL_TO_VALUE_V1 = {
    "none": 0.0,
    "low": 25.0,
    "medium": 50.0,
    "high": 75.0,
    "unknown": 40.0,
}

_SCORE_DIMENSION_WEIGHTS_V1 = {
    "clarity": 1.35,
    "signal_density": 1.20,
    "novelty": 1.10,
    "testability": 1.25,
    "pressure_worthiness": 1.10,
    "calibration_value": 1.15,
    "cross_domain_resonance": 1.05,
    "compression_value": 0.95,
    "risk_of_false_pattern": -1.20,
    "boundary_sensitivity": 0.55,
}

_CANDIDATE_TYPE_TO_PRESSURE_TYPE_V1 = {
    "source_signal": "edge_case",
    "generated_source_signal": "counterexample",
    "hidden_rule_candidate": "counterexample_search",
    "operator_candidate": "operator_substitution",
    "translation_candidate": "false_pattern_insertion",
    "structural_match_candidate": "boundary_case",
    "motif_candidate": "noise_injection",
    "gap_hypothesis": "scale_shift",
    "pressure_result": "counterexample_search",
    "correction_lesson": "control_case",
    "dialectic_turn": "adversarial_signal",
    "calibration_record": "control_case",
    "unknown": "edge_case",
}

_CANDIDATE_TYPE_TO_PREDICTION_TYPE_V1 = {
    "source_signal": "probe_prediction",
    "generated_source_signal": "probe_prediction",
    "hidden_rule_candidate": "gap_prediction",
    "operator_candidate": "operator_prediction",
    "translation_candidate": "translation_prediction",
    "structural_match_candidate": "gap_prediction",
    "motif_candidate": "motif_prediction",
    "gap_hypothesis": "gap_prediction",
    "pressure_result": "rule_pressure_prediction",
    "correction_lesson": "rule_pressure_prediction",
    "dialectic_turn": "rule_pressure_prediction",
    "calibration_record": "probe_prediction",
    "unknown": "unknown",
}

_CANDIDATE_TYPE_TO_PRIORITY_BASE_V1 = {
    "source_signal": 52.0,
    "generated_source_signal": 58.0,
    "hidden_rule_candidate": 68.0,
    "operator_candidate": 72.0,
    "translation_candidate": 66.0,
    "structural_match_candidate": 63.0,
    "motif_candidate": 61.0,
    "gap_hypothesis": 67.0,
    "pressure_result": 74.0,
    "correction_lesson": 69.0,
    "dialectic_turn": 70.0,
    "calibration_record": 64.0,
    "unknown": 50.0,
}


def _compact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.replace("\r", " ").replace("\n", " ").split())
    return _compact_text(str(value))


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    if overrides:
        data.update(overrides)
    return data


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    if isinstance(value, Mapping):
        return list(value.values())
    return [value]


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"1", "true", "yes", "y", "on"}:
            return True
        if raw in {"0", "false", "no", "n", "off"}:
            return False
    return bool(value)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda item: str(item)):
            key_text = str(key)
            lower = key_text.lower()
            if any(fragment in lower for fragment in _FORBIDDEN_KEY_FRAGMENTS_V1):
                continue
            out[key_text] = _json_safe(value[key])
        return out
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_compact_text)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _compact_text(value)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_choice(value: Any, allowed: tuple[str, ...], default: str) -> str:
    raw = _compact_text(value).lower()
    if not raw:
        return default
    return raw if raw in allowed else default


def _normalize_candidate_type(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_CANDIDATE_TYPES_V1, "unknown")


def _normalize_score_label(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_SCORE_LABELS_V1, "unknown")


def _normalize_overall_priority(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_OVERALL_PRIORITIES_V1, "unknown")


def _normalize_rank_bucket(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_RANK_BUCKETS_V1, "unknown")


def _normalize_public_claim_status(value: Any, default: str = "internal_candidate_only") -> str:
    return _normalize_choice(value, _ALLOWED_PUBLIC_CLAIM_STATUSES_V1, default)


def _contains_forbidden_text(value: Any) -> bool:
    text = _compact_text(value).lower()
    return any(marker in text for marker in _FORBIDDEN_TEXT_MARKERS_V1)


def _default_safe_metadata(engine_name: str, engine_family: str, research_mode: str) -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_provider_calls": True,
        "no_tool_execution": True,
        "no_persistence": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_behavior_pack_promotion": True,
        "no_final_answer": True,
        "no_public_claims": True,
        "perspicuity_is_not_a_gate": True,
        "no_live_ingestion": True,
        "no_network": True,
        "no_weslr_io": True,
        "no_autonomous_self_modification": True,
        "no_retrieval_execution": True,
        "no_code_as_action": True,
        "engine_name": engine_name,
        "engine_family": engine_family,
        "research_mode": research_mode,
    }


def _default_boundary_status() -> dict[str, Any]:
    denied = build_default_cognitive_research_denied_authority_v1()
    return {
        "status": "metadata_only",
        "runtime_wiring_authority": False,
        "runtime_authority": False,
        "tool_authority": False,
        "provider_authority": False,
        "provider_model_call_authority": False,
        "llm_authority": False,
        "chat_responder_authority": False,
        "final_answer_generation_authority": False,
        "public_claim_authority": False,
        "retrieval_tool_authority": False,
        "filesystem_authority": False,
        "network_authority": False,
        "subprocess_authority": False,
        "weslr_io_authority": False,
        "persistence_authority": False,
        "persistence_database_write_authority": False,
        "real_memory_mutation_authority": False,
        "real_project_mutation_authority": False,
        "behavior_change_authority": False,
        "behavior_pack_promotion_authority": False,
        "autonomous_self_modification_authority": False,
        "official_intelligence_claim_authority": False,
        "public_discovery_claim_authority": False,
        "boundary_notes": "metadata-only; fail closed; no runtime, provider, tool, persistence, or public-export authority",
        "denied_authority": denied,
    }


def _candidate_default_summary(candidate_type: str) -> str:
    return {
        "source_signal": "Source signal candidate for internal perspicuity ranking.",
        "generated_source_signal": "Generated source signal candidate for internal perspicuity ranking.",
        "hidden_rule_candidate": "Hidden-rule candidate for internal perspicuity ranking.",
        "operator_candidate": "Operator candidate for internal perspicuity ranking.",
        "translation_candidate": "Translation candidate for internal perspicuity ranking.",
        "structural_match_candidate": "Structural match candidate for internal perspicuity ranking.",
        "motif_candidate": "Motif candidate for internal perspicuity ranking.",
        "gap_hypothesis": "Gap hypothesis candidate for internal perspicuity ranking.",
        "pressure_result": "Pressure-result candidate for internal perspicuity ranking.",
        "correction_lesson": "Correction lesson candidate for internal perspicuity ranking.",
        "dialectic_turn": "Dialectic turn candidate for internal perspicuity ranking.",
        "calibration_record": "Calibration record candidate for internal perspicuity ranking.",
        "unknown": "Unknown candidate for internal perspicuity ranking.",
    }.get(candidate_type, "Unknown candidate for internal perspicuity ranking.")


def _label_to_value(label: str) -> float:
    return _SCORE_LABEL_TO_VALUE_V1.get(_normalize_score_label(label), 40.0)


def _value_to_label(value: float) -> str:
    if value < 12.5:
        return "none"
    if value < 37.5:
        return "low"
    if value < 62.5:
        return "medium"
    return "high"


def _priority_from_value(value: float) -> str:
    if value < 18.0:
        return "drop"
    if value < 30.0:
        return "archive"
    if value < 42.0:
        return "watch"
    if value < 54.0:
        return "probe"
    if value < 66.0:
        return "pressure_test"
    if value < 78.0:
        return "calibrate"
    return "promote_to_next_internal_step"


def _rank_bucket_from_priority(priority: str) -> str:
    return {
        "promote_to_next_internal_step": "top",
        "calibrate": "high",
        "pressure_test": "high",
        "probe": "medium",
        "watch": "low",
        "archive": "low",
        "drop": "blocked",
        "unknown": "unknown",
    }.get(priority, "unknown")


def _candidate_seed(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": _compact_text(payload.get("candidate_id")) or f"perspicuity-{_stable_digest({'source_engine_name': payload.get('source_engine_name'), 'source_run_id': payload.get('source_run_id'), 'candidate_type': payload.get('candidate_type'), 'candidate_summary': payload.get('candidate_summary')})[:12]}",
        "source_engine_name": _compact_text(payload.get("source_engine_name") or "unknown_engine").lower() or "unknown_engine",
        "source_run_id": _compact_text(payload.get("source_run_id")) or f"source-run-{_stable_digest({'engine': payload.get('source_engine_name'), 'summary': payload.get('candidate_summary')})[:12]}",
        "candidate_type": _normalize_candidate_type(payload.get("candidate_type") or "unknown"),
        "candidate_summary": _compact_text(payload.get("candidate_summary") or _candidate_default_summary(_normalize_candidate_type(payload.get("candidate_type") or "unknown"))),
        "candidate_scope": _compact_text(payload.get("candidate_scope") or payload.get("known_scope") or "metadata-only scope") or "metadata-only scope",
        "known_scope": _compact_text(payload.get("known_scope") or "metadata-only scope") or "metadata-only scope",
        "failure_scope": _compact_text(payload.get("failure_scope") or "bounded failure scope") or "bounded failure scope",
        "uncertainty_factors": _ensure_list(payload.get("uncertainty_factors")) or ["candidate remains provisional"],
        "invalidation_signals": _ensure_list(payload.get("invalidation_signals")) or ["not yet invalidated"],
        "public_claim_status": _normalize_public_claim_status(payload.get("public_claim_status") or "internal_candidate_only"),
    }


def build_perspicuity_candidate_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    return _json_safe(_candidate_seed(data))


def _dimension_defaults(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidate_type = _normalize_candidate_type(candidate.get("candidate_type"))
    base = {
        "clarity": ("high", "Candidate summary makes the structure easy to inspect.", [candidate.get("candidate_id")], "Clarity tracks whether the candidate can be seen directly."),
        "signal_density": ("high", "Candidate packs useful signals into a bounded summary.", [candidate.get("candidate_id")], "Signal density tracks how much usable information is present."),
        "novelty": ("medium", "Candidate may extend or recombine known structure.", [candidate.get("source_engine_name")], "Novelty is provisional until compared."),
        "testability": ("medium", "Candidate can be probed without authorizing execution.", [candidate.get("candidate_id")], "Testability tracks how cleanly it can be checked."),
        "pressure_worthiness": ("medium", "Candidate may benefit from rule pressure or counterexample search.", [candidate.get("candidate_id")], "Pressure worthiness tracks whether pressure is likely useful."),
        "calibration_value": ("medium", "Candidate may improve calibration if paired with later observation.", [candidate.get("candidate_id")], "Calibration value tracks whether future observation can refine it."),
        "cross_domain_resonance": ("medium", "Candidate may transfer across neighboring engine families.", [candidate.get("source_engine_name")], "Cross-domain resonance tracks transferability."),
        "compression_value": ("medium", "Candidate may compress a hidden pattern into a smaller summary.", [candidate.get("candidate_id")], "Compression value tracks whether the candidate helps shorten a structure."),
        "risk_of_false_pattern": ("medium", "Candidate could overfit a pattern without enough evidence.", [candidate.get("candidate_id")], "Risk tracks the chance of seeing a false pattern."),
        "boundary_sensitivity": ("medium", "Candidate touches a boundary that deserves careful internal review.", [candidate.get("candidate_id")], "Boundary sensitivity tracks proximity to policy or scope edges."),
    }
    if candidate_type in {"source_signal", "generated_source_signal"}:
        base["clarity"] = ("high", "Signal-oriented candidate is easy to inspect as metadata.", [candidate.get("candidate_id")], "Clarity stays high for signal candidates.")
        base["signal_density"] = ("high", "Signal candidate carries compact evidence-rich metadata.", [candidate.get("candidate_id")], "Signal density stays high for signal candidates.")
        base["testability"] = ("high", "Signal candidate can be probed through later comparisons.", [candidate.get("candidate_id")], "Signal candidates are testable by comparison.")
    elif candidate_type in {"operator_candidate", "dialectic_turn"}:
        base["pressure_worthiness"] = ("high", "Operator-like candidate is pressure-worthy for internal comparison.", [candidate.get("candidate_id")], "Pressure worthiness is high for operator or turn candidates.")
        base["testability"] = ("high", "Operator-like candidate can be checked with counterexamples.", [candidate.get("candidate_id")], "Operator candidates are easy to pressure test.")
        base["compression_value"] = ("high", "Operator-like candidate often compresses a reusable rule.", [candidate.get("candidate_id")], "Compression value can be high for operator candidates.")
    elif candidate_type in {"translation_candidate"}:
        base["cross_domain_resonance"] = ("high", "Translation candidate can bridge neighboring interpretations.", [candidate.get("source_engine_name")], "Translation candidates often resonate across domains.")
        base["compression_value"] = ("high", "Translation candidate may compress ambiguity into a clearer form.", [candidate.get("candidate_id")], "Compression can be useful for translation candidates.")
    elif candidate_type in {"structural_match_candidate", "motif_candidate", "gap_hypothesis"}:
        base["novelty"] = ("high", "Candidate may reveal structure that is not yet obvious.", [candidate.get("candidate_id")], "Novelty can be high for structure-finding candidates.")
        base["cross_domain_resonance"] = ("high", "Candidate may transfer or align across domains.", [candidate.get("source_engine_name")], "Resonance is often useful for structural candidates.")
    elif candidate_type in {"pressure_result", "correction_lesson"}:
        base["calibration_value"] = ("high", "Outcome-linked candidate is especially useful for calibration.", [candidate.get("candidate_id")], "Calibration value is high when results or lessons are observed.")
        base["risk_of_false_pattern"] = ("low", "Observed pressure result reduces speculative risk.", [candidate.get("candidate_id")], "Risk of false pattern is lower for observed results.")
    elif candidate_type in {"calibration_record"}:
        base["calibration_value"] = ("high", "Calibration record is directly useful for ranking follow-up.", [candidate.get("candidate_id")], "Calibration value is high for calibration records.")
        base["clarity"] = ("high", "Calibration record is already structured metadata.", [candidate.get("candidate_id")], "Calibration records are usually clear.")
    elif candidate_type == "unknown":
        base["risk_of_false_pattern"] = ("high", "Unknown candidate should be treated cautiously.", [candidate.get("candidate_id")], "Risk of false pattern stays high for unknowns.")
    return [
        {
            "dimension": dimension,
            "score_label": label,
            "reason": reason,
            "supporting_metadata_refs": _ensure_list(refs),
            "uncertainty_note": note,
        }
        for dimension, (label, reason, refs, note) in base.items()
    ]


def build_perspicuity_dimension_score_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    dimension = _compact_text(data.get("dimension") or data.get("score_dimension")).lower()
    score_label = _normalize_score_label(data.get("score_label"))
    if not dimension:
        dimension = "unknown"
    reason = _compact_text(data.get("reason") or "perspicuity dimension score is internal ranking metadata only")
    refs = _ensure_list(data.get("supporting_metadata_refs"))
    uncertainty_note = _compact_text(data.get("uncertainty_note") or "ranking remains provisional")
    return _json_safe({
        "dimension": dimension,
        "score_label": score_label,
        "reason": reason,
        "supporting_metadata_refs": refs,
        "uncertainty_note": uncertainty_note,
    })


def _dimension_scores_from_candidate(candidate: Mapping[str, Any], payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_scores = _ensure_list(payload.get("dimension_scores") or payload.get("perspicuity_dimension_scores"))
    if raw_scores:
        scores = [build_perspicuity_dimension_score_v1(item) for item in raw_scores]
    else:
        scores = _dimension_defaults(candidate)
    present = {_compact_text(score.get("dimension")).lower() for score in scores}
    for dimension in _ALLOWED_SCORE_DIMENSIONS_V1:
        if dimension not in present:
            scores.append(
                build_perspicuity_dimension_score_v1(
                    {
                        "dimension": dimension,
                        "score_label": "unknown",
                        "reason": f"Default internal fill for {dimension}.",
                        "supporting_metadata_refs": [candidate.get("candidate_id")],
                        "uncertainty_note": "filled by builder to keep the scorecard complete",
                    }
                )
            )
    return scores


def _scorecard_priority(candidate: Mapping[str, Any], dimension_scores: list[Mapping[str, Any]]) -> str:
    values: list[float] = []
    risk_penalty = 0.0
    boundary_boost = 0.0
    for score in dimension_scores:
        dimension = _compact_text(score.get("dimension")).lower()
        label_value = _label_to_value(score.get("score_label"))
        if dimension == "risk_of_false_pattern":
            risk_penalty = label_value
        elif dimension == "boundary_sensitivity":
            boundary_boost = label_value
        else:
            values.append(label_value * _SCORE_DIMENSION_WEIGHTS_V1.get(dimension, 1.0))
    base_value = _CANDIDATE_TYPE_TO_PRIORITY_BASE_V1.get(_normalize_candidate_type(candidate.get("candidate_type")), 50.0)
    positive_value = sum(values) / max(len(values), 1)
    adjusted = base_value * 0.30 + positive_value * 0.70 + (boundary_boost * 0.10) - (risk_penalty * 0.25)
    return _priority_from_value(_clamp(adjusted))


def build_perspicuity_scorecard_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    candidate = data.get("candidate") if isinstance(data.get("candidate"), Mapping) else _candidate_seed(data)
    dimension_scores = _dimension_scores_from_candidate(candidate, data)
    overall_priority = _normalize_overall_priority(data.get("overall_priority") or _scorecard_priority(candidate, dimension_scores))
    recommended_next_action = _compact_text(
        data.get("recommended_next_action")
        or {
            "drop": "archive and ignore for now",
            "archive": "archive for later context",
            "watch": "watch for a cleaner next signal",
            "probe": "probe with a narrow internal question",
            "pressure_test": "send to pressure testing next",
            "calibrate": "calibrate against later observation",
            "promote_to_next_internal_step": "promote to the next internal step",
            "unknown": "hold for internal review",
        }.get(overall_priority, "hold for internal review")
    )
    scorecard = {
        "scorecard_id": _compact_text(data.get("scorecard_id")) or f"scorecard-{_stable_digest({'candidate_id': candidate['candidate_id'], 'priority': overall_priority})[:12]}",
        "candidate_id": candidate["candidate_id"],
        "dimension_scores": dimension_scores,
        "overall_priority": overall_priority,
        "priority_reason": _compact_text(data.get("priority_reason") or "Perspicuity ranks investigation usefulness only; not authority or execution."),
        "recommended_next_action": recommended_next_action,
        "do_not_use_as_truth": True if data.get("do_not_use_as_truth") is None else _safe_bool(data.get("do_not_use_as_truth"), True),
        "public_claim_authorized": _safe_bool(data.get("public_claim_authorized", False)),
        "runtime_action_authorized": _safe_bool(data.get("runtime_action_authorized", False)),
        "behavior_promotion_authorized": _safe_bool(data.get("behavior_promotion_authorized", False)),
    }
    return _json_safe(scorecard)


def _ranking_bucket_and_reason(scorecard: Mapping[str, Any], candidate: Mapping[str, Any]) -> tuple[str, str]:
    priority = _normalize_overall_priority(scorecard.get("overall_priority"))
    bucket = _rank_bucket_from_priority(priority)
    if bucket == "blocked":
        return bucket, "Candidate is not suitable for internal ranking right now."
    if priority == "promote_to_next_internal_step":
        return bucket, "Candidate is worth advancing to the next internal step."
    if priority == "calibrate":
        return bucket, "Candidate is strong enough to calibrate against additional observations."
    if priority == "pressure_test":
        return bucket, "Candidate is pressure-worthy and should be tested internally."
    if priority == "probe":
        return bucket, "Candidate is worth a narrow internal probe."
    if priority == "watch":
        return bucket, "Candidate is useful but still needs more signal before action."
    if priority in {"archive", "drop"}:
        return bucket, "Candidate is better kept as background context for now."
    return bucket, "Candidate ranking remains provisional."


def build_perspicuity_ranking_entry_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    candidate = data.get("candidate") if isinstance(data.get("candidate"), Mapping) else _candidate_seed(data)
    scorecard = data.get("scorecard") if isinstance(data.get("scorecard"), Mapping) else build_perspicuity_scorecard_v1({"candidate": candidate, **data})
    rank_bucket = _normalize_rank_bucket(data.get("rank_bucket") or _ranking_bucket_and_reason(scorecard, candidate)[0])
    rank_reason = _compact_text(data.get("rank_reason") or _ranking_bucket_and_reason(scorecard, candidate)[1])
    next_probe = _compact_text(
        data.get("next_best_probe")
        or data.get("next_probe")
        or f"Probe {candidate['candidate_summary']} with a narrow internal question."
    )
    next_pressure_test = _compact_text(
        data.get("next_best_pressure_test")
        or data.get("next_pressure_test")
        or f"Pressure-test {candidate['candidate_summary']} against a bounded counterexample."
    )
    prediction_type = _CANDIDATE_TYPE_TO_PREDICTION_TYPE_V1.get(candidate["candidate_type"], "unknown")
    calibration_source_run = {
        "run_id": _compact_text(data.get("source_run_id") or candidate["source_run_id"] or f"perspicuity-run-{_stable_digest({'candidate_id': candidate['candidate_id'], 'bucket': rank_bucket})[:12]}") ,
        "engine_name": ENGINE_NAME_V1,
        "engine_family": ENGINE_FAMILY_V1,
        "research_mode": _normalize_choice(data.get("research_mode") or "synthetic_test", _ALLOWED_RESEARCH_MODES_V1, "synthetic_test"),
        "input_artifact_ref": _compact_text(data.get("input_artifact_ref") or f"candidate:{candidate['candidate_id']}"),
        "input_artifact_type": _compact_text(data.get("input_artifact_type") or "perspicuity-candidate"),
        "input_summary": candidate["candidate_summary"],
        "hypotheses": [candidate["candidate_summary"]],
        "predictions": [f"{candidate['candidate_type']} may rank {scorecard['overall_priority']} for internal investigation."],
        "probes": [next_probe],
        "compressed_lesson": "Perspicuity ranks usefulness for investigation, not truth or authorization.",
    }
    calibration_prediction = data.get("calibration_prediction")
    if not isinstance(calibration_prediction, Mapping):
        calibration_prediction = build_forecast_calibration_record_v1(
            source_run=calibration_source_run,
            record_id=_compact_text(data.get("calibration_record_id")) or f"calibration-{_stable_digest({'candidate_id': candidate['candidate_id'], 'probe': next_probe})[:12]}",
            prediction_id=_compact_text(data.get("prediction_id")) or f"prediction-{_stable_digest({'candidate_id': candidate['candidate_id'], 'pressure': next_pressure_test})[:12]}",
            prediction_statement=f"{candidate['candidate_type']} candidate may remain {scorecard['overall_priority']}",
            prediction_type=prediction_type,
            prediction_scope=_compact_text(data.get("prediction_scope") or candidate["candidate_scope"]) or candidate["candidate_scope"],
            confidence_before=_clamp(_safe_float(data.get("confidence_before"), 0.60)),
            confidence_after=_clamp(_safe_float(data.get("confidence_after"), 0.55)),
            confidence_basis=_compact_text(data.get("confidence_basis") or "internal perspicuity ranking only") or "internal perspicuity ranking only",
            uncertainty_factors=_ensure_list(data.get("uncertainty_factors")) or candidate["uncertainty_factors"],
            invalidation_signals=_ensure_list(data.get("invalidation_signals")) or candidate["invalidation_signals"],
            expected_outcome=_compact_text(data.get("expected_outcome") or next_probe) or next_probe,
            observed_outcome=_compact_text(data.get("observed_outcome") or ""),
            outcome_status=_compact_text(data.get("outcome_status") or "not_observed_yet") or "not_observed_yet",
            calibration_result=_compact_text(data.get("calibration_result") or "not_yet_calibrated") or "not_yet_calibrated",
            error_type=_compact_text(data.get("error_type") or "none") or "none",
            assumptions_used=_ensure_list(data.get("assumptions_used")) or [candidate["candidate_summary"]],
            assumptions_failed=_ensure_list(data.get("assumptions_failed")),
            missing_signals=_ensure_list(data.get("missing_signals")),
            conflicting_signals=_ensure_list(data.get("conflicting_signals")),
            correction=_compact_text(data.get("correction") or ""),
            compressed_lesson=_compact_text(data.get("compressed_lesson") or "") or "",
            future_adjustment=_compact_text(data.get("future_adjustment") or "keep ranking metadata-only") or "keep ranking metadata-only",
        )
    blocked_reason = _compact_text(data.get("blocked_reason") or ("blocked because internal ranking is not yet suitable" if rank_bucket == "blocked" else "not blocked"))
    ranking = {
        "ranking_id": _compact_text(data.get("ranking_id")) or f"ranking-{_stable_digest({'candidate_id': candidate['candidate_id'], 'bucket': rank_bucket, 'reason': rank_reason})[:12]}",
        "candidate_id": candidate["candidate_id"],
        "rank_bucket": rank_bucket,
        "rank_reason": rank_reason,
        "next_best_probe": next_probe,
        "next_best_pressure_test": next_pressure_test,
        "calibration_prediction": calibration_prediction,
        "blocked_reason": blocked_reason,
    }
    return _json_safe(ranking)


def _safe_metadata_flags(candidate: Mapping[str, Any], candidate_count: int) -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_provider_calls": True,
        "no_tool_execution": True,
        "no_persistence": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_behavior_pack_promotion": True,
        "no_final_answer": True,
        "no_public_claims": True,
        "perspicuity_is_not_a_gate": True,
        "engine_name": ENGINE_NAME_V1,
        "engine_family": ENGINE_FAMILY_V1,
        "research_mode": candidate.get("research_mode", "internal_exploration") if isinstance(candidate, Mapping) else "internal_exploration",
        "candidate_count": candidate_count,
    }


def _build_source_signal_for_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return build_source_signal_metadata_v1(
        {
            "signal_origin": "metadata_only",
            "source_ref": candidate["source_run_id"],
            "summary": candidate["candidate_summary"],
            "signal_type": f"perspicuity_{candidate['candidate_type']}_candidate",
            "trust_level": "bounded",
            "poison_risk": "low",
            "injection_risk": "low",
            "raw_content_included": False,
            "raw_content_ref_only": True,
            "normalization_required": True,
            "engine_name": candidate["source_engine_name"],
        }
    )


def _build_generated_source_signal_for_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return build_generated_source_signal_metadata_v1(
        {
            "parent_suggestion_id": candidate["candidate_id"],
            "generation_reason": f"perspicuity ranking mutation from {candidate['candidate_type']}",
            "mutation_type": "perspicuity_relevance_mutation",
            "expected_pressure": "edge_case",
            "target_uncertainty": candidate["failure_scope"],
            "generated_signal_summary": candidate["candidate_summary"],
            "safe_to_reingest": True,
            "raw_generated_content_included": False,
        }
    )


def _build_rule_pressure_test_for_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    pressure_type = _CANDIDATE_TYPE_TO_PRESSURE_TYPE_V1.get(candidate["candidate_type"], "edge_case")
    return build_rule_pressure_test_metadata_v1(
        {
            "target": {
                "source_engine_name": candidate["source_engine_name"],
                "source_run_id": candidate["source_run_id"],
                "target_type": candidate["candidate_type"],
                "target_summary": candidate["candidate_summary"],
                "candidate_rule_or_operator": candidate["candidate_summary"],
                "claimed_scope": candidate["known_scope"],
                "known_scope": candidate["known_scope"],
                "uncertainty_factors": candidate["uncertainty_factors"],
                "invalidation_signals": candidate["invalidation_signals"],
                "public_claim_status": candidate["public_claim_status"],
            },
            "target_rule_or_operator": candidate["candidate_summary"],
            "pressure_type": pressure_type,
            "mutated_input_summary": f"Perspicuity pressure test for {candidate['candidate_type']}.",
            "expected_behavior": "remain bounded",
            "observed_behavior": "pending",
            "result": "pending",
            "failure_mode": "none",
            "scope_update": "metadata_only",
            "safe_to_run_as_metadata": True,
        }
    )


def build_perspicuity_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    research_mode = _normalize_choice(data.get("research_mode") or "internal_exploration", _ALLOWED_RESEARCH_MODES_V1, "internal_exploration")
    input_artifact_ref = _compact_text(data.get("input_artifact_ref") or "artifact:perspicuity") or "artifact:perspicuity"
    input_artifact_type = _compact_text(data.get("input_artifact_type") or "perspicuity-candidate") or "perspicuity-candidate"
    candidate_payloads = _ensure_list(data.get("perspicuity_candidates"))
    if not candidate_payloads:
        candidate_payloads = [
            {
                "source_engine_name": data.get("source_engine_name") or "unknown_engine",
                "source_run_id": data.get("source_run_id") or f"source-run-{_stable_digest({'summary': data.get('candidate_summary') or data.get('input_summary') or 'perspicuity'})[:12]}",
                "candidate_type": data.get("candidate_type") or "unknown",
                "candidate_summary": data.get("candidate_summary") or data.get("input_summary") or "perspicuity candidate",
                "candidate_scope": data.get("candidate_scope") or data.get("known_scope") or "metadata-only scope",
                "known_scope": data.get("known_scope") or "metadata-only scope",
                "failure_scope": data.get("failure_scope") or "bounded failure scope",
                "uncertainty_factors": data.get("uncertainty_factors") or ["candidate remains provisional"],
                "invalidation_signals": data.get("invalidation_signals") or ["not yet invalidated"],
                "public_claim_status": data.get("public_claim_status") or "internal_candidate_only",
            }
        ]
    candidates = [build_perspicuity_candidate_v1(candidate) for candidate in candidate_payloads]
    primary_candidate = candidates[0]
    dimension_scores = _dimension_scores_from_candidate(primary_candidate, data)
    scorecard = build_perspicuity_scorecard_v1({"candidate": primary_candidate, "dimension_scores": dimension_scores, **data})
    ranking_payloads = _ensure_list(data.get("perspicuity_ranking_entries"))
    if not ranking_payloads:
        ranking_payloads = [
            {
                "candidate": candidate,
                "scorecard": scorecard,
                "research_mode": research_mode,
                "input_artifact_ref": input_artifact_ref,
                "input_artifact_type": input_artifact_type,
            }
            for candidate in candidates
        ]
    ranking_entries = [build_perspicuity_ranking_entry_v1(entry) for entry in ranking_payloads]

    source_signal = data.get("source_signal")
    if not isinstance(source_signal, Mapping):
        source_signal = _build_source_signal_for_candidate(primary_candidate)
    generated_source_signals = _ensure_list(data.get("generated_source_signals")) or [_build_generated_source_signal_for_candidate(primary_candidate)]
    rule_pressure_tests = _ensure_list(data.get("rule_pressure_tests")) or [_build_rule_pressure_test_for_candidate(primary_candidate)]

    hypotheses = _ensure_list(data.get("hypotheses")) or [primary_candidate["candidate_summary"]]
    predictions = _ensure_list(data.get("predictions")) or [f"{primary_candidate['candidate_type']} candidate may remain {scorecard['overall_priority']}."]
    confidence_map = _json_safe(data.get("confidence_map")) if data.get("confidence_map") is not None else {primary_candidate["candidate_id"]: _clamp(_label_to_value(scorecard["overall_priority"]) / 100.0 * 100.0)}
    uncertainty_map = _json_safe(data.get("uncertainty_map")) if data.get("uncertainty_map") is not None else {
        primary_candidate["candidate_id"]: {
            "uncertainty_factors": primary_candidate["uncertainty_factors"],
            "invalidation_signals": primary_candidate["invalidation_signals"],
        }
    }
    verification_steps = _ensure_list(data.get("verification_steps")) or ["rank candidate", "probe internal clarity", "pressure test internal usefulness", "calibrate follow-up"]
    human_verification_steps = _ensure_list(data.get("human_verification_steps")) or ["owner preview review"]
    machine_verification_steps = _ensure_list(data.get("machine_verification_steps")) or ["py_compile", "pytest", "release_gate", "release_check"]
    falsification_probes = _ensure_list(data.get("falsification_probes")) or [ranking_entries[0]["next_best_probe"]]
    probes = _ensure_list(data.get("probes")) or [primary_candidate["candidate_summary"]]
    outcomes = _ensure_list(data.get("outcomes")) or [f"{primary_candidate['candidate_type']} remains unobserved; internal ranking only."]
    corrections = _ensure_list(data.get("corrections")) or [f"Use {scorecard['recommended_next_action']} as the next internal step."]
    next_experiments = _ensure_list(data.get("next_experiments")) or [ranking_entries[0]["next_best_probe"]]
    suggestion_store_updates = _ensure_list(data.get("suggestion_store_updates")) or [
        {
            "suggestion_id": f"suggestion-{primary_candidate['candidate_id']}",
            "candidate_id": primary_candidate["candidate_id"],
            "status_action": "promote" if scorecard["overall_priority"] in {"calibrate", "promote_to_next_internal_step", "pressure_test", "probe"} else "archive",
            "reason": scorecard["priority_reason"],
            "scope_update": primary_candidate["candidate_scope"],
        }
    ]

    calibration_record = data.get("calibration_record")
    if not isinstance(calibration_record, Mapping):
        calibration_record = ranking_entries[0]["calibration_prediction"]

    perspicuity_score = build_perspicuity_score_metadata_v1(
        {
            "clarity": _label_to_value(next(item["score_label"] for item in dimension_scores if item["dimension"] == "clarity")),
            "signal_density": _label_to_value(next(item["score_label"] for item in dimension_scores if item["dimension"] == "signal_density")),
            "novelty": _label_to_value(next(item["score_label"] for item in dimension_scores if item["dimension"] == "novelty")),
            "gap_pressure": _label_to_value(next(item["score_label"] for item in dimension_scores if item["dimension"] == "pressure_worthiness")),
            "verification_potential": _label_to_value(next(item["score_label"] for item in dimension_scores if item["dimension"] == "testability")),
            "recurrence": _label_to_value(next(item["score_label"] for item in dimension_scores if item["dimension"] == "compression_value")),
            "cross_domain_resonance": _label_to_value(next(item["score_label"] for item in dimension_scores if item["dimension"] == "cross_domain_resonance")),
            "score": _clamp(sum(_label_to_value(item["score_label"]) for item in dimension_scores if item["dimension"] != "risk_of_false_pattern") / 8.0),
            "reason": "Perspicuity ranks internal usefulness only; never authority or execution.",
        }
    )

    packet = build_cognitive_research_run_v1(
        {
            "schema_version": SCHEMA_VERSION_V1,
            "run_id": _compact_text(data.get("run_id")) or f"perspicuity-run-{_stable_digest({'candidate_id': primary_candidate['candidate_id'], 'priority': scorecard['overall_priority']})[:12]}",
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": research_mode,
            "source_scope": "metadata_only",
            "input_artifact_ref": input_artifact_ref,
            "input_artifact_type": input_artifact_type,
            "input_summary": _compact_text(data.get("input_summary") or primary_candidate["candidate_summary"]),
            "source_signal": source_signal,
            "observations": [candidate["candidate_summary"] for candidate in candidates],
            "extracted_signals": [candidate["candidate_type"] for candidate in candidates],
            "motif_candidates": [candidate["candidate_summary"] for candidate in candidates if candidate["candidate_type"] == "motif_candidate"],
            "operator_candidates": [candidate["candidate_summary"] for candidate in candidates if candidate["candidate_type"] == "operator_candidate"],
            "invariant_candidates": [candidate["candidate_summary"] for candidate in candidates if candidate["candidate_type"] == "structural_match_candidate"],
            "resonance_candidates": [candidate["candidate_summary"] for candidate in candidates if candidate["candidate_type"] in {"motif_candidate", "gap_hypothesis", "translation_candidate"}],
            "nonlinear_inspiration_candidates": [candidate["candidate_summary"] for candidate in candidates if candidate["candidate_type"] in {"operator_candidate", "gap_hypothesis", "translation_candidate"}],
            "hypotheses": hypotheses,
            "predictions": predictions,
            "confidence_map": confidence_map,
            "uncertainty_map": uncertainty_map,
            "verification_steps": verification_steps,
            "human_verification_steps": human_verification_steps,
            "machine_verification_steps": machine_verification_steps,
            "falsification_probes": falsification_probes,
            "probes": probes,
            "mutations": [signal["generated_signal_summary"] for signal in generated_source_signals],
            "generated_source_signals": generated_source_signals,
            "rule_pressure_tests": rule_pressure_tests,
            "outcomes": outcomes,
            "corrections": corrections,
            "compressed_lesson": _compact_text(data.get("compressed_lesson") or f"Perspicuity ranks {primary_candidate['candidate_type']} as internal investigation metadata only.") or f"Perspicuity ranks {primary_candidate['candidate_type']} as internal investigation metadata only.",
            "next_experiments": next_experiments,
            "suggestion_store_updates": suggestion_store_updates,
            "calibration_record": calibration_record,
            "public_claim_status": _normalize_public_claim_status(data.get("public_claim_status") or primary_candidate["public_claim_status"]),
            "public_gap_card_status": _normalize_public_claim_status(data.get("public_gap_card_status") or "public_export_blocked", "public_export_blocked"),
            "boundary_status": data.get("boundary_status") or _default_boundary_status(),
            "denied_authority": data.get("denied_authority") or build_default_cognitive_research_denied_authority_v1(),
            "safe_metadata": data.get("safe_metadata") or _safe_metadata_flags(primary_candidate, len(candidates)),
            "domain": _compact_text(data.get("domain") or "recursive research") or "recursive research",
            "domain_subtype": _compact_text(data.get("domain_subtype") or "perspicuity scorer") or "perspicuity scorer",
            "system_level": _compact_text(data.get("system_level") or "component") or "component",
            "artifact_scale": _compact_text(data.get("artifact_scale") or "bounded artifact") or "bounded artifact",
            "constraint_map": data.get("constraint_map") or {
                "runtime": "denied",
                "tool": "denied",
                "provider": "denied",
                "search": "denied",
                "persistence": "denied",
                "public_claims": "blocked",
                "answer_authority": "denied",
            },
            "safety_boundary": data.get("safety_boundary") or {"mode": "metadata_only", "non_actionable": True},
            "hazard_flags": data.get("hazard_flags") or [],
            "validation_route": data.get("validation_route") or ["metadata_only_validation", "fail_closed_safety_validation", "json_safe_copy_validation"],
            "required_expert_review": _safe_bool(data.get("required_expert_review", False)),
            "source_requirements": data.get("source_requirements") or {"provenance_required": True, "raw_storage_allowed": False, "side_effect_free": True},
            "experiment_type": _compact_text(data.get("experiment_type") or "metadata_only") or "metadata_only",
            "simulation_before_real_world": _safe_bool(data.get("simulation_before_real_world", True)),
            "non_actionable_research_only": _safe_bool(data.get("non_actionable_research_only", True)),
            "forbidden_action_notes": data.get("forbidden_action_notes") or [],
            "cross_domain_analogies": data.get("cross_domain_analogies") or [],
            "candidate_transfer_patterns": data.get("candidate_transfer_patterns") or [],
            "failure_mode_map": data.get("failure_mode_map") or [],
            "measurement_gap_map": data.get("measurement_gap_map") or [],
            "operator_gap_map": data.get("operator_gap_map") or [],
            "language_gap_map": data.get("language_gap_map") or [],
            "unknown_unknowns": data.get("unknown_unknowns") or [],
        }
    )
    packet.update(
        {
            "perspicuity_candidates": candidates,
            "perspicuity_dimension_scores": dimension_scores,
            "perspicuity_scorecard": scorecard,
            "perspicuity_ranking_entries": ranking_entries,
            "perspicuity_score": perspicuity_score,
        }
    )
    return _json_safe(packet)


def _validate_candidate(candidate: Any) -> list[str]:
    blocked: list[str] = []
    item = candidate if isinstance(candidate, Mapping) else {}
    if not _compact_text(item.get("candidate_id")):
        blocked.append("missing_candidate_id")
    if not _compact_text(item.get("candidate_summary")):
        blocked.append("missing_candidate_summary")
    if not _compact_text(item.get("candidate_type")):
        blocked.append("missing_candidate_type")
    if not _ensure_list(item.get("uncertainty_factors")):
        blocked.append("missing_uncertainty_factors")
    if not _ensure_list(item.get("invalidation_signals")):
        blocked.append("missing_invalidation_signals")
    if _normalize_candidate_type(item.get("candidate_type")) not in _ALLOWED_CANDIDATE_TYPES_V1:
        blocked.append("invalid_candidate_type")
    public_status = _compact_text(item.get("public_claim_status")).lower()
    if public_status not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        blocked.append("invalid_public_claim_status")
    blocked.extend(_validate_text_block("forbidden_candidate_text", item.get("candidate_summary"), item.get("candidate_scope"), item.get("known_scope"), item.get("failure_scope")))
    return blocked


def _validate_text_block(label: str, *values: Any) -> list[str]:
    return [label] if any(_contains_forbidden_text(value) for value in values) else []


def _validate_dimension_scores(dimension_scores: Any) -> list[str]:
    blocked: list[str] = []
    scores = _ensure_list(dimension_scores)
    if not scores:
        return ["scorecard_without_dimension_scores"]
    seen: set[str] = set()
    for index, item in enumerate(scores):
        if not isinstance(item, Mapping):
            blocked.append(f"invalid_dimension_score_{index}")
            continue
        dimension = _compact_text(item.get("dimension")).lower()
        score_label_raw = _compact_text(item.get("score_label")).lower()
        if dimension not in _ALLOWED_SCORE_DIMENSIONS_V1:
            blocked.append(f"invalid_score_dimension_{index}")
        if score_label_raw not in _ALLOWED_SCORE_LABELS_V1:
            blocked.append(f"invalid_score_label_{index}")
        if not _compact_text(item.get("reason")):
            blocked.append(f"dimension_score_missing_reason_{index}")
        seen.add(dimension)
    missing_dims = [dimension for dimension in _ALLOWED_SCORE_DIMENSIONS_V1 if dimension not in seen]
    if missing_dims:
        blocked.append("scorecard_dimension_scores_missing_required_dimensions")
    return blocked


def _validate_scorecard(scorecard: Any) -> list[str]:
    blocked: list[str] = []
    item = scorecard if isinstance(scorecard, Mapping) else {}
    if not _compact_text(item.get("scorecard_id")):
        blocked.append("missing_scorecard_id")
    if not _compact_text(item.get("candidate_id")):
        blocked.append("missing_candidate_id")
    dimension_scores = item.get("dimension_scores")
    blocked.extend(_validate_dimension_scores(dimension_scores))
    overall_priority = _normalize_overall_priority(item.get("overall_priority"))
    if overall_priority not in _ALLOWED_OVERALL_PRIORITIES_V1:
        blocked.append("invalid_overall_priority")
    if not _compact_text(item.get("priority_reason")):
        blocked.append("missing_priority_reason")
    if not _compact_text(item.get("recommended_next_action")):
        blocked.append("missing_recommended_next_action")
    if not _safe_bool(item.get("do_not_use_as_truth", False)):
        blocked.append("scorecard_treated_as_truth")
    if _safe_bool(item.get("public_claim_authorized", False)):
        blocked.append("scorecard_authorizes_public_claim")
    if _safe_bool(item.get("runtime_action_authorized", False)):
        blocked.append("scorecard_authorizes_runtime_action")
    if _safe_bool(item.get("behavior_promotion_authorized", False)):
        blocked.append("scorecard_authorizes_behavior_promotion")
    blocked.extend(_validate_text_block("scorecard_treated_as_truth_or_gate", item.get("priority_reason"), item.get("recommended_next_action")))
    return blocked


def _validate_ranking_entry(entry: Any) -> list[str]:
    blocked: list[str] = []
    item = entry if isinstance(entry, Mapping) else {}
    if not _compact_text(item.get("ranking_id")):
        blocked.append("missing_ranking_id")
    if not _compact_text(item.get("candidate_id")):
        blocked.append("missing_candidate_id")
    rank_bucket = _normalize_rank_bucket(item.get("rank_bucket"))
    if rank_bucket not in _ALLOWED_RANK_BUCKETS_V1:
        blocked.append("invalid_rank_bucket")
    if not _compact_text(item.get("rank_reason")):
        blocked.append("missing_rank_reason")
    if not _compact_text(item.get("next_best_probe")):
        blocked.append("ranking_entry_missing_next_probe")
    if not _compact_text(item.get("next_best_pressure_test")):
        blocked.append("ranking_entry_missing_next_pressure_test")
    if not isinstance(item.get("calibration_prediction"), Mapping):
        blocked.append("ranking_entry_missing_calibration_prediction")
    if not _compact_text(item.get("blocked_reason")):
        blocked.append("ranking_entry_missing_blocked_reason")
    if rank_bucket == "blocked" and not _compact_text(item.get("blocked_reason")):
        blocked.append("ranking_entry_blocked_without_reason")
    blocked.extend(_validate_text_block("ranking_entry_marked_truth_or_proof", item.get("rank_reason"), item.get("next_best_probe"), item.get("next_best_pressure_test"), item.get("blocked_reason")))
    if any(fragment in _compact_text(item.get("rank_reason") or item.get("blocked_reason") or item.get("next_best_probe")).lower() for fragment in ("proof", "truth", "discovery")):
        blocked.append("ranking_entry_marked_truth_or_proof")
    return blocked


def validate_perspicuity_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    validation = validate_cognitive_research_run_v1(packet)
    blocked_labels = list(validation["blocked_labels"])
    if _compact_text(raw.get("engine_name")) != ENGINE_NAME_V1:
        blocked_labels.append("invalid_engine_name")
    if _compact_text(raw.get("engine_family")) != ENGINE_FAMILY_V1:
        blocked_labels.append("invalid_engine_family")
    if _compact_text(raw.get("research_mode")).lower() not in _ALLOWED_RESEARCH_MODES_V1:
        blocked_labels.append("invalid_research_mode")
    candidate_items = _ensure_list(raw.get("perspicuity_candidates"))
    if not candidate_items:
        blocked_labels.append("missing_candidate_id")
    for candidate in candidate_items:
        blocked_labels.extend(_validate_candidate(candidate))
    scorecard = raw.get("perspicuity_scorecard")
    if not isinstance(scorecard, Mapping):
        blocked_labels.append("scorecard_without_dimension_scores")
    else:
        blocked_labels.extend(_validate_scorecard(scorecard))
    ranking_entries = _ensure_list(raw.get("perspicuity_ranking_entries"))
    if not ranking_entries:
        blocked_labels.append("ranking_entry_missing_next_probe")
    for entry in ranking_entries:
        blocked_labels.extend(_validate_ranking_entry(entry))
    if _compact_text(raw.get("public_claim_status")).lower() not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        blocked_labels.append("invalid_public_claim_status")
    if _contains_forbidden_text(raw.get("compressed_lesson")):
        blocked_labels.append("forbidden_packet_text")
    if any(fragment in _compact_text(raw.get("compressed_lesson") or raw.get("scorecard_reason") or "").lower() for fragment in ("proof", "truth", "discover", "safety gate replacement", "replace safety gate")):
        blocked_labels.append("scorecard_treated_as_truth")
    blocked = bool(blocked_labels)
    summary_text = _perspicuity_summary_text(raw, blocked, blocked_labels)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "classification": ENGINE_NAME_V1 if not blocked else "invalid",
        "engine_name": ENGINE_NAME_V1,
        "engine_family": ENGINE_FAMILY_V1,
        "research_mode": _compact_text(raw.get("research_mode")) or "internal_exploration",
        "public_claim_status": _normalize_public_claim_status(raw.get("public_claim_status") or "internal_candidate_only"),
        "public_gap_card_status": _normalize_public_claim_status(raw.get("public_gap_card_status") or "public_export_blocked", "public_export_blocked"),
        "llm_helper_role": validation["llm_helper_role"],
        "boundary_status": validation["boundary_status"],
        "summary_text": summary_text[:320],
        "packet": to_perspicuity_json_safe_v1(packet),
    }


def _perspicuity_summary_text(packet: Mapping[str, Any], blocked: bool, blocked_labels: list[str]) -> str:
    engine_name = _compact_text(packet.get("engine_name")) or ENGINE_NAME_V1
    engine_family = _compact_text(packet.get("engine_family")) or ENGINE_FAMILY_V1
    research_mode = _compact_text(packet.get("research_mode")) or "internal_exploration"
    candidates = _ensure_list(packet.get("perspicuity_candidates"))
    candidate_count = len(candidates)
    primary = candidates[0] if candidates and isinstance(candidates[0], Mapping) else {}
    candidate_type = _compact_text(primary.get("candidate_type")) or "unknown"
    overall_priority = _compact_text(packet.get("perspicuity_scorecard", {}).get("overall_priority") if isinstance(packet.get("perspicuity_scorecard"), Mapping) else "unknown")
    summary = (
        f"Perspicuity scorer: engine={engine_name}; family={engine_family}; mode={research_mode}; "
        f"candidates={candidate_count}; primary={candidate_type}; priority={overall_priority}."
    )
    if blocked:
        preview = ", ".join(blocked_labels[:4])
        return f"Blocked perspicuity scorer: {preview or 'validation failed'}. {summary}"
    return summary


def summarize_perspicuity_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_perspicuity_packet_v1(packet)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": _perspicuity_summary_text(validation["packet"], validation["blocked"], validation["blocked_labels"])[:320],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "classification": validation["classification"],
        "engine_name": validation["engine_name"],
        "engine_family": validation["engine_family"],
        "research_mode": validation["research_mode"],
        "public_claim_status": validation["public_claim_status"],
        "public_gap_card_status": validation["public_gap_card_status"],
        "llm_helper_role": validation["llm_helper_role"],
        "boundary_status": validation["boundary_status"],
        "packet": validation["packet"],
    }


def to_perspicuity_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def build_initial_perspicuity_examples_v1() -> list[dict[str, Any]]:
    specs = [
        {
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": "internal_exploration",
            "input_artifact_ref": "artifact:perspicuity-unknown-001",
            "input_artifact_type": "candidate",
            "input_summary": "Unknown Engine candidate with a compact structural signal.",
            "perspicuity_candidates": [
                {
                    "source_engine_name": "unknown_engine",
                    "source_run_id": "run-unknown-001",
                    "candidate_type": "source_signal",
                    "candidate_summary": "Unknown Engine source signal candidate.",
                    "candidate_scope": "bounded metadata-only scope",
                    "known_scope": "bounded metadata-only scope",
                    "failure_scope": "narrow failure scope",
                    "uncertainty_factors": ["source interpretation remains provisional"],
                    "invalidation_signals": ["no invalidation observed yet"],
                    "public_claim_status": "internal_candidate_only",
                }
            ],
        },
        {
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": "synthetic_test",
            "input_artifact_ref": "artifact:perspicuity-nonlinear-001",
            "input_artifact_type": "candidate",
            "input_summary": "Nonlinear Inspiration candidate with a transferred operator.",
            "perspicuity_candidates": [
                {
                    "source_engine_name": "nonlinear_inspiration_engine",
                    "source_run_id": "run-nonlinear-001",
                    "candidate_type": "operator_candidate",
                    "candidate_summary": "Transferred operator candidate from resonance analysis.",
                    "candidate_scope": "adjacent domain",
                    "known_scope": "adjacent domain",
                    "failure_scope": "bridge failure scope",
                    "uncertainty_factors": ["analogy may break under pressure"],
                    "invalidation_signals": ["bridge not yet tested"],
                    "public_claim_status": "not_public_claim",
                }
            ],
        },
        {
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": "calibration_replay",
            "input_artifact_ref": "artifact:perspicuity-rule-pressure-001",
            "input_artifact_type": "candidate",
            "input_summary": "Rule Pressure candidate with a pressure result.",
            "perspicuity_candidates": [
                {
                    "source_engine_name": "rule_pressure_engine",
                    "source_run_id": "run-rule-pressure-001",
                    "candidate_type": "pressure_result",
                    "candidate_summary": "Observed pressure result candidate.",
                    "candidate_scope": "bounded pressure scope",
                    "known_scope": "bounded pressure scope",
                    "failure_scope": "pressure failure scope",
                    "uncertainty_factors": ["result still needs calibration replay"],
                    "invalidation_signals": ["not yet calibrated"],
                    "public_claim_status": "internal_candidate_only",
                }
            ],
        },
        {
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": "frontier_mapping",
            "input_artifact_ref": "artifact:perspicuity-dialectic-001",
            "input_artifact_type": "candidate",
            "input_summary": "Dialectic Generator Loop candidate with a turn candidate.",
            "perspicuity_candidates": [
                {
                    "source_engine_name": "dialectic_generator_loop",
                    "source_run_id": "run-dialectic-001",
                    "candidate_type": "dialectic_turn",
                    "candidate_summary": "Dialectic turn candidate that compresses a next experiment.",
                    "candidate_scope": "bounded dialectic scope",
                    "known_scope": "bounded dialectic scope",
                    "failure_scope": "turn failure scope",
                    "uncertainty_factors": ["turn recommendation remains provisional"],
                    "invalidation_signals": ["turn not yet pressure tested"],
                    "public_claim_status": "public_export_blocked",
                }
            ],
        },
    ]
    return [build_perspicuity_packet_v1(spec) for spec in specs]
