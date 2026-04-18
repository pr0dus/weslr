"""Request Classifier

Classifies requests into structured taxonomy for intelligent routing.

Beyond simple keyword matching:
- Multi-category classification
- Confidence scoring per category
- Cross-category disambiguation
- Difficulty-aware classification
- Evidence-aware classification

Classification taxonomy:
- ROUTING_CATEGORIES: Where should this go? (routing decision)
- REQUIREMENT_CATEGORIES: What does this need? (capability matching)
- EVIDENCE_CATEGORIES: What evidence is needed? (evidence policy)

This classifier feeds into the broader RequestIntelligence layer.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class RoutingCategory(Enum):
    """Where should this request be routed?"""
    LOCAL = "LOCAL"  # Can be handled with local evidence (time, weather)
    EVIDENCE = "EVIDENCE"  # Requires external evidence
    RESEARCH = "RESEARCH"  # Requires web research
    REASONING = "REASONING"  # Requires reasoning capabilities
    UNSUPPORTED = "UNSUPPORTED"  # Cannot be handled


class RequirementCategory(Enum):
    """What capabilities does this require?"""
    FACT = "FACT"  # Simple factual query
    CALCULATION = "CALCULATION"  # Math/computation
    ANALYSIS = "ANALYSIS"  # Analysis/interpretation
    CREATION = "CREATION"  # Content generation
    SYNTHESIS = "SYNTHESIS"  # Multi-source synthesis


class EvidenceCategory(Enum):
    """What type of evidence is needed?"""
    TIME = "TIME"  # System time
    WEATHER = "WEATHER"  # Weather data
    WEB = "WEB"  # Web search results
    FILE = "FILE"  # File content analysis
    CONTEXT = "CONTEXT"  # Existing context/snapshot


class ClassifierResult:
    """Result of request classification."""
    
    def __init__(
        self,
        primary_routing: RoutingCategory,
        secondary_categories: Dict[RequirementCategory, float] = None,
        evidence_requirements: List[EvidenceCategory] = None,
        confidence: float = 1.0,
        analysis: Dict[str, Any] = None,
    ):
        self.primary_routing = primary_routing
        self.secondary_categories = secondary_categories or {}
        self.evidence_requirements = evidence_requirements or []
        self.confidence = confidence
        self.analysis = analysis or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_routing": self.primary_routing.value,
            "secondary_categories": {k.value: v for k, v in self.secondary_categories.items()},
            "evidence_requirements": [e.value for e in self.evidence_requirements],
            "confidence": self.confidence,
            "analysis": self.analysis,
        }
    
    def __repr__(self) -> str:
        return f"ClassifierResult(routing={self.primary_routing.value}, confidence={self.confidence:.2f})"


class RequestClassifier:
    """Classifies requests into structured taxonomy.
    
    Produces multi-dimensional classification:
    - Primary routing category (where to send)
    - Secondary requirement categories (what capabilities needed)
    - Evidence requirements (what evidence sources needed)
    - Confidence scores (how sure we are about each category)
    
    Designed to be lightweight and fast for runtime use.
    """
    
    def __init__(self):
        # Evidence category keywords
        self._evidence_keywords = {
            EvidenceCategory.TIME: [
                "time", "now", "currently", "date", "clock", "timestamp",
                "current time", "what time", "current date",
            ],
            EvidenceCategory.WEATHER: [
                "weather", "temperature", "temp", "forecast", "rain", "snow",
                "sunny", "cloudy", "storm", "wind", "humidity",
            ],
            EvidenceCategory.WEB: [
                "research", "search", "find", "look up", "google", "web",
                "internet", "online", "website", "page",
            ],
            EvidenceCategory.FILE: [
                "file", "document", "pdf", "txt", "csv", "json", "yaml",
                "upload", "attachment", "read", "analyze file",
            ],
            EvidenceCategory.CONTEXT: [
                "previous", "before", "earlier", "context", "memory",
                "history", "past", "recent", "conversation",
            ],
        }
        
        # Routing category patterns
        self._routing_patterns = {
            RoutingCategory.LOCAL: [
                r"\b(what time|current time|now)\b",
                r"\b(weather|temperature)\b",
                r"\b(calculate|compute|add|subtract|multiply|divide)\b",
                r"\b(who is|what is|define|meaning)\b",
            ],
            RoutingCategory.EVIDENCE: [
                r"\b(population|count|number|value|price|rate|score)\b",
                r"\b(star|planet|galaxy|astronomy)\b",
                r"\b(molecule|compound|chemical|reaction)\b",
            ],
            RoutingCategory.RESEARCH: [
                r"\b(research|study|paper|experiment|finding)\b",
                r"\b(history|background|origin|development)\b",
                r"\b(compare|contrast|analysis|interpretation)\b",
            ],
            RoutingCategory.REASONING: [
                r"\b(why|reason|explanation|logic|rationale)\b",
                r"\b(analyze|interpret|evaluate|assess|judgment)\b",
                r"\b(explain why|reason about|philosophy)\b",
            ],
        }
    
    def classify(self, request_text: str, context: Dict[str, Any] = None) -> ClassifierResult:
        """Classify the request.
        
        Args:
            request_text: The request to classify
            context: Additional context (optional)
            
        Returns:
            ClassifierResult with routing, requirements, and evidence categories
        """
        context = context or {}
        text_lower = request_text.lower().strip()
        
        # Evidence category detection
        evidence_requirements = []
        evidence_scores = {}
        
        for cat, keywords in self._evidence_keywords.items():
            score = 0.0
            for kw in keywords:
                if kw in text_lower:
                    score += 0.3
            if score > 0:
                evidence_requirements.append(cat)
                evidence_scores[cat] = min(1.0, score)
        
        # Routing category detection
        routing_scores = {}
        for cat, patterns in self._routing_patterns.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 0.4
            if score > 0:
                routing_scores[cat] = min(1.0, score)
        
        # Determine primary routing (highest score)
        if routing_scores:
            primary_routing = max(routing_scores.keys(), key=lambda k: routing_scores[k])
        else:
            primary_routing = RoutingCategory.UNSUPPORTED
        
        # Determine secondary requirement categories
        requirement_categories = self._detect_requirements(request_text, context)
        
        # Build confidence score
        base_confidence = 0.7
        if len(evidence_requirements) > 0:
            base_confidence += 0.1 * len(evidence_requirements)
        if routing_scores.get(primary_routing, 0) > 0.8:
            base_confidence += 0.1
        base_confidence = min(1.0, base_confidence)
        
        # Build analysis
        analysis = {
            "evidence_keywords_matched": list(evidence_scores.keys()),
            "routing_patterns_matched": dict(routing_scores),
            "requirement_categories": {k.value: v for k, v in requirement_categories.items()},
        }
        
        return ClassifierResult(
            primary_routing=primary_routing,
            secondary_categories=requirement_categories,
            evidence_requirements=evidence_requirements,
            confidence=base_confidence,
            analysis=analysis,
        )
    
    def _detect_requirements(self, request_text: str, context: Dict[str, Any]) -> Dict[RequirementCategory, float]:
        """Detect required capabilities from request."""
        text_lower = request_text.lower()
        
        scores = {}
        
        # Calculation detection
        calc_keywords = ["calculate", "compute", "add", "subtract", "multiply", "divide", "math", "maths"]
        if any(kw in text_lower for kw in calc_keywords):
            scores[RequirementCategory.CALCULATION] = 0.9
        elif re.search(r"\d+\s*[\+\-\*\/]\s*\d+", text_lower):
            scores[RequirementCategory.CALCULATION] = 0.7
        
        # Fact detection (default)
        if RequirementCategory.CALCULATION not in scores:
            fact_keywords = ["who is", "what is", "where is", "when is", "define", "meaning"]
            if any(kw in text_lower for kw in fact_keywords):
                scores[RequirementCategory.FACT] = 0.8
            else:
                scores[RequirementCategory.FACT] = 0.5  # Default
        
        # Analysis detection
        analysis_keywords = ["analyze", "interpret", "compare", "contrast", "explain", "reason"]
        if any(kw in text_lower for kw in analysis_keywords):
            scores[RequirementCategory.ANALYSIS] = 0.8
        
        # Creation detection
        creation_keywords = ["create", "write", "generate", "compose", "draft"]
        if any(kw in text_lower for kw in creation_keywords):
            scores[RequirementCategory.CREATION] = 0.8
        
        # Synthesis detection
        synthesis_keywords = ["synthesis", "integrate", "combine", "relate", "connect"]
        if any(kw in text_lower for kw in synthesis_keywords):
            scores[RequirementCategory.SYNTHESIS] = 0.8
        
        # Research detection
        research_keywords = ["research", "study", "paper", "article", "find", "search"]
        if any(kw in text_lower for kw in research_keywords):
            scores[RequirementCategory.ANALYSIS] = 0.7  # Research requires analysis capability
        
        return scores
    
    def classify_simple(self, request_text: str, context: Dict[str, Any] = None) -> Tuple[RoutingCategory, List[EvidenceCategory]]:
        """Fast classification - just routing and evidence categories."""
        result = self.classify(request_text, context)
        return result.primary_routing, result.evidence_requirements
