"""WESLR Ontology Expansion Request Builder V1.

Pure metadata-only helpers for ontology-expansion request packets.
"""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.unfinished_research_discovery_constants import (
    allowed_unfinished_research_expansion_recommendations_v1,
    allowed_unfinished_research_route_types_v1,
    allowed_unfinished_research_signal_types_v1,
    denied_unfinished_research_authority_flags_v1,
    forbidden_unfinished_research_discovery_meanings_v1,
    required_unfinished_research_disconfirmation_fields_v1,
)
from weslr.unfinished_research_discovery_registry import (
    get_initial_domain_family_registry_v1,
    get_unfinished_research_registry_v1,
    validate_domain_family_registry_v1,
)

PROTOCOL_NAME_V1 = "weslr_ontology_expansion_request"
PROTOCOL_VERSION_V1 = "v1"
CREATED_BY_V1 = "weslr_metadata_only_helper"
ONTOLOGY_MARKER_V1 = "ontology_insufficient_for_domain"
OPERATOR_CONFIRMATION_TOKEN_REQUIRED_V1 = "ONTOLOGY_EXPANSION_REQUEST_CONFIRMED"
DEFAULT_SAFE_NEXT_STEP_V1 = "operator_review"
DEFAULT_STATUS_V1 = "pending_operator_review"

_ALLOWED_SAFE_NEXT_STEPS_V1 = (
    "operator_review",
    "design_new_discovery_lens",
    "repair_registry_constants",
    "repair_validator_enums",
    "request_stronger_disconfirmation",
    "run_second_controlled_true_run_after_review",
)

_ALLOWED_STATUS_V1 = (
    "pending_operator_review",
    "blocked_missing_operator_review",
    "blocked_invalid_request",
    "ready_for_design_lane",
)

_ALLOWED_CURRENT_SIGNAL_TYPES_V1 = allowed_unfinished_research_signal_types_v1() + ("unknown",)
_ALLOWED_CURRENT_ROUTE_TYPES_V1 = allowed_unfinished_research_route_types_v1() + ("unknown",)
_ALLOWED_RECOMMENDED_EXPANSION_ACTIONS_V1 = allowed_unfinished_research_expansion_recommendations_v1()
_ALLOWED_OPERATOR_CONFIRMATION_TOKENS_V1 = (OPERATOR_CONFIRMATION_TOKEN_REQUIRED_V1,)
_REQUIRED_FORBIDDEN_CLAIMS_V1 = tuple(forbidden_unfinished_research_discovery_meanings_v1()) + (
    "WESLR modified itself",
    "WESLR expanded its ontology automatically",
    "WESLR learned new ontology automatically",
)
_REQUIRED_BLOCKED_AUTHORITY_FALSE_STATE_V1 = {
    flag: False for flag in denied_unfinished_research_authority_flags_v1()
}
_REQUIRED_SAFE_METADATA_SUMMARY_V1 = {
    "metadata_only": True,
    "source_content_stored": False,
    "raw_text_stored": False,
    "source_ingestion_performed": False,
    "provider_call_performed": False,
    "runtime_wiring_performed": False,
    "accepted_evidence_created": False,
    "accepted_candidate_created": False,
    "public_claim_created": False,
    "final_answer_created": False,
    "ontology_auto_applied": False,
    "sufficient_power": False,
}
_REQUIRED_ROLLBACK_PLAN_KEYS_V1 = (
    "prior_registry_snapshot_required",
    "changed_fields_required",
    "affected_modules_required",
    "affected_tests_required",
    "revert_commit_required",
    "post_rollback_validation_required",
    "no_memory_mutation_required",
    "no_weslr_io_required",
)
_REQUIRED_PACKET_FIELDS_V1 = (
    "protocol_name",
    "protocol_version",
    "expansion_request_id",
    "created_by",
    "source_locator_ids",
    "triggering_signal_summary",
    "why_current_ontology_failed",
    "current_signal_type_attempted",
    "current_route_attempted",
    "sufficient_power",
    "ontology_marker",
    "recommended_expansion_actions",
    "operator_review_required",
    "operator_confirmation_token_required",
    "required_disconfirming_evidence",
    "rollback_plan",
    "blocked_authorities",
    "forbidden_claims",
    "safe_next_step",
    "status",
    "blocked_labels",
    "safe_metadata_summary",
)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_text_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        items = value
    elif isinstance(value, list):
        items = value
    else:
        items = (value,)
    result = []
    seen = set()
    for item in items:
        text = _normalize_text(item)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return tuple(result)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=str)]
    return deepcopy(value)


def _is_json_safe(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_json_safe(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_safe(item) for key, item in value.items())
    return False


def _contains_forbidden_language(text: str) -> bool:
    lowered = text.lower()
    forbidden_markers = (
        "accepted evidence",
        "accepted candidate",
        "proposal payload",
        "final answer",
        "public claim",
        "proof",
        "public science",
        "official benchmark result",
        "ontology self-modification",
        "proven truth",
        "solved theory",
        "verified invention",
        "discovery as proven truth",
        "discovery as solved theory",
        "discovery as verified invention",
        "discovery as accepted evidence",
        "discovery as public science claim",
        "discovery as agi consciousness sentience claim",
        "discovery as official benchmark result",
        "discovery as final answer",
        "discovery as ontology self-modification",
        "weslr modified itself",
        "weslr expanded its ontology automatically",
        "weslr learned new ontology automatically",
    )
    return any(marker in lowered for marker in forbidden_markers)


def _contains_forbidden_key_names(packet: Mapping[str, Any]) -> bool:
    forbidden = {
        "raw_html",
        "raw_text",
        "raw_source_text",
        "source_content",
        "source_contents",
        "page_content",
        "full_text",
        "snippet",
        "snippets",
        "html",
        "quote",
        "excerpt",
        "paper_text",
        "article_text",
        "repository_content",
        "downloaded_content",
        "private_data",
        "final_answer",
        "accepted_evidence",
        "accepted_candidate",
        "proposal_payload",
    }
    return any(str(key) in forbidden for key in packet.keys())


def _default_safe_metadata_summary() -> dict[str, Any]:
    return deepcopy(_REQUIRED_SAFE_METADATA_SUMMARY_V1)


def _default_blocked_authorities() -> dict[str, bool]:
    return deepcopy(_REQUIRED_BLOCKED_AUTHORITY_FALSE_STATE_V1)


def _default_required_disconfirming_evidence() -> dict[str, str]:
    return {field: "" for field in required_unfinished_research_disconfirmation_fields_v1()}


def _default_rollback_plan() -> dict[str, bool]:
    return {key: True for key in _REQUIRED_ROLLBACK_PLAN_KEYS_V1}


def _reason_allows_unknown(reason: str) -> bool:
    lowered = reason.lower()
    signals = (
        "no current enum fit",
        "no current signal enum fit",
        "no current route enum fit",
        "no current ontology fit",
        "no current enum matched",
        "no ontology enum fit",
    )
    return any(token in lowered for token in signals)


def _build_expansion_request_id(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"oer_{sha256(canonical.encode('utf-8')).hexdigest()[:16]}"


def build_ontology_expansion_request_v1(
    *,
    source_locator_ids: Any,
    triggering_signal_summary: Any,
    why_current_ontology_failed: Any,
    current_signal_type_attempted: Any,
    current_route_attempted: Any,
    recommended_expansion_actions: Any,
    required_disconfirming_evidence: Any,
    rollback_plan: Any,
    blocked_authorities: Any | None = None,
    forbidden_claims: Any | None = None,
    safe_next_step: str = DEFAULT_SAFE_NEXT_STEP_V1,
    status: str = DEFAULT_STATUS_V1,
    operator_review_required: bool = True,
    protocol_name: str = PROTOCOL_NAME_V1,
    protocol_version: str = PROTOCOL_VERSION_V1,
    created_by: str = CREATED_BY_V1,
    sufficient_power: bool = False,
    ontology_marker: str = ONTOLOGY_MARKER_V1,
    operator_confirmation_token_required: str = OPERATOR_CONFIRMATION_TOKEN_REQUIRED_V1,
    expansion_request_id: str | None = None,
    safe_metadata_summary: Any | None = None,
) -> dict[str, Any]:
    source_locator_ids_t = _normalize_text_list(source_locator_ids)
    recommended_actions_t = _normalize_text_list(recommended_expansion_actions)
    forbidden_claims_t = _normalize_text_list(forbidden_claims if forbidden_claims is not None else _REQUIRED_FORBIDDEN_CLAIMS_V1)
    blocked_authorities_map = dict(blocked_authorities) if isinstance(blocked_authorities, Mapping) else _default_blocked_authorities()
    required_disconfirming_evidence_map = dict(required_disconfirming_evidence) if isinstance(required_disconfirming_evidence, Mapping) else _default_required_disconfirming_evidence()
    rollback_plan_map = dict(rollback_plan) if isinstance(rollback_plan, Mapping) else _default_rollback_plan()
    safe_metadata = dict(safe_metadata_summary) if isinstance(safe_metadata_summary, Mapping) else _default_safe_metadata_summary()

    packet = {
        "protocol_name": _normalize_text(protocol_name),
        "protocol_version": _normalize_text(protocol_version),
        "expansion_request_id": _normalize_text(expansion_request_id) or "",
        "created_by": _normalize_text(created_by),
        "source_locator_ids": source_locator_ids_t,
        "triggering_signal_summary": _normalize_text(triggering_signal_summary),
        "why_current_ontology_failed": _normalize_text(why_current_ontology_failed),
        "current_signal_type_attempted": _normalize_text(current_signal_type_attempted),
        "current_route_attempted": _normalize_text(current_route_attempted),
        "sufficient_power": bool(sufficient_power),
        "ontology_marker": _normalize_text(ontology_marker),
        "recommended_expansion_actions": recommended_actions_t,
        "operator_review_required": bool(operator_review_required),
        "operator_confirmation_token_required": _normalize_text(operator_confirmation_token_required),
        "required_disconfirming_evidence": required_disconfirming_evidence_map,
        "rollback_plan": rollback_plan_map,
        "blocked_authorities": blocked_authorities_map,
        "forbidden_claims": forbidden_claims_t,
        "safe_next_step": _normalize_text(safe_next_step),
        "status": _normalize_text(status),
        "blocked_labels": (),
        "safe_metadata_summary": safe_metadata,
    }
    if not packet["expansion_request_id"]:
        packet["expansion_request_id"] = _build_expansion_request_id(packet)
    return packet


def validate_ontology_expansion_request_v1(packet: Any) -> dict[str, Any]:
    labels: list[str] = []
    ok = True
    if not isinstance(packet, Mapping):
        return {"valid": False, "blocked": True, "blocked_labels": ("invalid_request_type",), "validation_status": "blocked"}
    missing = [field for field in _REQUIRED_PACKET_FIELDS_V1 if field not in packet]
    if missing:
        ok = False
        labels.extend(f"missing_{field}" for field in missing)
    if _contains_forbidden_key_names(packet):
        ok = False
        labels.append("forbidden_content_key_present")
    if _normalize_text(packet.get("protocol_name")) != PROTOCOL_NAME_V1:
        ok = False
        labels.append("invalid_protocol_name")
    if _normalize_text(packet.get("protocol_version")) != PROTOCOL_VERSION_V1:
        ok = False
        labels.append("invalid_protocol_version")
    if not _normalize_text(packet.get("expansion_request_id")):
        ok = False
        labels.append("missing_expansion_request_id")
    if _normalize_text(packet.get("created_by")) != CREATED_BY_V1:
        ok = False
        labels.append("invalid_created_by")
    if not _normalize_text_list(packet.get("source_locator_ids")):
        ok = False
        labels.append("missing_source_locator_ids")
    if not _normalize_text(packet.get("triggering_signal_summary")):
        ok = False
        labels.append("missing_triggering_signal_summary")
    if not _normalize_text(packet.get("why_current_ontology_failed")):
        ok = False
        labels.append("missing_why_current_ontology_failed")
    current_signal = _normalize_text(packet.get("current_signal_type_attempted"))
    if current_signal == "unknown":
        if not _reason_allows_unknown(_normalize_text(packet.get("why_current_ontology_failed"))):
            ok = False
            labels.append("unknown_current_signal_without_justification")
    elif current_signal not in _ALLOWED_CURRENT_SIGNAL_TYPES_V1:
        ok = False
        labels.append("unknown_current_signal_type_attempted")
    current_route = _normalize_text(packet.get("current_route_attempted"))
    if current_route == "unknown":
        if not _reason_allows_unknown(_normalize_text(packet.get("why_current_ontology_failed"))):
            ok = False
            labels.append("unknown_current_route_without_justification")
    elif current_route not in _ALLOWED_CURRENT_ROUTE_TYPES_V1:
        ok = False
        labels.append("unknown_current_route_attempted")
    if packet.get("sufficient_power") is not False:
        ok = False
        labels.append("sufficient_power_not_false")
    if _normalize_text(packet.get("ontology_marker")) != ONTOLOGY_MARKER_V1:
        ok = False
        labels.append("invalid_ontology_marker")
    recommended_actions = _normalize_text_list(packet.get("recommended_expansion_actions"))
    if not recommended_actions:
        ok = False
        labels.append("empty_recommended_expansion_actions")
    else:
        allowed = set(_ALLOWED_RECOMMENDED_EXPANSION_ACTIONS_V1)
        for action in recommended_actions:
            if action not in allowed:
                ok = False
                labels.append("unknown_recommended_expansion_action")
                break
    if packet.get("operator_review_required") is not True:
        ok = False
        labels.append("operator_review_required_not_true")
    if _normalize_text(packet.get("operator_confirmation_token_required")) != OPERATOR_CONFIRMATION_TOKEN_REQUIRED_V1:
        ok = False
        labels.append("invalid_operator_confirmation_token_required")
    required_evidence = packet.get("required_disconfirming_evidence")
    if not isinstance(required_evidence, Mapping):
        ok = False
        labels.append("invalid_required_disconfirming_evidence")
    else:
        required_keys = set(required_unfinished_research_disconfirmation_fields_v1())
        if set(required_evidence.keys()) != required_keys:
            ok = False
            labels.append("missing_required_disconfirming_evidence_fields")
        for key in required_keys:
            if not _normalize_text(required_evidence.get(key)):
                ok = False
                labels.append(f"missing_required_disconfirming_evidence_{key}")
    rollback_plan = packet.get("rollback_plan")
    if not isinstance(rollback_plan, Mapping):
        ok = False
        labels.append("invalid_rollback_plan")
    else:
        for key in _REQUIRED_ROLLBACK_PLAN_KEYS_V1:
            if rollback_plan.get(key) is not True:
                ok = False
                labels.append(f"missing_rollback_field_{key}")
    blocked_authorities = packet.get("blocked_authorities")
    if not isinstance(blocked_authorities, Mapping):
        ok = False
        labels.append("invalid_blocked_authorities")
    else:
        for flag in denied_unfinished_research_authority_flags_v1():
            if blocked_authorities.get(flag) is not False:
                ok = False
                labels.append(f"blocked_authority_not_false_{flag}")
    forbidden_claims = _normalize_text_list(packet.get("forbidden_claims"))
    if not forbidden_claims:
        ok = False
        labels.append("empty_forbidden_claims")
    else:
        forbidden_required = set(_REQUIRED_FORBIDDEN_CLAIMS_V1)
        if not forbidden_required.issubset(set(forbidden_claims)):
            ok = False
            labels.append("missing_required_forbidden_claims")
        allowed_forbidden_claims = forbidden_required | {
            "WESLR modified itself",
            "WESLR expanded its ontology automatically",
            "WESLR learned new ontology automatically",
        }
        for claim in forbidden_claims:
            if claim not in allowed_forbidden_claims and _contains_forbidden_language(claim):
                ok = False
                labels.append("forbidden_claim_language_present")
                break
    if _normalize_text(packet.get("safe_next_step")) not in _ALLOWED_SAFE_NEXT_STEPS_V1:
        ok = False
        labels.append("invalid_safe_next_step")
    if _normalize_text(packet.get("status")) not in _ALLOWED_STATUS_V1:
        ok = False
        labels.append("invalid_status")
    safe_metadata = packet.get("safe_metadata_summary")
    if not isinstance(safe_metadata, Mapping):
        ok = False
        labels.append("invalid_safe_metadata_summary")
    else:
        required_safe = _default_safe_metadata_summary()
        for key, expected in required_safe.items():
            if safe_metadata.get(key) is not expected:
                ok = False
                labels.append(f"invalid_safe_metadata_summary_{key}")
    if not _is_json_safe(packet):
        ok = False
        labels.append("non_json_safe_request")
    return {
        "valid": ok,
        "blocked": not ok,
        "blocked_labels": tuple(dict.fromkeys(labels)),
        "validation_status": "valid" if ok else "blocked",
    }


def summarize_ontology_expansion_request_v1(packet: Any) -> dict[str, Any]:
    validation = validate_ontology_expansion_request_v1(packet)
    source_locator_ids = _normalize_text_list(packet.get("source_locator_ids")) if isinstance(packet, Mapping) else ()
    return {
        "protocol_name": PROTOCOL_NAME_V1,
        "protocol_version": PROTOCOL_VERSION_V1,
        "expansion_request_id": _normalize_text(packet.get("expansion_request_id")) if isinstance(packet, Mapping) else "",
        "created_by": CREATED_BY_V1,
        "source_locator_count": len(source_locator_ids),
        "recommended_expansion_action_count": len(_normalize_text_list(packet.get("recommended_expansion_actions"))) if isinstance(packet, Mapping) else 0,
        "operator_review_required": True,
        "sufficient_power": False,
        "ontology_marker": ONTOLOGY_MARKER_V1,
        "validation_status": validation["validation_status"],
        "summary_text": "Metadata-only ontology expansion request summary.",
    }


def to_ontology_expansion_request_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def build_initial_ontology_expansion_request_examples_v1() -> tuple[dict[str, Any], ...]:
    base_safe_metadata = _default_safe_metadata_summary()
    examples = (
        build_ontology_expansion_request_v1(
            source_locator_ids=("locator_unknown_domain_family_001",),
            triggering_signal_summary="An unfamiliar domain family appears to need a new discovery lens.",
            why_current_ontology_failed="No current enum fit: this appears to be an unknown domain family.",
            current_signal_type_attempted="unknown",
            current_route_attempted="unknown",
            recommended_expansion_actions=(
                "expansion_add_new_domain_family",
                "expansion_enlarge_signal_ontology",
                "expansion_add_new_route",
            ),
            required_disconfirming_evidence={field: "metadata-only placeholder" for field in required_unfinished_research_disconfirmation_fields_v1()},
            rollback_plan=_default_rollback_plan(),
            blocked_authorities=_default_blocked_authorities(),
            forbidden_claims=_REQUIRED_FORBIDDEN_CLAIMS_V1,
            safe_next_step="design_new_discovery_lens",
            status="ready_for_design_lane",
            safe_metadata_summary=base_safe_metadata,
        ),
        build_ontology_expansion_request_v1(
            source_locator_ids=("locator_language_protocol_001",),
            triggering_signal_summary="A language protocol pattern suggests ontology expansion is needed.",
            why_current_ontology_failed="Current ontology lacks a language protocol pattern for this request.",
            current_signal_type_attempted="language_protocol_discovery_signal",
            current_route_attempted="route_to_language_protocol_review",
            recommended_expansion_actions=(
                "expansion_add_new_language_protocol_pattern",
                "expansion_add_new_operator_review_category",
            ),
            required_disconfirming_evidence={field: "metadata-only placeholder" for field in required_unfinished_research_disconfirmation_fields_v1()},
            rollback_plan=_default_rollback_plan(),
            blocked_authorities=_default_blocked_authorities(),
            forbidden_claims=_REQUIRED_FORBIDDEN_CLAIMS_V1,
            safe_next_step="repair_registry_constants",
            status="pending_operator_review",
            safe_metadata_summary=base_safe_metadata,
        ),
        build_ontology_expansion_request_v1(
            source_locator_ids=("locator_fringe_claim_001",),
            triggering_signal_summary="A fringe-edge claim needs disconfirmation before any expansion lane can proceed.",
            why_current_ontology_failed="Current ontology cannot represent the fringe claim without a stronger disconfirmation lane.",
            current_signal_type_attempted="extraordinary_claim_signal",
            current_route_attempted="route_to_extraordinary_claim_quarantine",
            recommended_expansion_actions=(
                "expansion_add_new_disconfirmation_class",
                "expansion_add_new_artifact_type",
            ),
            required_disconfirming_evidence={field: "metadata-only placeholder" for field in required_unfinished_research_disconfirmation_fields_v1()},
            rollback_plan=_default_rollback_plan(),
            blocked_authorities=_default_blocked_authorities(),
            forbidden_claims=_REQUIRED_FORBIDDEN_CLAIMS_V1,
            safe_next_step="request_stronger_disconfirmation",
            status="blocked_missing_operator_review",
            safe_metadata_summary=base_safe_metadata,
        ),
        build_ontology_expansion_request_v1(
            source_locator_ids=("locator_future_work_001",),
            triggering_signal_summary="A future-work / job-transformation pattern suggests broader ontology coverage.",
            why_current_ontology_failed="Current ontology cannot capture workforce-impact future work without a new review category.",
            current_signal_type_attempted="future_workforce_impact_signal",
            current_route_attempted="route_to_future_workforce_impact_review",
            recommended_expansion_actions=(
                "expansion_add_new_operator_review_category",
                "expansion_create_new_discovery_lens_design_lane",
            ),
            required_disconfirming_evidence={field: "metadata-only placeholder" for field in required_unfinished_research_disconfirmation_fields_v1()},
            rollback_plan=_default_rollback_plan(),
            blocked_authorities=_default_blocked_authorities(),
            forbidden_claims=_REQUIRED_FORBIDDEN_CLAIMS_V1,
            safe_next_step="run_second_controlled_true_run_after_review",
            status="pending_operator_review",
            safe_metadata_summary=base_safe_metadata,
        ),
        build_ontology_expansion_request_v1(
            source_locator_ids=("locator_discovery_lens_001",),
            triggering_signal_summary="The current lens is too narrow, so a discovery-lens design lane is needed.",
            why_current_ontology_failed="The current ontology lacks an explicit discovery-lens design lane.",
            current_signal_type_attempted="ontology_insufficient_signal",
            current_route_attempted="route_to_artifact_proposal_plan",
            recommended_expansion_actions=(
                "expansion_create_new_discovery_lens_design_lane",
                "expansion_add_new_artifact_type",
            ),
            required_disconfirming_evidence={field: "metadata-only placeholder" for field in required_unfinished_research_disconfirmation_fields_v1()},
            rollback_plan=_default_rollback_plan(),
            blocked_authorities=_default_blocked_authorities(),
            forbidden_claims=_REQUIRED_FORBIDDEN_CLAIMS_V1,
            safe_next_step="design_new_discovery_lens",
            status="ready_for_design_lane",
            safe_metadata_summary=base_safe_metadata,
        ),
    )
    return examples
