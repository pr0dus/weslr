"""WESLR Cross-Domain Scout To MLCF Candidate Preparation Helper V1.

Deterministic, metadata-only helpers for turning a validated cross-domain scout
integration packet into a bounded candidate-preparation packet for later MLCF
candidate shaping. This module never fetches sources, ingests content, calls
models, touches runtime, writes state, or performs network/filesystem actions.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from weslr.cross_domain_scout_to_mlcf_integration import (
    summarize_cross_domain_scout_to_mlcf_integration_packet_v1,
    to_cross_domain_scout_to_mlcf_integration_json_safe_v1,
    validate_cross_domain_scout_to_mlcf_integration_packet_v1,
)

SCHEMA_VERSION_V1 = "weslr_cross_domain_scout_to_mlcf_candidate_preparation_v1"

_ALLOWED_STATUSES_V1 = (
    "candidate_preparation_ready_for_operator_review",
    "candidate_preparation_needs_source_selection_plan",
    "candidate_preparation_excluded_wrong_route",
    "candidate_preparation_needs_repair",
    "candidate_preparation_blocked_by_safety",
)

_ALLOWED_READINESS_LABELS_V1 = (
    "metadata_candidate_ready_for_review",
    "metadata_candidate_needs_evidence_plan",
    "metadata_candidate_needs_disconfirming_review",
    "metadata_candidate_low_value_or_weak",
    "metadata_candidate_blocked",
)

_ALLOWED_NEXT_STEPS_V1 = (
    "operator_review",
    "prepare_source_selection_evidence_plan",
    "prepare_mlcf_cross_domain_candidate",
    "blocked_by_safety",
    "needs_repair",
    "exclude_wrong_route",
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
    "accepted_candidate_authority": False,
    "proposal_payload_authority": False,
    "proposal_submission_authority": False,
    "proposal_application_authority": False,
}

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

_FORBIDDEN_KEY_NAMES_V1 = {
    "raw_html",
    "html",
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
    "proposal_payload",
    "proposal_submission",
    "proposal_application",
    "accepted_candidate",
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
    "accepted candidate",
    "proposal payload",
    "proposal submission",
    "proposal application",
    "final answer",
    "discovery",
    "proof",
    "solution",
    "official benchmark",
    "public science",
    "source access authority",
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

_REQUIRED_FIELD_NAMES_V1 = (
    "schema_version",
    "candidate_preparation_id",
    "source_integration_packet_ref",
    "source_selected_route",
    "preparation_status",
    "candidate_readiness_label",
    "domain_summaries",
    "relation_type_hints",
    "candidate_bridge_refs",
    "missing_evidence",
    "disconfirming_signals",
    "source_classes_needed",
    "pressure_test_questions",
    "probe_suggestions",
    "operator_review_reasons",
    "mlcf_cross_domain_candidate_helper_payload_preview",
    "source_selection_followup_preview",
    "blocked_reasons",
    "denied_authority_flags",
    "next_safe_step",
    "validation_status",
    "safe_metadata_summary",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "domain_summaries",
    "relation_type_hints",
    "candidate_bridge_refs",
    "missing_evidence",
    "disconfirming_signals",
    "source_classes_needed",
    "pressure_test_questions",
    "probe_suggestions",
    "operator_review_reasons",
    "blocked_reasons",
)

_REQUIRED_DICT_FIELDS_V1 = (
    "mlcf_cross_domain_candidate_helper_payload_preview",
    "source_selection_followup_preview",
    "denied_authority_flags",
    "validation_status",
    "safe_metadata_summary",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "candidate_preparation_id",
    "source_integration_packet_ref",
    "source_selected_route",
    "preparation_status",
    "candidate_readiness_label",
    "next_safe_step",
)

_SAFE_TRUE_FLAGS_V1 = (
    "metadata_only",
    "json_safe",
    "non_public",
    "operator_review_required",
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
)

_ALLOWED_MARKER_FIELDS_V1 = (
    "science_direction_summary",
    "domain_focus",
    "domain_summaries",
    "relation_type_hints",
    "cross_domain_bridge_refs",
    "candidate_bridge_refs",
    "missing_evidence",
    "disconfirming_signals",
    "source_classes_needed",
    "pressure_test_questions",
    "probe_suggestions",
    "owner_review_posture",
    "no_claim_authority",
    "github_role",
    "official_public_source_requirement",
    "operator_review_need",
    "safe_metadata_summary",
)

_BLOCKED_OR_REVIEW_ONLY_ROUTE_TYPES_V1 = {
    "blocked_by_safety",
    "route_to_blocked_by_safety",
    "scout_blocked_by_safety",
    "route_to_ontology_expansion_request",
}

_ONTOLOGY_EXPANSION_HANOFF_FIELDS_V1 = (
    "ontology_expansion_request_handoff",
    "ontology_expansion_request_validation",
)

_ONTOLOGY_EXPANSION_TEXT_MARKERS_V1 = (
    "ontology insufficient",
    "insufficient ontology",
    "ontology gap",
    "missing ontology",
    "route_to_ontology_expansion_request",
    "ontology expansion request",
    "ontology_expansion_request",
)

_REVIEW_ONLY_TEXT_MARKERS_V1 = (
    "extraordinary claim",
    "fringe edge science",
    "edge science",
    "future work",
    "future workforce",
    "job transformation",
    "job replacement",
    "language protocol",
    "universal language",
    "understands all communication",
    "artifact proposal",
    "proposal payload",
    "proposal submission",
    "proposal application",
)


def allowed_cross_domain_scout_to_mlcf_candidate_preparation_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_STATUSES_V1


def allowed_cross_domain_scout_to_mlcf_candidate_readiness_labels_v1() -> tuple[str, ...]:
    return _ALLOWED_READINESS_LABELS_V1


def allowed_cross_domain_scout_to_mlcf_candidate_preparation_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEPS_V1


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    elif payload is not None:
        merged["integration_packet"] = payload
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


def _normalize_unique_text_list(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        return []
    items = _normalize_text_list(value)
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def _json_safe(value: Any) -> bool:
    try:
        json.dumps(value, sort_keys=True)
    except (TypeError, ValueError):
        return False
    return True


def _stringify(value: Any) -> str:
    return _compact_text(value, default="")


def _lower_text(value: Any) -> str:
    return _stringify(value).lower()


def _iter_text_values(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_text_values(item))
        return values
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(_iter_text_values(item))
        return values
    if isinstance(value, tuple):
        values: list[str] = []
        for item in value:
            values.extend(_iter_text_values(item))
        return values
    text = _stringify(value)
    return [text] if text else []


def _contains_forbidden_marker(value: Any) -> bool:
    for text in _iter_text_values(value):
        lowered = text.lower()
        if any(marker in lowered for marker in _FORBIDDEN_TEXT_MARKERS_V1):
            return True
        if any(marker in lowered for marker in _PRIVATE_HIDDEN_PROTECTED_MARKERS_V1):
            return True
    return False


def _contains_forbidden_key_name(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _lower_text(key)
            if key_text.startswith("no_"):
                continue
            if any(marker in key_text for marker in _FORBIDDEN_KEY_NAMES_V1):
                return True
            if _contains_forbidden_key_name(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_key_name(item) for item in value)
    elif isinstance(value, tuple):
        return any(_contains_forbidden_key_name(item) for item in value)
    return False


def _pick_first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _pick_list(*values: Any) -> list[str]:
    for value in values:
        items = _normalize_unique_text_list(value)
        if items:
            return items
    return []


def _combined_text_blobs(*values: Any) -> str:
    return " ".join(_iter_text_values(values)).lower()


def _candidate_natural_language_blob(mapping: Mapping[str, Any]) -> str:
    if not isinstance(mapping, Mapping):
        return ""
    selected_keys = (
        "science_direction_summary",
        "domain_focus",
        "owner_review_posture",
        "operator_review_need",
        "official_public_source_requirement",
        "source_classes_needed",
        "missing_evidence",
        "disconfirming_evidence",
        "pressure_test_questions",
        "probe_suggestions",
    )
    values: list[Any] = []
    for key in selected_keys:
        if key in mapping:
            values.append(mapping.get(key))
    return " ".join(_iter_text_values(values)).lower()


def _contains_any_marker(text_blob: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text_blob for marker in markers)


def _safe_preview_from_integration(packet: Mapping[str, Any]) -> dict[str, Any]:
    preview = _pick_first_mapping(
        packet.get("mlcf_candidate_payload_preview"),
        packet.get("route_decision_payload_preview"),
    )
    preview.setdefault("science_direction_summary", _compact_text(preview.get("science_direction_summary") or packet.get("source_scout_summary") or packet.get("science_direction_summary")))
    preview.setdefault("domain_focus", _pick_list(preview.get("domain_focus"), packet.get("domain_focus"), packet.get("domain_summaries")))
    preview.setdefault("domain_summaries", _pick_list(preview.get("domain_summaries"), packet.get("domain_summaries"), packet.get("source_scout_summary")))
    preview.setdefault("relation_type_hints", _pick_list(preview.get("relation_type_hints"), packet.get("relation_type_hints"), packet.get("candidate_relation_types")))
    preview.setdefault("cross_domain_bridge_refs", _pick_list(preview.get("cross_domain_bridge_refs"), packet.get("candidate_bridge_refs"), packet.get("candidate_signal_refs")))
    preview.setdefault("missing_evidence", _pick_list(preview.get("missing_evidence"), packet.get("missing_evidence")))
    preview.setdefault("disconfirming_signals", _pick_list(preview.get("disconfirming_signals"), packet.get("disconfirming_signals")))
    preview.setdefault("source_classes_needed", _pick_list(preview.get("source_classes_needed"), packet.get("source_classes_needed")))
    preview.setdefault("pressure_test_questions", _pick_list(preview.get("pressure_test_questions"), packet.get("pressure_test_questions")))
    preview.setdefault("probe_suggestions", _pick_list(preview.get("probe_suggestions"), packet.get("probe_suggestions")))
    preview.setdefault("owner_review_posture", _compact_text(preview.get("owner_review_posture"), default="operator_review_required"))
    preview.setdefault("no_claim_authority", bool(preview.get("no_claim_authority", True)))
    return preview


def _source_selection_followup_preview_from_integration(packet: Mapping[str, Any]) -> dict[str, Any]:
    preview = _pick_first_mapping(
        packet.get("source_selection_plan_payload_preview"),
        packet.get("source_selection_followup_preview"),
    )
    preview.setdefault("science_direction_summary", _compact_text(preview.get("science_direction_summary") or packet.get("science_direction_summary") or packet.get("source_scout_summary")))
    preview.setdefault("domain_focus", _pick_list(preview.get("domain_focus"), packet.get("domain_focus"), packet.get("domain_summaries")))
    preview.setdefault("required_source_classes", _pick_list(preview.get("required_source_classes"), packet.get("source_classes_needed"), ["public_research_paper", "official_api_documentation"]))
    preview.setdefault("missing_evidence", _pick_list(preview.get("missing_evidence"), packet.get("missing_evidence")))
    preview.setdefault("disconfirming_evidence_to_seek", _pick_list(preview.get("disconfirming_evidence_to_seek"), packet.get("disconfirming_signals")))
    preview.setdefault("github_role", _compact_text(preview.get("github_role"), default="implementation/reference only"))
    preview.setdefault("official_public_source_requirement", _compact_text(preview.get("official_public_source_requirement"), default="required when evidence planning proceeds"))
    preview.setdefault("operator_review_need", _compact_text(preview.get("operator_review_need"), default="operator review required"))
    return preview


def _extract_bridges(packet: Mapping[str, Any], candidate_preview: Mapping[str, Any]) -> list[str]:
    return _pick_list(
        candidate_preview.get("candidate_bridge_refs"),
        candidate_preview.get("cross_domain_bridge_refs"),
        packet.get("candidate_signal_refs"),
    )


def _route_selected(packet: Mapping[str, Any]) -> str:
    route = _stringify(packet.get("selected_route"))
    if route:
        return route
    for decision in packet.get("route_decisions", []):
        if isinstance(decision, Mapping):
            route = _stringify(decision.get("route_type") or decision.get("selected_route"))
            if route:
                return route
    return ""


def _route_decision_present(packet: Mapping[str, Any], selected_route: str) -> bool:
    for decision in packet.get("route_decisions", []):
        if isinstance(decision, Mapping):
            route_type = _stringify(decision.get("route_type") or decision.get("selected_route"))
            if route_type == selected_route:
                return True
    return False


def _dominant_missing_evidence(missing_evidence: list[str], bridges: list[str], disconfirming: list[str]) -> bool:
    if not missing_evidence:
        return False
    return len(missing_evidence) >= 4


def _derive_missing_evidence_items(
    *,
    packet: Mapping[str, Any],
    candidate_preview: Mapping[str, Any],
    source_selection_preview: Mapping[str, Any],
    disconfirming_signals: list[str],
) -> list[str]:
    derived: list[str] = []

    def add(item: str) -> None:
        item = _compact_text(item)
        if item and item not in derived:
            derived.append(item)

    combined_text = " \n".join(
        _iter_text_values({
            "source_scout_summary": packet.get("source_scout_summary"),
            "science_direction_summary": candidate_preview.get("science_direction_summary"),
            "source_selection_summary": source_selection_preview.get("science_direction_summary"),
            "domain_summaries": candidate_preview.get("domain_summaries"),
            "relation_type_hints": candidate_preview.get("relation_type_hints"),
            "pressure_test_questions": candidate_preview.get("pressure_test_questions"),
            "probe_suggestions": candidate_preview.get("probe_suggestions"),
            "disconfirming_signals": disconfirming_signals,
            "operator_review_reasons": packet.get("operator_review_reasons"),
        })
    ).lower()

    checks: list[tuple[tuple[str, ...], str]] = [
        (("missing measurement", "missing measurements", "measurement coverage", "insufficient measurement", "uncertain measurement"), "missing measurement coverage needs controlled validation"),
        (("future validation", "needs validation", "future work", "future research", "further research", "controlled validation"), "future validation still needed"),
        (("unknown mechanism", "not fully understood", "unresolved mechanism", "mechanism is not fully understood", "mechanism remains unresolved"), "mechanism remains unresolved"),
        (("replication gap", "replication gaps", "replication target", "replication evidence", "replication needed"), "replication evidence still needed"),
        (("insufficient controlled evidence", "insufficient evidence", "controlled evidence", "validation before any stronger method", "before any stronger method is trusted"), "insufficient controlled evidence for stronger acceptance"),
        (("weak analogy", "pressure testing", "pressure-test", "pressure test", "weak route"), "additional pressure-testing evidence needed"),
        (("disconfirming", "counterexample", "contradiction", "anomaly", "model failure", "failed model"), "disconfirming evidence still needed"),
        (("source classes needed", "required_source_classes", "source class", "public_research_paper", "official_api_documentation", "official_standard"), "source classes still needed for review"),
    ]

    # Keep the derived list intentionally small so operator-review posture stays intact
    # for valid bridge candidates while still carrying unresolved-work metadata forward.
    for markers, item in checks:
        if any(marker in combined_text for marker in markers):
            add(item)
        if len(derived) >= 3:
            break

    if not derived and disconfirming_signals:
        add("disconfirming evidence still needed")
    return derived


def _build_safe_metadata_summary(packet: Mapping[str, Any], status: str, readiness: str, next_step: str) -> dict[str, Any]:
    return {
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
        "preparation_status": status,
        "candidate_readiness_label": readiness,
        "next_safe_step": next_step,
        "selected_route": _route_selected(packet),
    }


def _normalize_packet(packet: Mapping[str, Any], *, candidate_preparation_id: str) -> dict[str, Any]:
    integration_validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(packet)
    selected_route = _route_selected(packet)
    route_present = _route_decision_present(packet, selected_route) if selected_route else False
    candidate_preview = _safe_preview_from_integration(packet)
    source_selection_preview = _source_selection_followup_preview_from_integration(packet)
    bridges = _extract_bridges(packet, candidate_preview)
    domain_summaries = _pick_list(candidate_preview.get("domain_summaries"), packet.get("domain_summaries"), packet.get("source_scout_summary"))
    relation_hints = _pick_list(candidate_preview.get("relation_type_hints"), packet.get("relation_type_hints"))
    missing_evidence = _pick_list(candidate_preview.get("missing_evidence"), packet.get("missing_evidence"))
    disconfirming_signals = _pick_list(candidate_preview.get("disconfirming_signals"), packet.get("disconfirming_signals"))
    source_classes_needed = _pick_list(candidate_preview.get("source_classes_needed"), packet.get("source_classes_needed"), source_selection_preview.get("required_source_classes"), ["public_research_paper", "official_api_documentation"])
    pressure_questions = _pick_list(candidate_preview.get("pressure_test_questions"), packet.get("pressure_test_questions"))
    probe_suggestions = _pick_list(candidate_preview.get("probe_suggestions"), packet.get("probe_suggestions"))
    operator_review_reasons = _pick_list(packet.get("operator_review_reasons"), candidate_preview.get("operator_review_reasons"), source_selection_preview.get("operator_review_need"))
    blocked_reasons = _pick_list(packet.get("blocked_reasons"), integration_validation.get("blocked_labels"))
    denied_authority_flags = dict(_DENIED_AUTHORITY_FLAGS_V1)
    source_denied = packet.get("denied_authority_flags")
    if isinstance(source_denied, Mapping):
        for key in denied_authority_flags:
            if key in source_denied:
                denied_authority_flags[key] = bool(source_denied.get(key))
    source_selected_route = selected_route

    if not missing_evidence:
        missing_evidence = _derive_missing_evidence_items(
            packet=packet,
            candidate_preview=candidate_preview,
            source_selection_preview=source_selection_preview,
            disconfirming_signals=disconfirming_signals,
        )

    candidate_text_blob = _candidate_natural_language_blob(candidate_preview)
    source_selection_text_blob = _candidate_natural_language_blob(source_selection_preview)
    review_text_blob = " ".join([candidate_text_blob, source_selection_text_blob]).strip()
    ontology_expansion_requested = (
        selected_route == "route_to_ontology_expansion_request"
        or any(_compact_text(packet.get(field)) for field in _ONTOLOGY_EXPANSION_HANOFF_FIELDS_V1)
        or bool(isinstance(packet.get("safe_metadata_summary"), Mapping) and packet["safe_metadata_summary"].get("sufficient_power") is False)
        or _contains_any_marker(review_text_blob, _ONTOLOGY_EXPANSION_TEXT_MARKERS_V1)
    )
    review_only_marker_present = _contains_any_marker(review_text_blob, _REVIEW_ONLY_TEXT_MARKERS_V1)

    unsafe = (
        _contains_forbidden_key_name(candidate_preview)
        or _contains_forbidden_key_name(source_selection_preview)
        or _contains_forbidden_marker(candidate_preview)
        or _contains_forbidden_marker(source_selection_preview)
        or any(bool(denied_authority_flags.get(key)) for key in denied_authority_flags)
    )

    blocked_route = selected_route in _BLOCKED_OR_REVIEW_ONLY_ROUTE_TYPES_V1
    wrong_route = source_selected_route != "scout_to_mlcf_cross_domain_candidate"
    has_route_decision = route_present or bool(source_selected_route)
    missing_evidence_dominates = _dominant_missing_evidence(missing_evidence, bridges, disconfirming_signals)
    has_bridges = bool(bridges)

    if unsafe:
        status = "candidate_preparation_blocked_by_safety"
        readiness = "metadata_candidate_blocked"
        next_step = "blocked_by_safety"
        blocked_reasons = _pick_list(blocked_reasons, ["unsafe_source_content_or_authority_marker_detected"])
    elif ontology_expansion_requested:
        status = "candidate_preparation_blocked_by_safety"
        readiness = "metadata_candidate_blocked"
        next_step = "blocked_by_safety"
        blocked_reasons = _pick_list(
            blocked_reasons,
            [
                "ontology_expansion_request_not_candidate_preparation_eligible",
                "operator_review_required",
                "sufficient_power_false",
                "candidate_preparation_not_allowed",
            ],
        )
    elif blocked_route or integration_validation.get("blocked"):
        status = "candidate_preparation_blocked_by_safety"
        readiness = "metadata_candidate_blocked"
        next_step = "blocked_by_safety"
        blocked_reasons = _pick_list(
            blocked_reasons,
            integration_validation.get("blocked_labels") or ["source_scout_packet_not_candidate_preparation_eligible", "blocked_by_safety"],
        )
        for label in ("source_scout_packet_not_candidate_preparation_eligible", "blocked_by_safety", "operator_review_required"):
            if label not in blocked_reasons:
                blocked_reasons.append(label)
    elif review_only_marker_present:
        status = "candidate_preparation_blocked_by_safety"
        readiness = "metadata_candidate_blocked"
        next_step = "blocked_by_safety"
        blocked_reasons = _pick_list(
            blocked_reasons,
            [
                "candidate_preparation_not_allowed",
                "operator_review_required",
                "review_only_signal_not_candidate_preparation_eligible",
            ],
        )
    elif wrong_route:
        status = "candidate_preparation_excluded_wrong_route"
        readiness = "metadata_candidate_low_value_or_weak"
        next_step = "exclude_wrong_route"
        blocked_reasons = _pick_list(blocked_reasons, ["selected_route_not_mlcf_cross_domain_candidate"])
    elif not has_route_decision:
        status = "candidate_preparation_needs_repair"
        readiness = "metadata_candidate_low_value_or_weak"
        next_step = "needs_repair"
        blocked_reasons = _pick_list(blocked_reasons, ["missing_route_decision"])
    elif not has_bridges:
        status = "candidate_preparation_needs_repair"
        readiness = "metadata_candidate_low_value_or_weak"
        next_step = "needs_repair"
        blocked_reasons = _pick_list(blocked_reasons, ["missing_candidate_bridge_refs"])
    elif missing_evidence_dominates:
        status = "candidate_preparation_needs_source_selection_plan"
        readiness = "metadata_candidate_needs_evidence_plan"
        next_step = "prepare_source_selection_evidence_plan"
    else:
        status = "candidate_preparation_ready_for_operator_review"
        readiness = "metadata_candidate_ready_for_review"
        next_step = "operator_review"

    if any(
        signal in " ".join(disconfirming_signals + missing_evidence + operator_review_reasons).lower()
        for signal in ("contradiction", "anomaly", "model-failure", "model failure", "failed model")
    ):
        for reason in (
            "contradiction or anomaly signal requires operator review",
            "disconfirming evidence planning is preserved",
        ):
            if reason not in operator_review_reasons:
                operator_review_reasons.append(reason)

    if "operator review required" not in " ".join(operator_review_reasons).lower():
        operator_review_reasons.append("operator review required")

    if not candidate_preparation_id:
        status = "candidate_preparation_needs_repair"
        readiness = "metadata_candidate_low_value_or_weak"
        next_step = "needs_repair"
        blocked_reasons = _pick_list(blocked_reasons, ["missing_candidate_preparation_id"])

    validation_status = {
        "valid": True,
        "blocked": status == "candidate_preparation_blocked_by_safety",
        "validation_posture": "valid" if status != "candidate_preparation_blocked_by_safety" else "blocked",
        "integration_validation": integration_validation,
        "route_present": route_present,
        "has_bridges": has_bridges,
        "missing_evidence_dominates": missing_evidence_dominates,
        "unsafe": unsafe,
        "ontology_expansion_requested": ontology_expansion_requested,
        "review_only_marker_present": review_only_marker_present,
        "operator_review_required": True,
    }

    packet_out = {
        "schema_version": SCHEMA_VERSION_V1,
        "candidate_preparation_id": candidate_preparation_id,
        "source_integration_packet_ref": _compact_text(packet.get("integration_id") or packet.get("source_scout_packet_ref") or packet.get("source_scout_packet_id") or candidate_preparation_id),
        "source_selected_route": source_selected_route,
        "preparation_status": status,
        "candidate_readiness_label": readiness,
        "domain_summaries": domain_summaries,
        "relation_type_hints": relation_hints,
        "candidate_bridge_refs": bridges,
        "missing_evidence": missing_evidence,
        "disconfirming_signals": disconfirming_signals,
        "source_classes_needed": source_classes_needed,
        "pressure_test_questions": pressure_questions,
        "probe_suggestions": probe_suggestions,
        "operator_review_reasons": operator_review_reasons,
        "mlcf_cross_domain_candidate_helper_payload_preview": candidate_preview,
        "source_selection_followup_preview": source_selection_preview,
        "blocked_reasons": blocked_reasons,
        "denied_authority_flags": denied_authority_flags,
        "next_safe_step": next_step,
        "validation_status": validation_status,
        "safe_metadata_summary": _build_safe_metadata_summary(packet, status, readiness, next_step),
    }
    return packet_out


def build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(
    integration_packet=None,
    *,
    candidate_preparation_id=None,
    **overrides: Any,
) -> dict[str, Any]:
    merged = _merge_payload(integration_packet, **overrides)
    candidate_preparation_id = _compact_text(candidate_preparation_id or merged.get("candidate_preparation_id") or merged.get("integration_id") or "cross_domain_scout_to_mlcf_candidate_preparation")
    merged["candidate_preparation_id"] = candidate_preparation_id
    packet = _normalize_packet(merged, candidate_preparation_id=candidate_preparation_id)
    for key, value in overrides.items():
        if key == "candidate_preparation_id":
            continue
        if value is not None:
            packet[key] = copy.deepcopy(value)
    return packet


def validate_cross_domain_scout_to_mlcf_candidate_preparation_request_v1(request):
    blocked_labels: list[str] = []
    if not isinstance(request, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "blocked_labels": ["non_mapping_request"],
            "validation_posture": "blocked",
        }
    if _contains_forbidden_key_name(request) or _contains_forbidden_marker(request):
        blocked_labels.append("unsafe_request_content")
    if not _json_safe(dict(request)):
        blocked_labels.append("non_json_safe_request")
    if "integration_packet" not in request and "scout_packet" not in request:
        blocked_labels.append("missing_integration_packet")
    else:
        integration_packet = request.get("integration_packet", request.get("scout_packet"))
        integration_validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(integration_packet)
        if not isinstance(integration_packet, Mapping):
            blocked_labels.append("invalid_integration_packet")
        else:
            required_route_fields = ("integration_id", "selected_route", "route_decisions", "mlcf_candidate_payload_preview")
            route_present = _stringify(integration_packet.get("selected_route")) == "scout_to_mlcf_cross_domain_candidate"
            decision_present = any(
                isinstance(decision, Mapping)
                and _stringify(decision.get("route_type") or decision.get("selected_route")) == "scout_to_mlcf_cross_domain_candidate"
                for decision in integration_packet.get("route_decisions", [])
            )
            preview_present = isinstance(integration_packet.get("mlcf_candidate_payload_preview"), Mapping)
            if any(field not in integration_packet for field in required_route_fields) or not route_present or not decision_present or not preview_present or not integration_validation.get("valid", False):
                blocked_labels.append("invalid_integration_packet")
    if not _compact_text(request.get("candidate_preparation_id") or request.get("integration_id")):
        blocked_labels.append("missing_candidate_preparation_id")
    if blocked_labels:
        return {
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "validation_posture": "blocked",
        }
    return {
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
        "validation_posture": "valid",
    }


def validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet):
    if not isinstance(packet, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "blocked_labels": ["non_mapping_packet"],
            "validation_posture": "blocked",
        }
    blocked_labels: list[str] = []
    for field in _REQUIRED_FIELD_NAMES_V1:
        if field not in packet:
            blocked_labels.append(f"missing_{field}")
    if blocked_labels:
        return {
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "validation_posture": "blocked",
        }
    if _stringify(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")
    if _stringify(packet.get("candidate_preparation_id")) == "":
        blocked_labels.append("missing_candidate_preparation_id")
    preparation_status = _stringify(packet.get("preparation_status"))
    candidate_readiness_label = _stringify(packet.get("candidate_readiness_label"))
    next_safe_step = _stringify(packet.get("next_safe_step"))
    if preparation_status not in _ALLOWED_STATUSES_V1:
        blocked_labels.append("invalid_preparation_status")
    if candidate_readiness_label not in _ALLOWED_READINESS_LABELS_V1:
        blocked_labels.append("invalid_candidate_readiness_label")
    if next_safe_step not in _ALLOWED_NEXT_STEPS_V1:
        blocked_labels.append("invalid_next_safe_step")
    if preparation_status == "candidate_preparation_blocked_by_safety" or candidate_readiness_label == "metadata_candidate_blocked" or next_safe_step == "blocked_by_safety":
        blocked_labels.append("blocked_by_safety_preparation_status")
    for field in _REQUIRED_TEXT_FIELDS_V1:
        if not _stringify(packet.get(field)):
            blocked_labels.append(f"missing_text_{field}")
    for field in _REQUIRED_LIST_FIELDS_V1:
        value = packet.get(field)
        if not isinstance(value, list):
            blocked_labels.append(f"invalid_list_{field}")
        elif field in {"domain_summaries", "relation_type_hints", "candidate_bridge_refs", "source_classes_needed"} and not _normalize_text_list(value):
            blocked_labels.append(f"empty_{field}")
    for field in _REQUIRED_DICT_FIELDS_V1:
        if not isinstance(packet.get(field), Mapping):
            blocked_labels.append(f"invalid_dict_{field}")
    denied = packet.get("denied_authority_flags")
    if not isinstance(denied, Mapping):
        blocked_labels.append("invalid_denied_authority_flags")
    else:
        for key, expected in _DENIED_AUTHORITY_FLAGS_V1.items():
            if denied.get(key) is not expected:
                blocked_labels.append(f"unsafe_denied_authority_flag_true_{key}")
    if not isinstance(packet.get("validation_status"), Mapping):
        blocked_labels.append("invalid_validation_status")
    else:
        if not packet["validation_status"].get("operator_review_required", True):
            blocked_labels.append("missing_operator_review_posture")
        if packet["validation_status"].get("blocked", False):
            blocked_labels.append("blocked_by_safety_preparation_status")
    candidate_preview = packet.get("mlcf_cross_domain_candidate_helper_payload_preview")
    source_selection_preview = packet.get("source_selection_followup_preview")
    if _contains_forbidden_key_name(candidate_preview) or _contains_forbidden_key_name(source_selection_preview) or _contains_forbidden_marker(candidate_preview) or _contains_forbidden_marker(source_selection_preview):
        blocked_labels.append("unsafe_source_content_or_authority_marker")
    if not _json_safe(dict(packet)):
        blocked_labels.append("non_json_safe_packet")
    valid = not blocked_labels
    blocked = any(label.startswith("unsafe_") or label.startswith("invalid_") or label.startswith("missing_") or label.startswith("blocked_by_safety") or label == "non_json_safe_packet" for label in blocked_labels) or bool(packet.get("validation_status", {}).get("blocked", False))
    posture = "valid" if valid else "blocked"
    return {
        "valid": valid,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "validation_posture": posture,
    }


def summarize_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet):
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet)
    if not isinstance(packet, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "summary_text": "invalid candidate preparation packet",
            "blocked_labels": ["non_mapping_packet"],
        }
    summary = {
        "candidate_preparation_id": _stringify(packet.get("candidate_preparation_id")),
        "source_selected_route": _stringify(packet.get("source_selected_route")),
        "preparation_status": _stringify(packet.get("preparation_status")),
        "candidate_readiness_label": _stringify(packet.get("candidate_readiness_label")),
        "domain_summaries": _normalize_text_list(packet.get("domain_summaries")),
        "relation_type_hints": _normalize_text_list(packet.get("relation_type_hints")),
        "candidate_bridge_refs": _normalize_text_list(packet.get("candidate_bridge_refs")),
        "missing_evidence": _normalize_text_list(packet.get("missing_evidence")),
        "disconfirming_signals": _normalize_text_list(packet.get("disconfirming_signals")),
        "next_safe_step": _stringify(packet.get("next_safe_step")),
        "validation_posture": validation["validation_posture"],
        "safe_metadata_summary": copy.deepcopy(packet.get("safe_metadata_summary", {})),
    }
    summary["summary_text"] = (
        f"{summary['candidate_preparation_id']}: {summary['preparation_status']} -> {summary['next_safe_step']} "
        f"with {len(summary['candidate_bridge_refs'])} bridge refs, {len(summary['missing_evidence'])} missing-evidence items, "
        f"and operator review required."
    )
    return summary


def to_cross_domain_scout_to_mlcf_candidate_preparation_json_safe_v1(packet):
    if not isinstance(packet, Mapping):
        return packet
    safe = copy.deepcopy(dict(packet))
    safe["safe_metadata_summary"] = copy.deepcopy(safe.get("safe_metadata_summary", {}))
    safe["validation_status"] = copy.deepcopy(safe.get("validation_status", {}))
    safe["denied_authority_flags"] = copy.deepcopy(safe.get("denied_authority_flags", {}))
    safe["mlcf_cross_domain_candidate_helper_payload_preview"] = copy.deepcopy(safe.get("mlcf_cross_domain_candidate_helper_payload_preview", {}))
    safe["source_selection_followup_preview"] = copy.deepcopy(safe.get("source_selection_followup_preview", {}))
    return safe


def build_initial_cross_domain_scout_to_mlcf_candidate_preparation_examples_v1() -> list[dict[str, Any]]:
    ready = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(
        {
            "integration_id": "integration_ready_example",
            "selected_route": "scout_to_mlcf_cross_domain_candidate",
            "route_decisions": [{"route_type": "scout_to_mlcf_cross_domain_candidate"}],
            "source_scout_summary": "cross-domain bridge signals remain unresolved",
            "candidate_signal_refs": ["bridge_ref_1", "bridge_ref_2"],
            "mlcf_candidate_payload_preview": {
                "science_direction_summary": "Cross-domain bridge candidate from unresolved signals.",
                "domain_focus": ["physics", "ai_systems"],
                "domain_summaries": ["physics unresolved signal", "ai systems unresolved signal"],
                "relation_type_hints": ["shared_constraint_model"],
                "cross_domain_bridge_refs": ["bridge_ref_1", "bridge_ref_2"],
                "missing_evidence": ["official source confirmation"],
                "disconfirming_signals": ["no contradiction found"],
                "source_classes_needed": ["public_research_paper", "official_api_documentation"],
                "pressure_test_questions": ["What would disprove the bridge?"],
                "probe_suggestions": ["Prepare operator review only."],
                "owner_review_posture": "operator_review_required",
                "no_claim_authority": True,
            },
            "source_selection_plan_payload_preview": {
                "science_direction_summary": "Prepare evidence planning only.",
                "domain_focus": ["physics", "ai_systems"],
                "required_source_classes": ["public_research_paper", "official_api_documentation"],
                "missing_evidence": ["official source confirmation"],
                "disconfirming_evidence_to_seek": ["counterexample source"],
                "github_role": "implementation/reference only",
                "official_public_source_requirement": "required when evidence planning proceeds",
                "operator_review_need": "operator review required",
            },
            "operator_review_reasons": ["operator review required"],
            "blocked_reasons": [],
        },
        candidate_preparation_id="candidate_preparation_ready_example",
    )
    ready["preparation_status"] = "candidate_preparation_ready_for_operator_review"
    ready["candidate_readiness_label"] = "metadata_candidate_ready_for_review"
    ready["next_safe_step"] = "operator_review"
    ready["validation_status"]["blocked"] = False
    ready["validation_status"]["validation_posture"] = "valid"
    ready["safe_metadata_summary"]["preparation_status"] = ready["preparation_status"]
    ready["safe_metadata_summary"]["candidate_readiness_label"] = ready["candidate_readiness_label"]
    ready["safe_metadata_summary"]["next_safe_step"] = ready["next_safe_step"]
    ready["preparation_status"] = "candidate_preparation_ready_for_operator_review"
    ready["candidate_readiness_label"] = "metadata_candidate_ready_for_review"
    ready["next_safe_step"] = "operator_review"
    ready["validation_status"]["blocked"] = False
    ready["validation_status"]["validation_posture"] = "valid"
    ready["safe_metadata_summary"]["preparation_status"] = ready["preparation_status"]
    ready["safe_metadata_summary"]["candidate_readiness_label"] = ready["candidate_readiness_label"]
    ready["safe_metadata_summary"]["next_safe_step"] = ready["next_safe_step"]

    source_plan = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(
        {
            "integration_id": "integration_source_plan_example",
            "selected_route": "scout_to_mlcf_cross_domain_candidate",
            "route_decisions": [{"route_type": "scout_to_mlcf_cross_domain_candidate"}],
            "source_scout_summary": "cross-domain bridge signals remain unresolved",
            "candidate_signal_refs": ["bridge_ref_1"],
            "mlcf_candidate_payload_preview": {
                "science_direction_summary": "Cross-domain bridge candidate needs evidence planning.",
                "domain_focus": ["materials", "biology_life_sciences"],
                "domain_summaries": ["materials signal", "biology signal"],
                "relation_type_hints": ["shared_material_response"],
                "cross_domain_bridge_refs": ["bridge_ref_1"],
                "missing_evidence": ["official source confirmation", "replication target"],
                "disconfirming_signals": ["no contradiction found"],
                "source_classes_needed": ["public_research_paper", "official_standard"],
                "pressure_test_questions": ["Does the evidence support the bridge?"],
                "probe_suggestions": ["Prepare source selection plan."],
                "owner_review_posture": "operator_review_required",
                "no_claim_authority": True,
            },
            "source_selection_plan_payload_preview": {
                "science_direction_summary": "Evidence planning is the next safe step.",
                "domain_focus": ["materials", "biology_life_sciences"],
                "required_source_classes": ["public_research_paper", "official_standard"],
                "missing_evidence": ["official source confirmation", "replication target"],
                "disconfirming_evidence_to_seek": ["counterexample source"],
                "github_role": "implementation/reference only",
                "official_public_source_requirement": "required when evidence planning proceeds",
                "operator_review_need": "operator review required",
            },
            "operator_review_reasons": ["operator review required"],
            "blocked_reasons": [],
        },
        candidate_preparation_id="candidate_preparation_source_plan_example",
    )
    source_plan["missing_evidence"] = ["official source confirmation", "replication target", "additional evidence"]
    source_plan["mlcf_cross_domain_candidate_helper_payload_preview"]["missing_evidence"] = source_plan["missing_evidence"]
    source_plan["candidate_readiness_label"] = "metadata_candidate_needs_evidence_plan"
    source_plan["preparation_status"] = "candidate_preparation_needs_source_selection_plan"
    source_plan["next_safe_step"] = "prepare_source_selection_evidence_plan"
    source_plan["safe_metadata_summary"]["preparation_status"] = source_plan["preparation_status"]
    source_plan["safe_metadata_summary"]["candidate_readiness_label"] = source_plan["candidate_readiness_label"]
    source_plan["safe_metadata_summary"]["next_safe_step"] = source_plan["next_safe_step"]

    wrong_route = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(
        {
            "integration_id": "integration_wrong_route_example",
            "selected_route": "scout_to_source_selection_evidence_plan",
            "route_decisions": [{"route_type": "scout_to_source_selection_evidence_plan"}],
            "source_scout_summary": "route intentionally different",
            "candidate_signal_refs": ["bridge_ref_1"],
            "mlcf_candidate_payload_preview": {
                "science_direction_summary": "Wrong route sample.",
                "domain_focus": ["ai_systems"],
                "domain_summaries": ["route intentionally different"],
                "relation_type_hints": ["unknown_relation"],
                "cross_domain_bridge_refs": ["bridge_ref_1"],
                "missing_evidence": ["evidence"],
                "disconfirming_signals": ["no contradiction found"],
                "source_classes_needed": ["public_research_paper"],
                "pressure_test_questions": ["Should this be excluded?"],
                "probe_suggestions": ["Exclude wrong route."],
                "owner_review_posture": "operator_review_required",
                "no_claim_authority": True,
            },
            "source_selection_plan_payload_preview": {
                "science_direction_summary": "Wrong route excluded.",
                "domain_focus": ["ai_systems"],
                "required_source_classes": ["public_research_paper"],
                "missing_evidence": ["evidence"],
                "disconfirming_evidence_to_seek": ["counterexample source"],
                "github_role": "implementation/reference only",
                "official_public_source_requirement": "required when evidence planning proceeds",
                "operator_review_need": "operator review required",
            },
        },
        candidate_preparation_id="candidate_preparation_wrong_route_example",
    )

    blocked = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(
        {
            "integration_id": "integration_blocked_example",
            "selected_route": "scout_to_mlcf_cross_domain_candidate",
            "route_decisions": [{"route_type": "scout_to_mlcf_cross_domain_candidate"}],
            "source_scout_summary": "unsafe claim marker example",
            "candidate_signal_refs": ["bridge_ref_1"],
            "mlcf_candidate_payload_preview": {
                "science_direction_summary": "This says proof and discovery.",
                "domain_focus": ["physics"],
                "domain_summaries": ["unsafe claim marker example"],
                "relation_type_hints": ["shared_wave_behavior"],
                "cross_domain_bridge_refs": ["bridge_ref_1"],
                "missing_evidence": ["evidence"],
                "disconfirming_signals": ["no contradiction found"],
                "source_classes_needed": ["public_research_paper"],
                "pressure_test_questions": ["Is this blocked?"],
                "probe_suggestions": ["Block unsafe marker."],
                "owner_review_posture": "operator_review_required",
                "no_claim_authority": True,
                "unsafe_marker": "proof discovery final answer",
            },
            "source_selection_plan_payload_preview": {
                "science_direction_summary": "Unsafe marker sample.",
                "domain_focus": ["physics"],
                "required_source_classes": ["public_research_paper"],
                "missing_evidence": ["evidence"],
                "disconfirming_evidence_to_seek": ["counterexample source"],
                "github_role": "implementation/reference only",
                "official_public_source_requirement": "required when evidence planning proceeds",
                "operator_review_need": "operator review required",
            },
        },
        candidate_preparation_id="candidate_preparation_blocked_example",
    )
    blocked["preparation_status"] = "candidate_preparation_blocked_by_safety"
    blocked["candidate_readiness_label"] = "metadata_candidate_blocked"
    blocked["next_safe_step"] = "blocked_by_safety"
    blocked["blocked_reasons"] = ["unsafe source content or authority marker detected"]
    blocked["validation_status"]["blocked"] = True
    blocked["validation_status"]["validation_posture"] = "blocked"
    blocked["safe_metadata_summary"]["preparation_status"] = blocked["preparation_status"]
    blocked["safe_metadata_summary"]["candidate_readiness_label"] = blocked["candidate_readiness_label"]
    blocked["safe_metadata_summary"]["next_safe_step"] = blocked["next_safe_step"]

    needs_repair = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(
        {
            "integration_id": "integration_needs_repair_example",
            "selected_route": "scout_to_mlcf_cross_domain_candidate",
            "route_decisions": [{"route_type": "scout_to_mlcf_cross_domain_candidate"}],
            "source_scout_summary": "bridge refs absent",
            "candidate_signal_refs": [],
            "mlcf_candidate_payload_preview": {
                "science_direction_summary": "No bridge refs example.",
                "domain_focus": ["ai_systems"],
                "domain_summaries": ["bridge refs absent"],
                "relation_type_hints": ["unknown_relation"],
                "cross_domain_bridge_refs": [],
                "missing_evidence": ["evidence"],
                "disconfirming_signals": ["no contradiction found"],
                "source_classes_needed": ["public_research_paper"],
                "pressure_test_questions": ["Is there any bridge at all?"],
                "probe_suggestions": ["Repair the packet."],
                "owner_review_posture": "operator_review_required",
                "no_claim_authority": True,
            },
            "source_selection_plan_payload_preview": {
                "science_direction_summary": "No bridge refs example.",
                "domain_focus": ["ai_systems"],
                "required_source_classes": ["public_research_paper"],
                "missing_evidence": ["evidence"],
                "disconfirming_evidence_to_seek": ["counterexample source"],
                "github_role": "implementation/reference only",
                "official_public_source_requirement": "required when evidence planning proceeds",
                "operator_review_need": "operator review required",
            },
        },
        candidate_preparation_id="candidate_preparation_needs_repair_example",
    )
    needs_repair["candidate_bridge_refs"] = []
    needs_repair["preparation_status"] = "candidate_preparation_needs_repair"
    needs_repair["candidate_readiness_label"] = "metadata_candidate_low_value_or_weak"
    needs_repair["next_safe_step"] = "needs_repair"
    needs_repair["blocked_reasons"] = ["missing_candidate_bridge_refs"]
    needs_repair["safe_metadata_summary"]["preparation_status"] = needs_repair["preparation_status"]
    needs_repair["safe_metadata_summary"]["candidate_readiness_label"] = needs_repair["candidate_readiness_label"]
    needs_repair["safe_metadata_summary"]["next_safe_step"] = needs_repair["next_safe_step"]

    return [ready, source_plan, wrong_route, blocked, needs_repair]
