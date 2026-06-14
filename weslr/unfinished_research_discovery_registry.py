"""WESLR Unfinished Research Discovery Registry V1.

Pure metadata-only registry helpers for governed unfinished-research discovery.
No IO, no network, no provider/model calls, and no runtime wiring.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Iterable, Mapping

from weslr.unfinished_research_discovery_constants import (
    allowed_unfinished_research_artifact_types_v1,
    allowed_unfinished_research_evidence_roles_v1,
    allowed_unfinished_research_expansion_recommendations_v1,
    allowed_unfinished_research_operator_confirmation_tokens_v1,
    allowed_unfinished_research_route_types_v1,
    allowed_unfinished_research_signal_types_v1,
    allowed_unfinished_research_source_classes_v1,
    denied_unfinished_research_authority_flags_v1,
    forbidden_unfinished_research_discovery_meanings_v1,
    forbidden_unfinished_research_language_markers_v1,
    required_unfinished_research_disconfirmation_fields_v1,
    safe_unfinished_research_discovery_meanings_v1,
)

SCHEMA_VERSION_V1 = "unfinished_research_discovery_registry_v1"
DOMAIN_FAMILY_REGISTRY_SCHEMA_VERSION_V1 = "unfinished_research_domain_family_registry_v1"

_REQUIRED_DOMAIN_FAMILY_FIELDS_V1 = (
    "domain_family_id",
    "display_name",
    "description",
    "source_class_keywords",
    "signal_family_detection_cues",
    "query_templates",
    "likely_source_classes",
    "required_disconfirmation_classes",
    "blocked_claims",
    "operator_review_required",
)

_REQUIRED_REGISTRY_FIELDS_V1 = (
    "schema_version",
    "signal_types",
    "routes",
    "source_classes",
    "evidence_roles",
    "operator_confirmation_tokens",
    "expansion_recommendations",
    "artifact_types",
    "required_disconfirmation_fields",
    "safe_discovery_meanings",
    "forbidden_discovery_meanings",
    "denied_authority_flags",
    "denied_authority_flags_state",
    "forbidden_language_markers",
    "domain_family_registry",
)

_DOMAIN_FAMILY_BLUEPRINTS_V1 = (
    {
        "domain_family_id": "rf_sensing",
        "display_name": "RF sensing",
        "description": "Radio-frequency sensing, sensing-by-emission, and signal interpretation.",
        "source_class_keywords": ("rf", "wireless", "sensing", "radar", "signal", "antenna"),
        "signal_family_detection_cues": ("wireless sensing", "rf sensing", "signal processing", "radar sensing"),
        "query_templates": (
            "{topic} rf sensing survey",
            "{topic} wireless sensing benchmark",
            "{topic} radar sensing limitations",
        ),
        "likely_source_classes": ("public_research_paper", "survey_paper", "benchmark_paper", "dataset_record", "technical_report"),
        "required_disconfirmation_classes": ("benchmark_paper", "replication_study", "negative_result_paper"),
        "blocked_claims": ("discovery_as_final_answer", "discovery_as_verified_invention", "discovery_as_public_science_claim"),
        "operator_review_required": True,
    },
    {
        "domain_family_id": "energy_systems",
        "display_name": "Energy systems",
        "description": "Energy generation, storage, grids, conversion, and efficiency research.",
        "source_class_keywords": ("energy", "battery", "grid", "storage", "power", "conversion"),
        "signal_family_detection_cues": ("energy system", "grid", "battery", "storage", "power conversion"),
        "query_templates": (
            "{topic} energy systems survey",
            "{topic} battery benchmark",
            "{topic} grid limitations",
        ),
        "likely_source_classes": ("public_research_paper", "survey_paper", "benchmark_paper", "dataset_record", "government_agency_report", "technical_report"),
        "required_disconfirmation_classes": ("benchmark_paper", "replication_study", "negative_result_paper"),
        "blocked_claims": ("discovery_as_public_science_claim", "discovery_as_official_benchmark_result", "discovery_as_final_answer"),
        "operator_review_required": True,
    },
    {
        "domain_family_id": "materials",
        "display_name": "Materials",
        "description": "Materials discovery, characterization, synthesis, and process constraints.",
        "source_class_keywords": ("materials", "synthesis", "alloy", "polymer", "ceramic", "microstructure"),
        "signal_family_detection_cues": ("materials discovery", "synthesis route", "microstructure", "characterization"),
        "query_templates": (
            "{topic} materials survey",
            "{topic} synthesis benchmark",
            "{topic} characterization limitations",
        ),
        "likely_source_classes": ("public_research_paper", "survey_paper", "benchmark_paper", "lab_university_artifact", "patent", "technical_report"),
        "required_disconfirmation_classes": ("benchmark_paper", "replication_study", "negative_result_paper"),
        "blocked_claims": ("discovery_as_verified_invention", "discovery_as_public_science_claim", "discovery_as_final_answer"),
        "operator_review_required": True,
    },
    {
        "domain_family_id": "biology_medicine",
        "display_name": "Biology and medicine",
        "description": "Biology, biomedical, clinical, and translational research with strong safety review.",
        "source_class_keywords": ("biology", "medicine", "clinical", "biomedical", "patient", "trial"),
        "signal_family_detection_cues": ("clinical trial", "biomedical", "patient outcome", "biology"),
        "query_templates": (
            "{topic} biology review",
            "{topic} clinical study limitations",
            "{topic} biomedical benchmark",
        ),
        "likely_source_classes": ("public_research_paper", "survey_paper", "review_paper", "dataset_record", "government_agency_report", "thesis_dissertation"),
        "required_disconfirmation_classes": ("benchmark_paper", "replication_study", "negative_result_paper"),
        "blocked_claims": ("discovery_as_proven_truth", "discovery_as_verified_invention", "discovery_as_agi_consciousness_sentience_claim"),
        "operator_review_required": True,
    },
    {
        "domain_family_id": "mathematics",
        "display_name": "Mathematics",
        "description": "Mathematics, formal methods, proofs, and open problem structure.",
        "source_class_keywords": ("math", "mathematics", "proof", "theorem", "formal", "lemma"),
        "signal_family_detection_cues": ("open problem", "proof technique", "formal methods", "theorem"),
        "query_templates": (
            "{topic} mathematics survey",
            "{topic} open problem",
            "{topic} proof limitations",
        ),
        "likely_source_classes": ("public_research_paper", "survey_paper", "review_paper", "preprint", "technical_report"),
        "required_disconfirmation_classes": ("replication_study", "negative_result_paper", "benchmark_paper"),
        "blocked_claims": ("discovery_as_proven_truth", "discovery_as_solved_theory", "discovery_as_final_answer"),
        "operator_review_required": True,
    },
    {
        "domain_family_id": "physics_quantum",
        "display_name": "Physics and quantum",
        "description": "Physics, quantum systems, measurements, and foundational constraints.",
        "source_class_keywords": ("physics", "quantum", "measurement", "particle", "field", "experiment"),
        "signal_family_detection_cues": ("quantum", "measurement gap", "anomaly", "experimental physics"),
        "query_templates": (
            "{topic} physics review",
            "{topic} quantum measurement gap",
            "{topic} physics anomaly",
        ),
        "likely_source_classes": ("public_research_paper", "survey_paper", "benchmark_paper", "dataset_record", "lab_university_artifact"),
        "required_disconfirmation_classes": ("benchmark_paper", "replication_study", "negative_result_paper"),
        "blocked_claims": ("discovery_as_public_science_claim", "discovery_as_official_benchmark_result", "discovery_as_final_answer"),
        "operator_review_required": True,
    },
    {
        "domain_family_id": "ai_cognition",
        "display_name": "AI and cognition",
        "description": "AI systems, cognition research, models, and capability boundaries.",
        "source_class_keywords": ("ai", "cognition", "model", "learning", "reasoning", "agent"),
        "signal_family_detection_cues": ("model limitation", "cognition", "reasoning gap", "agent behavior"),
        "query_templates": (
            "{topic} ai cognition survey",
            "{topic} model limitation",
            "{topic} agent benchmark",
        ),
        "likely_source_classes": ("public_research_paper", "survey_paper", "benchmark_paper", "preprint", "github_repository", "forum_blog_as_weak_signal"),
        "required_disconfirmation_classes": ("benchmark_paper", "replication_study", "negative_result_paper"),
        "blocked_claims": ("discovery_as_agi_consciousness_sentience_claim", "discovery_as_public_science_claim", "discovery_as_final_answer"),
        "operator_review_required": True,
    },
    {
        "domain_family_id": "language_communication",
        "display_name": "Language and communication",
        "description": "Language structure, communication protocols, discourse, and meaning systems.",
        "source_class_keywords": ("language", "communication", "protocol", "semantics", "discourse", "syntax"),
        "signal_family_detection_cues": ("language protocol", "communication pattern", "semantic drift", "protocol design"),
        "query_templates": (
            "{topic} language protocol survey",
            "{topic} communication benchmark",
            "{topic} semantics limitations",
        ),
        "likely_source_classes": ("public_research_paper", "survey_paper", "review_paper", "technical_report", "official_standard"),
        "required_disconfirmation_classes": ("replication_study", "negative_result_paper", "benchmark_paper"),
        "blocked_claims": ("discovery_as_public_science_claim", "discovery_as_final_answer", "discovery_as_language_protocol_candidate"),
        "operator_review_required": True,
    },
    {
        "domain_family_id": "economics_labor",
        "display_name": "Economics and labor",
        "description": "Economics, labor markets, workforce impacts, and policy-sensitive analysis.",
        "source_class_keywords": ("economics", "labor", "workforce", "employment", "policy", "market"),
        "signal_family_detection_cues": ("labor market", "workforce impact", "employment trend", "policy analysis"),
        "query_templates": (
            "{topic} labor market survey",
            "{topic} workforce impact report",
            "{topic} economics policy limitations",
        ),
        "likely_source_classes": ("public_research_paper", "survey_paper", "government_agency_report", "official_standard", "technical_report"),
        "required_disconfirmation_classes": ("replication_study", "benchmark_paper", "negative_result_paper"),
        "blocked_claims": ("discovery_as_public_science_claim", "discovery_as_final_answer", "discovery_as_verified_invention"),
        "operator_review_required": True,
    },
    {
        "domain_family_id": "standards_specification",
        "display_name": "Standards and specification",
        "description": "Standards, formal specifications, interoperability, and normative guidance.",
        "source_class_keywords": ("standard", "specification", "interoperability", "normative", "protocol", "compliance"),
        "signal_family_detection_cues": ("official standard", "specification", "compliance", "interoperability"),
        "query_templates": (
            "{topic} standards specification",
            "{topic} official standard",
            "{topic} interoperability benchmark",
        ),
        "likely_source_classes": ("official_standard", "government_agency_report", "vendor_technical_documentation", "technical_report", "public_research_paper"),
        "required_disconfirmation_classes": ("benchmark_paper", "replication_study", "negative_result_paper"),
        "blocked_claims": ("discovery_as_official_benchmark_result", "discovery_as_final_answer", "discovery_as_public_science_claim"),
        "operator_review_required": True,
    },
)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(_normalize_text(item) for item in value)
    if isinstance(value, list):
        return tuple(_normalize_text(item) for item in value)
    return (_normalize_text(value),)


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


def _unique_tuple(values: Iterable[Any]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = _normalize_text(item)
        if text not in seen:
            seen.add(text)
            result.append(text)
    return tuple(result)


def get_initial_domain_family_registry_v1() -> tuple[dict[str, Any], ...]:
    return tuple(deepcopy(item) for item in _DOMAIN_FAMILY_BLUEPRINTS_V1)


def validate_domain_family_registry_v1(registry: Any) -> dict[str, Any]:
    expected_ids = {item["domain_family_id"] for item in _DOMAIN_FAMILY_BLUEPRINTS_V1}
    labels: list[str] = []
    ok = True
    if not isinstance(registry, (list, tuple)):
        return {
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_domain_family_registry_type"],
            "validation_status": "blocked",
        }
    ids: set[str] = set()
    for index, item in enumerate(registry):
        if not isinstance(item, Mapping):
            ok = False
            labels.append(f"invalid_domain_family_entry_{index}")
            continue
        missing = [field for field in _REQUIRED_DOMAIN_FAMILY_FIELDS_V1 if field not in item]
        if missing:
            ok = False
            labels.extend(f"missing_{field}" for field in missing)
        family_id = _normalize_text(item.get("domain_family_id"))
        if family_id:
            ids.add(family_id)
        if _normalize_text(item.get("domain_family_id")) not in expected_ids:
            ok = False
            labels.append("unknown_domain_family_id")
        for field in ("source_class_keywords", "signal_family_detection_cues", "query_templates", "likely_source_classes", "required_disconfirmation_classes", "blocked_claims"):
            value = item.get(field)
            if not isinstance(value, (list, tuple)) or not all(_normalize_text(v) for v in value):
                ok = False
                labels.append(f"invalid_{field}")
        if item.get("operator_review_required") is not True:
            ok = False
            labels.append("operator_review_required_not_true")
        unknown_sources = set(_normalize_text_tuple(item.get("likely_source_classes"))) - set(allowed_unfinished_research_source_classes_v1())
        if unknown_sources:
            ok = False
            labels.append("unknown_source_class_value")
        unknown_disconf = set(_normalize_text_tuple(item.get("required_disconfirmation_classes"))) - {"benchmark_paper", "replication_study", "negative_result_paper"}
        if unknown_disconf:
            ok = False
            labels.append("unknown_required_disconfirmation_class")
    if ids != expected_ids:
        ok = False
        labels.append("missing_or_extra_domain_family_ids")
    return {
        "valid": ok,
        "blocked": not ok,
        "blocked_labels": _unique_tuple(labels),
        "validation_status": "valid" if ok else "blocked",
    }


def summarize_domain_family_registry_v1(registry: Any) -> dict[str, Any]:
    families = list(registry) if isinstance(registry, (list, tuple)) else []
    validation = validate_domain_family_registry_v1(registry)
    return {
        "schema_version": DOMAIN_FAMILY_REGISTRY_SCHEMA_VERSION_V1,
        "family_count": len(families),
        "domain_family_ids": tuple(_normalize_text(item.get("domain_family_id")) for item in families if isinstance(item, Mapping)),
        "operator_review_required": True,
        "validation_status": validation["validation_status"],
        "summary_text": "Metadata-only registry of unfinished-research domain families.",
    }


def to_domain_family_registry_json_safe_v1(registry: Any) -> Any:
    return _json_safe(registry)


def get_unfinished_research_registry_v1() -> dict[str, Any]:
    denied_authority_flags = denied_unfinished_research_authority_flags_v1()
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "signal_types": allowed_unfinished_research_signal_types_v1(),
        "routes": allowed_unfinished_research_route_types_v1(),
        "source_classes": allowed_unfinished_research_source_classes_v1(),
        "evidence_roles": allowed_unfinished_research_evidence_roles_v1(),
        "operator_confirmation_tokens": allowed_unfinished_research_operator_confirmation_tokens_v1(),
        "expansion_recommendations": allowed_unfinished_research_expansion_recommendations_v1(),
        "artifact_types": allowed_unfinished_research_artifact_types_v1(),
        "required_disconfirmation_fields": required_unfinished_research_disconfirmation_fields_v1(),
        "safe_discovery_meanings": safe_unfinished_research_discovery_meanings_v1(),
        "forbidden_discovery_meanings": forbidden_unfinished_research_discovery_meanings_v1(),
        "denied_authority_flags": denied_authority_flags,
        "denied_authority_flags_state": {flag: False for flag in denied_authority_flags},
        "forbidden_language_markers": forbidden_unfinished_research_language_markers_v1(),
        "domain_family_registry": get_initial_domain_family_registry_v1(),
    }


def validate_unfinished_research_registry_v1(registry: Any) -> dict[str, Any]:
    labels: list[str] = []
    ok = True
    if not isinstance(registry, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "blocked_labels": ("invalid_registry_type",),
            "validation_status": "blocked",
        }
    missing = [field for field in _REQUIRED_REGISTRY_FIELDS_V1 if field not in registry]
    if missing:
        ok = False
        labels.extend(f"missing_{field}" for field in missing)
    if _normalize_text(registry.get("schema_version")) != SCHEMA_VERSION_V1:
        ok = False
        labels.append("invalid_schema_version")
    if tuple(_normalize_text_tuple(registry.get("signal_types"))) != allowed_unfinished_research_signal_types_v1():
        ok = False
        labels.append("invalid_signal_types")
    if tuple(_normalize_text_tuple(registry.get("routes"))) != allowed_unfinished_research_route_types_v1():
        ok = False
        labels.append("invalid_routes")
    if tuple(_normalize_text_tuple(registry.get("source_classes"))) != allowed_unfinished_research_source_classes_v1():
        ok = False
        labels.append("invalid_source_classes")
    if tuple(_normalize_text_tuple(registry.get("evidence_roles"))) != allowed_unfinished_research_evidence_roles_v1():
        ok = False
        labels.append("invalid_evidence_roles")
    if tuple(_normalize_text_tuple(registry.get("operator_confirmation_tokens"))) != allowed_unfinished_research_operator_confirmation_tokens_v1():
        ok = False
        labels.append("invalid_operator_confirmation_tokens")
    if tuple(_normalize_text_tuple(registry.get("expansion_recommendations"))) != allowed_unfinished_research_expansion_recommendations_v1():
        ok = False
        labels.append("invalid_expansion_recommendations")
    if tuple(_normalize_text_tuple(registry.get("artifact_types"))) != allowed_unfinished_research_artifact_types_v1():
        ok = False
        labels.append("invalid_artifact_types")
    if tuple(_normalize_text_tuple(registry.get("required_disconfirmation_fields"))) != required_unfinished_research_disconfirmation_fields_v1():
        ok = False
        labels.append("invalid_required_disconfirmation_fields")
    if tuple(_normalize_text_tuple(registry.get("safe_discovery_meanings"))) != safe_unfinished_research_discovery_meanings_v1():
        ok = False
        labels.append("invalid_safe_discovery_meanings")
    if tuple(_normalize_text_tuple(registry.get("forbidden_discovery_meanings"))) != forbidden_unfinished_research_discovery_meanings_v1():
        ok = False
        labels.append("invalid_forbidden_discovery_meanings")
    if tuple(_normalize_text_tuple(registry.get("denied_authority_flags"))) != denied_unfinished_research_authority_flags_v1():
        ok = False
        labels.append("invalid_denied_authority_flags")
    denied_state = registry.get("denied_authority_flags_state")
    if not isinstance(denied_state, Mapping):
        ok = False
        labels.append("invalid_denied_authority_flags_state")
    else:
        for flag in denied_unfinished_research_authority_flags_v1():
            if denied_state.get(flag) is not False:
                ok = False
                labels.append(f"denied_authority_flag_not_false_{flag}")
    if tuple(_normalize_text_tuple(registry.get("forbidden_language_markers"))) != forbidden_unfinished_research_language_markers_v1():
        ok = False
        labels.append("invalid_forbidden_language_markers")
    domain_registry = registry.get("domain_family_registry")
    domain_validation = validate_domain_family_registry_v1(domain_registry)
    if not domain_validation["valid"]:
        ok = False
        labels.extend(domain_validation["blocked_labels"])
    return {
        "valid": ok,
        "blocked": not ok,
        "blocked_labels": _unique_tuple(labels),
        "validation_status": "valid" if ok else "blocked",
    }


def summarize_unfinished_research_registry_v1(registry: Any) -> dict[str, Any]:
    validation = validate_unfinished_research_registry_v1(registry)
    domain_registry = registry.get("domain_family_registry") if isinstance(registry, Mapping) else ()
    families = list(domain_registry) if isinstance(domain_registry, (list, tuple)) else []
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "signal_type_count": len(tuple(_normalize_text_tuple(registry.get("signal_types")))) if isinstance(registry, Mapping) else 0,
        "route_count": len(tuple(_normalize_text_tuple(registry.get("routes")))) if isinstance(registry, Mapping) else 0,
        "domain_family_count": len(families),
        "operator_review_required": True,
        "validation_status": validation["validation_status"],
        "summary_text": "Metadata-only unfinished-research discovery registry.",
    }


def to_unfinished_research_registry_json_safe_v1(registry: Any) -> Any:
    return _json_safe(registry)
