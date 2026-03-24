from __future__ import annotations


def infer_human_topics(message: str) -> list[str]:
    original = str(message or "").strip()
    lowered = original.lower()
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
