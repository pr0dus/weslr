"""Capability Matcher

Matches requests to available capabilities and tools.

Capabilities are the execution units available to handle requests:
- File ingestion
- PDF processing
- Scientific analysis
- Materials analysis
- Evidence retrieval (time, weather)
- Web search
- Calculation
- Reasoning

Matching determines:
- Which capabilities can handle the request
- How well each capability matches (score 0-1)
- What evidence each capability needs
- What output each capability produces

Used by:
- RequestIntelligence for capability selection
- ProviderSuitability for provider matching
- Routing decisions
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set


class Capability:
    """A capability that can handle requests."""
    
    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[str],  # Types of requests it can handle
        evidence_types: List[str] = None,
        output_types: List[str] = None,
        confidence: float = 0.8,
        latency_ms: int = 100,
    ):
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.evidence_types = evidence_types or []
        self.output_types = output_types or []
        self.confidence = confidence
        self.latency_ms = latency_ms
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "evidence_types": self.evidence_types,
            "output_types": self.output_types,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
        }
    
    def __repr__(self) -> str:
        return f"Capability({self.name}, capabilities={self.capabilities})"


class CapabilityMatch:
    """Result of matching a request to a capability."""
    
    def __init__(
        self,
        capability: Capability,
        match_score: float,
        evidence_requirements: List[str] = None,
        estimated_latency_ms: int = None,
        confidence: float = 1.0,
    ):
        self.capability = capability
        self.match_score = match_score  # 0-1
        self.evidence_requirements = evidence_requirements or []
        self.estimated_latency_ms = estimated_latency_ms or capability.latency_ms
        self.confidence = confidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability": self.capability.to_dict(),
            "match_score": self.match_score,
            "evidence_requirements": self.evidence_requirements,
            "estimated_latency_ms": self.estimated_latency_ms,
            "confidence": self.confidence,
        }
    
    def __repr__(self) -> str:
        return f"CapabilityMatch({self.capability.name}, score={self.match_score:.2f})"


class CapabilityMatcher:
    """Matches requests to capabilities.
    
    Takes a request and context, then returns:
    - Matching capabilities with scores
    - Evidence requirements for each
    - Estimated latency
    - Confidence in match
    
    Designed for fast lookup and scoring.
    """
    
    def __init__(self):
        # Registered capabilities
        self._capabilities = {}
        self._register_default_capabilities()
    
    def _register_default_capabilities(self):
        """Register default capabilities based on available modules."""
        # File-based capabilities
        self._capabilities["file_ingestion"] = Capability(
            name="file_ingestion",
            description="Ingest and analyze text-based files",
            capabilities=["file_analysis", "content_extraction", "text_analysis"],
            evidence_types=["file", "content"],
            output_types=["content", "summary"],
            latency_ms=500,
        )
        
        self._capabilities["pdf_context"] = Capability(
            name="pdf_context",
            description="Process PDF documents with context awareness",
            capabilities=["pdf_analysis", "document_understanding", "structured_extraction"],
            evidence_types=["file", "pdf"],
            output_types=["content", "summary", "structured"],
            latency_ms=1000,
        )
        
        # Evidence-based capabilities
        self._capabilities["evidence_time"] = Capability(
            name="evidence_time",
            description="Get system time evidence",
            capabilities=["time_query", "date_query"],
            evidence_types=["system_time"],
            output_types=["time", "date"],
            confidence=0.99,
            latency_ms=10,
        )
        
        self._capabilities["evidence_weather"] = Capability(
            name="evidence_weather",
            description="Get weather data evidence",
            capabilities=["weather_query", "temperature_query"],
            evidence_types=["weather"],
            output_types=["weather", "temperature"],
            confidence=0.9,
            latency_ms=2000,
        )
        
        # Research capabilities
        self._capabilities["web_search"] = Capability(
            name="web_search",
            description="Search the web for information",
            capabilities=["research", "fact_lookup", "web_query"],
            evidence_types=["web"],
            output_types=["results", "snippets"],
            confidence=0.7,
            latency_ms=5000,
        )
        
        # Reasoning capabilities
        self._capabilities["reasoning"] = Capability(
            name="reasoning",
            description="Perform reasoning and analysis",
            capabilities=["reasoning", "analysis", "interpretation"],
            evidence_types=["context", "research"],
            output_types=["reasoning", "analysis"],
            confidence=0.8,
            latency_ms=3000,
        )
    
    def register_capability(self, capability: Capability):
        """Register a new capability."""
        self._capabilities[capability.name] = capability
    
    def get_capability(self, name: str) -> Capability:
        """Get a capability by name."""
        return self._capabilities.get(name)
    
    def match(self, request_text: str, context: Dict[str, Any] = None) -> List[CapabilityMatch]:
        """Match the request to capabilities.
        
        Args:
            request_text: The request to match
            context: Additional context (optional)
            
        Returns:
            List of capability matches sorted by score
        """
        context = context or {}
        text_lower = request_text.lower().strip()
        
        matches = []
        
        for cap_name, capability in self._capabilities.items():
            # Calculate match score
            score = self._calculate_match_score(capability, text_lower, context)
            
            if score > 0:
                matches.append(CapabilityMatch(
                    capability=capability,
                    match_score=score,
                    evidence_requirements=capability.evidence_types,
                    estimated_latency_ms=capability.latency_ms,
                    confidence=capability.confidence,
                ))
        
        # Sort by score descending
        matches.sort(key=lambda m: m.match_score, reverse=True)
        
        return matches
    
    def _calculate_match_score(self, capability: Capability, request_text: str, context: Dict[str, Any]) -> float:
        """Calculate match score for a capability."""
        score = 0.0
        text_lower = request_text.lower()
        
        # Check capability keywords
        for cap in capability.capabilities:
            cap_lower = cap.lower()
            if cap_lower in text_lower:
                score += 0.3
        
        # Check evidence requirements
        for evidence_type in capability.evidence_types:
            if self._has_evidence_requirement(text_lower, evidence_type, context):
                score += 0.2
        
        # Check context match
        if "active_thread" in context:
            active_thread = context["active_thread"].lower()
            if active_thread in capability.name.lower() or active_thread in capability.description.lower():
                score += 0.1
        
        # Apply confidence multiplier
        score = min(1.0, score * capability.confidence)
        
        return score
    
    def _has_evidence_requirement(self, request_text: str, evidence_type: str, context: Dict[str, Any]) -> bool:
        """Check if request has evidence for this type."""
        evidence_lower = evidence_type.lower()
        text_lower = request_text.lower()
        
        # Direct match in text
        if evidence_lower in text_lower:
            return True
        
        # Check context for evidence
        if evidence_type == "file":
            file_keywords = ["file", "pdf", "document", "upload", "attachment"]
            return any(kw in text_lower for kw in file_keywords)
        
        if evidence_type == "weather":
            weather_keywords = ["weather", "temperature", "temp", "forecast"]
            return any(kw in text_lower for kw in weather_keywords)
        
        if evidence_type == "system_time":
            time_keywords = ["time", "now", "currently", "date"]
            return any(kw in text_lower for kw in time_keywords)
        
        return False
    
    def match_simple(self, request_text: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Fast match - just return best capability name."""
        matches = self.match(request_text, context)
        if matches:
            return matches[0].capability.name
        return None
    
    def get_matching_capabilities(self, request_text: str, min_score: float = 0.3) -> List[Capability]:
        """Get capabilities that meet minimum score."""
        matches = self.match(request_text)
        return [m.capability for m in matches if m.match_score >= min_score]
    
    def list_capabilities(self) -> List[Capability]:
        """List all registered capabilities."""
        return list(self._capabilities.values())
