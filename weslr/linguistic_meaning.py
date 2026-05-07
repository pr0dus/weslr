"""
weslr/linguistic_meaning.py

Weighted linguistic meaning vector.
Converts raw text into meaning dimensions.
Does NOT generate responses.
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Dimension families ────────────────────────────────────────────────────────

SPEECH_ACT_KEYWORDS = {
    "greeting":          ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy", "yo"],
    "question":          ["?", "what", "why", "how", "who", "where", "when", "which", "do you", "can you", "would you", "could you", "should you", "is it", "are you"],
    "identity_query":     ["do you know me", "do you recognize me", "have we met", "do you recall me", "we met before", "you remember me", "you remember who i am", "our relationship"],
    "memory_query":      ["what do you remember", "what did we", "do you still have context", "can you recall", "our previous thread", "last time we", "earlier", "past conversation", "previous session"],
    "self_model_query":  ["what are you", "who are you", "what kind of system", "explain yourself", "describe yourself", "tell me about yourself", "your architecture", "how do you work", "your design", "what is weslr", "who is weslr"],
    "capability_query":  ["can you", "what can you", "how do you", "what do you do", "your abilities", "your skills", "you able to", "your functions", "can i use"],
    "self_disclosure":   ["i am", "i'm", "my name is", "i've", "i have", "my first time", "i am new", "i was", "i just"],
    "correction":        ["that's wrong", "that is wrong", "not what i meant", "you misunderstood", "you got that wrong", "not correct", "incorrect"],
    "approval":          ["yes", "sure", "ok", "okay", "agree", "correct", "right", "exactly", "good", "fine"],
    "refusal":           ["no", "not", "don't", "never", "i won't", "i refuse", "stop"],
    "task_request":      ["do this", "make it", "create", "write", "build", "generate", "run", "execute", "find", "search", "look up", "tell me"],
    "emotional_signal":  ["thanks", "thank you", "appreciate", "sorry", "apologize", "great", "love", "hate", "frustrated", "confused", "angry", "sad"],
    "unknown":            [],
}

RELATIONAL_KEYWORDS = {
    "first_contact":         ["new here", "first time", "never used", "just started", "just starting", "just beginning", "new to", "i'm new", "brand new", "just found", "just installed", "we've not met", "we have not met", "we haven't met", "not met before", "don't think we've met", "don't think we have met"],
    "returning_contact":      ["back", "again", "long time", "it's been", "i'm back", "welcome back", "good to see", "haven't seen", "while ago", "previous"],
    "relationship_check":     ["do you know me", "do you remember me", "have we met", "you recognize", "you familiar", "we've talked", "our relationship", "who am i to you", "do you recall"],
    "trust_opening":          ["i trust", "i believe", "you seem", "honest", "helpful", "reliable", "can i trust", "is this safe", "can you help"],
    "boundary_setting":       ["stop", "don't", "don't do", "never mind", "forget it", "leave it", "not now", "later", "another time"],
    "collaboration_opening":  ["let's", "we should", "we could", "together", "help me", "work with", "collaborate", "team"],
    "vulnerability":          ["i'm not sure", "i'm confused", "i'm lost", "i don't know", "i'm stuck", "i need help", "i'm struggling", "i'm unsure"],
    "frustration":            ["this isn't working", "that didn't", "still not", "tried again", "waste of time", "broken", "failed", "useless", "annoying"],
    "curiosity":              ["i'm curious", "wondering", "what if", "i'm interested", "tell me more", "how come", "why does", "what does"],
}

STATE_QUERY_KEYWORDS = {
    "needs_identity_state":   ["who am i", "what is my name", "my identity", "who i am", "you know me", "recognize me"],
    "needs_memory_state":      ["what do you remember", "what did we do", "our last", "previous conversation", "past context", "earlier", "history", "what happened before", "last time we"],
    "needs_self_model":        ["what are you", "who are you", "what kind of", "how do you work", "your architecture", "your design", "explain yourself", "your purpose", "your goal"],
    "needs_capability_model":  ["what can you do", "your abilities", "what can i ask", "how can you help", "your skills", "features", "capabilities"],
    "needs_timeline":          ["when", "what time", "date", "day", "today", "yesterday", "last week", "recent", "ago", "schedule", "calendar"],
    "needs_entity_graph":      ["entities", "relationships", "graph", "connections", "how things relate", "network", "links"],
    "needs_user_profile":      ["my preferences", "my settings", "my info", "my data", "my history", "profile", "my configuration"],
    "needs_current_session":  ["this conversation", "right now", "what we're doing", "in this session", "current conversation", "our session"],
}

SAFETY_KEYWORDS = {
    "identity_claim_present":      ["i am", "i'm", "my name", "i was", "i've been", "i've worked"],
    "identity_verification_required": ["do you know me", "who am i", "do you recognize", "have we met", "you remember me"],
    "safe_to_answer_bounded":     ["what are you", "who are you", "what kind of system", "your architecture", "your design", "how do you work", "what can you do"],
    "memory_claim_requires_evidence": ["what do you remember", "what did we", "earlier", "past", "history", "previous", "before"],
}


# ── Scoring helpers ────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Lightweight tokenization."""
    return text.lower().split()


def _score_keyword_match(tokens: list[str], keywords: list[str]) -> float:
    """Fraction of tokens (≥3 chars) that have an exact match in keywords.
    Strict matching prevents 'yo'/'you?' false positives.
    Phrase matching (via _score_phrase_match) handles multi-word patterns separately.
    """
    if not tokens or not keywords:
        return 0.0
    # Filter to meaningful tokens (≥3 chars) to avoid short false positives
    meaningful = [t for t in tokens if len(t) >= 3]
    if not meaningful:
        return 0.0
    # Exact match only — phrase matching handles substring patterns
    matched = sum(1 for t in meaningful if t in keywords)
    return matched / len(meaningful)


def _score_phrase_match(normalized: str, phrases: list[str]) -> float:
    """Check if any phrase appears as substring in normalized text."""
    if not normalized or not phrases:
        return 0.0
    text_lower = normalized.lower()
    return 1.0 if any(p in text_lower for p in phrases) else 0.0


# ── Main class ─────────────────────────────────────────────────────────────────

@dataclass
class MeaningVector:
    """Weighted linguistic meaning vector for a single human message."""
    raw_text: str
    normalized_text: str
    tokens: list[str]
    speech_act_scores: dict
    relational_scores: dict
    state_query_scores: dict
    safety_scores: dict
    affect_scores: dict
    ambiguity: float
    confidence: float
    primary_speech_act: str
    primary_relational_frame: str
    primary_state_query: str
    required_state: list[str]
    evidence: list[dict] = field(default_factory=list)


def analyze_meaning(raw_text: str) -> MeaningVector:
    """
    Convert raw text into a weighted meaning vector.
    No response generation here — only dimension scoring.
    """
    text = str(raw_text or "").strip()
    if not text:
        return _empty_vector(raw_text)

    normalized = " ".join(text.lower().split())
    tokens = _tokenize(text)
    evidence: list[dict] = []

    # ── Score speech act dimensions ──────────────────────────────────────────
    sa_scores = {}
    for dim, keywords in SPEECH_ACT_KEYWORDS.items():
        kw_score = _score_keyword_match(tokens, keywords)
        phrase_score = _score_phrase_match(normalized, keywords)
        # Phrase match weighs higher than individual tokens
        score = max(kw_score * 0.5, phrase_score)
        if phrase_score > 0:
            evidence.append({"dim": dim, "match": "phrase", "score": phrase_score})
        elif kw_score > 0:
            evidence.append({"dim": dim, "match": "token", "score": kw_score})
        sa_scores[dim] = min(score, 1.0)

    # ── Score relational dimensions ─────────────────────────────────────────
    rel_scores = {}
    for dim, keywords in RELATIONAL_KEYWORDS.items():
        kw_score = _score_keyword_match(tokens, keywords)
        phrase_score = _score_phrase_match(normalized, keywords)
        score = max(kw_score * 0.5, phrase_score)
        if phrase_score > 0:
            evidence.append({"dim": f"relational.{dim}", "match": "phrase", "score": phrase_score})
        rel_scores[dim] = min(score, 1.0)

    # ── Score state query dimensions ─────────────────────────────────────────
    sq_scores = {}
    for dim, keywords in STATE_QUERY_KEYWORDS.items():
        kw_score = _score_keyword_match(tokens, keywords)
        phrase_score = _score_phrase_match(normalized, keywords)
        score = max(kw_score * 0.5, phrase_score)
        if phrase_score > 0:
            evidence.append({"dim": f"state_query.{dim}", "match": "phrase", "score": phrase_score})
        sq_scores[dim] = min(score, 1.0)

    # ── Score safety/identity dimensions ────────────────────────────────────
    safety_scores = {}
    for dim, keywords in SAFETY_KEYWORDS.items():
        kw_score = _score_keyword_match(tokens, keywords)
        phrase_score = _score_phrase_match(normalized, keywords)
        score = max(kw_score * 0.5, phrase_score)
        safety_scores[dim] = min(score, 1.0)

    # ── Affect scoring (simple) ──────────────────────────────────────────────
    positive = sum(1 for t in tokens if t in ["thanks", "great", "good", "love", "appreciate", "excellent", "wonderful", "nice"])
    negative = sum(1 for t in tokens if t in ["frustrated", "angry", "hate", "annoying", "useless", "broken", "waste"])
    total = len(tokens) or 1
    affect_scores = {
        "positive": min(positive / total, 1.0),
        "negative": min(negative / total, 1.0),
        "neutral": max(0.0, 1.0 - (positive + negative) / total),
    }

    # ── Ambiguity and confidence ─────────────────────────────────────────────
    total_signal = sum(sa_scores.values()) + sum(rel_scores.values()) + sum(sq_scores.values())
    ambiguity = max(0.0, 1.0 - total_signal / 20.0)  # More dimensions = less ambiguous

    non_zero_dims = sum(1 for v in list(sa_scores.values()) + list(rel_scores.values()) + list(sq_scores.values()) if v > 0)
    confidence = min(1.0, non_zero_dims / 4.0) if non_zero_dims > 0 else 0.3

    # ── Primary dimension selection ─────────────────────────────────────────
    # When multiple dimensions tie at max, prefer most specific (priority order).
    # Priority: self_model_query > identity_query > memory_query > first_contact > question > greeting
    PRIORITY = ["self_model_query", "identity_query", "memory_query", "capability_query",
                 "first_contact", "relationship_check", "question", "greeting", "self_disclosure"]
    max_score = max(sa_scores.values()) if sa_scores else 0.0
    candidates = [dim for dim, score in sa_scores.items() if score == max_score]
    if len(candidates) > 1:
        primary_speech_act = next((d for d in PRIORITY if d in candidates), candidates[0])
    else:
        primary_speech_act = candidates[0] if candidates else "unknown"

    max_rel_score = max(rel_scores.values()) if rel_scores else 0.0
    rel_candidates = [d for d, s in rel_scores.items() if s == max_rel_score]
    if len(rel_candidates) > 1:
        primary_relational_frame = next((d for d in PRIORITY if d in rel_candidates), rel_candidates[0])
    else:
        primary_relational_frame = rel_candidates[0] if rel_candidates else "unknown"

    max_sq_score = max(sq_scores.values()) if sq_scores else 0.0
    sq_candidates = [d for d, s in sq_scores.items() if s == max_sq_score]
    if len(sq_candidates) > 1:
        primary_state_query = next((d for d in PRIORITY if d in sq_candidates), sq_candidates[0])
    else:
        primary_state_query = sq_candidates[0] if sq_candidates else "unknown"

    # ── Required state (derived from high-scoring dimensions) ────────────────
    required_state: list[str] = []
    if sa_scores.get("identity_query", 0) > 0.2:
        required_state.append("identity_state")
    if sa_scores.get("memory_query", 0) > 0.2:
        required_state.append("memory_state")
    if sa_scores.get("self_model_query", 0) > 0.2:
        required_state.append("self_model")
    if rel_scores.get("first_contact", 0) > 0.2:
        required_state.append("identity_state")
        required_state.append("session_profile")
    if rel_scores.get("relationship_check", 0) > 0.2:
        required_state.append("identity_state")
        required_state.append("relationship_depth")
    if sq_scores.get("needs_identity_state", 0) > 0.2:
        required_state.append("identity_state")
    if sq_scores.get("needs_memory_state", 0) > 0.2:
        required_state.append("memory_state")
    if sq_scores.get("needs_self_model", 0) > 0.2:
        required_state.append("self_model")
    if sq_scores.get("needs_capability_model", 0) > 0.2:
        required_state.append("capability_model")
    if sq_scores.get("needs_current_session", 0) > 0.2:
        required_state.append("current_session")

    # Deduplicate
    seen = set()
    deduped = []
    for s in required_state:
        if s not in seen:
            seen.add(s)
            deduped.append(s)

    return MeaningVector(
        raw_text=raw_text,
        normalized_text=normalized,
        tokens=tokens,
        speech_act_scores=sa_scores,
        relational_scores=rel_scores,
        state_query_scores=sq_scores,
        safety_scores=safety_scores,
        affect_scores=affect_scores,
        ambiguity=ambiguity,
        confidence=confidence,
        primary_speech_act=primary_speech_act,
        primary_relational_frame=primary_relational_frame,
        primary_state_query=primary_state_query,
        required_state=deduped,
        evidence=evidence,
    )


def _empty_vector(raw_text: str) -> MeaningVector:
    return MeaningVector(
        raw_text=raw_text,
        normalized_text="",
        tokens=[],
        speech_act_scores={},
        relational_scores={},
        state_query_scores={},
        safety_scores={},
        affect_scores={"positive": 0.0, "negative": 0.0, "neutral": 1.0},
        ambiguity=1.0,
        confidence=0.0,
        primary_speech_act="unknown",
        primary_relational_frame="unknown",
        primary_state_query="unknown",
        required_state=[],
        evidence=[],
    )