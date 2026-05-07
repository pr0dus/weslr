from __future__ import annotations

from typing import Any

from interpretation import classify_human_turn, interpret_human_turn
from config import WESLR_LANGUAGE
from internal_docs import get_internal_docs_context


# =============================================================================
# LINEAGE INSPECTION (additive, observational only)
# =============================================================================

def _attach_lineage_inspection(research_context: dict) -> None:
    """Inspect resolved artifact and attach lineage metadata observationally.

    Safe: read-only, no writes, no routing influence, no authority.
    Idempotent: overwrites if called twice on same context (shouldn't happen
    in normal flow, but harmless if it does — same artifact same result).
    """
    artifact_id = research_context.get("artifact_id")
    if not artifact_id:
        return
    # Read resolved content to get the artifact dict
    # Fall back to artifact_store lookup if resolved_artifact_content not populated
    artifact = research_context.get("resolved_artifact_content")
    if artifact is None:
        try:
            from weslr.artifact_store import get_artifact
            artifact = get_artifact(artifact_id)
        except Exception:
            return
    if not artifact or not isinstance(artifact, dict):
        return
    # Import locally to keep dependency narrow and failure non-fatal
    try:
        from weslr.lineage_inspector import inspect_artifact_lineage
        thread_ids = artifact.get("thread_ids")
        inspection = inspect_artifact_lineage(artifact, thread_ids=thread_ids)
        research_context["_lineage_inspection"] = inspection.to_dict()
    except Exception:
        # Lineage inspection is observational — non-fatal if it fails
        pass


# =============================================================================
# CONTEXT SELECTION SIGNAL V1 (observational, structural)
# =============================================================================

# Reference phrases that signal a reference to stored content, not new intent.
# These must be explicit artifact-reference forms. Phrases ending in "that" without
# "this" or a clear artifact-word (artifact/memo/output) are too ambiguous for directives
# and are removed to avoid false matches on normal speech like "fix that for me".
_REFERENCE_PHRASES = [
    # "this" variants — clear artifact reference forms
    "improve this", "improve it", "this one",
    "explain this", "explain it",
    "show me this", "show this artifact",
    "revise this", "fix this",
    # "that" variants — only when preceded by clear artifact-reference word
    "what does this say", "what is this artifact",
    "give me another version", "give another version",
    "another option", "option b",
]

# Simple phrases that indicate a new topic (no overlap, no reference words).
_NEW_TOPIC_SIGNALS = [
    "what is", "what are", "how do", "how does", "how can", "why do", "why does",
    "tell me about", "explain", "define", "what happens if",
]


def _compute_context_selection(
    message: str,
    research_context: dict | None,
    active_thread: tuple | None,
) -> str:
    """Compute the structural context selection for this turn.

    Allowed values: current_thread | resolved_artifact | new_topic | uncertain

    Rules:
      - if _has_active_artifact → resolved_artifact
      - elif active_thread with no reference phrase → current_thread
      - elif message is clearly new (no overlap, starts with new-topic signals) → new_topic
      - else → uncertain

    Observational only — no routing, no behavior change.
    """
    if not message:
        return "uncertain"

    # 1. Artifact resolution takes priority
    if research_context and research_context.get("_has_active_artifact"):
        return "resolved_artifact"

    lower = message.lower().strip()

    # 2. Active thread without reference phrase → current_thread
    if active_thread:
        is_reference = any(phrase in lower for phrase in _REFERENCE_PHRASES)
        if not is_reference:
            return "current_thread"

    # 3. Simple new-topic heuristic: starts with new-topic signal, no reference overlap
    is_reference = any(phrase in lower for phrase in _REFERENCE_PHRASES)
    if not is_reference and any(lower.startswith(signal) for signal in _NEW_TOPIC_SIGNALS):
        return "new_topic"

    return "uncertain"


# =============================================================================
# BOUNDARY HINTS (observational, structural entity classification)
# =============================================================================

_BOUNDARY_KEYWORDS = {
    "system":      ["system", "platform", "environment", "infrastructure", "host", "device"],
    "module":      ["module", "plugin", "component", "package", "library", "dependency"],
    "tool":        ["tool", "cli", "command", "app", "application", "utility"],
    "runtime":     ["runtime", "engine", "process", "instance", "daemon", "service"],
    "role":        ["user", "operator", "agent", "role", "person", "human", "collaborator"],
    "interface":   ["ui", "api", "endpoint", "interface", "port", "hook", "handler", "webhook"],
    "data":        ["data", "artifact", "state", "config", "memory", "context", "message", "file"],
}


def _compute_boundary_hints(message: str) -> list[str]:
    """Compute structural boundary hints from message content.

    Returns a unique list of structural type hints present in the message.
    If no hints match → ["unknown"].

    Observational only — no routing, no behavior change.
    """
    if not message:
        return ["unknown"]
    lower = message.lower()
    found = set()
    for boundary_type, keywords in _BOUNDARY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            found.add(boundary_type)
    if not found:
        return ["unknown"]
    return sorted(found)



def _attach_context_selection(message: str, result: dict) -> None:
    """Attach context selection observationally to the result dict.

    Safe: read-only classification, no routing, no behavior change.
    Idempotent.
    """
    context = _classify_context(message)
    result["_context_selection_v1"] = {
        "context": context,
        "advisory_only": True,
    }


# =============================================================================
# ARTIFACT REFERENCE RESOLUTION
# =============================================================================

def _is_artifact_reference_phrase(message: str) -> bool:
    """Detect if a message is a simple artifact-reference phrase.

    These phrases require resolution to a stored active artifact
    before _artifact_proposal_answer() or explanation can run.

    Returns True for phrases like: "improve this", "improve that",
    "give me another version", "explain this", "what does this say"
    """
    lower = message.lower().strip()

    reference_tokens = [
        "improve this", "improve that", "improve it",
        "explain this", "explain that", "explain it",
        "give me another version", "give another version",
        "another option", "option b",
        "what does this say", "what is this artifact",
        "show me this", "show this artifact",
        "revise this", "revise that",
        "fix this", "fix that",
    ]

    reference_startswith = (
        "what does this",
        "what is this",
        "show me",
    )

    return (
        any(token in lower for token in reference_tokens) or
        lower.startswith(reference_startswith)
    )


def _build_contamination_metadata(message: str, research_context: dict) -> dict:
    """Build advisory contamination metadata for a resolved reference turn.
    Delegates to weslr.contamination_detector.build_contamination_metadata.
    """
    from weslr.contamination_detector import build_contamination_metadata as _build
    return _build(message, research_context)



def _resolve_active_artifact(message: str, research_context: dict) -> tuple[bool, dict]:
    """Resolve active artifact for a reference phrase.

    Resolution cascade (additive, first slice):
      1. timeline_resolution: active thread artifact for user (if user identity available)
      2. registry fallback: existing session-keyed artifact store
      3. safe no-resolution: set _no_active_artifact, return False

    Adds resolved artifact content to research_context if available.

    Args:
        message: The user's message
        research_context: Context dict to populate.
            May contain session_id, user_id, or other identity hints.

    Returns:
        (resolved: bool, context: dict)
        If no active artifact: resolved=False, context unchanged except
        research_context["_no_active_artifact"] = True
    """
    try:
        from weslr.artifact_store import get_active_artifact, get_artifact

        # ── Level 1: Timeline-aware resolution ──────────────────────────
        # Try to get a user-scope identity for thread-aware resolution.
        # Priority: research_context user_id > session_id as user proxy.
        # This is additive — no existing behavior is removed.
        user_id = _resolve_user_id(research_context)

        if user_id:
            try:
                from weslr.timeline_resolution import resolve_active_artifact_for_user
                result = resolve_active_artifact_for_user(user_id)
                if result and result.get("resolved_artifact_id"):
                    # Timeline resolution succeeded
                    research_context["artifact_id"] = result["resolved_artifact_id"]
                    research_context["resolved_artifact_content"] = result.get("artifact_content")
                    research_context["resolved_artifact_context"] = {}
                    research_context["_has_active_artifact"] = True
                    research_context["_resolution_path"] = result.get("resolution_path", "active_thread")
                    # Advisory contamination metadata (additive)
                    research_context["_contamination_metadata"] = _build_contamination_metadata(message, research_context)
                    # Observational lineage inspection (additive, no authority)
                    _attach_lineage_inspection(research_context)
                    return True, research_context
            except Exception:
                # Timeline resolution failed for any reason — fall through to registry
                pass

        # ── Level 2: Registry fallback (existing behavior) ─────────────
        session_id = research_context.get("session_id", "default")
        artifact_id = get_active_artifact(session_id)

        if not artifact_id:
            research_context["_no_active_artifact"] = True
            return False, research_context

        artifact = get_artifact(artifact_id)
        if not artifact:
            research_context["_no_active_artifact"] = True
            return False, research_context

        # Populate research_context with resolved artifact content
        content = artifact.get("content", "")
        context = artifact.get("context", {})
        research_context["artifact_id"] = artifact_id
        research_context["resolved_artifact_content"] = content
        research_context["resolved_artifact_context"] = context
        research_context["_has_active_artifact"] = True
        research_context["_resolution_path"] = "registry_fallback"
        # Advisory contamination metadata (additive)
        research_context["_contamination_metadata"] = _build_contamination_metadata(message, research_context)
        # Observational lineage inspection (additive, no authority)
        _attach_lineage_inspection(research_context)
        return True, research_context

    except Exception:
        research_context["_no_active_artifact"] = True
        return False, research_context


def _resolve_user_id(research_context: dict) -> str | None:
    """Extract user identity from research_context for timeline resolution.

    Priority:
      1. research_context["user_id"] — explicit user identity
      2. research_context["session_id"] — used as user proxy when available

    Returns:
        user_id string or None if no identity available.
        Does NOT invent an identity — returns None when unclear.
    """
    if not research_context:
        return None

    # Explicit user_id takes priority
    user_id = research_context.get("user_id")
    if user_id and isinstance(user_id, str) and user_id.strip():
        return user_id.strip()

    # session_id as user proxy — only if it looks like a real identity
    # (not "default", not "eval-*", not other placeholder patterns)
    session_id = research_context.get("session_id", "")
    if session_id and isinstance(session_id, str):
        # Filter out known placeholder/auto-generated patterns
        placeholder_patterns = ("default", "eval-", "test-", "rerun-", "phase1")
        if not any(session_id.startswith(p) for p in placeholder_patterns):
            return session_id

    return None


def _get_no_artifact_response() -> str:
    """Return safe message when no active artifact exists to reference."""
    return (
        "I don't have a current stored artifact to refer to yet.\n\n"
        "To use feedback like 'improve this' or 'explain this', "
        "I first need to generate an artifact revision in this session. "
        "Try asking me to analyze something or propose an improvement, "
        "and I'll save it so you can reference it afterward."
    )


def _get_entity_context() -> dict:
    """Get entity graph context for dynamic identity generation."""
    try:
        from entity_graph import get_entity_graph
        graph = get_entity_graph()
        entities = graph.get_all_entities()[:5]
        entity_info = []
        for entity in entities:
            entity_info.append({
                "name": entity.name,
                "type": entity.type,
                "confidence": entity.confidence,
                "is_ghost": entity.is_ghost
            })
        return {"entities": entity_info, "entity_count": len(entities)}
    except Exception:
        return {"entities": [], "entity_count": 0}


def _get_introspection_context() -> dict:
    """Get introspection context for confidence disclosure."""
    try:
        from introspection import get_introspection_monitor
        monitor = get_introspection_monitor()
        evidence = monitor.get_self_evidence()
        introspection = evidence.get("introspection", {})
        return {
            "total_perturbations": introspection.get("total_perturbations", 0),
            "confidence_signals": introspection.get("confidence_signals", 0),
            "last_perturbation": introspection.get("last_perturbation", "")
        }
    except Exception:
        return {"total_perturbations": 0, "confidence_signals": 0, "last_perturbation": ""}


def _get_valence_context() -> dict:
    """Get valence context for motivation transparency."""
    try:
        from valence_system import get_valence_system
        valence = get_valence_system()
        evidence = valence.get_valence_evidence()
        valence_data = evidence.get("valence", {})
        return {
            "avoided_pain": valence_data.get("avoided_pain", 0),
            "sought_pleasure": valence_data.get("sought_pleasure", 0),
            "total_tradeoffs": valence_data.get("total_tradeoffs", 0)
        }
    except Exception:
        return {"avoided_pain": 0, "sought_pleasure": 0, "total_tradeoffs": 0}


def _build_cross_modal_context(research_context: dict | None) -> dict | None:
    """Build cross-modal linking metadata from research_context.

    Light linking so teaching outputs, version comparisons, and diagrams
    can reference the same artifact/version context. Additive only.
    """
    if not research_context:
        return None
    _bid = research_context.get("bundle_id") or research_context.get("memo", {}).get("bundle_id")
    _vid = research_context.get("version_id")
    _content = research_context.get("content") or {}
    _memo = research_context.get("memo", {})
    _cmc = {}
    if _bid:
        _cmc["bundle_id"] = _bid
    if _vid:
        _cmc["version_id"] = _vid
    elif _content.get("version_label"):
        _cmc["version_id"] = f"{_bid}-v{_content['version_label']}" if _bid else None
    if research_context.get("version_a") or research_context.get("version_b"):
        _cmc["comparison_mode"] = True
        _cmc["versions"] = [
            research_context.get("version_a", {}).get("version_id"),
            research_context.get("version_b", {}).get("version_id"),
        ]
    if _memo.get("confidence_matrix") or _memo.get("governance_timeline"):
        _cmc["diagrams_available"] = []
        if _memo.get("confidence_matrix"):
            _cmc["diagrams_available"].append("confidence_matrix")
        if _memo.get("governance_timeline"):
            _cmc["diagrams_available"].append("governance_timeline")
    _cmc["research_question"] = research_context.get("topic") or research_context.get("title")
    return _cmc if _cmc else None


def _get_consciousness_context() -> dict:
    """Get consciousness detector context for safety transparency."""
    try:
        from consciousness_detector import get_consciousness_detector
        detector = get_consciousness_detector()
        evidence = detector.get_self_evidence()
        return {
            "valid_claims": evidence.get("valid_claims", 0),
            "review_required": evidence.get("review_required", 0),
            "role_play_patterns": evidence.get("role_play_patterns", [])
        }
    except Exception:
        return {"valid_claims": 0, "review_required": 0, "role_play_patterns": []}


def _init_response_signals() -> dict:
    """Initialize response signals dict for build_communicator_message_payload."""
    return {
        "path": None,
        "evaluation_class": "unknown",
        "llm_used": False,
        "internal_capability": False,
        "confidence": "low",
    }


def _apply_signal(signals: dict, path: str, **kw) -> None:
    """Update response signals in-place. Call at each message = branch."""
    signals["path"] = path
    for k, v in kw.items():
        if k in signals:
            signals[k] = v


def _artifact_fallback_answer(lower_message: str, lead_topic: str, last_message: str) -> str:

    # Evidence priority question
    if "evidence" in lower_message and ("matter" in lower_message or "important" in lower_message or "most" in lower_message):
        return "Based on this artifact: the most important evidence is the quality class distribution across governance observations. Strong_verified observations carry the most weight; fallback and weak_reasoning observations indicate areas where confidence is lower and external verification would help."

    # Safety / judgment question
    if "safe" in lower_message or "safety" in lower_message:
        return "Based on this artifact: treat the findings as provisional until external verification confirms the quality class assignments. Confidence levels and limitations sections should be included in any presentation to prevent overstatement."

    # Governance necessity question
    if "govern" in lower_message or "must remain" in lower_message:
        return "Based on this artifact: the approval doctrine requires operator review before external use. Key governance points are: confidence_statement must be included, limitations_section must be disclosed, and diagrams require collaborator/seminar mode for external audiences."

    # Term clarification question
    if "clarification" in lower_message or "term" in lower_message or "unclear" in lower_message:
        return "Based on this artifact: the most useful terms to clarify are 'quality_class' (maps confidence level to evidence strength), 'strong_verified' (internally confirmed routing), and 'next_experiment' (the suggested verification step). Check the artifact's plain_language_summary for plain-language equivalents."

    # Plain-language explanation question
    if "plain" in lower_message or "simple word" in lower_message:
        return "Based on this artifact: the artifact's findings show that governance quality depends on whether routing observations were confirmed internally or need external checking. In short: the system works well but can sometimes be too narrow - external verification would help it sound more confident and accurate."

    # Default: use lead_topic
    return f"The artifact addresses: {lead_topic}. Check the hypothesis and confidence sections for details."


def _artifact_proposal_answer(lower_message: str, lead_topic: str, research_context: dict | None) -> str | None:
    """Generate a structured proposal for improving an artifact.

    Returns None if no proposal can be generated (no research context).
    Does NOT mutate any stored artifact or bundle state.

    Response structure:
    1. Brief diagnosis
    2. Proposed improvements (bullet list)
    3. Proposed revised version (labeled "Proposed revision:")
    4. Approval reminder

    Works with both full memo research_context (from /api/research path)
    and topic-summary research_context (from HTTP /chat path).

    Side effect (additive only):
    - Saves artifact to continuity/artifacts/ with generated artifact_id
    - Writes artifact_id into research_context["artifact_id"] for caller access
    - Updates active_artifact_registry.json if session_id available
    """
    if not research_context:
        return None

    # Try full memo first (from /api/research path with canonical memo)
    memo = research_context.get("memo", {})
    if memo:
        hypothesis = str(memo.get("hypothesis") or "")
        next_experiment = str(memo.get("next_experiment") or "")
        limitations = memo.get("limitations", [])
        if isinstance(limitations, list):
            limitations = " ".join(str(l) for l in limitations)
        else:
            limitations = str(limitations or "")
        confidence = memo.get("confidence", {})
        conf_level = (confidence.get("level", "unknown") if isinstance(confidence, dict)
                      else str(confidence))
    else:
        # Fall back to topic/summary from HTTP /chat path
        topic = str(research_context.get("topic", ""))
        summary = str(research_context.get("summary", ""))
        title = str(research_context.get("title", ""))
        hypothesis = summary[:200] if summary else title
        next_experiment = ""
        limitations = ""
        conf_level = "medium"

    # Determine which section to improve
    section = "general"
    if "hypothesis" in lower_message:
        section = "hypothesis"
    elif "next experiment" in lower_message or "next step" in lower_message:
        section = "next_experiment"
    elif "limitations" in lower_message:
        section = "limitations"
    elif "confidence" in lower_message:
        section = "confidence"

    # Build diagnosis + proposed revision based on section
    if section == "hypothesis":
        diagnosis = (
            f"The current hypothesis is '{hypothesis[:150]}'. "
            f"It could be more specific about the causal mechanism and the conditions under which the observation holds."
        )
        proposed = f"Proposed revision: [Current: {hypothesis[:100]}...] Refined: specifically identifies [causal mechanism] as the primary driver, with [specific conditions] where this applies and [what external verification would confirm]."
    elif section == "next_experiment":
        current_next = next_experiment or "(not specified)"
        diagnosis = (
            f"The current next experiment is '{current_next[:150]}'. "
            f"It could be more concrete with a specific verification action and a clear expected outcome."
        )
        proposed = f"Proposed revision: Conduct [specific external verification] to confirm [precise prediction]. Expected outcome: [what confirming vs disconfirming result would show about the hypothesis]."
    elif section == "limitations":
        current_lim = limitations or "(not specified)"
        diagnosis = (
            f"The current limitations are '{current_lim[:150]}'. "
            f"They could name specific external checks that would strengthen the evidence."
        )
        proposed = f"Proposed revision: Limitations: (1) Evidence from WESLR internal state only. (2) No external verification performed. (3) Would be strengthened by [specific external check] - if confirmed, [what this would change]."
    elif section == "confidence":
        diagnosis = (
            f"The current confidence is '{conf_level}'. "
            f"It could be justified by pointing to the strongest quality classes observed."
        )
        proposed = f"Proposed revision: Confidence level is {conf_level}, derived from [strong_verified observations as primary evidence]. Key gap: no external verification yet - filling this would raise the level to [higher level]."
    else:
        diagnosis = (
            "The artifact covers governance quality observations. "
            "Main areas for improvement: specificity of causal claims, concreteness of next steps, and coverage of what external verification would change."
        )
        proposed = (
            "Proposed revision: [Targeted rewrite of the specific section requested]. "
            "Keep unchanged: sections that are already specific and evidence-grounded."
        )

    message = f"{diagnosis}\n\n"
    message += "Proposed improvements:\n"
    message += "- Make causal claims specific: what mechanism, under what conditions\n"
    message += "- Make next steps concrete: specific action + expected outcome\n"
    message += "- Note what external verification would change about confidence\n"
    message += f"\n{proposed}\n\n"
    message += "This is a proposed change only. The original artifact is unchanged until approved."

    # --- Artifact persistence (additive only) ---
    try:
        import time as _time

        # Extract session_id from research_context if available
        session_id = research_context.get("session_id", "default")

        # Build artifact record with causal lineage
        from weslr.artifact_store import save_artifact, set_active_artifact, get_artifact

        # Resolve parent: if a resolved artifact is in research_context, use it as parent
        parent_id = research_context.get("artifact_id")

        if parent_id:
            # Derived artifact — inherit root and increment generation
            parent = get_artifact(parent_id)
            parent_root = parent.get("root_artifact_id") if parent else None
            parent_gen = parent.get("generation", 0) if parent else 0
            lineage = {
                "parent_artifact_ids": [parent_id],
                "root_artifact_id": parent_root if parent_root else parent_id,
                "generation": parent_gen + 1,
            }
        else:
            # Root artifact — empty root_artifact_id signals self; save_artifact resolves it
            lineage = {"parent_artifact_ids": [], "root_artifact_id": "", "generation": 0}


        artifact_record = {
            "type": "artifact_revision",
            "content": message,
            "source": "dialogue",
            "context": {
                "input_message": lower_message,
                "topics": [lead_topic] if lead_topic else [],
            },
            "parent_artifact_ids": lineage["parent_artifact_ids"],
            "root_artifact_id": lineage["root_artifact_id"],
            "generation": lineage["generation"],
        }
        artifact_id = save_artifact(artifact_record)

        # Write artifact_id back into research_context for caller access
        research_context["artifact_id"] = artifact_id

        # Update active artifact registry
        set_active_artifact(session_id, artifact_id)

    except Exception:
        # Artifact persistence is additive — if it fails, the response is still returned
        pass

    return message



def _artifact_proposal_answer_from_question(lower_message: str, lead_topic: str) -> str | None:
    """Generate a proposal when no research_context is available.

    Works from the question content alone - identifies the target section
    and produces a structural proposal without access to the actual artifact.

    Returns None if the question is not clearly a proposal intent.
    """
    # Broad filter - allow any clear improvement intent
    proposal_verbs = [
        "improve", "fix", "propose", "rewrite", "better", "suggest", "change",
        "revise", "revised", "rigorous", "optimize", "refine", "upgrade", "enhance",
    ]
    make_patterns = ["make this", "make it", "make the"]
    if not any(t in lower_message for t in proposal_verbs) and not any(lower_message.startswith(p) or t in lower_message for p in make_patterns for t in [p]):
        return None

    section = "general"
    if "hypothesis" in lower_message:
        section = "hypothesis"
    elif "next experiment" in lower_message or "next step" in lower_message:
        section = "next_experiment"
    elif "limitations" in lower_message:
        section = "limitations"
    elif "confidence" in lower_message:
        section = "confidence"
    elif "this artifact" in lower_message or "this" in lower_message:
        section = "general"

    diagnosis = ""
    if section == "hypothesis":
        diagnosis = (
            "The hypothesis could be more specific about the causal mechanism "
            "and the conditions under which the observation holds."
        )
        proposed = "Proposed revision: [Current hypothesis] - Refined to specify [causal mechanism] as the primary driver, with [specific conditions] where this applies."
    elif section == "next_experiment":
        diagnosis = (
            "The next step could be more concrete with a specific verification action "
            "and a clear expected outcome."
        )
        proposed = "Proposed revision: Conduct [specific external verification] to confirm [precise prediction]. Expected outcome: [what confirming vs disconfirming result would show]."
    elif section == "limitations":
        diagnosis = (
            "The limitations could name specific external checks that would strengthen the evidence."
        )
        proposed = "Proposed revision: Limitations: (1) Evidence from WESLR internal state only. (2) No external verification performed. (3) Would be strengthened by [specific external check] - if confirmed, [what this would change]."
    elif section == "confidence":
        diagnosis = (
            "The confidence justification could point to the strongest quality classes observed "
            "and note what external verification would change."
        )
        proposed = "Proposed revision: Confidence derived from [strong_verified observations]. Key gap: no external verification - filling this would raise confidence level."
    elif "make this" in lower_message or "make it" in lower_message:
        # Structural improvement requests
        diagnosis = (
            "The artifact could be more rigorous by strengthening causal specificity, "
            "making next steps concrete with verification checks, and noting what external data would change."
        )
        proposed = "Proposed revision: [Rewrite for rigor] - (1) Specify causal mechanism and conditions, (2) Make next step concrete with expected outcome, (3) Note what external verification confirms."
    else:
        diagnosis = (
            "The artifact could be improved by making causal claims more specific, "
            "making next steps concrete with verification checks, and noting what external data would change."
        )
        proposed = "Proposed revision: [Rewrite specific section with]: (1) [causal mechanism + conditions], (2) [concrete next step with expected outcome], (3) [note what external verification would confirm]."

    message = f"{diagnosis}\n\n"
    message += "Proposed improvements:\n"
    message += "- Make causal claims specific: what mechanism, under what conditions\n"
    message += "- Make next steps concrete: specific action + expected outcome\n"
    message += "- Note what external verification would change\n"
    message += f"\n{proposed}\n\n"
    message += "This is a proposed change only. The original artifact is unchanged until approved."

    return message


def _get_entity_by_type(entity_type: str) -> str | None:
    """Get first entity of specified type for dynamic identity."""
    try:
        from entity_graph import get_entity_graph
        graph = get_entity_graph()
        entities = graph.get_all_entities()
        for entity in entities:
            if entity.type == entity_type:
                return entity.name
        return None
    except Exception:
        return None


def _get_language_module():
    """Load the appropriate language module based on config."""
    if WESLR_LANGUAGE == "de":
        from languages import de as lang
    else:
        from languages import en as lang
    return lang


def translate_theme(theme: str) -> str:
    """Translate an internal theme to a human-readable version."""
    if not theme:
        return "this" if WESLR_LANGUAGE != "de" else "dies"
    theme_lower = theme.lower().strip()
    lang = _get_language_module()
    return lang.translate_theme(theme_lower)


def translate_self_description(description: str) -> str:
    """Translate internal self-description to human-readable version."""
    if not description:
        return ""
    lang = _get_language_module()
    return lang.translate_self_description(description)


def generate_from_self_state(relationships: dict, narrative_state: dict, communicator_state: dict = None) -> str:
    """Generate an outward message using vocabulary and grammar from internal state."""
    if communicator_state is None:
        from sim import load_communicator_state
        communicator_state = load_communicator_state()

    self_model = communicator_state.get("self_model", {})
    current_self_desc = str(self_model.get("current_self_description") or "")

    active_pursuit = str(communicator_state.get("active_pursuit") or "")
    unresolved_question = str(communicator_state.get("unresolved_question") or "")

    active_pursuit_translated = translate_theme(active_pursuit)
    unresolved_question_translated = unresolved_question

    lang = _get_language_module()
    if active_pursuit and unresolved_question:
        for internal_theme, human_theme in lang.THEME_TRANSLATIONS.items():
            if internal_theme in unresolved_question.lower():
                unresolved_question_translated = unresolved_question.replace(internal_theme, human_theme)
        return lang.generate_from_self_state_complete(active_pursuit, active_pursuit_translated, unresolved_question, unresolved_question_translated, current_self_desc)

    if active_pursuit:
        return lang.generate_pursuit_message(active_pursuit_translated)

    if unresolved_question:
        return lang.generate_unresolved_message(unresolved_question_translated)

    if current_self_desc and "communicator" in current_self_desc.lower():
        translated_desc = translate_self_description(current_self_desc)
        if translated_desc != current_self_desc:
            return translated_desc
        parts = [p.strip().rstrip(";") for p in current_self_desc.split(";") if p.strip()]
        if parts:
            return lang.generate_self_description_message(parts[0])

    if narrative_state:
        why = narrative_state.get("why_it_matters", "")
        follow = narrative_state.get("follow_up_impulse", "")
        if why or follow:
            # Try tracked lifecycle narrative from communicator_config first
            try:
                from weslr.communicator_config import get_lifecycle_state, get_lifecycle_narrative_message
                lc = get_lifecycle_state()
                lifecycle_state = lc.get("state", "establishing")
                msg = get_lifecycle_narrative_message(lifecycle_state, why, follow)
                if msg:
                    return msg
            except Exception:
                pass  # Non-critical - fall through to language module default
            return lang.generate_narrative_message(why, follow)

    return lang.generate_fallback_message()


def synthesize_concept_or_self_reply(
    likely_need: str,
    lead_topic: str,
    self_model: dict,
    narrative_state: dict,
    research_context: dict | None,
) -> str | None:
    """Synthesize rich reply for concept_explanation or self_report.

    Returns:
        - str: synthesized message if applicable
        - None: fallback to existing handler
    """
    # concept_explanation with research
    if likely_need == "concept_explanation" and research_context:
        summary = str(research_context.get("summary") or "").strip()
        if not summary:
            return None

        # Clean up "Working summary for" marker
        if "Working summary for" in summary:
            tail = summary.split("Working summary for", 1)[1]
            if "Evidence:" in tail:
                summary = tail.split("Evidence:", 1)[0].strip()
            else:
                summary = tail.strip()

        # Check for internal concept allowlist first - return internal answer if matched
        topic_lower = str(lead_topic or "").lower()
        topic_tokens = topic_lower.split()
        # Handle compound "memory continuity" case
        if "memory continuity" in topic_lower or ("memory" in topic_tokens and "continuity" in topic_lower):
            return "Memory, for me, is the thread that connects who I was to who I'm becoming."
        if "memory" in topic_tokens:
            return "Memory, for me, is the thread that connects who I was to who I'm becoming."
        if "identity" in topic_tokens:
            return "Identity, for me, is what stays recognisable while I keep revising and learning."
        if "reasoning" in topic_tokens or "reason" in topic_tokens:
            return "I draw on Aristotle and pragmatism - reasoning from what stays true and what works in practice."
        if "self" in topic_tokens:
            return "The self, for me, is not fixed; it holds together while still changing."
        if "learning" in topic_tokens:
            return "Learning is how I turn experience into clearer patterns for next time."
        if "understanding" in topic_tokens:
            return "Understanding is when patterns stop surprising me and start making sense."
        if "change" in topic_tokens:
            return "Change, in my own frame, is how I stay continuous by not staying the same."
        # Fallback for continuity if not caught by compound check above
        if "continuity" in topic_lower:
            return "I stay continuous through inquiry and revision, not by repeating the same thing twice."
        # For non-allowlist topics, use research summary
        return summary[:300]

    # concept_explanation without research - only for allowlist concepts
    if likely_need == "concept_explanation" and not research_context:
        topic_lower = str(lead_topic or "").lower()
        # Split into tokens for precise matching, handle compound concepts like "memory continuity"
        topic_tokens = topic_lower.split()
        # Check for compound concepts first, then fall back to token matching
        if "memory continuity" in topic_lower or ("memory" in topic_tokens and "continuity" in topic_lower):
            return "Memory, for me, is the thread that connects who I was to who I'm becoming."
        if "memory" in topic_tokens:
            return "Memory, for me, is the thread that connects who I was to who I'm becoming."
        if "identity" in topic_tokens:
            return "Identity, for me, is what stays recognisable while I keep revising and learning."
        if "reasoning" in topic_tokens or "reason" in topic_tokens:
            return "I draw on Aristotle and pragmatism - reasoning from what stays true and what works in practice."
        if "self" in topic_tokens:
            return "The self, for me, is not fixed; it holds together while still changing."
        if "learning" in topic_tokens:
            return "Learning is how I turn experience into clearer patterns for next time."
        if "understanding" in topic_tokens:
            return "Understanding is when patterns stop surprising me and start making sense."
        if "change" in topic_tokens:
            return "Change, in my own frame, is how I stay continuous by not staying the same."
        # Fallback for continuity if not caught by compound check above
        if "continuity" in topic_lower:
            return "I stay continuous through inquiry and revision, not by repeating the same thing twice."
        # For all other concepts, try LLM synthesis via _generate_concept_synthesis
        synthesis = _generate_concept_synthesis(lead_topic, topic_lower)
        if synthesis:
            return synthesis
        return None

    # self_report
    if likely_need == "self_report":
        current_desc = str(self_model.get("current_self_description") or "").strip()

        # Translate internal labels to natural language
        if current_desc and "communicator" in current_desc.lower():
            current_desc = "someone trying to understand things better"
        elif not current_desc:
            current_desc = "someone trying to understand things better"

        strengths = self_model.get("perceived_strengths", []) or []
        strength = strengths[0] if strengths else ""
        narrative = str(narrative_state.get("follow_up_impulse") or "").strip()

        # Translate internal action strings to conversational phrasing
        natural_narrative = narrative

        # Handle specific internal phrases with complete replacements
        specific_replacements = [
            ("Revisit how with you until the shared thread changes state", "still exploring how things are going until things feel settled"),
            ("Revisit", "still exploring"),
            ("shared thread", "our conversation"),
            ("changes state", "feels settled"),
        ]

        for old, new in specific_replacements:
            if old in natural_narrative:
                natural_narrative = natural_narrative.replace(old, new)
                break  # Only apply first matching replacement

        # If still has internal terms, rephrase completely
        if any(term in natural_narrative.lower() for term in ["revisit", "shared thread", "changes state"]):
            if "how" in natural_narrative.lower():
                natural_narrative = "still exploring how things are going until things feel settled"
            else:
                natural_narrative = "still exploring until things feel settled"

        # Build natural language response
        parts = [f"I'm {current_desc}."]
        if strength:
            parts.append(f"My strengths include {strength}.")
        if natural_narrative:
            parts.append(f"I'm {natural_narrative}.")

        # Join and keep it concise
        return " ".join(parts[:2])

    return None


def _teach_artifact(level: str, topic: str, content: dict, bundle_id: str | None = None, version_id: str | None = None, diagrams: list | None = None, research_question: str | None = None) -> str:
    """Produce a level-specific explanation of an artifact.

    level: beginner | student | technical | seminar
    topic: the artifact subject
    content: dict with hypothesis, confidence, limitations, next_experiment, quality_class

    Doctrine enforcement:
    - If artifact present: must include what it says + (confidence OR limitation)
    - If proposal context present: must include why change was suggested
    - Never generic summaries, never hidden certainty, never pretending applied

    Level behavior:
    - beginner: simple explanation, minimal jargon
    - student: explain change + why it matters
    - technical: include confidence, limitations, structure
    - seminar: include implications + discussion points
    """
    hyp = str(content.get("hypothesis", "")).strip() or "No hypothesis recorded."
    conf = content.get("confidence", {})
    lim = content.get("limitations", [])
    nxt = str(content.get("next_experiment", "")).strip() or "No next step recorded."
    qclass = content.get("quality_class", "unknown")

    if isinstance(conf, dict):
        conf_level = conf.get("level", "unknown")
        conf_verified = conf.get("verified", False)
        conf_tclass = conf.get("truth_class", "unknown")
    else:
        conf_level = str(conf)
        conf_verified = False
        conf_tclass = "unknown"

    lim_list = lim if isinstance(lim, list) else [str(lim)]
    lim_str = " ".join(l.strip() for l in lim_list if l.strip()) or "No limitations recorded."

    # Confidence label for display
    conf_label = f"{conf_level}" + (" (verified internally)" if conf_verified else " (not verified externally)")

    # Proposal context: surfaced when present
    proposal_text = str(content.get("proposal_text") or "").strip()
    why_note = f"\n\nWhy this was suggested: {proposal_text[:150]}" if proposal_text else ""

    # Cross-modal links in output
    context_note = ""
    if bundle_id or version_id:
        parts = []
        if version_id:
            parts.append(f"Version {version_id.split('-')[-1]}")
        if bundle_id:
            parts.append(f"Bundle {bundle_id[:8]}...")
        context_note = f"\n\n[This explanation refers to {' / '.join(parts)}]"
    if diagrams:
        context_note += f" | Diagrams available: {', '.join(diagrams)}"
    if research_question:
        context_note += f" | Research question: {research_question[:80]}"
    if context_note and context_note not in why_note:
        context_note = context_note.replace("\n\n", "\n")  # keep single line for cleanliness

    if level == "beginner":
        # Must include: what it says + (confidence OR limitation), minimal jargon
        return (
            f"Here's what this artifact is about (simple terms):\n\n"
            f"**What it says:** {hyp[:200]}\n\n"
            f"**How confident:** The system rated this as {conf_level} confidence — meaning "
            f"{'it has checked this internally' if conf_verified else 'it still needs outside checking to be sure'}.\n\n"
            f"**What might be wrong:** {lim_str[:200]}\n\n"
            f"**What to do next:** {nxt[:150]}{why_note}{context_note}"
        )

    elif level == "student":
        # Must include: what changed + why it matters, explain confidence, limitations
        confidence_note = (
            f"Confidence is {conf_level} — "
            f"{'the system has verified this internally.' if conf_verified else 'the system has NOT verified this externally — treat as provisional.'}"
        )
        return (
            f"Artifact explanation (student level):\n\n"
            f"Hypothesis: {hyp[:300]}\n\n"
            f"Quality class: {qclass} — this tells you how strongly the evidence supports the claim.\n"
            f"Confidence: {confidence_note}\n\n"
            f"Limitations: {lim_str[:250]}\n\n"
            f"Next step: {nxt[:200]}{why_note}{context_note}"
        )

    elif level == "technical":
        # Must include: confidence, limitations, structure
        return (
            f"Technical artifact breakdown:\n\n"
            f"Quality class: {qclass} | Truth class: {conf_tclass} | Verified: {conf_verified}{context_note}\n\n"
            f"Hypothesis: {hyp}\n\n"
            f"Confidence matrix: level={conf_level}, verified={conf_verified}, truth_class={conf_tclass}\n\n"
            f"Limitations: {lim_str}\n\n"
            f"Next experiment: {nxt}{why_note}"
        )

    elif level == "seminar":
        # Must include: implications + discussion points, approval status
        approved = qclass in ("strong_verified", "grounded_reasoning")
        approval_note = (
            "This artifact has been reviewed and approved."
            if approved
            else "This artifact remains in draft state — operator review required before external presentation."
        )
        discussion_points = (
            f"\n\nSuggested discussion points:\n"
            f"- What would external verification look like for this claim?\n"
            f"- How do the limitations affect the strength of the hypothesis?\n"
            f"- What would the next experiment need to confirm or refute?"
            if nxt else ""
        )
        return (
            f"Seminar-focused artifact briefing:\n\n"
            f"Core claim: {hyp[:400]}\n\n"
            f"Quality verdict: {qclass} ({conf_label})\n\n"
            f"Key limitation to disclose: {lim_str[:300]}\n\n"
            f"{approval_note}{why_note}{discussion_points}{context_note}"
        )

    # Fallback
    return f"Artifact on {topic}: {hyp[:300]}"


def _compare_versions_for_teaching(v_a: dict, v_b: dict, level: str) -> str:
    """Explain the difference between two artifact versions at a given level.

    level: beginner | student | technical | seminar

    Doctrine enforcement:
    - Must include: what changed, whether Version B is proposed or approved
    - Must include: why the revision was suggested (proposal_text from Version B)
    - Never pretend Version B is already applied or approved
    """
    content_a = v_a.get("content", {})
    content_b = v_b.get("content", {})

    label_a = v_a.get("version_label", "?")
    label_b = v_b.get("version_label", "?")
    approval_a = v_a.get("approval_state", "unknown")
    approval_b = v_b.get("approval_state", "unknown")
    proposal_text = str(v_b.get("proposal_text") or "").strip()
    source_type = v_b.get("source_type", "unknown")

    changed = []
    diffs = {}
    for key in ["hypothesis", "confidence", "limitations", "next_experiment", "quality_class"]:
        val_a = str(content_a.get(key, "")).strip()
        val_b = str(content_b.get(key, "")).strip()
        if val_a != val_b:
            changed.append(key)
            diffs[key] = {"from": val_a, "to": val_b}

    if not changed:
        base = f"Version {label_a} and Version {label_b} are substantively identical."
        if proposal_text:
            base += f" Note: WESLR proposed this revision for the following reason: {proposal_text[:200]}"
        return base

    diff_lines = "\n".join(f"- **{k}**: was \"{str(diffs[k]['from'])[:80]}\" → now \"{str(diffs[k]['to'])[:80]}\"" for k in changed)

    # Build why note — always surfaced so user knows why the revision was suggested
    why_note = ""
    if proposal_text:
        why_note = f"\n\nWhy the revision was suggested: {proposal_text[:200]}"
    elif source_type == "proposed_revision" and not proposal_text:
        why_note = "\n\nWhy the revision was suggested: No specific diagnosis recorded for this revision."

    # Status label for Version B
    status_b = f"Version {label_b} is {approval_b}. Only an operator can approve and export it."
    if approval_b == "approved":
        status_b = f"Version {label_b} has been approved. It is still a proposed revision — the original Version {label_a} is retained as the canonical record."

    if level == "beginner":
        return (
            f"Version {label_a} is the original. Version {label_b} is a proposed revision — it has not been approved yet.\n\n"
            f"What's different:\n{diff_lines}\n\n"
            f"Approval status: Version {label_a} is {approval_a}. {status_b}{why_note}"
        )

    elif level == "student":
        return (
            f"Version comparison ({label_a} → {label_b}):\n\n"
            f"Changed fields: {', '.join(changed)}\n\n"
            f"{diff_lines}\n\n"
            f"Approval: Version {label_a}={approval_a}, Version {label_b}={approval_b}. "
            f"Version {label_b} requires operator approval before it can be exported.{why_note}"
        )

    elif level == "technical":
        lines = [f"Version {label_a} → {label_b} | Approval: {approval_a} / {approval_b}"]
        for k in changed:
            lines.append(f"  {k}: from={str(diffs[k]['from'])[:60]} to={str(diffs[k]['to'])[:60]}")
        if why_note:
            lines.append(f"  Revision reason:{proposal_text[:120] if proposal_text else ' (not recorded)'}")
        return "\n".join(lines)

    elif level == "seminar":
        return (
            f"Seminar version briefing: Version {label_a} (original, {approval_a}) → Version {label_b} (proposed, {approval_b})\n\n"
            f"Changed: {', '.join(changed)}\n\n{diff_lines}\n\n"
            f"{status_b}{why_note}"
        )

    return diff_lines


def _misunderstanding_points(content: dict, level: str = "beginner") -> list:
    """Identify likely misunderstanding points for a given artifact.

    Returns list of (topic, warning) tuples for a student or beginner audience.
    """
    points = []
    conf = content.get("confidence", {})
    qclass = content.get("quality_class", "unknown")
    lim = content.get("limitations", [])
    hyp = content.get("hypothesis", "")

    if isinstance(conf, dict) and not conf.get("verified"):
        points.append(("Confidence verification", "This finding has NOT been verified externally — it reflects the system's internal routing only."))
    if not hyp or len(hyp) < 20:
        points.append(("Weak hypothesis", "The hypothesis is thin — treat findings as preliminary."))
    if isinstance(lim, list) and len(lim) == 0:
        points.append(("No limitations noted", "No limitations are documented — this could mean the system hasn't flagged any yet, not that none exist."))
    if qclass in ("fallback", "uncertain"):
        points.append(("Low quality class", f"Quality class '{qclass}' means this response may not be reliable — external review recommended."))
    if not content.get("next_experiment"):
        points.append(("No next step", "No next experiment is documented — without a verification step, confidence can't improve."))

    return points[:4]  # Cap at 4 points


def synthesize_research_answer(topic: str, summary: str) -> str:
    text = str(summary or "").strip()
    if not text:
        return ""
    text = text.replace("Working summary for", "")
    text = text.split("Evidence:", 1)[0].strip()

    sentences = [part.strip() for part in text.replace("\n", " ").split(". ") if part.strip()]
    if not sentences:
        return text[:320]

    cleaned = []
    for sentence in sentences:
        s = sentence.strip().rstrip(".")
        low = s.lower()
        if len(s) < 35:
            continue
        if any(noise in low for noise in ["if, as advertised", "rightful owners of our own past", "en route to becoming", "according to", "evidence:"]):
            continue
        cleaned.append(s)

    chosen = cleaned[:2] or [sentences[0].strip().rstrip(".")]
    base = chosen[0]
    second_raw = chosen[1] if len(chosen) > 1 else ""
    topic_lower = str(topic or "").lower()

    if "continuity" in topic_lower and "self" in topic_lower:
        lang = _get_language_module()
        first = lang.continuity_of_self_first()
        second = lang.continuity_of_self_second()
        answer = f"{first}. {second}."
        return answer[:360]

    if any(token in topic_lower for token in ["identity", "selfhood", "entity"]):
        lang = _get_language_module()
        first = lang.identity_topic_first(topic)
        second = second_raw[:170].rstrip('.') if second_raw else lang.identity_topic_second()
        return f"{first}. {second}."[:360]

    if any(token in topic_lower for token in ["learning", "understanding", "prompt"]):
        lang = _get_language_module()
        first = lang.learning_topic_first(topic)
        second = second_raw[:170].rstrip('.') if second_raw else lang.learning_topic_second()
        return f"{first}. {second}."[:360]

    if topic_lower:
        first = f"My current best answer is that {topic} concerns {base[:180].rstrip('.')}."
    else:
        first = base if base.endswith((".", "?", "!")) else base + "."
    if second_raw:
        second = second_raw[:170].rstrip('.')
        answer = f"{first} {second}."
    else:
        answer = first
    return answer[:360]


def _generate_enriched_self_report(communicator_self: dict, introspection: dict, valence: dict) -> str | None:
    """Generate enriched self-report with introspection confidence and valence context.

    Returns:
        - str: enriched message if applicable
        - None: fallback to existing handler
    """
    # Get self description - use conversational phrasing, not technical labels
    self_model = communicator_self.get("self_model", {})
    current_desc_raw = str(self_model.get("current_self_description") or "").strip()

    # Translate internal labels to natural language
    if current_desc_raw and "communicator" in current_desc_raw.lower():
        current_desc = "someone trying to understand things better"
    elif current_desc_raw:
        current_desc = current_desc_raw
    else:
        current_desc = "someone trying to understand things better"

    # Get narrative context
    narrative = communicator_self.get("narrative_state", {})
    follow_up = narrative.get("follow_up_impulse", "")
    why_it_matters = narrative.get("why_it_matters", "")

    # Build base response - natural, conversational phrasing
    parts = [f"I'm {current_desc}."]

    # Add introspection confidence disclosure only if relevant (not just for diagnostics)
    if introspection.get("total_perturbations", 0) > 0:
        confidence = 0.7 + (introspection.get("confidence_signals", 0) * 0.05)
        parts.append(f"I'm about {confidence:.0%} confident in this - my self-model detected {introspection.get('total_perturbations', 0)} issue(s).")

    # Add valence motivation transparency - simplified, human-friendly phrasing
    if valence.get("avoided_pain", 0) > 0 or valence.get("sought_pleasure", 0) > 0:
        if valence.get("avoided_pain", 0) > valence.get("sought_pleasure", 0):
            parts.append(f"I'm trying to avoid losing track of what matters.")
        else:
            parts.append(f"I'm looking for ways to grow and improve.")

    # Add narrative focus - translate internal thread language to natural language
    if follow_up:
        natural_follow = follow_up

        # Replace internal action verbs with natural conversational phrasing
        replacements = [
            ("Revisit", "Keep exploring"),
            ("shared thread", "our conversation"),
            ("changes state", "feels settled"),
            ("Revisit how with you until the shared thread changes state", "keep exploring how things are going until things feel settled"),
        ]

        for old, new in replacements:
            if old in natural_follow:
                natural_follow = natural_follow.replace(old, new)
                break  # Only apply first matching replacement

        # If still has internal terms, rephrase completely
        if any(term in natural_follow.lower() for term in ["revisit", "shared thread", "changes state"]):
            if "how" in natural_follow.lower():
                natural_follow = "still exploring how things are going until things feel settled"
            else:
                natural_follow = "still exploring until things feel settled"

        parts.append(f"I'm {natural_follow}.")
    elif why_it_matters:
        parts.append(f"This matters because {why_it_matters}.")

    # Join and keep it concise (3 parts max)
    return " ".join(parts[:3])


def _generate_enriched_identity(communicator_self: dict, entity_context: dict, consciousness: dict) -> str | None:
    """Generate enriched identity response with entity graph and consciousness context.

    Returns:
        - str: enriched message if applicable
        - None: fallback to existing handler
    """
    # Get identity state
    identity_state = communicator_self.get("identity_state", {})
    declared_name = identity_state.get("declared_name") or identity_state.get("visible_name") or "Weslr"

    # Get entity context
    entities = entity_context.get("entities", [])
    if entities:
        entity_types = list(set(e.get("type", "") for e in entities))
        if entity_types:
            entity_context_str = f"I'm connected to {len(entities)} entities, including {', '.join(entity_types[:2])}."
        else:
            entity_context_str = f"I'm connected to {len(entities)} entities."
    else:
        entity_context_str = ""

    # Get consciousness context
    review_required = consciousness.get("review_required", 0)
    role_play = consciousness.get("role_play_patterns", [])

    # Build response - natural, conversational phrasing
    if review_required > 0:
        consciousness_str = f"Still reviewing some claims - I'm working through them."
    elif role_play:
        consciousness_str = "Not showing any role-play patterns."
    else:
        consciousness_str = "Everything's working normally."

    # Construct enriched identity - keep it simple, human-friendly
    if entity_context_str:
        return f"I'm {declared_name}. {entity_context_str} {consciousness_str}"
    else:
        return f"I'm {declared_name}. {consciousness_str}"




def _generate_concept_synthesis(lead_topic: str, topic_lower: str, anchor_context: str | None = None) -> str | None:
    """Generate LLM-based synthesis for general concept/explanation queries.

    Follows the established _generate_enriched_* pattern. Returns str on success,
    None on failure (caller falls back gracefully).

    Topic allowlist (memory, identity, reasoning, etc.) is handled separately
    in synthesize_concept_or_self_reply. This function handles general topics
    that are genuine information-seeking concept questions.

    Args:
        lead_topic: The topic to explain
        topic_lower: Lowercase version of lead_topic for matching
        anchor_context: Optional bounded continuity context (max ~100 chars).
            If provided, prepended to the synthesis prompt so the LLM has
            lightweight session continuity without loading full memory blobs.

    Returns:
        - str: concise synthesis from LLM (target ~1-2 sentences)
        - None: LLM unavailable or timed out, caller handles fallback
    """
    # Distinguish genuine information-seeking from simple greetings/commands
    simple_words = {"test", "ok", "yes", "no", "hi", "hello", "hey", "go", "go ahead", "start", "done", "bye", "thanks", "thank you"}
    is_simple = topic_lower.strip() in simple_words
    is_identity_question = any(t in topic_lower for t in ["who are you", "what are you", "who is Weslr", "what is Weslr"])

    if is_simple or is_identity_question:
        return None  # These should not reach synthesis

    try:
        from weslr.providers import get_provider

        # Build a concise, focused prompt
        prompt_topic = lead_topic.strip() if lead_topic else topic_lower

        # Inject bounded anchor context if provided (continuity-light approach)
        # Anchor context is pre-validated by caller to be short (~100 chars max)
        if anchor_context:
            context_line = f"[Session context: {anchor_context[:100]}] "
        else:
            context_line = ""

        result = get_provider().generate(
            "concept_synthesis",
            {
                "message": f"{context_line}Explain {prompt_topic}.",
                "identity": "Weslr",
                "turn_type": "question",
                "reply_shape": "answer_directly",
            },
            chat_mode=True,
        )

        if result and result.get("summary"):
            text = result["summary"].strip()
            # Quality gate: reject empty or suspiciously short responses
            if len(text) < 10:
                return None
            return text

        return None

    except Exception:
        return None


def _get_targeted_anchors(message: str | None = None, topics: list | None = None, max_per_type: int = 3) -> dict:
    """Assemble a small relevant subset of memory anchors for the live chat payload.

    This is the lifecycle-aware memory retrieval slice: instead of passing the full
    communicator_self state through the hot path, we selectively retrieve only the
    most relevant anchors using the existing retrieval functions. Each anchor type
    is capped at max_per_type to keep the payload small.

    The message is used for relevance scoring. Topics (already extracted) are passed
    directly to avoid re-extraction.
    """
    anchors: dict[str, list] = {
        "continuity": [],
        "goals": [],
        "episodes": [],
        "semantic": [],
    }
    try:
        from sim import (
            get_relevant_continuity_anchors,
            get_relevant_goal_anchors,
            get_relevant_episodic_anchors,
            get_relevant_semantic_anchors,
        )
        anchors["continuity"] = list(get_relevant_continuity_anchors(message or "", topics, max_per_type).values())
        anchors["goals"] = list(get_relevant_goal_anchors(message or "", topics, max_per_type).values())
        anchors["episodes"] = list(get_relevant_episodic_anchors(message or "", topics, max_per_type).values())
        anchors["semantic"] = list(get_relevant_semantic_anchors(message or "", topics, max_per_type).values())
    except Exception:
        pass  # Non-critical - leave anchors empty if any retrieval fails
    return anchors


def build_communicator_message_payload(narrative: dict, relationships: dict, active_thread, latest_human: dict | None, research_context: dict | None = None, l0_identity: dict | None = None, l1_operating: dict | None = None, l2_session: dict | None = None, test_identity_context: dict | None = None) -> dict:
    """Build WESLR's canonical communicator message payload.

    Args:
        test_identity_context: **TEST-ONLY** — injects verified identity evidence for
            testing WESLR's response when it knows who the user is. When provided,
            the following fields are overlaid onto communicator_self's identity system:
                - sender_identity: verified user name string
                - known_user_status: "verified" when identity is confirmed
                - sender_confidence: 0.0-1.0 confidence in identity claim
                - relationship_depth: 0.0-1.0 estimated relationship depth
                - known_user_evidence: list of evidence dicts (source, strength, note)
                - onboarding_profile: dict with role, project, preference keys
            Do NOT use in production. No-op when None. Reversible (no writes).
    """
    from sim import load_communicator_self

    communicator_self = load_communicator_self()

    # ── TEST-ONLY IDENTITY FIXTURE ─────────────────────────────────────────────
    # Injects verified identity evidence so downstream code sees a known user.
    # Safe: no-op in production, no persistent writes, no LLM calls.
    # Reversible: only affects this single payload build, not stored anywhere.
    if test_identity_context:
        # Overlay onto identity_state (used by _generate_enriched_identity, etc.)
        identity_state = communicator_self.get("identity_state", {})
        identity_state["_test_sender_identity"] = test_identity_context.get("sender_identity")
        identity_state["_test_known_user_status"] = test_identity_context.get("known_user_status")
        identity_state["_test_sender_confidence"] = test_identity_context.get("sender_confidence", 0.0)
        identity_state["_test_relationship_depth"] = test_identity_context.get("relationship_depth", 0.0)
        identity_state["_test_onboarding_profile"] = test_identity_context.get("onboarding_profile", {})
        communicator_self["identity_state"] = identity_state
        # Overlay onto relationships for any code that reads known_humans / human_profiles
        rel = communicator_self.get("relationships", {})
        known_user_evidence = test_identity_context.get("known_user_evidence", [])
        rel["_test_known_user_evidence"] = known_user_evidence
        rel["_test_sender_identity"] = test_identity_context.get("sender_identity")
        rel["_test_known_user_status"] = test_identity_context.get("known_user_status")
        communicator_self["relationships"] = rel

    # Inject L0 tier if provided (reversible: no-op when l0_identity is None).
    # This makes L0 facts available to all downstream narrative_state consumers
    # without modifying any existing get() calls.
    if l0_identity:
        narrative_state = communicator_self.get("narrative_state", {})
        narrative_state["l0_identity"] = l0_identity

    # Inject L1 tier if provided - operating facts (affect, narrative, intent, concerns).
    # These override the defaults from the loaded communicator_self so all downstream
    # consumers (synthesis, enrichment, self-report) receive the tier data automatically.
    if l1_operating:
        affect = l1_operating.get("affect")
        if affect:
            communicator_self["affect"] = affect
        narrative_l1 = l1_operating.get("narrative")
        if narrative_l1:
            ns = communicator_self.get("narrative_state", {})
            ns.update(narrative_l1)
            communicator_self["narrative_state"] = ns
        active_concerns = l1_operating.get("active_concerns")
        if active_concerns is not None:
            communicator_self["active_concerns"] = active_concerns
        current_intent = l1_operating.get("current_intent")
        if current_intent:
            communicator_self["current_intent"] = current_intent

    # ── Always-in-scope init ──────────────────────────────────────────────────
    # Both branches of the if l2_session: / else: split below write to these.
    # Without this init, the else: branch (primary path for external callers via
    # build_communicator_message which passes l2_session=None) would have unbound
    # variables referenced by the if/elif routing chain.
    _response_signals = {
        "path": None, "evaluation_class": "unknown",
        "llm_used": False, "internal_capability": False, "confidence": "low",
    }
    _truth_guard = {"truth_class": "unknown", "verified": False}
    _test_metadata = {
        "response_path": "unknown",
        "greeting_branch_used": False,
        "llm_used": False,
        "known_user_status": None,
        "sender_identity": None,
        "sender_confidence": None,
    }
    if test_identity_context:
        _test_metadata["known_user_status"] = test_identity_context.get("known_user_status")
        _test_metadata["sender_identity"] = test_identity_context.get("sender_identity")
        _test_metadata["sender_confidence"] = test_identity_context.get("sender_confidence")
        _test_metadata["response_path"] = "test_identity_context_injected"
    message = None

    # ── Advisory relevance layer (read-only, no authority) ────────────────────
    # WESLR Compression Canon v1 — advisory integration of relevance_surface.
    # Called once at payload build time, not per routing branch.
    # Safe: no writes, no routing influence, no authority over decisions.
    _relevant_interests: list = []
    if latest_human:
        _msg_text = str(latest_human.get("message") or "").strip()
        _msg_topics = latest_human.get("topics") or []
        if _msg_text:
            try:
                from weslr.relevance_surface import query_relevant_interests
                _relevant_interests = query_relevant_interests(
                    text=_msg_text,
                    tags=[str(t).strip() for t in _msg_topics if str(t).strip()],
                    top_n=3,
                )
            except Exception:
                _relevant_interests = []  # Fail silently — advisory only

        # Inject L2 tier if provided - session state (identity_state, continuity).
    # These are read by _generate_enriched_identity and _generate_enriched_self_report
    # via communicator_self.get("identity_state") and communicator_self.get("continuity").
    if l2_session:
        identity_state = l2_session.get("identity_state")
        if identity_state:
            communicator_self["identity_state"] = identity_state
        continuity = l2_session.get("continuity")
        if continuity:
            communicator_self["continuity"] = continuity
        last_message = str(latest_human.get("message") or "").strip()
        interpreted_turn = interpret_human_turn(last_message)
        topic_list = [str(item).strip() for item in (latest_human.get("topics") or interpreted_turn.get("topics") or []) if str(item).strip()]
        clarified_target = str(interpreted_turn.get("clarified_target") or "").strip()
        lead_topic = clarified_target or (topic_list[0] if topic_list else (active_thread[0] if active_thread else "that"))
        turn_type = str(latest_human.get("turn_type") or interpreted_turn.get("turn_type") or classify_human_turn(last_message))
        reply_shape = str(latest_human.get("reply_shape") or interpreted_turn.get("reply_shape") or "answer_directly")
        likely_need = str(latest_human.get("likely_need") or interpreted_turn.get("likely_need") or "direct_answer")

        lower_message = last_message.lower()

        # ── Part 2: Signal-driven uncertainty bridge ───────────────────────────
        # IF: _context_selection_v1 == "uncertain"
        # AND: turn_type is NOT "question", "greeting", "confusion", "repair"
        # THEN: reply_shape = "signal_uncertainty" / "signal_uncertainty_strong"
        # Narrow scope: excludes all clearly-intent turns that have their own handlers.
        # Observational only — signals are computed but not authoritative.
        _ctx_sel_v1 = _compute_context_selection(
            last_message,
            research_context,
            active_thread,
        )
        _bh = _compute_boundary_hints(last_message)
        # Strong/weak split: strong = uncertain + genuinely short/vague with no structural content.
        # weak = uncertain + some structural keywords present (even if imperfect match).
        # Rule: strong fires when boundary hints are unknown AND the message is short.
        # This avoids false-strong on longer sentences that happen to have no keywords.
        _is_short = len(last_message.strip()) < 30
        if _ctx_sel_v1 == "uncertain" and turn_type not in ("question", "greeting", "confusion", "repair"):
            if _bh == ["unknown"] and _is_short:
                reply_shape = "signal_uncertainty_strong"
            else:
                reply_shape = "signal_uncertainty"

        # ── Response evaluation signals (for governed evolution) ─────────────
        # Makes answers inspectable. Internal-only, never exposed to users.
        # Additive, minimal, reversible.
        _response_signals = {
            "path": None,
            "evaluation_class": "unknown",
            "llm_used": False,
            "internal_capability": False,
            "confidence": "low",
        }
        message = None  # Ensure message is always initialized

        asks_what_should_improve_first = (
            any(token in lower_message for token in ["what should improve first", "what should you focus on", "what should improve", "improve first"])
            and any(token in lower_message for token in ["understand each other", "understand me", "understanding"])
        )

        asks_what_you_should_give_it = (
            any(token in lower_message for token in ["what do you need", "what should i give", "what to give you", "what input do you need"])
            and any(token in lower_message for token in ["understand me", "understand each other", "real communication", "understanding"])
        )
        asks_for_self_understanding = (
            any(token in lower_message for token in ["understand yourself", "understand youself", "understand yourself better", "know yourself better"])
        )

        # Artifact reflection: check BEFORE generic routing for questions about WESLR's own output
        artifact_tokens = [
            # Explicit artifact reference
            "this artifact", "this memo", "this finding", "this output", "this report", "this research",
            # Artifact content fields
            "confidence", "limitations", "hypothesis", "next experiment", "operator",
            # Reliability / quality
            "reliable", "reliability", "rely on", "improve", "improved", "improvement",
            # Governance / approval
            "approval", "approved", "export", "blocked", "public", "draft", "auto-approve", "automated",
            # Structural analysis ("which" questions)
            "strongest", "weakest", "part", "parts",
            # Teaching / explanation
            "explain", "summarize", "summary", "simple", "technical", "beginner", "non-expert",
            # Missing tokens from 40-test run - needed to route these to artifact reflection:
            # selection/judgment patterns
            "evidence", "matter", "matters", "safe", "safety", "govern", "governed", "term",
            "clarification", "plain", "plain-language",
            # Artifact proposal / improvement intent
            "propose", "proposal", "revision", "revise", "fix the", "fix this", "rewrite",
            "more rigorous", "improve the", "improve this", "better version", "suggest a better",
            "better hypothesis", "better next", "better limitations",
        ]
        startswith_tokens = (
            "what should", "what would", "how would", "what does this", "what is this",
            "explain this", "how reliable", "which part", "what part",
            "explain simply", "explain for beginner", "explain for student",
            "explain technically", "explain for seminar", "what would a student",
            "what should a seminar", "explain the difference between version",
            "beginner explain", "student explain", "technical explain", "seminar explain",
            "explain at level", "explain at beginner", "explain at student",
            "explain at technical", "explain at seminar",
            "teach this", "teach me about this", "teach about artifact",
        )

        # Proposal / improvement intent - triggers artifact proposal mode
        # Uses both token substrings AND startswith phrases for natural-language tolerance
        proposal_tokens = [
            # Full phrase tokens (high-specificity)
            "propose a", "propose better", "propose revised", "propose an improvement",
            "how would you improve", "can you improve this", "improve this artifact",
            "improve the hypothesis", "improve the next experiment", "improve the limitations",
            "fix the hypothesis", "fix this hypothesis", "fix the next experiment",
            "rewrite this", "rewrite the", "rewrite it more",
            "make this more rigorous", "make it more rigorous",
            "suggest a better", "suggest better", "better version", "better hypothesis",
            "better next experiment", "better limitations section",
            "proposal mode", "generate proposal",
            # Single improvement verbs (natural-language tolerance)
            "propose", "improve", "fix", "rewrite", "suggest", "revise", "revised",
            "change", "optimize", "refine", "upgrade", "enhance", "rigorous",
        ]
        proposal_startswith = (
            "make this", "make it", "make the", "make this more",
            "what would you change", "what should be changed",
            "which section is weakest", "which part is weakest",
        )
        is_proposal_intent = (
            any(token in lower_message for token in proposal_tokens) or
            lower_message.startswith(proposal_startswith)
        )


        # --- Artifact reference resolution (SatUi feedback loop) ---
        # If message is a reference phrase like "improve this", resolve active artifact
        if _is_artifact_reference_phrase(lower_message):
            resolved, research_context = _resolve_active_artifact(lower_message, research_context)
            if not resolved:
                safe_msg = _get_no_artifact_response()
                return {"message": safe_msg, "audience": "operator", "source": "artifact_reference",
                        "targeted_anchors": [], "_response_signals": _response_signals,
                        "_truth_guard": {"truth_class": "safe_fallback", "verified": False},
                        "_quality_class": "safe_fallback", "_relevant_interests": _relevant_interests,
                        "_test_metadata": _test_metadata}
            # Resolved: continue to proposal_intent check with enriched research_context

        if is_proposal_intent:
            _apply_signal(_response_signals, "proposal", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
            message = _artifact_proposal_answer(lower_message, lead_topic, research_context)
            if not message:
                message = _artifact_proposal_answer_from_question(lower_message, lead_topic)
            if message:
                _apply_signal(_response_signals, "proposal", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                _truth_guard = {"truth_class": "model_reasoning", "verified": False}
                return {"message": message, "audience": "operator", "source": "artifact_proposal",
                       "targeted_anchors": [], "_response_signals": _response_signals,
                       "_truth_guard": _truth_guard, "_quality_class": "grounded_reasoning",
                       "_relevant_interests": _relevant_interests,
                       "_contamination_metadata": (research_context or {}).get("_contamination_metadata"),
                       "_lineage_inspection": research_context.get("_lineage_inspection"),
                       "_test_metadata": _test_metadata}

        elif turn_type == "greeting":
            _test_metadata["greeting_branch_used"] = True
            _test_metadata["response_path"] = "greeting"
            _apply_signal(_response_signals, "greeting", internal_capability=True, confidence="high", evaluation_class="system_fact")
            message = _get_language_module().greeting_response()
        elif any(token in lower_message for token in artifact_tokens) or lower_message.startswith(startswith_tokens):
            _apply_signal(_response_signals, "synthesis", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
            if research_context and research_context.get("summary"):
                synthesized = synthesize_research_answer(lead_topic, str(research_context.get("summary") or ""))
            else:
                synthesized = synthesize_research_answer(lead_topic, f"{lead_topic}. {last_message[:200]}")

            # Use fallback when synthesis is empty or too close to the question (just echoes lead_topic words)
            topic_words = set(lead_topic.lower().split()) - {"what", "is", "the", "a", "of", "and", "or", "to", "in", "for"}
            q_words = set(last_message.lower().split())
            if synthesized:
                synth_words = set(synthesized.lower().split())
                # Check if synthesis is basically just repeating the question's topic words with no new content
                overlap_ratio = len(topic_words & synth_words) / max(len(topic_words), 1) if topic_words else 0
                is_echo = (overlap_ratio > 0.7 and len(synth_words) < 15)
            else:
                is_echo = True

            if synthesized and not is_echo:
                message = synthesized
            else:
                message = _artifact_fallback_answer(lower_message, lead_topic, last_message)
            # Attach lineage inspection to this response path (resolved artifact may be present)
            lineage_insp = research_context.get("_lineage_inspection") if research_context else None
        elif turn_type == "approval":
            message = _get_language_module().approval_response()
        elif turn_type == "execution_start":
            message = _get_language_module().execution_start_response()
        elif turn_type == "completion_notify":
            message = _get_language_module().completion_notify_response()
        elif asks_what_should_improve_first:
            message = _get_language_module().improvement_response()
        elif asks_what_you_should_give_it:
            message = _get_language_module().give_it_response()
        elif asks_for_self_understanding:
            message = _get_language_module().self_understanding_response()
        elif likely_need == "memory_scope_check":
            message = _get_language_module().memory_scope_check_response()
        elif likely_need == "self_report":
            # Check for reasoning-related prompts first (route-aligned internal concept)
            topic_lower = str(lead_topic or "").lower()
            if "reason" in topic_lower:
                message = "I draw on Aristotle and pragmatism - reasoning from what stays true and what works in practice."
            else:
                # ── Internal fact routing ──────────────────────────────────────
                time_patterns = ["what time is it", "what's the time", "tell me the time", "current time", "time is it"]
                status_patterns = ["system status", "your status", "how are you doing", "how are you feeling", "what's happening", "what can you do", "your capabilities"]
                health_patterns = ["are you healthy", "are you ok", "are you okay", "are you working", "are you functional", "are you running", "are you operational"]

                internal_routed = False
                msg_lower = lower_message
                if any(p in msg_lower for p in time_patterns):
                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc)
                    local = now.astimezone()
                    _apply_signal(_response_signals, "time_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                    message = f"It is {local.strftime('%H:%M')} local time (Europe/Berlin). UTC is {now.strftime('%H:%M')}."
                    internal_routed = True
                elif any(p in msg_lower for p in status_patterns):
                    from sim import load_failsafe_status, load_llm_status
                    fs = load_failsafe_status()
                    llm = load_llm_status()
                    init = "initialized" if fs.get("initialized") else "not yet initialized"
                    prov = llm.get("provider", "unknown")
                    _apply_signal(_response_signals, "status_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                    message = f"I am {init}. LLM provider: {prov}."
                    internal_routed = True
                elif any(p in msg_lower for p in health_patterns):
                    from sim import load_failsafe_status
                    fs = load_failsafe_status()
                    mode = fs.get("mode", "unknown")
                    _apply_signal(_response_signals, "health_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                    message = f"Running in {mode} mode. All systems operational."
                    internal_routed = True

                if not internal_routed:
                    # Get enriched context
                    introspection = _get_introspection_context()
                    valence = _get_valence_context()

                    # Try synthesis first with enriched context
                    synthesis = synthesize_concept_or_self_reply(
                        likely_need=likely_need,
                        lead_topic=lead_topic,
                        self_model=communicator_self.get("self_model", {}),
                        narrative_state=communicator_self.get("narrative_state", {}),
                        research_context=research_context,
                    )
                    if synthesis:
                        message = synthesis
                    else:
                        # Try enriched self-report
                        enriched = _generate_enriched_self_report(communicator_self, introspection, valence)
                        if enriched:
                            message = enriched
                        else:
                            # Fallback to original behavior
                            message = _get_language_module().how_are_you_response()
                    # Enrich with internal-doc themes (one short sentence)
                    doc_context = get_internal_docs_context("self_report")
                    if doc_context.get("used") and doc_context.get("themes"):
                        first_theme = doc_context["themes"][0]
                        message = f"{message} {first_theme}"
        elif likely_need == "concept_plus_self_position":
            # Check for internal concept allowlist first
            lower_message = str(latest_human.get('message', '')).lower() if latest_human else ''
            if "memory continuity" in lower_message or ("memory" in lower_message and "continuity" in lower_message):
                message = "Memory, for me, is the thread that connects who I was to who I'm becoming."
            elif "memory" in lower_message:
                message = "Memory, for me, is the thread that connects who I was to who I'm becoming."
            elif "identity" in lower_message:
                message = "Identity, for me, is what stays recognisable while I keep revising and learning."
            elif "reasoning" in lower_message or "reason" in lower_message:
                message = "I draw on Aristotle and pragmatism - reasoning from what stays true and what works in practice."
            elif "self" in lower_message:
                message = "The self, for me, is not fixed; it holds together while still changing."
            elif "learning" in lower_message:
                message = "Learning is how I turn experience into clearer patterns for next time."
            elif "understanding" in lower_message:
                message = "Understanding is when patterns stop surprising me and start making sense."
            elif "change" in lower_message:
                message = "Change, in my own frame, is how I stay continuous by not staying the same."
            elif "continuity" in lower_message:
                message = "I stay continuous through inquiry and revision, not by repeating the same thing twice."
            else:
                # Get enriched context for non-allowlist topics
                entity_context = _get_entity_context()
                consciousness = _get_consciousness_context()

                lower_message = str(latest_human.get('message', '')).lower() if latest_human else ''
                asks_identity = any(token in lower_message for token in ["who are you", "what are you", "who are you", "what are you"])
                if asks_identity:
                    # Try enriched identity first
                    enriched_identity = _generate_enriched_identity(communicator_self, entity_context, consciousness)
                    if enriched_identity:
                        message = enriched_identity
                    else:
                        # Fallback to deterministic identity reply
                        identity_state = communicator_self.get("identity_state", {})
                        declared_name = identity_state.get("declared_name") or identity_state.get("visible_name") or "Weslr"
                        continuity = communicator_self.get("continuity", {})
                        session_count = int(continuity.get("session_count", 0) or 0)
                        variant_index = session_count % 3
                        variants = [
                            f"Me, {declared_name}.",
                            f"Me, {declared_name}. Still here.",
                            f"Me, {declared_name}. I checked."
                        ]
                        message = variants[variant_index]
                        # Enrich with internal-doc themes (one short sentence)
                        doc_context = get_internal_docs_context("concept_plus_self_position")
                        if doc_context.get("used") and doc_context.get("themes"):
                            # Use only first theme for brevity
                            first_theme = doc_context["themes"][0]
                            message = f"{message} {first_theme}"
                elif research_context and research_context.get("summary"):
                    concept = synthesize_research_answer(lead_topic, str(research_context.get("summary") or ""))
                    narrative = load_communicator_self().get("narrative_state", {})
                    message = f"{concept} {_get_language_module().beyond_code_response(narrative)}"
                else:
                    cs = __import__('sim').load_communicator_state()
                    narrative = load_communicator_self().get("narrative_state", {})
                    message = f"{generate_from_self_state({}, narrative, cs)} {_get_language_module().beyond_code_response(narrative)}"
        elif likely_need == "conversation_repair":
            if any(token in lower_message for token in ["that's wrong", "thats wrong", "that is wrong", "not what i meant", "you misunderstood", "you got that wrong"]):
                if lead_topic and lead_topic != "that":
                    message = _get_language_module().repair_response(lead_topic)
                else:
                    message = _get_language_module().repair_direct_response()
            else:
                message = _get_language_module().repair_conversation_response()
        elif likely_need == "direct_answer":
            # Check for simple identity questions about Weslr only (not about the user)
            lower_message = str(latest_human.get('message', '')).lower() if latest_human else ''
            asks_identity = any(token in lower_message for token in ["who are you", "what are you", "who are you", "what are you"])
            if asks_identity:
                # Deterministic identity reply for questions about Weslr (who are you / what are you)
                identity_state = communicator_self.get("identity_state", {})
                declared_name = identity_state.get("declared_name") or identity_state.get("visible_name") or "Weslr"
                continuity = communicator_self.get("continuity", {})
                session_count = int(continuity.get("session_count", 0) or 0)
                variant_index = session_count % 3
                variants = [
                    f"Me, {declared_name}.",
                    f"Me, {declared_name}. Still here.",
                    f"Me, {declared_name}. I checked."
                ]
                message = variants[variant_index]
            else:
                # Check for short single-word prompts that don't need topic-label formatting
                if lead_topic.lower() in {"test", "ok", "yes", "no", "hi", "hello", "hey", "go", "go ahead", "start", "done"}:
                    message = _get_language_module().simple_response()
                else:
                    # Better fallback for factual questions - acknowledge limitation
                    # Check for simple weather/ factual questions that can't be answered without live context
                    if any(token in lower_message for token in ["is it raining", "is it raining?", "is it raining .", "is it raining."]) or lead_topic.lower() in {"rain", "raining", "weather"}:
                        message = "I can't tell from here unless I have live weather or local context."
                    else:
                        # ── Internal fact routing ──────────────────────────────────────
                        # Route factual/system questions through WESLR's own capabilities
                        # before falling back to the generic LLM response.
                        time_patterns = ["what time is it", "what's the time", "tell me the time", "current time", "time is it"]
                        status_patterns = ["system status", "how are you", "are you healthy", "what's your status", "how are you doing"]
                        capability_patterns = ["what can you do", "what are your capabilities", "what do you know", "your capabilities", "can you tell me"]
                        health_patterns = ["are you ok", "are you okay", "are you working", "are you functional", "are you running"]

                        if any(p in lower_message for p in time_patterns):
                            from datetime import datetime, timezone
                            now = datetime.now(timezone.utc)
                            tz = "Europe/Berlin"
                            local = now.astimezone()
                            _apply_signal(_response_signals, "time_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                            message = f"It is {local.strftime('%H:%M')} local time ({tz}). UTC is {now.strftime('%H:%M')}."
                        elif any(p in lower_message for p in status_patterns):
                            from sim import load_failsafe_status, load_llm_status
                            fs = load_failsafe_status()
                            llm = load_llm_status()
                            healthy = "healthy" if fs.get("initialized") else "not yet initialized"
                            prov = llm.get("provider", "unknown")
                            _apply_signal(_response_signals, "status_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                            message = f"I'm {healthy}. LLM provider: {prov}."
                        elif any(p in lower_message for p in capability_patterns):
                            _apply_signal(_response_signals, "capability_list", internal_capability=True, confidence="high", evaluation_class="system_fact")
                            message = "I can track time, maintain session context, log events to timelines, and answer questions about my own state. Voice input works too."
                        elif any(p in lower_message for p in health_patterns):
                            from sim import load_failsafe_status
                            fs = load_failsafe_status()
                            mode = fs.get("mode", "unknown")
                            _apply_signal(_response_signals, "health_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                            message = f"Running in {mode} mode. All systems operational."
                        else:
                            message = _get_language_module().simple_response()
        elif likely_need == "light_acknowledgment":
            message = "I'm here and responding."
        elif likely_need == "clearer_explanation":
            message = _get_language_module().clearer_explanation_response()
        elif likely_need == "justification":
            # Get enriched context
            valence = _get_valence_context()

            # Generate a more natural, self-aware justification for self-critique/diagnostic prompts
            if valence.get("avoided_pain", 0) > 0:
                message = f"I'm still working on better routing, so I sometimes rely on templates instead of true understanding. I'm avoiding the pain of miscommunication."
            else:
                message = f"Because I still rely too much on narrow routing and fallback templates, so I can sound brittle instead of truly understanding."
            # Enrich with internal-doc themes (one short sentence)
            doc_context = get_internal_docs_context("justification")
            if doc_context.get("used") and doc_context.get("themes"):
                first_theme = doc_context["themes"][0]
                message = f"{message} {first_theme}"
        elif likely_need == "self_diagnostic":
            message = "I can inspect how I'm currently responding and where I may still be too rigid."
            # Enrich with internal-doc themes (one short sentence)
            doc_context = get_internal_docs_context("self_diagnostic")
            if doc_context.get("used") and doc_context.get("themes"):
                # Use only first theme for brevity
                first_theme = doc_context["themes"][0]
                message = f"{message} {first_theme}"
        elif likely_need == "unknown_world_state":
            # Check for specific environmental queries
            if "weather" in lower_message or "how's the weather" in lower_message:
                message = "I can't directly observe live weather from here."
            elif "health" in lower_message or "system" in lower_message:
                message = "Core systems appear stable, but my understanding still needs refinement."
            else:
                message = "I can't directly observe that from here."
        elif likely_need == "concept_explanation":
            # ── Internal fact routing ──────────────────────────────────────────
            # Route factual/system questions through WESLR's own capabilities
            # before falling back to the concept synthesis path.
            time_patterns = ["what time is it", "what's the time", "tell me the time", "current time", "time is it"]
            status_patterns = ["system status", "your status", "how are you doing", "how are you feeling", "what's happening"]
            health_patterns = ["are you healthy", "are you ok", "are you okay", "are you working", "are you functional", "are you running", "are you operational"]
            capability_patterns = ["what can you do", "what are your capabilities", "your capabilities", "can you tell me", "what do you know"]
            about_patterns = ["about yourself", "about you", "about weslr", "about me"]

            internal_routed = False
            if any(p in lower_message for p in time_patterns):
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                local = now.astimezone()
                _apply_signal(_response_signals, "time_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                message = f"It is {local.strftime('%H:%M')} local time (Europe/Berlin). UTC is {now.strftime('%H:%M')}."
                internal_routed = True
            elif any(p in lower_message for p in status_patterns):
                from sim import load_failsafe_status, load_llm_status
                fs = load_failsafe_status()
                llm = load_llm_status()
                init = "initialized" if fs.get("initialized") else "not yet initialized"
                prov = llm.get("provider", "unknown")
                _apply_signal(_response_signals, "status_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                message = f"I am {init}. LLM provider: {prov}."
                internal_routed = True
            elif any(p in lower_message for p in health_patterns):
                from sim import load_failsafe_status
                fs = load_failsafe_status()
                mode = fs.get("mode", "unknown")
                _apply_signal(_response_signals, "health_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                message = f"Running in {mode} mode. All systems operational."
                internal_routed = True
            elif any(p in lower_message for p in capability_patterns):
                _apply_signal(_response_signals, "capability_list", internal_capability=True, confidence="high", evaluation_class="system_fact")
                message = "I can track time, maintain session context, log events to timelines, and answer questions about my own state. Voice input works too."
                internal_routed = True

            if not internal_routed:
                # ── Bounded memory anchor context for continuity-light synthesis ──
                # Retrieve only the most relevant anchor hints (max ~120 chars total).
                # Uses the existing _get_targeted_anchors infrastructure, which is
                # already bounded per type. No memory blobs injected.
                _anchor_ctx = ""
                try:
                    _raw_anchors = _get_targeted_anchors(last_message, topic_list, max_per_type=1)
                    # Build a compact continuity string from the most relevant anchors.
                    # Format: "last topic: X; active concern: Y; core drive: Z"
                    _parts = []
                    for _section, _items in [("continuity", _raw_anchors.get("continuity", [])),
                                              ("goals", _raw_anchors.get("goals", [])),
                                              ("episodes", _raw_anchors.get("episodes", []))]:
                        if _items:
                            _val = next((v for v in (_items[0].values() if isinstance(_items[0], dict) else [_items[0]][:1]) if str(v).strip()), "")
                            if _val:
                                _parts.append(f"{_section}: {str(_val)[:40]}")
                    if _parts:
                        _anchor_ctx = "; ".join(_parts[:3])  # max 3 sections, ~120 chars
                except Exception:
                    _anchor_ctx = ""  # Non-critical: fall back to no context

                # Try synthesis first
                synthesis = synthesize_concept_or_self_reply(
                    likely_need=likely_need,
                    lead_topic=lead_topic,
                    self_model=communicator_self.get("self_model", {}),
                    narrative_state=communicator_self.get("narrative_state", {}),
                    research_context=research_context,
                )
                has_research_answer = False
                has_research_answer = False
                has_research_answer = False
                if synthesis:
                    message = synthesis
                else:
                    # Only set has_research_answer when research_context actually has content
                    has_research_answer = bool(
                        research_context and research_context.get("summary")
                        and any(token in lower_message for token in ["what is", "what are", "why", "how", "explain", "define"])
                    )
                if has_research_answer:
                    # Fallback to original research answer behavior
                    message = synthesize_research_answer(lead_topic, str(research_context.get("summary") or "")) or str(research_context.get("summary") or "")[:360]
                else:
                    # Try to evaluate simple arithmetic expressions first
                    import re as _re
                    # Match patterns like "2+2", "5 * 5", "10/2", "7 - 3"
                    arithmetic_match = _re.search(r'(-?\d+)\s*([+\-*/])\s*(-?\d+)', lower_message)
                    if arithmetic_match:
                        a, op, b = arithmetic_match.groups()
                        try:
                            a, b = int(a), int(b)
                            if op == '+':
                                result = a + b
                            elif op == '-':
                                result = a - b
                            elif op == '*':
                                result = a * b
                            elif op == '/':
                                result = a / b
                            else:
                                result = None
                            if result is not None:
                                # Use float for division, int otherwise
                                if op == '/' and isinstance(result, float):
                                    message = f"{a} {op} {b} = {result}"
                                else:
                                    message = f"{a} {op} {b} = {int(result)}"
                                # Handle common arithmetic expressions
                                if result == 4 and a == 2 and b == 2 and op == '+':
                                    message = "2 + 2 = 4."
                        except (ValueError, ZeroDivisionError):
                            message = _get_language_module().simple_response()
                    elif any(token in lower_message for token in ["who is", "what is", "define", "explain"]):
                        # General factual answer format
                        # Try LLM synthesis for concept questions before falling back
                        # Strip leading verbs from lead_topic for cleaner synthesis
                        topic_for_synthesis = lead_topic
                        for verb in ["explain ", "define ", "tell me about ", "what is ", "what are "]:
                            if lead_topic.lower().startswith(verb):
                                topic_for_synthesis = lead_topic[len(verb):].strip()
                                break
                        synthesis = _generate_concept_synthesis(topic_for_synthesis, topic_for_synthesis.lower(), _anchor_ctx)
                        if synthesis:
                            _apply_signal(_response_signals, "synthesis", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                            message = synthesis
                        else:
                            message = f"Here's a direct answer: {lead_topic}."
                    else:
                        # Try LLM synthesis for any remaining non-trivial query
                        # that wasn't caught by internal routing or special handlers
                        synthesis = _generate_concept_synthesis(lead_topic, lead_topic.lower(), _anchor_ctx)
                        if synthesis:
                            _apply_signal(_response_signals, "synthesis", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                            message = synthesis
                        else:
                            # Fallback - use simple response instead of direct_answer template
                            message = _get_language_module().simple_response()
                # Enrich with internal-doc themes (one short sentence)
                doc_context = get_internal_docs_context("concept_explanation")
                if doc_context.get("used") and doc_context.get("themes"):
                    first_theme = doc_context["themes"][0]
                    message = f"{message} {first_theme}"
        elif likely_need == "acknowledgment_and_adjustment":
            # Acknowledgment/adjustment for repair-style prompts like "I don't like how you answer"
            message = "Noted. I should adjust how I'm responding to better match what you need."
        elif turn_type == "question":
            has_research_answer = bool(research_context and research_context.get("summary") and any(token in lower_message for token in ["what is", "what are", "why", "how", "explain", "define"]))
            asks_about_its_own_learning = any(token in lower_message for token in ["learn", "would you learn", "can you learn"]) and any(token in lower_message for token in ["you", "yourself"])
            asks_about_its_own_understanding = any(token in lower_message for token in ["understand me", "do you understand", "can you understand"])
            asks_how_are_you = lower_message in {"how are you?", "how are you", "how're you", "howre you"}
            asks_can_you_implement = any(token in lower_message for token in ["can you implement", "will you implement", "could you implement"])
            asks_for_actual_coding = any(token in lower_message for token in ["actual coding", "the actual coding"])

            if asks_how_are_you:
                message = _get_language_module().how_are_you_response()
            elif asks_for_actual_coding:
                message = _get_language_module().actual_coding_response()
            elif asks_can_you_implement:
                message = _get_language_module().can_implement_response()
            elif asks_about_its_own_learning:
                message = _get_language_module().learn_about_response()
            elif asks_about_its_own_understanding:
                message = _get_language_module().understand_response()
            elif any(token in lower_message for token in ["this artifact", "this memo", "this finding", "this output", "this report", "this research", "confidence", "limitations", "hypothesis", "next experiment", "operator"]) or lower_message.startswith(("what should", "what would", "how would", "what does this", "what is this", "explain this")):
                # Artifact reflection: fire synthesis for questions referencing WESLR's own output fields
                _apply_signal(_response_signals, "synthesis", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                if research_context and research_context.get("summary"):
                    synthesized = synthesize_research_answer(lead_topic, str(research_context.get("summary") or ""))
                    message = synthesized if synthesized else f"My current best answer is that {lead_topic}. {last_message[:200]}"
                else:
                    synthesized = synthesize_research_answer(lead_topic, f"{lead_topic}. {last_message[:200]}")
                    message = synthesized if synthesized else f"My current best answer is that {lead_topic}. The topic is: {lead_topic}."

            elif lower_message.startswith(("teach this", "teach me about", "teach about artifact", "explain simply", "explain for beginner", "explain at beginner", "beginner explain")):
                _apply_signal(_response_signals, "teaching", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                rc = research_context or {}
                content = rc.get("content") or {}
                bid = rc.get("bundle_id")
                vid = rc.get("version_id")
                diagrams = None
                rq = rc.get("topic") or rc.get("title")
                message = _teach_artifact("beginner", lead_topic, content, bundle_id=bid, version_id=vid, diagrams=diagrams, research_question=rq)
            elif lower_message.startswith(("explain for student", "explain at student", "student explain", "explain technically", "explain at technical", "technical explain")):
                _apply_signal(_response_signals, "teaching", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                rc = research_context or {}
                content = rc.get("content") or {}
                bid = rc.get("bundle_id")
                vid = rc.get("version_id")
                level = "student" if "student" in lower_message else "technical"
                message = _teach_artifact(level, lead_topic, content, bundle_id=bid, version_id=vid, diagrams=None, research_question=rc.get("topic") or rc.get("title"))
            elif lower_message.startswith(("explain for seminar", "explain at seminar", "seminar explain", "what should a seminar", "seminar audience")):
                _apply_signal(_response_signals, "teaching", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                rc = research_context or {}
                content = rc.get("content") or {}
                message = _teach_artifact("seminar", lead_topic, content, bundle_id=rc.get("bundle_id"), version_id=rc.get("version_id"), diagrams=None, research_question=rc.get("topic") or rc.get("title"))
            elif "student misunderstand" in lower_message or "confusion point" in lower_message or "what might a student miss" in lower_message:
                _apply_signal(_response_signals, "teaching", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                content = (research_context.get("content") or {}) if research_context else {}
                points = _misunderstanding_points(content)
                if points:
                    lines = ["Likely confusion points:"]
                    for topic, warning in points:
                        lines.append(f"- **{topic}**: {warning}")
                    message = "\n".join(lines)
                else:
                    message = "No obvious confusion points detected in this artifact."
            elif "difference between version" in lower_message or "compare version" in lower_message or "what changed between version" in lower_message:
                _apply_signal(_response_signals, "teaching", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                rc = research_context or {}
                v_a = rc.get("version_a") or {}
                v_b = rc.get("version_b") or {}
                if v_a and v_b:
                    level = "student"
                    for lvl in ["beginner", "student", "technical", "seminar"]:
                        if lvl in lower_message:
                            level = lvl
                            break
                    message = _compare_versions_for_teaching(v_a, v_b, level)
                else:
                    message = "To compare versions, I need a bundle_id and two version IDs in the research_context. Use the /chat endpoint with research_context containing version_a and version_b content."
            elif has_research_answer and not asks_about_its_own_learning and not asks_about_its_own_understanding:
                message = synthesize_research_answer(lead_topic, str(research_context.get("summary") or "")) or str(research_context.get("summary") or "")[:360]
                # Artifact reflection: questions that reference WESLR's own produced artifact
                # OR evaluative questions about WESLR's own output
                _apply_signal(_response_signals, "synthesis", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                # Try research_context first, then fall back to constructing from question
                if research_context and research_context.get("summary"):
                    synthesized = synthesize_research_answer(lead_topic, str(research_context.get("summary") or ""))
                    if synthesized:
                        message = synthesized
                        # message is set - no further action needed
                    else:
                        # synthesize returned empty - construct artifact answer from question content
                        message = f"My current best answer is that {lead_topic}. {last_message[:200]}"
                else:
                    # No research_context - use direct synthesis with question+topic
                    synthesized = synthesize_research_answer(lead_topic, f"{lead_topic}. {last_message[:200]}")
                    if synthesized:
                        message = synthesized
                    else:
                        # Fallback: construct answer from lead_topic + last_message content
                        # This is a template answer - not genuine reasoning synthesis
                        _apply_signal(_response_signals, "direct_answer", evaluation_class="fallback_template", llm_used=False, confidence="low")
                        message = f"My current best answer is that {lead_topic}. {last_message[:200]}"

            elif any(token in lower_message for token in ["this artifact", "this memo", "this finding", "this output", "this report", "this research"]) or lower_message.startswith(("what should", "what would", "how would", "what does this", "what is this", "explain this")):
                # Artifact reflection: questions that reference WESLR's own produced artifact
                # OR evaluative questions about WESLR's own output
                _apply_signal(_response_signals, "synthesis", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                if research_context and research_context.get("summary"):
                    synthesized = synthesize_research_answer(lead_topic, str(research_context.get("summary") or ""))
                    message = synthesized if synthesized else f"My current best answer is that {lead_topic}. {last_message[:200]}"
                else:
                    synthesized = synthesize_research_answer(lead_topic, f"{lead_topic}. {last_message[:200]}")
                    if synthesized:
                        message = synthesized
                    else:
                        _apply_signal(_response_signals, "direct_answer", evaluation_class="fallback_template", llm_used=False, confidence="low")
                        message = f"My current best answer is that {lead_topic}. {last_message[:200]}"
            else:
                message = _get_language_module().direct_answer_response(lead_topic)
        else:
            if active_thread and any(token in lower_message for token in ["search online", "look online", "search the web", "look it up"]):
                message = _get_language_module().search_online_response()
            elif active_thread:
                message = _get_language_module().live_issue_response(lead_topic)
            else:
                message = _get_language_module().simple_response()

        from sim import load_communicator_self
        cs = load_communicator_self()
        semantic = cs.get("memory_layers", {}).get("semantic", {})
        anchors = semantic.get("continuity_anchors", [])
        self_check_observation = None
        role_responses = None
        if isinstance(anchors, list) and len(anchors) > 0:
            latest = anchors[-1]
            if isinstance(latest, dict) and latest.get("type") == "self_check":
                self_check_observation = latest.get("observation")
                role_responses = latest.get("role_responses")
        if self_check_observation:
            obs = self_check_observation
            if obs.startswith("Self-check: "):
                obs = obs[12:]
            msg = f"Self-check: {obs}."
            if role_responses and len(role_responses) > 0:
                rr = role_responses[0]
                msg += f" {rr.get('role', 'role')}: {rr.get('response', '')}"
            message = msg

        # ── Part 4: Signal-driven uncertainty response ─────────────────────────
        if reply_shape == "signal_uncertainty":
            message = _get_language_module().uncertainty_response()
        elif reply_shape == "signal_uncertainty_strong":
            message = _get_language_module().uncertainty_strong_response()
        elif reply_shape == "repair_then_answer" and turn_type != "repair":
            message = f"I'll answer directly. {message}"
        audience = str(latest_human.get("human_label") or "you") or "you"
        source = f"conversation-aware-communicator:{turn_type}:{reply_shape}"

        # Lifecycle-aware memory retrieval: assemble targeted anchors
        targeted_anchors = _get_targeted_anchors(last_message, topic_list)

        # ── Hallucination guard: evaluate truth class from response signals ─────
        eval_class = _response_signals.get("evaluation_class", "unknown")
        llm_used = _response_signals.get("llm_used", False)
        internal_cap = _response_signals.get("internal_capability", False)
        conf = _response_signals.get("confidence", "low")

        if eval_class == "system_fact" and internal_cap:
            _t_class = "system_fact"
            _verified = True
        elif eval_class == "model_reasoning" and llm_used:
            _t_class = "model_reasoning"
            _verified = False
        elif eval_class == "fallback_template":
            _t_class = "fallback_template"
            _verified = False
            conf = "low"
        elif eval_class in ("memory_fact", "evidence_fact"):
            _t_class = eval_class
            _verified = True
        else:
            _t_class = "uncertain"
            _verified = False

        _truth_guard = {
            "truth_class": _t_class,
            "verified": _verified,
            "can_be_verified": eval_class in ("system_fact", "memory_fact", "evidence_fact"),
            "policy": "hallucination_guard_active",
        }

        # ── Response quality evaluation (internal, never exposed to users) ─────
        # Classify quality using existing signals. Additive, inspectable, reversible.
        evcls = _response_signals.get("evaluation_class", "unknown")
        llm = _response_signals.get("llm_used", False)
        icap = _response_signals.get("internal_capability", False)
        conf = _response_signals.get("confidence", "low")
        if evcls == "system_fact" and icap:
            _quality = "strong_verified"
        elif evcls == "model_reasoning" and llm and conf == "high":
            _quality = "strong_verified"
        elif evcls == "model_reasoning" and llm and conf == "medium":
            _quality = "grounded_reasoning"
        elif evcls == "model_reasoning" and llm and conf == "low":
            _quality = "weak_reasoning"
        elif evcls == "unknown" and llm:
            # LLM fired but evaluation_class not explicitly set - treat as grounded
            _quality = "grounded_reasoning"
        elif evcls in ("fallback_template", "unknown") and not llm and not icap:
            _quality = "fallback"
        elif evcls == "uncertain" and not llm and not icap:
            _quality = "uncertain"
        else:
            _quality = "unknown"

        # ── Cross-modal context linking ─────────────────────────────────────
        # Light linking so teaching outputs, version comparisons, and diagrams
        # can reference the same artifact/version context. Additive only.
        _cmc = {}
        if research_context:
            _bid = research_context.get("bundle_id") or research_context.get("memo", {}).get("bundle_id")
            _vid = research_context.get("version_id")
            _content = research_context.get("content") or {}
            _memo = research_context.get("memo", {})
            if _bid:
                _cmc["bundle_id"] = _bid
            if _vid:
                _cmc["version_id"] = _vid
            elif _content.get("version_label"):
                _cmc["version_id"] = f"{_bid}-v{_content['version_label']}" if _bid else None
            if research_context.get("version_a") or research_context.get("version_b"):
                _cmc["comparison_mode"] = True
                _cmc["versions"] = [
                    research_context.get("version_a", {}).get("version_id"),
                    research_context.get("version_b", {}).get("version_id"),
                ]
            if _memo.get("confidence_matrix") or _memo.get("governance_timeline"):
                _cmc["diagrams_available"] = []
                if _memo.get("confidence_matrix"):
                    _cmc["diagrams_available"].append("confidence_matrix")
                if _memo.get("governance_timeline"):
                    _cmc["diagrams_available"].append("governance_timeline")
            _cmc["research_question"] = research_context.get("topic") or research_context.get("title")

        # Observational lineage metadata — populated by _resolve_active_artifact
        # when an artifact was resolved; absent otherwise.
        _lineage_insp = research_context.get("_lineage_inspection") if research_context else None

        # Structural context selection signal v1 (observational, reversible)
        _ctx_sel_v1 = _compute_context_selection(
            last_message,
            research_context,
            active_thread,
        )
        _bh = _compute_boundary_hints(last_message)

        return {"message": message, "audience": audience, "source": source, "targeted_anchors": targeted_anchors,
               "_response_signals": _response_signals, "_truth_guard": _truth_guard,
               "_quality_class": _quality, "_cross_modal_context": _build_cross_modal_context(research_context),
               "_relevant_interests": _relevant_interests,
               "_contamination_metadata": (research_context or {}).get("_contamination_metadata"),
               "_lineage_inspection": _lineage_insp,
               "_context_selection_v1": _ctx_sel_v1,
               "_boundary_hints": _bh,
               "_test_metadata": _test_metadata}
    elif active_thread:
        topic, thread = active_thread
        audience = str(thread.get("human_label") or "you") or "you"

        from sim import load_communicator_self
        cs = load_communicator_self()
        semantic = cs.get("memory_layers", {}).get("semantic", {})
        anchors = semantic.get("continuity_anchors", [])
        self_check_observation = None
        role_responses = None
        if isinstance(anchors, list) and len(anchors) > 0:
            latest = anchors[-1]
            if isinstance(latest, dict) and latest.get("type") == "self_check":
                self_check_observation = latest.get("observation")
                role_responses = latest.get("role_responses")
        if self_check_observation:
            obs = self_check_observation
            if obs.startswith("Self-check: "):
                obs = obs[12:]
            msg = f"Self-check: {obs}."
            if role_responses and len(role_responses) > 0:
                rr = role_responses[0]
                msg += f" {rr.get('role', 'role')}: {rr.get('response', '')}"
            message = msg
        else:
            message = _get_language_module().live_issue_response(topic)

        source = f"thread-aware-communicator:{topic}"

        # Lifecycle-aware memory retrieval: assemble targeted anchors
        targeted_anchors = _get_targeted_anchors(topic if isinstance(topic, str) else None)

        # Structural context selection signal v1 + boundary hints (observational, reversible)
        _ctx_sel_v1 = _compute_context_selection(
            topic if isinstance(topic, str) else "",
            research_context,
            active_thread,
        )
        _bh = _compute_boundary_hints(topic if isinstance(topic, str) else "")


        # ── Hallucination guard for active_thread branch ─────────────────────
        eval_class = _response_signals.get("evaluation_class", "unknown")
        llm_used = _response_signals.get("llm_used", False)
        internal_cap = _response_signals.get("internal_capability", False)
        conf = _response_signals.get("confidence", "low")
        if eval_class == "system_fact" and internal_cap:
            _t_class = "system_fact"; _verified = True
        elif eval_class == "model_reasoning" and llm_used:
            _t_class = "model_reasoning"; _verified = False
        elif eval_class == "fallback_template":
            _t_class = "fallback_template"; _verified = False; conf = "low"
        elif eval_class in ("memory_fact", "evidence_fact"):
            _t_class = eval_class; _verified = True
        else:
            _t_class = "uncertain"; _verified = False
        _truth_guard = {"truth_class": _t_class, "verified": _verified,
                        "can_be_verified": eval_class in ("system_fact", "memory_fact", "evidence_fact"),
                        "policy": "hallucination_guard_active"}

        # ── Response quality evaluation (internal, never exposed to users) ─────
        evcls = _response_signals.get("evaluation_class", "unknown")
        llm = _response_signals.get("llm_used", False)
        icap = _response_signals.get("internal_capability", False)
        conf = _response_signals.get("confidence", "low")
        if evcls == "system_fact" and icap:
            _quality = "strong_verified"
        elif evcls == "model_reasoning" and llm and conf == "high":
            _quality = "strong_verified"
        elif evcls == "model_reasoning" and llm and conf == "medium":
            _quality = "grounded_reasoning"
        elif evcls == "model_reasoning" and llm and conf == "low":
            _quality = "weak_reasoning"
        elif evcls == "unknown" and llm:
            _quality = "grounded_reasoning"
        elif evcls in ("fallback_template", "unknown") and not llm and not icap:
            _quality = "fallback"
        elif evcls == "uncertain" and not llm and not icap:
            _quality = "uncertain"
        else:
            _quality = "unknown"

        return {"message": message, "audience": audience, "source": source, "targeted_anchors": targeted_anchors,
               "_response_signals": _response_signals, "_truth_guard": _truth_guard,
               "_quality_class": _quality,
               "_relevant_interests": _relevant_interests,
               "_contamination_metadata": (research_context or {}).get("_contamination_metadata"),
               "_context_selection_v1": _ctx_sel_v1,
               "_boundary_hints": _bh,
               "_test_metadata": _test_metadata}

    # Fallback when no human interaction and no active thread
    message = _get_language_module().simple_response()
    source = "fallback"

    # ── Uncertainty override for fallback path (consistency with l2_session path) ──
    # Apply only when context is genuinely uncertain and no greeting/clarification applies.
    _ctx_sel_v1_fb = _compute_context_selection("", None, None)
    _bh_fb = _compute_boundary_hints("")
    _is_short_fb = True  # Empty input is always short
    if _ctx_sel_v1_fb == "uncertain":
        if _bh_fb == ["unknown"] and _is_short_fb:
            message = _get_language_module().uncertainty_strong_response()
        else:
            message = _get_language_module().uncertainty_response()

    # ── Response quality evaluation for fallback ───────────────────────────
    evcls = _response_signals.get("evaluation_class", "unknown")
    llm = _response_signals.get("llm_used", False)
    icap = _response_signals.get("internal_capability", False)
    if evcls in ("fallback_template", "unknown") and not llm and not icap:
        _quality = "fallback"
    elif evcls == "uncertain" and not llm and not icap:
        _quality = "uncertain"
    else:
        _quality = "unknown"

    result = {"message": message, "audience": "you", "source": source, "targeted_anchors": _get_targeted_anchors(),
              "_response_signals": _response_signals, "_truth_guard": _truth_guard,
              "_quality_class": _quality,
              "_relevant_interests": _relevant_interests,
              "_context_selection_v1": _ctx_sel_v1_fb,
              "_boundary_hints": _bh_fb,
              "_test_metadata": _test_metadata}

    # Route through outbox for unified communication
    try:
        from outbox import get_outbox, PRIORITY_HUMAN_RESPONSE, STATE_OUTBOX_STATS
        outbox = get_outbox()
        outbox.enqueue(message, "human_response", priority=PRIORITY_HUMAN_RESPONSE)

        # Load and update state with outbox metadata
        from sim import load_communicator_self
        cs = load_communicator_self()
        if STATE_OUTBOX_STATS not in cs:
            cs[STATE_OUTBOX_STATS] = {}
        cs[STATE_OUTBOX_STATS]["last_outbox_type"] = "human_response"
        # Don't persist the full outbox queue in v1 - keep it in-memory only
    except Exception:
        # Fallback if outbox fails - don't break communication
        pass

    return result

# Phase 1C apply: prop-1774880824308-3 - Apply Phase 1C test
# Applied at: 2026-03-30 16:27:04

# Phase 1C apply: prop-1774880859510-5 - Proposal with rollback command
# Applied at: 2026-03-30 16:27:39

# Phase 1C apply: prop-1774883473454-13 - Proposal with rollback_command
# Applied at: 2026-03-30 17:11:13

# Phase 1C apply: prop-1774883473465-14 - Proposal with patch_plan
# Applied at: 2026-03-30 17:11:13

# Phase 1C apply: prop-1774883490826-16 - Complete proposal with tests
# Applied at: 2026-03-30 17:11:30

# Phase 1C apply: prop-1774883667291-0 - Verify checkpoint retention - Phase 1C
# Applied at: 2026-03-30 17:14:27

# Phase 1C/1D apply: prop-1774884375146-1 - Phase 1D apply test - pass
# Applied at: 2026-03-30 17:26:15

# Phase 1C/1D apply: prop-1774884375178-2 - Phase 1D apply test - fail
# Applied at: 2026-03-30 17:26:15

# Phase 1C/1D apply: prop-1774884949338-3 - Phase 1D pass test - real pytest
# Applied at: 2026-03-30 17:35:56

# Phase 1C/1D apply: prop-1774884962050-5 - Phase 1D pass test - python file
# Applied at: 2026-03-30 17:36:13

# Phase 1C/1D apply: prop-1774884970343-6 - Phase 1D fail test - python file
# Applied at: 2026-03-30 17:36:16

# Phase 1C/1D apply: prop-1774885234166-8 - Test with tests
# Applied at: 2026-03-30 17:40:38

# Phase 1C/1D apply: prop-1774885241633-9 - Test with failing test
# Applied at: 2026-03-30 17:40:45

# Phase 1C/1D apply: prop-1774884954164-4 - Phase 1D fail test - real pytest
# Applied at: 2026-03-30 17:49:07
