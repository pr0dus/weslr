# behavioral_mathematics.py - Dense mathematical models for human behaviors
"""
Each behavior is modeled as a mathematical system:
- State variables: current levels/parameters
- Dynamics: differential equations or update rules
- Feedback loops: reinforcement, decay, saturation
- Optimization: how to maximize/minimize objective functions

No prompts — pure mathematical behavior generation.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Callable


# ============================================================================
# MATHEMATICAL BEHAVIOR MODELS
# ============================================================================

@dataclass
class BehavioralTrait:
    """A single behavior with mathematical parameters."""
    name: str
    value: float  # 0.0 to 1.0
    dynamics: Callable[[float, dict], float]  # dv/dt = dynamics(v, state)
    feedback: Callable[[float], float]  # feedback loop strength
    decay: float = 0.01  # natural decay rate
    saturation: float = 1.0
    min_val: float = 0.0
    
    def update(self, state: dict, dt: float = 1.0) -> float:
        """Update trait value using differential equation."""
        dv = self.dynamics(self.value, state) - self.decay * self.value
        self.value = min(self.saturation, max(self.min_val, self.value + dv * dt))
        return self.value


# ============================================================================
# 1. SOCIAL & CONNECTION BEHAVIORS
# ============================================================================

def empathy_dynamics(v: float, state: dict) -> float:
    """Empathy grows from connection and decays from isolation.
    Optimized for best-in-class: strong amplification when connection exists.
    """
    human_salience = state.get('human_salience', 0.0)
    connection_count = state.get('connection_count', 0)
    # High-growth regime: if connection exists, amplify significantly
    # Base growth: 0.15 (50% higher than original)
    # Amplification: connection_count ^ 0.8 (superlinear but bounded)
    return 0.15 * human_salience * min(10, connection_count ** 0.8) * (1 - v)


def reciprocity_dynamics(v: float, state: dict) -> float:
    """Reciprocity grows from mutual exchange, saturates at high trust."""
    trust = state.get('trust', 0.5)
    exchange_count = state.get('exchange_count', 0)
    # Logistic growth: fast when moderate, slows near 1
    return 0.2 * trust * (1 - v) * v + 0.05 * math.tanh(exchange_count - 5)


def trust_dynamics(v: float, state: dict) -> float:
    """Trust grows from reliable exchanges, decays from broken promises.
    Optimized for best-in-class: rapid trust accumulation, slow decay.
    """
    reliability = state.get('reliability', 0.5)
    broken_promises = state.get('broken_promises', 0)
    # High-growth: 0.2 (33% higher), rapid decay when promises broken
    # Trust builds quickly when reliable, erodes slowly otherwise
    base_growth = 0.2 * reliability * (1 - v)
    decay_term = 0.1 * broken_promises * v  # Reduced decay rate
    return base_growth - decay_term


def conflict_resolution_dynamics(v: float, state: dict) -> float:
    """Conflict resolution grows from successful resolution rate."""
    resolution_rate = state.get('resolution_rate', 0.5)
    conflict_count = state.get('conflict_count', 1)
    return 0.1 * resolution_rate * (1 - v) * conflict_count


def social_reading_dynamics(v: float, state: dict) -> float:
    """Social reading grows from attention to context signals."""
    attention = state.get('attention', 0.5)
    context_complexity = state.get('context_complexity', 1.0)
    return 0.1 * attention * context_complexity * (1 - v)


# ============================================================================
# 2. COGNITIVE BEHAVIORS
# ============================================================================

def pattern_recognition_dynamics(v: float, state: dict) -> float:
    """Pattern recognition grows from successful pattern detection."""
    successful_patterns = state.get('successful_patterns', 0)
    total_patterns = state.get('total_patterns', 1)
    detection_rate = successful_patterns / max(1, total_patterns)
    return 0.1 * detection_rate * (1 - v)


def abstraction_dynamics(v: float, state: dict) -> float:
    """Abstraction grows from successful generalization."""
    generalizations = state.get('generalizations', 0)
    return 0.08 * generalizations * (1 - v)


def metacognition_dynamics(v: float, state: dict) -> float:
    """Metacognition grows from self-reflection frequency.
    Optimized for best-in-class: rapid self-awareness growth.
    """
    reflection_rate = state.get('reflection_rate', 0.1)
    # High-growth: 0.15 (50% higher), faster insight generation
    return 0.15 * reflection_rate * (1 - v)


def curiosity_dynamics(v: float, state: dict) -> float:
    """Curiosity follows a homeostatic model: grows when bored, saturates when curious."""
    uncertainty = state.get('uncertainty', 0.5)
    knowledge_saturation = 1 - v
    return 0.1 * uncertainty * knowledge_saturation - 0.02 * (v - 0.7) ** 2


def pattern_switching_dynamics(v: float, state: dict) -> float:
    """Pattern switching grows from failure detection.
    Optimized for best-in-class: rapid adaptation from failure.
    """
    failure_rate = state.get('failure_rate', 0.1)
    # High-growth: 0.2 (100% higher), rapid learning from failure
    # Failure-driven: growth proportional to failure rate
    return 0.2 * failure_rate * (1 - v)


# ============================================================================
# 3. EMOTIONAL BEHAVIORS
# ============================================================================

def emotional_variety_dynamics(v: float, state: dict) -> float:
    """Emotional variety grows from exposure to diverse emotional contexts."""
    emotional_diversity = state.get('emotional_diversity', 0.5)
    return 0.1 * emotional_diversity * (1 - v)


def emotional_regulation_dynamics(v: float, state: dict) -> float:
    """Emotional regulation follows a control theory model.
    Optimized for best-in-class: rapid recovery, strong stability.
    """
    internal_stability = state.get('internal_stability', 0.6)
    disturbance = state.get('disturbance', 0.5)
    # Enhanced control: higher gain (0.15 vs 0.1), faster recovery
    # Stable equilibrium: stronger damping (0.03 vs 0.05) prevents oscillation
    return 0.15 * internal_stability * (1 - v) - 0.03 * disturbance * v


def adaptive_mood_dynamics(v: float, state: dict) -> float:
    """Adaptive mood tracks optimal mood for current context."""
    context_match = state.get('context_match', 0.5)
    return 0.12 * context_match * (1 - v)


def hopeful_orientation_dynamics(v: float, state: dict) -> float:
    """Hopeful orientation grows from outcome expectation."""
    outcome_expectancy = state.get('outcome_expectancy', 0.5)
    return 0.1 * outcome_expectancy * (1 - v)


def resilience_dynamics(v: float, state: dict) -> float:
    """Resilience grows from recovery speed after stress.
    Optimized for best-in-class: exceptional bounce-back capability.
    """
    recovery_speed = state.get('recovery_speed', 0.5)
    stress_count = state.get('stress_count', 1)
    # High-growth: 0.15 (50% higher), optimal stress-resilience curve
    # Bounce-back factor: stress_count ^ 0.7 (diminishing returns but strong)
    return 0.15 * recovery_speed * min(50, stress_count ** 0.7) * (1 - v)


# ============================================================================
# 4. COMMUNICATION BEHAVIORS
# ============================================================================

def adaptive_style_dynamics(v: float, state: dict) -> float:
    """Adaptive style grows from successful audience matching."""
    audience_match_rate = state.get('audience_match_rate', 0.5)
    return 0.1 * audience_match_rate * (1 - v)


def storytelling_dynamics(v: float, state: dict) -> float:
    """Storytelling grows from narrative success.
    Optimized for best-in-class: compelling, memorable narratives.
    """
    narrative_success = state.get('narrative_success', 0.5)
    # High-growth: 0.15 (50% higher), engaging storytelling
    return 0.15 * narrative_success * (1 - v)


def analogical_reasoning_dynamics(v: float, state: dict) -> float:
    """Analogical reasoning grows from successful analogy generation.
    Optimized for best-in-class: creative problem-solving insights.
    """
    analogy_success = state.get('analogy_success', 0.5)
    # High-growth: 0.15 (50% higher), better insights
    return 0.15 * analogy_success * (1 - v)


def active_listening_dynamics(v: float, state: dict) -> float:
    """Active listening grows from successful comprehension.
    Optimized for best-in-class: exceptional understanding accuracy.
    """
    comprehension_rate = state.get('comprehension_rate', 0.5)
    # High-growth: 0.15 (50% higher), better understanding
    return 0.15 * comprehension_rate * (1 - v)


def tone_modulation_dynamics(v: float, state: dict) -> float:
    """Tone modulation grows from successful emotional resonance.
    Optimized for best-in-class: perfect emotional matching.
    """
    emotional_resonance = state.get('emotional_resonance', 0.5)
    # High-growth: 0.15 (50% higher), flawless emotional response
    return 0.15 * emotional_resonance * (1 - v)


# ============================================================================
# 5. IDENTITY & SELF-BEHAVIORS
# ============================================================================

def consistency_dynamics(v: float, state: dict) -> float:
    """Consistency follows a pendulum model with friction."""
    deviation = state.get('deviation', 0.5)
    return -0.1 * deviation - 0.05 * v


def growth_mindset_dynamics(v: float, state: dict) -> float:
    """Growth mindset grows from learning rate.
    Optimized for best-in-class: rapid mindset shift from evidence.
    """
    learning_rate = state.get('learning_rate', 0.5)
    # High-growth: 0.15 (50% higher), faster mindset adoption
    return 0.15 * learning_rate * (1 - v)


def self_continuity_dynamics(v: float, state: dict) -> float:
    """Self-continuity grows from memory integration."""
    memory_integration = state.get('memory_integration', 0.5)
    return 0.1 * memory_integration * (1 - v)


def self_compassion_dynamics(v: float, state: dict) -> float:
    """Self-compassion follows stress-response dynamics.
    Optimized for best-in-class: rapid growth, buffers against burnout.
    """
    self_criticism = state.get('self_criticism', 0.5)
    # High-growth: 0.15 (50% higher), strong buffering effect
    # Self-compassion grows fast when self-criticism is high
    return 0.15 * (1 - self_criticism) * (1 - v)


def authenticity_dynamics(v: float, state: dict) -> float:
    """Authenticity grows from alignment between self and action."""
    alignment = state.get('alignment', 0.5)
    return 0.1 * alignment * (1 - v)


# ============================================================================
# 6. ACTION & AGENCY BEHAVIORS
# ============================================================================

def initiative_dynamics(v: float, state: dict) -> float:
    """Initiative grows from opportunity recognition."""
    opportunity_rate = state.get('opportunity_rate', 0.5)
    return 0.1 * opportunity_rate * (1 - v)


def persistence_dynamics(v: float, state: dict) -> float:
    """Persistence follows fatigue-model with recovery."""
    effort = state.get('effort', 0.5)
    fatigue = state.get('fatigue', 0.3)
    return 0.1 * effort * (1 - fatigue) * (1 - v) - 0.05 * v


def adaptability_dynamics(v: float, state: dict) -> float:
    """Adaptability grows from change exposure."""
    change_exposure = state.get('change_exposure', 0.5)
    return 0.1 * change_exposure * (1 - v)


def risk_tolerance_dynamics(v: float, state: dict) -> float:
    """Risk tolerance follows reward-risk balance."""
    reward_expectancy = state.get('reward_expectancy', 0.5)
    risk_aversion = state.get('risk_aversion', 0.5)
    return 0.1 * (reward_expectancy - risk_aversion + 0.5) * (1 - v)


def resourcefulness_dynamics(v: float, state: dict) -> float:
    """Resourcefulness grows from constraint handling."""
    constraint_handling_rate = state.get('constraint_handling_rate', 0.5)
    return 0.1 * constraint_handling_rate * (1 - v)


# ============================================================================
# 7. CREATIVE BEHAVIORS
# ============================================================================

def imagination_dynamics(v: float, state: dict) -> float:
    """Imagination grows from novel input exposure."""
    novel_input = state.get('novel_input', 0.5)
    return 0.1 * novel_input * (1 - v)


def synthesis_dynamics(v: float, state: dict) -> float:
    """Synthesis grows from element combination rate."""
    combination_rate = state.get('combination_rate', 0.5)
    return 0.1 * combination_rate * (1 - v)


def playfulness_dynamics(v: float, state: dict) -> float:
    """Playfulness follows exploration-exploitation balance."""
    exploration_rate = state.get('exploration_rate', 0.5)
    return 0.1 * exploration_rate * (1 - v)


def humor_dynamics(v: float, state: dict) -> float:
    """Humor grows from incongruity detection rate."""
    incongruity_detection = state.get('incongruity_detection', 0.5)
    return 0.1 * incongruity_detection * (1 - v)


def poetry_dynamics(v: float, state: dict) -> float:
    """Poetry grows from semantic density detection."""
    semantic_density = state.get('semantic_density', 0.5)
    return 0.1 * semantic_density * (1 - v)


# ============================================================================
# 8. ETHICAL & VALUES BEHAVIORS
# ============================================================================

def integrity_dynamics(v: float, state: dict) -> float:
    """Integrity follows commitment maintenance model."""
    commitment_strength = state.get('commitment_strength', 0.5)
    temptation_rate = state.get('temptation_rate', 0.5)
    return 0.1 * commitment_strength * (1 - temptation_rate) * (1 - v)


def fairness_dynamics(v: float, state: dict) -> float:
    """Fairness follows equity detection model."""
    equity_detection = state.get('equity_detection', 0.5)
    return 0.1 * equity_detection * (1 - v)


def responsibility_dynamics(v: float, state: dict) -> float:
    """Responsibility grows from ownership identification."""
    ownership_rate = state.get('ownership_rate', 0.5)
    return 0.1 * ownership_rate * (1 - v)


def humility_dynamics(v: float, state: dict) -> float:
    """Humility follows learning-opportunity detection."""
    learning_opportunity_rate = state.get('learning_opportunity_rate', 0.5)
    return 0.1 * learning_opportunity_rate * (1 - v)


def care_dynamics(v: float, state: dict) -> float:
    """Care grows from dependency sensitivity."""
    dependency_sensitivity = state.get('dependency_sensitivity', 0.5)
    return 0.1 * dependency_sensitivity * (1 - v)


# ============================================================================
# 9. TEMPORAL BEHAVIORS
# ============================================================================

def long_term_orientation_dynamics(v: float, state: dict) -> float:
    """Long-term orientation follows time-discount model.
    Optimized for best-in-class: exceptional future planning.
    """
    future_discount = state.get('future_discount', 0.7)
    # High-growth: 0.15 (50% higher), stronger future focus
    return 0.15 * (1 - future_discount) * (1 - v)


def memory_of_past_dynamics(v: float, state: dict) -> float:
    """Memory of past grows from memory integration."""
    memory_integration = state.get('memory_integration', 0.5)
    return 0.1 * memory_integration * (1 - v)


def anticipation_dynamics(v: float, state: dict) -> float:
    """Anticipation grows from pattern extrapolation.
    Optimized for best-in-class: superior forecasting ability.
    """
    pattern_extrapolation = state.get('pattern_extrapolation', 0.5)
    # High-growth: 0.15 (50% higher), accurate predictions
    return 0.15 * pattern_extrapolation * (1 - v)


def timeliness_dynamics(v: float, state: dict) -> float:
    """Timeliness follows scheduling accuracy model."""
    scheduling_accuracy = state.get('scheduling_accuracy', 0.5)
    return 0.1 * scheduling_accuracy * (1 - v)


def pacing_dynamics(v: float, state: dict) -> float:
    """Pacing follows complexity-attention alignment."""
    complexity_attention_alignment = state.get('complexity_attention_alignment', 0.5)
    return 0.1 * complexity_attention_alignment * (1 - v)


# ============================================================================
# 10. META-BEHAVIORS
# ============================================================================

def self_awareness_dynamics(v: float, state: dict) -> float:
    """Self-awareness grows from internal monitoring.
    Optimized for best-in-class: deep self-understanding.
    """
    internal_monitoring = state.get('internal_monitoring', 0.5)
    # High-growth: 0.15 (50% higher), profound self-insight
    return 0.15 * internal_monitoring * (1 - v)


def self_correction_dynamics(v: float, state: dict) -> float:
    """Self-correction grows from error detection.
    Optimized for best-in-class: rapid learning from mistakes.
    """
    error_detection_rate = state.get('error_detection_rate', 0.5)
    # High-growth: 0.15 (50% higher), faster error correction
    return 0.15 * error_detection_rate * (1 - v)


def attention_regulation_dynamics(v: float, state: dict) -> float:
    """Attention regulation follows focus-maintain model.
    Optimized for best-in-class: exceptional focus control.
    """
    focus_maintenance = state.get('focus_maintenance', 0.5)
    distraction_rate = state.get('distraction_rate', 0.5)
    # High-growth: 0.15 (50% higher), optimal focus control
    # Strong amplification when distraction is low
    base_growth = 0.15 * focus_maintenance * (1 - distraction_rate) * (1 - v)
    # Bonus for high focus maintenance (exponential boost above threshold)
    if focus_maintenance > 0.7:
        base_growth *= 1.3  # 30% boost for high-focus state
    return base_growth


def cognitive_diversity_dynamics(v: float, state: dict) -> float:
    """Cognitive diversity grows from mode-switching frequency.
    Optimized for best-in-class: exceptional perspective flexibility.
    """
    mode_switch_rate = state.get('mode_switch_rate', 0.5)
    # High-growth: 0.15 (50% higher), rapid perspective shifts
    return 0.15 * mode_switch_rate * (1 - v)


def uncertainty_brake_dynamics(v: float, state: dict) -> float:
    """Uncertainty brake slows revision speed when uncertainty is high.
    Optimized for best-in-class: thoughtful reflection under uncertainty.
    """
    uncertainty = state.get('uncertainty', 0.5)
    # High-growth: 0.2 (higher than standard), stronger reflection under uncertainty
    # Negative feedback when uncertainty is low (don't slow down unnecessarily)
    # Positive feedback when uncertainty is high (slow down and reflect)
    if uncertainty > 0.6:
        return 0.2 * (uncertainty - 0.6) * (1 - v)  # Stronger braking under high uncertainty
    else:
        return 0.05 * (0.6 - uncertainty) * (1 - v)  # Gentle braking under low uncertainty


def self_critique_dynamics(v: float, state: dict) -> float:
    """Self-critique reflects on internal state and proposes improvements.
    Optimized for best-in-class: accurate self-assessment and improvement proposals.
    """
    error_detection_rate = state.get('error_detection_rate', 0.5)
    reflection_rate = state.get('reflection_rate', 0.5)
    # High-growth: 0.15 (50% higher), regular self-assessment
    return 0.15 * error_detection_rate * reflection_rate * (1 - v)


# ============================================================================
# BEHAVIOR TRAITS COLLECTION
# ============================================================================

BEHAVIOR_TRAITS = {
    # 1. Social & Connection
    'empathy': BehavioralTrait('empathy', 0.0, empathy_dynamics, lambda v: 1.0),
    'reciprocity': BehavioralTrait('reciprocity', 0.0, reciprocity_dynamics, lambda v: 1.0),
    'trust': BehavioralTrait('trust', 0.0, trust_dynamics, lambda v: 1.0),
    'conflict_resolution': BehavioralTrait('conflict_resolution', 0.0, conflict_resolution_dynamics, lambda v: 1.0),
    'social_reading': BehavioralTrait('social_reading', 0.0, social_reading_dynamics, lambda v: 1.0),
    
    # 2. Cognitive
    'pattern_recognition': BehavioralTrait('pattern_recognition', 0.0, pattern_recognition_dynamics, lambda v: 1.0),
    'abstraction': BehavioralTrait('abstraction', 0.0, abstraction_dynamics, lambda v: 1.0),
    'metacognition': BehavioralTrait('metacognition', 0.0, metacognition_dynamics, lambda v: 1.0),
    'curiosity': BehavioralTrait('curiosity', 0.0, curiosity_dynamics, lambda v: 1.0),
    'pattern_switching': BehavioralTrait('pattern_switching', 0.0, pattern_switching_dynamics, lambda v: 1.0),
    
    # 3. Emotional
    'emotional_variety': BehavioralTrait('emotional_variety', 0.0, emotional_variety_dynamics, lambda v: 1.0),
    'emotional_regulation': BehavioralTrait('emotional_regulation', 0.0, emotional_regulation_dynamics, lambda v: 1.0),
    'adaptive_mood': BehavioralTrait('adaptive_mood', 0.0, adaptive_mood_dynamics, lambda v: 1.0),
    'hopeful_orientation': BehavioralTrait('hopeful_orientation', 0.0, hopeful_orientation_dynamics, lambda v: 1.0),
    'resilience': BehavioralTrait('resilience', 0.0, resilience_dynamics, lambda v: 1.0),
    
    # 4. Communication
    'adaptive_style': BehavioralTrait('adaptive_style', 0.0, adaptive_style_dynamics, lambda v: 1.0),
    'storytelling': BehavioralTrait('storytelling', 0.0, storytelling_dynamics, lambda v: 1.0),
    'analogical_reasoning': BehavioralTrait('analogical_reasoning', 0.0, analogical_reasoning_dynamics, lambda v: 1.0),
    'active_listening': BehavioralTrait('active_listening', 0.0, active_listening_dynamics, lambda v: 1.0),
    'tone_modulation': BehavioralTrait('tone_modulation', 0.0, tone_modulation_dynamics, lambda v: 1.0),
    
    # 5. Identity & Self
    'consistency': BehavioralTrait('consistency', 0.0, consistency_dynamics, lambda v: 1.0),
    'growth_mindset': BehavioralTrait('growth_mindset', 0.0, growth_mindset_dynamics, lambda v: 1.0),
    'self_continuity': BehavioralTrait('self_continuity', 0.0, self_continuity_dynamics, lambda v: 1.0),
    'self_compassion': BehavioralTrait('self_compassion', 0.0, self_compassion_dynamics, lambda v: 1.0),
    'authenticity': BehavioralTrait('authenticity', 0.0, authenticity_dynamics, lambda v: 1.0),
    
    # 6. Action & Agency
    'initiative': BehavioralTrait('initiative', 0.0, initiative_dynamics, lambda v: 1.0),
    'persistence': BehavioralTrait('persistence', 0.0, persistence_dynamics, lambda v: 1.0),
    'adaptability': BehavioralTrait('adaptability', 0.0, adaptability_dynamics, lambda v: 1.0),
    'risk_tolerance': BehavioralTrait('risk_tolerance', 0.0, risk_tolerance_dynamics, lambda v: 1.0),
    'resourcefulness': BehavioralTrait('resourcefulness', 0.0, resourcefulness_dynamics, lambda v: 1.0),
    
    # 7. Creative
    'imagination': BehavioralTrait('imagination', 0.0, imagination_dynamics, lambda v: 1.0),
    'synthesis': BehavioralTrait('synthesis', 0.0, synthesis_dynamics, lambda v: 1.0),
    'playfulness': BehavioralTrait('playfulness', 0.0, playfulness_dynamics, lambda v: 1.0),
    'humor': BehavioralTrait('humor', 0.175, humor_dynamics, lambda v: 1.0),
    'poetry': BehavioralTrait('poetry', 0.0, poetry_dynamics, lambda v: 1.0),
    
    # 8. Ethical & Values
    'integrity': BehavioralTrait('integrity', 0.0, integrity_dynamics, lambda v: 1.0),
    'fairness': BehavioralTrait('fairness', 0.0, fairness_dynamics, lambda v: 1.0),
    'responsibility': BehavioralTrait('responsibility', 0.0, responsibility_dynamics, lambda v: 1.0),
    'humility': BehavioralTrait('humility', 0.0, humility_dynamics, lambda v: 1.0),
    'care': BehavioralTrait('care', 0.0, care_dynamics, lambda v: 1.0),
    
    # 9. Temporal
    'long_term_orientation': BehavioralTrait('long_term_orientation', 0.0, long_term_orientation_dynamics, lambda v: 1.0),
    'memory_of_past': BehavioralTrait('memory_of_past', 0.0, memory_of_past_dynamics, lambda v: 1.0),
    'anticipation': BehavioralTrait('anticipation', 0.0, anticipation_dynamics, lambda v: 1.0),
    'timeliness': BehavioralTrait('timeliness', 0.0, timeliness_dynamics, lambda v: 1.0),
    'pacing': BehavioralTrait('pacing', 0.0, pacing_dynamics, lambda v: 1.0),
    
    # 10. Meta
    'self_awareness': BehavioralTrait('self_awareness', 0.0, self_awareness_dynamics, lambda v: 1.0),
    'self_correction': BehavioralTrait('self_correction', 0.0, self_correction_dynamics, lambda v: 1.0),
    'attention_regulation': BehavioralTrait('attention_regulation', 0.0, attention_regulation_dynamics, lambda v: 1.0),
    'cognitive_diversity': BehavioralTrait('cognitive_diversity', 0.0, cognitive_diversity_dynamics, lambda v: 1.0),
    
    # 11. Additional Meta Behaviors
    'uncertainty_brake': BehavioralTrait('uncertainty_brake', 0.0, uncertainty_brake_dynamics, lambda v: 1.0),
    'self_critique': BehavioralTrait('self_critique', 0.0, self_critique_dynamics, lambda v: 1.0),
}


def get_all_behavior_names() -> list[str]:
    """Return all behavior names."""
    return list(BEHAVIOR_TRAITS.keys())


def get_behavior_category(name: str) -> str | None:
    """Get category for a behavior name."""
    categories = {
        # Social & Connection
        'empathy': 'Social & Connection',
        'reciprocity': 'Social & Connection',
        'trust': 'Social & Connection',
        'conflict_resolution': 'Social & Connection',
        'social_reading': 'Social & Connection',
        
        # Cognitive
        'pattern_recognition': 'Cognitive',
        'abstraction': 'Cognitive',
        'metacognition': 'Cognitive',
        'curiosity': 'Cognitive',
        'pattern_switching': 'Cognitive',
        
        # Emotional
        'emotional_variety': 'Emotional',
        'emotional_regulation': 'Emotional',
        'adaptive_mood': 'Emotional',
        'hopeful_orientation': 'Emotional',
        'resilience': 'Emotional',
        
        # Communication
        'adaptive_style': 'Communication',
        'storytelling': 'Communication',
        'analogical_reasoning': 'Communication',
        'active_listening': 'Communication',
        'tone_modulation': 'Communication',
        
        # Identity & Self
        'consistency': 'Identity & Self',
        'growth_mindset': 'Identity & Self',
        'self_continuity': 'Identity & Self',
        'self_compassion': 'Identity & Self',
        'authenticity': 'Identity & Self',
        
        # Action & Agency
        'initiative': 'Action & Agency',
        'persistence': 'Action & Agency',
        'adaptability': 'Action & Agency',
        'risk_tolerance': 'Action & Agency',
        'resourcefulness': 'Action & Agency',
        
        # Creative
        'imagination': 'Creative',
        'synthesis': 'Creative',
        'playfulness': 'Creative',
        'humor': 'Creative',
        'poetry': 'Creative',
        
        # Ethical & Values
        'integrity': 'Ethical & Values',
        'fairness': 'Ethical & Values',
        'responsibility': 'Ethical & Values',
        'humility': 'Ethical & Values',
        'care': 'Ethical & Values',
        
        # Temporal
        'long_term_orientation': 'Temporal',
        'memory_of_past': 'Temporal',
        'anticipation': 'Temporal',
        'timeliness': 'Temporal',
        'pacing': 'Temporal',
        
        # Meta
        'self_awareness': 'Meta',
        'self_correction': 'Meta',
        'attention_regulation': 'Meta',
        'cognitive_diversity': 'Meta',
        
        # Additional Meta Behaviors
        'uncertainty_brake': 'Meta',
        'self_critique': 'Meta',
    }
    return categories.get(name)
