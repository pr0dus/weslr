"""Uncertainty Discipline Module

Enforces uncertainty budgets and enforcement rules for requests.

Uncertainty discipline is critical for:
- Knowing when to reject requests that can't be answered
- Defining fallback policies for uncertain requests
- Setting confidence thresholds for response generation
- Preventing speculative answers from being presented as facts

Rules:
- Uncertainty budget: maximum acceptable uncertainty level
- Fallback threshold: when to use fallback vs reject
- Confidence minimum: required confidence for response
- Uncertainty categories: known, unknown, unverifiable, speculative
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class UncertaintyCategory(Enum):
    """Categories of uncertainty."""
    KNOWN = "KNOWN"  # Can be known with available evidence
    UNKNOWN = "UNKNOWN"  # Unknown but potentially knowable
    UNVERIFIABLE = "UNVERIFIABLE"  # Cannot be verified
    SPECULATIVE = "SPECULATIVE"  # Based on assumptions


class UncertaintyBudget:
    """Uncertainty budget for a request.
    
    Defines:
    - Maximum acceptable uncertainty (0-1)
    - Confidence minimum threshold
    - Uncertainty tolerance per category
    - Fallback policy when budget exceeded
    """
    
    def __init__(
        self,
        max_uncertainty: float = 0.3,  # Max 30% uncertainty
        min_confidence: float = 0.7,  # Min 70% confidence
        uncertainty_tolerance: Dict[UncertaintyCategory, float] = None,
        fallback_policy: str = "none",  # none, cached, fallback, reject
    ):
        self.max_uncertainty = max_uncertainty
        self.min_confidence = min_confidence
        self.uncertainty_tolerance = uncertainty_tolerance or {
            UncertaintyCategory.KNOWN: 0.0,
            UncertaintyCategory.UNKNOWN: 0.2,
            UncertaintyCategory.UNVERIFIABLE: 0.5,
            UncertaintyCategory.SPECULATIVE: 0.8,
        }
        self.fallback_policy = fallback_policy
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_uncertainty": self.max_uncertainty,
            "min_confidence": self.min_confidence,
            "uncertainty_tolerance": {k.value: v for k, v in self.uncertainty_tolerance.items()},
            "fallback_policy": self.fallback_policy,
        }
    
    def allows_uncertainty(self, category: UncertaintyCategory, actual_uncertainty: float) -> bool:
        """Check if actual uncertainty is within budget for category."""
        tolerance = self.uncertainty_tolerance.get(category, 0.5)
        return actual_uncertainty <= tolerance + self.max_uncertainty
    
    def allows_response(self, actual_confidence: float, uncertainty_budget_used: float) -> bool:
        """Check if response is allowed given confidence and budget."""
        if actual_confidence < self.min_confidence:
            return False
        if uncertainty_budget_used > self.max_uncertainty:
            return False
        return True
    
    def __repr__(self) -> str:
        return f"UncertaintyBudget(max_uncertainty={self.max_uncertainty}, fallback={self.fallback_policy})"


class UncertaintyResult:
    """Result of uncertainty analysis."""
    
    def __init__(
        self,
        uncertainty_category: UncertaintyCategory,
        uncertainty_level: float,
        confidence: float,
        budget_used: float,
        allowed: bool,
        analysis: Dict[str, Any] = None,
    ):
        self.uncertainty_category = uncertainty_category
        self.uncertainty_level = uncertainty_level  # 0-1
        self.confidence = confidence  # 0-1
        self.budget_used = budget_used
        self.allowed = allowed
        self.analysis = analysis or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uncertainty_category": self.uncertainty_category.value,
            "uncertainty_level": self.uncertainty_level,
            "confidence": self.confidence,
            "budget_used": self.budget_used,
            "allowed": self.allowed,
            "analysis": self.analysis,
        }
    
    def __repr__(self) -> str:
        return f"UncertaintyResult({self.uncertainty_category.value}, confidence={self.confidence:.2f}, allowed={self.allowed})"


class UncertaintyDiscipline:
    """Enforces uncertainty discipline for requests.
    
    Monitors:
    - Request uncertainty level
    - Evidence quality
    - Provider capability
    - Context gaps
    
    Enforces:
    - Uncertainty budgets
    - Confidence thresholds
    - Rejection policies
    - Fallback strategies
    """
    
    def __init__(self):
        # Budgets by difficulty level
        # For BASIC requests, allow more uncertainty since evidence can be gathered easily
        self._budgets = {
            "basic": UncertaintyBudget(
                max_uncertainty=0.35,  # More lenient for basic requests
                min_confidence=0.7,
                fallback_policy="cached",
            ),
            "medium": UncertaintyBudget(
                max_uncertainty=0.35,
                min_confidence=0.7,
                fallback_policy="fallback",
            ),
            "high": UncertaintyBudget(
                max_uncertainty=0.45,
                min_confidence=0.6,
                fallback_policy="fallback",
            ),
            "extreme": UncertaintyBudget(
                max_uncertainty=0.55,
                min_confidence=0.5,
                fallback_policy="fallback",
            ),
        }
    
    def analyze(self, request_text: str, context: Dict[str, Any] = None) -> UncertaintyResult:
        """Analyze uncertainty for a request.
        
        Args:
            request_text: The request to analyze
            context: Additional context (optional)
            
        Returns:
            UncertaintyResult with analysis and enforcement decision
        """
        context = context or {}
        
        # Determine difficulty (for budget selection)
        difficulty = self._estimate_difficulty(request_text, context)
        budget = self._budgets.get(difficulty, self._budgets["medium"])
        
        # Analyze uncertainty sources
        knowledge_uncertainty = self._analyze_knowledge_uncertainty(request_text, context)
        evidence_uncertainty = self._analyze_evidence_uncertainty(request_text, context)
        provider_uncertainty = self._analyze_provider_uncertainty(request_text, context)
        
        # Calculate total uncertainty
        uncertainty_level = (
            knowledge_uncertainty * 0.4 +
            evidence_uncertainty * 0.3 +
            provider_uncertainty * 0.3
        )
        
        # Determine category
        if uncertainty_level < 0.2:
            category = UncertaintyCategory.KNOWN
        elif uncertainty_level < 0.4:
            category = UncertaintyCategory.UNKNOWN
        elif uncertainty_level < 0.6:
            category = UncertaintyCategory.UNVERIFIABLE
        else:
            category = UncertaintyCategory.SPECULATIVE
        
        # Calculate budget used
        category_tolerance = budget.uncertainty_tolerance.get(category, 0.3)
        budget_used = uncertainty_level / (category_tolerance + budget.max_uncertainty)
        budget_used = min(1.0, budget_used)
        
        # Calculate confidence (inverse of uncertainty)
        confidence = max(0.0, min(1.0, 1.0 - uncertainty_level))
        
        # Check if allowed
        allowed = budget.allows_response(confidence, budget_used)
        
        # Build analysis
        analysis = {
            "difficulty": difficulty,
            "uncertainty_sources": {
                "knowledge": knowledge_uncertainty,
                "evidence": evidence_uncertainty,
                "provider": provider_uncertainty,
            },
            "category": category.value,
            "category_tolerance": category_tolerance,
        }
        
        return UncertaintyResult(
            uncertainty_category=category,
            uncertainty_level=uncertainty_level,
            confidence=confidence,
            budget_used=budget_used,
            allowed=allowed,
            analysis=analysis,
        )
    
    def _estimate_difficulty(self, request_text: str, context: Dict[str, Any]) -> str:
        """Estimate request difficulty for budget selection."""
        text_lower = request_text.lower()
        
        # Simple keyword-based estimation
        if any(kw in text_lower for kw in ["weather", "time", "now", "calculate"]):
            return "basic"
        elif any(kw in text_lower for kw in ["analyze", "compare", "reason"]):
            return "medium"
        elif any(kw in text_lower for kw in ["research", "explain why", "philosophy"]):
            return "high"
        else:
            return "medium"
    
    def _analyze_knowledge_uncertainty(self, request_text: str, context: Dict[str, Any]) -> float:
        """Analyze uncertainty from knowledge gaps."""
        text_lower = request_text.lower()
        
        # Check for speculative language
        if any(kw in text_lower for kw in ["imagine", "create", "design", "speculate"]):
            return 0.6
        
        if any(kw in text_lower for kw in ["believe", "opinion", "should", "must"]):
            return 0.5
        
        # Check for factual queries
        if any(kw in text_lower for kw in ["what is", "who is", "define"]):
            return 0.2
        
        # Check for context availability
        if context:
            return 0.1
        else:
            return 0.3
    
    def _analyze_evidence_uncertainty(self, request_text: str, context: Dict[str, Any]) -> float:
        """Analyze uncertainty from evidence gaps."""
        text_lower = request_text.lower()
        
        # Check for evidence needs
        if any(kw in text_lower for kw in ["weather", "temperature", "forecast"]):
            return 0.2
        
        if any(kw in text_lower for kw in ["research", "find", "search", "internet"]):
            return 0.3
        
        # Evidence available in context
        if context and "active_thread" in context:
            return 0.1
        
        return 0.2
    
    def _analyze_provider_uncertainty(self, request_text: str, context: Dict[str, Any]) -> float:
        """Analyze uncertainty from provider limitations."""
        text_lower = request_text.lower()
        
        # Check for specialized needs
        if any(kw in text_lower for kw in ["code", "programming", "syntax"]):
            return 0.3
        
        if any(kw in text_lower for kw in ["math", "calculate", "compute"]):
            return 0.2
        
        if any(kw in text_lower for kw in ["analysis", "interpret", "reason"]):
            return 0.2
        
        return 0.1
    
    def get_budget(self, difficulty: str) -> UncertaintyBudget:
        """Get uncertainty budget for difficulty level."""
        return self._budgets.get(difficulty, self._budgets["medium"])
    
    def enforce(self, result: UncertaintyResult, budget: UncertaintyBudget = None) -> bool:
        """Enforce uncertainty discipline on a result."""
        if budget is None:
            budget = self._budgets.get("medium")
        
        return budget.allows_response(result.confidence, result.budget_used)
    
    def get_fallback_policy(self, uncertainty_result: UncertaintyResult) -> str:
        """Get appropriate fallback policy based on uncertainty."""
        if uncertainty_result.uncertainty_category == UncertaintyCategory.SPECULATIVE:
            return "reject"
        elif uncertainty_result.uncertainty_category == UncertaintyCategory.UNVERIFIABLE:
            return "none"
        elif uncertainty_result.confidence < 0.7:
            return "cached"
        else:
            return "fallback"
