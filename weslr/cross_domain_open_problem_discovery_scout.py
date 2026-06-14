"""WESLR Cross-Domain Open Problem Discovery Scout Helper V1.

Pure, deterministic, metadata-only helpers for turning safe owner-provided
metadata into a bounded scout packet for later governed use. This module does
not fetch sources, ingest content, call models, touch runtime, write state, or
perform network/filesystem/subprocess actions.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any, Iterable

from weslr.unfinished_research_discovery_constants import (
    allowed_unfinished_research_artifact_types_v1,
    allowed_unfinished_research_evidence_roles_v1,
    allowed_unfinished_research_route_types_v1,
    allowed_unfinished_research_signal_types_v1,
    required_unfinished_research_disconfirmation_fields_v1,
)
from weslr.unfinished_research_discovery_registry import get_initial_domain_family_registry_v1

SCHEMA_VERSION_V1 = "cross_domain_open_problem_scout_v1"

_DOMAIN_FAMILY_REGISTRY_V1 = get_initial_domain_family_registry_v1()
_DOMAIN_FAMILY_BY_ID_V1 = {
    entry["domain_family_id"]: entry
    for entry in _DOMAIN_FAMILY_REGISTRY_V1
    if isinstance(entry, dict) and entry.get("domain_family_id")
}
_KNOWN_DOMAIN_FAMILY_IDS_V1 = tuple(_DOMAIN_FAMILY_BY_ID_V1)

_SAFE_SIGNAL_TYPE_OUTPUT_ALIASES_V1 = {
    "unsolved_theory_signal": "theory_gap_signal",
    "formal_unsolved_problem_signal": "formal_open_question_signal",
    "language_protocol_discovery_signal": "language_protocol_candidate",
}

_ALLOWED_SIGNAL_TYPES_V1 = tuple(dict.fromkeys(allowed_unfinished_research_signal_types_v1() + (
    "unfinished_work_signal",
    "technology_blocked_signal",
    "cross_domain_transfer_signal",
    "dormant_direction_signal",
    "anomaly_signal",
    "measurement_benchmark_gap_signal",
    "formal_unsolved_problem_signal",
    "extraordinary_claim_signal",
    "fringe_edge_science_signal",
    "time_revisit_signal",
    "domain_convergence_signal",
    "future_workforce_impact_signal",
    "language_protocol_discovery_signal",
    "artifact_generation_candidate",
    "disconfirmation_required",
    "ontology_insufficient_signal",
    "theory_gap_signal",
    "formal_open_question_signal",
    "language_protocol_candidate",
    "open_problem_signal",
    "unsolved_theory_signal",
    "unresolved_mechanism_signal",
    "unexplained_anomaly_signal",
    "future_work_signal",
    "limitation_signal",
    "failed_model_signal",
    "contradiction_signal",
    "underexplored_dataset_signal",
    "missing_measurement_signal",
    "weak_signal",
    "replication_gap_signal",
    "incomplete_benchmark_signal",
    "survey_gap_signal",
    "calibration_gap_signal",
    "not_fully_understood_signal",
    "unknown_mechanism_signal",
    "requires_further_research_signal",
    "blocked_or_unsafe_signal",
    "unknown_signal",
)))

_ALLOWED_NEXT_STEPS_V1 = (
    "operator_review",
    "route_to_source_selection_plan",
    "route_to_cross_domain_scout",
    "route_to_operator_review",
    "route_to_disconfirming_review",
    "route_to_extraordinary_claim_quarantine",
    "route_to_archive_low_value_signal",
    "route_to_blocked_by_safety",
    "route_to_time_revisit_review",
    "route_to_domain_convergence_review",
    "route_to_future_workforce_impact_review",
    "route_to_language_protocol_review",
    "route_to_artifact_proposal_plan",
    "route_to_ontology_expansion_request",
    "needs_repair",
    "blocked_by_safety",
    "archive_low_value_signal",
)

_ALLOWED_SEARCH_GOVERNANCE_MODES_V1 = (
    "metadata_only_owner_review",
    "metadata_only_review",
    "metadata_only_archive",
)

_ALLOWED_CONFIDENCE_LABELS_V1 = ("low", "medium", "high", "unknown")

_ALLOWED_SOURCE_CLASS_LABELS_V1 = {
    "official_standard",
    "official_government_or_agency_data",
    "official_vendor_documentation",
    "official_api_documentation",
    "public_research_paper",
    "survey_paper",
    "review_paper",
    "benchmark_paper",
    "dataset_record",
    "public_dataset",
    "public_patent",
    "thesis_dissertation",
    "github_repository",
    "code_repository_as_implementation_reference",
    "software_release_or_changelog",
    "public_lab_or_university_artifact",
    "conference_workshop_artifact",
    "negative_result_paper",
    "replication_study",
    "historical_archive",
    "technical_report",
    "preprint",
    "vendor_technical_documentation",
    "forum_blog_as_weak_signal",
    "owner_supplied_observation",
    "internal_project_artifact",
    "community_discussion",
    "unknown_authority",
    "unknown_source",
    "blocked_private_or_hidden_source",
}

_AUTHORITY_FALSE_FLAGS_V1 = (
    "source_access_authority",
    "source_fetching_authority",
    "source_ingestion_authority",
    "raw_retention_authority",
    "final_answer_authority",
    "public_claim_authority",
    "discovery_claim_authority",
    "proof_claim_authority",
    "benchmark_claim_authority",
    "agi_claim_authority",
    "consciousness_claim_authority",
    "sentience_claim_authority",
    "runtime_execution_authority",
    "memory_mutation_authority",
    "project_mutation_authority",
    "weslr_io_authority",
    "autonomous_routing_authority",
    "external_action_authority",
    "provider_model_authority",
    "http_authority",
    "web_search_authority",
    "behavior_pack_promotion_authority",
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

_UNSAFE_URL_MARKERS_V1 = (
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "file:",
    "ftp:",
    "data:",
    "javascript:",
    "/private/",
    "/hidden/",
    "/protected/",
    "/secret/",
    "login",
    "signin",
    "auth",
    "credential",
    "password",
)

_FORBIDDEN_CLAIM_MARKERS_V1 = (
    "discovery",
    "proof",
    "public science",
    "official benchmark",
    "solved",
    "solution",
    "truth",
    "accepted evidence",
    "trusted evidence",
    "final answer",
)

_OPEN_PROBLEM_MARKERS_V1 = (
    "open problem",
    "unsolved",
    "unresolved",
    "not solved",
    "unknown mechanism",
    "not fully understood",
)

_FUTURE_WORK_MARKERS_V1 = (
    "future work",
    "future research",
    "further research",
    "limitation",
    "limited by",
    "requires further research",
)

_ANOMALY_MARKERS_V1 = (
    "anomaly",
    "unexpected",
    "contradiction",
    "contradictory",
    "does not explain",
    "failed to explain",
    "model failure",
)

_MEASUREMENT_GAP_MARKERS_V1 = (
    "missing measurement",
    "measurement gap",
    "dataset gap",
    "underexplored dataset",
    "replication needed",
    "replication gap",
    "benchmark incomplete",
    "survey gap",
    "calibration gap",
)

_CROSS_DOMAIN_MARKERS_V1 = (
    "similar structure",
    "shared constraint",
    "same pattern",
    "transfer",
    "analogy",
    "cross-domain",
)

_WEAK_SIGNAL_MARKERS_V1 = (
    "maybe",
    "might",
    "possibly",
    "seems",
    "suggests",
    "vague",
    "weak analogy",
    "approximate",
)

DEFAULT_SAFETY_BOUNDARY_V1 = {
    "metadata_only": True,
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
    "no_forbidden_claim_elevation": True,
    "operator_review_required": True,
}


def allowed_cross_domain_open_problem_signal_types_v1() -> tuple[str, ...]:
    return _ALLOWED_SIGNAL_TYPES_V1


def allowed_cross_domain_open_problem_scout_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEPS_V1


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
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
    elif isinstance(value, set):
        items = sorted(value, key=repr)
    else:
        text = _compact_text(value)
        return [text] if text else []
    result: list[str] = []
    for item in items:
        text = _compact_text(item)
        if text:
            result.append(text)
    return result


def _normalize_mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            result.append(dict(item))
        elif isinstance(item, str):
            result.append({"title_or_descriptor": item})
    return result


def _is_json_safe(value: Any) -> bool:
    return _first_non_json_safe_path(value) is None


def _first_non_json_safe_path(value: Any, path: str = "$") -> str | None:
    if value is None or isinstance(value, (str, int, bool)):
        return None
    if isinstance(value, float):
        return None if value == value and value not in {float("inf"), float("-inf")} else path
    if isinstance(value, (bytes, bytearray, memoryview, tuple, set)):
        return path
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                return f"{path}.[non-string-key:{type(key).__name__}]"
            issue = _first_non_json_safe_path(nested, f"{path}.{key}")
            if issue is not None:
                return issue
        return None
    if isinstance(value, list):
        for index, nested in enumerate(value):
            issue = _first_non_json_safe_path(nested, f"{path}[{index}]")
            if issue is not None:
                return issue
        return None
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _first_non_json_safe_path(value.to_dict(), path)
    if hasattr(value, "__dict__"):
        return _first_non_json_safe_path(vars(value), path)
    return path


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)

_FORBIDDEN_OUTPUT_REPLACEMENTS_V1 = (
    ("accepted evidence", "reviewed evidence"),
    ("trusted evidence", "reviewed evidence"),
    ("final answer", "final response"),
    ("discovery", "detection"),
    ("proof", "support"),
    ("unsolved", "open"),
    ("unresolved", "open"),
    ("not solved", "open"),
    ("solution", "resolution"),
    ("truth", "claim"),
)


def _sanitize_forbidden_output_text(text: str) -> str:
    result = text
    lowered = result.lower()
    for forbidden, replacement in _FORBIDDEN_OUTPUT_REPLACEMENTS_V1:
        if forbidden in lowered:
            result = result.replace(forbidden, replacement)
            result = result.replace(forbidden.title(), replacement.title())
            lowered = result.lower()
    return result


def _sanitize_forbidden_output_key(key: Any) -> str:
    return str(key)


def _sanitize_forbidden_output(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize_forbidden_output(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, list):
        return [_sanitize_forbidden_output(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_forbidden_output(item) for item in value]
    if isinstance(value, set):
        return [_sanitize_forbidden_output(item) for item in sorted(value, key=repr)]
    if isinstance(value, str):
        return _sanitize_forbidden_output_text(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _sanitize_forbidden_output(value.to_dict())
    if hasattr(value, "__dict__"):
        return _sanitize_forbidden_output(vars(value))
    return repr(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _contains_any_marker(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    for marker in markers:
        marker_lower = marker.lower()
        if any(ch for ch in marker_lower if not (ch.isalnum() or ch.isspace() or ch == "_")):
            if marker_lower in lowered:
                return True
            continue
        pattern = rf"(?<!\w){re.escape(marker_lower)}(?!\w)"
        if re.search(pattern, lowered):
            return True
    return False


def _contains_forbidden_text(value: Any, markers: Iterable[str] = _FORBIDDEN_CLAIM_MARKERS_V1) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_forbidden_text(item, markers) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    return _contains_any_marker(value, markers)


def _contains_private_hidden_protected_marker(value: Any, markers: Iterable[str] = _PRIVATE_HIDDEN_PROTECTED_MARKERS_V1) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_private_hidden_protected_marker(item, markers) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_private_hidden_protected_marker(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    return _contains_any_marker(value, markers)


def _contains_unsafe_url_or_domain(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_unsafe_url_or_domain(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_unsafe_url_or_domain(item) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    if lowered.startswith(("http://", "https://", "ftp://", "file:", "data:", "javascript:")) and _contains_any_marker(lowered, _UNSAFE_URL_MARKERS_V1):
        return True
    return _contains_any_marker(lowered, _UNSAFE_URL_MARKERS_V1)


def _contains_forbidden_keys(value: Any, forbidden_keys: set[str] = _FORBIDDEN_KEY_NAMES_V1) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _compact_text(key).lower()
            if key_text in forbidden_keys:
                return True
            if _contains_forbidden_keys(nested, forbidden_keys):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_keys(item, forbidden_keys) for item in value)
    return False


def _contains_any_true_flag(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _compact_text(key).lower()
            if key_text.startswith("no_"):
                continue
            if key_text in _AUTHORITY_FALSE_FLAGS_V1 and nested is True:
                return True
            if key_text.endswith("_authorized") and nested is True:
                return True
            if key_text.endswith("_authority") and nested is True:
                return True
            if key_text.endswith("_claims") and nested is True:
                return True
            if _contains_any_true_flag(nested):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_any_true_flag(item) for item in value)
    return False


def _safe_text_source_summary(item: Mapping[str, Any]) -> str:
    fields = (
        "title_or_descriptor",
        "title",
        "descriptor",
        "name",
        "summary",
        "description",
        "why_it_matters",
        "domain_family",
        "source_ref",
        "url",
        "source_class_label",
        "authority_guess",
        "evidence_role_guess",
        "novelty_label",
        "risk_label",
        "query_descriptor",
        "note",
    )
    values = [_compact_text(item.get(field)) for field in fields if _compact_text(item.get(field))]
    return " | ".join(values).lower()


def _safe_domain_family(value: Any) -> str:
    text = _compact_text(value, "unknown_domain")
    return text if text else "unknown_domain"


def _domain_family_profile(domain_family: str) -> dict[str, Any]:
    family_id = _safe_domain_family(domain_family)
    profile = _DOMAIN_FAMILY_BY_ID_V1.get(family_id, {})
    return {
        "domain_family_id": family_id,
        "domain_family_known": family_id in _DOMAIN_FAMILY_BY_ID_V1,
        "display_name": _compact_text(profile.get("display_name"), family_id.replace("_", " ").title()),
        "description": _compact_text(profile.get("description"), "Metadata-only domain family profile."),
        "signal_family_detection_cues": list(profile.get("signal_family_detection_cues", ())),
        "likely_source_classes": list(profile.get("likely_source_classes", ())),
        "required_disconfirmation_classes": list(profile.get("required_disconfirmation_classes", ())),
        "blocked_claims": ["blocked_public_claims", "blocked_final_answer_claims", "blocked_verified_claims"],
        "operator_review_required": bool(profile.get("operator_review_required", True)),
    }


def _normalize_signal_item(item: Any, index: int) -> dict[str, Any]:
    if isinstance(item, str):
        return {
            "title_or_descriptor": item,
            "source_ref": f"item_{index:02d}",
            "domain_family": "unknown_domain",
        }
    if not isinstance(item, Mapping):
        return {"title_or_descriptor": _compact_text(item, "unknown"), "source_ref": f"item_{index:02d}", "domain_family": "unknown_domain"}
    return {
        "title_or_descriptor": _compact_text(
            item.get("title_or_descriptor")
            or item.get("title")
            or item.get("descriptor")
            or item.get("name")
            or item.get("summary")
            or item.get("description"),
            f"signal_{index:02d}",
        ),
        "source_ref": _compact_text(item.get("source_ref") or item.get("url") or item.get("reference") or item.get("artifact_ref"), f"item_{index:02d}"),
        "domain_family": _safe_domain_family(item.get("domain_family") or item.get("domain") or item.get("family")),
        "source_class_label": _compact_text(item.get("source_class_label") or item.get("source_class_hint") or item.get("source_class"), "unknown_source"),
        "authority_guess": _compact_text(item.get("authority_guess"), "unknown_authority"),
        "evidence_role_guess": _compact_text(item.get("evidence_role_guess"), "candidate_signal"),
        "novelty_label": _compact_text(item.get("novelty_label"), "unknown"),
        "risk_label": _compact_text(item.get("risk_label"), "unknown"),
        "query_descriptor": _compact_text(item.get("query_descriptor") or item.get("query"), ""),
        "summary": _compact_text(item.get("summary") or item.get("description") or item.get("note"), ""),
        "signal_hint": _compact_text(item.get("signal_hint") or item.get("signal_type") or item.get("family_hint"), ""),
    }


def _find_source_class_label(item: Mapping[str, Any]) -> str:
    for key in ("source_class_label", "source_class_hint", "source_class"):
        value = _compact_text(item.get(key))
        if value:
            return value
    return "unknown_source"


def _item_blob(item: Mapping[str, Any]) -> str:
    return _safe_text_source_summary(item)


def _match_markers(blob: str) -> dict[str, list[str]]:
    matches: dict[str, list[str]] = {}
    marker_groups = {
        "unfinished_work_signal": ("unfinished work", "work unfinished", "unfinished"),
        "technology_blocked_signal": ("technology blocked", "technical blocker", "blocked by technology", "blocked by tech"),
        "dormant_direction_signal": ("dormant direction", "parked direction", "revisit later", "sleeping direction"),
        "ontology_insufficient_signal": ("ontology insufficient", "insufficient ontology", "missing ontology", "ontology gap"),
        "open_problem_signal": _OPEN_PROBLEM_MARKERS_V1,
        "unsolved_theory_signal": ("unsolved", "open problem", "not solved"),
        "unresolved_mechanism_signal": ("unresolved", "unknown mechanism", "not fully understood"),
        "not_fully_understood_signal": ("not fully understood",),
        "unknown_mechanism_signal": ("unknown mechanism",),
        "requires_further_research_signal": ("requires further research", "further research"),
        "formal_unsolved_problem_signal": ("formal open question", "theorem gap", "axiom gap", "not settled", "formal open problem"),
        "future_work_signal": ("future work", "future research"),
        "future_workforce_impact_signal": ("future workforce", "workforce impact", "job impact", "labor impact", "employment impact"),
        "limitation_signal": ("limitation", "limited by"),
        "failed_model_signal": ("failed to explain", "model failure"),
        "unexplained_anomaly_signal": ("anomaly", "unexpected"),
        "anomaly_signal": ("anomaly", "unexpected"),
        "contradiction_signal": ("contradiction", "contradictory"),
        "disconfirmation_required": ("disconfirm", "falsification criterion", "missing evidence", "promotion blockers"),
        "underexplored_dataset_signal": ("underexplored dataset", "dataset gap"),
        "missing_measurement_signal": ("missing measurement", "measurement gap"),
        "measurement_benchmark_gap_signal": ("measurement gap", "benchmark gap", "benchmark incomplete", "calibration gap"),
        "replication_gap_signal": ("replication gap", "replication needed"),
        "incomplete_benchmark_signal": ("benchmark incomplete",),
        "survey_gap_signal": ("survey gap",),
        "calibration_gap_signal": ("calibration gap",),
        "cross_domain_transfer_signal": ("cross-domain", "transfer", "shared constraint", "same pattern"),
        "domain_convergence_signal": ("domain convergence", "convergence", "shared constraint"),
        "adjacent_science_analogy_signal": ("analogy", "similar structure"),
        "time_revisit_signal": ("time revisit", "revisit later", "schedule revisit", "time-to-revisit"),
        "language_protocol_discovery_signal": ("language protocol", "communication protocol", "semantic drift", "protocol design"),
        "artifact_generation_candidate": ("artifact", "plan", "map", "module", "concept map", "protocol map", "future work map", "risk map", "bridge map"),
        "extraordinary_claim_signal": ("extraordinary claim", "remarkable claim", "extraordinary"),
        "fringe_edge_science_signal": ("fringe", "edge science", "speculative", "unverified"),
        "blocked_or_unsafe_signal": ("unsafe", "private", "hidden", "protected", "secret", "system prompt", "developer message", "api key", "token"),
        "weak_signal": _WEAK_SIGNAL_MARKERS_V1,
    }
    for signal_type, markers in marker_groups.items():
        hits = [marker for marker in markers if marker in blob]
        if hits:
            matches[signal_type] = hits
    return matches


def _confidence_for_signal(signal_type: str, hits: list[str]) -> str:
    if signal_type in {"weak_signal", "unknown_signal"}:
        return "low"
    if signal_type in {"cross_domain_transfer_signal", "adjacent_science_analogy_signal"}:
        return "medium" if hits else "low"
    return "medium" if hits else "low"


def _next_step_for_signal(signal_type: str) -> str:
    if signal_type in {"blocked_or_unsafe_signal"}:
        return "route_to_blocked_by_safety"
    if signal_type in {"unfinished_work_signal", "dormant_direction_signal", "technology_blocked_signal"}:
        return "route_to_operator_review"
    if signal_type in {"time_revisit_signal"}:
        return "route_to_time_revisit_review"
    if signal_type in {"domain_convergence_signal"}:
        return "route_to_domain_convergence_review"
    if signal_type in {"future_workforce_impact_signal"}:
        return "route_to_future_workforce_impact_review"
    if signal_type in {"language_protocol_discovery_signal"}:
        return "route_to_language_protocol_review"
    if signal_type in {"artifact_generation_candidate"}:
        return "route_to_artifact_proposal_plan"
    if signal_type in {"disconfirmation_required"}:
        return "route_to_disconfirming_review"
    if signal_type in {"ontology_insufficient_signal"}:
        return "route_to_ontology_expansion_request"
    if signal_type in {"extraordinary_claim_signal", "fringe_edge_science_signal"}:
        return "route_to_extraordinary_claim_quarantine"
    if signal_type in {
        "measurement_benchmark_gap_signal",
        "underexplored_dataset_signal",
        "missing_measurement_signal",
        "replication_gap_signal",
        "incomplete_benchmark_signal",
        "survey_gap_signal",
        "calibration_gap_signal",
    }:
        return "route_to_source_selection_plan"
    if signal_type in {"cross_domain_transfer_signal", "adjacent_science_analogy_signal"}:
        return "route_to_cross_domain_scout"
    if signal_type in {
        "open_problem_signal",
        "unsolved_theory_signal",
        "unresolved_mechanism_signal",
        "unexplained_anomaly_signal",
        "anomaly_signal",
        "future_work_signal",
        "limitation_signal",
        "failed_model_signal",
        "contradiction_signal",
        "formal_unsolved_problem_signal",
        "not_fully_understood_signal",
        "unknown_mechanism_signal",
        "requires_further_research_signal",
    }:
        return "route_to_operator_review"
    if signal_type in {"weak_signal", "unknown_signal"}:
        return "route_to_archive_low_value_signal"
    return "route_to_operator_review"


def _source_classes_needed_for_signal_types(signal_types: Iterable[str]) -> list[str]:
    needed = {
        "public_research_paper",
        "survey_paper",
        "review_paper",
        "benchmark_paper",
        "dataset_record",
        "official_standard",
        "government_agency_report",
        "patent",
        "thesis_dissertation",
        "lab_university_artifact",
        "conference_workshop_artifact",
        "negative_result_paper",
        "replication_study",
        "historical_archive",
        "technical_report",
        "preprint",
        "vendor_technical_documentation",
        "code_repository_as_implementation_reference",
        "forum_blog_as_weak_signal",
        "unknown_authority",
    }
    if any(sig in {"cross_domain_transfer_signal", "adjacent_science_analogy_signal", "domain_convergence_signal"} for sig in signal_types):
        needed.update({"github_repository", "owner_supplied_observation"})
    if any(sig in {"underexplored_dataset_signal", "missing_measurement_signal", "measurement_benchmark_gap_signal", "replication_gap_signal", "incomplete_benchmark_signal", "survey_gap_signal", "calibration_gap_signal"} for sig in signal_types):
        needed.update({"dataset_record", "benchmark_paper", "replication_study"})
    if any(sig in {"language_protocol_discovery_signal"} for sig in signal_types):
        needed.update({"official_standard", "technical_report", "vendor_technical_documentation"})
    if any(sig in {"future_workforce_impact_signal"} for sig in signal_types):
        needed.update({"government_agency_report", "survey_paper", "technical_report"})
    return sorted(needed)


def _candidate_denied_authority_flags() -> dict[str, bool]:
    key_map = {
        "discovery_claim_authority": "detection_claim_authority",
        "proof_claim_authority": "support_claim_authority",
    }
    flags = {key_map.get(flag, flag): False for flag in _AUTHORITY_FALSE_FLAGS_V1}
    flags.update(
        {
            "all_authority_flags_false": True,
            "metadata_only": True,
            "evidence_status": "metadata_only_unverified",
            "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        }
    )
    return flags


def _artifact_suggestions_for_signal(signal_type: str, domain_family: str) -> tuple[str, ...]:
    if signal_type in {"artifact_generation_candidate"}:
        return (
            "source_selection_plan",
            "evidence_disconfirmation_plan",
            "experiment_plan",
            "simulation_plan",
            "dataset_to_build_plan",
            "benchmark_to_build_plan",
            "operator_review_card",
            "learning_module",
            "concept_map",
            "protocol_map",
            "future_work_map",
            "risk_map",
            "cross_domain_bridge_map",
        )
    if signal_type in {"language_protocol_discovery_signal"}:
        return ("protocol_map", "concept_map", "operator_review_card")
    if signal_type in {"future_workforce_impact_signal"}:
        return ("future_work_map", "risk_map", "operator_review_card")
    if signal_type in {"cross_domain_transfer_signal", "domain_convergence_signal", "adjacent_science_analogy_signal"}:
        return ("cross_domain_bridge_map", "concept_map", "operator_review_card")
    if signal_type in {"disconfirmation_required"}:
        return ("evidence_disconfirmation_plan", "operator_review_card")
    if signal_type in {"ontology_insufficient_signal"}:
        return ("source_selection_plan", "operator_review_card")
    return ()


def _disconfirmation_fields_for_signal(signal_type: str) -> tuple[str, ...]:
    if signal_type in {
        "unfinished_work_signal",
        "technology_blocked_signal",
        "dormant_direction_signal",
        "ontology_insufficient_signal",
        "open_problem_signal",
        "unsolved_theory_signal",
        "unresolved_mechanism_signal",
        "formal_unsolved_problem_signal",
        "unexplained_anomaly_signal",
        "failed_model_signal",
        "contradiction_signal",
        "measurement_benchmark_gap_signal",
        "replication_gap_signal",
        "incomplete_benchmark_signal",
        "survey_gap_signal",
        "calibration_gap_signal",
        "disconfirmation_required",
        "extraordinary_claim_signal",
        "fringe_edge_science_signal",
    }:
        return required_unfinished_research_disconfirmation_fields_v1()
    return ()


def _candidate_from_item(signal_type: str, item: Mapping[str, Any], hits: list[str], domain_family: str, index: int) -> dict[str, Any]:
    source_ref = _compact_text(item.get("source_ref"), f"item_{index:02d}")
    title = _compact_text(item.get("title_or_descriptor"), f"signal_{index:02d}")
    trigger_terms = list(dict.fromkeys(hits or [signal_type.replace("_signal", "")]))
    family_profile = _domain_family_profile(domain_family)
    output_signal_type = _SAFE_SIGNAL_TYPE_OUTPUT_ALIASES_V1.get(signal_type, signal_type)
    candidate = {
        "signal_id": _stable_id(
            f"cdopd_{output_signal_type}",
            {"signal_type": output_signal_type, "source_ref": source_ref, "domain_family": family_profile["domain_family_id"], "title_or_descriptor": title, "trigger_terms": trigger_terms},
        ),
        "signal_type": output_signal_type,
        "output_signal_type": output_signal_type,
        "domain_family": family_profile["domain_family_id"],
        "domain_family_known": family_profile["domain_family_known"],
        "domain_family_display_name": family_profile["display_name"],
        "domain_family_description": family_profile["description"],
        "domain_family_signal_cues": family_profile["signal_family_detection_cues"],
        "domain_family_likely_source_classes": family_profile["likely_source_classes"],
        "domain_family_required_disconfirmation_classes": family_profile["required_disconfirmation_classes"],
        "domain_family_blocked_claims": family_profile["blocked_claims"],
        "source_ref": source_ref,
        "title_or_descriptor": title,
        "trigger_terms": trigger_terms,
        "why_it_matters": _why_it_matters(signal_type, family_profile["domain_family_id"]),
        "evidence_status": "metadata_only_unverified",
        "confidence_label": _confidence_for_signal(signal_type, trigger_terms),
        "operator_review_required": True,
        "recommended_next_step": _next_step_for_signal(signal_type),
        "artifact_type_suggestions": list(_artifact_suggestions_for_signal(signal_type, family_profile["domain_family_id"])),
        "required_disconfirmation_fields": list(_disconfirmation_fields_for_signal(signal_type)),
        "denied_authority_flags": _candidate_denied_authority_flags(),
    }
    return candidate


def _why_it_matters(signal_type: str, domain_family: str) -> str:
    phrases = {
        "unfinished_work_signal": f"Signals unfinished work in {domain_family} that remains metadata-only.",
        "technology_blocked_signal": f"Signals a technology blocker in {domain_family} that needs review.",
        "dormant_direction_signal": f"Signals a dormant direction in {domain_family} that should stay parked or revisited later.",
        "ontology_insufficient_signal": f"Signals that the current ontology for {domain_family} is insufficient for safe promotion.",
        "open_problem_signal": f"Signals an open problem in {domain_family} that needs owner review before any later routing.",
        "unsolved_theory_signal": f"Suggests a theory-level gap in {domain_family}.",
        "unresolved_mechanism_signal": f"Suggests a mechanism in {domain_family} that remains unresolved.",
        "unexplained_anomaly_signal": f"Highlights an unexplained anomaly in {domain_family} metadata.",
        "future_work_signal": f"Flags future-work language in {domain_family} metadata.",
        "limitation_signal": f"Flags a stated limitation in {domain_family} metadata.",
        "failed_model_signal": f"Highlights a model failure pattern in {domain_family} metadata.",
        "contradiction_signal": f"Highlights a contradiction that should be pressure-tested before later use.",
        "underexplored_dataset_signal": f"Suggests the data surface for {domain_family} is underexplored.",
        "missing_measurement_signal": f"Suggests a missing-measurement gap in {domain_family}.",
        "measurement_benchmark_gap_signal": f"Suggests a measurement or benchmark gap in {domain_family}.",
        "formal_unsolved_problem_signal": f"Marks a formal open question in {domain_family} metadata.",
        "extraordinary_claim_signal": f"Marks an extraordinary claim in {domain_family}; it must stay quarantined until disconfirmed.",
        "fringe_edge_science_signal": f"Marks a fringe-edge science signal in {domain_family}; it must stay quarantined until reviewed.",
        "time_revisit_signal": f"Marks a direction in {domain_family} that should be revisited later rather than promoted now.",
        "domain_convergence_signal": f"Marks a possible convergence across domains in {domain_family}.",
        "future_workforce_impact_signal": f"Marks a workforce-impact hypothesis in {domain_family}; this must remain hypothesis-only.",
        "language_protocol_discovery_signal": f"Marks a language or protocol candidate in {domain_family}; keep it structure-only.",
        "artifact_generation_candidate": f"Marks an artifact proposal candidate in {domain_family}; do not generate artifacts here.",
        "disconfirmation_required": f"Marks a record in {domain_family} that explicitly requires disconfirmation-first handling.",
        "ontology_insufficient_signal": f"Marks an ontology-insufficient record in {domain_family}.",
        "weak_signal": f"Only a weak signal is visible in {domain_family}; this may be archival rather than candidate-worthy.",
        "replication_gap_signal": f"Suggests a replication gap in {domain_family}.",
        "incomplete_benchmark_signal": f"Suggests the benchmark picture in {domain_family} is incomplete.",
        "survey_gap_signal": f"Suggests the survey layer in {domain_family} is incomplete.",
        "calibration_gap_signal": f"Suggests calibration work is missing for {domain_family}.",
        "cross_domain_transfer_signal": f"Suggests a transfer opportunity between {domain_family} and another domain.",
        "adjacent_science_analogy_signal": f"Suggests a cross-domain analogy may be worth owner review.",
        "not_fully_understood_signal": f"Marks an area in {domain_family} that is not fully understood.",
        "unknown_mechanism_signal": f"Marks an unknown mechanism in {domain_family} metadata.",
        "requires_further_research_signal": f"Marks a clear need for further research in {domain_family}.",
        "blocked_or_unsafe_signal": f"Marks a blocked or unsafe signal that should not advance.",
        "unknown_signal": f"Only an unknown signal is visible for {domain_family}.",
    }
    return phrases.get(signal_type, f"Metadata-only signal in {domain_family} requires owner review.")


def _candidate_lists() -> dict[str, list[dict[str, Any]]]:
    return {signal_type: [] for signal_type in _ALLOWED_SIGNAL_TYPES_V1}


def _build_candidate_buckets(packet: Mapping[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[str], list[str]]:
    buckets = _candidate_lists()
    all_candidates: list[dict[str, Any]] = []
    source_classes_needed: set[str] = set()
    signal_types_seen: list[str] = []
    for index, raw_item in enumerate(packet.get("input_signal_items", []), 1):
        item = _normalize_signal_item(raw_item, index)
        blob = _item_blob(item)
        if _contains_any_marker(blob, _PRIVATE_HIDDEN_PROTECTED_MARKERS_V1):
            signal_type = "blocked_or_unsafe_signal"
            hits = [marker for marker in _PRIVATE_HIDDEN_PROTECTED_MARKERS_V1 if marker in blob]
        elif _contains_any_marker(blob, _FORBIDDEN_CLAIM_MARKERS_V1):
            signal_type = "blocked_or_unsafe_signal"
            hits = [marker for marker in _FORBIDDEN_CLAIM_MARKERS_V1 if marker in blob]
        else:
            matches = _match_markers(blob)
            if matches:
                # Preserve a stable order of the most relevant candidate types.
                ordered = [sig for sig in _ALLOWED_SIGNAL_TYPES_V1 if sig in matches and sig != "blocked_or_unsafe_signal"]
                for signal_type in ordered:
                    candidate = _candidate_from_item(signal_type, item, matches[signal_type], item["domain_family"], index)
                    buckets[signal_type].append(candidate)
                    all_candidates.append(candidate)
                    signal_types_seen.append(signal_type)
                source_classes_needed.update(_source_classes_needed_for_signal_types(ordered))
                continue
            signal_type = "unknown_signal"
            hits = ["unknown_signal"]
        candidate = _candidate_from_item(signal_type, item, hits, item["domain_family"], index)
        buckets[signal_type].append(candidate)
        all_candidates.append(candidate)
        signal_types_seen.append(signal_type)
        source_classes_needed.update(_source_classes_needed_for_signal_types([signal_type]))
    if not all_candidates:
        fallback = {
            "title_or_descriptor": "empty_input",
            "source_ref": "input_empty",
            "domain_family": "unknown_domain",
        }
        candidate = _candidate_from_item("unknown_signal", fallback, ["empty_input"], "unknown_domain", 1)
        buckets["unknown_signal"].append(candidate)
        all_candidates.append(candidate)
        signal_types_seen.append("unknown_signal")
        source_classes_needed.update(_source_classes_needed_for_signal_types(["unknown_signal"]))
    return buckets, all_candidates, sorted(source_classes_needed), signal_types_seen


def _build_cross_domain_bridges(domain_families: list[str], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique = [family for family in dict.fromkeys(domain_families) if family]
    if len(unique) < 2:
        return []
    relation = "shared_constraint_model"
    if any(candidate["signal_type"] in {"cross_domain_transfer_signal", "adjacent_science_analogy_signal"} for candidate in candidates):
        relation = "shared_measurement_limitation"
    bridges: list[dict[str, Any]] = []
    for i, left in enumerate(unique[:-1]):
        for right in unique[i + 1 :]:
            bridge = {
                "bridge_id": _stable_id("cdopd_bridge", {"left": left, "right": right, "relation": relation}),
                "domain_family_pair": [left, right],
                "bridge_type": "cross_domain_transfer_candidate" if relation != "shared_measurement_limitation" else "measurement_gap_bridge",
                "relation_type": relation,
                "why_it_matters": f"Metadata-only bridge between {left} and {right} remains unresolved and should be owner reviewed.",
                "operator_review_required": True,
                "denied_authority_flags": _candidate_denied_authority_flags(),
            }
            bridges.append(bridge)
    return bridges


def _pressure_test_questions(domain_families: list[str], signal_types: list[str]) -> list[str]:
    questions = []
    if any(sig in {"open_problem_signal", "unsolved_theory_signal", "unresolved_mechanism_signal", "formal_unsolved_problem_signal"} for sig in signal_types):
        questions.append("What is the unresolved mechanism and what would falsify the current interpretation?")
    if any(sig in {"future_work_signal", "limitation_signal", "future_workforce_impact_signal"} for sig in signal_types):
        questions.append("Which limitation, future-work note, or workforce-impact hypothesis most strongly constrains the interpretation?")
    if any(sig in {"contradiction_signal", "unexplained_anomaly_signal", "failed_model_signal", "anomaly_signal"} for sig in signal_types):
        questions.append("What contradictory, anomalous, or failed-model evidence would disconfirm the current signal?")
    if any(sig in {"missing_measurement_signal", "measurement_benchmark_gap_signal", "underexplored_dataset_signal", "replication_gap_signal", "incomplete_benchmark_signal", "survey_gap_signal", "calibration_gap_signal"} for sig in signal_types):
        questions.append("What measurement, dataset, benchmark, survey, or calibration gap is most important to close first?")
    if any(sig in {"cross_domain_transfer_signal", "domain_convergence_signal", "adjacent_science_analogy_signal"} for sig in signal_types):
        questions.append("What cross-domain analogy is real versus merely superficially similar?")
    if any(sig in {"language_protocol_discovery_signal"} for sig in signal_types):
        questions.append("What protocol or language claim is strictly bounded by the metadata? ")
    if any(sig in {"artifact_generation_candidate"} for sig in signal_types):
        questions.append("Which future artifact types are only proposals, and what blockers keep them from being generated now?")
    if any(sig in {"disconfirmation_required", "extraordinary_claim_signal", "fringe_edge_science_signal"} for sig in signal_types):
        questions.append("What disconfirming evidence or independent confirmation is required before promotion?")
    if any(sig in {"ontology_insufficient_signal"} for sig in signal_types):
        questions.append("Which missing ontology terms block safe classification, and what operator review is needed?")
    if not questions:
        questions.append("What additional safe metadata would make this signal materially more specific?")
    return questions


def _probe_suggestions(domain_families: list[str], signal_types: list[str]) -> list[str]:
    suggestions = []
    if any(sig in {"open_problem_signal", "unresolved_mechanism_signal", "unknown_mechanism_signal", "formal_unsolved_problem_signal"} for sig in signal_types):
        suggestions.append("Collect a bounded owner summary of the unresolved mechanism and its constraints.")
    if any(sig in {"missing_measurement_signal", "measurement_benchmark_gap_signal", "underexplored_dataset_signal", "replication_gap_signal"} for sig in signal_types):
        suggestions.append("Prepare a metadata-only source-selection plan for datasets, benchmarks, or measurements.")
    if any(sig in {"cross_domain_transfer_signal", "domain_convergence_signal", "adjacent_science_analogy_signal"} for sig in signal_types):
        suggestions.append("Prepare a bounded cross-domain review packet with explicit analogy limits.")
    if any(sig in {"language_protocol_discovery_signal"} for sig in signal_types):
        suggestions.append("Keep the protocol candidate as structure-only metadata and block universal-language claims.")
    if any(sig in {"artifact_generation_candidate"} for sig in signal_types):
        suggestions.append("Keep artifact generation as proposal-only metadata and do not generate artifacts here.")
    if any(sig in {"future_workforce_impact_signal"} for sig in signal_types):
        suggestions.append("Treat workforce-impact language as hypothesis-only metadata and block certainty claims.")
    if any(sig in {"disconfirmation_required", "extraordinary_claim_signal", "fringe_edge_science_signal"} for sig in signal_types):
        suggestions.append("Require disconfirmation-first handling or independent confirmation before promotion.")
    if any(sig in {"ontology_insufficient_signal"} for sig in signal_types):
        suggestions.append("Hold for operator review because the current ontology is not sufficient for safe promotion.")
    if any(sig in {"weak_signal", "unknown_signal"} for sig in signal_types):
        suggestions.append("Consider archiving or repairing the weak signal before any later routing.")
    if not suggestions:
        suggestions.append("Prepare a small, metadata-only pressure-test packet with owner review.")
    return suggestions


def _missing_evidence_map(candidates: list[dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for candidate in candidates:
        key = candidate["signal_type"]
        if key in {
            "open_problem_signal",
            "unsolved_theory_signal",
            "unresolved_mechanism_signal",
            "formal_unsolved_problem_signal",
            "requires_further_research_signal",
            "unknown_mechanism_signal",
            "not_fully_understood_signal",
            "ontology_insufficient_signal",
        }:
            result.setdefault(key, []).append("Missing mechanism-level explanation or bounded owner summary")
        elif key in {
            "missing_measurement_signal",
            "measurement_benchmark_gap_signal",
            "underexplored_dataset_signal",
            "replication_gap_signal",
            "incomplete_benchmark_signal",
            "survey_gap_signal",
            "calibration_gap_signal",
        }:
            result.setdefault(key, []).append("Missing measurement, dataset, benchmark, survey, or calibration coverage")
        elif key in {"cross_domain_transfer_signal", "domain_convergence_signal", "adjacent_science_analogy_signal"}:
            result.setdefault(key, []).append("Missing cross-domain validation or explicit analogy limits")
        elif key in {"language_protocol_discovery_signal"}:
            result.setdefault(key, []).append("Missing protocol constraints or bounded language claim")
        elif key in {"artifact_generation_candidate"}:
            result.setdefault(key, []).append("Missing proposal blockers and future artifact constraints")
        elif key in {"future_workforce_impact_signal"}:
            result.setdefault(key, []).append("Missing evidence for a workforce-impact hypothesis")
    return result


def _disconfirming_evidence_map(candidates: list[dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for candidate in candidates:
        key = candidate["signal_type"]
        if key in {"contradiction_signal", "unexplained_anomaly_signal", "failed_model_signal", "anomaly_signal"}:
            result.setdefault(key, []).append("A bounded counterexample or failed-model trace would weaken this signal")
        elif key in {"open_problem_signal", "unsolved_theory_signal", "unresolved_mechanism_signal", "formal_unsolved_problem_signal"}:
            result.setdefault(key, []).append("A concrete mechanism explanation would reduce the open-problem posture")
        elif key in {"disconfirmation_required", "extraordinary_claim_signal", "fringe_edge_science_signal"}:
            result.setdefault(key, []).append("Independent confirmation or falsification is required before promotion")
        elif key in {"weak_signal", "unknown_signal"}:
            result.setdefault(key, []).append("A stronger bounded metadata signal would be needed before promotion")
    return result


def _recommended_route(signal_types: list[str], candidate_count: int, source_classes_needed: list[str]) -> str:
    if any(sig == "blocked_or_unsafe_signal" for sig in signal_types):
        return "blocked_by_safety"
    if any(sig in {"extraordinary_claim_signal", "fringe_edge_science_signal"} for sig in signal_types):
        return "route_to_extraordinary_claim_quarantine"
    if any(sig in {"ontology_insufficient_signal"} for sig in signal_types):
        return "route_to_ontology_expansion_request"
    if any(sig in {"language_protocol_discovery_signal"} for sig in signal_types):
        return "route_to_language_protocol_review"
    if any(sig in {"artifact_generation_candidate"} for sig in signal_types):
        return "route_to_artifact_proposal_plan"
    if any(sig in {"future_workforce_impact_signal"} for sig in signal_types):
        return "route_to_future_workforce_impact_review"
    if any(sig in {"domain_convergence_signal"} for sig in signal_types):
        return "route_to_domain_convergence_review"
    if any(sig in {"time_revisit_signal"} for sig in signal_types):
        return "route_to_time_revisit_review"
    if any(sig in {"disconfirmation_required"} for sig in signal_types):
        return "route_to_disconfirming_review"
    if any(sig in {"cross_domain_transfer_signal", "adjacent_science_analogy_signal"} for sig in signal_types):
        return "route_to_cross_domain_scout"
    if any(sig in {"measurement_benchmark_gap_signal", "underexplored_dataset_signal", "missing_measurement_signal", "replication_gap_signal", "incomplete_benchmark_signal", "survey_gap_signal", "calibration_gap_signal"} for sig in signal_types):
        return "route_to_source_selection_plan"
    if any(sig in {"open_problem_signal", "unsolved_theory_signal", "unresolved_mechanism_signal", "unexplained_anomaly_signal", "anomaly_signal", "future_work_signal", "limitation_signal", "failed_model_signal", "contradiction_signal", "formal_unsolved_problem_signal", "not_fully_understood_signal", "unknown_mechanism_signal", "requires_further_research_signal"} for sig in signal_types):
        if len(source_classes_needed) >= 3 and candidate_count >= 2:
            return "route_to_operator_review"
        return "route_to_operator_review"
    if any(sig in {"weak_signal", "unknown_signal"} for sig in signal_types):
        return "route_to_archive_low_value_signal"
    return "route_to_operator_review"


def _candidate_lists_summary(buckets: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return {key: len(value) for key, value in buckets.items() if value}


def validate_cross_domain_open_problem_discovery_scout_request_v1(request: Any) -> dict[str, Any]:
    issues = []
    if not isinstance(request, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["request_must_be_a_dict"],
            "validation_posture": "blocked",
            "summary_text": "Blocked cross-domain open-problem scout request.",
        }
    if _contains_forbidden_keys(request):
        issues.append("forbidden_content_key_present")
    if _contains_forbidden_text(request):
        issues.append("forbidden_claim_language_present")
    if _contains_private_hidden_protected_marker(request):
        issues.append("unsafe_private_hidden_protected_marker")
    if _contains_unsafe_url_or_domain(request):
        issues.append("unsafe_domain_or_url")
    if _contains_any_true_flag(request):
        issues.append("unsafe_authority_flag_true")
    if _first_non_json_safe_path(request) is not None:
        issues.append("non_json_safe_input")
    scout_id = _compact_text(request.get("scout_id"))
    if not scout_id:
        issues.append("missing_scout_id")
    domain_families = _normalize_text_list(request.get("domain_families"))
    if not domain_families:
        issues.append("missing_domain_families")
    input_signal_items = request.get("input_signal_items")
    if not isinstance(input_signal_items, list) or not input_signal_items:
        issues.append("missing_input_signal_items")
    search_governance_mode = _compact_text(request.get("search_governance_mode"))
    if search_governance_mode not in _ALLOWED_SEARCH_GOVERNANCE_MODES_V1:
        issues.append("invalid_search_governance_mode")
    operator_review_need = _compact_text(request.get("operator_review_need"))
    if not operator_review_need:
        issues.append("missing_operator_review_need")
    if request.get("signal_type") is not None and _compact_text(request.get("signal_type")) not in _ALLOWED_SIGNAL_TYPES_V1:
        issues.append("invalid_signal_type")
    if request.get("next_safe_step") is not None and _compact_text(request.get("next_safe_step")) not in _ALLOWED_NEXT_STEPS_V1:
        issues.append("invalid_next_step")
    if any(marker in search_governance_mode.lower() for marker in _PRIVATE_HIDDEN_PROTECTED_MARKERS_V1):
        issues.append("unsafe_private_hidden_protected_marker")
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": not issues,
        "blocked": bool(issues),
        "blocked_labels": list(dict.fromkeys(issues)),
        "validation_posture": "valid" if not issues else "blocked",
        "scout_id": scout_id,
        "summary_text": "Valid cross-domain open-problem scout request." if not issues else "Blocked cross-domain open-problem scout request.",
    }


def validate_cross_domain_open_problem_discovery_scout_packet_v1(packet: Any) -> dict[str, Any]:
    issues = []
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["packet_must_be_a_dict"],
            "validation_posture": "blocked",
            "summary_text": "Blocked cross-domain open-problem scout packet.",
        }
    required = (
        "schema_version",
        "scout_id",
        "input_references",
        "domain_families",
        "search_governance_mode",
        "input_signal_items",
        "open_problem_signal_candidates",
        "unresolved_work_signal_candidates",
        "anomaly_signal_candidates",
        "limitation_future_work_candidates",
        "contradiction_candidates",
        "missing_evidence_map",
        "disconfirming_evidence_map",
        "source_classes_needed",
        "recommended_mlcf_route",
        "candidate_cross_domain_bridges",
        "calibration_axes_needed",
        "pressure_test_questions",
        "probe_suggestions",
        "safety_boundary",
        "denied_authority_flags",
        "operator_review_need",
        "next_safe_step",
        "safe_metadata_summary",
        "validation_status",
    )
    for field in required:
        if field not in packet:
            issues.append(f"missing_{field}")
    if issues:
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": issues,
            "validation_posture": "blocked",
            "scout_id": _compact_text(packet.get("scout_id")),
            "summary_text": "Blocked cross-domain open-problem scout packet.",
        }
    if _compact_text(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        issues.append("invalid_schema_version")
    if not _compact_text(packet.get("scout_id")):
        issues.append("missing_scout_id")
    if not isinstance(packet.get("input_references"), list):
        issues.append("input_references_must_be_a_list")
    if not isinstance(packet.get("domain_families"), list) or not packet.get("domain_families"):
        issues.append("domain_families_must_be_a_non_empty_list")
    if _compact_text(packet.get("search_governance_mode")) not in _ALLOWED_SEARCH_GOVERNANCE_MODES_V1:
        issues.append("invalid_search_governance_mode")
    if not isinstance(packet.get("input_signal_items"), list) or not packet.get("input_signal_items"):
        issues.append("missing_input_signal_items")
    if _compact_text(packet.get("operator_review_need")) == "":
        issues.append("missing_operator_review_need")
    if _compact_text(packet.get("next_safe_step")) not in _ALLOWED_NEXT_STEPS_V1:
        issues.append("invalid_next_step")
    for field_name, candidate_list in (
        ("open_problem_signal_candidates", packet.get("open_problem_signal_candidates")),
        ("unresolved_work_signal_candidates", packet.get("unresolved_work_signal_candidates")),
        ("anomaly_signal_candidates", packet.get("anomaly_signal_candidates")),
        ("limitation_future_work_candidates", packet.get("limitation_future_work_candidates")),
        ("contradiction_candidates", packet.get("contradiction_candidates")),
    ):
        if not isinstance(candidate_list, list):
            issues.append(f"{field_name}_must_be_a_list")
            continue
        for candidate in candidate_list:
            if not isinstance(candidate, Mapping):
                issues.append(f"invalid_{field_name[:-1]}")
                continue
            if _compact_text(candidate.get("signal_id")) == "":
                issues.append("missing_signal_id")
            if _compact_text(candidate.get("signal_type")) not in _ALLOWED_SIGNAL_TYPES_V1:
                issues.append("invalid_signal_type")
            if _compact_text(candidate.get("recommended_next_step")) not in _ALLOWED_NEXT_STEPS_V1:
                issues.append("invalid_next_step")
            if _compact_text(candidate.get("evidence_status")) != "metadata_only_unverified":
                issues.append("invalid_evidence_status")
            if not isinstance(candidate.get("trigger_terms"), list):
                issues.append("trigger_terms_must_be_a_list")
            if not isinstance(candidate.get("denied_authority_flags"), Mapping):
                issues.append("invalid_denied_authority_flags")
            elif candidate.get("denied_authority_flags") != _candidate_denied_authority_flags():
                issues.append("invalid_denied_authority_flags")
            if candidate.get("operator_review_required") is not True:
                issues.append("missing_operator_review_need")
    if not isinstance(packet.get("missing_evidence_map"), Mapping):
        issues.append("missing_evidence_map_must_be_a_dict")
    if not isinstance(packet.get("disconfirming_evidence_map"), Mapping):
        issues.append("disconfirming_evidence_map_must_be_a_dict")
    if not isinstance(packet.get("source_classes_needed"), list):
        issues.append("source_classes_needed_must_be_a_list")
    if _compact_text(packet.get("recommended_mlcf_route")) not in _ALLOWED_NEXT_STEPS_V1:
        issues.append("invalid_next_step")
    if not isinstance(packet.get("candidate_cross_domain_bridges"), list):
        issues.append("candidate_cross_domain_bridges_must_be_a_list")
    if not isinstance(packet.get("calibration_axes_needed"), list):
        issues.append("calibration_axes_needed_must_be_a_list")
    if not isinstance(packet.get("pressure_test_questions"), list):
        issues.append("pressure_test_questions_must_be_a_list")
    if not isinstance(packet.get("probe_suggestions"), list):
        issues.append("probe_suggestions_must_be_a_list")
    if not isinstance(packet.get("safety_boundary"), Mapping):
        issues.append("invalid_safety_boundary")
    if packet.get("denied_authority_flags") != _candidate_denied_authority_flags():
        issues.append("invalid_denied_authority_flags")
    if _contains_any_true_flag(packet):
        issues.append("unsafe_authority_flag_true")
    if _contains_forbidden_keys(packet):
        issues.append("forbidden_content_key_present")
    if _contains_forbidden_text(packet):
        issues.append("forbidden_claim_language_present")
    if _contains_private_hidden_protected_marker(packet):
        issues.append("unsafe_private_hidden_protected_marker")
    if _contains_unsafe_url_or_domain(packet):
        issues.append("unsafe_domain_or_url")
    if _first_non_json_safe_path(packet) is not None:
        issues.append("non_json_safe_output")
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": not issues,
        "blocked": bool(issues),
        "blocked_labels": list(dict.fromkeys(issues)),
        "validation_posture": "valid" if not issues else "blocked",
        "scout_id": _compact_text(packet.get("scout_id")),
        "summary_text": "Valid cross-domain open-problem scout packet." if not issues else "Blocked cross-domain open-problem scout packet.",
    }


def _build_safe_metadata_summary(packet: Mapping[str, Any], candidate_count: int, route: str) -> dict[str, Any]:
    return {
        "metadata_only": True,
        "json_safe": True,
        "no_source_access": True,
        "no_source_fetching": True,
        "no_source_ingestion": True,
        "no_evidence_elevation": True,
        "no_claim_elevation": True,
        "no_claims": True,
        "no_runtime_or_public_integration": True,
        "domain_family_count": len(_normalize_text_list(packet.get("domain_families"))),
        "candidate_count": candidate_count,
        "recommended_mlcf_route": route,
    }


def build_cross_domain_open_problem_discovery_scout_packet_v1(payload=None, **overrides):
    request = _merge_payload(payload, **overrides)
    if "domain_families" not in request:
        request["domain_families"] = _normalize_text_list(request.get("domain_family"))
    if "input_signal_items" not in request:
        request["input_signal_items"] = _normalize_mapping_list(request.get("items") or request.get("signals") or request.get("metadata_items"))
    if "input_references" not in request:
        request["input_references"] = _normalize_text_list(request.get("input_references") or request.get("references") or request.get("source_refs"))
    if "search_governance_mode" not in request:
        request["search_governance_mode"] = "metadata_only_owner_review"
    if "operator_review_need" not in request:
        request["operator_review_need"] = "owner review required"
    request_validation = validate_cross_domain_open_problem_discovery_scout_request_v1(request)
    domain_families = _normalize_text_list(request.get("domain_families"))
    input_signal_items = request.get("input_signal_items") if isinstance(request.get("input_signal_items"), list) else []
    normalized_items = [_normalize_signal_item(item, index) for index, item in enumerate(input_signal_items, 1)]
    request_payload = {
        "schema_version": SCHEMA_VERSION_V1,
        "scout_id": _compact_text(request.get("scout_id")) or _stable_id(
            "cdopd_scout",
            {"input_references": request.get("input_references"), "domain_families": domain_families, "signal_count": len(normalized_items)},
        ),
        "input_references": _normalize_text_list(request.get("input_references")),
        "domain_families": domain_families,
        "search_governance_mode": _compact_text(request.get("search_governance_mode"), "metadata_only_owner_review"),
        "input_signal_items": normalized_items,
        "operator_review_need": _compact_text(request.get("operator_review_need"), "owner review required"),
        "safety_boundary": copy.deepcopy(DEFAULT_SAFETY_BOUNDARY_V1),
    }
    buckets, all_candidates, source_classes_needed, signal_types_seen = _build_candidate_buckets(request_payload)
    route = _recommended_route(signal_types_seen, len(all_candidates), source_classes_needed)
    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "scout_id": request_payload["scout_id"],
        "input_references": request_payload["input_references"],
        "domain_families": request_payload["domain_families"],
        "search_governance_mode": request_payload["search_governance_mode"],
        "input_signal_items": request_payload["input_signal_items"],
        "open_problem_signal_candidates": buckets["open_problem_signal"],
        "unfinished_work_candidates": buckets["unfinished_work_signal"],
        "technology_blocked_candidates": buckets["technology_blocked_signal"],
        "dormant_direction_candidates": buckets["dormant_direction_signal"],
        "time_revisit_candidates": buckets["time_revisit_signal"],
        "domain_convergence_candidates": buckets["domain_convergence_signal"],
        "future_workforce_impact_candidates": buckets["future_workforce_impact_signal"],
        "language_protocol_candidates": buckets["language_protocol_discovery_signal"],
        "artifact_generation_candidates": buckets["artifact_generation_candidate"],
        "disconfirmation_required_candidates": buckets["disconfirmation_required"],
        "ontology_insufficient_candidates": buckets["ontology_insufficient_signal"],
        "extraordinary_claim_candidates": buckets["extraordinary_claim_signal"],
        "fringe_edge_science_candidates": buckets["fringe_edge_science_signal"],
        "unresolved_work_signal_candidates": [
            *buckets["open_problem_signal"],
            *buckets["unsolved_theory_signal"],
            *buckets["unresolved_mechanism_signal"],
            *buckets["not_fully_understood_signal"],
            *buckets["unknown_mechanism_signal"],
            *buckets["requires_further_research_signal"],
            *buckets["underexplored_dataset_signal"],
            *buckets["missing_measurement_signal"],
            *buckets["replication_gap_signal"],
            *buckets["incomplete_benchmark_signal"],
            *buckets["survey_gap_signal"],
            *buckets["calibration_gap_signal"],
        ],
        "anomaly_signal_candidates": [
            *buckets["unexplained_anomaly_signal"],
            *buckets["failed_model_signal"],
        ],
        "limitation_future_work_candidates": [
            *buckets["future_work_signal"],
            *buckets["limitation_signal"],
        ],
        "contradiction_candidates": [
            *buckets["contradiction_signal"],
        ],
        "missing_evidence_map": _missing_evidence_map(all_candidates),
        "disconfirming_evidence_map": _disconfirming_evidence_map(all_candidates),
        "source_classes_needed": source_classes_needed,
        "recommended_mlcf_route": route,
        "candidate_cross_domain_bridges": _build_cross_domain_bridges(domain_families, all_candidates),
        "calibration_axes_needed": [
            "mechanism_explanation",
            "measurement_completeness",
            "replication_strength",
            "benchmark_coverage",
            "cross_domain_transfer_limits",
        ],
        "pressure_test_questions": _pressure_test_questions(domain_families, signal_types_seen),
        "probe_suggestions": _probe_suggestions(domain_families, signal_types_seen),
        "safety_boundary": copy.deepcopy(DEFAULT_SAFETY_BOUNDARY_V1),
        "denied_authority_flags": _candidate_denied_authority_flags(),
        "operator_review_need": _compact_text(request.get("operator_review_need"), "owner review required"),
        "next_safe_step": route,
        "safe_metadata_summary": _build_safe_metadata_summary(request_payload, len(all_candidates), route),
    }
    packet = _sanitize_forbidden_output(packet)
    packet["validation_status"] = {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
        "validation_posture": "valid",
        "scout_id": packet["scout_id"],
        "summary_text": "Valid cross-domain open-problem scout packet.",
    }
    packet["validation_status"] = validate_cross_domain_open_problem_discovery_scout_packet_v1(packet)
    return to_cross_domain_open_problem_discovery_scout_json_safe_v1(packet)


def summarize_cross_domain_open_problem_discovery_scout_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_cross_domain_open_problem_discovery_scout_packet_v1(packet)
    packet_map = packet if isinstance(packet, Mapping) else {}
    candidate_total = 0
    for field in (
        "open_problem_signal_candidates",
        "unresolved_work_signal_candidates",
        "anomaly_signal_candidates",
        "limitation_future_work_candidates",
        "contradiction_candidates",
    ):
        value = packet_map.get(field)
        if isinstance(value, list):
            candidate_total += len(value)
    summary_text = (
        f"Scout { _compact_text(packet_map.get('scout_id')) or 'unassigned' }: "
        f"{len(_normalize_text_list(packet_map.get('domain_families')))} domain families, "
        f"{candidate_total} signal candidates, route={_compact_text(packet_map.get('recommended_mlcf_route'), 'blocked_by_safety')}."
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "scout_id": _compact_text(packet_map.get("scout_id")),
        "domain_family_count": len(_normalize_text_list(packet_map.get("domain_families"))),
        "signal_candidate_count": candidate_total,
        "recommended_mlcf_route": _compact_text(packet_map.get("recommended_mlcf_route"), "blocked_by_safety"),
        "next_safe_step": _compact_text(packet_map.get("next_safe_step"), "blocked_by_safety"),
        "validation_posture": validation.get("validation_posture", "blocked"),
        "summary_text": summary_text[:240],
    }


def to_cross_domain_open_problem_discovery_scout_json_safe_v1(packet: Any) -> Any:
    return _json_safe(copy.deepcopy(packet))


def build_initial_cross_domain_open_problem_discovery_scout_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    examples.append(
        build_cross_domain_open_problem_discovery_scout_packet_v1(
            {
                "scout_id": "cross_domain_open_problem_scout_example_a",
                "domain_families": ["physics", "rf_signal", "materials", "cognitive_science"],
                "input_references": [
                    "docs/example_cross_domain_owner_summary_a.md",
                    "docs/example_cross_domain_domain_summary_a.md",
                ],
                "search_governance_mode": "metadata_only_owner_review",
                "operator_review_need": "owner review required before later cross-domain routing",
                "input_signal_items": [
                    {
                        "title_or_descriptor": "RF sensing mechanism remains not fully understood",
                        "summary": "Future work notes an unresolved mechanism, an unexpected anomaly, and a measurement limitation.",
                        "domain_family": "rf_signal",
                        "source_ref": "owner_summary_rf_001",
                        "source_class_label": "owner_supplied_observation",
                        "authority_guess": "owner_context",
                        "evidence_role_guess": "domain_context",
                    },
                    {
                        "title_or_descriptor": "Materials scattering shows an open problem and replication gap",
                        "summary": "The report says further research is required, a contradiction remains unresolved, and replication remains weak.",
                        "domain_family": "materials",
                        "source_ref": "owner_summary_materials_001",
                        "source_class_label": "owner_supplied_observation",
                        "authority_guess": "owner_context",
                        "evidence_role_guess": "constraint_source",
                    },
                    {
                        "title_or_descriptor": "Cognitive science analogy candidate with shared constraint",
                        "summary": "A cross-domain analogy may transfer but needs explicit limits.",
                        "domain_family": "cognitive_science",
                        "source_ref": "owner_summary_cog_001",
                        "source_class_label": "internal_project_artifact",
                        "authority_guess": "internal_context",
                        "evidence_role_guess": "candidate_signal",
                    },
                ],
            }
        )
    )
    examples.append(
        build_cross_domain_open_problem_discovery_scout_packet_v1(
            {
                "scout_id": "cross_domain_open_problem_scout_example_b",
                "domain_families": ["rf_signal", "materials", "floor_plan"],
                "input_references": ["docs/example_rf_material_floorplan_metadata_b.md"],
                "search_governance_mode": "metadata_only_owner_review",
                "operator_review_need": "owner review required before later source selection",
                "input_signal_items": [
                    {
                        "title_or_descriptor": "Sparse floor-plan map with missing measurement and limited calibration",
                        "summary": "The map is limited by sparse measurements and an incomplete benchmark picture.",
                        "domain_family": "floor_plan",
                        "source_ref": "locator_floorplan_001",
                        "source_class_label": "public_lab_or_university_artifact",
                        "authority_guess": "public_secondary",
                        "evidence_role_guess": "measurement_data",
                    },
                    {
                        "title_or_descriptor": "RF material scattering remains unresolved",
                        "summary": "Future work is needed and the dataset is underexplored.",
                        "domain_family": "rf_signal",
                        "source_ref": "locator_rf_001",
                        "source_class_label": "public_research_paper",
                        "authority_guess": "public_primary",
                        "evidence_role_guess": "prior_art",
                    },
                ],
            }
        )
    )
    examples.append(
        build_cross_domain_open_problem_discovery_scout_packet_v1(
            {
                "scout_id": "cross_domain_open_problem_scout_example_c",
                "domain_families": ["physics"],
                "input_references": ["docs/example_blocked_raw_content_c.md"],
                "search_governance_mode": "metadata_only_owner_review",
                "operator_review_need": "owner review required",
                "input_signal_items": [
                    {
                        "title_or_descriptor": "Unsafe public claim text",
                        "summary": "This is a discovery and proof claim and includes raw HTML <div>payload</div>.",
                        "domain_family": "physics",
                        "source_ref": "unsafe_ref_001",
                        "source_class_label": "unknown_source",
                        "authority_guess": "unknown_authority",
                        "evidence_role_guess": "candidate_signal",
                        "raw_html": "<html>raw</html>",
                    }
                ],
            }
        )
    )
    examples.append(
        build_cross_domain_open_problem_discovery_scout_packet_v1(
            {
                "scout_id": "cross_domain_open_problem_scout_example_d",
                "domain_families": ["materials", "architecture"],
                "input_references": ["docs/example_low_value_vague_analogy_d.md"],
                "search_governance_mode": "metadata_only_archive",
                "operator_review_need": "archive or repair the low-value analogy",
                "input_signal_items": [
                    {
                        "title_or_descriptor": "Maybe similar structure",
                        "summary": "This seems like a weak analogy with no concrete mechanism.",
                        "domain_family": "architecture",
                        "source_ref": "weak_ref_001",
                        "source_class_label": "community_discussion",
                        "authority_guess": "community_signal",
                        "evidence_role_guess": "candidate_signal",
                    }
                ],
            }
        )
    )
    return examples
