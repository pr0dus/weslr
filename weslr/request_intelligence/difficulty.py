"""Task Difficulty Grading

Defines the Difficulty ladder and grades requests accordingly.

BASIC:
  - Single-turn, deterministic
  - Can be handled by 0.5B model
  - Local evidence available (time, weather, cached facts)
  - No external web research needed

MEDIUM:
  - Multi-step reasoning (2-3 steps)
  - Requires context synthesis
  - May need limited external facts (with fallback)
  - Can use bounded embedded reasoning with evidence

HIGH:
  - Complex multi-step reasoning (4+ steps)
  - Requires external research
  - Multiple evidence sources needed
  - Uncertainty handling required
  - Provider suitability matters significantly

EXTREME:
  - Unbounded or open-ended tasks
  - Requires significant external facts
  - No local evidence source exists
  - High uncertainty or speculative
  - May need human judgment input

Difficulty grading rules:
  - Start with keyword-based detection (simple patterns)
  - Refine with complexity scoring (sentence complexity, subtasks)
  - Apply difficulty floor/ceiling based on request type
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, Optional


class DifficultyGrade(Enum):
    """Difficulty levels for requests."""
    BASIC = "BASIC"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class TaskDifficulty:
    """Grades requests on difficulty scale (BASIC/MEDIUM/HIGH/EXTREME).
    
    Uses multiple signals:
    - Keyword patterns (simple indicators)
    - Complexity features (sentence count, token count)
    - Evidence requirements (what's needed)
    - Task structure (single-step vs multi-step)
    
    Returns DifficultyGrade and detailed analysis.
    """
    
    # BASIC keywords - simple, local, deterministic
    BASIC_KEYWORDS = {
        "weather", "temperature", "time", "date", "now", "currently",
        "define", "what is", "who is", "how to", "calculate",
        "add", "subtract", "multiply", "divide",
        "current", "today", "yesterday", "tomorrow",
    }
    
    # EXTREME keywords - open-ended, speculative, no local evidence
    EXTREME_KEYWORDS = {
        "believe", "think", "opinion", "should", "must",
        "explain why", "reason about", "philosophy", "meaning",
        "create", "invent", "design", "imagine",
        "universe", "existence", "consciousness", "life",
        "future", "prediction", "prophecy", "destiny",
        "spiritual", "metaphysical", "transcendental",
    }
    
    # MEDIUM keywords - require some reasoning or context
    MEDIUM_KEYWORDS = {
        "compare", "contrast", "difference", "similar",
        "analyze", "interpret", "explain", "reason",
        "history", "background", "context", "overview",
        "process", "steps", "sequence", "how does",
        "impact", "effect", "influence", "relationship",
    }
    
    def __init__(self):
        # Pattern for multi-step task detection
        self.multi_step_pattern = re.compile(
            r"(first|then|next|after|step|phase|stage|阶段|步骤|first.*then|next.*after)",
            re.IGNORECASE
        )
        # Pattern for complex question detection
        self.complex_question_pattern = re.compile(
            r"(how.*why|why.*how|explain.*reason|detailed.*analysis)",
            re.IGNORECASE
        )
    
    def grade(self, request_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Grade the request difficulty.
        
        Args:
            request_text: The request to grade
            context: Additional context (optional)
            
        Returns:
            Dict with:
            - grade: DifficultyGrade enum
            - confidence: 0.0-1.0 confidence score
            - analysis: Detailed analysis reasons
            - difficulty_score: 0-10 numeric score
        """
        text_lower = request_text.lower().strip()
        context = context or {}
        
        analysis = {
            "keywords_found": [],
            "complexity_signals": [],
            "reasoning": [],
        }
        
        # Score components
        keyword_score = 0.0
        complexity_score = 0.0
        evidence_score = 0.0
        
        # Check for basic keywords first - these override other scoring
        if any(kw in text_lower for kw in ["time", "now", "currently", "date"]):
            # Time query - very basic
            keyword_score = 1.0
            analysis["keywords_found"].append("basic:time_query")
            analysis["reasoning"].append("Time query - high confidence BASIC")
            return {
                "grade": DifficultyGrade.BASIC,
                "confidence": 0.95,
                "difficulty_score": 0.5,
                "analysis": analysis,
            }
        
        if any(kw in text_lower for kw in ["calculate", "compute", "math", "add", "subtract", "multiply", "divide"]):
            # Calculation query - basic
            keyword_score = 0.8
            analysis["keywords_found"].append("basic:calculation")
            analysis["reasoning"].append("Calculation query - high confidence BASIC")
            return {
                "grade": DifficultyGrade.BASIC,
                "confidence": 0.9,
                "difficulty_score": 1.0,
                "analysis": analysis,
            }
        
        if any(kw in text_lower for kw in ["weather", "temperature", "temp"]):
            # Weather query - basic
            keyword_score = 0.9
            analysis["keywords_found"].append("basic:weather")
            analysis["reasoning"].append("Weather query - high confidence BASIC")
            return {
                "grade": DifficultyGrade.BASIC,
                "confidence": 0.9,
                "difficulty_score": 1.0,
                "analysis": analysis,
            }
        
        # Check BASIC keywords
        for kw in self.BASIC_KEYWORDS:
            if kw in text_lower:
                keyword_score += 0.3
                analysis["keywords_found"].append(f"basic:{kw}")
                analysis["reasoning"].append(f"Contains basic keyword '{kw}'")
        
        # Check EXTREME keywords
        for kw in self.EXTREME_KEYWORDS:
            if kw in text_lower:
                keyword_score -= 0.4  # Moves toward higher difficulty
                analysis["keywords_found"].append(f"extreme:{kw}")
                analysis["reasoning"].append(f"Contains extreme keyword '{kw}'")
        
        # Check complexity signals
        if self.multi_step_pattern.search(text_lower):
            complexity_score += 0.4
            analysis["complexity_signals"].append("multi-step")
            analysis["reasoning"].append("Contains multi-step indicators")
        
        if self.complex_question_pattern.search(text_lower):
            complexity_score += 0.3
            analysis["complexity_signals"].append("complex-question")
            analysis["reasoning"].append("Contains complex question pattern")
        
        # Text length analysis (longer = potentially more complex)
        text_length = len(text_lower.split())
        if text_length > 20:
            complexity_score += 0.2
            analysis["complexity_signals"].append("long-text")
            analysis["reasoning"].append("Long text (high token count)")
        
        # Evidence requirements from context
        if context.get("requires_evidence"):
            evidence_score += 0.3
            analysis["reasoning"].append("Requires external evidence")
        
        # Calculate composite difficulty score
        difficulty_score = max(0, min(10, keyword_score * 10 + complexity_score * 10 + evidence_score * 5))
        
        # Determine grade
        if difficulty_score < 3:
            grade = DifficultyGrade.BASIC
            confidence = 0.85
        elif difficulty_score < 5:
            grade = DifficultyGrade.MEDIUM
            confidence = 0.75
        elif difficulty_score < 8:
            grade = DifficultyGrade.HIGH
            confidence = 0.65
        else:
            grade = DifficultyGrade.EXTREME
            confidence = 0.6
        
        return {
            "grade": grade,
            "confidence": confidence,
            "difficulty_score": round(difficulty_score, 2),
            "analysis": analysis,
        }
    
    def grade_simple(self, request_text: str, context: Dict[str, Any] = None) -> DifficultyGrade:
        """Simple grade - just return the enum.
        
        Faster version for high-throughput routing.
        """
        result = self.grade(request_text, context)
        return result["grade"]
    
    def is_bounded(self, grade: DifficultyGrade) -> bool:
        """Check if grade is bounded (can be handled locally)."""
        return grade in (DifficultyGrade.BASIC, DifficultyGrade.MEDIUM)
    
    def requires_external_evidence(self, grade: DifficultyGrade) -> bool:
        """Check if grade likely needs external evidence."""
        return grade in (DifficultyGrade.HIGH, DifficultyGrade.EXTREME)
    
    def requires_uncertainty_handling(self, grade: DifficultyGrade) -> bool:
        """Check if grade needs uncertainty discipline."""
        return grade in (DifficultyGrade.HIGH, DifficultyGrade.EXTREME)
