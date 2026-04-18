"""Knowledge State Tracker

Tracks what is known, unknown, unverifiable, and speculative in a request.

Knowledge states:
- KNOWN_FROM_EVIDENCE: Something that can be verified with available evidence
- KNOWN_FROM_CONTEXT: Something that's already in the current context
- UNKNOWN: We don't know, but it could be known with evidence
- UNVERIFIABLE: Cannot be verified (subjective, speculative, etc.)
- SPECULATIVE: Highly uncertain, requires assumption building

This module enables:
- Request intelligence: knowing what we can and can't answer
- Evidence policy: what evidence is needed to move states
- Provider suitability: choosing providers based on knowledge needs
- Uncertainty discipline: enforcing boundaries on speculative requests
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set


class KnowledgeState(Enum):
    """Categories of knowledge status."""
    KNOWN_FROM_EVIDENCE = "KNOWN_FROM_EVIDENCE"  # Can be verified with evidence
    KNOWN_FROM_CONTEXT = "KNOWN_FROM_CONTEXT"  # Already in context
    UNKNOWN = "UNKNOWN"  # Unknown but potentially knowable
    UNVERIFIABLE = "UNVERIFIABLE"  # Cannot be verified (subjective, etc.)
    SPECULATIVE = "SPECULATIVE"  # Highly uncertain, assumption-based


class KnowledgeStateResult:
    """Result of knowledge state analysis."""
    
    def __init__(
        self,
        request_knowledge_states: Dict[str, KnowledgeState],
        gaps: List[str] = None,
        unverifiable_items: List[str] = None,
        speculative_items: List[str] = None,
        confidence: float = 1.0,
        analysis: Dict[str, Any] = None,
    ):
        self.request_knowledge_states = request_knowledge_states or {}
        self.gaps = gaps or []
        self.unverifiable_items = unverifiable_items or []
        self.speculative_items = speculative_items or []
        self.confidence = confidence
        self.analysis = analysis or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_knowledge_states": {k: v.value for k, v in self.request_knowledge_states.items()},
            "gaps": self.gaps,
            "unverifiable_items": self.unverifiable_items,
            "speculative_items": self.speculative_items,
            "confidence": self.confidence,
            "analysis": self.analysis,
        }
    
    def is_fully_verifiable(self) -> bool:
        """Check if all requested knowledge is verifiable."""
        for state in self.request_knowledge_states.values():
            if state in (KnowledgeState.UNVERIFIABLE, KnowledgeState.SPECULATIVE):
                return False
        return len(self.speculative_items) == 0 and len(self.unverifiable_items) == 0
    
    def has_uncertainty(self) -> bool:
        """Check if any uncertainty exists."""
        return (
            len(self.speculative_items) > 0 or
            len(self.unverifiable_items) > 0 or
            any(s == KnowledgeState.UNKNOWN for s in self.request_knowledge_states.values())
        )


class KnowledgeStateAnalyzer:
    """Analyzes knowledge states in a request.
    
    Determines:
    - What knowledge is already available (from context)
    - What needs to be verified (from evidence)
    - What is unverifiable (subjective, etc.)
    - What is speculative (assumption-based)
    
    Returns structured knowledge state map for the request.
    """
    
    def __init__(self):
        # Context indicators - things that are typically in context
        self._context_indicators = [
            "previous conversation", "earlier", "before", "last time",
            "context", "current state", "existing knowledge",
        ]
        
        # Uncertainty indicators - signals of unverifiability/speculation
        self._uncertainty_indicators = {
            "subjective": [
                "believe", "think", "opinion", "feeling", "emotion",
                "should", "must", "ought to", "need to",
                "meaning", "purpose", "essence",
            ],
            "speculative": [
                "imagine", "create", "invent", "design", "build",
                "future", "prediction", "prophecy", "destiny",
                "universe", "existence", "consciousness",
                "spiritual", "metaphysical", "transcendental",
            ],
            "unverifiable": [
                "prove", "disprove", "absolute truth", "final answer",
                "prove that", "prove the existence",
            ],
        }
        
        # Evidence-indicators - things that can be verified
        self._evidence_indicators = [
            "weather", "temperature", "time", "date", "current",
            "population", "count", "number", "value", "price",
            "statistic", "fact", "data",
        ]
    
    def analyze(self, request_text: str, context: Dict[str, Any] = None) -> KnowledgeStateResult:
        """Analyze knowledge states in the request.
        
        Args:
            request_text: The request to analyze
            context: Current context (optional)
            
        Returns:
            KnowledgeStateResult with knowledge state mapping
        """
        context = context or {}
        text_lower = request_text.lower().strip()
        
        # Extract key concepts from request
        concepts = self._extract_concepts(text_lower)
        
        # Analyze each concept's knowledge state
        request_knowledge_states = {}
        unverifiable_items = []
        speculative_items = []
        gaps = []
        
        # Get existing context items
        existing_context = set()
        if "active_thread" in context:
            existing_context.add(context["active_thread"])
        if "proposed_theme" in context:
            existing_context.add(context["proposed_theme"])
        if "continuity" in context:
            existing_context.update(context["continuity"].get("topics", []))
        
        # Analyze each concept
        for concept in concepts:
            state = self._analyze_concept(concept, existing_context, text_lower)
            request_knowledge_states[concept] = state
            
            if state == KnowledgeState.UNVERIFIABLE:
                unverifiable_items.append(concept)
            elif state == KnowledgeState.SPECULATIVE:
                speculative_items.append(concept)
            elif state == KnowledgeState.UNKNOWN:
                gaps.append(concept)
        
        # Build analysis
        analysis = {
            "concepts_found": list(concepts),
            "existing_context": list(existing_context),
            "analysis_steps": [],
        }
        
        for concept, state in request_knowledge_states.items():
            analysis["analysis_steps"].append(f"{concept}: {state.value}")
        
        # Determine overall confidence
        base_confidence = 0.7
        if len(concepts) > 0:
            base_confidence += 0.05 * len(concepts)
        base_confidence = min(1.0, base_confidence)
        
        return KnowledgeStateResult(
            request_knowledge_states=request_knowledge_states,
            gaps=gaps,
            unverifiable_items=unverifiable_items,
            speculative_items=speculative_items,
            confidence=base_confidence,
            analysis=analysis,
        )
    
    def _extract_concepts(self, text_lower: str) -> Set[str]:
        """Extract key concepts from request text."""
        concepts = set()
        
        # Simple NLP-like extraction
        # Look for subject-verb-object patterns
        # For now, use keyword-based extraction
        
        # Time-based concepts
        time_keywords = ["time", "date", "now", "currently", "today", "yesterday", "tomorrow"]
        for kw in time_keywords:
            if kw in text_lower:
                concepts.add(kw)
        
        # Weather concepts
        weather_keywords = ["weather", "temperature", "temp", "forecast", "rain", "snow", "sunny"]
        for kw in weather_keywords:
            if kw in text_lower:
                concepts.add(kw)
        
        # Common fact patterns
        fact_patterns = [
            (r"who is ([\w\s]+)", "who_is"),
            (r"what is ([\w\s]+)", "what_is"),
            (r"where is ([\w\s]+)", "where_is"),
            (r"how to ([\w\s]+)", "how_to"),
        ]
        import re
        for pattern, prefix in fact_patterns:
            match = re.search(pattern, text_lower)
            if match:
                concepts.add(f"{prefix}_{match.group(1).strip()}")
        
        # Direct content concepts
        content_keywords = ["file", "document", "pdf", "csv", "json", "data"]
        for kw in content_keywords:
            if kw in text_lower:
                concepts.add("content_analysis")
        
        # Add request type as concept if specific
        if "weather" in text_lower:
            concepts.add("weather_query")
        if "time" in text_lower and "weather" not in text_lower:
            concepts.add("time_query")
        
        # If we have no specific concepts, mark as general inquiry
        if not concepts:
            concepts.add("general_inquiry")
        
        return concepts
    
    def _analyze_concept(self, concept: str, existing_context: Set[str], request_text: str) -> KnowledgeState:
        """Determine the knowledge state of a concept."""
        
        # Check if already in context
        if concept in existing_context:
            return KnowledgeState.KNOWN_FROM_CONTEXT
        
        # Check for unverifiable indicators
        for category, keywords in self._uncertainty_indicators.items():
            if any(kw in concept.lower() for kw in keywords):
                if category == "unverifiable":
                    return KnowledgeState.UNVERIFIABLE
                if category == "speculative":
                    return KnowledgeState.SPECULATIVE
        
        # Check for evidence-indicators
        if any(kw in concept.lower() for kw in self._evidence_indicators):
            return KnowledgeState.KNOWN_FROM_EVIDENCE
        
        # Check for context indicators (not in existing context)
        context_indicator_found = False
        for indicator in self._context_indicators:
            if indicator in concept.lower():
                context_indicator_found = True
                break
        
        if context_indicator_found:
            return KnowledgeState.UNKNOWN  # Could be known but not in current context
        
        # Default: unknown (potentially knowable with evidence)
        return KnowledgeState.UNKNOWN
    
    def analyze_simple(self, request_text: str, context: Dict[str, Any] = None) -> Dict[str, KnowledgeState]:
        """Fast analysis - just return the mapping."""
        result = self.analyze(request_text, context)
        return result.request_knowledge_states
