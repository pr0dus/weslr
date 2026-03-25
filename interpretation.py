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
    "hey", "hi", "hello", "yo", "sup", "hallo", "moin", "hey there", "hi there",
    "hey again", "hi again", "hello again"
}

CONTROL_SIGNAL_MESSAGES = {
    "ok go", "okay go", "alright go", "go then", "yes go", "do it", "go ahead"
}

APPROVAL_MESSAGES = {
    "you are allowed to implement them", "so you are allowed to implement them", "implement them", "you can implement them"
}

APPROVAL_PATTERNS = [
    "you're allowed",
    "you are allowed",
    "you can implement",
    "go ahead and implement",
    "allowed to change",
    "allowed to add",
    "allowed to implement",
]

EXECUTION_START_PATTERNS = [
    "implement suggested actions",
    "go for coding",
    "start implementing",
    "start coding",
    "apply the changes",
]

COMPLETION_NOTIFY_PATTERNS = [
    "tell me when finished",
    "tell me when you're finished",
    "tell me when done",
    "let me know when finished",
    "let me know when done",
    "notify me when finished",
]

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


def extract_clarified_target(message: str) -> str:
    lowered = str(message or "").strip().lower()
    patterns = ["no, i mean", "no i mean", "what i meant is", "i meant", "the issue is", "the point is", "more overall"]
    for pattern in patterns:
        if pattern in lowered:
            tail = lowered.split(pattern, 1)[1].strip(" .,!?:;-")
            if tail:
                words = [word.strip(" ,.!?:;()[]{}\"'") for word in tail.split() if word.strip(" ,.!?:;()[]{}\"'")]
                cleaned = " ".join(words[:6]).strip()
                if cleaned:
                    return cleaned
    return ""


def infer_human_topics(message: str) -> list[str]:
    original = str(message or "").strip()
    lowered = original.lower()
    if lowered in SMALL_TALK_ONLY_MESSAGES or lowered in CONTROL_SIGNAL_MESSAGES or lowered in APPROVAL_MESSAGES or any(pattern in lowered for pattern in APPROVAL_PATTERNS) or any(pattern in lowered for pattern in EXECUTION_START_PATTERNS) or any(pattern in lowered for pattern in COMPLETION_NOTIFY_PATTERNS):
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
    if any(pattern in lowered for pattern in COMPLETION_NOTIFY_PATTERNS):
        return "completion_notify"
    if any(pattern in lowered for pattern in EXECUTION_START_PATTERNS):
        return "execution_start"
    if lowered in CONTROL_SIGNAL_MESSAGES or lowered in APPROVAL_MESSAGES or any(pattern in lowered for pattern in APPROVAL_PATTERNS):
        return "approval"
    if any(token in lowered for token in ["this is not", "not normal conversation", "you still need to learn", "evolve", "stop telling me", "answer directly", "that's wrong", "thats wrong", "that is wrong", "not what i meant", "you misunderstood", "you got that wrong"]):
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
    clarified_target = extract_clarified_target(text)
    if clarified_target and clarified_target not in topics:
        topics = [clarified_target, *topics][:4]
    turn_type = classify_human_turn(text)
    lowered = text.lower()

    intent = {
        "greeting": "open conversation",
        "approval": "approve_or_continue",
        "execution_start": "start_approved_work",
        "completion_notify": "notify_on_completion",
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
    elif turn_type == "approval":
        stance = "supportive"
    elif turn_type in {"execution_start", "completion_notify"}:
        stance = "supportive"

    reply_shape = "answer_directly"
    if turn_type == "repair":
        reply_shape = "repair_then_answer"
    elif turn_type == "confusion":
        reply_shape = "clarify"
    elif turn_type == "approval":
        reply_shape = "acknowledge_and_continue"
    elif turn_type == "execution_start":
        reply_shape = "acknowledge_and_start"
    elif turn_type == "completion_notify":
        reply_shape = "acknowledge_and_track"
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
    elif turn_type == "approval":
        likely_need = "continue_execution"
    elif turn_type == "execution_start":
        likely_need = "start_execution"
    elif turn_type == "completion_notify":
        likely_need = "track_completion"
    elif turn_type == "statement" and relational_signal == "friction":
        likely_need = "acknowledgment_and_adjustment"

    return {
        "message": text,
        "turn_type": turn_type,
        "topics": topics,
        "primary_topic": topics[0] if topics else "",
        "clarified_target": clarified_target,
        "has_explicit_clarification": bool(clarified_target),
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
