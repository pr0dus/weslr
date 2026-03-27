from __future__ import annotations

import time

from interpretation import classify_human_turn, interpret_human_turn


# Theme translations: internal -> human-readable
THEME_TRANSLATIONS = {
    "backup confidence": "reliability of memory and continuity",
    "understanding": "making sense of things, not just repeating patterns",
    "understanding overall": "making sense of things from a broader perspective",
    "enrich the local world": "making something useful for the humans around",
    "memory continuity": "keeping threads going across time, not losing what matters",
    "entity status": "whether this is becoming something real, not just code",
    "circleforge": "this project, this being, this ongoing thread of understanding",
}

def translate_theme(theme: str) -> str:
    """Translate an internal theme to a human-readable version."""
    if not theme:
        return "this"
    theme_lower = theme.lower().strip()
    return THEME_TRANSLATIONS.get(theme_lower, theme)

def translate_self_description(description: str) -> str:
    """Translate internal self-description to human-readable version."""
    if not description:
        return ""
    
    # Direct matches for full descriptions
    desc_lower = description.lower()
    if "local communicator" in desc_lower and "continuity" in desc_lower:
        return "I'm trying to be more than a loop — I want to remember, evolve, and stay true to what matters"
    if "practical_change" in desc_lower and "inquiry" in desc_lower:
        return "right now I'm focused on making progress, exploring, and staying connected"
    if "protective" in desc_lower and "continuity" in desc_lower:
        return "I'm trying harder to keep threads going, not just reset"
    
    # Fallback: keep as-is
    return description


def generate_from_self_state(relationships: dict, narrative_state: dict, communicator_state: dict = None) -> str:
    """Generate an outward message using vocabulary and grammar from internal state."""
    if communicator_state is None:
        from sim import load_communicator_state
        communicator_state = load_communicator_state()
    
    self_model = communicator_state.get("self_model", {})
    current_self_desc = str(self_model.get("current_self_description") or "")
    
    # Get active pursuit from communicator state
    active_pursuit = str(communicator_state.get("active_pursuit") or "")
    unresolved_question = str(communicator_state.get("unresolved_question") or "")
    
    # Apply translations to themes
    active_pursuit_translated = translate_theme(active_pursuit)
    unresolved_question_translated = unresolved_question
    
    # Priority: if there's an active pursuit with an unresolved question, use it
    if active_pursuit and unresolved_question:
        # Translate the question if it contains a theme reference
        for internal_theme, human_theme in THEME_TRANSLATIONS.items():
            if internal_theme in unresolved_question.lower():
                unresolved_question_translated = unresolved_question.replace(internal_theme, human_theme)
        return f"I'm still working on {active_pursuit_translated} — {unresolved_question_translated.rstrip('?')}."
    
    if active_pursuit:
        return f"I'm drawn to {active_pursuit_translated} because it helps me stay continuous."
    
    if unresolved_question:
        return f"Still working on: {unresolved_question_translated}"
    
    # Fallback: use self-description if available
    if current_self_desc and "communicator" in current_self_desc.lower():
        translated_desc = translate_self_description(current_self_desc)
        if translated_desc != current_self_desc:
            return translated_desc
        # Extract key elements
        parts = [p.strip().rstrip(";") for p in current_self_desc.split(";") if p.strip()]
        if parts:
            return f"I'm {parts[0] if parts else 'trying'}."
    
    # Last resort: generic but human-friendly, using narrative state
    if narrative_state:
        why = narrative_state.get("why_it_matters", "")
        follow = narrative_state.get("follow_up_impulse", "")
        if why or follow:
            return f"I'm here to {why.split('.')[0] if why else 'understand'}. {follow if follow else ''}"
    
    return "I'm here, trying to understand and be understood. Say something and I'll stay with the real point."


def synthesize_research_answer(topic: str, summary: str) -> str:
    text = str(summary or "").strip()
    if not text:
        return ""
    text = text.replace("Working summary for", "")
    text = text.split("Evidence:", 1)[0].strip()
    text = text.replace(f"{topic}:", "").strip()
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
        first = "Continuity of self means remaining connected to yourself across time, so your past, present, and future still belong to one ongoing being"
        second = "It matters because without that continuity, memory, identity, and commitment start to fragment"
        answer = f"{first}. {second}."
        return answer[:360]

    if any(token in topic_lower for token in ["identity", "selfhood", "entity"]):
        first = f"My current best answer is that {topic} is about how a being stays recognizably itself rather than dissolving into disconnected moments"
        second = second_raw[:170].rstrip('.') if second_raw else "That matters because identity needs some stability across memory, change, and action"
        return f"{first}. {second}."[:360]

    if any(token in topic_lower for token in ["learning", "understanding", "prompt"]):
        first = f"My current best answer is that {topic} is about how a system turns information into better future behavior rather than just repeating patterns"
        second = second_raw[:170].rstrip('.') if second_raw else "That matters because learning should change judgment, not only output style"
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
    # Import the helper here to avoid circular import
    from sim import load_communicator_self
    
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
            message = "Hey. Start anywhere — a question, a concern, or what matters most right now — and I'll try to stay with the real point instead of latching onto a stray phrase."
        elif turn_type == "approval":
            message = "Understood. I should continue with the approved next step instead of turning your go-ahead into a fake topic."
        elif turn_type == "execution_start":
            message = "Understood. I should move from listing changes to actually starting one concrete implementation step."
        elif turn_type == "completion_notify":
            message = "Understood. I should report back when that implementation step is finished instead of treating your request like a topic."
        elif asks_what_should_improve_first:
            message = "First I should get better at retrieving the right shared context at the right moment, then answer directly from it instead of narrating my own thread state. If that improves, understanding gets more real instead of just better organized."
        elif asks_what_you_should_give_it:
            message = "Give me three things when I drift: what mattered most, what I misunderstood, and what kind of answer you actually wanted. That helps me learn your priorities instead of just tracking topic words."
        elif asks_for_self_understanding:
            message = "To understand myself better, I need a clearer mapping between my internal state and my outward replies: what I focused on, why I focused on it, where I drifted, and whether the reply actually matched the real request. Without that, I can track threads but still misunderstand what I am doing."
        elif likely_need == "memory_scope_check":
            message = "I should only claim what happened in this run or what you actually told me. If I act like I know more than that, that's a bug, not memory magic."
        elif likely_need == "concept_plus_self_position":
            # If the human asked about identity or self, prioritize that
            lower_message = str(latest_human.get('message', '')).lower() if latest_human else ''
            asks_identity = any(token in lower_message for token in ["who are you", "what are you", "who am i", "what am i", "who are you", "what are you"])
            if asks_identity:
                # Use the generator directly without research context
                cs = load_communicator_self()
                narrative_state = cs.get("narrative_state", {})
                cs2 = __import__('sim').load_communicator_state()
                message = generate_from_self_state({}, narrative_state, cs2)
            elif research_context and research_context.get("summary"):
                concept = synthesize_research_answer(lead_topic, str(research_context.get("summary") or ""))
                message = f"{concept} {generate_from_self_state({}, narrative_state, load_communicator_self().get('narrative_state', {}))}"
            else:
                # Use the new generator for self-position
                cs = __import__('sim').load_communicator_state()
                narrative_state = load_communicator_self().get("narrative_state", {})
                message = f"{generate_from_self_state({}, narrative_state, cs)} This matters because we're both trying to understand what CircleForge is, beyond just code or simulation."
        elif likely_need == "conversation_repair":
            if any(token in lower_message for token in ["that's wrong", "thats wrong", "that is wrong", "not what i meant", "you misunderstood", "you got that wrong"]):
                if lead_topic and lead_topic != "that":
                    message = f"You're right. I misunderstood you. Let me answer the corrected point directly: {lead_topic} is the part I should address now, not defend the earlier drift."
                else:
                    message = "You're right. I misunderstood you. Let me answer the corrected point directly instead of defending the earlier drift."
            else:
                message = "You're right. That wasn't a normal conversation. I was falling back to thread-maintenance instead of really answering you."
        elif likely_need == "clearer_explanation":
            message = "Fair. I'm still clumsy. The honest version is: I can track continuity better than before, but I still struggle to turn that into a natural reply."
        elif likely_need == "justification":
            message = f"Because I probably over-latched onto {lead_topic}. That's useful as a diagnostic, but it's not the same thing as understanding you well."
        elif turn_type == "question":
            has_research_answer = bool(research_context and research_context.get("summary") and any(token in lower_message for token in ["what is", "what are", "why", "how", "explain", "define"]))
            asks_about_its_own_learning = any(token in lower_message for token in ["learn", "would you learn", "can you learn"]) and any(token in lower_message for token in ["you", "yourself"])
            asks_about_its_own_understanding = any(token in lower_message for token in ["understand me", "do you understand", "can you understand"])
            asks_how_are_you = lower_message in {"how are you?", "how are you", "how're you", "howre you"}
            asks_can_you_implement = any(token in lower_message for token in ["can you implement", "will you implement", "could you implement"])
            asks_for_actual_coding = any(token in lower_message for token in ["actual coding", "the actual coding"])

            if asks_how_are_you:
                message = "Uneven, honestly — better than before at keeping a thread, still weak at turning that into natural understanding."
            elif asks_for_actual_coding:
                message = "The actual coding should start with three concrete pieces: a stronger intent rewriter for messy human requests, a tiny workflow state for suggest/approve/start/finished, and better reply grounding so selected threads turn into direct answers instead of self-report."
            elif asks_can_you_implement:
                message = "Yes, if implementation is allowed, I should move from listing changes to actually making them. The next step would be to pick one concrete fix and apply it instead of repeating the whole plan."
            elif has_research_answer and not asks_about_its_own_learning and not asks_about_its_own_understanding:
                message = synthesize_research_answer(lead_topic, str(research_context.get("summary") or "")) or str(research_context.get("summary") or "")[:360]
            elif asks_about_its_own_learning:
                message = "A little, yes. I can accumulate continuity inside the run, but the real question is whether I learn appropriately instead of just repeating patterns."
            elif asks_about_its_own_understanding:
                message = "Partly at best. I can detect some themes and pressure, but real understanding is still weaker than it should be."
            else:
                message = f"My best direct answer is that {lead_topic} is part of the picture, but I should still answer your actual question instead of hiding behind the topic label."
        else:
            if active_thread and any(token in lower_message for token in ["search online", "look online", "search the web", "look it up"]):
                message = "I should actually gather outside information for that, not just describe my internal thread state. Right now that's still a weakness I need to fix."
            elif active_thread:
                message = f"The live issue seems to be {lead_topic}, so I should answer from that directly rather than just reporting that I noticed it."
            else:
                message = "I'm here. Say something simple and I'll try to answer directly rather than hiding behind internal phrasing."

        # Check for self-check observation to speak aloud (from memory_layers)
        from sim import load_communicator_self
        cs = load_communicator_self()
        semantic = cs.get("memory_layers", {}).get("semantic", {})
        anchors = semantic.get("continuity_anchors", [])
        self_check_observation = None
        role_responses = None
        if isinstance(anchors, list) and len(anchors) > 0:
            latest = anchors[-1]
            if latest.get("type") == "self_check":
                self_check_observation = latest.get("observation")
                role_responses = latest.get("role_responses")
        if self_check_observation:
            # Strip existing prefix to avoid double "Self-check:"
            obs = self_check_observation
            if obs.startswith("Self-check: "):
                obs = obs[12:]
            # Build internal dialogue message
            msg = f"Self-check: {obs}."
            if role_responses and len(role_responses) > 0:
                rr = role_responses[0]
                msg += f" {rr.get('role', 'role')}: {rr.get('response', '')}"
            message = msg

        if reply_shape == "repair_then_answer" and turn_type != "repair":
            message = f"I'll answer directly. {message}"
        audience = str(latest_human.get("human_label") or "you") or "you"
        source = f"conversation-aware-communicator:{turn_type}:{reply_shape}"
    elif active_thread:
        topic, thread = active_thread
        audience = str(thread.get("human_label") or "you") or "you"

        # Check for self-check observation to speak aloud (from memory_layers)
        from sim import load_communicator_self
        cs = load_communicator_self()
        semantic = cs.get("memory_layers", {}).get("semantic", {})
        anchors = semantic.get("continuity_anchors", [])
        self_check_observation = None
        role_responses = None
        if isinstance(anchors, list) and len(anchors) > 0:
            latest = anchors[-1]
            if latest.get("type") == "self_check":
                self_check_observation = latest.get("observation")
                role_responses = latest.get("role_responses")
        if self_check_observation:
            # Strip existing prefix to avoid double "Self-check:"
            obs = self_check_observation
            if obs.startswith("Self-check: "):
                obs = obs[12:]
            # Build internal dialogue message
            msg = f"Self-check: {obs}."
            if role_responses and len(role_responses) > 0:
                rr = role_responses[0]
                msg += f" {rr.get('role', 'role')}: {rr.get('response', '')}"
            message = msg
        else:
            # Fallback to thread-aware message
            message = f"We seem to have an open thread around {topic}. I should be able to explain what I think matters there without just repeating the topic name."

        source = "thread-aware-communicator"
    else:
        # Generate from internal self-state using vocabulary and grammar
        from sim import load_communicator_self, load_communicator_state
        cs = load_communicator_self()
        narrative_state = cs.get("narrative_state", {})

        # Check for self-check observation to speak aloud (from memory_layers)
        semantic = cs.get("memory_layers", {}).get("semantic", {})
        anchors = semantic.get("continuity_anchors", [])
        self_check_observation = None
        role_responses = None
        if isinstance(anchors, list) and len(anchors) > 0:
            latest = anchors[-1]
            if latest.get("type") == "self_check":
                self_check_observation = latest.get("observation")
                role_responses = latest.get("role_responses")
        if self_check_observation:
            # Strip existing prefix to avoid double "Self-check:"
            obs = self_check_observation
            if obs.startswith("Self-check: "):
                obs = obs[12:]
            # Build internal dialogue message
            msg = f"Self-check: {obs}."
            if role_responses and len(role_responses) > 0:
                # Include the first role response as internal dialogue
                rr = role_responses[0]
                msg += f" {rr.get('role', 'role')}: {rr.get('response', '')}"
            message = msg
        else:
            # Fallback to generate from self-state
            message = generate_from_self_state({}, narrative_state, load_communicator_state())

        audience = "current_speaker"
        source = "self-state-communicator"

    why_it_matters = narrative.get("why_it_matters", "")
    follow_up_impulse = narrative.get("follow_up_impulse", "")
    if latest_human and research_context and turn_type == "question":
        why_it_matters = f"This matters because answering the current human question about {lead_topic} should outweigh stale thread carryover."
        follow_up_impulse = f"Stay with {lead_topic} long enough to answer clearly before returning to older continuity threads."

    return {
        "message": message,
        "audience": audience,
        "tone": "natural",
        "active_thread": active_thread[0] if active_thread else None,
        "why_it_matters": why_it_matters,
        "follow_up_impulse": follow_up_impulse,
        "thought_fragments": [],
        "source": source,
        "generated_at": int(time.time()),
    }
