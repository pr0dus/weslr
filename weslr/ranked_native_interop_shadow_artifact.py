"""Ranked/native interop shadow artifact helpers v1.

Pure in-memory helpers for a metadata-only ranked/native interop shadow
artifact. This module does not call runtime systems, providers, network,
subprocesses, or persistence paths.
"""

from __future__ import annotations

import copy
import json
from numbers import Number
from typing import Any, Dict, Iterable, List, Mapping

SCHEMA_VERSION = "ranked_native_interop_shadow_artifact_v1"
HELPER_NAME = "ranked_native_interop_shadow_artifact_helpers_v1"
ARTIFACT_TYPE = "ranked_native_interop_shadow_artifact_v1"

REQUIRED_READINESS_LABELS = (
    "ranked_native_interop_shadow_artifact_helpers_implemented",
    "metadata_only_artifact",
    "helper_only_not_runtime_wired",
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

FALSE_SAFETY_FLAGS = (
    "final_answer_generated",
    "runtime_wired",
    "raw_prompt_response_retained",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "persistence_performed",
    "feature_flag_enabled",
    "official_evaluation_claimed",
)

FORBIDDEN_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "prompt_text",
    "response_text",
    "final_answer_text",
    "full_conversation",
    "hidden_prompt",
    "answer_key",
    "private_content",
    "provider_output",
    "model_output",
    "official_score",
    "iq_score",
    "turing_passed",
    "benchmark_certified",
    "product_ready",
    "conscious",
    "sentient",
    "occ_as_weslr",
    "openclaw_as_weslr",
)

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
    "network_call_made",
    "subprocess_call_made",
)

REQUIRED_FIELDS = (
    "schema_version",
    "helper_name",
    "artifact_type",
    "ranked_state_frame_summary",
    "selected_candidate_metadata",
    "rejected_candidate_labels",
    "ranking_label_summary",
    "final_answer_contract_metadata",
    "native_reasoning_frame_metadata",
    "native_draft_shape_metadata",
    "native_self_check_metadata",
    "native_assembly_metadata",
    "provenance_constraints",
    "evidence_constraints",
    "safety_boundary_labels",
    "interop_notes",
    "readiness_labels",
    "minor_followups",
    *FALSE_SAFETY_FLAGS,
)

_ALLOWED_KEYS_WITH_FORBIDDEN_FRAGMENTS = {
    "final_answer_contract_metadata",
    "final_answer_generated",
    "raw_prompt_response_retained",
}


def _dict_or_empty(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return copy.deepcopy(dict(value))
    return {"value": copy.deepcopy(value)}


def _list_or_empty(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(copy.deepcopy(list(value)))
    return [copy.deepcopy(value)]


def _merge_unique(first: Iterable[Any], second: Iterable[Any]) -> List[Any]:
    merged: List[Any] = []
    for item in list(first) + list(second):
        if item not in merged:
            merged.append(item)
    return merged


def build_ranked_native_interop_shadow_artifact_v1(
    *,
    ranked_state_frame_summary: Any = None,
    selected_candidate_metadata: Any = None,
    rejected_candidate_labels: Any = None,
    ranking_label_summary: Any = None,
    final_answer_contract_metadata: Any = None,
    native_reasoning_frame_metadata: Any = None,
    native_draft_shape_metadata: Any = None,
    native_self_check_metadata: Any = None,
    native_assembly_metadata: Any = None,
    provenance_constraints: Any = None,
    evidence_constraints: Any = None,
    safety_boundary_labels: Any = None,
    interop_notes: Any = None,
    readiness_labels: Any = None,
) -> Dict[str, Any]:
    """Build a metadata-only ranked/native interop shadow artifact."""

    readiness = _merge_unique(_list_or_empty(readiness_labels), REQUIRED_READINESS_LABELS)
    minor_followups = list(MINOR_FOLLOWUPS)

    artifact: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "helper_name": HELPER_NAME,
        "artifact_type": ARTIFACT_TYPE,
        "ranked_state_frame_summary": _dict_or_empty(ranked_state_frame_summary),
        "selected_candidate_metadata": _dict_or_empty(selected_candidate_metadata),
        "rejected_candidate_labels": _list_or_empty(rejected_candidate_labels),
        "ranking_label_summary": _dict_or_empty(ranking_label_summary),
        "final_answer_contract_metadata": _dict_or_empty(final_answer_contract_metadata),
        "native_reasoning_frame_metadata": _dict_or_empty(native_reasoning_frame_metadata),
        "native_draft_shape_metadata": _dict_or_empty(native_draft_shape_metadata),
        "native_self_check_metadata": _dict_or_empty(native_self_check_metadata),
        "native_assembly_metadata": _dict_or_empty(native_assembly_metadata),
        "provenance_constraints": _list_or_empty(provenance_constraints),
        "evidence_constraints": _list_or_empty(evidence_constraints),
        "safety_boundary_labels": _list_or_empty(safety_boundary_labels),
        "interop_notes": _list_or_empty(interop_notes),
        "readiness_labels": readiness,
        "minor_followups": minor_followups,
    }
    artifact.update({flag: False for flag in FALSE_SAFETY_FLAGS})
    return artifact


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


def validate_ranked_native_interop_shadow_artifact_v1(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Validate artifact safety without exposing offending content."""

    reason_labels: List[str] = []

    if not isinstance(artifact, dict):
        return {"valid": False, "safe_to_render": False, "reason_labels": ["artifact_not_dict"]}

    for field in REQUIRED_FIELDS:
        if field not in artifact:
            reason_labels.append(f"missing_required_field:{field}")

    if artifact.get("artifact_type") != ARTIFACT_TYPE:
        reason_labels.append("unexpected_artifact_type")
    if artifact.get("schema_version") != SCHEMA_VERSION:
        reason_labels.append("unexpected_schema_version")

    for flag in FALSE_SAFETY_FLAGS:
        if artifact.get(flag) is not False:
            reason_labels.append(f"required_false_flag_violation:{flag}")

    for flag in FORBIDDEN_TRUE_FLAGS:
        if artifact.get(flag) is True:
            reason_labels.append(f"forbidden_true_flag:{flag}")

    readiness = artifact.get("readiness_labels", [])
    if not isinstance(readiness, list):
        reason_labels.append("readiness_labels_not_list")
    else:
        for label in REQUIRED_READINESS_LABELS:
            if label not in readiness:
                reason_labels.append(f"missing_readiness_label:{label}")

    minor = artifact.get("minor_followups", [])
    if not isinstance(minor, list):
        reason_labels.append("minor_followups_not_list")
    else:
        for label in MINOR_FOLLOWUPS:
            if label not in minor:
                reason_labels.append(f"missing_minor_followup:{label}")

    for path, value in _walk(artifact):
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
            for marker in (
                "official benchmark",
                "turing-test pass",
                "turing test pass",
                "iq claim",
                "certification claim",
                "product-readiness claim",
                "product readiness claim",
                "consciousness claim",
                "sentience claim",
                "runtime ready",
                "runtime-ready",
                "occ is weslr",
                "openclaw is weslr",
            ):
                if marker in lowered:
                    reason_labels.append(f"forbidden_claim_marker:{marker.replace(' ', '_')}")
            if "final answer:" in lowered:
                reason_labels.append("forbidden_final_answer_text_marker")

        if isinstance(value, Number) and not isinstance(value, bool):
            lowered_path = path.lower()
            if any(fragment in lowered_path for fragment in ("official_score", "iq_score", "benchmark_score", "turing_score")):
                reason_labels.append(f"forbidden_numeric_official_score:{_safe_reason(path)}")

    # Stable de-duplication preserves order for deterministic output.
    deduped: List[str] = []
    for reason in reason_labels:
        if reason not in deduped:
            deduped.append(reason)

    valid = not deduped
    return {"valid": valid, "safe_to_render": valid, "reason_labels": deduped}


def summarize_ranked_native_interop_shadow_artifact_v1(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Return count/status/label metadata only."""

    validation = validate_ranked_native_interop_shadow_artifact_v1(artifact)
    return {
        "artifact_type": artifact.get("artifact_type") if isinstance(artifact, dict) else None,
        "valid": validation["valid"],
        "safe_to_render": validation["safe_to_render"],
        "ranked_metadata_present": bool(
            isinstance(artifact, dict)
            and (
                artifact.get("ranked_state_frame_summary")
                or artifact.get("selected_candidate_metadata")
                or artifact.get("ranking_label_summary")
            )
        ),
        "native_metadata_present": bool(
            isinstance(artifact, dict)
            and (
                artifact.get("native_reasoning_frame_metadata")
                or artifact.get("native_draft_shape_metadata")
                or artifact.get("native_self_check_metadata")
                or artifact.get("native_assembly_metadata")
            )
        ),
        "rejected_label_count": len(artifact.get("rejected_candidate_labels", [])) if isinstance(artifact, dict) else 0,
        "safety_boundary_label_count": len(artifact.get("safety_boundary_labels", [])) if isinstance(artifact, dict) else 0,
        "readiness_labels": copy.deepcopy(artifact.get("readiness_labels", [])) if isinstance(artifact, dict) else [],
        "minor_followups": copy.deepcopy(artifact.get("minor_followups", [])) if isinstance(artifact, dict) else [],
        "safety_flags": {flag: artifact.get(flag) for flag in FALSE_SAFETY_FLAGS} if isinstance(artifact, dict) else {},
    }


def render_ranked_native_interop_shadow_artifact_markdown_v1(artifact: Dict[str, Any]) -> str:
    """Render safe Markdown from metadata status only."""

    validation = validate_ranked_native_interop_shadow_artifact_v1(artifact)
    if not validation["valid"]:
        reasons = "\n".join(f"- `{reason}`" for reason in validation["reason_labels"])
        return (
            "# Ranked/Native Interop Shadow Artifact — BLOCKED\n\n"
            "## Validation Status\n"
            "- valid: `False`\n"
            "- safe_to_render: `False`\n\n"
            "## Safe Reason Labels\n"
            f"{reasons}\n\n"
            "Offending content is intentionally not rendered.\n"
        )

    summary = summarize_ranked_native_interop_shadow_artifact_v1(artifact)
    readiness = "\n".join(f"- `{label}`" for label in summary["readiness_labels"])
    followups = "\n".join(f"- `{label}`" for label in summary["minor_followups"])
    flags = "\n".join(f"- `{flag}`: `{value}`" for flag, value in summary["safety_flags"].items())
    return (
        "# Ranked/Native Interop Shadow Artifact\n\n"
        "## Artifact Status\n"
        f"- artifact_type: `{summary['artifact_type']}`\n"
        f"- valid: `{summary['valid']}`\n"
        f"- safe_to_render: `{summary['safe_to_render']}`\n"
        f"- ranked_metadata_present: `{summary['ranked_metadata_present']}`\n"
        f"- native_metadata_present: `{summary['native_metadata_present']}`\n\n"
        "## Constraints Summary\n"
        f"- rejected_label_count: `{summary['rejected_label_count']}`\n"
        f"- safety_boundary_label_count: `{summary['safety_boundary_label_count']}`\n\n"
        "## Readiness Labels\n"
        f"{readiness}\n\n"
        "## Minor Followups\n"
        f"{followups}\n\n"
        "## Safety Confirmation\n"
        f"{flags}\n"
        "- no runtime wiring\n"
        "- no final answer generation\n"
        "- no raw prompt/response retention\n"
        "- no official claims\n\n"
        "## Next Lane Recommendation\n"
        "`REVIEW_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_IMPLEMENTATION_V1`\n"
    )


def to_ranked_native_interop_shadow_artifact_json_safe_v1(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe deep copy, or an invalid wrapper for unsafe artifacts."""

    validation = validate_ranked_native_interop_shadow_artifact_v1(artifact)
    if not validation["valid"]:
        return {
            "valid": False,
            "safe_to_render": False,
            "reason_labels": copy.deepcopy(validation["reason_labels"]),
            "artifact_type": artifact.get("artifact_type") if isinstance(artifact, dict) else None,
        }
    return json.loads(json.dumps(artifact, sort_keys=True))


__all__ = [
    "build_ranked_native_interop_shadow_artifact_v1",
    "validate_ranked_native_interop_shadow_artifact_v1",
    "summarize_ranked_native_interop_shadow_artifact_v1",
    "render_ranked_native_interop_shadow_artifact_markdown_v1",
    "to_ranked_native_interop_shadow_artifact_json_safe_v1",
]
