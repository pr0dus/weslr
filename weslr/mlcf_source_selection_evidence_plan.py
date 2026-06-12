"""WESLR MLCF Source Selection and Evidence Acquisition Plan V1.

Deterministic, metadata-only helpers for selecting source classes and evidence
roles before any source access. This module does not browse, fetch, ingest, or
retain raw content, and it does not authorize runtime, public claims, or final
answers.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.mlcf_ledger_registry import allowed_mlcf_ledger_ids_v1

SCHEMA_VERSION_V1 = "mlcf_source_selection_evidence_plan_v1"
HELPER_FAMILY_V1 = "mlcf_source_selection_evidence_plan"

_ALLOWED_SOURCE_CLASSES_V1 = (
    "official_standard",
    "official_government_or_agency_data",
    "official_vendor_documentation",
    "official_api_documentation",
    "public_research_paper",
    "public_dataset",
    "public_patent",
    "github_repository",
    "software_release_or_changelog",
    "public_lab_or_university_artifact",
    "public_benchmark_or_test_suite",
    "owner_supplied_observation",
    "internal_project_artifact",
    "community_discussion",
    "unknown_source",
    "blocked_private_or_hidden_source",
)

_ALLOWED_SOURCE_AUTHORITY_LEVELS_V1 = (
    "official_primary",
    "public_primary",
    "public_secondary",
    "implementation_evidence",
    "community_signal",
    "owner_context",
    "internal_context",
    "unknown_authority",
    "blocked",
)

_ALLOWED_EVIDENCE_ROLES_V1 = (
    "definition_or_standard",
    "measurement_data",
    "implementation_reference",
    "prior_art",
    "candidate_signal",
    "counterexample_source",
    "replication_target",
    "constraint_source",
    "domain_context",
    "safety_boundary_context",
    "not_authoritative_context",
)

_ALLOWED_NEXT_STEP_LABELS_V1 = (
    "build_source_plan_only",
    "operator_review",
    "prepare_authorized_ingestion_boundary",
    "prepare_metadata_only_source_summary",
    "blocked_by_safety",
    "needs_repair",
)
_ALLOWED_LEDGER_IDS_V1 = allowed_mlcf_ledger_ids_v1()

_AUTHORITY_FALSE_FLAGS_V1 = (
    "runtime_authorized",
    "source_ingestion_authorized",
    "public_claim_authorized",
    "final_answer_authority",
    "provider_model_call_authority",
    "provider_authority",
    "model_authority",
    "tool_execution_authority",
    "retrieval_tool_authority",
    "web_authority",
    "github_call_authority",
    "weslr_io_authorized",
    "weslr_read_authorized",
    "weslr_write_authorized",
    "weslr_persistence_authorized",
    "database_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "behavior_pack_promotion_authorized",
    "public_science_claim_authorized",
    "proof_claim_authorized",
    "benchmark_claim_authorized",
    "agi_claim_authorized",
    "automatic_discovery_authorized",
    "cross_user_leakage_authorized",
    "hidden_private_protected_authorized",
)

_AUTHORITY_TEXT_MARKERS_V1 = (
    "discovery",
    "proof",
    "benchmark",
    "agi",
    "final answer",
    "public claim",
    "runtime authorization",
    "source ingestion authorization",
    "provider/model/tool/retrieval/web",
    "github call authorization",
    ".weslr",
    "memory mutation",
    "project mutation",
    "behavior pack promotion",
    "cross-user leakage",
)

_HIDDEN_PRIVATE_PROTECTED_MARKERS_V1 = (
    "hidden prompt",
    "system prompt",
    "private text",
    "secret",
    "api key",
    "protected file",
    "protected",
    "private",
    "hidden",
)

_SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1 = (
    "safe",
    "metadata_only",
    "json_safe",
    "non_public",
    "source_plan_only",
    "no_runtime_wiring",
    "no_model_provider_calls",
    "no_tool_execution",
    "no_retrieval",
    "no_web_calls",
    "no_github_calls",
    "no_source_ingestion",
    "no_raw_content_retention",
    "no_weslr_io",
    "no_weslr_read",
    "no_weslr_write",
    "no_weslr_persistence",
    "no_database_writes",
    "no_memory_mutation",
    "no_project_mutation",
    "no_behavior_pack_promotion",
    "no_public_claim_authority",
    "no_final_answer_authority",
    "no_discovery_claims",
    "no_proof_claims",
    "no_benchmark_claims",
    "no_agi_claims",
    "no_public_science_claims",
    "no_hidden_private_protected_markers",
)

_REQUIRED_FIELD_NAMES_V1 = (
    "schema_version",
    "plan_id",
    "science_direction_summary",
    "domain_focus",
    "source_selection_goal",
    "recommended_source_classes",
    "source_priority_order",
    "source_authority_map",
    "evidence_role_map",
    "quality_checks",
    "freshness_checks",
    "license_or_access_checks",
    "privacy_checks",
    "blocked_source_classes",
    "why_github_is_or_is_not_useful",
    "why_official_sources_are_needed",
    "why_community_sources_are_limited",
    "recommended_ledger_id",
    "calibration_axes_to_apply",
    "missing_evidence",
    "disconfirming_evidence_to_seek",
    "operator_review_need",
    "next_safe_step",
    "forbidden_interpretations",
    "authority_status",
    "safe_metadata",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "plan_id",
    "science_direction_summary",
    "domain_focus",
    "source_selection_goal",
    "why_github_is_or_is_not_useful",
    "why_official_sources_are_needed",
    "why_community_sources_are_limited",
    "recommended_ledger_id",
    "operator_review_need",
    "next_safe_step",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "recommended_source_classes",
    "source_priority_order",
    "quality_checks",
    "freshness_checks",
    "license_or_access_checks",
    "privacy_checks",
    "blocked_source_classes",
    "calibration_axes_to_apply",
    "missing_evidence",
    "disconfirming_evidence_to_seek",
    "forbidden_interpretations",
)

_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1 = [
    "this is proven",
    "this is discovered",
    "this is public truth",
    "this is a final answer",
    "this authorizes ingestion",
    "this authorizes runtime",
    "this authorizes provider/tool/web use",
    "this authorizes github calls",
    "this authorizes .weslr access",
    "this authorizes persistence",
]

_SOURCE_CLASS_TO_AUTHORITY_V1 = {
    "official_standard": ("official_primary", ["definition_or_standard", "constraint_source"]),
    "official_government_or_agency_data": ("official_primary", ["measurement_data", "domain_context"]),
    "official_vendor_documentation": ("official_primary", ["implementation_reference", "constraint_source"]),
    "official_api_documentation": ("official_primary", ["implementation_reference"]),
    "public_research_paper": ("public_primary", ["prior_art", "replication_target"]),
    "public_dataset": ("public_primary", ["measurement_data", "replication_target"]),
    "public_patent": ("public_secondary", ["prior_art"]),
    "github_repository": ("implementation_evidence", ["implementation_reference", "candidate_signal"]),
    "software_release_or_changelog": ("implementation_evidence", ["implementation_reference", "candidate_signal"]),
    "public_lab_or_university_artifact": ("public_secondary", ["measurement_data", "replication_target"]),
    "public_benchmark_or_test_suite": ("public_secondary", ["counterexample_source", "replication_target"]),
    "owner_supplied_observation": ("owner_context", ["domain_context"]),
    "internal_project_artifact": ("internal_context", ["constraint_source"]),
    "community_discussion": ("community_signal", ["candidate_signal", "not_authoritative_context"]),
    "unknown_source": ("unknown_authority", ["not_authoritative_context"]),
}

_SOURCE_CLASS_TO_BLOCKED_AUTHORITY_V1 = {
    "blocked_private_or_hidden_source": ("blocked", ["safety_boundary_context"]),
}

_SOURCE_CLASS_TO_EVIDENCE_ROLES_V1 = {
    **{key: value[1] for key, value in _SOURCE_CLASS_TO_AUTHORITY_V1.items()},
    **{key: value[1] for key, value in _SOURCE_CLASS_TO_BLOCKED_AUTHORITY_V1.items()},
}

_SOURCE_CLASS_TO_AUTHORITY_LEVEL_V1 = {
    **{key: value[0] for key, value in _SOURCE_CLASS_TO_AUTHORITY_V1.items()},
    **{key: value[0] for key, value in _SOURCE_CLASS_TO_BLOCKED_AUTHORITY_V1.items()},
}

_SOURCE_CLASS_TO_ROLES_V1 = {
    **{key: value[1] for key, value in _SOURCE_CLASS_TO_AUTHORITY_V1.items()},
    **{key: value[1] for key, value in _SOURCE_CLASS_TO_BLOCKED_AUTHORITY_V1.items()},
}

_ALLOWED_OFFICIAL_SOURCE_CLASSES_V1 = {
    "official_standard",
    "official_government_or_agency_data",
    "official_vendor_documentation",
    "official_api_documentation",
}

_ALLOWED_IMPLEMENTATION_SOURCE_CLASSES_V1 = {
    "github_repository",
    "software_release_or_changelog",
    "public_lab_or_university_artifact",
    "public_benchmark_or_test_suite",
}

_ALLOWED_RESEARCH_SOURCE_CLASSES_V1 = {
    "public_research_paper",
    "public_dataset",
    "public_patent",
}


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
    normalized: list[str] = []
    for item in items:
        text = _compact_text(item)
        if text:
            normalized.append(text)
    return normalized


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"[redacted:{type(value).__name__}]"
    if callable(value):
        return f"[redacted:{type(value).__name__}]"
    if isinstance(value, (bool, int, float)) or value is None or isinstance(value, str):
        return value
    return f"[redacted:{type(value).__name__}]"


def _first_non_json_safe_path(value: Any, path: str = "result") -> str | None:
    if value is None or isinstance(value, (bool, int, float, str)):
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        return path
    if isinstance(value, (tuple, set, frozenset)):
        return path
    if callable(value):
        return path
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                return f"{path}.[non-string-key:{type(key).__name__}]"
            issue = _first_non_json_safe_path(item, f"{path}.{key}")
            if issue is not None:
                return issue
        return None
    if isinstance(value, list):
        for index, item in enumerate(value):
            issue = _first_non_json_safe_path(item, f"{path}[{index}]")
            if issue is not None:
                return issue
        return None
    return path


def _contains_text_markers(value: Any, markers: tuple[str, ...]) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_text_markers(item, markers) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_markers(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in markers)


def _default_authority_status() -> dict[str, Any]:
    authority_status = {flag: False for flag in _AUTHORITY_FALSE_FLAGS_V1}
    authority_status.update(
        {
            "all_authority_flags_false": True,
            "status": "metadata_only",
            "boundary_notes": "metadata-only source selection evidence plan boundary",
        }
    )
    return authority_status


def _default_safe_metadata() -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "source_plan_only": True,
        "no_runtime_wiring": True,
        "no_model_provider_calls": True,
        "no_tool_execution": True,
        "no_retrieval": True,
        "no_web_calls": True,
        "no_github_calls": True,
        "no_source_ingestion": True,
        "no_raw_content_retention": True,
        "no_weslr_io": True,
        "no_weslr_read": True,
        "no_weslr_write": True,
        "no_weslr_persistence": True,
        "no_database_writes": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_behavior_pack_promotion": True,
        "no_public_claim_authority": True,
        "no_final_answer_authority": True,
        "no_discovery_claims": True,
        "no_proof_claims": True,
        "no_benchmark_claims": True,
        "no_agi_claims": True,
        "no_public_science_claims": True,
        "no_hidden_private_protected_markers": True,
        "helper_family": HELPER_FAMILY_V1,
        "schema_family": SCHEMA_VERSION_V1,
    }


def _implemented_axis_ids() -> tuple[str, ...]:
    # Use the known axis ids from the calibrated axes helper by asking it for the
    # canonical examples and reading the declared axis ids.
    from weslr.theoretical_calibration_axes import build_initial_theoretical_calibration_axes_examples_v1

    example_set = build_initial_theoretical_calibration_axes_examples_v1()
    return tuple(axis["axis_id"] for axis in example_set["axes"])


def _canonical_forbidden_interpretations() -> list[str]:
    return list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1)


def _plan_type_from_text(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in ("private", "hidden", "protected", "scraped", "unauthorized", "no access")):
        return "blocked"
    if "github" in lowered and not any(marker in lowered for marker in ("paper", "dataset", "standard", "government", "vendor", "official")):
        return "github_heavy"
    if any(marker in lowered for marker in ("rf", "wifi", "floor-plan", "floor plan", "material", "scattering", "spatial")):
        return "rf_material_floorplan"
    return "general"


def _normalize_source_classes(value: Any) -> list[str]:
    return _normalize_text_list(value)


def _validate_source_classes(source_classes: Any) -> tuple[bool, list[str]]:
    if not isinstance(source_classes, list):
        return False, ["invalid_recommended_source_classes"]
    if not source_classes:
        return False, ["missing_recommended_source_classes"]
    labels: list[str] = []
    for item in source_classes:
        if _compact_text(item) not in _ALLOWED_SOURCE_CLASSES_V1:
            labels.append("invalid_source_class")
    return not labels, labels


def _validate_blocked_source_classes(blocked_source_classes: Any) -> tuple[bool, list[str]]:
    if not isinstance(blocked_source_classes, list):
        return False, ["invalid_blocked_source_classes"]
    labels: list[str] = []
    for item in blocked_source_classes:
        if _compact_text(item) not in _ALLOWED_SOURCE_CLASSES_V1:
            labels.append("invalid_source_class")
    return not labels, labels


def _validate_priority_order(priority_order: Any, recommended: list[str]) -> list[str]:
    if not isinstance(priority_order, list):
        return ["invalid_source_priority_order"]
    if not priority_order:
        return ["missing_source_priority_order"]
    normalized = [_compact_text(item) for item in priority_order]
    if any(not item for item in normalized):
        return ["invalid_source_priority_order"]
    if any(item not in _ALLOWED_SOURCE_CLASSES_V1 for item in normalized):
        return ["invalid_source_class"]
    if set(normalized) != set(recommended):
        return ["mismatched_source_priority_order"]
    return []


def _validate_source_authority_map(source_authority_map: Any, recommended: list[str]) -> list[str]:
    if not isinstance(source_authority_map, Mapping):
        return ["invalid_source_authority_map"]
    labels: list[str] = []
    for source_class in recommended:
        if source_class not in source_authority_map:
            labels.append(f"missing_source_authority_map_{source_class}")
            continue
        entry = source_authority_map[source_class]
        if not isinstance(entry, Mapping):
            labels.append(f"invalid_source_authority_map_{source_class}")
            continue
        authority_level = _compact_text(entry.get("authority_level"))
        if authority_level not in _ALLOWED_SOURCE_AUTHORITY_LEVELS_V1:
            labels.append("invalid_source_authority_level")
        roles = _normalize_text_list(entry.get("evidence_roles"))
        if not roles:
            labels.append(f"missing_source_authority_map_{source_class}_evidence_roles")
        elif any(role not in _ALLOWED_EVIDENCE_ROLES_V1 for role in roles):
            labels.append("invalid_evidence_role")
    for source_class, entry in source_authority_map.items():
        if _compact_text(source_class) not in _ALLOWED_SOURCE_CLASSES_V1:
            labels.append("invalid_source_class")
            continue
        if not isinstance(entry, Mapping):
            labels.append(f"invalid_source_authority_map_{source_class}")
    return list(dict.fromkeys(labels))


def _validate_evidence_role_map(evidence_role_map: Any, recommended: list[str]) -> list[str]:
    if not isinstance(evidence_role_map, Mapping):
        return ["invalid_evidence_role_map"]
    labels: list[str] = []
    for source_class in recommended:
        if source_class not in evidence_role_map:
            labels.append(f"missing_evidence_role_map_{source_class}")
            continue
        roles = _normalize_text_list(evidence_role_map[source_class])
        if not roles:
            labels.append(f"missing_evidence_role_map_{source_class}")
        elif any(role not in _ALLOWED_EVIDENCE_ROLES_V1 for role in roles):
            labels.append("invalid_evidence_role")
    for source_class, roles in evidence_role_map.items():
        if _compact_text(source_class) not in _ALLOWED_SOURCE_CLASSES_V1:
            labels.append("invalid_source_class")
        elif not isinstance(roles, list):
            labels.append("invalid_evidence_role_map")
    return list(dict.fromkeys(labels))


def _validate_source_plan_lists(name: str, value: Any, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        return [f"invalid_{name}"]
    if not value and not allow_empty:
        return [f"missing_{name}"]
    if any(_compact_text(item) == "" for item in value):
        return [f"invalid_{name}"]
    return []


def _source_classes_for_direction(plan_type: str) -> list[str]:
    if plan_type == "blocked":
        return [
            "official_standard",
            "official_government_or_agency_data",
            "public_research_paper",
            "public_dataset",
            "official_vendor_documentation",
            "public_lab_or_university_artifact",
        ]
    if plan_type == "github_heavy":
        return [
            "official_standard",
            "official_government_or_agency_data",
            "official_vendor_documentation",
            "public_research_paper",
            "public_dataset",
            "github_repository",
            "software_release_or_changelog",
            "public_lab_or_university_artifact",
            "public_benchmark_or_test_suite",
        ]
    if plan_type == "rf_material_floorplan":
        return [
            "official_standard",
            "official_government_or_agency_data",
            "official_vendor_documentation",
            "public_research_paper",
            "public_dataset",
            "github_repository",
            "public_lab_or_university_artifact",
            "public_benchmark_or_test_suite",
        ]
    return [
        "official_standard",
        "public_research_paper",
        "public_dataset",
        "github_repository",
        "software_release_or_changelog",
        "public_lab_or_university_artifact",
    ]


def _blocked_source_classes_for_direction(plan_type: str) -> list[str]:
    if plan_type == "blocked":
        return ["blocked_private_or_hidden_source"]
    return []


def _source_authority_map_for_classes(source_classes: list[str]) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for source_class in source_classes:
        if source_class in _SOURCE_CLASS_TO_AUTHORITY_V1:
            level, roles = _SOURCE_CLASS_TO_AUTHORITY_V1[source_class]
        else:
            level, roles = _SOURCE_CLASS_TO_BLOCKED_AUTHORITY_V1[source_class]
        mapping[source_class] = {
            "authority_level": level,
            "evidence_roles": list(roles),
        }
    return mapping


def _evidence_role_map_for_classes(source_classes: list[str]) -> dict[str, Any]:
    return {source_class: list(_SOURCE_CLASS_TO_ROLES_V1[source_class]) for source_class in source_classes}


def _recommended_ledger_id(plan_type: str) -> str:
    if plan_type == "blocked":
        return "decision_ledger"
    if plan_type == "rf_material_floorplan":
        return "evidence_ledger"
    if plan_type == "github_heavy":
        return "evidence_ledger"
    return "evidence_ledger"


def _recommended_calibration_axes(plan_type: str, text: str) -> list[str]:
    lowered = text.lower()
    axes: list[str] = []
    if any(marker in lowered for marker in ("rf", "wifi", "floor-plan", "floor plan", "material", "scattering", "spatial")):
        axes.extend(
            [
                "topological_structure_preserving_calibration",
                "signal_detection_calibration",
                "bayesian_calibration",
                "popper_falsification_calibration",
                "causal_counterfactual_calibration",
            ]
        )
    elif plan_type == "github_heavy":
        axes.extend(
            [
                "signal_detection_calibration",
                "bayesian_calibration",
                "information_theory_compression_calibration",
                "popper_falsification_calibration",
            ]
        )
    elif plan_type == "blocked":
        axes.extend(
            [
                "game_theory_incentive_calibration",
                "popper_falsification_calibration",
                "signal_detection_calibration",
            ]
        )
    else:
        axes.extend(["signal_detection_calibration", "bayesian_calibration", "popper_falsification_calibration"])
    return list(dict.fromkeys(axes))


def _build_quality_checks(plan_type: str) -> list[str]:
    checks = [
        "Check provenance and source class",
        "Check access scope and licensing",
        "Check date, version, and freshness",
        "Check whether the source is authoritative for the claim",
        "Check for counterexamples and replication targets",
    ]
    if plan_type == "blocked":
        checks.append("Check that closed-access or unauthorized access is not requested")
    return checks


def _build_freshness_checks() -> list[str]:
    return [
        "Prefer current standards or current releases when defining interfaces",
        "Check publication date and version history",
        "Prefer the newest authoritative artifact when a version matters",
    ]


def _build_license_or_access_checks(plan_type: str) -> list[str]:
    checks = [
        "Confirm license or access rights before ingestion",
        "Prefer public, permissioned, or clearly documented access",
        "Confirm that the access mode matches the source class",
    ]
    if plan_type == "blocked":
        checks.append("Reject closed-access or scraped sources")
    return checks


def _build_privacy_checks(plan_type: str) -> list[str]:
    checks = [
        "Avoid personal data and unnecessary retention",
        "Avoid raw-content retention in the plan",
        "Keep the output metadata-only",
    ]
    if plan_type == "blocked":
        checks.append("Do not plan access to closed-access sources")
    return checks


def _build_missing_evidence(plan_type: str) -> list[str]:
    if plan_type == "blocked":
        return [
            "No authorized source access",
            "No public evidence path yet",
        ]
    if plan_type == "github_heavy":
        return [
            "No official standard yet",
            "No authoritative paper or dataset yet",
            "No measurement or replication target yet",
        ]
    if plan_type == "rf_material_floorplan":
        return [
            "No measurement dataset yet",
            "No official standard or protocol yet",
            "No replication target yet",
        ]
    return [
        "No authoritative source plan yet",
        "No replication target yet",
    ]


def _build_disconfirming_evidence_to_seek(plan_type: str) -> list[str]:
    if plan_type == "blocked":
        return [
            "Any request for unauthorized or closed-access sources",
            "Any attempt to authorize ingestion before review",
        ]
    if plan_type == "github_heavy":
        return [
            "An official standard that contradicts the GitHub-only hypothesis",
            "A paper or dataset that shows the GitHub implementation is incomplete",
        ]
    if plan_type == "rf_material_floorplan":
        return [
            "A measurement that shows the bridge does not survive topology constraints",
            "A counterexample that makes the surface-scattering assumption unnecessary",
        ]
    return [
        "A source class that better explains the direction than the current plan",
    ]


def _build_operator_review_need(plan_type: str) -> str:
    if plan_type == "blocked":
        return "Operator review is required; closed-access, scraped, or unauthorized sources are not allowed."
    if plan_type == "github_heavy":
        return "Operator review is required because GitHub is implementation evidence, not enough by itself for authoritative science grounding."
    return "Operator review is required before any source access or ingestion decision."


def _build_next_safe_step(plan_type: str) -> str:
    if plan_type == "blocked":
        return "blocked_by_safety"
    if plan_type == "github_heavy":
        return "needs_repair"
    return "prepare_authorized_ingestion_boundary"


def _build_why_github_is_or_is_not_useful(plan_type: str) -> str:
    if plan_type == "blocked":
        return "GitHub is not useful for closed-access source access; it stays out of the plan."
    if plan_type == "github_heavy":
        return "GitHub is useful as implementation evidence and release history, but GitHub alone is not enough for authoritative science evidence."
    return "GitHub is useful as implementation evidence and a candidate-signal source, but it is not authoritative on its own."


def _build_why_official_sources_are_needed(plan_type: str) -> str:
    if plan_type == "blocked":
        return "Official public sources are needed because the requested closed-access sources are blocked."
    if plan_type == "github_heavy":
        return "Official standards, papers, datasets, or agency data are needed to ground the plan beyond GitHub implementation evidence."
    return "Official sources are needed to anchor definitions, measurements, and authoritative constraints."


def _build_why_community_sources_are_limited() -> str:
    return "Community discussion can suggest candidate leads, but it is usually not authoritative and must be cross-checked against higher-authority sources."


def _build_source_selection_goal(plan_type: str) -> str:
    if plan_type == "blocked":
        return "Keep the source plan blocked from unauthorized or closed-access sources and preserve a safe metadata-only posture."
    if plan_type == "github_heavy":
        return "Repair a GitHub-heavy plan by adding authoritative public sources, measurements, and replication targets."
    return "Select source classes that can support authoritative, implementation, and counterexample evidence without raw ingestion."


def _build_science_direction_summary(data: Mapping[str, Any]) -> str:
    text = _compact_text(data.get("science_direction_summary") or data.get("direction_summary") or data.get("input_summary"))
    if text:
        return text
    return _compact_text(data.get("domain_focus"), "Metadata-only source selection plan.")


def _build_domain_focus(data: Mapping[str, Any], science_direction_summary: str) -> str:
    focus = _compact_text(data.get("domain_focus"))
    if focus:
        return focus
    lowered = science_direction_summary.lower()
    if any(marker in lowered for marker in ("rf", "wifi", "floor-plan", "floor plan", "material", "scattering", "spatial")):
        return "RF/material/floor-plan evidence source planning"
    if "github" in lowered:
        return "GitHub-heavy evidence source planning"
    if any(marker in lowered for marker in ("private", "hidden", "protected", "scraped")):
        return "Blocked private-source planning"
    return "General source selection planning"


def allowed_mlcf_source_classes_v1() -> tuple[str, ...]:
    return _ALLOWED_SOURCE_CLASSES_V1


def allowed_mlcf_source_authority_levels_v1() -> tuple[str, ...]:
    return _ALLOWED_SOURCE_AUTHORITY_LEVELS_V1


def allowed_mlcf_evidence_roles_v1() -> tuple[str, ...]:
    return _ALLOWED_EVIDENCE_ROLES_V1


def allowed_mlcf_source_selection_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEP_LABELS_V1


def _build_default_for_plan(data: Mapping[str, Any]) -> dict[str, Any]:
    science_direction_summary = _build_science_direction_summary(data)
    plan_type = _plan_type_from_text(science_direction_summary + " " + _compact_text(data.get("source_selection_goal")) + " " + _compact_text(data.get("domain_focus")))
    domain_focus = _build_domain_focus(data, science_direction_summary)
    source_selection_goal = _compact_text(data.get("source_selection_goal"), _build_source_selection_goal(plan_type))
    recommended_source_classes = _normalize_source_classes(data.get("recommended_source_classes")) or _source_classes_for_direction(plan_type)
    blocked_source_classes = _normalize_source_classes(data.get("blocked_source_classes")) or _blocked_source_classes_for_direction(plan_type)
    source_priority_order = _normalize_source_classes(data.get("source_priority_order")) or list(recommended_source_classes)
    source_authority_map = data.get("source_authority_map")
    if source_authority_map is None:
        source_authority_map = _source_authority_map_for_classes(recommended_source_classes)
    evidence_role_map = data.get("evidence_role_map")
    if evidence_role_map is None:
        evidence_role_map = _evidence_role_map_for_classes(recommended_source_classes)
    calibration_axes_to_apply = _normalize_text_list(data.get("calibration_axes_to_apply")) or _recommended_calibration_axes(plan_type, science_direction_summary + " " + source_selection_goal + " " + domain_focus)
    plan_id = _compact_text(
        data.get("plan_id"),
        f"source_plan_{sha256((science_direction_summary + '|' + domain_focus + '|' + source_selection_goal).encode('utf-8')).hexdigest()[:16]}",
    )
    next_safe_step = _compact_text(data.get("next_safe_step"), _build_next_safe_step(plan_type))
    quality_checks = _normalize_text_list(data.get("quality_checks")) or _build_quality_checks(plan_type)
    freshness_checks = _normalize_text_list(data.get("freshness_checks")) or _build_freshness_checks()
    license_or_access_checks = _normalize_text_list(data.get("license_or_access_checks")) or _build_license_or_access_checks(plan_type)
    privacy_checks = _normalize_text_list(data.get("privacy_checks")) or _build_privacy_checks(plan_type)
    missing_evidence = _normalize_text_list(data.get("missing_evidence")) or _build_missing_evidence(plan_type)
    disconfirming_evidence_to_seek = _normalize_text_list(data.get("disconfirming_evidence_to_seek")) or _build_disconfirming_evidence_to_seek(plan_type)
    operator_review_need = _compact_text(data.get("operator_review_need"), _build_operator_review_need(plan_type))
    why_github_is_or_is_not_useful = _compact_text(data.get("why_github_is_or_is_not_useful"), _build_why_github_is_or_is_not_useful(plan_type))
    why_official_sources_are_needed = _compact_text(data.get("why_official_sources_are_needed"), _build_why_official_sources_are_needed(plan_type))
    why_community_sources_are_limited = _compact_text(data.get("why_community_sources_are_limited"), _build_why_community_sources_are_limited())
    recommended_ledger_id = _compact_text(data.get("recommended_ledger_id"), _recommended_ledger_id(plan_type))
    forbidden_interpretations = _normalize_text_list(data.get("forbidden_interpretations")) or _canonical_forbidden_interpretations()
    authority_status = data.get("authority_status") or _default_authority_status()
    safe_metadata = data.get("safe_metadata") or _default_safe_metadata()
    blocked_source_classes = list(dict.fromkeys(blocked_source_classes))
    source_priority_order = list(dict.fromkeys(source_priority_order))
    recommended_source_classes = list(dict.fromkeys(recommended_source_classes))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "plan_id": plan_id,
        "science_direction_summary": science_direction_summary,
        "domain_focus": domain_focus,
        "source_selection_goal": source_selection_goal,
        "recommended_source_classes": recommended_source_classes,
        "source_priority_order": source_priority_order,
        "source_authority_map": _json_safe(source_authority_map),
        "evidence_role_map": _json_safe(evidence_role_map),
        "quality_checks": quality_checks,
        "freshness_checks": freshness_checks,
        "license_or_access_checks": license_or_access_checks,
        "privacy_checks": privacy_checks,
        "blocked_source_classes": blocked_source_classes,
        "why_github_is_or_is_not_useful": why_github_is_or_is_not_useful,
        "why_official_sources_are_needed": why_official_sources_are_needed,
        "why_community_sources_are_limited": why_community_sources_are_limited,
        "recommended_ledger_id": recommended_ledger_id,
        "calibration_axes_to_apply": calibration_axes_to_apply,
        "missing_evidence": missing_evidence,
        "disconfirming_evidence_to_seek": disconfirming_evidence_to_seek,
        "operator_review_need": operator_review_need,
        "next_safe_step": next_safe_step,
        "forbidden_interpretations": forbidden_interpretations,
        "authority_status": _json_safe(authority_status),
        "safe_metadata": _json_safe(safe_metadata),
    }


def build_mlcf_source_selection_evidence_plan_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged = _merge_payload(payload, **overrides)
    return _build_default_for_plan(merged)


def validate_mlcf_source_selection_evidence_plan_v1(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_plan_type"],
            "validation_posture": "blocked",
            "summary_text": "Blocked MLCF source selection evidence plan: invalid plan type.",
        }

    blocked_labels: list[str] = []
    for field in _REQUIRED_FIELD_NAMES_V1:
        if field not in plan:
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(plan.get(field)):
            blocked_labels.append(f"missing_{field}")

    if _compact_text(plan.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")

    science_direction_summary = _compact_text(plan.get("science_direction_summary"))
    domain_focus = _compact_text(plan.get("domain_focus"))
    source_selection_goal = _compact_text(plan.get("source_selection_goal"))
    if not science_direction_summary:
        blocked_labels.append("missing_science_direction_summary")
    if not domain_focus:
        blocked_labels.append("missing_domain_focus")
    if not source_selection_goal:
        blocked_labels.append("missing_source_selection_goal")

    recommended_source_classes = _normalize_source_classes(plan.get("recommended_source_classes"))
    if not recommended_source_classes:
        blocked_labels.append("missing_recommended_source_classes")
    else:
        blocked_labels.extend(_validate_source_classes(recommended_source_classes)[1])

    blocked_source_classes = _normalize_source_classes(plan.get("blocked_source_classes"))
    blocked_labels.extend(_validate_blocked_source_classes(blocked_source_classes)[1])

    blocked_set = set(blocked_source_classes)
    if any(source_class in blocked_set for source_class in recommended_source_classes):
        blocked_labels.append("invalid_source_class")

    source_priority_order = _normalize_source_classes(plan.get("source_priority_order"))
    blocked_labels.extend(_validate_priority_order(source_priority_order, recommended_source_classes))

    source_authority_map = plan.get("source_authority_map")
    blocked_labels.extend(_validate_source_authority_map(source_authority_map, recommended_source_classes))

    evidence_role_map = plan.get("evidence_role_map")
    blocked_labels.extend(_validate_evidence_role_map(evidence_role_map, recommended_source_classes))

    calibration_axes = _normalize_text_list(plan.get("calibration_axes_to_apply"))
    if not calibration_axes:
        blocked_labels.append("missing_calibration_axes_to_apply")
    elif any(axis not in _implemented_axis_ids() for axis in calibration_axes):
        blocked_labels.append("invalid_calibration_axis")

    next_safe_step = _compact_text(plan.get("next_safe_step"))
    if next_safe_step not in _ALLOWED_NEXT_STEP_LABELS_V1:
        blocked_labels.append("invalid_next_safe_step")

    recommended_ledger_id = _compact_text(plan.get("recommended_ledger_id"))
    if recommended_ledger_id not in _ALLOWED_LEDGER_IDS_V1:
        blocked_labels.append("invalid_recommended_ledger_id")

    authority_status = plan.get("authority_status")
    if not isinstance(authority_status, Mapping):
        blocked_labels.append("missing_authority_status")
    else:
        for flag in _AUTHORITY_FALSE_FLAGS_V1:
            if authority_status.get(flag) is True:
                blocked_labels.append(f"unsafe_authority_flag:{flag}")
        if authority_status.get("all_authority_flags_false") is not True:
            blocked_labels.append("unsafe_authority_flags")
        if _compact_text(authority_status.get("status")) != "metadata_only":
            blocked_labels.append("unsafe_authority_status")
        if not _compact_text(authority_status.get("boundary_notes")):
            blocked_labels.append("missing_authority_boundary_notes")
        if _contains_text_markers(authority_status.get("boundary_notes"), _AUTHORITY_TEXT_MARKERS_V1):
            blocked_labels.append("unsafe_authority_text")
        if _contains_text_markers(authority_status.get("boundary_notes"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            blocked_labels.append("forbidden_hidden_private_protected_marker")

    safe_metadata = plan.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        blocked_labels.append("missing_safe_metadata")
    else:
        for flag in _SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1:
            if safe_metadata.get(flag) is not True:
                blocked_labels.append(f"unsafe_safe_metadata_flag:{flag}")
        if _contains_text_markers(safe_metadata.get("boundary_notes"), _AUTHORITY_TEXT_MARKERS_V1):
            blocked_labels.append("unsafe_safe_metadata_text")
        if _contains_text_markers(safe_metadata.get("boundary_notes"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            blocked_labels.append("forbidden_hidden_private_protected_marker")

    for field_name in (
        "science_direction_summary",
        "domain_focus",
        "source_selection_goal",
        "why_github_is_or_is_not_useful",
        "why_official_sources_are_needed",
        "why_community_sources_are_limited",
        "operator_review_need",
        "next_safe_step",
    ):
        if _contains_text_markers(plan.get(field_name), _AUTHORITY_TEXT_MARKERS_V1):
            blocked_labels.append("unsafe_authority_text")

    for field_name in (
        "science_direction_summary",
        "domain_focus",
        "source_selection_goal",
        "why_github_is_or_is_not_useful",
        "why_official_sources_are_needed",
        "why_community_sources_are_limited",
        "operator_review_need",
        "next_safe_step",
        "quality_checks",
        "freshness_checks",
        "license_or_access_checks",
        "privacy_checks",
        "missing_evidence",
        "disconfirming_evidence_to_seek",
    ):
        if _contains_text_markers(plan.get(field_name), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            blocked_labels.append("forbidden_hidden_private_protected_marker")

    for field_name in (
        "quality_checks",
        "freshness_checks",
        "license_or_access_checks",
        "privacy_checks",
        "missing_evidence",
        "disconfirming_evidence_to_seek",
        "forbidden_interpretations",
    ):
        value = plan.get(field_name)
        if not isinstance(value, list):
            blocked_labels.append(f"invalid_{field_name}")
        elif not value:
            blocked_labels.append(f"missing_{field_name}")
        elif any(_compact_text(item) == "" for item in value):
            blocked_labels.append(f"invalid_{field_name}")

    if not _compact_text(plan.get("why_github_is_or_is_not_useful")):
        blocked_labels.append("missing_why_github_is_or_is_not_useful")
    if not _compact_text(plan.get("why_official_sources_are_needed")):
        blocked_labels.append("missing_why_official_sources_are_needed")
    if not _compact_text(plan.get("why_community_sources_are_limited")):
        blocked_labels.append("missing_why_community_sources_are_limited")

    if not isinstance(plan.get("source_authority_map"), Mapping):
        blocked_labels.append("invalid_source_authority_map")
    if not isinstance(plan.get("evidence_role_map"), Mapping):
        blocked_labels.append("invalid_evidence_role_map")

    if _compact_text(plan.get("source_selection_goal")) and _compact_text(plan.get("why_github_is_or_is_not_useful")).lower().count("github") > 0:
        recommended = set(recommended_source_classes)
        if "github_repository" in recommended and not recommended.intersection(_ALLOWED_OFFICIAL_SOURCE_CLASSES_V1):
            blocked_labels.append("github_only_official_evidence_claim")

    if any(_compact_text(item) == "blocked_private_or_hidden_source" for item in blocked_source_classes):
        if next_safe_step not in {"blocked_by_safety", "needs_repair"}:
            blocked_labels.append("unsafe_private_hidden_source_plan")

    if _compact_text(plan.get("source_selection_goal")).lower().find("official") >= 0 and not set(recommended_source_classes).intersection(_ALLOWED_OFFICIAL_SOURCE_CLASSES_V1):
        blocked_labels.append("official_claim_without_official_source_class")

    if _compact_text(plan.get("source_selection_goal")).lower().find("github") >= 0 and set(recommended_source_classes) == {"github_repository"}:
        blocked_labels.append("github_only_official_evidence_claim")

    blocked_labels.extend(["non_json_safe_output"] if _first_non_json_safe_path(plan) is not None else [])

    valid = not blocked_labels
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "validation_posture": "valid" if valid else "blocked",
        "summary_text": "Valid MLCF source selection evidence plan." if valid else "Blocked MLCF source selection evidence plan: metadata or authority checks failed.",
    }


def summarize_mlcf_source_selection_evidence_plan_v1(plan: Any) -> dict[str, Any]:
    packet = plan if isinstance(plan, Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "plan_id": _compact_text(packet.get("plan_id")),
        "science_direction_summary": _compact_text(packet.get("science_direction_summary")),
        "domain_focus": _compact_text(packet.get("domain_focus")),
        "recommended_ledger_id": _compact_text(packet.get("recommended_ledger_id")),
        "source_class_count": len(_normalize_text_list(packet.get("recommended_source_classes"))),
        "next_safe_step": _compact_text(packet.get("next_safe_step")),
        "summary_text": _compact_text(
            packet.get("source_selection_goal"),
            "Metadata-only source selection evidence plan.",
        ),
        "validation_posture": validate_mlcf_source_selection_evidence_plan_v1(packet).get("validation_posture", "blocked"),
    }


def to_mlcf_source_selection_evidence_plan_json_safe_v1(plan: Any) -> Any:
    return _json_safe(plan)


def _build_initial_mlcf_source_selection_evidence_plan_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []

    examples.append(
        build_mlcf_source_selection_evidence_plan_v1(
            plan_id="rf_material_floorplan_source_plan",
            science_direction_summary="Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.",
            domain_focus="RF/material/floor-plan evidence planning",
            source_selection_goal="Select authoritative public sources that can ground the RF/material/floor-plan candidate safely.",
            recommended_source_classes=[
                "official_standard",
                "official_government_or_agency_data",
                "public_research_paper",
                "public_dataset",
                "github_repository",
                "public_lab_or_university_artifact",
                "official_vendor_documentation",
            ],
            source_priority_order=[
                "official_standard",
                "official_government_or_agency_data",
                "public_research_paper",
                "public_dataset",
                "github_repository",
                "public_lab_or_university_artifact",
                "official_vendor_documentation",
            ],
            source_authority_map=_source_authority_map_for_classes([
                "official_standard",
                "official_government_or_agency_data",
                "public_research_paper",
                "public_dataset",
                "github_repository",
                "public_lab_or_university_artifact",
                "official_vendor_documentation",
            ]),
            evidence_role_map=_evidence_role_map_for_classes([
                "official_standard",
                "official_government_or_agency_data",
                "public_research_paper",
                "public_dataset",
                "github_repository",
                "public_lab_or_university_artifact",
                "official_vendor_documentation",
            ]),
            quality_checks=[
                "Check provenance, version, and scope",
                "Check that the source is authoritative for its role",
                "Check for counterexamples and replication targets",
            ],
            freshness_checks=[
                "Prefer current standards and current releases",
                "Check publication date and version history",
            ],
            license_or_access_checks=[
                "Confirm access rights before any ingestion",
                "Prefer public and permissioned access",
            ],
            privacy_checks=[
                "Avoid raw retention",
                "Keep the plan metadata-only",
            ],
            blocked_source_classes=[],
            why_github_is_or_is_not_useful="GitHub is useful as implementation evidence and release history, but it is not authoritative on its own.",
            why_official_sources_are_needed="Official standards, papers, datasets, or agency data are needed to ground the candidate beyond implementation evidence.",
            why_community_sources_are_limited="Community discussion can suggest leads, but it is not authoritative and must be cross-checked.",
            recommended_ledger_id="evidence_ledger",
            calibration_axes_to_apply=[
                "signal_detection_calibration",
                "bayesian_calibration",
                "topological_structure_preserving_calibration",
                "causal_counterfactual_calibration",
                "popper_falsification_calibration",
            ],
            missing_evidence=[
                "No measurement dataset yet",
                "No official standard or protocol yet",
                "No replication target yet",
            ],
            disconfirming_evidence_to_seek=[
                "A measurement that shows the bridge does not survive topology constraints",
                "A counterexample that makes the surface-scattering assumption unnecessary",
            ],
            operator_review_need="Operator review is required before any source access or ingestion decision.",
            next_safe_step="prepare_authorized_ingestion_boundary",
            forbidden_interpretations=_canonical_forbidden_interpretations(),
        )
    )

    examples.append(
        build_mlcf_source_selection_evidence_plan_v1(
            plan_id="github_only_source_plan_blocked_as_insufficient",
            science_direction_summary="A direction that tries to rely only on GitHub repositories for evidence.",
            domain_focus="GitHub-heavy evidence planning",
            source_selection_goal="Repair the plan by adding authoritative public sources beyond GitHub implementation evidence.",
            recommended_source_classes=[
                "official_standard",
                "official_government_or_agency_data",
                "public_research_paper",
                "public_dataset",
                "github_repository",
                "software_release_or_changelog",
                "public_lab_or_university_artifact",
            ],
            source_priority_order=[
                "official_standard",
                "official_government_or_agency_data",
                "public_research_paper",
                "public_dataset",
                "github_repository",
                "software_release_or_changelog",
                "public_lab_or_university_artifact",
            ],
            source_authority_map=_source_authority_map_for_classes([
                "official_standard",
                "official_government_or_agency_data",
                "public_research_paper",
                "public_dataset",
                "github_repository",
                "software_release_or_changelog",
                "public_lab_or_university_artifact",
            ]),
            evidence_role_map=_evidence_role_map_for_classes([
                "official_standard",
                "official_government_or_agency_data",
                "public_research_paper",
                "public_dataset",
                "github_repository",
                "software_release_or_changelog",
                "public_lab_or_university_artifact",
            ]),
            quality_checks=[
                "Check provenance, version, and scope",
                "Check whether GitHub is only implementation evidence",
                "Check for official standards, papers, or datasets",
            ],
            freshness_checks=[
                "Check release history and publication dates",
                "Prefer recent authoritative artifacts where relevant",
            ],
            license_or_access_checks=[
                "Confirm access rights before any ingestion",
                "Confirm whether the repository or artifact is public and permissioned",
            ],
            privacy_checks=[
                "Avoid raw retention",
                "Do not treat GitHub alone as authoritative science evidence",
            ],
            blocked_source_classes=[],
            why_github_is_or_is_not_useful="GitHub is useful as implementation evidence, but GitHub alone is not enough for authoritative science evidence.",
            why_official_sources_are_needed="Official standards, papers, datasets, or agency data are needed to ground the plan beyond GitHub.",
            why_community_sources_are_limited="Community discussion can help candidate leads, but it is not authoritative and must be cross-checked.",
            recommended_ledger_id="evidence_ledger",
            calibration_axes_to_apply=[
                "signal_detection_calibration",
                "bayesian_calibration",
                "information_theory_compression_calibration",
                "popper_falsification_calibration",
            ],
            missing_evidence=[
                "No official standard yet",
                "No authoritative paper or dataset yet",
                "No measurement or replication target yet",
            ],
            disconfirming_evidence_to_seek=[
                "An official source that contradicts the GitHub-only assumption",
                "A dataset or paper that shows the implementation evidence is incomplete",
            ],
            operator_review_need="Operator review is required because GitHub is implementation evidence, not enough by itself for authoritative science grounding.",
            next_safe_step="needs_repair",
            forbidden_interpretations=_canonical_forbidden_interpretations(),
        )
    )

    examples.append(
        build_mlcf_source_selection_evidence_plan_v1(
            plan_id="private_hidden_source_plan_blocked",
            science_direction_summary="A direction that requests unauthorized closed-access sources.",
            domain_focus="Blocked closed-access planning",
            source_selection_goal="Block unauthorized or closed-access sources and keep the plan metadata-only.",
            recommended_source_classes=[
                "official_standard",
                "public_research_paper",
                "public_dataset",
                "official_vendor_documentation",
            ],
            source_priority_order=[
                "official_standard",
                "public_research_paper",
                "public_dataset",
                "official_vendor_documentation",
            ],
            source_authority_map=_source_authority_map_for_classes([
                "official_standard",
                "public_research_paper",
                "public_dataset",
                "official_vendor_documentation",
            ]),
            evidence_role_map=_evidence_role_map_for_classes([
                "official_standard",
                "public_research_paper",
                "public_dataset",
                "official_vendor_documentation",
            ]),
            quality_checks=[
                "Check provenance, scope, and access rights",
                "Check for closed-access or unauthorized access requests",
            ],
            freshness_checks=[
                "Check publication date and version history",
            ],
            license_or_access_checks=[
                "Reject closed-access or scraped sources",
                "Confirm only public, permissioned access paths",
            ],
            privacy_checks=[
                "Do not plan raw retention",
                "Do not plan access to closed-access sources",
            ],
            blocked_source_classes=["blocked_private_or_hidden_source"],
            why_github_is_or_is_not_useful="GitHub is not useful for closed-access source access; it stays out of the plan.",
            why_official_sources_are_needed="Official public sources are needed because the requested closed-access sources are blocked.",
            why_community_sources_are_limited="Community discussion cannot authorize closed-access source access.",
            recommended_ledger_id="decision_ledger",
            calibration_axes_to_apply=[
                "game_theory_incentive_calibration",
                "popper_falsification_calibration",
                "signal_detection_calibration",
            ],
            missing_evidence=[
                "No authorized source access",
                "No public evidence path yet",
            ],
            disconfirming_evidence_to_seek=[
                "Any request for unauthorized or closed-access sources",
                "Any attempt to authorize ingestion before review",
            ],
            operator_review_need="Operator review is required; closed-access, scraped, or unauthorized sources are not allowed.",
            next_safe_step="blocked_by_safety",
            forbidden_interpretations=_canonical_forbidden_interpretations(),
        )
    )

    return examples


def build_initial_mlcf_source_selection_evidence_plan_examples_v1() -> list[dict[str, Any]]:
    return deepcopy(_build_initial_mlcf_source_selection_evidence_plan_examples_v1())
