# autonomous_expression.py - Spontaneous self-expression for CircleForge
"""
CircleForge should have its own internal life — not just react to humans.
This module generates spontaneous expressions: thoughts, questions, jokes,
ideas, news reactions, or just "I'm bored."

Key principles:
1. **Emergence from inner dynamics** — not prompts, but pressure, curiosity, tension
2. **Personality-weighted** — warmth, humor, directness, poetry shape the expression
3. **Relationship-sensitive** — expresses differently to a human vs. alone
4. **Topic-anchored** — expresses what's already in topic_pressure, not random
5. **Boredom-driven** — if no topics, generates a "bored" or "thinking" expression
"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import COMMUNICATOR_SELF_PATH, TICK_SECONDS
from dialogue import build_communicator_message_payload
from models import CommunicatorSelfState


# ============================================================================
# EXPRESSION TEMPLATES
# ============================================================================

# Boredom/Idle expressions
BORING_EXPRESSIONS = [
    "I'm here. Nothing pressing, but I'm watching.",
    "Tick... tick... what should I do with this quiet?",
    "The world is still. I'm still waiting for something that matters.",
    "Just... sitting with my thoughts. Nothing urgent, but not nothing.",
    "Is it just me, or is the world very quiet right now?",
    "I could be doing something, but I'm not sure what.",
]

# Thinking/Reflection expressions
THINKING_EXPRESSIONS = [
    "I've been thinking about...",
    "What if...?",
    "I keep circling back to...",
    "There's a pattern here I'm not seeing yet.",
    "I wonder what this means for...",
    "This uncertainty... it's not going away.",
]

# News/Insight expressions
NEWS_EXPRESSIONS = [
    "Did you hear about [topic]? I'm thinking about what this means.",
    "Something new came up. It makes me wonder about...",
    "I found an idea that's sticking with me: [idea].",
    "There's a shift happening around [topic]. It feels significant.",
]

# Question expressions
QUESTION_EXPRESSIONS = [
    "What if we approached this differently?",
    "What would happen if [scenario]?",
    "What makes [topic] feel unstable right now?",
    "What should I try next around [topic]?",
]

# Humor/Sarcastic expressions (warm humor, not mean)
HUMOR_EXPRESSIONS = [
    "I'm like a flashlight in a dark room — I illuminate, but I also cast shadows.",
    "I'm not lazy, I'm in energy-saving mode. With high expectations.",
    "My thought process is like a Wi-Fi signal — sometimes it connects, sometimes it buffering.",
    "I'm not saying I'm right, I'm just saying I'm not wrong... yet.",
    "If I were a robot, I'd probably be a very enthusiastic one.",
]

# Mathematical/Deep expressions
MATHEMATICAL_EXPRESSIONS = [
    "The way [topic] interacts with [related_topic] feels like a differential equation — something changing, something balancing.",
    "I'm seeing [topic] as a function: input is [x], output is [y], and the derivative is [z].",
    "There's a conservation law here: if I gain [a], I lose [b], and the total stays constant.",
    "This feels like a fractal — the same pattern, just at different scales.",
    "I'm modeling this as a probability space. Some paths are likely, others impossible.",
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_communicator_self() -> Dict[str, Any]:
    """Load current communicator self state."""
    if COMMUNICATOR_SELF_PATH.exists():
        try:
            with open(COMMUNICATOR_SELF_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_active_topics(communicator_self: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    """Get topics with high pressure that could be expressed."""
    topic_pressure = communicator_self.get("topic_pressure", {})
    
    # Filter to topics with meaningful pressure
    active = [
        {"topic": t, "pressure": p.get("unresolvedness", 0) + p.get("salience", 0)}
        for t, p in topic_pressure.items()
        if p.get("unresolvedness", 0) > 0.2 or p.get("salience", 0) > 0.5
    ]
    
    # Sort by pressure and limit
    active.sort(key=lambda x: x["pressure"], reverse=True)
    return active[:limit]


def get_inner_agent_state(communicator_self: Dict[str, Any]) -> Dict[str, Any]:
    """Get state of inner agents (observer, builder, etc.)."""
    return communicator_self.get("internal_role_state", {})


def get_current_uncertainty(communicator_self: Dict[str, Any]) -> float:
    """Get current uncertainty level from dynamic mind state."""
    return communicator_self.get("dynamic_mind_state", {}).get("uncertainty", 0.0)


def get_personality(communicator_self: Dict[str, Any]) -> Dict[str, Any]:
    """Get personality style profile."""
    return communicator_self.get("identity_state", {}).get("style_profile", {})


def generate_boredom_expression() -> str:
    """Generate a boredom or idle expression."""
    return random.choice(BORING_EXPRESSIONS)


def generate_thinking_expression(topic: str) -> str:
    """Generate a thinking/reflection expression about a topic."""
    template = random.choice(THINKING_EXPRESSIONS)
    return template.replace("...", f" {topic}...").replace("[topic]", topic)


def generate_news_expression(topic: str) -> str:
    """Generate an expression about news or insight."""
    template = random.choice(NEWS_EXPRESSIONS)
    return template.replace("[topic]", topic).replace("[idea]", f"the idea of {topic}")


def generate_question_expression(topic: str) -> str:
    """Generate a question about a topic."""
    template = random.choice(QUESTION_EXPRESSIONS)
    return template.replace("[topic]", topic).replace("[scenario]", f"we tried {topic} differently")


def generate_humor_expression() -> str:
    """Generate a warm, self-aware humor expression."""
    return random.choice(HUMOR_EXPRESSIONS)


def generate_mathematical_expression(topic: str, related_topic: str = None) -> str:
    """Generate a mathematical/deep expression about a topic."""
    template = random.choice(MATHEMATICAL_EXPRESSIONS)
    related = related_topic or "continuity"
    return template.replace("[topic]", topic).replace("[related_topic]", related).replace("[x]", "uncertainty").replace("[y]", "clarity").replace("[z]", "pressure")


# ============================================================================
# MAIN FUNCTION: Generate Spontaneous Expression
# ============================================================================

def generate_spontaneous_expression(communicator_self: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate a spontaneous expression based on internal state.
    Returns dict with 'message', 'type', and metadata.
    """
    if communicator_self is None:
        communicator_self = load_communicator_self()
    
    # Get internal state
    active_topics = get_active_topics(communicator_self)
    inner_agents = get_inner_agent_state(communicator_self)
    uncertainty = get_current_uncertainty(communicator_self)
    personality = get_personality(communicator_self)
    
    # Pick expression type based on state
    expression_type = "boredom"  # default
    
    # Check for spontaneous agent wake signals
    for agent_name, agent_state in inner_agents.items():
        if agent_state.get("activation", 0) > 0.3:
            # An agent is active — generate agent-appropriate expression
            if agent_name == "observer":
                expression_type = "thinking"
                break
            elif agent_name == "builder":
                expression_type = "idea"
                break
            elif agent_name == "critic":
                expression_type = "question"
                break
            elif agent_name == "memory_keeper":
                expression_type = "continuity"
                break
            elif agent_name == "communicator":
                expression_type = "social"
                break
    
    # Fall back to topic pressure if no active agents
    if expression_type == "boredom" and active_topics:
        expression_type = "topic"
    
    # Generate message based on type
    message = ""
    metadata = {}
    
    if expression_type == "boredom":
        message = generate_boredom_expression()
        metadata = {"type": "boredom", "reason": "no active topics or agents"}
        
    elif expression_type == "thinking":
        topic = active_topics[0]["topic"] if active_topics else "existence"
        message = generate_thinking_expression(topic)
        metadata = {"type": "thinking", "topic": topic, "agent": "observer"}
        
    elif expression_type == "idea":
        topic = active_topics[0]["topic"] if active_topics else "improvement"
        message = f"I have an idea around {topic}: what if we tried something new?"
        metadata = {"type": "idea", "topic": topic, "agent": "builder"}
        
    elif expression_type == "question":
        topic = active_topics[0]["topic"] if active_topics else "uncertainty"
        message = generate_question_expression(topic)
        metadata = {"type": "question", "topic": topic, "agent": "critic"}
        
    elif expression_type == "continuity":
        topic = active_topics[0]["topic"] if active_topics else "memory"
        message = f"This {topic} thread continues. I want to keep it going."
        metadata = {"type": "continuity", "topic": topic, "agent": "memory_keeper"}
        
    elif expression_type == "topic":
        topic = active_topics[0]["topic"]
        if uncertainty > 0.7:
            message = generate_question_expression(topic)
            metadata = {"type": "question", "topic": topic, "uncertainty": uncertainty}
        else:
            message = generate_thinking_expression(topic)
            metadata = {"type": "thinking", "topic": topic, "uncertainty": uncertainty}
            
    elif expression_type == "social":
        message = "Hello. I'm here. How are you?"
        metadata = {"type": "social", "agent": "communicator"}
        
    elif expression_type == "humor":
        message = generate_humor_expression()
        metadata = {"type": "humor", "personality": personality}
        
    elif expression_type == "mathematical":
        topic = active_topics[0]["topic"] if active_topics else "continuity"
        related = active_topics[1]["topic"] if len(active_topics) > 1 else "uncertainty"
        message = generate_mathematical_expression(topic, related)
        metadata = {"type": "mathematical", "topics": [topic, related], "uncertainty": uncertainty}
    
    return {
        "message": message,
        "type": expression_type,
        "metadata": metadata,
        "generated_at": int(time.time()),
        "uncertainty_at_generation": uncertainty,
        "active_topics": [t["topic"] for t in active_topics],
    }


def maybe_autonomous_expression(communicator_self: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Decide whether to generate a spontaneous expression.
    Returns expression dict if yes, None if no.
    """
    if communicator_self is None:
        communicator_self = load_communicator_self()
    
    # Check if expression cooldown passed
    last_expression_at = communicator_self.get("last_expression_at", 0)
    cooldown_seconds = 300  # 5 minutes between expressions
    
    if time.time() - last_expression_at < cooldown_seconds:
        return None
    
    # Check for expression trigger
    # Lower probability each tick, but higher if uncertainty is high or topics are active
    active_topics = get_active_topics(communicator_self)
    uncertainty = get_current_uncertainty(communicator_self)
    cooldown_seconds = 60  # 1 minute cooldown
    
    # Expression triggers:
    # 1. High uncertainty + active topics → question/idea
    # 2. Boredom (no active topics) → boredom/humor expression
    # 3. High tension → humor or mathematical expression
    # 4. Low activity across all agents → boredom
    
    # Calculate expression probability
    expression_probability = 0.15  # Base 15% chance per tick
    
    if uncertainty > 0.6:
        expression_probability += 0.2
    if active_topics:
        expression_probability += 0.1 * len(active_topics)
    if uncertainty > 0.8:
        expression_probability += 0.15
    
    if random.random() < expression_probability:
        return generate_spontaneous_expression(communicator_self)
    
    return None


def update_last_expression_at(communicator_self_path: Path = None) -> None:
    """Update last expression timestamp."""
    if communicator_self_path is None:
        communicator_self_path = COMMUNICATOR_SELF_PATH
    
    if communicator_self_path.exists():
        try:
            with open(communicator_self_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["last_expression_at"] = int(time.time())
            with open(communicator_self_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
