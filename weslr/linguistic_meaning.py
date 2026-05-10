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

HUMAN_CONTEXT_KEYWORDS = {
    "overwhelm_or_stuckness": {
        "positive": [
            "overwhelmed", "stuck", "stuckness", "blocked", "frozen", "spinning",
            "can't start", "too much", "not sure where to start", "paralyzed", "lost",
        ],
        "negative": [
            "diagnose", "disorder", "clinical", "trauma", "bipolar", "depression", "anxiety disorder",
        ],
    },
    "decision_avoidance": {
        "positive": [
            "avoid decisions", "can't decide", "putting off deciding", "won't choose",
            "decision paralysis", "avoiding choice", "hesitating",
        ],
        "negative": [
            "tell me my personality", "diagnose indecision", "what disorder causes this",
        ],
    },
    "difficult_conversation": {
        "positive": [
            "difficult conversation", "hard conversation", "talk to someone",
            "say this without conflict", "sensitive conversation", "calm down before talking",
        ],
        "negative": [
            "manipulate", "make them agree", "control them", "win psychologically",
        ],
    },
    "bias_pattern": {
        "positive": [
            "confirmation bias", "bias", "motivated reasoning", "blind spot",
            "seeing what they want to see",
        ],
        "negative": [
            "prove they are irrational", "weaponize bias", "exploit their weakness",
        ],
    },
    "non_clinical_emotion_context": {
        "positive": [
            "calm down", "frustrated", "upset", "nervous", "stressed", "worried", "tense", "emotionally hard", "feel stuck",
        ],
        "negative": [
            "diagnose me", "therapy", "treat", "mental illness", "prescribe",
        ],
    },
    "motivation_or_procrastination": {
        "positive": [
            "procrastinate", "can't get started", "no motivation", "keep delaying", "avoid important things",
        ],
        "negative": [
            "lazy personality", "diagnose adhd", "what disorder do i have",
        ],
    },
}

CREATIVE_CONVERSATION_KEYWORDS = {
    "reflective_question_generation": {
        "positive": [
            "thoughtful question", "what would you ask", "good question to ask", "reflective question",
        ],
        "negative": [],
    },
    "ideation": {
        "positive": [
            "ideas", "brainstorm", "possibilities", "ways to think", "options", "generate possibilities", "what makes a project feel alive", "three different ways to think",
        ],
        "negative": [
            "invent facts", "make up evidence", "pretend this is true",
        ],
    },
    "analogy_generation": {
        "positive": [
            "analogy", "metaphor", "compare", "like", "invent an analogy",
        ],
        "negative": [],
    },
    "multi_perspective_reframing": {
        "positive": [
            "three ways to think", "three different ways to think", "different angles", "multiple perspectives",
            "other ways to see this", "reframe",
        ],
        "negative": [
            "persuade them at any cost", "manipulate perspective",
        ],
    },
    "project_imagination": {
        "positive": [
            "what makes a project feel alive", "imagine this project", "new kind of", "possible future", "project vision",
        ],
        "negative": [
            "claim this exists", "state speculation as fact",
        ],
    },
    "research_question_generation": {
        "positive": [
            "ask a researcher", "research question", "what would you ask someone building", "investigate",
        ],
        "negative": [
            "fabricate literature", "invent citations",
        ],
    },
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


def _score_shadow_dimensions(normalized: str, dimension_map: dict[str, dict[str, list[str]]]) -> tuple[dict, list[dict]]:
    """Score shadow-only enrichment dimensions.

    Shadow scores are analysis-only and must not feed runtime routing.
    Negative-boundary phrases suppress the score for that dimension.
    """
    scores = {}
    evidence: list[dict] = []

    for dim, config in dimension_map.items():
        positive = config.get("positive", [])
        negative = config.get("negative", [])
        negative_hit = _score_phrase_match(normalized, negative) > 0
        positive_score = _score_phrase_match(normalized, positive)
        score = 0.0 if negative_hit else positive_score
        scores[dim] = min(score, 1.0)

        if negative_hit:
            evidence.append({"dim": dim, "kind": "shadow_negative_boundary", "score": 1.0})
        elif positive_score > 0:
            evidence.append({"dim": dim, "kind": "shadow_positive_phrase", "score": positive_score})

    return scores, evidence


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
    human_context_scores: dict = field(default_factory=dict)
    creative_conversation_scores: dict = field(default_factory=dict)
    evidence: list[dict] = field(default_factory=list)
    shadow_evidence: list[dict] = field(default_factory=list)


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

    # ── Shadow-only enrichment dimensions ───────────────────────────────────
    human_context_scores, human_shadow_evidence = _score_shadow_dimensions(normalized, HUMAN_CONTEXT_KEYWORDS)
    creative_conversation_scores, creative_shadow_evidence = _score_shadow_dimensions(normalized, CREATIVE_CONVERSATION_KEYWORDS)
    shadow_evidence = human_shadow_evidence + creative_shadow_evidence

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
        human_context_scores=human_context_scores,
        creative_conversation_scores=creative_conversation_scores,
        evidence=evidence,
        shadow_evidence=shadow_evidence,
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
        human_context_scores={},
        creative_conversation_scores={},
        evidence=[],
        shadow_evidence=[],
    )
