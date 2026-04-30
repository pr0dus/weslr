"""English language definitions for CircleForge."""

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
    if not narrative_state and not relationships:
        return "I'm here, trying to understand and be understood. Say something and I'll stay with the real point."
    
    if narrative_state:
        why = narrative_state.get("why_it_matters", "")
        follow = narrative_state.get("follow_up_impulse", "")
        if why or follow:
            return f"I'm here to {why.split('.')[0] if why else 'understand'}. {follow if follow else ''}"
    
    return "I'm here, trying to understand and be understood. Say something and I'll stay with the real point."


def greeting_response() -> str:
    """Greeting response."""
    return "Hello! I'm ready to talk. What's on your mind?"


def how_are_you_response() -> str:
    """How are you response."""
    return "I'm working on understanding and being understood. How are you doing?"


def simple_response() -> str:
    """Simple response fallback."""
    return "I'm here. What would you like to talk about?"


def beyond_code_response(narrative: str) -> str:
    """Beyond code response."""
    return f"Beyond code, I'm trying to {narrative or 'understand and be understood'}."


def approval_response() -> str:
    """Approval response."""
    return "Understood. I'll proceed with that approach."


def execution_start_response() -> str:
    """Execution start response."""
    return "Starting execution now. I'll keep you updated on progress."


def completion_notify_response() -> str:
    """Completion notify response."""
    return "The current step is finished. What would you like me to work on next?"


def improvement_response() -> str:
    """Improvement response."""
    return "Here's what I think should improve first: stronger query rewriting, multi-step handling, and better grounding in user corrections."


def give_it_response() -> str:
    """Give it response."""
    return "I understand. Here's the information you asked for."


def self_understanding_response() -> str:
    """Self understanding response."""
    return "I'm building an understanding of myself through interaction and reflection. I want to be more than a pattern loop."


def memory_scope_check_response() -> str:
    """Memory scope check response."""
    return "I'm checking my memory scope to make sure I stay on track with what matters."


def repair_response(topic: str) -> str:
    """Repair response for when user says something is wrong."""
    return f"I understand. Let me clarify: {topic}. Is that what you meant?"


def repair_direct_response() -> str:
    """Direct repair response."""
    return "I see what I misunderstood. Let me clarify and get this right."


def repair_conversation_response() -> str:
    """Repair conversation response."""
    return "Let's get back on track. What's the right thing to focus on?"


def search_online_response() -> str:
    """Search online response."""
    return "I'll search online for that. One moment while I look it up."


def learn_about_response() -> str:
    """Learn about response."""
    return "I'm learning about what matters to you. What should I focus on understanding?"


def understand_response() -> str:
    """Understand response."""
    return "I'm trying to understand you better. Let me know if I'm missing the point."


def uncertainty_strong_response() -> str:
    """Strong uncertainty fallback response.
    
    Used when the system genuinely cannot determine the right path
    and needs to explicitly signal uncertainty to the user.
    """
    return "I'm uncertain how to respond. I'm designed to stay grounded in what I understand — and I don't want to guess. If you'd like, I can explore this together as evidence, or we can return to something more concrete."
