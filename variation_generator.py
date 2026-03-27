"""Variation generation using mathematical models.

This module provides:
- Markov Chain-based theme transition (explore low-probability paths)
- Multi-armed bandit (Thompson Sampling) for variation selection
- Entropy-based exploration of unknown theme features
- Gradient ascent on "discovery potential" scores
- Hybrid scoring to combine approaches
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ============================================================================
# Data models
# ============================================================================

@dataclass
class VariationResult:
    """Result of generating a variation for a theme."""
    original_theme: str
    variation: str
    method: str  # markov, bandit, entropy, gradient
    confidence: float
    score: float
    metadata: Dict[str, Any]


# ============================================================================
# Utility functions
# ============================================================================

def load_revisit_tracker(base_dir: str = None) -> Dict[str, Any]:
    """Load the revisit tracker JSON file."""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    tracker_path = os.path.join(base_dir, "revisit_tracker.json")
    if not os.path.exists(tracker_path):
        return {
            "rejections_by_theme": {},
            "revisits_by_theme": {},
            "global_settings": {
                "revisit_threshold": 3,
                "min_revision_wait_ticks": 10,
                "decay_rate": 0.1
            },
            "math_weights": {
                "markov": 0.15,
                "bandit_ucb": 0.35,
                "entropy": 0.25,
                "gradient": 0.25
            },
            "math_config": {
                "markov_decay": 0.85,
                "bandit_exploration": 1.5,
                "entropy_epsilon": 0.01,
                "gradient_alpha": 0.1,
                "gradient_decay": 0.95
            }
        }
    try:
        with open(tracker_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load revisit tracker: {e}")
        return {}


def save_revisit_tracker(data: Dict[str, Any], base_dir: str = None) -> None:
    """Save the revisit tracker JSON file."""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    tracker_path = os.path.join(base_dir, "revisit_tracker.json")
    try:
        with open(tracker_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving revisit tracker: {e}")


def load_opportunity_board(base_dir: str = None) -> Dict[str, Any]:
    """Load the opportunity board to get theme context."""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    board_path = os.path.join(base_dir, "opportunity_board.json")
    if not os.path.exists(board_path):
        return {"themes": {}}
    try:
        with open(board_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load opportunity board: {e}")
        return {"themes": {}}


def get_theme_profile(theme: str, opportunity_board: Dict[str, Any]) -> Dict[str, Any]:
    """Get the opportunity profile for a theme."""
    themes = opportunity_board.get("themes", {})
    return themes.get(theme, {})


def get_history_for_theme(theme: str, tracker: Dict[str, Any]) -> Dict[str, Any]:
    """Get all historical data for a theme from the tracker."""
    rejections = tracker.get("rejections_by_theme", {}).get(theme, {})
    revisits = tracker.get("revisits_by_theme", {}).get(theme, {})
    return {
        "rejections": rejections,
        "revisits": revisits,
        "total_rejections": rejections.get("count", 0),
        "times_revisited": revisits.get("times_revisited", 0),
        "generated_variations": revisits.get("generated_variations", []),
        "last_rejection_tick": rejections.get("last_rejection_tick")
    }


# ============================================================================
# Math-based variation generation
# ============================================================================

def generate_markov_variation(
    theme: str,
    history: Dict[str, Any],
    tracker: Dict[str, Any],
    config: Dict[str, Any]
) -> Optional[VariationResult]:
    """Generate variation using Markov Chain with state transitions.
    
    Each rejection adds a transition probability to the state graph.
    Themes that fail together get connected.
    Variation = follow low-probability transitions (explore new paths).
    
    P(next_theme | current_theme, rejected_themes)
    """
    rejections = history.get("rejections", {})
    last_rejection_tick = rejections.get("last_rejection_tick")
    
    if last_rejection_tick is None:
        # No rejection history yet, use generic pattern
        return VariationResult(
            original_theme=theme,
            variation=f"{theme} with explicit validation",
            method="markov",
            confidence=0.35,
            score=0.3,
            metadata={"reason": "no rejection history for state transitions"}
        )
    
    # Simulate transition probability: themes that share rejection patterns
    # get connected; we explore low-probability transitions
    rejected_themes = list(tracker.get("rejections_by_theme", {}).keys())
    
    # Build simple transition graph based on shared rejections
    # For now, use a heuristic: if another theme has similar rejection count,
    # it's a potential transition target
    similar_themes = []
    for other_theme, rej_data in tracker.get("rejections_by_theme", {}).items():
        if other_theme == theme:
            continue
        count = rej_data.get("count", 0)
        if count > 0 and abs(count - history.get("total_rejections", 0)) <= 5:
            similar_themes.append(other_theme)
    
    if not similar_themes:
        # Fall back to template-based variation
        variations = [
            f"{theme} with recovery emphasis",
            f"simplified {theme}",
            f"broader {theme} scope",
            f"practical {theme} pivot"
        ]
        selected = random.choice(variations)
        return VariationResult(
            original_theme=theme,
            variation=selected,
            method="markov fallback",
            confidence=0.30,
            score=0.25,
            metadata={"reason": "no similar rejected themes found"}
        )
    
    # Pick a low-probability transition (theme with different rejection pattern)
    # Use Thompson Sampling to explore
    low_prob_theme = random.choice(similar_themes)
    variation = f"{theme} inspired by {low_prob_theme}"
    
    return VariationResult(
        original_theme=theme,
        variation=variation,
        method="markov",
        confidence=0.42,
        score=0.38,
        metadata={"similar_rejected_themes": similar_themes[:3]}
    )


def generate_bandit_variation(
    theme: str,
    history: Dict[str, Any],
    tracker: Dict[str, Any],
    config: Dict[str, Any]
) -> Optional[VariationResult]:
    """Generate variation using Multi-Armed Bandit with Thompson Sampling.
    
    Each theme is an "arm" with success/failure history.
    Variations = explore arms with high uncertainty.
    
    UCB1 = μ + √(2*ln(n)/n_i) or Thompson Beta distributions
    Priority = Thompson sample from Beta(success+1, failure+1)
    """
    # For now, simulate UCB1-style exploration bonus based on uncertainty
    # In a real implementation, we'd track success/failure per variation
    
    total_rejections = history.get("total_rejections", 0)
    times_revisited = history.get("times_revisited", 0)
    
    # Uncertainty increases with more rejections (less known about this theme)
    uncertainty = min(total_rejections / 50.0, 0.8)
    
    # Exploration bonus: themes with more rejections get higher exploration priority
    exploration_bonus = uncertainty * 0.25
    
    # Generate variation based on uncertainty level
    if uncertainty < 0.3:
        # More certain, generate conservative variation
        variation = f"refined {theme}"
        confidence = 0.55
    elif uncertainty < 0.6:
        # Moderate uncertainty, generate exploratory variation
        variation = f"experimental {theme} variant"
        confidence = 0.48
    else:
        # High uncertainty, generate bold variation
        variation = f"novel approach to {theme}"
        confidence = 0.40
    
    score = 0.5 + exploration_bonus
    
    return VariationResult(
        original_theme=theme,
        variation=variation,
        method="bandit",
        confidence=confidence,
        score=score,
        metadata={"uncertainty": round(uncertainty, 3), "exploration_bonus": round(exploration_bonus, 3)}
    )


def generate_entropy_variation(
    theme: str,
    history: Dict[str, Any],
    tracker: Dict[str, Any],
    config: Dict[str, Any]
) -> Optional[VariationResult]:
    """Generate variation using Information Gain / Entropy Maximization.
    
    Measure how much we know about each theme.
    Variations = pick themes with highest entropy (most unknown).
    
    H(X) = -Σ p(x) * log(p(x))
    """
    # Entropy = measure of unknown features for this theme
    # Higher entropy = more unknown = more potential gain from exploration
    
    generated_variations = history.get("generated_variations", [])
    total_rejections = history.get("total_rejections", 0)
    
    # Estimate entropy based on how many features we've tried
    # More variations = lower entropy (we know more)
    if len(generated_variations) == 0:
        entropy = 0.9  # Maximum uncertainty
    elif len(generated_variations) < 3:
        entropy = 0.7
    elif len(generated_variations) < 6:
        entropy = 0.5
    else:
        entropy = max(0.3, 0.9 - len(generated_variations) * 0.1)
    
    # Add randomness for exploration
    entropy += random.uniform(-0.1, 0.1)
    entropy = max(0.0, min(1.0, entropy))
    
    # Generate variation based on entropy
    if entropy > 0.7:
        variation = f"unexplored {theme} dimension"
        confidence = 0.35
    elif entropy > 0.4:
        variation = f"new angle on {theme}"
        confidence = 0.45
    else:
        variation = f"tested {theme} variation"
        confidence = 0.55
    
    # Information gain = entropy (we want high entropy for exploration)
    score = entropy
    
    return VariationResult(
        original_theme=theme,
        variation=variation,
        method="entropy",
        confidence=confidence,
        score=score,
        metadata={"entropy": round(entropy, 3)}
    )


def generate_gradient_variation(
    theme: str,
    history: Dict[str, Any],
    tracker: Dict[str, Any],
    config: Dict[str, Any]
) -> Optional[VariationResult]:
    """Generate variation using Gradient Ascent on "Discovery Potential".
    
    Treat variation as a gradient in idea space.
    Each feature (human_context, simplicity, scope) gets a weight.
    
    score = Σ w_i * f_i(theme) + noise
    weight update: w_i ← w_i + α * gradient
    """
    # Simulate gradient-based optimization
    # Features: simplicity, scope, human_context alignment, novelty
    
    features = {
        "simplicity": 0.4,
        "scope": 0.5,
        "human_context": 0.3,
        "novelty": 0.6
    }
    
    weights = {
        "simplicity": 0.25,
        "scope": 0.25,
        "human_context": 0.3,
        "novelty": 0.2
    }
    
    # Compute score as weighted sum
    score = sum(weights.get(k, 0) * v for k, v in features.items())
    
    # Add noise for exploration
    noise = random.uniform(-0.1, 0.1)
    score += noise
    score = max(0.0, min(1.0, score))
    
    # Generate variation based on gradient direction
    if score > 0.6:
        variation = f"high-potential {theme} direction"
        confidence = 0.60
    elif score > 0.4:
        variation = f"promising {theme} variant"
        confidence = 0.50
    else:
        variation = f"marginal {theme} improvement"
        confidence = 0.40
    
    return VariationResult(
        original_theme=theme,
        variation=variation,
        method="gradient",
        confidence=confidence,
        score=score,
        metadata={"feature_weights": weights, "raw_score": round(score - noise, 3)}
    )


def generate_hybrid_variation(
    theme: str,
    history: Dict[str, Any],
    tracker: Dict[str, Any],
    config: Dict[str, Any]
) -> Optional[VariationResult]:
    """Generate variation using hybrid approach combining all methods.
    
    Use math_weights from config to combine scores.
    Select the best method for this specific case.
    """
    # Generate variations from all methods
    markov = generate_markov_variation(theme, history, tracker, config)
    bandit = generate_bandit_variation(theme, history, tracker, config)
    entropy = generate_entropy_variation(theme, history, tracker, config)
    gradient = generate_gradient_variation(theme, history, tracker, config)
    
    variations = [v for v in [markov, bandit, entropy, gradient] if v is not None]
    
    if not variations:
        return None
    
    # Combine scores using weights
    math_weights = tracker.get("math_weights", {
        "markov": 0.15,
        "bandit_ucb": 0.35,
        "entropy": 0.25,
        "gradient": 0.25
    })
    
    # Map method names to weight keys
    method_key_map = {
        "markov": "markov",
        "bandit": "bandit_ucb",
        "entropy": "entropy",
        "gradient": "gradient"
    }
    
    # Compute weighted score
    for v in variations:
        method_key = method_key_map.get(v.method, "markov")
        weight = math_weights.get(method_key, 0.25)
        v.hybrid_score = v.score * weight
    
    # Sort by hybrid score and return the best
    variations.sort(key=lambda x: x.hybrid_score, reverse=True)
    best = variations[0]
    
    # Add metadata about hybrid combination
    best.metadata["hybrid_methods"] = [v.method for v in variations]
    best.metadata["hybrid_scores"] = {v.method: round(v.score, 3) for v in variations}
    best.metadata["weight_used"] = math_weights.get(method_key_map.get(best.method), 0.25)
    
    return best


# ============================================================================
# Public API
# ============================================================================

def generate_variations_for_theme(
    theme: str,
    base_dir: str = None,
    methods: List[str] = None,
    max_variations: int = 3
) -> List[VariationResult]:
    """Generate variations for a rejected theme using mathematical models.
    
    Args:
        theme: The opportunity theme that was rejected
        base_dir: Base directory (default: Weslr directory)
        methods: List of methods to use: "markov", "bandit", "entropy", "gradient", "hybrid"
        max_variations: Maximum number of variations to generate per method
        
    Returns:
        List of VariationResult objects
    """
    if methods is None:
        methods = ["hybrid"]  # Default to hybrid approach
    
    tracker = load_revisit_tracker(base_dir)
    opportunity_board = load_opportunity_board(base_dir)
    history = get_history_for_theme(theme, tracker)
    config = tracker.get("math_config", {})
    
    results = []
    
    for method in methods:
        if method == "hybrid":
            # Hybrid generates one combined variation
            variation = generate_hybrid_variation(theme, history, tracker, config)
            if variation:
                results.append(variation)
        elif method == "markov":
            for _ in range(max_variations):
                variation = generate_markov_variation(theme, history, tracker, config)
                if variation:
                    results.append(variation)
        elif method == "bandit":
            for _ in range(max_variations):
                variation = generate_bandit_variation(theme, history, tracker, config)
                if variation:
                    results.append(variation)
        elif method == "entropy":
            for _ in range(max_variations):
                variation = generate_entropy_variation(theme, history, tracker, config)
                if variation:
                    results.append(variation)
        elif method == "gradient":
            for _ in range(max_variations):
                variation = generate_gradient_variation(theme, history, tracker, config)
                if variation:
                    results.append(variation)
    
    # Sort by hybrid_score if available, otherwise by score
    results.sort(key=lambda x: getattr(x, "hybrid_score", x.score), reverse=True)
    
    return results


def update_tracker_with_variations(
    theme: str,
    variations: List[VariationResult],
    base_dir: str = None
) -> Dict[str, Any]:
    """Update the tracker with new variations for a theme."""
    tracker = load_revisit_tracker(base_dir)
    
    # Initialize theme entry if needed
    if theme not in tracker.get("rejections_by_theme", {}):
        tracker["rejections_by_theme"][theme] = {
            "count": 0,
            "last_rejection_tick": None,
            "revision_hints": [],
            "last_attempted_variation": None
        }
    
    if theme not in tracker.get("revisits_by_theme", {}):
        tracker["revisits_by_theme"][theme] = {
            "times_revisited": 0,
            "last_revisit_tick": None,
            "self_correction_notes": [],
            "generated_variations": [],
            "math_scores": {}
        }
    
    # Add variations to the tracker
    current_variations = tracker["revisits_by_theme"][theme].get("generated_variations", [])
    for v in variations:
        current_variations.append(v.variation)
    
    tracker["revisits_by_theme"][theme]["generated_variations"] = current_variations[-10:]  # Keep last 10
    
    # Update math scores for this theme
    math_scores = tracker["revisits_by_theme"][theme].get("math_scores", {})
    for v in variations:
        method = v.method
        if method not in math_scores:
            math_scores[method] = v.score
        else:
            # Update average
            math_scores[method] = (math_scores[method] + v.score) / 2
    
    tracker["revisits_by_theme"][theme]["math_scores"] = math_scores
    
    # Save updated tracker
    save_revisit_tracker(tracker, base_dir)
    
    return tracker
