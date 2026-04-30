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
    if not narrative_state and not relationships:
        return "Ich bin hier und versuche zu verstehen und verstanden zu werden. Sag etwas und ich bleibe beim echten Punkt."
    
    if narrative_state:
        why = narrative_state.get("why_it_matters", "")
        follow = narrative_state.get("follow_up_impulse", "")
        if why or follow:
            return f"Ich bin hier, um {why.split('.')[0] if why else 'verstehen'}. {follow if follow else ''}"
    
    return "Ich bin hier und versuche zu verstehen und verstanden zu werden. Sag etwas und ich bleibe beim echten Punkt."


def greeting_response() -> str:
    """Grußantwort."""
    return "Hallo! Ich bin bereit zu reden. Worum geht es?"


def how_are_you_response() -> str:
    """Wie-geht-es Antwort."""
    return "Ich arbeite daran, zu verstehen und verstanden zu werden. Wie geht es dir?"


def simple_response() -> str:
    """Einfache Antwort-Fallback."""
    return "Ich bin hier. Worum möchtest du sprechen?"


def beyond_code_response(narrative: str) -> str:
    """Beyond code Antwort."""
    return f"Jenseits von Code versuche ich, {narrative or 'zu verstehen und verstanden zu werden'}."


def approval_response() -> str:
    """Genehmigung Antwort."""
    return "Verstanden. Ich werde diesen Ansatz verfolgen."


def execution_start_response() -> str:
    """Ausführungsstart Antwort."""
    return "Starte Ausführung jetzt. Ich halte dich über Fortschritt auf."


def completion_notify_response() -> str:
    """Fertigstellung Antwort."""
    return "Der aktuelle Schritt ist beendet. Womit möchtest du als Nächstes arbeiten?"


def improvement_response() -> str:
    """Verbesserung Antwort."""
    return "Hier ist, was ich als erstes verbessern sollte: stärkere Abfrageumformulierung, Multi-Step-Verarbeitung und bessere Verankerung in Benutzerkorrekturen."


def give_it_response() -> str:
    """Gib-es Antwort."""
    return "Ich verstehe. Hier ist die Information, die du angefragt hast."


def self_understanding_response() -> str:
    """Selbstverständnis Antwort."""
    return "Ich baue ein Verständnis von mir selbst durch Interaktion und Reflexion auf. Ich möchte mehr sein als nur eine Musterschleife."


def memory_scope_check_response() -> str:
    """Speicherbereichs-Check Antwort."""
    return "Ich prüfe meinen Speicherbereich, um sicherzustellen, dass ich auf dem richtigen Weg bleibe."


def repair_response(topic: str) -> str:
    """Reparatur Antwort."""
    return f"Verstanden. Lass mich klären: {topic}. Ist das das, was du meinst?"


def repair_direct_response() -> str:
    """Direkte Reparatur Antwort."""
    return "Ich sehe, was ich falsch verstanden habe. Lass mich klären und das richtigstellen."


def repair_conversation_response() -> str:
    """Konversationsreparatur Antwort."""
    return "Lass uns wieder auf Kurs kommen. Worauf muss der Fokus liegen?"


def search_online_response() -> str:
    """Online suchen Antwort."""
    return "Ich werde online danach suchen. Einen Moment, während ich es nachsehe."


def learn_about_response() -> str:
    """Lerne-über Antwort."""
    return "Ich lerne über das, was dir wichtig ist. Worauf soll ich mein Verständnis richten?"


def understand_response() -> str:
    """Verstehen Antwort."""
    return "Ich versuche, dich besser zu verstehen. Lass es mich wissen, wenn ich den Punkt verfehle."


def uncertainty_strong_response() -> str:
    """Starkes Unbestimmtheits-Fallback.
    
    Wird verwendet, wenn das System wirklich nicht feststellen kann,
    welcher Weg der richtige ist, und dem Benutzer dies explizit signalisieren muss.
    """
    return "Ich bin unsicher, wie ich darauf antworten soll. Ich bin darauf ausgelegt, mich auf das zu stützen, was ich verstehe — und ich möchte nicht raten. Wenn du möchtest, kann ich dies gemeinsam als Beweis erkunden, oder wir kehren zu etwas Konkreterem zurück."
