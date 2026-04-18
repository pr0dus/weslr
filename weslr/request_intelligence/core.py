"""Request Intelligence Core - Main Orchestrator

This is the main entry point for Request Intelligence.

Orchestrates all subcomponents:
1. RequestClassifier - Classifies request into categories
2. KnowledgeStateAnalyzer - Tracks known/unknown state
3. EvidencePolicyBuilder - Builds evidence requirements
4. CapabilityMatcher - Matches to capabilities
5. ProviderSuitabilityScorer - Scores providers
6. UncertaintyDiscipline - Enforces uncertainty budgets
7. TaskDifficultyGrader - Grades request difficulty

Produces a comprehensive Intelligence Report with:
- Classification
- Knowledge state
- Evidence policy
- Capability matches
- Provider scores
- Uncertainty analysis
- Difficulty grade

Used by:
- llm_runtime.py for intelligent routing
- RequestIntelligenceTest for validation
- Future provider selection logic
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class IntelligenceReport:
    """Comprehensive intelligence report for a request.
    
    Contains all intelligence analysis results.
    """
    
    def __init__(
        self,
        request_text: str,
        classification: Dict[str, Any],
        knowledge_state: Dict[str, Any],
        evidence_policy: Dict[str, Any],
        capability_matches: List[Dict[str, Any]],
        provider_scores: List[Dict[str, Any]],
        uncertainty_analysis: Dict[str, Any],
        difficulty_grade: Dict[str, Any],
        combined_score: float = 1.0,
    ):
        self.request_text = request_text
        self.classification = classification
        self.knowledge_state = knowledge_state
        self.evidence_policy = evidence_policy
        self.capability_matches = capability_matches
        self.provider_scores = provider_scores
        self.uncertainty_analysis = uncertainty_analysis
        self.difficulty_grade = difficulty_grade
        self.combined_score = combined_score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_text": self.request_text,
            "classification": self.classification,
            "knowledge_state": self.knowledge_state,
            "evidence_policy": self.evidence_policy,
            "capability_matches": self.capability_matches,
            "provider_scores": self.provider_scores,
            "uncertainty_analysis": self.uncertainty_analysis,
            "difficulty_grade": self.difficulty_grade,
            "combined_score": self.combined_score,
        }
    
    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def __repr__(self) -> str:
        return f"IntelligenceReport(difficulty={self.difficulty_grade.get('grade')}, score={self.combined_score:.2f})"


class RequestIntelligence:
    """Main Request Intelligence orchestrator.
    
    Coordinates all subcomponents to produce comprehensive request intelligence.
    
    Usage:
        ri = RequestIntelligence(context)
        report = ri.analyze("What's the weather in Rome?")
        
        # Use report for routing decision
        if report.difficulty_grade["grade"] == "BASIC":
            # Use local evidence provider
        elif report.uncertainty_analysis["allowed"]:
            # Proceed with execution
    """
    
    def __init__(self, context: Dict[str, Any] = None):
        """Initialize Request Intelligence with context."""
        self.context = context or {}
        self._classifiers = {}
        self._knowledge_analyzer = None
        self._evidence_policy = None
        self._capability_matcher = None
        self._provider_suitability = None
        self._uncertainty_discipline = None
        self._difficulty_grader = None
    
    def _get_classifier(self):
        """Lazy-load classifier."""
        if self._classifiers.get("main") is None:
            from .classifier import RequestClassifier
            self._classifiers["main"] = RequestClassifier()
        return self._classifiers["main"]
    
    def _get_knowledge_analyzer(self):
        """Lazy-load knowledge analyzer."""
        if self._knowledge_analyzer is None:
            from .knowledge import KnowledgeStateAnalyzer
            self._knowledge_analyzer = KnowledgeStateAnalyzer()
        return self._knowledge_analyzer
    
    def _get_evidence_policy(self):
        """Lazy-load evidence policy."""
        if self._evidence_policy is None:
            from .evidence_policy import EvidencePolicyBuilder
            self._evidence_policy = EvidencePolicyBuilder()
        return self._evidence_policy
    
    def _get_capability_matcher(self):
        """Lazy-load capability matcher."""
        if self._capability_matcher is None:
            from .capability_matcher import CapabilityMatcher
            self._capability_matcher = CapabilityMatcher()
        return self._capability_matcher
    
    def _get_provider_suitability(self):
        """Lazy-load provider suitability."""
        if self._provider_suitability is None:
            from .provider_suitability import ProviderSuitability
            self._provider_suitability = ProviderSuitability()
        return self._provider_suitability
    
    def _get_uncertainty_discipline(self):
        """Lazy-load uncertainty discipline."""
        if self._uncertainty_discipline is None:
            from .uncertainty import UncertaintyDiscipline
            self._uncertainty_discipline = UncertaintyDiscipline()
        return self._uncertainty_discipline
    
    def _get_difficulty_grader(self):
        """Lazy-load difficulty grader."""
        if self._difficulty_grader is None:
            from .difficulty import TaskDifficulty
            self._difficulty_grader = TaskDifficulty()
        return self._difficulty_grader
    
    def analyze(self, request_text: str) -> IntelligenceReport:
        """Analyze a request comprehensively.
        
        Args:
            request_text: The request to analyze
            
        Returns:
            IntelligenceReport with all analysis results
        """
        # Analyze each dimension
        classification = self._analyze_classification(request_text)
        knowledge_state = self._analyze_knowledge_state(request_text)
        evidence_policy = self._analyze_evidence_policy(request_text, classification)
        capability_matches = self._analyze_capabilities(request_text, classification)
        provider_scores = self._analyze_providers(request_text, classification)
        uncertainty_analysis = self._analyze_uncertainty(request_text, classification)
        difficulty_grade = self._analyze_difficulty(request_text, knowledge_state, classification)
        
        # Combine scores
        combined_score = self._combine_scores(
            classification,
            evidence_policy,
            provider_scores,
            uncertainty_analysis,
            difficulty_grade,
        )
        
        return IntelligenceReport(
            request_text=request_text,
            classification=classification,
            knowledge_state=knowledge_state,
            evidence_policy=evidence_policy,
            capability_matches=capability_matches,
            provider_scores=provider_scores,
            uncertainty_analysis=uncertainty_analysis,
            difficulty_grade=difficulty_grade,
            combined_score=combined_score,
        )
    
    def _analyze_classification(self, request_text: str) -> Dict[str, Any]:
        """Analyze request classification."""
        classifier = self._get_classifier()
        result = classifier.classify(request_text, self.context)
        return result.to_dict()
    
    def _analyze_knowledge_state(self, request_text: str) -> Dict[str, Any]:
        """Analyze knowledge state."""
        analyzer = self._get_knowledge_analyzer()
        result = analyzer.analyze(request_text, self.context)
        return result.to_dict()
    
    def _analyze_evidence_policy(self, request_text: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze evidence policy."""
        builder = self._get_evidence_policy()
        
        # Determine request type from classification
        primary_routing = classification.get("primary_routing", "LOCAL")
        
        if primary_routing == "LOCAL":
            request_type = "time_query" if "time" in request_text.lower() else "factual_query"
        elif primary_routing == "EVIDENCE":
            request_type = "weather_query" if "weather" in request_text.lower() else "factual_query"
        elif primary_routing == "RESEARCH":
            request_type = "research_query"
        else:
            request_type = "factual_query"
        
        policy = builder.build_policy(request_type, difficulty=2)
        return policy.to_dict()
    
    def _analyze_capabilities(self, request_text: str, classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze capability matches."""
        matcher = self._get_capability_matcher()
        matches = matcher.match(request_text, self.context)
        return [m.to_dict() for m in matches]
    
    def _analyze_providers(self, request_text: str, classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze provider suitability."""
        scorer = self._get_provider_suitability()
        scores = scorer.score_all(request_text, self.context)
        return [s.to_dict() for s in scores]
    
    def _analyze_uncertainty(self, request_text: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze uncertainty."""
        discipline = self._get_uncertainty_discipline()
        result = discipline.analyze(request_text, self.context)
        return result.to_dict()
    
    def _analyze_difficulty(self, request_text: str, knowledge_state: Dict[str, Any], classification: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task difficulty."""
        grader = self._get_difficulty_grader()
        result = grader.grade(request_text, self.context)
        return result
    
    def _combine_scores(
        self,
        classification: Dict[str, Any],
        evidence_policy: Dict[str, Any],
        provider_scores: List[Dict[str, Any]],
        uncertainty_analysis: Dict[str, Any],
        difficulty_grade: Dict[str, Any],
    ) -> float:
        """Combine all scores into a single confidence score."""
        # Base score from classification confidence
        classification_confidence = classification.get("confidence", 0.7)
        
        # Base score from provider scores (take best provider)
        best_provider_score = 0.0
        if provider_scores:
            best_provider_score = max(s.get("score", 0) for s in provider_scores)
        
        # Base score from uncertainty analysis
        uncertainty_confidence = uncertainty_analysis.get("confidence", 0.7)
        uncertainty_allowed = uncertainty_analysis.get("allowed", True)
        uncertainty_penalty = 0.0 if uncertainty_allowed else 0.3
        
        # Combine
        combined = (
            classification_confidence * 0.2 +
            best_provider_score * 0.3 +
            uncertainty_confidence * 0.3 +
            (0.2 if difficulty_grade.get("confidence", 0.7) > 0.6 else 0.1)
        )
        
        # Apply penalty
        combined = max(0.0, combined - uncertainty_penalty)
        
        return round(min(1.0, combined), 3)
    
    def get_best_provider(self, request_text: str) -> str:
        """Get the best provider name for a request."""
        report = self.analyze(request_text)
        if report.provider_scores:
            return report.provider_scores[0].get("provider_name", "embedded")
        return "embedded"
    
    def get_routing_decision(self, request_text: str) -> Tuple[str, Dict[str, Any]]:
        """Get routing decision based on analysis.
        
        Returns:
            (category, details) where category is:
            - "LOCAL": Use local evidence (time/weather APIs via evidence_api)
            - "EVIDENCE": Use evidence provider
            - "REASONING": Use reasoning provider (embedded LLM)
            - "REJECT": Request cannot be handled
        """
        report = self.analyze(request_text)
        
        uncertainty_allowed = report.uncertainty_analysis.get("allowed", False)
        
        if not uncertainty_allowed:
            return ("REJECT", {"reason": "uncertainty_exceeded", "analysis": report.uncertainty_analysis})
        
        difficulty = report.difficulty_grade.get("grade", "MEDIUM")
        primary_routing = report.classification.get("primary_routing", "LOCAL")
        
        if difficulty == "BASIC":
            # BASIC requests should go to evidence API (time/weather) or embedded reasoning
            if primary_routing in ("LOCAL", "EVIDENCE"):
                return ("LOCAL", {"difficulty": difficulty, "confidence": report.combined_score, "provider": "evidence_api"})
            else:
                return ("REASONING", {"difficulty": difficulty, "confidence": report.combined_score, "provider": "embedded"})
        elif primary_routing == "LOCAL":
            return ("EVIDENCE", {"difficulty": difficulty, "confidence": report.combined_score})
        else:
            return ("REASONING", {"difficulty": difficulty, "confidence": report.combined_score})
