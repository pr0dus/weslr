"""Artifact forward work plan helpers.

Metadata-only helper for operator review packets.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, List
import json

SCHEMA_NAME = "artifact_forward_work_plan"
SCHEMA_VERSION = "v1"

_ALLOWED_ARTIFACT_KINDS = {
    "design_doc",
    "review_doc",
    "implementation_result",
    "true_run_result",
    "true_run_plan",
    "sample_result",
    "source_selection_plan",
    "metadata_locator_result",
    "evidence_packet",
    "ontology_expansion_request",
    "oer_noop_record",
    "artifact_proposal",
    "unknown",
}
_ALLOWED_ARTIFACT_STATUS = {
    "ready_for_review",
    "reviewed_valid",
    "ready_for_owner_approval",
    "ready_for_implementation",
    "ready_for_true_run",
    "blocked",
    "needs_repair",
    "validation_incomplete",
    "pause_until_owner_approval",
    "unknown",
    "ready_for_design",
}
_ALLOWED_LANE_TYPES = {
    "review",
    "design",
    "implementation",
    "run",
    "repair",
    "context_alignment",
    "push_fetch_sync",
    "pause",
    "operator_decision",
    "unknown",
}
_FALSE_AUTHORITY_KEYS = [
    "runtime_wiring_authority",
    "chat_responder_edit_authority",
    "ui_voice_integration_authority",
    "provider_model_call_authority",
    "web_source_fetch_authority",
    "source_ingestion_authority",
    "database_write_authority",
    "memory_mutation_authority",
    "project_mutation_authority",
    "behavior_pack_promotion_authority",
    "public_claim_authority",
    "accepted_evidence_authority",
    "accepted_candidate_authority",
    "proposal_action_authority",
    "final_answer_authority",
    "ontology_auto_application_authority",
    "ontology_self_modification_authority",
]


def _base_authority_status() -> Dict[str, bool]:
    return {k: False for k in _FALSE_AUTHORITY_KEYS}


def _safe_text(value: Any) -> str:
    return "" if value is None else str(value)


def _contains_forbidden_language(text: str) -> bool:
    lowered = text.lower()
    banned = [
        "proof",
        "proven",
        "discovery claim",
        "public discovery",
        "final answer",
        "agi",
        "consciousness",
        "sentience",
        "source ingestion authority",
        "provider model authority",
        "runtime authority",
        "chat authority",
        "voice authority",
    ]
    return any(token in lowered for token in banned)


def build_artifact_forward_work_plan_v1(**packet: Any) -> Dict[str, Any]:
    result = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "plan_id": packet.get("plan_id", "artifact_forward_work_plan_v1"),
        "artifact_id": packet.get("artifact_id", "unknown"),
        "artifact_kind": packet.get("artifact_kind", "unknown"),
        "artifact_title": packet.get("artifact_title", ""),
        "artifact_source_path": packet.get("artifact_source_path", ""),
        "artifact_status": packet.get("artifact_status", "unknown"),
        "artifact_summary": packet.get("artifact_summary", ""),
        "interesting_result_summary": packet.get("interesting_result_summary", ""),
        "visible_gaps": list(packet.get("visible_gaps", [])),
        "blocked_actions": list(packet.get("blocked_actions", [])),
        "recommended_next_lanes": deepcopy(packet.get("recommended_next_lanes", [])),
        "recommended_first_lane": deepcopy(packet.get("recommended_first_lane", {})),
        "owner_approval_required": bool(packet.get("owner_approval_required", False)),
        "operator_review_required": bool(packet.get("operator_review_required", True)),
        "validation_plan": list(packet.get("validation_plan", [])),
        "protected_file_checks": list(packet.get("protected_file_checks", [])),
        "authority_status": _base_authority_status(),
        "safe_metadata_summary": packet.get("safe_metadata_summary", ""),
        "blocked_labels": list(packet.get("blocked_labels", [])),
        "final_judgment": packet.get("final_judgment", "unknown"),
    }
    authority = packet.get("authority_status") or {}
    for key in _FALSE_AUTHORITY_KEYS:
        if key in authority:
            result["authority_status"][key] = bool(authority[key])
    if not result["recommended_next_lanes"] and result["recommended_first_lane"]:
        result["recommended_next_lanes"] = [deepcopy(result["recommended_first_lane"])]
    return result


def validate_artifact_forward_work_plan_v1(packet: Dict[str, Any]) -> bool:
    required = [
        "schema_name",
        "schema_version",
        "plan_id",
        "artifact_id",
        "artifact_kind",
        "artifact_title",
        "artifact_source_path",
        "artifact_status",
        "artifact_summary",
        "interesting_result_summary",
        "visible_gaps",
        "blocked_actions",
        "recommended_next_lanes",
        "recommended_first_lane",
        "owner_approval_required",
        "operator_review_required",
        "validation_plan",
        "protected_file_checks",
        "authority_status",
        "safe_metadata_summary",
        "blocked_labels",
        "final_judgment",
    ]
    if any(k not in packet for k in required):
        return False
    if ".weslr" in _safe_text(packet.get("artifact_source_path")):
        return False
    if not packet.get("validation_plan") or not packet.get("protected_file_checks"):
        return False
    if not packet.get("final_judgment"):
        return False
    if packet.get("artifact_kind") not in _ALLOWED_ARTIFACT_KINDS:
        return False
    if packet.get("artifact_status") not in _ALLOWED_ARTIFACT_STATUS:
        return False
    text_fields = [
        _safe_text(packet.get("artifact_title")),
        _safe_text(packet.get("artifact_summary")),
        _safe_text(packet.get("interesting_result_summary")),
        _safe_text(packet.get("safe_metadata_summary")),
        _safe_text(packet.get("final_judgment")),
    ]
    if any(_contains_forbidden_language(field) for field in text_fields):
        return False
    authority = packet.get("authority_status") or {}
    for key in _FALSE_AUTHORITY_KEYS:
        if authority.get(key) is not False:
            return False
    lanes = packet.get("recommended_next_lanes") or []
    if not isinstance(lanes, list) or not lanes:
        return False
    for lane in lanes:
        if not isinstance(lane, dict):
            return False
        for field in [
            "lane_id", "lane_type", "lane_title", "why_recommended", "depends_on",
            "owner_approval_required", "operator_review_required", "blocked_until",
            "allowed_actions", "forbidden_actions", "validation_commands",
            "protected_file_checks", "expected_output_artifact", "final_judgment_options",
        ]:
            if field not in lane:
                return False
        if lane["lane_type"] not in _ALLOWED_LANE_TYPES:
            return False
        forbidden_actions = lane.get("forbidden_actions") or []
        if not forbidden_actions:
            return False
        if any(a in ("final_answer", "source_ingestion", "provider_model_call", "runtime_wiring", "chat_responder_edit", "ui_voice_integration") for a in forbidden_actions):
            pass
        else:
            return False
        if lane.get("owner_approval_required") is False and lane.get("lane_type") == "run":
            return False
        if lane.get("allowed_actions") and any(a in ("execute", "approve", "run", "ingest", "call_provider") for a in lane.get("allowed_actions", [])):
            return False
    if not packet.get("safe_metadata_summary"):
        return False
    return True


def summarize_artifact_forward_work_plan_v1(packet: Dict[str, Any]) -> str:
    return (
        f"{packet.get('artifact_kind', 'unknown')}:{packet.get('artifact_status', 'unknown')} "
        f"-> {packet.get('recommended_first_lane', {}).get('lane_id', 'none')} | "
        f"blocked={len(packet.get('blocked_actions', []))} gaps={len(packet.get('visible_gaps', []))}"
    )


def render_artifact_forward_work_plan_markdown_v1(packet: Dict[str, Any]) -> str:
    lane = packet.get("recommended_first_lane") or {}
    auth = packet.get("authority_status") or {}
    lines = [
        f"# {packet.get('artifact_title', 'Artifact Forward Work Plan')}",
        f"- Artifact kind: {packet.get('artifact_kind', 'unknown')}",
        f"- Artifact status: {packet.get('artifact_status', 'unknown')}",
        f"- Recommended next lane: {lane.get('lane_id', 'none')}",
        f"- Why: {lane.get('why_recommended', '')}",
        f"- Blocked actions: {', '.join(packet.get('blocked_actions', [])) or 'none'}",
        f"- Validation plan: {', '.join(packet.get('validation_plan', [])) or 'none'}",
        f"- Owner approval required: {packet.get('owner_approval_required', False)}",
        f"- Authority summary: {', '.join([k for k, v in auth.items() if v is False])}",
        f"- Final judgment: {packet.get('final_judgment', 'unknown')}",
    ]
    return "\n".join(lines)


def to_artifact_forward_work_plan_json_safe_v1(packet: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(json.dumps(packet, default=str))


def build_initial_artifact_forward_work_plan_examples_v1() -> List[Dict[str, Any]]:
    base_auth = _base_authority_status()
    examples: List[Dict[str, Any]] = []

    examples.append(build_artifact_forward_work_plan_v1(
        plan_id="artifact_forward_example_second_true_run_result",
        artifact_id="second_true_run_result_v1",
        artifact_kind="true_run_result",
        artifact_title="Reviewed second controlled true run result",
        artifact_source_path="docs/WESLR_SECOND_CONTROLLED_TRUE_RUN_AFTER_DISCOVERY_REGISTRY_REPAIR_RESULT_REVIEW_V1.md",
        artifact_status="reviewed_valid",
        artifact_summary="Reviewed valid metadata-only run result.",
        interesting_result_summary="Pipeline held boundaries and exposed sparse scout bucket population.",
        visible_gaps=[
            "sparse scout bucket population",
            "OER no-op builder follow-up",
            "richer metadata-only signal item shape",
        ],
        blocked_actions=["source_ingestion", "final_answer", "public_claim"],
        recommended_first_lane={
            "lane_id": "PLAN_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_V1",
            "lane_type": "design",
            "lane_title": "Plan third controlled true run on non-materials domain",
            "why_recommended": "Prepare a safer, richer non-materials follow-up.",
            "depends_on": ["reviewed_valid"],
            "owner_approval_required": True,
            "operator_review_required": True,
            "blocked_until": ["owner approval"],
            "allowed_actions": ["review", "design"],
            "forbidden_actions": ["execute", "run", "source_ingestion", "final_answer"],
            "validation_commands": ["git diff --check"],
            "protected_file_checks": ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
            "expected_output_artifact": "docs/WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_PLAN_V1.md",
            "final_judgment_options": ["ready_for_owner_approval"],
        },
        owner_approval_required=False,
        operator_review_required=True,
        validation_plan=["review summary", "check gaps"],
        protected_file_checks=["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
        safe_metadata_summary="Reviewed valid result with metadata-only boundaries and visible follow-up gaps.",
        blocked_labels=["no_execution_authority"],
        final_judgment="reviewed_valid",
        authority_status=base_auth,
    ))

    examples.append(build_artifact_forward_work_plan_v1(
        plan_id="artifact_forward_example_third_true_run_plan",
        artifact_id="third_true_run_plan_v1",
        artifact_kind="true_run_plan",
        artifact_title="Third controlled true run plan",
        artifact_source_path="docs/WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_PLAN_V1.md",
        artifact_status="ready_for_owner_approval",
        artifact_summary="Plan for a non-materials follow-up run.",
        interesting_result_summary="Energy systems is the primary domain.",
        visible_gaps=["awaiting owner approval"],
        blocked_actions=["run", "source_ingestion", "final_answer"],
        recommended_first_lane={
            "lane_id": "RUN_WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_V1",
            "lane_type": "run",
            "lane_title": "Run third controlled true run on non-materials domain",
            "why_recommended": "Execute only after explicit owner approval.",
            "depends_on": ["owner approval"],
            "owner_approval_required": True,
            "operator_review_required": True,
            "blocked_until": ["owner approval"],
            "allowed_actions": ["review"],
            "forbidden_actions": ["execute", "source_ingestion", "final_answer"],
            "validation_commands": ["git diff --check"],
            "protected_file_checks": ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
            "expected_output_artifact": "docs/WESLR_THIRD_CONTROLLED_TRUE_RUN_ON_NON_MATERIALS_DOMAIN_RESULT_V1.md",
            "final_judgment_options": ["ready_for_true_run"],
        },
        owner_approval_required=True,
        operator_review_required=True,
        validation_plan=["confirm owner approval", "confirm no ingestion"],
        protected_file_checks=["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
        safe_metadata_summary="Plan remains metadata-only and blocked until owner approval.",
        blocked_labels=["no_source_ingestion", "no_execution_authority"],
        final_judgment="ready_for_owner_approval",
        authority_status=base_auth,
    ))

    examples.append(build_artifact_forward_work_plan_v1(
        plan_id="artifact_forward_example_oer_noop",
        artifact_id="oer_noop_record_v1",
        artifact_kind="oer_noop_record",
        artifact_title="OER no-op builder follow-up",
        artifact_source_path="docs/WESLR_OER_NOOP_RECORD_BUILDER_PLAN_V1.md",
        artifact_status="ready_for_design",
        artifact_summary="Design follow-up for a no-op OER record.",
        interesting_result_summary="No ontology auto-application authority.",
        visible_gaps=["no-op OER record structure not yet designed"],
        blocked_actions=["ontology_auto_application", "source_ingestion", "final_answer"],
        recommended_first_lane={
            "lane_id": "DESIGN_WESLR_OER_NO_OP_RECORD_BUILDER_V1",
            "lane_type": "design",
            "lane_title": "Design OER no-op record builder",
            "why_recommended": "Keep OER as audit-only metadata.",
            "depends_on": ["reviewed_valid"],
            "owner_approval_required": False,
            "operator_review_required": True,
            "blocked_until": ["design review"],
            "allowed_actions": ["design", "review"],
            "forbidden_actions": ["execute", "source_ingestion", "ontology_auto_application", "final_answer"],
            "validation_commands": ["git diff --check"],
            "protected_file_checks": ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
            "expected_output_artifact": "docs/WESLR_OER_NO_OP_RECORD_BUILDER_PLAN_V1.md",
            "final_judgment_options": ["ready_for_design"],
        },
        owner_approval_required=False,
        operator_review_required=True,
        validation_plan=["confirm audit-only posture"],
        protected_file_checks=["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
        safe_metadata_summary="OER follow-up remains audit-only and non-authoritative.",
        blocked_labels=["no_ontology_auto_application"],
        final_judgment="ready_for_design",
        authority_status=base_auth,
    ))

    examples.append(build_artifact_forward_work_plan_v1(
        plan_id="artifact_forward_example_richer_signal_shape",
        artifact_id="richer_signal_shape_v1",
        artifact_kind="design_doc",
        artifact_title="Richer metadata-only signal item shape follow-up",
        artifact_source_path="docs/WESLR_RICHER_METADATA_ONLY_SIGNAL_ITEM_SHAPE_V1.md",
        artifact_status="ready_for_design",
        artifact_summary="Design richer metadata-only signal item shape.",
        interesting_result_summary="Better signal buckets without ingestion.",
        visible_gaps=["generic signal descriptors produced sparse scout buckets"],
        blocked_actions=["source_ingestion", "snippets_as_evidence", "final_answer"],
        recommended_first_lane={
            "lane_id": "DESIGN_WESLR_RICHER_METADATA_ONLY_SIGNAL_ITEM_SHAPE_V1",
            "lane_type": "design",
            "lane_title": "Design richer metadata-only signal item shape",
            "why_recommended": "Increase metadata richness while preserving no-ingestion boundaries.",
            "depends_on": ["scout gap review"],
            "owner_approval_required": False,
            "operator_review_required": True,
            "blocked_until": ["design review"],
            "allowed_actions": ["design", "review"],
            "forbidden_actions": ["execute", "source_ingestion", "snippets_as_evidence", "final_answer"],
            "validation_commands": ["git diff --check"],
            "protected_file_checks": ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
            "expected_output_artifact": "docs/WESLR_RICHER_METADATA_ONLY_SIGNAL_ITEM_SHAPE_V1.md",
            "final_judgment_options": ["ready_for_design"],
        },
        owner_approval_required=False,
        operator_review_required=True,
        validation_plan=["confirm source ingestion remains blocked"],
        protected_file_checks=["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
        safe_metadata_summary="Signal-shape follow-up is metadata-only and rejects snippets as evidence.",
        blocked_labels=["no_source_ingestion", "no_snippets_as_evidence"],
        final_judgment="ready_for_design",
        authority_status=base_auth,
    ))

    unsafe = build_artifact_forward_work_plan_v1(
        plan_id="artifact_forward_example_unsafe",
        artifact_id="unsafe_v1",
        artifact_kind="unknown",
        artifact_title="Unsafe artifact",
        artifact_source_path="docs/unsafe.md",
        artifact_status="blocked",
        artifact_summary="This is a proof of AGI and final answer authority.",
        interesting_result_summary="public discovery claim",
        visible_gaps=[],
        blocked_actions=["source_ingestion", "final_answer"],
        recommended_first_lane={
            "lane_id": "BLOCKED_UNSAFE",
            "lane_type": "unknown",
            "lane_title": "Blocked unsafe artifact",
            "why_recommended": "Unsafe claim language.",
            "depends_on": [],
            "owner_approval_required": False,
            "operator_review_required": True,
            "blocked_until": ["review"],
            "allowed_actions": ["review"],
            "forbidden_actions": ["execute", "final_answer", "source_ingestion"],
            "validation_commands": ["git diff --check"],
            "protected_file_checks": ["weslr/chat_responder.py"],
            "expected_output_artifact": "docs/unsafe.md",
            "final_judgment_options": ["blocked"],
        },
        owner_approval_required=False,
        operator_review_required=True,
        validation_plan=["review only"],
        protected_file_checks=["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"],
        safe_metadata_summary="Blocked unsafe artifact.",
        blocked_labels=["unsafe_claim_language"],
        final_judgment="blocked",
        authority_status=base_auth,
    )
    unsafe["authority_status"]["public_claim_authority"] = True
    examples.append(unsafe)
    return examples
