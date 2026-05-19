"""Ranked/native interop shadow artifact report helpers v1.

Pure, deterministic, in-memory report helpers for metadata-only
``ranked_native_interop_shadow_artifact_v1`` artifacts. This module does not
wire runtime behavior, call providers, execute prompts, persist data, or produce
final answers.
"""

from __future__ import annotations

import copy
import json
from numbers import Number
from typing import Any, Dict, Iterable, List, Mapping

from weslr.ranked_native_interop_shadow_artifact import (
    validate_ranked_native_interop_shadow_artifact_v1,
    summarize_ranked_native_interop_shadow_artifact_v1,
)

SCHEMA_VERSION = "ranked_native_interop_shadow_artifact_report_v1"
HELPER_NAME = "ranked_native_interop_shadow_artifact_report_helpers_v1"
REPORT_TYPE = "ranked_native_interop_shadow_artifact_report_v1"
ARTIFACT_TYPE = "ranked_native_interop_shadow_artifact_v1"

FALSE_SAFETY_FLAGS = (
    "runtime_wired",
    "final_answer_generated",
    "raw_prompt_response_retained",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "persistence_performed",
    "feature_flag_enabled",
    "official_evaluation_claimed",
)

READINESS_LABELS = (
    "ranked_native_artifact_report_helpers_implemented",
    "metadata_only_report_surface",
    "helper_authority_boundaries_preserved",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
)

MINOR_FOLLOWUPS = (
    "renderer_next_lane_wording_drift",
    "validator_phrase_key_limitation",
)

REQUIRED_REPORT_FIELDS = (
    "schema_version",
    "helper_name",
    "report_type",
    "artifact_type",
    "artifact_valid",
    "safe_to_render",
    "validation",
    "artifact_identity",
    "ranked_metadata_summary",
    "native_metadata_summary",
    "constraint_summary",
    "safety_flag_summary",
    "readiness_labels",
    "minor_followups",
    "aggregate_labels",
    "gaps_risks",
    *FALSE_SAFETY_FLAGS,
)

FORBIDDEN_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "prompt_text",
    "response_text",
    "final_answer_text",
    "final_answer",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "model_output",
    "official_score",
    "iq_score",
    "turing_score",
    "benchmark_score",
    "runtime_output",
    "occ_as_weslr",
    "openclaw_as_weslr",
    "conscious",
    "sentient",
)

_ALLOWED_KEYS_WITH_FORBIDDEN_FRAGMENTS = {
    "final_answer_generated",
    "final_answer_authority_not_granted",
    "final_answer_contract_metadata",
    "raw_prompt_response_retained",
}

FORBIDDEN_TRUE_FLAGS = (
    "runtime_wired",
    "final_answer_generated",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "persistence_performed",
    "feature_flag_enabled",
    "official_evaluation_claimed",
    "raw_prompt_response_retained",
    "network_call_made",
    "subprocess_call_made",
)

FORBIDDEN_VALUE_MARKERS = (
    "raw prompt",
    "raw response",
    "final answer:",
    "final answer text",
    "private content",
    "hidden prompt",
    "answer key",
    "provider output",
    "model output",
    "official score",
    "official benchmark",
    "benchmark score",
    "turing-test pass",
    "turing test pass",
    "iq score",
    "iq claim",
    "certification claim",
    "product-readiness claim",
    "product readiness claim",
    "runtime output treated as authority",
    "runtime authority",
    "runtime ready",
    "runtime-ready",
    "consciousness claim",
    "sentience claim",
    "occ is weslr",
    "openclaw is weslr",
)


def _deepcopy_json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True))


def _list_or_empty(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return copy.deepcopy(value)
    if isinstance(value, (tuple, set)):
        return list(copy.deepcopy(list(value)))
    return [copy.deepcopy(value)]


def _merge_unique(*iterables: Iterable[Any]) -> List[Any]:
    merged: List[Any] = []
    for iterable in iterables:
        for item in iterable:
            if item not in merged:
                merged.append(item)
    return merged


def _walk(value: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield child_path, child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child
            yield from _walk(child, child_path)


def _safe_reason(label: str) -> str:
    return label.replace(" ", "_").replace(".", "_").replace("[", "_").replace("]", "_")


def _presence(value: Any) -> str:
    if value is None:
        return "absent"
    if isinstance(value, (Mapping, list, tuple, set, str)) and len(value) == 0:
        return "absent"
    return "present"


def _count(value: Any) -> int:
    if isinstance(value, Mapping):
        return len(value)
    if isinstance(value, (list, tuple, set, str)):
        return len(value)
    return 0 if value is None else 1


def _metadata_summary(artifact: Dict[str, Any], fields: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    return {
        field: {
            "presence": _presence(artifact.get(field)),
            "count": _count(artifact.get(field)),
        }
        for field in fields
    }


def _safe_labels(value: Any) -> List[Any]:
    return _list_or_empty(value)


def derive_ranked_native_artifact_report_aggregate_labels_v1(report: dict) -> list[str]:
    """Derive qualitative report aggregate labels only; no scores."""

    artifact_valid = bool(report.get("artifact_valid")) if isinstance(report, dict) else False
    labels = [
        "metadata_only_report_surface",
        "runtime_integration_not_authorized",
        "final_answer_authority_not_granted",
        "official_evaluation_not_claimed",
    ]
    if artifact_valid:
        labels.append("artifact_valid")
    else:
        labels.append("artifact_invalid_blocked")

    minor = report.get("minor_followups", []) if isinstance(report, dict) else []
    if minor:
        labels.append("minor_followup_carried_forward")
    return labels


def build_ranked_native_interop_shadow_artifact_report_v1(artifact: dict) -> dict:
    """Build a safe metadata-only report from a ranked/native interop artifact."""

    artifact_validation = validate_ranked_native_interop_shadow_artifact_v1(artifact)
    artifact_summary = summarize_ranked_native_interop_shadow_artifact_v1(artifact)
    artifact_is_dict = isinstance(artifact, dict)
    artifact_valid = bool(artifact_validation.get("valid"))

    report: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "helper_name": HELPER_NAME,
        "report_type": REPORT_TYPE,
        "artifact_type": artifact.get("artifact_type") if artifact_is_dict else None,
        "artifact_valid": artifact_valid,
        "safe_to_render": artifact_valid,
        "validation": {
            "valid": artifact_valid,
            "safe_to_render": bool(artifact_validation.get("safe_to_render")),
            "reason_labels": copy.deepcopy(artifact_validation.get("reason_labels", [])),
        },
        "artifact_identity": {
            "schema_version": artifact.get("schema_version") if artifact_is_dict else None,
            "helper_name": artifact.get("helper_name") if artifact_is_dict else None,
            "artifact_type": artifact.get("artifact_type") if artifact_is_dict else None,
        },
        "ranked_metadata_summary": {},
        "native_metadata_summary": {},
        "constraint_summary": {},
        "safety_flag_summary": {flag: False for flag in FALSE_SAFETY_FLAGS},
        "readiness_labels": list(READINESS_LABELS),
        "minor_followups": list(MINOR_FOLLOWUPS),
        "aggregate_labels": [],
        "gaps_risks": [],
    }
    report.update({flag: False for flag in FALSE_SAFETY_FLAGS})

    if artifact_valid and artifact_is_dict:
        report["ranked_metadata_summary"] = _metadata_summary(
            artifact,
            (
                "ranked_state_frame_summary",
                "selected_candidate_metadata",
                "rejected_candidate_labels",
                "ranking_label_summary",
                "final_answer_contract_metadata",
            ),
        )
        report["native_metadata_summary"] = _metadata_summary(
            artifact,
            (
                "native_reasoning_frame_metadata",
                "native_draft_shape_metadata",
                "native_self_check_metadata",
                "native_assembly_metadata",
            ),
        )
        report["constraint_summary"] = {
            "provenance_constraints": {
                "count": _count(artifact.get("provenance_constraints")),
                "labels": _safe_labels(artifact.get("provenance_constraints")),
            },
            "evidence_constraints": {
                "count": _count(artifact.get("evidence_constraints")),
                "labels": _safe_labels(artifact.get("evidence_constraints")),
            },
            "safety_boundary_labels": {
                "count": _count(artifact.get("safety_boundary_labels")),
                "labels": _safe_labels(artifact.get("safety_boundary_labels")),
            },
            "rejected_candidate_labels": {
                "count": _count(artifact.get("rejected_candidate_labels")),
                "labels": _safe_labels(artifact.get("rejected_candidate_labels")),
            },
        }
        artifact_readiness = _list_or_empty(artifact.get("readiness_labels"))
        artifact_followups = _list_or_empty(artifact.get("minor_followups"))
        report["readiness_labels"] = _merge_unique(READINESS_LABELS, artifact_readiness)
        report["minor_followups"] = _merge_unique(MINOR_FOLLOWUPS, artifact_followups)
    else:
        report["ranked_metadata_summary"] = {
            "blocked": True,
            "reason": "artifact_invalid_blocked",
            "ranked_metadata_present": bool(artifact_summary.get("ranked_metadata_present")),
        }
        report["native_metadata_summary"] = {
            "blocked": True,
            "reason": "artifact_invalid_blocked",
            "native_metadata_present": bool(artifact_summary.get("native_metadata_present")),
        }
        report["constraint_summary"] = {
            "blocked": True,
            "reason": "artifact_invalid_blocked",
            "validator_reason_label_count": _count(artifact_validation.get("reason_labels", [])),
        }
        report["gaps_risks"] = [
            "unsafe_artifact_blocked",
            "raw_content_leakage_guard_active",
            "final_answer_authority_not_granted",
            "runtime_authority_not_granted",
        ]

    report["aggregate_labels"] = derive_ranked_native_artifact_report_aggregate_labels_v1(report)
    if artifact_valid:
        report["gaps_risks"] = [
            "runtime_integration_not_authorized",
            "final_answer_authority_not_granted",
            "minor_followup_visibility_required",
            "identity_boundary_preserved",
        ]
    return report


def build_ranked_native_artifact_report_tables_v1(report: dict) -> dict:
    """Return metadata-only table rows for internal engineering review."""

    if not isinstance(report, dict):
        return {
            "artifact_field_presence": [],
            "safety_flags": [],
            "ranked_native_metadata": [],
            "constraint_labels": [],
            "validator_reason_labels": [
                {"reason_label": "report_not_dict", "presence": "present"},
            ],
        }

    artifact_identity = report.get("artifact_identity", {}) if isinstance(report.get("artifact_identity"), dict) else {}
    artifact_field_presence = [
        {"field": field, "presence": _presence(artifact_identity.get(field))}
        for field in ("schema_version", "helper_name", "artifact_type")
    ] + [
        {"field": field, "presence": _presence(report.get(field))}
        for field in (
            "validation",
            "ranked_metadata_summary",
            "native_metadata_summary",
            "constraint_summary",
            "readiness_labels",
            "minor_followups",
        )
    ]

    safety_flags = [
        {"safety_flag": flag, "required_state": False, "actual_state": report.get(flag), "compliant": report.get(flag) is False}
        for flag in FALSE_SAFETY_FLAGS
    ]

    ranked_native_metadata: List[Dict[str, Any]] = []
    for side, summary_key in (("ranked", "ranked_metadata_summary"), ("native", "native_metadata_summary")):
        summary = report.get(summary_key, {})
        if isinstance(summary, Mapping):
            for category, metadata in summary.items():
                if isinstance(metadata, Mapping):
                    ranked_native_metadata.append(
                        {
                            "side": side,
                            "metadata_category": category,
                            "presence": metadata.get("presence", "present" if metadata else "absent"),
                            "count": metadata.get("count", 0),
                        }
                    )
                else:
                    ranked_native_metadata.append(
                        {"side": side, "metadata_category": category, "presence": _presence(metadata), "count": _count(metadata)}
                    )

    constraint_labels: List[Dict[str, Any]] = []
    constraints = report.get("constraint_summary", {})
    if isinstance(constraints, Mapping):
        for category, metadata in constraints.items():
            labels = metadata.get("labels", []) if isinstance(metadata, Mapping) else []
            if labels:
                for label in labels:
                    constraint_labels.append({"constraint_category": category, "label": label, "presence": "present"})
            else:
                constraint_labels.append(
                    {
                        "constraint_category": category,
                        "label_count": metadata.get("count", 0) if isinstance(metadata, Mapping) else 0,
                        "presence": _presence(metadata),
                    }
                )

    validation = report.get("validation", {}) if isinstance(report.get("validation"), Mapping) else {}
    reasons = validation.get("reason_labels", []) if isinstance(validation.get("reason_labels", []), list) else []
    validator_reason_labels = [
        {"reason_label": reason, "presence": "present"}
        for reason in reasons
    ] or [{"reason_label": "none", "presence": "absent"}]

    return {
        "artifact_field_presence": artifact_field_presence,
        "safety_flags": safety_flags,
        "ranked_native_metadata": ranked_native_metadata,
        "constraint_labels": constraint_labels,
        "validator_reason_labels": validator_reason_labels,
    }


def validate_ranked_native_interop_shadow_artifact_report_v1(report: dict) -> dict:
    """Validate report safety without rendering offending content."""

    if not isinstance(report, dict):
        return {"valid": False, "safe_to_render": False, "reason_labels": ["report_not_dict"]}

    reason_labels: List[str] = []
    for field in REQUIRED_REPORT_FIELDS:
        if field not in report:
            reason_labels.append(f"missing_required_field:{field}")

    if report.get("schema_version") != SCHEMA_VERSION:
        reason_labels.append("unexpected_schema_version")
    if report.get("helper_name") != HELPER_NAME:
        reason_labels.append("unexpected_helper_name")
    if report.get("report_type") != REPORT_TYPE:
        reason_labels.append("unexpected_report_type")

    for flag in FALSE_SAFETY_FLAGS:
        if report.get(flag) is not False:
            reason_labels.append(f"required_false_flag_violation:{flag}")
    for flag in FORBIDDEN_TRUE_FLAGS:
        if report.get(flag) is True:
            reason_labels.append(f"forbidden_true_flag:{flag}")

    readiness = report.get("readiness_labels", [])
    if not isinstance(readiness, list):
        reason_labels.append("readiness_labels_not_list")
    else:
        for label in READINESS_LABELS:
            if label not in readiness:
                reason_labels.append(f"missing_readiness_label:{label}")

    minor = report.get("minor_followups", [])
    if not isinstance(minor, list):
        reason_labels.append("minor_followups_not_list")
    else:
        for label in MINOR_FOLLOWUPS:
            if label not in minor:
                reason_labels.append(f"missing_minor_followup:{label}")

    for path, value in _walk(report):
        key = path.split(".")[-1].split("[")[0].lower()
        if key not in _ALLOWED_KEYS_WITH_FORBIDDEN_FRAGMENTS:
            for fragment in FORBIDDEN_KEY_FRAGMENTS:
                if fragment in key:
                    reason_labels.append(f"forbidden_key:{_safe_reason(path)}")
                    break

        if key in FORBIDDEN_TRUE_FLAGS and value is True:
            reason_labels.append(f"forbidden_true_flag:{key}")

        lowered = value.lower() if isinstance(value, str) else ""
        if lowered:
            for marker in FORBIDDEN_VALUE_MARKERS:
                if marker in lowered:
                    reason_labels.append(f"forbidden_value_marker:{marker.replace(' ', '_')}")

        if isinstance(value, Number) and not isinstance(value, bool):
            lowered_path = path.lower()
            if any(fragment in lowered_path for fragment in ("official_score", "iq_score", "benchmark_score", "turing_score")):
                reason_labels.append(f"forbidden_numeric_official_score:{_safe_reason(path)}")

    deduped: List[str] = []
    for reason in reason_labels:
        if reason not in deduped:
            deduped.append(reason)
    valid = not deduped
    return {"valid": valid, "safe_to_render": valid, "reason_labels": deduped}


def _format_bool(value: Any) -> str:
    return "true" if value is True else "false" if value is False else "absent"


def render_ranked_native_interop_shadow_artifact_report_markdown_v1(report: dict) -> str:
    """Render a safe Markdown report from metadata-only report content."""

    validation = validate_ranked_native_interop_shadow_artifact_report_v1(report)
    if not validation["valid"]:
        reasons = "\n".join(f"- `{reason}`" for reason in validation["reason_labels"])
        return (
            "# Ranked/Native Interop Shadow Artifact Report — BLOCKED\n\n"
            "## Report Status\n"
            "- report_valid: `False`\n"
            "- safe_to_render: `False`\n\n"
            "## Safe Reason Labels\n"
            f"{reasons}\n\n"
            "Offending content is intentionally not rendered.\n"
        )

    tables = build_ranked_native_artifact_report_tables_v1(report)
    identity = report.get("artifact_identity", {})
    readiness = "\n".join(f"- `{label}`" for label in report.get("readiness_labels", []))
    followups = "\n".join(f"- `{label}`" for label in report.get("minor_followups", []))
    gaps = "\n".join(f"- `{label}`" for label in report.get("gaps_risks", []))
    flags = "\n".join(f"- `{flag}`: `{_format_bool(report.get(flag))}`" for flag in FALSE_SAFETY_FLAGS)
    aggregate = "\n".join(f"- `{label}`" for label in report.get("aggregate_labels", []))

    return (
        "# Ranked/Native Interop Shadow Artifact Report\n\n"
        "## Report Status\n"
        f"- report_type: `{report.get('report_type')}`\n"
        f"- artifact_valid: `{report.get('artifact_valid')}`\n"
        f"- safe_to_render: `{report.get('safe_to_render')}`\n\n"
        "## Artifact Identity\n"
        f"- schema_version: `{identity.get('schema_version')}`\n"
        f"- helper_name: `{identity.get('helper_name')}`\n"
        f"- artifact_type: `{identity.get('artifact_type')}`\n\n"
        "## Validation Status\n"
        f"- valid: `{report.get('validation', {}).get('valid')}`\n"
        f"- reason_label_count: `{len(report.get('validation', {}).get('reason_labels', []))}`\n\n"
        "## Ranked Metadata Summary\n"
        f"- table_rows: `{len(tables['ranked_native_metadata'])}`\n"
        "- metadata shape only; no candidate prose\n\n"
        "## Native Metadata Summary\n"
        f"- table_rows: `{len(tables['ranked_native_metadata'])}`\n"
        "- metadata shape only; no dry preview prose\n\n"
        "## Constraints Summary\n"
        f"- constraint_table_rows: `{len(tables['constraint_labels'])}`\n\n"
        "## Safety Boundary Summary\n"
        f"{flags}\n"
        "- runtime integration not authorized\n"
        "- final-answer authority not granted\n"
        "- raw prompt/response not retained\n"
        "- official evaluation not claimed\n\n"
        "## Readiness Labels\n"
        f"{readiness}\n\n"
        "## Minor Followups\n"
        f"{followups}\n\n"
        "## Metadata-only Table Summaries\n"
        f"- artifact_field_presence_rows: `{len(tables['artifact_field_presence'])}`\n"
        f"- safety_flag_rows: `{len(tables['safety_flags'])}`\n"
        f"- ranked_native_metadata_rows: `{len(tables['ranked_native_metadata'])}`\n"
        f"- constraint_label_rows: `{len(tables['constraint_labels'])}`\n"
        f"- validator_reason_label_rows: `{len(tables['validator_reason_labels'])}`\n\n"
        "## Aggregate Labels\n"
        f"{aggregate}\n\n"
        "## Gaps/Risks\n"
        f"{gaps}\n\n"
        "## Next-lane Recommendation\n"
        "`REVIEW_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_HELPERS_IMPLEMENTATION_V1`\n\n"
        "## Safety Confirmation\n"
        "- helper-only metadata report surface\n"
        "- no runtime wiring\n"
        "- no final answer generation\n"
        "- no prompt execution\n"
        "- no provider, search, or advisor calls\n"
        "- no persistence or .weslr writes\n"
        "- no feature flag enablement\n"
        "- no official claims\n"
    )


def to_ranked_native_interop_shadow_artifact_report_json_safe_v1(report: dict) -> dict:
    """Return a JSON-safe deep copy, or explicit invalid wrapper for unsafe reports."""

    validation = validate_ranked_native_interop_shadow_artifact_report_v1(report)
    if not validation["valid"]:
        return {
            "valid": False,
            "safe_to_render": False,
            "reason_labels": copy.deepcopy(validation["reason_labels"]),
            "report_type": report.get("report_type") if isinstance(report, dict) else None,
        }
    return _deepcopy_json_safe(report)


__all__ = [
    "build_ranked_native_interop_shadow_artifact_report_v1",
    "build_ranked_native_artifact_report_tables_v1",
    "derive_ranked_native_artifact_report_aggregate_labels_v1",
    "validate_ranked_native_interop_shadow_artifact_report_v1",
    "render_ranked_native_interop_shadow_artifact_report_markdown_v1",
    "to_ranked_native_interop_shadow_artifact_report_json_safe_v1",
]
