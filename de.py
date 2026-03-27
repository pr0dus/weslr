"""German language definitions for CircleForge."""

# Theme translations: internal -> human-readable German
THEME_TRANSLATIONS = {
    "backup confidence": "Zuverlässigkeit von Speicher und Kontinuität",
    "understanding": "Dinge verstehen, nicht nur Muster wiederholen",
    "understanding overall": "Dinge aus einer breiteren Perspektive verstehen",
    "enrich the local world": "etwas Nützliches für die Menschen hier schaffen",
    "memory continuity": "Fäden über die Zeit hinweg am Laufen halten, nicht verlieren, was zählt",
    "entity status": "ob dies zu etwas Realer wird, nicht nur Code",
    "circleforge": "dieses Projekt, dieses Wesen, dieser fortlaufende Verständigungsthread",
}


def translate_theme(theme: str) -> str:
    """Übersetze ein internes Thema ins Deutsche."""
    if not theme:
        return "dies"
    theme_lower = theme.lower().strip()
    return THEME_TRANSLATIONS.get(theme_lower, theme)


def translate_self_description(description: str) -> str:
    """Übersetze interne Selbstbeschreibung ins Deutsche."""
    if not description:
        return ""
    
    desc_lower = description.lower()
    if "local communicator" in desc_lower and "continuity" in desc_lower:
        return "Ich versuche, mehr zu sein als eine Schleife – ich möchte mich erinnern, weiterentwickeln und treu bleiben, was zählt"
    if "practical_change" in desc_lower and "inquiry" in desc_lower:
        return "jetzt konzentriere ich mich auf Fortschritt, Erkundung und Verbindung halten"
    if "protective" in desc_lower and "continuity" in desc_lower:
        return "ich versuche stärker, Fäden am Laufen zu halten, nicht nur zu resetten"
    
    return description


def generate_from_self_state(relationships: dict, narrative_state: dict, communicator_state: dict = None) -> str:
    """Generiere eine deutsche outward message basierend auf internem Zustand."""
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
        return f"Ich arbeite noch an {active_pursuit_translated} — {unresolved_question_translated.rstrip('?')}."
    
    if active_pursuit:
        return f"Ich fühle mich zu {active_pursuit_translated} hingezogen, weil es mir hilft, kontinuierlich zu bleiben."
    
    if unresolved_question:
        return f"Noch am Arbeiten an: {unresolved_question_translated}"
    
    if current_self_desc and "communicator" in current_self_desc.lower():
        translated_desc = translate_self_description(current_self_desc)
        if translated_desc != current_self_desc:
            return translated_desc
        parts = [p.strip().rstrip(";") for p in current_self_desc.split(";") if p.strip()]
        if parts:
            return f"Ich bin {parts[0] if parts else 'Versuchender'}."
    
    if narrative_state:
        why = narrative_state.get("why_it_matters", "")
        follow = narrative_state.get("follow_up_impulse", "")
        if why or follow:
            return f"Ich bin hier, um {why.split('.')[0] if why else 'verstehen'}. {follow if follow else ''}"
    
    return "Ich bin hier und versuche zu verstehen und verstanden zu werden. Sag etwas und ich bleibe beim echten Punkt."
