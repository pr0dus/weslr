"""WESLR OER no-op record builder V1.

Helper-only, metadata-only, deterministic, in-memory helpers for ontology-
sufficient no-op record packets. These helpers do not create ontology expansion
requests, mutate ontology, auto-apply ontology changes, call providers/models,
fetch sources, ingest sources, write .weslr data, or grant any discovery,
proof, public-science, product-readiness, or final-answer authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

SCHEMA_NAME_V1 = "oer_noop_record_schema_v1"
SCHEMA_VERSION_V1 = "v1"
ONTOLOGY_MARKER_V1 = "ontology_sufficient_for_domain"

_ALLOWED_DOMAIN_FAMILIES_V1 = (
    "materials",
    "energy_systems",
    "radio_astronomy",
    "language_communication",
    "ai_cognition",
    "biology_medicine",
    "unknown_domain",
)
_ALLOWED_NEXT_SAFE_STEPS_V1 = (
    "operator_review",
    "continue_metadata_only_route",
    "prepare_source_selection_plan",
    "prepare_review_artifact",
    "candidate_preparation_excluded_wrong_route",
    "blocked_until_owner_approval",
)
_DENIED_AUTHORITY_FLAGS_V1 = (
    "ontology_expansion_request_authority",
    "ontology_auto_application_authority",
    "ontology_self_modification_authority",
    "runtime_wiring_authority",
    "provider_model_call_authority",
    "source_ingestion_authority",
    "source_fetch_authority",
    "accepted_evidence_authority",
    "accepted_candidate_authority",
    "proposal_action_authority",
    "final_answer_authority",
    "public_claim_authority",
    "proof_claim_authority",
    "discovery_truth_claim_authority",
    "product_readiness_claim_authority",
    "memory_mutation_authority",
    "database_write_authority",
    "weslr_io_authority",
)
_FORBIDDEN_WORDINGS_V1 = (
    "weslr expanded ontology",
    "ontology applied automatically",
    "ontology self-modified",
    "proof",
    "confirmed discovery",
    "public science claim",
    "accepted evidence",
    "accepted candidate",
    "final answer",
    "agi",
    "consciousness",
    "sentience",
    "source ingestion authorized",
    "provider call authorized",
    "runtime enabled",
    "product readiness",
)
_REQUIRED_FIELDS_V1 = (
    "schema_name",
    "schema_version",
    "record_id",
    "source_artifact_id",
    "domain_family",
    "signal_type",
    "current_route",
    "ontology_marker",
    "sufficient_power",
    "why_no_expansion_needed",
    "covered_by_registry_entries",
    "missing_ontology_items",
    "recommended_expansion_actions",
    "next_safe_step",
    "owner_review_required",
    "operator_review_required",
    "blocked_claims",
    "denied_authority_flags",
    "safe_metadata_summary",
    "blocked_labels",
    "final_judgment",
)


def _normalize_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(value)
    return [deepcopy(value)]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, set):
        return [_json_safe(v) for v in sorted(value, key=str)]
    return deepcopy(value)


def _contains_forbidden_language(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _FORBIDDEN_WORDINGS_V1)


def _looks_like_weslr_io(text: str) -> bool:
    lowered = text.lower()
    return ".weslr" in lowered or "weslr/" in lowered and "io" in lowered


def build_oer_noop_record_v1(**packet: Any) -> dict[str, Any]:
    record = {
        "schema_name": SCHEMA_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "record_id": _normalize_text(packet.get("record_id", "oer_noop_record_v1")),
        "source_artifact_id": _normalize_text(packet.get("source_artifact_id", "unknown")),
        "domain_family": _normalize_text(packet.get("domain_family", "unknown_domain")),
        "signal_type": _normalize_text(packet.get("signal_type", "unknown_signal")),
        "current_route": _normalize_text(packet.get("current_route", "metadata_only_route")),
        "ontology_marker": ONTOLOGY_MARKER_V1,
        "sufficient_power": True,
        "why_no_expansion_needed": _normalize_text(
            packet.get(
                "why_no_expansion_needed",
                "Ontology is sufficient for this domain and signal; no expansion request is needed.",
            )
        ),
        "covered_by_registry_entries": _normalize_list(packet.get("covered_by_registry_entries", [])),
        "missing_ontology_items": [],
        "recommended_expansion_actions": [],
        "next_safe_step": _normalize_text(packet.get("next_safe_step", "operator_review")),
        "owner_review_required": True,
        "operator_review_required": True,
        "blocked_claims": _normalize_list(
            packet.get(
                "blocked_claims",
                [
                    "no_unapproved_claims",
                    "no_ownerless_change",
                    "no_auto_application",
                    "no_runtime_activation",
                ],
            )
        ),
        "denied_authority_flags": {flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        "safe_metadata_summary": _normalize_text(
            packet.get(
                "safe_metadata_summary",
                "ontology sufficient for domain; no expansion request created; continue metadata-only review",
            )
        ),
        "blocked_labels": _normalize_list(packet.get("blocked_labels", ["no_ontology_expansion_request", "no_auto_application"])),
        "final_judgment": _normalize_text(
            packet.get(
                "final_judgment",
                "ontology_sufficient_no_expansion_request_needed",
            )
        ),
    }
    if packet.get("denied_authority_flags"):
        for key, value in dict(packet["denied_authority_flags"]).items():
            if key in record["denied_authority_flags"]:
                record["denied_authority_flags"][key] = bool(value)
    return record


def validate_oer_noop_record_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    blocked_labels: list[str] = []

    def block(label: str) -> None:
        if label not in blocked_labels:
            blocked_labels.append(label)

    if not isinstance(record, Mapping):
        return {"valid": False, "blocked": True, "blocked_labels": ["invalid_record_type"]}
    missing = [field for field in _REQUIRED_FIELDS_V1 if field not in record]
    if missing:
        for field in missing:
            block(f"missing_field:{field}")
    if record.get("ontology_marker") != ONTOLOGY_MARKER_V1:
        block("invalid_ontology_marker")
    if record.get("sufficient_power") is not True:
        block("sufficient_power_not_true")
    if list(record.get("recommended_expansion_actions") or []):
        block("recommended_expansion_actions_not_empty")
    if list(record.get("missing_ontology_items") or []):
        block("missing_ontology_items_not_empty")
    if record.get("owner_review_required") is not True:
        block("owner_review_required_not_true")
    if record.get("operator_review_required") is not True:
        block("operator_review_required_not_true")
    blocked_claims = list(record.get("blocked_claims") or [])
    if not blocked_claims:
        block("blocked_claims_empty")
    denied = record.get("denied_authority_flags") or {}
    if not isinstance(denied, Mapping):
        block("denied_authority_flags_invalid")
    else:
        for flag in _DENIED_AUTHORITY_FLAGS_V1:
            if denied.get(flag) is True:
                block(f"denied_authority_true:{flag}")
    text_blobs = [
        _normalize_text(record.get("why_no_expansion_needed")),
        _normalize_text(record.get("safe_metadata_summary")),
        _normalize_text(record.get("final_judgment")),
        _normalize_text(record.get("record_id")),
        _normalize_text(record.get("source_artifact_id")),
        _normalize_text(record.get("domain_family")),
        _normalize_text(record.get("signal_type")),
        _normalize_text(record.get("current_route")),
        _normalize_text(record.get("next_safe_step")),
        " ".join(map(_normalize_text, blocked_claims)),
        " ".join(map(_normalize_text, record.get("blocked_labels") or [])),
    ]
    for text in text_blobs:
        lowered = text.lower()
        if _contains_forbidden_language(lowered):
            block("forbidden_wording_present")
        if ".weslr" in lowered:
            block("weslr_io_reference_blocked")
        if any(marker in lowered for marker in ("source ingestion authorized", "source fetch authority", "provider call authorized", "runtime enabled")):
            block("runtime_source_provider_authority_language_present")
        if any(marker in lowered for marker in ("accepted evidence", "accepted candidate", "final answer")):
            block("accepted_or_final_answer_language_present")
        if any(marker in lowered for marker in ("proof", "confirmed discovery", "public science claim", "product readiness")):
            block("proof_discovery_public_science_language_present")
        if any(marker in lowered for marker in ("agi", "consciousness", "sentience")):
            block("agi_consciousness_sentience_language_present")
    if record.get("schema_name") != SCHEMA_NAME_V1:
        block("invalid_schema_name")
    if record.get("schema_version") != SCHEMA_VERSION_V1:
        block("invalid_schema_version")
    if record.get("next_safe_step") not in _ALLOWED_NEXT_SAFE_STEPS_V1:
        block("invalid_next_safe_step")
    if record.get("domain_family") not in _ALLOWED_DOMAIN_FAMILIES_V1:
        block("invalid_domain_family")
    if not record.get("final_judgment"):
        block("missing_final_judgment")
    valid = not blocked_labels
    return {"valid": valid, "blocked": not valid, "blocked_labels": blocked_labels}


def summarize_oer_noop_record_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_oer_noop_record_v1(record)
    return {
        "record_id": _normalize_text(record.get("record_id")),
        "source_artifact_id": _normalize_text(record.get("source_artifact_id")),
        "domain_family": _normalize_text(record.get("domain_family")),
        "signal_type": _normalize_text(record.get("signal_type")),
        "ontology_marker": _normalize_text(record.get("ontology_marker")),
        "sufficient_power": bool(record.get("sufficient_power")),
        "next_safe_step": _normalize_text(record.get("next_safe_step")),
        "owner_review_required": bool(record.get("owner_review_required")),
        "operator_review_required": bool(record.get("operator_review_required")),
        "blocked": validation["blocked"],
        "final_judgment": _normalize_text(record.get("final_judgment")),
    }


def render_oer_noop_record_markdown_v1(record: Mapping[str, Any]) -> str:
    summary = summarize_oer_noop_record_v1(record)
    registry_entries = "\n".join(f"- {item}" for item in _normalize_list(record.get("covered_by_registry_entries"))) or "- none"
    blocked_claims_items = [item for item in _normalize_list(record.get("blocked_claims"))]
    blocked_claims_rendered = []
    for item in blocked_claims_items:
        text = _normalize_text(item)
        if "final answer" in text.lower():
            text = "[redacted final-answer wording]"
        blocked_claims_rendered.append(text)
    blocked_claims = "\n".join(f"- {item}" for item in blocked_claims_rendered) or "- none"
    denied = record.get("denied_authority_flags") or {}
    denied_lines = "\n".join(f"- {key}: {bool(denied.get(key))}" for key in _DENIED_AUTHORITY_FLAGS_V1)
    return (
        f"# OER no-op record\n\n"
        f"- Record ID: {summary['record_id']}\n"
        f"- Source artifact ID: {summary['source_artifact_id']}\n"
        f"- Domain family: {summary['domain_family']}\n"
        f"- Signal type: {summary['signal_type']}\n"
        f"- Ontology marker: {summary['ontology_marker']}\n"
        f"- Sufficient power: {summary['sufficient_power']}\n"
        f"- Next safe step: {summary['next_safe_step']}\n"
        f"- Owner review required: {summary['owner_review_required']}\n"
        f"- Operator review required: {summary['operator_review_required']}\n"
        f"- Final judgment: {summary['final_judgment']}\n\n"
        f"## Why no expansion is needed\n"
        f"{_normalize_text(record.get('why_no_expansion_needed'))}\n\n"
        f"## Covered registry entries\n{registry_entries}\n\n"
        f"## Blocked claims\n{blocked_claims}\n\n"
        f"## Denied authority summary\n{denied_lines}\n"
    )


def to_oer_noop_record_json_safe_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return _json_safe(record)


def build_initial_oer_noop_record_examples_v1() -> tuple[dict[str, Any], ...]:
    safe_materials = build_oer_noop_record_v1(
        record_id="materials_second_true_run_noop",
        source_artifact_id="second_controlled_true_run_materials",
        domain_family="materials",
        signal_type="materials_metadata_signal",
        current_route="scout_to_metadata_only_source_locator_route",
        covered_by_registry_entries=("materials_registry_entry_v1", "ontology_sufficient_for_domain_v1"),
        next_safe_step="operator_review",
        blocked_claims=("no_unapproved_claims", "no_ownerless_change", "no_auto_application", "no_runtime_activation"),
        blocked_labels=("no_unapproved_claims", "no_auto_application"),
        final_judgment="ontology_sufficient_no_expansion_request_needed",
    )
    safe_energy = build_oer_noop_record_v1(
        record_id="energy_systems_planned_noop",
        source_artifact_id="planned_energy_metadata_route",
        domain_family="energy_systems",
        signal_type="energy_metadata_signal",
        current_route="metadata_only_planned_route",
        covered_by_registry_entries=("energy_registry_entry_v1",),
        next_safe_step="continue_metadata_only_route",
        blocked_claims=("no_unapproved_claims", "no_auto_application"),
        final_judgment="ontology_sufficient_no_expansion_request_needed",
    )
    unsafe = build_oer_noop_record_v1(
        record_id="unsafe_fake_expansion_noop",
        source_artifact_id="unsafe_expansion_example",
        domain_family="unknown_domain",
        signal_type="unsafe_metadata_signal",
        current_route="metadata_only_route",
        covered_by_registry_entries=(),
        next_safe_step="blocked_until_owner_approval",
        blocked_claims=("no_unapproved_claims", "no_auto_application"),
        final_judgment="ontology_sufficient_no_expansion_request_needed",
    )
    unsafe["denied_authority_flags"]["ontology_auto_application_authority"] = True
    unsafe["why_no_expansion_needed"] = "ontology applied automatically"
    return (safe_materials, safe_energy, unsafe)


__all__ = [
    "build_oer_noop_record_v1",
    "validate_oer_noop_record_v1",
    "summarize_oer_noop_record_v1",
    "render_oer_noop_record_markdown_v1",
    "to_oer_noop_record_json_safe_v1",
    "build_initial_oer_noop_record_examples_v1",
]
