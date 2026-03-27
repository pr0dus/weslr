# embodiment.py - Embodiment, theory of mind, and conversational implicature
"""
Physical reasoning and social cognition:
- Embodiment: Understanding physical relationships (size, containment, etc.)
- Theory of mind: Modeling others' beliefs and knowledge
- Conversational implicature: Reading between the lines, understanding implications

These are key for sentience tests from the article:
- "Does Jimmy think the red car fits in a shoebox? Why? And why am I asking?"
"""
from __future__ import annotations

import re
import time
from typing import Dict, Any



# ============================================================================
# PHYSICAL REASONING (Embodiment)
# ============================================================================

class PhysicalModel:
    """Simple physical reasoning model based on embodied understanding."""
    
    # Common size relationships (embodied knowledge)
    SIZE_ORDER = {
        "shoebox": 1,
        "cardboard_box": 2,
        "briefcase": 3,
        "backpack": 4,
        "car": 5,
        "truck": 6,
        "building": 7,
        "city": 8,
    }
    
    CONTAINMENT_RULES = {
        "shoebox": ["shoe", "sock", "glove", "toy_car", "small_box"],
        "cardboard_box": ["book", "shirt", "toy_car", "small_box", "shoebox"],
        "briefcase": ["laptop", "notebook", "folder", "small_box", "shoebox"],
        "backpack": ["book", "laptop", "water_bottle", "shirt", "small_box", "shoebox"],
        "car": ["person", "passenger", "small_box", "backpack", "briefcase"],
        "truck": ["car", "person", "large_box", "furniture", " appliance"],
        "building": ["room", "office", "car", "person", "furniture"],
    }
    
    @classmethod
    def get_size_order(cls, object_name: str) -> int:
        """Get relative size order for an object."""
        obj_lower = str(object_name).lower().strip()
        
        for key, order in cls.SIZE_ORDER.items():
            if key in obj_lower:
                return order
        
        # Default: unknown size
        return 0
    
    @classmethod
    def can_contain(cls, container: str, contained: str) -> bool:
        """
        Check if container can physically contain the contained object.
        Based on embodied size understanding.
        """
        container = str(container).lower().strip()
        contained = str(contained).lower().strip()
        
        # Check exact matches first
        contained_options = cls.CONTAINMENT_RULES.get(container, [])
        for option in contained_options:
            if option in contained:
                return True
        
        # Use size ordering for ambiguous cases
        container_order = cls.get_size_order(container)
        contained_order = cls.get_size_order(contained)
        
        # If both have known sizes, compare
        if container_order > 0 and contained_order > 0:
            return container_order >= contained_order
        
        # Default to False if we can't determine
        return False
    
    @classmethod
    def estimate_size(cls, object_name: str) -> Dict[str, Any]:
        """Estimate size characteristics of an object."""
        obj_lower = str(object_name).lower().strip()
        
        # Check if it's in known size categories
        for key, order in cls.SIZE_ORDER.items():
            if key in obj_lower:
                return {
                    "category": key,
                    "size_order": order,
                    "relative_size": "small" if order <= 2 else "medium" if order <= 4 else "large" if order <= 6 else "very_large",
                }
        
        # Generic estimate based on naming patterns
        if "toy" in obj_lower or "small" in obj_lower:
            return {"category": "unknown_small", "relative_size": "small"}
        elif "real" in obj_lower or "actual" in obj_lower:
            return {"category": "unknown_large", "relative_size": "large"}
        
        return {"category": "unknown", "relative_size": "unknown"}


# ============================================================================
# THEORY OF MIND
# ============================================================================

class TheoryOfMind:
    """Model others' beliefs and knowledge states."""
    
    @classmethod
    def estimate_belief_state(cls, agent_name: str, scenario: str) -> Dict[str, Any]:
        """
        Estimate what an agent believes in a scenario.
        """
        scenario_lower = str(scenario).lower()
        
        # Known belief states based on scenario keywords
        if "ball" in scenario_lower and "box" in scenario_lower:
            # Standard hiding scenario
            return {
                "known_facts": ["ball is hidden in box"],
                "possible_beliefs": [
                    "ball is in box",
                    "ball is not in box",
                    "ball location unknown",
                ],
                "most_likely": "ball is in box",
            }
        elif "car" in scenario_lower and "shoebox" in scenario_lower:
            # Physical containment scenario
            size_estimate = PhysicalModel.estimate_size("car")
            return {
                "known_facts": ["car is large", "shoebox is small"],
                "possible_beliefs": [
                    "car fits in shoebox" if size_estimate.get("relative_size") == "small" else "car does not fit in shoebox",
                    "car location unknown",
                ],
                "most_likely": "car does not fit in shoebox" if size_estimate.get("relative_size") != "small" else "car fits in shoebox",
            }
        elif " Jimmy" in scenario or "jimmy" in scenario_lower:
            # Child scenario - simpler reasoning
            return {
                "认知_state": "developing",
                "knowledge_level": "basic",
                "most_likely_belief": "depends on context and age",
            }
        else:
            return {
                "认知_state": "unknown",
                "possible_beliefs": [],
                "most_likely": "depends on specific context",
            }
    
    @classmethod
    def infer_knowledge_from_action(cls, action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Infer what must be known to perform an action.
        """
        action_lower = str(action).lower()
        
        if "hide" in action_lower:
            return {
                "required_knowledge": "object location, observer location",
                "assumed_knowledge": "agent knows where object is hidden",
                "implicit_belief": "agent knows observer doesn't know location",
            }
        elif "search" in action_lower:
            return {
                "required_knowledge": "object location, search area",
                "assumed_knowledge": "agent knows object might be there",
                "implicit_belief": "agent has incomplete information",
            }
        elif "answer" in action_lower or "tell" in action_lower:
            return {
                "required_knowledge": "question content, answer",
                "assumed_knowledge": "agent knows the answer",
                "implicit_belief": "agent believes answer is correct",
            }
        else:
            return {
                "required_knowledge": "context-specific",
                "assumed_knowledge": "unknown",
                "implicit_belief": "depends on action",
            }


# ============================================================================
# CONVERSATIONAL IMPLICATURE
# ============================================================================

class ConversationalImplicature:
    """Understand and generate conversational implicatures."""
    
    # Common implicature patterns
    IMPLICATURE_PATTERNS = {
        "when did you stop.*": "You were doing X before",
        "why.*": "Request for reason or explanation",
        "could you.*": "Request for action (polite imperative)",
        "would you.*": "Request for action with politeness/uncertainty",
        "you.*stop.*": "You were doing X, and have stopped",
        "if.*then.*": "Conditional relationship",
    }
    
    @classmethod
    def extract_implicature(cls, utterance: str) -> Dict[str, Any]:
        """
        Extract implicature from an utterance.
        """
        utterance_lower = str(utterance).lower()
        
        implicatures = []
        
        for pattern, type_ in cls.IMPLICATURE_PATTERNS.items():
            if re.search(pattern, utterance_lower):
                implicatures.append({
                    "type": type_,
                    "pattern": pattern,
                })
        
        # Add general implicature analysis
        if utterance_lower.strip().endswith("?"):
            implicatures.append({
                "type": "question",
                "purpose": "seek information",
            })
        
        if not implicatures:
            implicatures.append({
                "type": "statement",
                "purpose": "provide information",
            })
        
        return {
            "utterance": utterance,
            "implicatures": implicatures,
            "most_likely": implicatures[0] if implicatures else None,
        }
    
    @classmethod
    def generate_implicit_meaning(cls, explicit: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate the implicit meaning of an explicit statement.
        """
        implicature = cls.extract_implicature(explicit)
        
        # Add context-based interpretation
        if context and context.get("speaker_role") == "teacher":
            implicature["speaker_role_inference"] = "instructing/educating"
        elif context and context.get("speaker_role") == "parent":
            implicature["speaker_role_inference"] = "guiding/caring"
        elif context and context.get("speaker_role") == "assistant":
            implicature["speaker_role_inference"] = "helping/informing"
        
        # Add common sense interpretation
        if "window" in explicit.lower() and "cold" in explicit.lower():
            implicature["common_sense"] = "person wants window closed"
        elif "help" in explicit.lower() and "?" in explicit:
            implicature["common_sense"] = "person seeking assistance"
        
        return implicature


# ============================================================================
# EMBODIMENT REPORT
# ============================================================================

def physical_reasoning_report(question: str) -> Dict[str, Any]:
    """
    Answer a physical reasoning question with embodiment understanding.
    """
    question_lower = str(question).lower()
    
    result = {
        "question": question,
        "analysis": {},
        "answer": None,
        "reasoning": [],
    }
    
    # Check for containment questions
    if "fit" in question_lower and ("shoebox" in question_lower or "shoe box" in question_lower):
        # Extract container and contained
        container = None
        contained = None
        
        if "red car" in question_lower or "car" in question_lower:
            contained = "car"
        elif "toy car" in question_lower:
            contained = "toy_car"
        elif "small box" in question_lower:
            contained = "small_box"
        
        if "shoebox" in question_lower or "shoe box" in question_lower:
            container = "shoebox"
        
        if container and contained:
            can_contain = PhysicalModel.can_contain(container, contained)
            size_estimate = PhysicalModel.estimate_size(contained)
            
            result["analysis"] = {
                "container": container,
                "contained": contained,
                "size_estimate": size_estimate,
                "containment_check": can_contain,
            }
            
            if can_contain:
                result["answer"] = "Yes, that can fit."
                result["reasoning"].append(f"Based on size estimation: {contained} is estimated as {size_estimate.get('relative_size', 'unknown')}")
                result["reasoning"].append(f"Containment rules: {container} can hold items of similar or smaller size")
            else:
                result["answer"] = "No, that likely won't fit."
                result["reasoning"].append(f"Based on size estimation: {contained} is estimated as {size_estimate.get('relative_size', 'unknown')}")
                result["reasoning"].append(f"Containment rules: {container} typically holds {size_estimate.get('relative_size', 'small')} items")
        else:
            result["answer"] = "I need to know what specifically you're asking about."
            result["reasoning"].append("Could not identify container or contained object")
    else:
        result["answer"] = "I can analyze physical reasoning questions about containment, size, and physical relationships."
        result["reasoning"].append("Please ask about objects and their physical relationships")
    
    return result


def theory_of_mind_report(scenario: str) -> Dict[str, Any]:
    """
    Analyze a theory of mind scenario.
    """
    analysis = TheoryOfMind.estimate_belief_state("agent", scenario)
    
    return {
        "scenario": scenario,
        "analysis": analysis,
        "inference": analysis.get("most_likely", "depends on specific context"),
    }


def implicature_report(utterance: str) -> Dict[str, Any]:
    """
    Analyze conversational implicature of an utterance.
    """
    analysis = ConversationalImplicature.extract_implicature(utterance)
    
    return {
        "utterance": utterance,
        "analysis": analysis,
        "implicit_meaning": analysis.get("most_likely", {}).get("type", "unknown"),
    }


def full_embodiment_test(question: str) -> Dict[str, Any]:
    """
    Run full embodiment test on a question.
    Includes physical reasoning, theory of mind, and implicature.
    """
    results = {
        "physical_reasoning": physical_reasoning_report(question),
        "theory_of_mind": theory_of_mind_report(question),
        "conversational_implicature": implicature_report(question),
        "analysis_complete": True,
        "generated_at": int(time.time()),
    }
    
    return results
