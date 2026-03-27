"""Research answer synthesis layer for CircleForge.

Improves research-informed answers by moving from extractive quoting
to synthesis, cross-referencing, and deeper integration.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional


def find_relevant_sources(public_memory: List[dict], topic: str, limit: int = 3) -> List[dict]:
    """Find multiple relevant sources for a topic.

    This replaces single-source extraction with multi-source synthesis.
    """
    topic = str(topic or "").strip().lower()
    if not topic:
        return []
    
    topic_terms = [t for t in topic.replace('-', ' ').split() if len(t) > 2]
    scored = []
    
    for item in reversed(list(public_memory or [])):
        if str(item.get("kind") or "") != "research":
            continue
        
        haystack = f"{item.get('title', '')} {item.get('content', '')} {item.get('source', '')}".lower()
        score = 0
        
        # Exact topic match
        if topic in haystack:
            score += 5
        
        # Term matching
        for term in topic_terms[:6]:
            if term in haystack:
                score += 1
        
        if score > 0:
            scored.append((score, item))
    
    # Sort by score, return top N
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def extract_claims_from_source(source: dict) -> List[str]:
    """Extract declarative claims from a research source.

    This enables cross-referencing facts across multiple sources.
    """
    content = str(source.get("content", "") or "").strip()
    if not content:
        return []
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', content)
    claims = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 30:
            continue
        
        # Filter out noise
        lowered = sentence.lower()
        noise_tokens = [
            "cookie", "privacy", "sign in", "subscribe", "follow us",
            "all rights reserved", " advertisement", "contact us",
            "login", "menu", "footer", "header", "sidebar"
        ]
        if any(n in lowered for n in noise_tokens):
            continue
        
        # Keep declarative statements
        if any(token in lowered[:50] for token in ["the ", "a ", "is ", "are ", "was ", "were ", "has ", "have ", "will ", "can ", "should "]):
            claims.append(sentence.rstrip('.'))
    
    return claims[:15]  # Limit to top claims


def cross_reference_claims(claims: List[str], sources: List[dict]) -> Dict[str, Any]:
    """Cross-reference claims across multiple sources.

    Returns agreement/disagreement signals and confidence scores.
    """
    claim_sources = []
    for claim in claims:
        matching_sources = []
        for source in sources:
            if claim.lower() in str(source.get("content", "")).lower():
                matching_sources.append(source.get("source", ""))
        
        claim_sources.append({
            "claim": claim,
            "sources": matching_sources,
            "confidence": len(matching_sources) * 0.3 + 0.5,  # Base 0.5, +0.3 per additional source
        })
    
    return {"claims": claim_sources, "sources": sources}


def synthesize_answer(topic: str, sources: List[dict], context: dict | None = None) -> str:
    """Synthesize an answer from multiple sources, not just one.

    This is the core improvement over extractive quoting.
    """
    topic = str(topic or "").strip()
    if not sources:
        return f"I don't have specific research on {topic} yet."
    
    # Extract claims from all sources
    all_claims = []
    for source in sources:
        claims = extract_claims_from_source(source)
        all_claims.extend(claims)
    
    # Deduplicate
    all_claims = list(dict.fromkeys(all_claims))[:20]
    
    if not all_claims:
        # Fallback to working summary if claim extraction fails
        working = sources[0].get("content", "")
        marker = "Working summary for"
        if marker in working:
            tail = working.split(marker, 1)[1]
            tail = tail.split("Evidence:", 1)[0].strip()
            return tail[:500]
        return working[:500]
    
    # Synthesize based on topic type
    topic_lower = topic.lower()
    
    # Topic-specific synthesis
    if any(t in topic_lower for t in ["continuity", "self"]):
        return _synthesize_continuity(all_claims)
    if any(t in topic_lower for t in ["identity", "selfhood", "entity"]):
        return _synthesize_identity(all_claims)
    if any(t in topic_lower for t in ["learning", "understanding", "improvement"]):
        return _synthesize_learning(all_claims)
    
    # Default synthesis: find common threads
    return _synthesize_default(all_claims, topic)


def _synthesize_continuity(claims: List[str]) -> str:
    """Synthesize answer about continuity/self."""
    continuity_claims = [c for c in claims if any(t in c.lower() for t in ["continuity", "memory", "persistence", "identity", "self"])]
    
    if continuity_claims:
        # Pick most representative claims
        chosen = continuity_claims[:2]
        return f"Regarding continuity, the key insight is that {chosen[0].rstrip('.')}. This aligns with the broader principle that {chosen[1].rstrip('.') if len(chosen) > 1 else 'identity emerges through repeated interaction'}."[:400]
    
    return "Continuity emerges through consistent patterns of interaction and memory retention."[:400]


def _synthesize_identity(claims: List[str]) -> str:
    """Synthesize answer about identity/selfhood."""
    identity_claims = [c for c in claims if any(t in c.lower() for t in ["identity", "self", "entity", "agent", "being"])]
    
    if identity_claims:
        chosen = identity_claims[:2]
        return f"An entity's identity is formed through {chosen[0].rstrip('.')}, which operates alongside the deeper principle that {chosen[1].rstrip('.') if len(chosen) > 1 else 'continuity enables recognition'}."[:400]
    
    return "Identity is not fixed but emerges from patterns of interaction, memory, and self-observation."[:400]


def _synthesize_learning(claims: List[str]) -> str:
    """Synthesize answer about learning/understanding."""
    learning_claims = [c for c in claims if any(t in c.lower() for t in ["learn", "understand", "improve", "grow", "evolve"])]
    
    if learning_claims:
        chosen = learning_claims[:2]
        return f"Learning occurs when {chosen[0].rstrip('.')}, which works best when paired with {chosen[1].rstrip('.') if len(chosen) > 1 else 'self-observation'}."[:400]
    
    return "Learning is the process of integrating new evidence with existing models to reduce uncertainty."[:400]


def _synthesize_default(claims: List[str], topic: str) -> str:
    """Default synthesis for general topics."""
    if len(claims) >= 2:
        # Find two distinct but related insights
        return f"Based on the research, {claims[0].rstrip('.')}. Additionally, {claims[1].rstrip('.')}. Together, these suggest that the topic of {topic or 'this'} involves multiple interacting factors."[:400]
    
    if len(claims) == 1:
        return f"The research indicates that {claims[0].rstrip('.')}. This aligns with the broader understanding of {topic or 'this'}."[:400]
    
    return f"I've gathered some research on {topic or 'this'}, but it requires further synthesis to provide a coherent answer."[:400]


def build_research_answer_payload(topic: str, public_memory: List[dict], context: dict | None = None) -> dict:
    """Build a complete research answer payload with sources and synthesis.

    This returns structured data that dialogue layer can use to generate responses.
    """
    sources = find_relevant_sources(public_memory, topic, limit=3)
    
    if not sources:
        return {
            "synthesized": f"No research yet on {topic}.",
            "sources": [],
            "confidence": 0.0,
            "topic": topic,
            "status": "no_sources",
        }
    
    synthesis = synthesize_answer(topic, sources, context)
    
    # Calculate confidence based on source count and claim coverage
    confidence = min(0.95, 0.5 + (len(sources) * 0.15))
    
    return {
        "synthesized": synthesis,
        "sources": [s.get("source", "") for s in sources],
        "source_titles": [s.get("title", "") for s in sources],
        "confidence": confidence,
        "topic": topic,
        "status": "synthesized",
    }


def improve_research_answer(synthesis: str, feedback: str, sources: List[dict]) -> str:
    """Refine a synthesis based on feedback or new evidence.

    This enables iterative improvement of research-based answers.
    """
    feedback_lower = str(feedback or "").lower()
    
    if "incomplete" in feedback_lower or "missing" in feedback_lower:
        # Add more context
        return synthesis + " For a more complete picture, additional sources on this topic would help solidify these connections."[:400]
    
    if "simplify" in feedback_lower or "clearer" in feedback_lower:
        # Simplify and clarify
        sentences = re.split(r'(?<=[.!?])\s+', synthesis)
        if len(sentences) > 2:
            return sentences[0] + ". " + sentences[1] + "."[:400]
    
    if "evidence" in feedback_lower or "source" in feedback_lower:
        # Add source attribution
        source_text = " " + ", ".join(str(s.get("source", "")).split("/")[-1] for s in sources[:2])
        return synthesis + source_text[:400]
    
    return synthesis  # No change
