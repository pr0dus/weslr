"""Request Intelligence Core Layer

This module provides medium/high intelligence for request processing:
- Request classification beyond keyword-only routing
- Knowledge-state awareness (what's known vs unknown)
- Evidence policy and requirements
- Capability and provider matching
- Uncertainty discipline and enforcement
- Task difficulty grading

Architecture:
  RequestIntelligence — orchestrator that coordinates all subcomponents
  RequestClassifier — classifies request into structured taxonomy
  KnowledgeState — tracks known/unknown/unverifiable/speculative
  EvidencePolicy — defines evidentiary requirements per request type
  CapabilityMatcher — matches request to available capabilities
  ProviderSuitability — scores providers for fit
  UncertaintyDiscipline — enforces uncertainty budgets
  TaskDifficulty — grades request difficulty (BASIC/MEDIUM/HIGH/EXTREME)

Runtime Flow:
  request → RequestIntelligence.analyze() → intelligence_report
  intelligence_report → routing decision → execution

This is additive to existing llm_runtime.py routing.
"""

from .core import RequestIntelligence
from .classifier import RequestClassifier
from .knowledge import KnowledgeState
from .evidence_policy import EvidencePolicy, EvidenceRequirement, EvidencePolicyBuilder
from .capability_matcher import CapabilityMatcher
from .provider_suitability import ProviderSuitability, ProviderScore
from .uncertainty import UncertaintyDiscipline, UncertaintyBudget
from .difficulty import TaskDifficulty, DifficultyGrade

__all__ = [
    "RequestIntelligence",
    "RequestClassifier",
    "KnowledgeState",
    "EvidencePolicy",
    "EvidenceRequirement",
    "EvidencePolicyBuilder",
    "CapabilityMatcher",
    "ProviderSuitability",
    "ProviderScore",
    "UncertaintyDiscipline",
    "UncertaintyBudget",
    "TaskDifficulty",
    "DifficultyGrade",
]
