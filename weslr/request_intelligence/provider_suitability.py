"""Provider Suitability Scorer

Scores providers for suitability given a request.

Providers are the execution endpoints:
- Embedded (GGUF model)
- Llama-server (local API)
- Ollama (remote API)
- OpenAI-compatible
- Claude
- Fallback (no LLM)

Suitability considers:
- Capability match (can it handle the request?)
- Evidence availability (can it get needed evidence?)
- Latency requirements (how fast does it need to be?)
- Quality requirements (what confidence is needed?)
- Cost constraints (if applicable)

Used by:
- RequestIntelligence for provider selection
- Runtime routing decisions
- Load balancing across providers
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ProviderType(Enum):
    """Types of providers."""
    EMBEDDED = "embedded"  # Local GGUF inference
    LLAMA_SERVER = "llama-server"  # Local llama-server
    OLLAMA = "ollama"  # Remote Ollama
    OPENAI = "openai"  # OpenAI or compatible
    CLAUDE = "claude"  # Anthropic Claude
    FALLBACK = "fallback"  # No LLM (fallback only)
    EVIDENCE = "evidence"  # Evidence APIs only (time, weather)


class ProviderScore:
    """Score for a provider on a request."""
    
    def __init__(
        self,
        provider_type: ProviderType,
        provider_name: str,
        score: float,
        suitability_factors: Dict[str, float] = None,
        evidence_score: float = 1.0,
        latency_ms: int = 0,
        confidence: float = 1.0,
    ):
        self.provider_type = provider_type
        self.provider_name = provider_name
        self.score = score  # 0-1
        self.suitability_factors = suitability_factors or {}
        self.evidence_score = evidence_score
        self.latency_ms = latency_ms
        self.confidence = confidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_type": self.provider_type.value,
            "provider_name": self.provider_name,
            "score": self.score,
            "suitability_factors": self.suitability_factors,
            "evidence_score": self.evidence_score,
            "latency_ms": self.latency_ms,
            "confidence": self.confidence,
        }
    
    def __repr__(self) -> str:
        return f"ProviderScore({self.provider_name}, score={self.score:.2f})"


class ProviderSuitability:
    """Scores provider suitability for requests.
    
    Considers:
    - Provider capabilities (what can it do?)
    - Evidence access (what evidence can it get?)
    - Latency profile (how fast is it?)
    - Quality profile (how accurate is it?)
    - Cost profile (if applicable)
    
    Produces normalized scores for provider selection.
    """
    
    def __init__(self):
        # Provider capabilities mapping
        self._provider_capabilities = {
            ProviderType.EMBEDDED: {
                "capabilities": ["reasoning", "analysis", "local_generation"],
                "evidence_types": ["context", "cached"],
                "latency_ms": 200,
                "quality": 0.85,
                "cost": "free",
            },
            ProviderType.LLAMA_SERVER: {
                "capabilities": ["reasoning", "analysis", "generation"],
                "evidence_types": ["context", "cached", "local"],
                "latency_ms": 500,
                "quality": 0.9,
                "cost": "free",
            },
            ProviderType.OLLAMA: {
                "capabilities": ["reasoning", "analysis", "generation"],
                "evidence_types": ["context", "cached", "local"],
                "latency_ms": 800,
                "quality": 0.88,
                "cost": "free",
            },
            ProviderType.OPENAI: {
                "capabilities": ["reasoning", "analysis", "generation", "research"],
                "evidence_types": ["context", "cached", "web", "research"],
                "latency_ms": 1500,
                "quality": 0.95,
                "cost": "paid",
            },
            ProviderType.CLAUDE: {
                "capabilities": ["reasoning", "analysis", "generation", "synthesis"],
                "evidence_types": ["context", "cached", "web", "research"],
                "latency_ms": 1200,
                "quality": 0.94,
                "cost": "paid",
            },
            ProviderType.EVIDENCE: {
                "capabilities": ["time", "weather", "facts"],
                "evidence_types": ["time", "weather", "web"],
                "latency_ms": 500,
                "quality": 0.99,
                "cost": "free",
            },
        }
        
        # Evidence provider names (for evidence-based routing)
        self._evidence_providers = {
            "time": "system_time",
            "weather": "weather_api",
        }
    
    def score(self, provider_type: ProviderType, request_text: str, context: Dict[str, Any] = None) -> ProviderScore:
        """Score a provider for a request.
        
        Args:
            provider_type: The provider to score
            request_text: The request to handle
            context: Additional context (optional)
            
        Returns:
            ProviderScore with suitability metrics
        """
        context = context or {}
        
        # Get provider capabilities
        caps = self._provider_capabilities.get(provider_type, {})
        
        # Calculate scores
        capability_score = self._calculate_capability_score(provider_type, request_text, context, caps)
        evidence_score = self._calculate_evidence_score(provider_type, request_text, context, caps)
        latency_score = self._calculate_latency_score(provider_type, caps)
        quality_score = caps.get("quality", 0.8)
        
        # Combine scores
        # Weight: capability 40%, evidence 30%, latency 15%, quality 15%
        score = (
            capability_score * 0.4 +
            evidence_score * 0.3 +
            latency_score * 0.15 +
            quality_score * 0.15
        )
        
        # Build suitability factors
        suitability_factors = {
            "capability": capability_score,
            "evidence": evidence_score,
            "latency": latency_score,
            "quality": quality_score,
        }
        
        return ProviderScore(
            provider_type=provider_type,
            provider_name=self._get_provider_name(provider_type, context),
            score=min(1.0, score),
            suitability_factors=suitability_factors,
            evidence_score=evidence_score,
            latency_ms=caps.get("latency_ms", 1000),
            confidence=quality_score,
        )
    
    def score_all(self, request_text: str, context: Dict[str, Any] = None) -> List[ProviderScore]:
        """Score all providers for a request.
        
        Returns sorted list (highest score first).
        """
        scores = []
        for provider_type in ProviderType:
            if provider_type != ProviderType.FALLBACK:  # Skip fallback
                score = self.score(provider_type, request_text, context)
                scores.append(score)
        
        scores.sort(key=lambda s: s.score, reverse=True)
        return scores
    
    def _calculate_capability_score(
        self,
        provider_type: ProviderType,
        request_text: str,
        context: Dict[str, Any],
        caps: Dict[str, Any],
    ) -> float:
        """Calculate capability match score."""
        text_lower = request_text.lower()
        capabilities = caps.get("capabilities", [])
        
        # Check for capability keywords
        capability_matches = 0
        for cap in capabilities:
            cap_lower = cap.lower()
            if cap_lower in text_lower:
                capability_matches += 1
        
        # Base score from matches
        base_score = capability_matches / max(1, len(capabilities))
        
        # Boost for evidence providers
        if provider_type == ProviderType.EVIDENCE:
            evidence_keywords = ["time", "weather", "temperature", "now", "currently"]
            if any(kw in text_lower for kw in evidence_keywords):
                base_score = min(1.0, base_score + 0.3)
        
        return min(1.0, base_score)
    
    def _calculate_evidence_score(
        self,
        provider_type: ProviderType,
        request_text: str,
        context: Dict[str, Any],
        caps: Dict[str, Any],
    ) -> float:
        """Calculate evidence access score."""
        text_lower = request_text.lower()
        evidence_types = caps.get("evidence_types", [])
        
        # Check if evidence is available in context
        evidence_available = False
        for ev_type in evidence_types:
            if ev_type == "context" and context:
                evidence_available = True
            elif ev_type == "time" and any(kw in text_lower for kw in ["time", "now", "currently"]):
                evidence_available = True
            elif ev_type == "weather" and any(kw in text_lower for kw in ["weather", "temperature"]):
                evidence_available = True
        
        # Score based on evidence availability
        if evidence_available:
            return 0.9
        elif "local" in evidence_types or "cached" in evidence_types:
            return 0.7
        else:
            return 0.5
    
    def _calculate_latency_score(self, provider_type: ProviderType, caps: Dict[str, Any]) -> float:
        """Calculate latency score (lower latency = higher score)."""
        latency_ms = caps.get("latency_ms", 1000)
        
        # Score inversely related to latency
        # <100ms: 1.0, 1000ms: 0.5, >5000ms: 0.1
        if latency_ms < 100:
            return 1.0
        elif latency_ms < 500:
            return 0.9
        elif latency_ms < 1500:
            return 0.7
        elif latency_ms < 3000:
            return 0.5
        else:
            return 0.3
    
    def _get_provider_name(self, provider_type: ProviderType, context: Dict[str, Any]) -> str:
        """Get provider name from context or type."""
        if provider_type == ProviderType.EMBEDDED:
            return "embedded"
        elif provider_type == ProviderType.EVIDENCE:
            return "evidence"
        elif provider_type == ProviderType.OPENAI:
            return context.get("openai_provider", "openai")
        elif provider_type == ProviderType.CLAUDE:
            return "claude"
        elif provider_type == ProviderType.OLLAMA:
            return "ollama"
        else:
            return provider_type.value
    
    def get_best_provider(self, request_text: str, context: Dict[str, Any] = None) -> ProviderScore:
        """Get the best provider for a request."""
        scores = self.score_all(request_text, context)
        if scores:
            return scores[0]
        return None
    
    def get_evidence_provider(self, request_text: str) -> str:
        """Get appropriate evidence provider for request."""
        text_lower = request_text.lower()
        
        if any(kw in text_lower for kw in ["time", "now", "currently", "date"]):
            return self._evidence_providers.get("time", "system_time")
        elif any(kw in text_lower for kw in ["weather", "temperature", "forecast"]):
            return self._evidence_providers.get("weather", "weather_api")
        else:
            return "none"
