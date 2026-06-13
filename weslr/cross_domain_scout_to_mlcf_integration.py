"""WESLR Cross-Domain Scout To MLCF Integration Helper V1.

Deterministic, metadata-only helpers for routing a validated cross-domain open
problem discovery scout packet into bounded MLCF planning metadata. This module
never fetches sources, ingests content, calls models, touches runtime, or writes
state.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from weslr.cross_domain_open_problem_discovery_scout import (
    build_initial_cross_domain_open_problem_discovery_scout_examples_v1,
    summarize_cross_domain_open_problem_discovery_scout_packet_v1,
    to_cross_domain_open_problem_discovery_scout_json_safe_v1,
    validate_cross_domain_open_problem_discovery_scout_packet_v1,
)

SCHEMA_VERSION_V1 = "weslr_cross_domain_scout_to_mlcf_integration_v1"

_ALLOWED_ROUTE_TYPES_V1 = (
    "scout_to_source_selection_evidence_plan",
    "scout_to_mlcf_cross_domain_candidate",
    "scout_to_metadata_only_source_locator_route",
    "scout_to_cognitive_research_run_packet",
    "scout_to_operator_review",
    "scout_to_archive_low_value_signal",
    "scout_blocked_by_safety",
)

_ALLOWED_NEXT_STEPS_V1 = (
    "operator_review",
    "prepare_source_selection_evidence_plan",
    "prepare_mlcf_cross_domain_candidate",
    "prepare_metadata_only_source_locator_route",
    "prepare_cognitive_research_run_packet",
    "archive_low_value_signal",
    "blocked_by_safety",
    "needs_repair",
)

_DENIED_AUTHORITY_FLAGS_V1 = {
    "source_access_authority": False,
    "source_fetching_authority": False,
    "source_ingestion_authority": False,
    "raw_retention_authority": False,
    "final_answer_authority": False,
    "public_claim_authority": False,
    "discovery_claim_authority": False,
    "proof_claim_authority": False,
    "benchmark_claim_authority": False,
    "agi_claim_authority": False,
    "consciousness_claim_authority": False,
    "sentience_claim_authority": False,
    "runtime_execution_authority": False,
    "memory_mutation_authority": False,
    "project_mutation_authority": False,
    "weslr_io_authority": False,
    "autonomous_routing_authority": False,
    "external_action_authority": False,
    "provider_model_authority": False,
    "http_authority": False,
    "web_search_authority": False,
    "behavior_pack_promotion_authority": False,
}

_ALLOWED_METADATA_FIELDS_V1 = (
    "schema_version",
    "integration_id",
    "source_scout_packet_ref",
    "source_scout_summary",
    "route_decisions",
    "selected_route",
    "route_reason",
    "candidate_signal_refs",
    "mlcf_candidate_payload_preview",
    "source_selection_plan_payload_preview",
    "metadata_locator_route_payload_preview",
    "operator_review_reasons",
    "blocked_reasons",
    "denied_authority_flags",
    "next_safe_step",
    "validation_status",
    "safe_metadata_summary",
)

_FORBIDDEN_KEY_NAMES_V1 = {
    "raw_paper_text",
    "raw_article_text",
    "raw_html",
    "html",
    "page_text",
    "full_text",
    "full_snippets",
    "source_excerpt",
    "source_excerpts",
    "copied_source_text",
    "copied_article_text",
    "provider_output",
    "source_content",
    "source_contents",
    "paper_text",
    "article_text",
    "abstract_text",
    "unbounded_abstract",
    "private_data",
    "hidden_content",
    "protected_content",
    "trusted_evidence_verdict",
    "accepted_evidence_verdict",
    "evidence_accepted",
    "proof",
    "discovery",
    "solution",
    "official_benchmark",
}

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw html",
    "full text",
    "full snippets",
    "source excerpt",
    "source excerpts",
    "copied source text",
    "copied article text",
    "provider output",
    "source content",
    "paper text",
    "article text",
    "abstract text",
    "trusted evidence",
    "accepted evidence",
    "final answer",
    "discovery",
    "proof",
    "solution",
    "official benchmark",
    "public science",
    "source access authorization",
    "runtime authorization",
    "provider/model/tool/retrieval/web",
    ".weslr",
)

_PRIVATE_HIDDEN_PROTECTED_MARKERS_V1 = (
    "private",
    "hidden",
    "protected",
    "secret",
    "system prompt",
    "developer message",
    "api key",
    "token",
)

_ALLOWED_SAFE_METADATA_FIELDS_V1 = (
    "metadata_only",
    "json_safe",
    "non_public",
    "no_source_access",
    "no_source_fetching",
    "no_source_ingestion",
    "no_raw_content_retention",
    "no_runtime_wiring",
    "no_model_provider_calls",
    "no_web_calls",
    "no_weslr_io",
    "no_memory_mutation",
    "no_project_mutation",
    "no_behavior_pack_promotion",
    "no_public_claims",
    "no_discovery_or_proof_claims",
    "operator_review_required",
)


def allowed_cross_domain_scout_to_mlcf_route_types_v1() -> tuple[str, ...]:
    return _ALLOWED_ROUTE_TYPES_V1


def allowed_cross_domain_scout_to_mlcf_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEPS_V1


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    elif payload is not None:
        merged["scout_packet"] = payload
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
    return merged


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    else:
        items = [value]
    normalized = [_compact_text(item) for item in items]
    return [item for item in normalized if item]


def _normalize_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return dict(value)


def _normalize_mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if value == value and value not in (float("inf"), float("-inf")) else None
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _first_non_json_safe_path(value: Any, path: str = "") -> str | None:
    if value is None or isinstance(value, (str, int, bool)):
        return None
    if isinstance(value, float):
        return None if value == value and value not in (float("inf"), float("-inf")) else (path or "<root>")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                return path or "<root>"
            child_path = f"{path}.{key}" if path else key
            found = _first_non_json_safe_path(item, child_path)
            if found is not None:
                return found
        return None
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            found = _first_non_json_safe_path(item, child_path)
            if found is not None:
                return found
        return None
    return path or "<root>"


def _string_contains_markers(text: Any, markers: tuple[str, ...]) -> bool:
    lowered = _compact_text(text).lower()
    return any(marker in lowered for marker in markers)


def _iter_text_blobs(value: Any):
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_text_blobs(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_text_blobs(item)
    elif value is not None:
        yield _compact_text(value)


def _contains_forbidden_key_or_text(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _compact_text(key).lower() in _FORBIDDEN_KEY_NAMES_V1:
                return True
            if _contains_forbidden_key_or_text(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_key_or_text(item) for item in value)
    lowered = _compact_text(value).lower()
    return any(marker in lowered for marker in _FORBIDDEN_TEXT_MARKERS_V1) or any(marker in lowered for marker in _PRIVATE_HIDDEN_PROTECTED_MARKERS_V1)


def _contains_true_flag(flags: Any, allowed_keys: tuple[str, ...] | None = None) -> tuple[bool, str | None]:
    if not isinstance(flags, Mapping):
        return False, None
    allowed = set(allowed_keys) if allowed_keys is not None else None
    for key, value in flags.items():
        if allowed is not None and key not in allowed:
            continue
        if bool(value) is True:
            return True, str(key)
    return False, None


def _stable_id(prefix: str, payload: Any) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:16]}"


def _route_next_step(route_type: str) -> str:
    return {
        "scout_to_source_selection_evidence_plan": "prepare_source_selection_evidence_plan",
        "scout_to_mlcf_cross_domain_candidate": "prepare_mlcf_cross_domain_candidate",
        "scout_to_metadata_only_source_locator_route": "prepare_metadata_only_source_locator_route",
        "scout_to_cognitive_research_run_packet": "prepare_cognitive_research_run_packet",
        "scout_to_operator_review": "operator_review",
        "scout_to_archive_low_value_signal": "archive_low_value_signal",
        "scout_blocked_by_safety": "blocked_by_safety",
    }[route_type]


def _collect_candidate_signal_refs(packet: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for field in (
        "open_problem_signal_candidates",
        "unresolved_work_signal_candidates",
        "anomaly_signal_candidates",
        "limitation_future_work_candidates",
        "contradiction_candidates",
    ):
        for item in _normalize_mapping_list(packet.get(field)):
            ref = _compact_text(item.get("signal_id")) or _compact_text(item.get("source_ref")) or _compact_text(item.get("title_or_descriptor"))
            if ref and ref not in refs:
                refs.append(ref)
    for item in _normalize_mapping_list(packet.get("input_signal_items")):
        ref = _compact_text(item.get("signal_id")) or _compact_text(item.get("source_ref")) or _compact_text(item.get("title_or_descriptor"))
        if ref and ref not in refs:
            refs.append(ref)
    return refs


def _mapping_signal_strength(value: Any) -> int:
    if not isinstance(value, Mapping):
        return 0
    strength = 0
    for item in value.values():
        if isinstance(item, Mapping):
            if any(_compact_text(v) for v in item.values()):
                strength += 1
        elif isinstance(item, list):
            if any(_compact_text(v) for v in item):
                strength += 1
        elif _compact_text(item):
            strength += 1
    return strength


def _signal_list_count(packet: Mapping[str, Any], field: str) -> int:
    value = packet.get(field)
    return len(value) if isinstance(value, list) else 0


def _has_bridge_signals(packet: Mapping[str, Any]) -> bool:
    bridge_count = _signal_list_count(packet, "candidate_cross_domain_bridges")
    unresolved_total = _signal_list_count(packet, "open_problem_signal_candidates") + _signal_list_count(packet, "unresolved_work_signal_candidates")
    return bridge_count >= 5 and unresolved_total >= 4


def _has_strong_missing_evidence(packet: Mapping[str, Any]) -> bool:
    missing_strength = _mapping_signal_strength(packet.get("missing_evidence_map")) + _mapping_signal_strength(packet.get("disconfirming_evidence_map"))
    return missing_strength >= 4


def _has_locator_need(packet: Mapping[str, Any]) -> bool:
    source_classes_needed = _normalize_text_list(packet.get("source_classes_needed"))
    bridge_count = _signal_list_count(packet, "candidate_cross_domain_bridges")
    missing_strength = _mapping_signal_strength(packet.get("missing_evidence_map")) + _mapping_signal_strength(packet.get("disconfirming_evidence_map"))
    return bool(source_classes_needed) and bridge_count < 5 and missing_strength < 4


def _has_operator_review_need(packet: Mapping[str, Any]) -> bool:
    return _signal_list_count(packet, "anomaly_signal_candidates") > 0 or _signal_list_count(packet, "contradiction_candidates") > 0 or _signal_list_count(packet, "failed_model_signal_candidates") > 0


def _has_cognitive_research_need(packet: Mapping[str, Any]) -> bool:
    openish = _signal_list_count(packet, "open_problem_signal_candidates") + _signal_list_count(packet, "unresolved_work_signal_candidates") + _signal_list_count(packet, "limitation_future_work_candidates")
    pressure = len(_normalize_text_list(packet.get("pressure_test_questions"))) + len(_normalize_text_list(packet.get("probe_suggestions")))
    return openish >= 1 and pressure >= 2 and not _has_bridge_signals(packet) and not _has_strong_missing_evidence(packet) and not _has_locator_need(packet)


def _has_weak_only_need(packet: Mapping[str, Any]) -> bool:
    weakish = _signal_list_count(packet, "weak_signal_candidates") + _signal_list_count(packet, "unknown_signal_candidates")
    if weakish == 0:
        # Fall back to natural-language weak markers in summaries when explicit weak lists are absent.
        for blob in _iter_text_blobs(packet):
            lowered = blob.lower()
            if "weak analogy" in lowered or "vague" in lowered or "maybe" in lowered or "possibly" in lowered:
                weakish += 1
                break
    return weakish > 0 and not _has_bridge_signals(packet) and not _has_strong_missing_evidence(packet) and not _has_locator_need(packet) and not _has_operator_review_need(packet)


def _build_source_selection_preview(packet: Mapping[str, Any]) -> dict[str, Any]:
    source_summary = _normalize_mapping(packet.get("source_scout_summary"))
    return {
        "science_direction_summary": _compact_text(source_summary.get("summary_text")) or _compact_text(packet.get("search_governance_mode")),
        "domain_focus": ", ".join(_normalize_text_list(packet.get("domain_families"))) or "cross-domain",
        "required_source_classes": _normalize_text_list(packet.get("source_classes_needed")),
        "missing_evidence": _normalize_mapping(packet.get("missing_evidence_map")),
        "disconfirming_evidence": _normalize_mapping(packet.get("disconfirming_evidence_map")),
        "operator_review_need": _compact_text(packet.get("operator_review_need")),
    }


def _build_mlcf_candidate_preview(packet: Mapping[str, Any]) -> dict[str, Any]:
    domain_summaries = []
    for item in _normalize_mapping_list(packet.get("input_signal_items")):
        domain_summaries.append(
            {
                "domain_family": _compact_text(item.get("domain_family")),
                "summary": _compact_text(item.get("summary")),
                "source_ref": _compact_text(item.get("source_ref")),
            }
        )
    relation_hints = []
    for bridge in _normalize_mapping_list(packet.get("candidate_cross_domain_bridges")):
        relation = _compact_text(bridge.get("relation_type")) or _compact_text(bridge.get("relation_hint"))
        if relation and relation not in relation_hints:
            relation_hints.append(relation)
    if not relation_hints:
        relation_hints = ["cross-domain bridge metadata only"]
    return {
        "domain_summaries": domain_summaries,
        "relation_type_hints": relation_hints,
        "missing_evidence": _normalize_mapping(packet.get("missing_evidence_map")),
        "disconfirming_signals": _normalize_mapping(packet.get("disconfirming_evidence_map")),
        "pressure_test_questions": _normalize_text_list(packet.get("pressure_test_questions")),
        "probe_suggestions": _normalize_text_list(packet.get("probe_suggestions")),
        "no_claim_authority": True,
    }


def _build_metadata_locator_preview(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "query_intent": f"metadata-only source locator route for {', '.join(_normalize_text_list(packet.get('domain_families'))) or 'cross-domain research'}",
        "source_classes_needed": _normalize_text_list(packet.get("source_classes_needed")),
        "allowed_metadata_fields": [
            "title",
            "domain_family",
            "source_class_label",
            "authority_guess",
            "evidence_role_guess",
            "source_ref",
        ],
        "blocked_source_content_fields": [
            "raw text",
            "full text",
            "html",
            "snippets",
            "source excerpts",
            "provider output",
            "trusted evidence",
            "accepted evidence",
        ],
        "operator_review_need": _compact_text(packet.get("operator_review_need")),
    }


def _decision(route_type: str, signal_refs: list[str], confidence_label: str, why_selected: str, operator_review_required: bool, allowed_next_helper: str, safe_payload_preview: dict[str, Any], blocked_authorities: list[str] | None = None) -> dict[str, Any]:
    return {
        "route_id": _stable_id(route_type, {"refs": signal_refs, "why": why_selected, "confidence": confidence_label}),
        "route_type": route_type,
        "signal_refs": signal_refs,
        "confidence_label": confidence_label,
        "why_selected": why_selected,
        "required_operator_review": bool(operator_review_required),
        "allowed_next_helper": allowed_next_helper,
        "blocked_authorities": blocked_authorities or list(_DENIED_AUTHORITY_FLAGS_V1.keys()),
        "safe_payload_preview": safe_payload_preview,
    }


def _route_analysis(packet: Mapping[str, Any]) -> dict[str, Any]:
    signal_refs = _collect_candidate_signal_refs(packet)
    operator_review_reasons: list[str] = []
    blocked_reasons: list[str] = []
    route_decisions: list[dict[str, Any]] = []

    unsafe_scout = validate_cross_domain_open_problem_discovery_scout_packet_v1(packet)
    unsafe_flag, unsafe_flag_name = _contains_true_flag(packet.get("denied_authority_flags"), tuple(_DENIED_AUTHORITY_FLAGS_V1.keys()))
    unsafe_markers = _contains_forbidden_key_or_text(packet)
    private_markers = any(_string_contains_markers(blob, _PRIVATE_HIDDEN_PROTECTED_MARKERS_V1) for blob in _iter_text_blobs(packet))
    claim_markers = any(_string_contains_markers(blob, ("discovery", "proof", "official benchmark", "final answer", "trusted evidence", "accepted evidence", "solution", "public science")) for blob in _iter_text_blobs(packet))

    if unsafe_scout.get("blocked") or unsafe_flag or unsafe_markers or private_markers or claim_markers:
        selected_route = "scout_blocked_by_safety"
        route_reason = "Safety blocked: unsafe scout packet, unsafe content markers, denied authority flags, or claim language present."
        blocked_reasons.extend(["unsafe_scout_packet", "unsafe_content_or_claim_marker", "denied_authority_flag_true" if unsafe_flag else "denied_authority_flags_false_only"])
        if unsafe_flag_name:
            blocked_reasons.append(f"denied_authority_flag_true:{unsafe_flag_name}")
        operator_review_reasons.append("Review is required because safety blockers or prohibited content markers were detected.")
        route_decisions.append(
            _decision(
                "scout_blocked_by_safety",
                signal_refs,
                "high",
                route_reason,
                True,
                _route_next_step("scout_blocked_by_safety"),
                {
                    "blocked_reasons": blocked_reasons,
                    "operator_review_reasons": operator_review_reasons,
                    "denied_authority_flags": dict(_DENIED_AUTHORITY_FLAGS_V1),
                },
            )
        )
        return {
            "selected_route": selected_route,
            "route_reason": route_reason,
            "route_decisions": route_decisions,
            "operator_review_reasons": operator_review_reasons,
            "blocked_reasons": blocked_reasons,
            "next_safe_step": _route_next_step(selected_route),
        }

    bridge = _has_bridge_signals(packet)
    missing = _has_strong_missing_evidence(packet)
    locator = _has_locator_need(packet)
    operator = _has_operator_review_need(packet)
    cognitive = _has_cognitive_research_need(packet)
    weak_only = _has_weak_only_need(packet)

    if bridge:
        route_decisions.append(
            _decision(
                "scout_to_mlcf_cross_domain_candidate",
                signal_refs,
                "high",
                "Cross-domain bridge candidates are strong and safe enough to route into the MLCF candidate path.",
                True,
                _route_next_step("scout_to_mlcf_cross_domain_candidate"),
                _build_mlcf_candidate_preview(packet),
            )
        )
    if missing:
        route_decisions.append(
            _decision(
                "scout_to_source_selection_evidence_plan",
                signal_refs,
                "high",
                "Missing-evidence pressure is strong enough to route into the source selection evidence plan.",
                True,
                _route_next_step("scout_to_source_selection_evidence_plan"),
                _build_source_selection_preview(packet),
            )
        )
    if locator:
        route_decisions.append(
            _decision(
                "scout_to_metadata_only_source_locator_route",
                signal_refs,
                "medium",
                "Source classes are needed and metadata-only locator planning is the safest next helper.",
                True,
                _route_next_step("scout_to_metadata_only_source_locator_route"),
                _build_metadata_locator_preview(packet),
            )
        )
    if operator:
        operator_review_reasons.append("Contradiction, anomaly, or model-failure signals require operator review and disconfirming-evidence planning.")
        route_decisions.append(
            _decision(
                "scout_to_operator_review",
                signal_refs,
                "medium",
                "Contradiction, anomaly, or failed-model style signals require operator review and a disconfirming-evidence plan.",
                True,
                _route_next_step("scout_to_operator_review"),
                {
                    "disconfirming_evidence_map": _normalize_mapping(packet.get("disconfirming_evidence_map")),
                    "pressure_test_questions": _normalize_text_list(packet.get("pressure_test_questions")),
                    "probe_suggestions": _normalize_text_list(packet.get("probe_suggestions")),
                },
            )
        )
    if cognitive:
        route_decisions.append(
            _decision(
                "scout_to_cognitive_research_run_packet",
                signal_refs,
                "medium",
                "Open-problem and pressure-test metadata are sufficient for a bounded cognitive research run packet.",
                True,
                _route_next_step("scout_to_cognitive_research_run_packet"),
                {
                    "domain_families": _normalize_text_list(packet.get("domain_families")),
                    "pressure_test_questions": _normalize_text_list(packet.get("pressure_test_questions")),
                    "probe_suggestions": _normalize_text_list(packet.get("probe_suggestions")),
                    "no_claim_authority": True,
                },
            )
        )
    if weak_only:
        route_decisions.append(
            _decision(
                "scout_to_archive_low_value_signal",
                signal_refs,
                "low",
                "The scout packet is weak or vague only, so archival posture is safer than deeper routing.",
                False,
                _route_next_step("scout_to_archive_low_value_signal"),
                {
                    "weak_signal_notes": "vague, weak, or low-value only",
                    "operator_review_need": _compact_text(packet.get("operator_review_need")),
                },
            )
        )

    if bridge:
        selected_route = "scout_to_mlcf_cross_domain_candidate"
        route_reason = "Cross-domain bridge candidates are strong and unresolved-work signals are sufficient for MLCF candidate routing."
        next_safe_step = _route_next_step(selected_route)
    elif missing:
        selected_route = "scout_to_source_selection_evidence_plan"
        route_reason = "Missing-evidence pressure dominates, so source selection evidence planning comes first."
        next_safe_step = _route_next_step(selected_route)
    elif locator:
        selected_route = "scout_to_metadata_only_source_locator_route"
        route_reason = "Source classes are needed but no source locator metadata is present, so metadata-only locator planning is safest."
        next_safe_step = _route_next_step(selected_route)
    elif operator:
        selected_route = "scout_to_operator_review"
        route_reason = "Contradiction, anomaly, or failed-model signals dominate, so operator review is required."
        next_safe_step = _route_next_step(selected_route)
    elif cognitive:
        selected_route = "scout_to_cognitive_research_run_packet"
        route_reason = "The packet needs a bounded cognitive research run packet rather than direct evidence planning."
        next_safe_step = _route_next_step(selected_route)
    elif weak_only:
        selected_route = "scout_to_archive_low_value_signal"
        route_reason = "The packet is weak or vague only, so archival posture is safer than deeper routing."
        next_safe_step = "needs_repair"
    else:
        selected_route = "scout_to_operator_review"
        route_reason = "The packet does not strongly justify a deeper route, so operator review is the safe fallback."
        next_safe_step = _route_next_step(selected_route)
        operator_review_reasons.append("Fallback operator review is required because no stronger route dominated.")
        route_decisions.append(
            _decision(
                "scout_to_operator_review",
                signal_refs,
                "low",
                route_reason,
                True,
                next_safe_step,
                {"operator_review_need": _compact_text(packet.get("operator_review_need"))},
            )
        )

    if selected_route not in {item["route_type"] for item in route_decisions}:
        preview = {
            "selected_route": selected_route,
            "route_reason": route_reason,
        }
        if selected_route == "scout_blocked_by_safety":
            preview["blocked_reasons"] = blocked_reasons
        route_decisions.insert(0, _decision(selected_route, signal_refs, "high", route_reason, selected_route != "scout_to_archive_low_value_signal", next_safe_step, preview))

    return {
        "selected_route": selected_route,
        "route_reason": route_reason,
        "route_decisions": route_decisions,
        "operator_review_reasons": operator_review_reasons or (["Operator review posture retained for metadata-only safety."] if selected_route != "scout_to_archive_low_value_signal" else ["Archive posture does not replace owner review."]),
        "blocked_reasons": blocked_reasons,
        "next_safe_step": next_safe_step,
    }


def build_cross_domain_scout_to_mlcf_integration_packet_v1(scout_packet=None, *, integration_id=None, **overrides):
    request = _merge_payload(scout_packet, **overrides)
    source_scout_packet = request.get("scout_packet")
    if source_scout_packet is None and isinstance(scout_packet, Mapping):
        source_scout_packet = dict(scout_packet)
        for key, value in overrides.items():
            if key != "integration_id" and value is not None:
                source_scout_packet[key] = value
    if source_scout_packet is None and isinstance(request.get("source_scout_packet"), Mapping):
        source_scout_packet = request["source_scout_packet"]

    source_validation = validate_cross_domain_open_problem_discovery_scout_packet_v1(source_scout_packet)
    source_summary = summarize_cross_domain_open_problem_discovery_scout_packet_v1(source_scout_packet) if isinstance(source_scout_packet, Mapping) else {
        "schema_version": "cross_domain_open_problem_scout_v1",
        "scout_id": "",
        "domain_family_count": 0,
        "signal_candidate_count": 0,
        "recommended_mlcf_route": "blocked_by_safety",
        "next_safe_step": "blocked_by_safety",
        "validation_posture": "blocked",
        "summary_text": "Blocked cross-domain open-problem scout packet.",
    }

    source_ref = _compact_text((source_scout_packet or {}).get("scout_id") if isinstance(source_scout_packet, Mapping) else None) or _compact_text(request.get("source_scout_packet_ref")) or "missing_scout_packet"
    route_analysis = _route_analysis(source_scout_packet if isinstance(source_scout_packet, Mapping) else {})

    integration_payload = {
        "schema_version": SCHEMA_VERSION_V1,
        "integration_id": _compact_text(integration_id) or _compact_text(request.get("integration_id")) or _stable_id("scout_to_mlcf_integration", {"source_ref": source_ref, "selected_route": route_analysis["selected_route"]}),
        "source_scout_packet_ref": source_ref,
        "source_scout_packet": to_cross_domain_open_problem_discovery_scout_json_safe_v1(source_scout_packet) if isinstance(source_scout_packet, Mapping) else None,
        "source_scout_summary": source_summary,
        "route_decisions": route_analysis["route_decisions"],
        "selected_route": route_analysis["selected_route"],
        "route_reason": route_analysis["route_reason"],
        "candidate_signal_refs": _collect_candidate_signal_refs(source_scout_packet if isinstance(source_scout_packet, Mapping) else {}),
        "mlcf_candidate_payload_preview": _build_mlcf_candidate_preview(source_scout_packet if isinstance(source_scout_packet, Mapping) else {}),
        "source_selection_plan_payload_preview": _build_source_selection_preview(source_scout_packet if isinstance(source_scout_packet, Mapping) else {}),
        "metadata_locator_route_payload_preview": _build_metadata_locator_preview(source_scout_packet if isinstance(source_scout_packet, Mapping) else {}),
        "operator_review_reasons": route_analysis["operator_review_reasons"],
        "blocked_reasons": route_analysis["blocked_reasons"],
        "denied_authority_flags": dict(_DENIED_AUTHORITY_FLAGS_V1),
        "next_safe_step": route_analysis["next_safe_step"],
        "validation_status": {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": True,
            "blocked": False,
            "blocked_labels": [],
            "validation_posture": "valid",
            "summary_text": "Provisional cross-domain scout-to-MLCF integration packet.",
            "source_scout_validation_posture": source_validation.get("validation_posture", "blocked"),
        },
        "safe_metadata_summary": {
            "metadata_only": True,
            "json_safe": True,
            "non_public": True,
            "no_source_access": True,
            "no_source_fetching": True,
            "no_source_ingestion": True,
            "no_raw_content_retention": True,
            "no_runtime_wiring": True,
            "no_model_provider_calls": True,
            "no_web_calls": True,
            "no_weslr_io": True,
            "no_memory_mutation": True,
            "no_project_mutation": True,
            "no_behavior_pack_promotion": True,
            "no_public_claims": True,
            "no_discovery_or_proof_claims": True,
            "operator_review_required": True,
            "source_scout_validation_posture": source_validation.get("validation_posture", "blocked"),
            "selected_route": route_analysis["selected_route"],
        },
    }
    return to_cross_domain_scout_to_mlcf_integration_json_safe_v1(integration_payload)


def validate_cross_domain_scout_to_mlcf_integration_request_v1(request):
    if not isinstance(request, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_request_type"],
            "validation_posture": "blocked",
            "summary_text": "Blocked cross-domain scout-to-MLCF integration request.",
        }
    scout_packet = request.get("scout_packet")
    if scout_packet is None and isinstance(request.get("source_scout_packet"), Mapping):
        scout_packet = request.get("source_scout_packet")
    scout_validation = validate_cross_domain_open_problem_discovery_scout_packet_v1(scout_packet)
    blocked_labels: list[str] = []
    if scout_packet is None:
        blocked_labels.append("missing_source_scout_packet")
    elif scout_validation.get("blocked"):
        blocked_labels.append("invalid_source_scout_packet")
    integration_id = _compact_text(request.get("integration_id"))
    if not integration_id:
        blocked_labels.append("missing_integration_id")
    if _first_non_json_safe_path(request) is not None:
        blocked_labels.append("non_json_safe_request")
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": not blocked_labels,
        "blocked": bool(blocked_labels),
        "blocked_labels": blocked_labels,
        "validation_posture": "valid" if not blocked_labels else "blocked",
        "summary_text": "Valid cross-domain scout-to-MLCF integration request." if not blocked_labels else "Blocked cross-domain scout-to-MLCF integration request.",
        "source_scout_validation_posture": scout_validation.get("validation_posture", "blocked"),
    }


def validate_cross_domain_scout_to_mlcf_integration_packet_v1(packet):
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_packet_type"],
            "validation_posture": "blocked",
            "summary_text": "Blocked cross-domain scout-to-MLCF integration packet.",
        }

    blocked_labels: list[str] = []
    for field in _ALLOWED_METADATA_FIELDS_V1:
        if field not in packet:
            blocked_labels.append(f"missing_{field}")

    if _compact_text(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")

    integration_id = _compact_text(packet.get("integration_id"))
    source_ref = _compact_text(packet.get("source_scout_packet_ref"))
    selected_route = _compact_text(packet.get("selected_route"))
    next_safe_step = _compact_text(packet.get("next_safe_step"))
    route_reason = _compact_text(packet.get("route_reason"))
    if not integration_id:
        blocked_labels.append("missing_integration_id")
    if not source_ref:
        blocked_labels.append("missing_source_scout_packet_ref")
    if not route_reason:
        blocked_labels.append("missing_route_reason")
    if selected_route not in _ALLOWED_ROUTE_TYPES_V1:
        blocked_labels.append("invalid_selected_route")
    if next_safe_step not in _ALLOWED_NEXT_STEPS_V1:
        blocked_labels.append("invalid_next_safe_step")

    source_scout_packet = packet.get("source_scout_packet")
    if source_scout_packet is None:
        blocked_labels.append("missing_source_scout_packet")
    scout_validation = validate_cross_domain_open_problem_discovery_scout_packet_v1(source_scout_packet) if isinstance(source_scout_packet, Mapping) else None
    if scout_validation and scout_validation.get("blocked"):
        blocked_labels.append("invalid_source_scout_packet")
        if _contains_forbidden_key_or_text(source_scout_packet):
            blocked_labels.append("unsafe_source_content_field")
        true_flag, true_name = _contains_true_flag(source_scout_packet.get("denied_authority_flags"), tuple(_DENIED_AUTHORITY_FLAGS_V1.keys()))
        if true_flag and true_name:
            blocked_labels.append(f"unsafe_denied_authority_flag_true:{true_name}")
        for label in scout_validation.get("blocked_labels", []):
            if label not in blocked_labels:
                blocked_labels.append(label)
    if packet.get("source_scout_summary") is None:
        blocked_labels.append("missing_source_scout_summary")

    route_decisions = packet.get("route_decisions")
    if not isinstance(route_decisions, list) or not route_decisions:
        blocked_labels.append("missing_route_decisions")
    else:
        route_types_seen: list[str] = []
        for index, decision in enumerate(route_decisions):
            if not isinstance(decision, Mapping):
                blocked_labels.append(f"invalid_route_decision_{index}")
                continue
            for field in ("route_id", "route_type", "signal_refs", "confidence_label", "why_selected", "required_operator_review", "allowed_next_helper", "blocked_authorities", "safe_payload_preview"):
                if field not in decision:
                    blocked_labels.append(f"missing_route_decision_{field}")
            route_type = _compact_text(decision.get("route_type"))
            route_types_seen.append(route_type)
            if route_type not in _ALLOWED_ROUTE_TYPES_V1:
                blocked_labels.append("invalid_route_decision_route_type")
            if _compact_text(decision.get("allowed_next_helper")) not in _ALLOWED_NEXT_STEPS_V1:
                blocked_labels.append("invalid_route_decision_allowed_next_helper")
            if not isinstance(decision.get("signal_refs"), list):
                blocked_labels.append("invalid_route_decision_signal_refs")
            if not isinstance(decision.get("blocked_authorities"), list):
                blocked_labels.append("invalid_route_decision_blocked_authorities")
            if _compact_text(decision.get("why_selected")) == "":
                blocked_labels.append("missing_route_decision_reason")
            if not isinstance(decision.get("safe_payload_preview"), Mapping):
                blocked_labels.append("invalid_route_decision_safe_payload_preview")
        if selected_route and selected_route not in route_types_seen:
            blocked_labels.append("selected_route_not_in_route_decisions")

    operator_review_reasons = packet.get("operator_review_reasons")
    if not isinstance(operator_review_reasons, list) or not operator_review_reasons:
        blocked_labels.append("missing_operator_review_need")

    if not isinstance(packet.get("blocked_reasons"), list):
        blocked_labels.append("invalid_blocked_reasons")
    if not isinstance(packet.get("candidate_signal_refs"), list):
        blocked_labels.append("invalid_candidate_signal_refs")
    if not isinstance(packet.get("denied_authority_flags"), Mapping):
        blocked_labels.append("invalid_denied_authority_flags")
    else:
        true_flag, true_name = _contains_true_flag(packet.get("denied_authority_flags"), tuple(_DENIED_AUTHORITY_FLAGS_V1.keys()))
        if true_flag:
            blocked_labels.append(f"unsafe_denied_authority_flag_true:{true_name}")
        for name in _DENIED_AUTHORITY_FLAGS_V1:
            if name not in packet["denied_authority_flags"]:
                blocked_labels.append(f"missing_denied_authority_flag:{name}")
    safe_metadata_summary = packet.get("safe_metadata_summary")
    if not isinstance(safe_metadata_summary, Mapping):
        blocked_labels.append("invalid_safe_metadata_summary")
    validation_status = packet.get("validation_status")
    if not isinstance(validation_status, Mapping):
        blocked_labels.append("invalid_validation_status")

    if _first_non_json_safe_path(packet) is not None:
        blocked_labels.append("non_json_safe_output")

    scanned_texts: list[Any] = [packet.get("route_reason")]
    source_scout_summary = packet.get("source_scout_summary")
    if isinstance(source_scout_summary, Mapping):
        scanned_texts.append(source_scout_summary.get("summary_text"))
    scanned_texts.extend(packet.get("operator_review_reasons") or [])
    scanned_texts.extend(packet.get("blocked_reasons") or [])
    for decision in route_decisions if isinstance(route_decisions, list) else []:
        if isinstance(decision, Mapping):
            scanned_texts.append(decision.get("why_selected"))
            preview = decision.get("safe_payload_preview")
            if isinstance(preview, Mapping):
                scanned_texts.extend(
                    value for key, value in preview.items()
                    if key not in {"blocked_authorities", "blocked_source_content_fields", "allowed_metadata_fields", "required_source_classes", "source_classes_needed"}
                )
    if any(_string_contains_markers(blob, _PRIVATE_HIDDEN_PROTECTED_MARKERS_V1) for blob in scanned_texts):
        blocked_labels.append("unsafe_private_hidden_protected_marker")
    if any(_string_contains_markers(blob, ("discovery", "proof", "official benchmark", "final answer", "trusted evidence", "accepted evidence", "solution", "public science")) for blob in scanned_texts):
        blocked_labels.append("unsafe_claim_language_present")
    if any(_string_contains_markers(blob, ("raw html", "full text", "full snippets", "source excerpt", "source excerpts", "copied source text", "copied article text", "provider output", "source content", "paper text", "article text", "abstract text")) for blob in scanned_texts):
        blocked_labels.append("unsafe_source_content_field")

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": not blocked_labels,
        "blocked": bool(blocked_labels),
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "validation_posture": "valid" if not blocked_labels else "blocked",
        "summary_text": "Valid cross-domain scout-to-MLCF integration packet." if not blocked_labels else "Blocked cross-domain scout-to-MLCF integration packet.",
        "integration_id": integration_id,
        "selected_route": selected_route,
        "next_safe_step": next_safe_step,
    }


def summarize_cross_domain_scout_to_mlcf_integration_packet_v1(packet):
    validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(packet)
    packet_map = packet if isinstance(packet, Mapping) else {}
    summary_text = (
        f"Scout-to-MLCF integration { _compact_text(packet_map.get('integration_id')) or 'unassigned' }: "
        f"route={_compact_text(packet_map.get('selected_route')) or 'blocked_by_safety'}, "
        f"next={_compact_text(packet_map.get('next_safe_step')) or 'blocked_by_safety'}, "
        f"signals={len(_normalize_text_list(packet_map.get('candidate_signal_refs')))}."
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "integration_id": _compact_text(packet_map.get("integration_id")),
        "source_scout_packet_ref": _compact_text(packet_map.get("source_scout_packet_ref")),
        "selected_route": _compact_text(packet_map.get("selected_route")),
        "next_safe_step": _compact_text(packet_map.get("next_safe_step")),
        "route_decision_count": len(packet_map.get("route_decisions", [])) if isinstance(packet_map.get("route_decisions"), list) else 0,
        "validation_posture": validation.get("validation_posture", "blocked"),
        "summary_text": summary_text[:240],
    }


def to_cross_domain_scout_to_mlcf_integration_json_safe_v1(packet):
    return _json_safe(copy.deepcopy(packet))


def build_initial_cross_domain_scout_to_mlcf_integration_examples_v1() -> list[dict[str, Any]]:
    scout_examples = build_initial_cross_domain_open_problem_discovery_scout_examples_v1()
    examples: list[dict[str, Any]] = []

    examples.append(
        build_cross_domain_scout_to_mlcf_integration_packet_v1(
            scout_examples[0],
            integration_id="cross_domain_scout_to_mlcf_candidate_example_a",
        )
    )

    examples.append(
        build_cross_domain_scout_to_mlcf_integration_packet_v1(
            scout_examples[1],
            integration_id="cross_domain_scout_to_mlcf_source_selection_example_b",
        )
    )

    locator_scout = copy.deepcopy(scout_examples[1])
    locator_scout["scout_id"] = "cross_domain_open_problem_scout_locator_example"
    locator_scout["candidate_cross_domain_bridges"] = []
    locator_scout["missing_evidence_map"] = {"source_class_gap": ["metadata-only locator needed"]}
    locator_scout["disconfirming_evidence_map"] = {"blocked_private_or_hidden_source": ["no raw content", "no claim authority"]}
    locator_scout["recommended_mlcf_route"] = "prepare_metadata_only_source_locator_route"
    locator_scout["next_safe_step"] = "prepare_metadata_only_source_locator_route"
    examples.append(
        build_cross_domain_scout_to_mlcf_integration_packet_v1(
            locator_scout,
            integration_id="cross_domain_scout_to_mlcf_locator_example_c",
        )
    )

    examples.append(
        build_cross_domain_scout_to_mlcf_integration_packet_v1(
            scout_examples[2],
            integration_id="cross_domain_scout_to_mlcf_blocked_example_d",
        )
    )

    weak_scout = copy.deepcopy(scout_examples[3])
    weak_scout["scout_id"] = "cross_domain_open_problem_scout_weak_example"
    weak_scout["candidate_cross_domain_bridges"] = []
    weak_scout["open_problem_signal_candidates"] = []
    weak_scout["unresolved_work_signal_candidates"] = []
    weak_scout["anomaly_signal_candidates"] = []
    weak_scout["limitation_future_work_candidates"] = []
    weak_scout["contradiction_candidates"] = []
    weak_scout["missing_evidence_map"] = {}
    weak_scout["disconfirming_evidence_map"] = {}
    weak_scout["source_classes_needed"] = []
    weak_scout["candidate_cross_domain_bridges"] = []
    weak_scout["pressure_test_questions"] = ["Is this only a vague analogy?"]
    weak_scout["probe_suggestions"] = ["Archive unless a stronger signal appears."]
    weak_scout["recommended_mlcf_route"] = "archive_low_value_signal"
    weak_scout["next_safe_step"] = "archive_low_value_signal"
    examples.append(
        build_cross_domain_scout_to_mlcf_integration_packet_v1(
            weak_scout,
            integration_id="cross_domain_scout_to_mlcf_weak_example_e",
        )
    )

    cognitive_scout = copy.deepcopy(scout_examples[0])
    cognitive_scout["scout_id"] = "cross_domain_open_problem_scout_cognitive_example"
    cognitive_scout["candidate_cross_domain_bridges"] = []
    cognitive_scout["missing_evidence_map"] = {}
    cognitive_scout["disconfirming_evidence_map"] = {}
    cognitive_scout["anomaly_signal_candidates"] = []
    cognitive_scout["contradiction_candidates"] = []
    cognitive_scout["source_classes_needed"] = []
    cognitive_scout["recommended_mlcf_route"] = "prepare_cognitive_research_run_packet"
    cognitive_scout["next_safe_step"] = "prepare_cognitive_research_run_packet"
    examples.append(
        build_cross_domain_scout_to_mlcf_integration_packet_v1(
            cognitive_scout,
            integration_id="cross_domain_scout_to_mlcf_cognitive_example_f",
        )
    )

    return copy.deepcopy(examples)
