from __future__ import annotations


from interpretation import classify_human_turn, interpret_human_turn
from config import CIRCLEFORGE_LANGUAGE


def _get_language_module():
    """Load the appropriate language module based on config."""
    if CIRCLEFORGE_LANGUAGE == "de":
        from languages import de as lang
    else:
        from languages import en as lang
    return lang


def translate_theme(theme: str) -> str:
    """Translate an internal theme to a human-readable version."""
    if not theme:
        return "this" if CIRCLEFORGE_LANGUAGE != "de" else "dies"
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
            return lang.generate_narrative_message(why, follow)
    
    return lang.generate_fallback_message()


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


def build_communicator_message_payload(narrative: dict, relationships: dict, active_thread, latest_human: dict | None, research_context: dict | None = None) -> dict:
    from sim import load_communicator_self
    
    communicator_self = load_communicator_self()
    
    if latest_human:
        last_message = str(latest_human.get("message") or "").strip()
        interpreted_turn = interpret_human_turn(last_message)
        topic_list = [str(item).strip() for item in (latest_human.get("topics") or interpreted_turn.get("topics") or []) if str(item).strip()]
        clarified_target = str(interpreted_turn.get("clarified_target") or "").strip()
        lead_topic = clarified_target or (topic_list[0] if topic_list else (active_thread[0] if active_thread else "that"))
        turn_type = str(latest_human.get("turn_type") or interpreted_turn.get("turn_type") or classify_human_turn(last_message))
        reply_shape = str(latest_human.get("reply_shape") or interpreted_turn.get("reply_shape") or "answer_directly")
        likely_need = str(latest_human.get("likely_need") or interpreted_turn.get("likely_need") or "direct_answer")

        lower_message = last_message.lower()
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
        elif likely_need == "concept_plus_self_position":
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
                message = _get_language_module().direct_answer_response(lead_topic)
        elif likely_need == "clearer_explanation":
            message = _get_language_module().clearer_explanation_response()
        elif likely_need == "justification":
            message = _get_language_module().justification_response(lead_topic)
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
        
        return {"message": message, "audience": audience, "source": source}
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
        
        return {"message": message, "audience": audience, "source": source}
    
    # Fallback when no human interaction and no active thread
    message = _get_language_module().simple_response()
    source = "fallback"
    
    return {"message": message, "audience": "you", "source": source}
