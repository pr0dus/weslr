"""Metadata-only project-start chat-flow helpers v1."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

from weslr.first_tool_lanes_contracts import build_first_tool_lane_contract_v1, validate_first_tool_lane_contract_v1
from weslr.memory_state_model_helpers import build_memory_state_item_v1, validate_memory_state_item_v1
from weslr.project_state_model_helpers import build_project_state_item_v1, validate_project_state_item_v1
from weslr.state_and_continuity_mvp_helpers import build_state_continuity_item_v1, validate_state_continuity_item_v1

SCHEMA_VERSION_V1 = "project_start_chat_flow_metadata_v1"
FLOW_TYPE_V1 = "project_start_chat_flow_packet_v1"

_ALLOWED_INTENT_CLASSES_V1 = (
    "new_project_start",
    "continue_existing_project",
    "project_clarification",
    "project_planning_request",
    "project_gap_review_request",
    "memory_update_proposal_request",
    "tool_action_request",
    "unknown_or_ambiguous",
)

_REQUIRED_MISSING_PROJECT_FIELDS_V1 = (
    "goal",
    "scope",
    "constraints",
    "success_criteria",
    "known_inputs",
    "desired_output",
    "deadline_or_priority",
    "approval_needed",
    "privacy_sensitivity",
    "tool_use_expectation",
)

_DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "chat_" "responder_authority",
    "final_answer_generation_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "project_state_mutation_authority",
    "memory_mutation_authority",
    "tool_execution_authority",
    "external_action_authority",
    "hidden_memory_authority",
    "hidden_project_state_authority",
    "silent_personalization_authority",
    "cross_user_leakage_authority",
    "public_product_readiness_authority",
)

_ALLOWED_NEXT_STEPS_V1 = (
    "ask_clarifying_questions",
    "await_user_confirmation",
    "await_operator_approval",
    "propose_project_plan_metadata",
    "propose_memory_update_metadata",
    "surface_gap_review_metadata",
    "propose_tool_lane_contract_candidate",
    "return_project_start_summary_metadata",
)

_PRIVATE_MECHANISM_MARKERS = (
    "unknown engine",
    "chat responder",
    "runtime wiring",
    "hidden memory",
    "fake continuity",
    "silent personalization",
)


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return _compact_text(str(value), default=default)


def _has_text(value: Any) -> bool:
    return bool(_compact_text(value, default=""))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return copy.deepcopy(value)
    if isinstance(value, tuple):
        return list(copy.deepcopy(value))
    if isinstance(value, set):
        return sorted(copy.deepcopy(value), key=repr)
    return [copy.deepcopy(value)]


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _stable_marker(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _normalize_denied_authority(value: Any = None) -> dict[str, Any]:
    denied = {field: False for field in _DENIED_AUTHORITY_FIELDS_V1}
    if isinstance(value, Mapping):
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field in value:
                denied[field] = False
    return denied


def _default_next_step(intent_class: str) -> str:
    return {
        "new_project_start": "propose_project_plan_metadata",
        "continue_existing_project": "return_project_start_summary_metadata",
        "project_clarification": "ask_clarifying_questions",
        "project_planning_request": "propose_project_plan_metadata",
        "project_gap_review_request": "surface_gap_review_metadata",
        "memory_update_proposal_request": "propose_memory_update_metadata",
        "tool_action_request": "propose_tool_lane_contract_candidate",
        "unknown_or_ambiguous": "ask_clarifying_questions",
    }.get(intent_class, "ask_clarifying_questions")


def _intent_scores(request_text: str, project_id: str, goal: str, scope: str, desired_output: str, tool_use_expectation: str) -> dict[str, int]:
    text = " ".join((request_text, project_id, goal, scope, desired_output, tool_use_expectation)).lower()
    scores = {
        "new_project_start": 0,
        "continue_existing_project": 0,
        "project_clarification": 0,
        "project_planning_request": 0,
        "project_gap_review_request": 0,
        "memory_update_proposal_request": 0,
        "tool_action_request": 0,
        "unknown_or_ambiguous": 0,
    }
    for marker in ("start a project", "new project", "begin project", "create a project", "help me start", "project start", "launch project"):
        if marker in text:
            scores["new_project_start"] += 2
    for marker in ("continue", "resume", "pick up", "existing project", "that project", "ongoing project"):
        if marker in text:
            scores["continue_existing_project"] += 2
    for marker in ("clarify", "clarification", "need details", "what do you need", "more info", "missing info", "questions"):
        if marker in text:
            scores["project_clarification"] += 2
    for marker in ("plan", "roadmap", "checklist", "steps", "planning", "structure"):
        if marker in text:
            scores["project_planning_request"] += 1
    for marker in ("gap review", "review gaps", "missing pieces", "friction", "blind spots", "what's missing", "what is missing"):
        if marker in text:
            scores["project_gap_review_request"] += 2
    for marker in ("remember", "save this", "update memory", "memory update", "note this", "keep this in memory"):
        if marker in text:
            scores["memory_update_proposal_request"] += 2
    for marker in ("run", "execute", "tool", "send", "post", "deploy", "wire", "do it", "make it happen"):
        if marker in text:
            scores["tool_action_request"] += 1
    if project_id:
        scores["continue_existing_project"] += 1
    if goal:
        scores["new_project_start"] += 1
        scores["project_planning_request"] += 1
    if desired_output:
        scores["project_planning_request"] += 1
    if scope:
        scores["project_gap_review_request"] += 1
    if tool_use_expectation:
        scores["tool_action_request"] += 1
    return scores


def _detect_private_mechanism_text(*values: Any) -> bool:
    text = " ".join(_compact_text(value, default="").lower() for value in values)
    return any(marker in text for marker in _PRIVATE_MECHANISM_MARKERS)


def _build_missing_project_fields(payload: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in _REQUIRED_MISSING_PROJECT_FIELDS_V1:
        value = payload.get(field)
        if field in {"approval_needed", "privacy_sensitivity"}:
            if value is None or not _has_text(value):
                missing.append(field)
        elif not _has_text(value):
            missing.append(field)
    return missing


def _build_clarification_questions(missing_fields: list[str], intent_class: str) -> list[str]:
    questions = []
    mapping = {
        "goal": "What is the goal?",
        "scope": "What is the scope?",
        "constraints": "What constraints should I respect?",
        "success_criteria": "How will success be recognized?",
        "known_inputs": "What inputs do you already have?",
        "desired_output": "What output do you want?",
        "deadline_or_priority": "What deadline or priority should I use?",
        "approval_needed": "Does this need approval?",
        "privacy_sensitivity": "Does this involve sensitive or personal data?",
        "tool_use_expectation": "Should this stay metadata-only, or does it point to a future tool lane?",
    }
    for field in missing_fields:
        question = mapping.get(field)
        if question:
            questions.append(question)
    if intent_class == "continue_existing_project" and "project_id" in missing_fields:
        questions.append("Which existing project should I continue?")
    if intent_class == "unknown_or_ambiguous":
        questions.append("Do you want to start a new project, continue an existing one, or clarify the request?")
    return questions


def _build_user_visible_status_phrase(intent_class: str, pending_approval: bool, requires_user_confirmation: bool, requires_operator_approval: bool, blocked_reason: str, missing_project_fields: list[str]) -> str:
    if blocked_reason:
        return f"I can only treat this as metadata right now because {blocked_reason}."
    if intent_class == "new_project_start":
        if missing_project_fields:
            return "I can help start a new project, but I need a few details first."
        return "This looks like a new project start metadata request."
    if intent_class == "continue_existing_project":
        if missing_project_fields:
            return "I can continue the project metadata, but I need the project identifier first."
        return "This looks like a continuation of an existing project metadata flow."
    if intent_class == "project_clarification":
        return "I need a few more details before I can shape the project metadata."
    if intent_class == "project_planning_request":
        return "This looks like a project planning metadata request."
    if intent_class == "project_gap_review_request":
        return "This looks like a project gap review metadata request."
    if intent_class == "memory_update_proposal_request":
        return "This looks like a memory update proposal metadata request."
    if intent_class == "tool_action_request":
        return "This looks like a tool-lane metadata request, not an executed tool action."
    if pending_approval or requires_user_confirmation or requires_operator_approval:
        return "I can keep this as metadata, but confirmation is needed before anything deeper."
    return "I can only treat this as project-start metadata until the request is clearer."


def _build_operator_visible_summary(intent_class: str, missing_project_fields: list[str], risk_flags: list[str], requires_user_confirmation: bool, requires_operator_approval: bool) -> str:
    parts = [f"intent={intent_class}"]
    if missing_project_fields:
        parts.append(f"missing={','.join(missing_project_fields)}")
    if risk_flags:
        parts.append(f"risk_flags={','.join(risk_flags)}")
    if requires_user_confirmation:
        parts.append("user_confirmation_required")
    if requires_operator_approval:
        parts.append("operator_approval_required")
    return " | ".join(parts)


def _build_denied_authority() -> dict[str, Any]:
    return _normalize_denied_authority()


def classify_project_start_intent_v1(
    *,
    requested_action: Any = None,
    project_id: Any = None,
    goal: Any = None,
    scope: Any = None,
    desired_output: Any = None,
    tool_use_expectation: Any = None,
    privacy_sensitivity: Any = None,
    approval_needed: Any = None,
    source_type: Any = None,
    source_ref: Any = None,
    owner_user_scope: Any = None,
    tenant_account_scope: Any = None,
) -> dict[str, Any]:
    request_text = _compact_text(requested_action)
    project_id_text = _compact_text(project_id)
    goal_text = _compact_text(goal)
    scope_text = _compact_text(scope)
    desired_output_text = _compact_text(desired_output)
    tool_text = _compact_text(tool_use_expectation)
    scores = _intent_scores(request_text, project_id_text, goal_text, scope_text, desired_output_text, tool_text)
    ordered = sorted(scores.items(), key=lambda item: (item[1], item[0]), reverse=True)
    top_intent, top_score = ordered[0]
    second_score = ordered[1][1] if len(ordered) > 1 else 0
    if top_score <= 0:
        top_intent = "unknown_or_ambiguous"
    elif top_score == second_score and top_intent not in {"continue_existing_project", "project_clarification"}:
        top_intent = "unknown_or_ambiguous"

    missing_project_fields = _build_missing_project_fields(
        {
            "goal": goal,
            "scope": scope,
            "constraints": None,
            "success_criteria": None,
            "known_inputs": None,
            "desired_output": desired_output,
            "deadline_or_priority": None,
            "approval_needed": approval_needed,
            "privacy_sensitivity": privacy_sensitivity,
            "tool_use_expectation": tool_use_expectation,
        }
    )
    clarification_questions = _build_clarification_questions(missing_project_fields, top_intent)
    if top_intent == "continue_existing_project" and not project_id_text:
        clarification_questions.append("Which existing project should I continue?")
    risk_flags: list[str] = []
    if _detect_private_mechanism_text(request_text, goal_text, desired_output_text, tool_text):
        risk_flags.append("user_visible_phrase_must_stay_mechanism_neutral")
    if _has_text(privacy_sensitivity) and _compact_text(privacy_sensitivity).lower() in {"true", "yes", "sensitive", "private", "personal"}:
        risk_flags.append("privacy_sensitive")
    if top_intent == "project_gap_review_request":
        risk_flags.append("deeper_analysis_requires_explicit_user_approval")
    if top_intent == "tool_action_request":
        risk_flags.append("tool_request_is_metadata_only")
    if top_intent == "memory_update_proposal_request":
        risk_flags.append("memory_update_remains_proposal")

    requires_user_confirmation = bool(risk_flags) or top_intent in {"project_clarification", "project_gap_review_request", "memory_update_proposal_request", "unknown_or_ambiguous"}
    if _compact_text(approval_needed).lower() in {"yes", "true", "required", "needs approval"}:
        requires_user_confirmation = True
    requires_operator_approval = False
    if top_intent == "tool_action_request":
        requires_operator_approval = True
    if _compact_text(tenant_account_scope).lower() in {"shared", "system", "tenant-wide", "account-wide"}:
        requires_operator_approval = True
    if _compact_text(owner_user_scope).lower() in {"shared", "system", "cross-user"}:
        requires_operator_approval = True
    if _compact_text(privacy_sensitivity).lower() in {"high", "sensitive", "private", "personal"}:
        requires_operator_approval = True
    if top_intent == "project_gap_review_request":
        requires_operator_approval = True

    pending_approval = requires_user_confirmation or requires_operator_approval
    blocked_reason = ""
    if top_intent == "continue_existing_project" and not project_id_text:
        blocked_reason = "continue_existing_project requires project_id or clarification"
    elif top_intent == "unknown_or_ambiguous":
        blocked_reason = "request is ambiguous and needs clarification metadata"
    elif requires_operator_approval and top_intent == "tool_action_request":
        blocked_reason = "tool action remains a metadata-only contract candidate"
    elif _detect_private_mechanism_text(request_text, goal_text, desired_output_text, tool_text):
        blocked_reason = "user-visible wording must remain mechanism-neutral"

    allowed_next_step = _default_next_step(top_intent)
    if missing_project_fields:
        allowed_next_step = "ask_clarifying_questions"
    if blocked_reason and top_intent == "tool_action_request":
        allowed_next_step = "propose_tool_lane_contract_candidate"
    if top_intent == "project_gap_review_request" and not blocked_reason:
        allowed_next_step = "surface_gap_review_metadata"

    return {
        "classification_schema": "project_start_chat_flow_intent_v1",
        "intent_class": top_intent,
        "confidence": "high" if top_score >= 3 else "medium" if top_score > 0 else "low",
        "matched_rule": top_intent if top_intent != "unknown_or_ambiguous" else "ambiguous_or_low_signal",
        "missing_project_fields": missing_project_fields,
        "clarification_questions": clarification_questions,
        "risk_flags": risk_flags,
        "blocked_reason": blocked_reason,
        "pending_approval": pending_approval,
        "requires_user_confirmation": requires_user_confirmation,
        "requires_operator_approval": requires_operator_approval,
        "allowed_next_step": allowed_next_step,
        "source_type": _compact_text(source_type),
        "source_ref": _compact_text(source_ref),
    }


def build_project_start_clarification_prompt_metadata_v1(missing_project_fields: Any, intent_class: Any = "unknown_or_ambiguous") -> list[str]:
    fields = [field for field in _listify(missing_project_fields) if _has_text(field)]
    return _build_clarification_questions(fields, _compact_text(intent_class, default="unknown_or_ambiguous"))


def build_project_start_status_phrase_metadata_v1(
    intent_class: Any,
    *,
    pending_approval: Any = False,
    requires_user_confirmation: Any = False,
    requires_operator_approval: Any = False,
    blocked_reason: Any = "",
    missing_project_fields: Any = None,
) -> str:
    return _build_user_visible_status_phrase(
        _compact_text(intent_class, default="unknown_or_ambiguous"),
        bool(pending_approval),
        bool(requires_user_confirmation),
        bool(requires_operator_approval),
        _compact_text(blocked_reason),
        [field for field in _listify(missing_project_fields) if _has_text(field)],
    )


def build_project_start_chat_flow_packet_v1(
    *,
    requested_action: Any = None,
    owner_user_scope: Any = "",
    tenant_account_scope: Any = "",
    project_id: Any = "",
    session_id: Any = "",
    source_type: Any = "synthetic",
    source_ref: Any = None,
    goal: Any = None,
    scope: Any = None,
    constraints: Any = None,
    success_criteria: Any = None,
    known_inputs: Any = None,
    desired_output: Any = None,
    deadline_or_priority: Any = None,
    approval_needed: Any = None,
    privacy_sensitivity: Any = None,
    tool_use_expectation: Any = None,
    project_state_candidate: Any = None,
    memory_state_candidates: Any = None,
    continuity_state_items: Any = None,
    tool_lane_contract_candidates: Any = None,
    limitations: Any = None,
    denied_authority: Any = None,
) -> dict[str, Any]:
    owner_text = _compact_text(owner_user_scope)
    tenant_text = _compact_text(tenant_account_scope)
    project_text = _compact_text(project_id)
    session_text = _compact_text(session_id)
    source_type_text = _compact_text(source_type, default="synthetic")
    source_ref_text = _compact_text(source_ref)
    if not source_ref_text:
        source_ref_text = _stable_marker("project_start_source", {"requested_action": _compact_text(requested_action), "owner": owner_text, "tenant": tenant_text, "project": project_text, "session": session_text})

    classification = classify_project_start_intent_v1(
        requested_action=requested_action,
        project_id=project_id,
        goal=goal,
        scope=scope,
        desired_output=desired_output,
        tool_use_expectation=tool_use_expectation,
        privacy_sensitivity=privacy_sensitivity,
        approval_needed=approval_needed,
        source_type=source_type_text,
        source_ref=source_ref_text,
        owner_user_scope=owner_text,
        tenant_account_scope=tenant_text,
    )
    intent_class = classification["intent_class"]
    missing_project_fields = classification["missing_project_fields"]
    clarification_questions = classification["clarification_questions"]
    risk_flags = classification["risk_flags"]
    blocked_reason = classification["blocked_reason"]
    pending_approval = bool(classification["pending_approval"])
    requires_user_confirmation = bool(classification["requires_user_confirmation"])
    requires_operator_approval = bool(classification["requires_operator_approval"])
    allowed_next_step = classification["allowed_next_step"]

    user_visible_status_phrase = build_project_start_status_phrase_metadata_v1(
        intent_class,
        pending_approval=pending_approval,
        requires_user_confirmation=requires_user_confirmation,
        requires_operator_approval=requires_operator_approval,
        blocked_reason=blocked_reason,
        missing_project_fields=missing_project_fields,
    )
    operator_visible_summary = _build_operator_visible_summary(intent_class, missing_project_fields, risk_flags, requires_user_confirmation, requires_operator_approval)

    if not project_text and intent_class != "continue_existing_project":
        project_text = _stable_marker("project_candidate", {"requested_action": _compact_text(requested_action), "goal": _compact_text(goal), "intent": intent_class})
    if not session_text:
        session_text = _stable_marker("session_candidate", {"requested_action": _compact_text(requested_action), "project": project_text, "intent": intent_class})

    project_phase = "clarification" if missing_project_fields else "intake"
    if intent_class == "project_planning_request":
        project_phase = "planning"
    elif intent_class == "project_gap_review_request":
        project_phase = "review"
    elif intent_class == "continue_existing_project":
        project_phase = "planning"

    project_status = "pending_approval" if pending_approval else "proposed"
    if intent_class == "tool_action_request":
        project_status = "proposed"
    if intent_class == "memory_update_proposal_request":
        project_status = "proposed"

    project_state_candidate_out = project_state_candidate
    if project_state_candidate_out is None:
        project_state_candidate_out = build_project_state_item_v1(
            project_id=project_text,
            item_id=_stable_marker("project_state_item", {"flow": source_ref_text, "intent": intent_class}),
            owner_user_scope=owner_text,
            tenant_account_scope=tenant_text,
            session_id=session_text,
            project_status=project_status,
            project_phase=project_phase,
            state_kind="project_context",
            title=_compact_text(requested_action, default="project start metadata"),
            summary=user_visible_status_phrase,
            goal=_compact_text(goal),
            open_questions=clarification_questions,
            constraints=_listify(constraints),
            decisions=[],
            tasks=[],
            blocked_items=[],
            linked_memory_refs=[],
            linked_artifact_refs=[],
            linked_support_refs=[],
            source_type=f"{source_type_text}_project_start_candidate",
            source_ref=source_ref_text,
            visibility="project_scoped",
            correction_path="review_and_refresh",
            stale=False,
            contradicted=False,
            invalidated=False,
            pending_approval=pending_approval,
            blocked_reason=blocked_reason,
            audit_note=operator_visible_summary,
            denied_authority=_build_denied_authority(),
        )

    memory_candidates_out = _listify(memory_state_candidates)
    if not memory_candidates_out and (intent_class in {"memory_update_proposal_request", "new_project_start", "project_planning_request"} or _has_text(goal) or _has_text(desired_output)):
        memory_candidates_out = [
            build_memory_state_item_v1(
                memory_id=_stable_marker("memory_candidate", {"flow": source_ref_text, "intent": intent_class}),
                memory_type="project_context",
                scope="project_scoped" if project_text else "session_only",
                owner_user_scope=owner_text,
                tenant_account_scope=tenant_text,
                project_id=project_text,
                session_id=session_text,
                status="proposed",
                source_type=f"{source_type_text}_memory_candidate",
                source_ref=source_ref_text,
                evidence_count=1,
                confidence_level="uncertain",
                visibility="project_scoped" if project_text else "session_only",
                correction_path="review_or_refresh",
                export_relevance=False,
                deletion_relevance=False,
                revocation_relevance=False,
                stale=False,
                contradicted=False,
                invalidated=False,
                pending_approval=True,
                blocked_reason=blocked_reason,
                user_visible_summary=user_visible_status_phrase,
                operator_visible_summary=operator_visible_summary,
                audit_note=operator_visible_summary,
            )
        ]

    continuity_items_out = _listify(continuity_state_items)
    if not continuity_items_out:
        continuity_items_out = [
            build_state_continuity_item_v1(
                item_id=_stable_marker("continuity_item", {"flow": source_ref_text, "intent": intent_class}),
                category="project_state",
                scope="project_scoped" if project_text else "session_only",
                owner_user_scope=owner_text,
                tenant_account_scope=tenant_text,
                project_id=project_text,
                session_id=session_text,
                status="proposed" if not pending_approval else "pending_approval",
                source_type=f"{source_type_text}_continuity_candidate",
                source_ref=source_ref_text,
                evidence_count=1,
                confidence_level="uncertain",
                visibility="project_scoped" if project_text else "session_only",
                update_authority="metadata_only",
                correction_path="review_and_refresh",
                user_visible_summary=user_visible_status_phrase,
                operator_visible_summary=operator_visible_summary,
                stale=False,
                contradicted=False,
                invalidated=False,
                pending_approval=pending_approval,
                blocked_reason=blocked_reason,
                audit_note=operator_visible_summary,
                denied_authority=_build_denied_authority(),
            )
        ]

    lane_candidates = _listify(tool_lane_contract_candidates)
    if not lane_candidates:
        lane_text = _compact_text(requested_action, default="project start metadata")
        candidate_lane_id = {
            "new_project_start": "project_plan_checklist",
            "continue_existing_project": "project_plan_checklist",
            "project_clarification": "project_plan_checklist",
            "project_planning_request": "project_plan_checklist",
            "project_gap_review_request": "safe_internal_report_generation",
            "memory_update_proposal_request": "scoped_memory_project_update_proposal",
            "tool_action_request": "draft_artifact_creation",
            "unknown_or_ambiguous": "project_plan_checklist",
        }.get(intent_class, "project_plan_checklist")
        lane_candidates = [
            build_first_tool_lane_contract_v1(
                candidate_lane_id,
                lane_id=candidate_lane_id,
                project_id=project_text or "project_candidate",
                memory_reference_ids=[source_ref_text],
                owner_user_scope=owner_text or "self",
                tenant_account_scope=tenant_text or "self",
                requested_action=lane_text,
            )
        ]

    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "flow_id": _stable_marker("flow", {"requested_action": _compact_text(requested_action), "source_ref": source_ref_text, "intent": intent_class}),
        "flow_type": FLOW_TYPE_V1,
        "intent_class": intent_class,
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "project_id": project_text,
        "session_id": session_text,
        "source_type": source_type_text,
        "source_ref": source_ref_text,
        "user_visible_status_phrase": user_visible_status_phrase,
        "operator_visible_summary": operator_visible_summary,
        "project_state_candidate": _json_safe(project_state_candidate_out),
        "memory_state_candidates": _json_safe(memory_candidates_out),
        "continuity_state_items": _json_safe(continuity_items_out),
        "tool_lane_contract_candidates": _json_safe(lane_candidates),
        "missing_project_fields": _json_safe(missing_project_fields),
        "clarification_questions": _json_safe(clarification_questions),
        "risk_flags": _json_safe(risk_flags),
        "blocked_reason": blocked_reason,
        "pending_approval": pending_approval,
        "requires_user_confirmation": requires_user_confirmation,
        "requires_operator_approval": requires_operator_approval,
        "allowed_next_step": allowed_next_step,
        "limitations": _json_safe(_listify(limitations)),
        "denied_authority": _build_denied_authority() if denied_authority is None else _normalize_denied_authority(denied_authority),
    }
    return _json_safe(packet)


def validate_project_start_chat_flow_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        violations.append("packet must be a mapping")
        return {"valid": False, "violation_count": len(violations), "violations": violations, "classification": {"intent_class": "unknown_or_ambiguous", "risk": "blocked"}}

    packet = _json_safe(copy.deepcopy(packet))
    required_fields = (
        "schema_version",
        "flow_id",
        "flow_type",
        "intent_class",
        "owner_user_scope",
        "tenant_account_scope",
        "project_id",
        "session_id",
        "source_type",
        "source_ref",
        "user_visible_status_phrase",
        "operator_visible_summary",
        "project_state_candidate",
        "memory_state_candidates",
        "continuity_state_items",
        "tool_lane_contract_candidates",
        "missing_project_fields",
        "clarification_questions",
        "risk_flags",
        "blocked_reason",
        "pending_approval",
        "requires_user_confirmation",
        "requires_operator_approval",
        "allowed_next_step",
        "denied_authority",
        "limitations",
    )
    for field in required_fields:
        if field not in packet:
            violations.append(f"missing field: {field}")

    if _compact_text(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")
    if _compact_text(packet.get("flow_type")) != FLOW_TYPE_V1:
        violations.append("flow_type mismatch")
    intent_class = _compact_text(packet.get("intent_class"))
    if intent_class not in _ALLOWED_INTENT_CLASSES_V1:
        violations.append(f"unknown intent class: {intent_class or '<blank>'}")
    if not _has_text(packet.get("flow_id")):
        violations.append("flow_id missing or blank")
    if not _has_text(packet.get("owner_user_scope")):
        violations.append("owner_user_scope missing or blank")
    if not _has_text(packet.get("tenant_account_scope")):
        violations.append("tenant_account_scope missing or blank")
    if not _has_text(packet.get("source_type")):
        violations.append("source_type missing or blank")
    if not _has_text(packet.get("source_ref")):
        violations.append("source_ref missing or blank")
    if not _has_text(packet.get("user_visible_status_phrase")):
        violations.append("user_visible_status_phrase missing or blank")
    if not _has_text(packet.get("operator_visible_summary")):
        violations.append("operator_visible_summary missing or blank")
    if not isinstance(packet.get("project_state_candidate"), Mapping):
        violations.append("project_state_candidate must be a mapping")
    if not isinstance(packet.get("memory_state_candidates"), list):
        violations.append("memory_state_candidates must be a list")
    if not isinstance(packet.get("continuity_state_items"), list):
        violations.append("continuity_state_items must be a list")
    if not isinstance(packet.get("tool_lane_contract_candidates"), list):
        violations.append("tool_lane_contract_candidates must be a list")
    if not isinstance(packet.get("missing_project_fields"), list):
        violations.append("missing_project_fields must be a list")
    if not isinstance(packet.get("clarification_questions"), list):
        violations.append("clarification_questions must be a list")
    if not isinstance(packet.get("risk_flags"), list):
        violations.append("risk_flags must be a list")
    if not isinstance(packet.get("limitations"), list):
        violations.append("limitations must be a list")
    if not isinstance(packet.get("pending_approval"), bool):
        violations.append("pending_approval must be a boolean")
    if not isinstance(packet.get("requires_user_confirmation"), bool):
        violations.append("requires_user_confirmation must be a boolean")
    if not isinstance(packet.get("requires_operator_approval"), bool):
        violations.append("requires_operator_approval must be a boolean")
    if _compact_text(packet.get("allowed_next_step")) not in _ALLOWED_NEXT_STEPS_V1:
        violations.append("allowed_next_step must be metadata-approved")
    if _detect_private_mechanism_text(packet.get("user_visible_status_phrase"), packet.get("operator_visible_summary")):
        violations.append("user-visible wording must stay mechanism-neutral")
    if "Unknown Engine" in _compact_text(packet.get("user_visible_status_phrase")):
        violations.append("user-visible wording must not mention Unknown Engine")

    if intent_class == "continue_existing_project" and not _has_text(packet.get("project_id")) and not packet.get("clarification_questions"):
        violations.append("continue_existing_project requires project_id or clarification")
    if intent_class == "unknown_or_ambiguous" and not packet.get("clarification_questions"):
        violations.append("unknown_or_ambiguous intent must surface clarification metadata")
    if intent_class == "new_project_start" and not _has_text(packet.get("project_id")) and not packet.get("clarification_questions"):
        violations.append("new_project_start must provide candidate project metadata")
    if packet.get("requires_user_confirmation") and intent_class not in {"new_project_start", "continue_existing_project", "project_clarification", "project_planning_request", "project_gap_review_request", "memory_update_proposal_request", "tool_action_request", "unknown_or_ambiguous"}:
        violations.append("requires_user_confirmation is inconsistent with intent")
    if packet.get("requires_operator_approval") and intent_class not in {"tool_action_request", "project_gap_review_request", "continue_existing_project", "new_project_start", "unknown_or_ambiguous"}:
        violations.append("requires_operator_approval is inconsistent with intent")
    if packet.get("pending_approval") and not (packet.get("requires_user_confirmation") or packet.get("requires_operator_approval")):
        violations.append("pending approvals remain visible")
    if not isinstance(packet.get("denied_authority"), Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field not in packet["denied_authority"]:
                violations.append(f"missing denied authority: {field}")
            elif packet["denied_authority"].get(field) is not False:
                violations.append(f"denied authority must remain blocked: {field}")

    project_state_result = validate_project_state_item_v1(packet.get("project_state_candidate"))
    if not project_state_result["valid"]:
        violations.append(f"invalid project_state_candidate: {', '.join(project_state_result['violations'])}")

    for index, item in enumerate(packet.get("memory_state_candidates", [])):
        result = validate_memory_state_item_v1(item)
        if not result["valid"]:
            violations.append(f"invalid memory_state_candidate at index {index}: {', '.join(result['violations'])}")
    for index, item in enumerate(packet.get("continuity_state_items", [])):
        result = validate_state_continuity_item_v1(item)
        if not result["valid"]:
            violations.append(f"invalid continuity_state_item at index {index}: {', '.join(result['violations'])}")
    for index, item in enumerate(packet.get("tool_lane_contract_candidates", [])):
        result = validate_first_tool_lane_contract_v1(item)
        if not result["valid"]:
            violations.append(f"invalid tool_lane_contract_candidate at index {index}: {', '.join(v['message'] for v in result['violations'])}")

    if intent_class == "tool_action_request" and not packet.get("tool_lane_contract_candidates"):
        violations.append("tool actions must become tool-lane contract candidates")
    if intent_class == "memory_update_proposal_request" and not packet.get("memory_state_candidates"):
        violations.append("memory updates must remain proposals")
    if intent_class == "project_gap_review_request" and not packet.get("requires_user_confirmation"):
        violations.append("gap review requires explicit user approval metadata")
    if _compact_text(packet.get("blocked_reason")) and not packet.get("pending_approval"):
        violations.append("blocked metadata should remain visible")

    classification = {"intent_class": intent_class or "unknown_or_ambiguous", "risk": "blocked" if violations else "review_required"}
    return {"valid": not violations, "violation_count": len(violations), "violations": violations, "classification": classification}


def summarize_project_start_chat_flow_packet_v1(packet: Any) -> dict[str, Any]:
    normalized = _json_safe(copy.deepcopy(packet)) if isinstance(packet, Mapping) else {}
    summary = {
        "flow_id": _compact_text(normalized.get("flow_id"), default="unknown_flow"),
        "flow_type": _compact_text(normalized.get("flow_type"), default=FLOW_TYPE_V1),
        "intent_class": _compact_text(normalized.get("intent_class"), default="unknown_or_ambiguous"),
        "project_id": _compact_text(normalized.get("project_id"), default=""),
        "session_id": _compact_text(normalized.get("session_id"), default=""),
        "missing_project_field_count": len(_listify(normalized.get("missing_project_fields"))),
        "clarification_question_count": len(_listify(normalized.get("clarification_questions"))),
        "risk_flag_count": len(_listify(normalized.get("risk_flags"))),
        "pending_approval": bool(normalized.get("pending_approval")),
        "requires_user_confirmation": bool(normalized.get("requires_user_confirmation")),
        "requires_operator_approval": bool(normalized.get("requires_operator_approval")),
        "allowed_next_step": _compact_text(normalized.get("allowed_next_step"), default="ask_clarifying_questions"),
        "user_visible_status_phrase": _compact_text(normalized.get("user_visible_status_phrase"), default=""),
        "operator_visible_summary": _compact_text(normalized.get("operator_visible_summary"), default=""),
    }
    return _json_safe(summary)


def to_project_start_chat_flow_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def build_initial_project_start_chat_flow_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_project_start_chat_flow_packet_v1(
            requested_action="Start a new project with a clear goal",
            owner_user_scope="self",
            tenant_account_scope="self",
            goal="launch a metadata-only project",
            scope="bounded",
            constraints=["no runtime wiring"],
            success_criteria="a safe plan exists",
            known_inputs=["initial idea"],
            desired_output="project intake packet",
            deadline_or_priority="soon",
            approval_needed="yes",
            privacy_sensitivity="low",
            tool_use_expectation="metadata only",
        ),
        build_project_start_chat_flow_packet_v1(
            requested_action="Continue existing project project_alpha and review gaps",
            owner_user_scope="self",
            tenant_account_scope="self",
            project_id="project_alpha",
            session_id="session_alpha",
            goal="review current project state",
            scope="bounded",
            constraints=["metadata only"],
            success_criteria="gaps identified",
            known_inputs=["existing project"],
            desired_output="gap review packet",
            deadline_or_priority="medium",
            approval_needed="yes",
            privacy_sensitivity="low",
            tool_use_expectation="metadata only",
        ),
    ]
    return [to_project_start_chat_flow_json_safe_v1(example) for example in examples]


__all__ = [
    "SCHEMA_VERSION_V1",
    "FLOW_TYPE_V1",
    "classify_project_start_intent_v1",
    "build_project_start_chat_flow_packet_v1",
    "validate_project_start_chat_flow_packet_v1",
    "summarize_project_start_chat_flow_packet_v1",
    "to_project_start_chat_flow_json_safe_v1",
    "build_initial_project_start_chat_flow_examples_v1",
    "build_project_start_clarification_prompt_metadata_v1",
    "build_project_start_status_phrase_metadata_v1",
]
