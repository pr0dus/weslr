from __future__ import annotations


LOW_INFORMATION_REFERENTIAL_PHRASES = [
    "no, i mean",
    "no i mean",
    "i mean the thing",
    "the thing that matters",
    "what i meant",
    "that one",
    "the important thing",
    "more overall",
]

SMALL_TALK_ONLY_MESSAGES = {
    "hey", "hi", "hello", "yo", "sup", "hallo", "moin", "hey there", "hi there"
}

IMPERATIVE_REQUEST_PHRASES = [
    "suggest code",
    "implement",
    "search online",
    "search the web",
    "look online",
    "look it up",
    "change your coding",
    "changed in your coding",
]


def infer_human_topics(message: str) -> list[str]:
    original = str(message or "").strip()
    lowered = original.lower()
    if lowered in SMALL_TALK_ONLY_MESSAGES:
        return []
    topics = []
    keyword_map = {
        "circleforge": "CircleForge",
        "backup confidence": "backup confidence",
        "backup": "backup confidence",
        "memory": "memory continuity",
        "communicator": "communicator self",
        "dashboard": "dashboard",
        "agent": "internal minds",
        "tester": "testers and feedback",
        "feedback": "testers and feedback",
        "github": "GitHub positioning",
        "emergence": "emergence",
        "entity": "entity status",
        "conversation": "conversation quality",
        "understand": "understanding",
        "learn": "learning",
        "prompt": "prompt dependence",
    }
    for token, topic in keyword_map.items():
        if token in lowered and topic not in topics:
            topics.append(topic)

    if topics:
        return topics[:4]

    if any(phrase in lowered for phrase in LOW_INFORMATION_REFERENTIAL_PHRASES):
        return []
    if any(phrase in lowered for phrase in IMPERATIVE_REQUEST_PHRASES):
        return []

    cleaned = lowered
    for phrase in [
        "why do you", "why are you", "how do you", "what do you", "can you", "could you", "would you", "do you", "are you", "is this", "i don't want to ask,", "i dont want to ask,",
        "please", "actually", "really", "just", "still", "again"
    ]:
        cleaned = cleaned.replace(phrase, " ")
    words = [word.strip(" ,.!?:;()[]{}\"'") for word in cleaned.split()]
    stopwords = {
        "i", "you", "me", "my", "we", "us", "this", "that", "it", "to", "the", "a", "an", "and", "or", "but", "if", "then", "of", "on", "in", "at", "for", "with", "about", "do", "does", "did", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "want", "need", "not"
    }
    filtered = [word for word in words if word and word not in stopwords]
    if filtered:
        topics.append(" ".join(filtered[:3]).strip())
    elif original:
        topics.append(original[:48].strip())
    return topics[:4]


def classify_human_turn(message: str) -> str:
    lowered = str(message or "").strip().lower()
    if not lowered:
        return "empty"
    if lowered in SMALL_TALK_ONLY_MESSAGES:
        return "greeting"
    if any(token in lowered for token in ["this is not", "not normal conversation", "you still need to learn", "evolve", "stop telling me", "answer directly"]):
        return "repair"
    if any(token in lowered for token in ["who are you", "what are you", "emergence", "new entity", "entity"]):
        return "identity_probe"
    if any(token in lowered for token in ["what do you remember", "do you remember", "remember me"]):
        return "memory_probe"
    if any(token in lowered for token in ["why", "how come", "what for"]):
        return "objection"
    if any(token in lowered for token in ["i don't understand", "dont understand", "do not understand"]):
        return "confusion"
    if "?" in lowered or lowered.startswith(("do ", "are ", "can ", "will ", "would ", "is ", "should ", "could ", "what ", "why ", "how ", "who ")):
        return "question"
    return "statement"


def interpret_human_turn(message: str) -> dict:
    text = str(message or "").strip()
    topics = infer_human_topics(text)
    turn_type = classify_human_turn(text)
    lowered = text.lower()

    intent = {
        "greeting": "open conversation",
        "repair": "repair conversation",
        "identity_probe": "test identity / emergence",
        "memory_probe": "test memory scope",
        "objection": "challenge current behavior",
        "confusion": "request clarification",
        "question": "ask for explanation",
        "statement": "share/update stance",
        "empty": "no content",
    }.get(turn_type, "unknown")

    stance = "neutral"
    if turn_type in {"repair", "objection"}:
        stance = "resistant"
    elif turn_type == "confusion":
        stance = "uncertain"
    elif turn_type in {"question", "memory_probe", "identity_probe"}:
        stance = "inquiring"

    reply_shape = "answer_directly"
    if turn_type == "repair":
        reply_shape = "repair_then_answer"
    elif turn_type == "confusion":
        reply_shape = "clarify"
    elif turn_type in {"memory_probe", "identity_probe"}:
        reply_shape = "answer_with_scope"

    relational_signal = "neutral"
    if any(token in lowered for token in ["no", "stop", "wrong", "not normal", "don't", "do not"]):
        relational_signal = "friction"
    elif any(token in lowered for token in ["understand", "learn", "help", "continue"]):
        relational_signal = "engagement"

    likely_need = "direct_answer"
    if turn_type == "repair":
        likely_need = "conversation_repair"
    elif turn_type == "confusion":
        likely_need = "clearer_explanation"
    elif turn_type == "memory_probe":
        likely_need = "memory_scope_check"
    elif turn_type == "identity_probe":
        likely_need = "concept_plus_self_position"
    elif turn_type == "objection":
        likely_need = "justification"
    elif turn_type == "question":
        if any(token in lowered for token in ["what is", "what are", "define", "explain", "how does", "why does"]):
            likely_need = "concept_explanation"
        elif any(token in lowered for token in ["do you", "can you", "would you", "are you"]):
            likely_need = "self_report"
    elif turn_type == "statement" and relational_signal == "friction":
        likely_need = "acknowledgment_and_adjustment"

    return {
        "message": text,
        "turn_type": turn_type,
        "topics": topics,
        "primary_topic": topics[0] if topics else "",
        "intent": intent,
        "stance": stance,
        "relational_signal": relational_signal,
        "likely_need": likely_need,
        "needs_repair": turn_type == "repair",
        "asks_for_clarification": turn_type == "confusion",
        "probes_identity": turn_type == "identity_probe",
        "probes_memory": turn_type == "memory_probe",
        "reply_shape": reply_shape,
    }
