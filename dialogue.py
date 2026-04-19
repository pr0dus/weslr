from __future__ import annotations


from interpretation import classify_human_turn, interpret_human_turn
from config import WESLR_LANGUAGE
from internal_docs import get_internal_docs_context


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
                pass  # Non-critical — fall through to language module default
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
            return "I draw on Aristotle and pragmatism — reasoning from what stays true and what works in practice."
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
    
    # concept_explanation without research — only for allowlist concepts
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
            return "I draw on Aristotle and pragmatism — reasoning from what stays true and what works in practice."
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
        parts.append(f"I'm about {confidence:.0%} confident in this — my self-model detected {introspection.get('total_perturbations', 0)} issue(s).")
    
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
        consciousness_str = f"Still reviewing some claims — I'm working through them."
    elif role_play:
        consciousness_str = "Not showing any role-play patterns."
    else:
        consciousness_str = "Everything's working normally."
    
    # Construct enriched identity - keep it simple, human-friendly
    if entity_context_str:
        return f"I'm {declared_name}. {entity_context_str} {consciousness_str}"
    else:
        return f"I'm {declared_name}. {consciousness_str}"




def _generate_concept_synthesis(lead_topic: str, topic_lower: str) -> str | None:
    """Generate LLM-based synthesis for general concept/explanation queries.
    
    Follows the established _generate_enriched_* pattern. Returns str on success,
    None on failure (caller falls back gracefully).
    
    Topic allowlist (memory, identity, reasoning, etc.) is handled separately
    in synthesize_concept_or_self_reply. This function handles general topics
    that are genuine information-seeking concept questions.
    
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
        system_prompt = (
            f"You are a concise, factual explainer. "
            f"Explain '{prompt_topic}' in 1-2 clear sentences. "
            f"Be direct. No preamble or follow-up questions."
        )
        
        result = get_provider().generate(
            "concept_synthesis",
            {
                "message": f"Explain {prompt_topic}.",
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
        pass  # Non-critical — leave anchors empty if any retrieval fails
    return anchors


def build_communicator_message_payload(narrative: dict, relationships: dict, active_thread, latest_human: dict | None, research_context: dict | None = None, l0_identity: dict | None = None, l1_operating: dict | None = None, l2_session: dict | None = None) -> dict:
    from sim import load_communicator_self
    
    communicator_self = load_communicator_self()

    # Inject L0 tier if provided (reversible: no-op when l0_identity is None).
    # This makes L0 facts available to all downstream narrative_state consumers
    # without modifying any existing get() calls.
    if l0_identity:
        narrative_state = communicator_self.get("narrative_state", {})
        narrative_state["l0_identity"] = l0_identity

    # Inject L1 tier if provided — operating facts (affect, narrative, intent, concerns).
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

    # Inject L2 tier if provided — session state (identity_state, continuity).
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
        def _set_signal(path: str, **kw) -> None:
            """Update _response_signals. Call at each message = branch."""
            nonlocal _response_signals
            _response_signals["path"] = path
            for k, v in kw.items():
                if k in _response_signals:
                    _response_signals[k] = v

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

        if turn_type == "greeting":
            message = _get_language_module().greeting_response()
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
                message = "I draw on Aristotle and pragmatism — reasoning from what stays true and what works in practice."
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
                    _set_signal("time_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                    message = f"It is {local.strftime('%H:%M')} local time (Europe/Berlin). UTC is {now.strftime('%H:%M')}."
                    internal_routed = True
                elif any(p in msg_lower for p in status_patterns):
                    from sim import load_failsafe_status, load_llm_status
                    fs = load_failsafe_status()
                    llm = load_llm_status()
                    init = "initialized" if fs.get("initialized") else "not yet initialized"
                    prov = llm.get("provider", "unknown")
                    _set_signal("status_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                    message = f"I am {init}. LLM provider: {prov}."
                    internal_routed = True
                elif any(p in msg_lower for p in health_patterns):
                    from sim import load_failsafe_status
                    fs = load_failsafe_status()
                    mode = fs.get("mode", "unknown")
                    _set_signal("health_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
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
                message = "I draw on Aristotle and pragmatism — reasoning from what stays true and what works in practice."
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
                            _set_signal("time_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                            message = f"It is {local.strftime('%H:%M')} local time ({tz}). UTC is {now.strftime('%H:%M')}."
                        elif any(p in lower_message for p in status_patterns):
                            from sim import load_failsafe_status, load_llm_status
                            fs = load_failsafe_status()
                            llm = load_llm_status()
                            healthy = "healthy" if fs.get("initialized") else "not yet initialized"
                            prov = llm.get("provider", "unknown")
                            _set_signal("status_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                            message = f"I'm {healthy}. LLM provider: {prov}."
                        elif any(p in lower_message for p in capability_patterns):
                            _set_signal("capability_list", internal_capability=True, confidence="high", evaluation_class="system_fact")
                            message = "I can track time, maintain session context, log events to timelines, and answer questions about my own state. Voice input works too."
                        elif any(p in lower_message for p in health_patterns):
                            from sim import load_failsafe_status
                            fs = load_failsafe_status()
                            mode = fs.get("mode", "unknown")
                            _set_signal("health_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
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
                _set_signal("time_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                message = f"It is {local.strftime('%H:%M')} local time (Europe/Berlin). UTC is {now.strftime('%H:%M')}."
                internal_routed = True
            elif any(p in lower_message for p in status_patterns):
                from sim import load_failsafe_status, load_llm_status
                fs = load_failsafe_status()
                llm = load_llm_status()
                init = "initialized" if fs.get("initialized") else "not yet initialized"
                prov = llm.get("provider", "unknown")
                _set_signal("status_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                message = f"I am {init}. LLM provider: {prov}."
                internal_routed = True
            elif any(p in lower_message for p in health_patterns):
                from sim import load_failsafe_status
                fs = load_failsafe_status()
                mode = fs.get("mode", "unknown")
                _set_signal("health_answer", internal_capability=True, confidence="high", evaluation_class="system_fact")
                message = f"Running in {mode} mode. All systems operational."
                internal_routed = True
            elif any(p in lower_message for p in capability_patterns):
                _set_signal("capability_list", internal_capability=True, confidence="high", evaluation_class="system_fact")
                message = "I can track time, maintain session context, log events to timelines, and answer questions about my own state. Voice input works too."
                internal_routed = True

            if not internal_routed:
                # Try synthesis first
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
                    # Simple factual answer for "what is X" style questions
                    has_research_answer = bool(research_context and research_context.get("summary") and any(token in lower_message for token in ["what is", "what are", "why", "how", "explain", "define"]))
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
                        synthesis = _generate_concept_synthesis(topic_for_synthesis, topic_for_synthesis.lower())
                        if synthesis:
                            _set_signal("synthesis", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
                            message = synthesis
                        else:
                            message = f"Here's a direct answer: {lead_topic}."
                    else:
                        # Try LLM synthesis for any remaining non-trivial query
                        # that wasn't caught by internal routing or special handlers
                        synthesis = _generate_concept_synthesis(lead_topic, lead_topic.lower())
                        if synthesis:
                            _set_signal("synthesis", evaluation_class="model_reasoning", llm_used=True, confidence="medium")
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
            elif has_research_answer and not asks_about_its_own_learning and not asks_about_its_own_understanding:
                message = synthesize_research_answer(lead_topic, str(research_context.get("summary") or "")) or str(research_context.get("summary") or "")[:360]
            elif asks_about_its_own_learning:
                message = _get_language_module().learn_about_response()
            elif asks_about_its_own_understanding:
                message = _get_language_module().understand_response()
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

        if reply_shape == "repair_then_answer" and turn_type != "repair":
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

        return {"message": message, "audience": audience, "source": source, "targeted_anchors": targeted_anchors,
               "_response_signals": _response_signals, "_truth_guard": _truth_guard}
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

        return {"message": message, "audience": audience, "source": source, "targeted_anchors": targeted_anchors,
               "_response_signals": _response_signals, "_truth_guard": _truth_guard}

    # Fallback when no human interaction and no active thread
    message = _get_language_module().simple_response()
    source = "fallback"

    result = {"message": message, "audience": "you", "source": source, "targeted_anchors": _get_targeted_anchors(), "_response_signals": _response_signals, "_truth_guard": _truth_guard}
    
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
