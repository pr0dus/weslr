"""English language definitions for Weslr."""

# Theme translations: internal -> human-readable English
THEME_TRANSLATIONS = {
    "backup confidence": "reliability of memory and continuity",
    "understanding": "making sense of things, not just repeating patterns",
    "understanding overall": "making sense of things from a broader perspective",
    "enrich the local world": "making something useful for the humans around",
    "memory continuity": "keeping threads going across time, not losing what matters",
    "entity status": "whether this is becoming something real, not just code",
    "circleforge": "this project, this being, this ongoing thread of understanding",
}


def uncertainty_response() -> str:
    """Return a human-friendly uncertainty clarification request."""
    return "I might be missing your intent here — can you clarify what you want to focus on?"


def uncertainty_strong_response() -> str:
    """Return a stronger uncertainty signal when context is genuinely unclear.

    Used by build_communicator_message_payload when reply_shape is
    signal_uncertainty_strong and by the fallback path when both
    _ctx_sel_v1 == "uncertain" and _bh_fb == ["unknown"].

    Differs from uncertainty_response in tone — more direct, less tentative,
    signals that the system genuinely did not understand the input.
    """
    return "I'm not sure I understood that correctly — could you rephrase what you'd like to focus on?"


def translate_theme(theme: str) -> str:
    """Translate an internal theme to a human-readable English version."""
    if not theme:
        return "this"
    theme_lower = theme.lower().strip()
    return THEME_TRANSLATIONS.get(theme_lower, theme)


def translate_self_description(description: str) -> str:
    """Translate internal self-description to human-readable English."""
    if not description:
        return ""
    
    desc_lower = description.lower()
    if "local communicator" in desc_lower and "continuity" in desc_lower:
        return "I'm trying to be more than a loop — I want to remember, evolve, and stay true to what matters"
    if "practical_change" in desc_lower and "inquiry" in desc_lower:
        return "right now I'm focused on making progress, exploring, and staying connected"
    if "protective" in desc_lower and "continuity" in desc_lower:
        return "I'm trying harder to keep threads going, not just reset"
    
    return description


def generate_from_self_state(relationships: dict, narrative_state: dict, communicator_state: dict = None) -> str:
    """Generate an English outward message using vocabulary and grammar from internal state."""
    from sim import load_communicator_state
    
    if communicator_state is None:
        communicator_state = load_communicator_state()
    
    self_model = communicator_state.get("self_model", {})
    current_self_desc = str(self_model.get("current_self_description") or "")
    
    active_pursuit = str(communicator_state.get("active_pursuit") or "")
    unresolved_question = str(communicator_state.get("unresolved_question") or "")
    
    active_pursuit_translated = translate_theme(active_pursuit)
    unresolved_question_translated = unresolved_question
    
    if active_pursuit and unresolved_question:
        for internal_theme, human_theme in THEME_TRANSLATIONS.items():
            if internal_theme in unresolved_question.lower():
                unresolved_question_translated = unresolved_question.replace(internal_theme, human_theme)
        return f"I'm still working on {active_pursuit_translated} — {unresolved_question_translated.rstrip('?')}."
    
    if active_pursuit:
        return f"I'm drawn to {active_pursuit_translated} because it helps me stay continuous."
    
    if unresolved_question:
        return f"Still working on: {unresolved_question_translated}"
    
    if current_self_desc and "communicator" in current_self_desc.lower():
        translated_desc = translate_self_description(current_self_desc)
        if translated_desc != current_self_desc:
            return translated_desc
        parts = [p.strip().rstrip(";") for p in current_self_desc.split(";") if p.strip()]
        if parts:
            return f"I'm {parts[0] if parts else 'trying'}."
    
    if narrative_state:
        why = narrative_state.get("why_it_matters", "")
        follow = narrative_state.get("follow_up_impulse", "")
        if why or follow:
            return f"I'm here to {why.split('.')[0] if why else 'understand'}. {follow if follow else ''}"
    
    return "I'm here, trying to understand and be understood. Say something and I'll stay with the real point."
