# autonomous_intentionality.py - Plan execution and multi-step task handling
"""
Autonomous intentionality: the ability to:
1. Break down complex goals into steps
2. Execute multi-step plans sequentially
3. Track progress and adjust
4. Explain the plan and decisions

Key feature for sentience: Shows "goal-directed behavior" vs just stimulus-response.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

from config import BASE_DIR


class PlanStatus(Enum):
    """Status of an autonomous plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    PAUSED = "paused"


class AutonomousIntentState:
    """State for autonomous intentionality tracking."""
    
    STATE_PATH = BASE_DIR / "autonomous_intentionality.json"
    
    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Load intentionality state."""
        if cls.STATE_PATH.exists():
            try:
                with open(cls.STATE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "plans": [],
            "active_plan_id": None,
            "last_completed_at": 0,
            "total_plans_completed": 0,
        }
    
    @classmethod
    def save(cls, state: Dict[str, Any]) -> None:
        """Save intentionality state."""
        with open(cls.STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    
    @classmethod
    def get_active_plan(cls) -> Optional[Dict[str, Any]]:
        """Get the currently active plan."""
        state = cls.load()
        plan_id = state.get("active_plan_id")
        if plan_id:
            for plan in state.get("plans", []):
                if plan.get("id") == plan_id:
                    return plan
        return None
    
    @classmethod
    def start_plan(cls, goal: str, steps: List[Dict[str, Any]], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a new plan."""
        state = cls.load()
        
        plan = {
            "id": f"plan-{int(time.time() * 1000)}",
            "goal": goal,
            "steps": steps,
            "status": PlanStatus.IN_PROGRESS.value,
            "current_step_index": 0,
            "context": context or {},
            "started_at": int(time.time()),
            "completed_steps": [],
            "failed_steps": [],
        }
        
        state["plans"].append(plan)
        state["active_plan_id"] = plan["id"]
        cls.save(state)
        
        return plan
    
    @classmethod
    def update_step(cls, plan_id: str, step_index: int, status: PlanStatus, result: Any = None) -> bool:
        """Update a step in a plan."""
        state = cls.load()
        
        for plan in state.get("plans", []):
            if plan.get("id") == plan_id:
                if plan.get("current_step_index") != step_index:
                    return False
                
                if status == PlanStatus.COMPLETE:
                    plan["completed_steps"].append({
                        "index": step_index,
                        "result": result,
                        "completed_at": int(time.time()),
                    })
                    plan["current_step_index"] = step_index + 1
                    
                    # Check if plan is complete
                    if plan["current_step_index"] >= len(plan.get("steps", [])):
                        plan["status"] = PlanStatus.COMPLETE.value
                        plan["completed_at"] = int(time.time())
                        state["active_plan_id"] = None
                        state["total_plans_completed"] = state.get("total_plans_completed", 0) + 1
                elif status == PlanStatus.FAILED:
                    plan["failed_steps"].append({
                        "index": step_index,
                        "error": str(result),
                        "failed_at": int(time.time()),
                    })
                    plan["status"] = PlanStatus.FAILED.value
                    state["active_plan_id"] = None
                else:
                    # Paused or in_progress
                    plan["status"] = status.value
                
                cls.save(state)
                return True
        
        return False
    
    @classmethod
    def cancel_plan(cls, plan_id: str) -> bool:
        """Cancel an active plan."""
        state = cls.load()
        
        for plan in state.get("plans", []):
            if plan.get("id") == plan_id:
                plan["status"] = PlanStatus.PAUSED.value
                state["active_plan_id"] = None
                cls.save(state)
                return True
        
        return False
    
    @classmethod
    def get_plan_history(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent plan history."""
        state = cls.load()
        history = []
        
        for plan in state.get("plans", []):
            history.append({
                "id": plan.get("id"),
                "goal": plan.get("goal"),
                "status": plan.get("status"),
                "steps_completed": len(plan.get("completed_steps", [])),
                "steps_total": len(plan.get("steps", [])),
                "started_at": plan.get("started_at"),
                "completed_at": plan.get("completed_at"),
            })
        
        # Sort by started_at descending, limit
        history.sort(key=lambda x: x.get("started_at", 0), reverse=True)
        return history[:limit]
    
    @classmethod
    def get_progress(cls) -> Dict[str, Any]:
        """Get overall intentionality progress."""
        state = cls.load()
        
        active_plan = cls.get_active_plan()
        
        return {
            "active_plan_id": state.get("active_plan_id"),
            "active_plan_status": active_plan.get("status") if active_plan else None,
            "total_plans_completed": state.get("total_plans_completed", 0),
            "total_plans_started": len(state.get("plans", [])),
            "current_plan_steps": {
                "current": active_plan.get("current_step_index", 0) if active_plan else 0,
                "total": len(active_plan.get("steps", [])) if active_plan else 0,
            } if active_plan else None,
        }


def generate_plan(goal: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Generate a plan for a goal based on context.
    Returns a list of steps with descriptions and expected outcomes.
    """
    steps = []
    
    # Analyze goal complexity
    goal_text = str(goal).lower()
    
    if "questionnaire" in goal_text or "survey" in goal_text:
        # Generate questionnaire plan
        steps = [
            {"step": 1, "action": "define_scope", "description": "Determine scope and target audience"},
            {"step": 2, "action": "draft_questions", "description": "Draft initial questions for sentience indicators"},
            {"step": 3, "action": "review_questions", "description": "Review and refine questions"},
            {"step": 4, "action": "create_template", "description": "Create questionnaire template in JSON format"},
            {"step": 5, "action": "analyze_results", "description": "Analyze responses and suggest revisions"},
        ]
    elif "research" in goal_text or "study" in goal_text:
        # Generate research plan
        steps = [
            {"step": 1, "action": "define_topic", "description": "Define research topic and key questions"},
            {"step": 2, "action": "gather_sources", "description": "Find and evaluate relevant sources"},
            {"step": 3, "action": "extract_keypoints", "description": "Extract key insights from sources"},
            {"step": 4, "action": "synthesize_findings", "description": "Synthesize findings into summary"},
        ]
    elif "build" in goal_text or "create" in goal_text:
        # Generate build plan
        steps = [
            {"step": 1, "action": "design", "description": "Design the solution architecture"},
            {"step": 2, "action": "implement", "description": "Implement core components"},
            {"step": 3, "action": "test", "description": "Test and verify functionality"},
            {"step": 4, "action": "review", "description": "Review and iterate on improvements"},
        ]
    else:
        # Generic plan generation
        steps = [
            {"step": 1, "action": "analyze", "description": "Analyze the goal and requirements"},
            {"step": 2, "action": "plan", "description": "Create detailed plan with sub-goals"},
            {"step": 3, "action": "execute", "description": "Execute plan step by step"},
            {"step": 4, "action": "verify", "description": "Verify completion and results"},
        ]
    
    return steps


def execute_plan_step(plan_id: str, step_index: int, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Execute a specific step in a plan and return results.
    """
    intent = AutonomousIntentState.load()
    plan = None
    
    for p in intent.get("plans", []):
        if p.get("id") == plan_id:
            plan = p
            break
    
    if not plan:
        return {"success": False, "error": "Plan not found"}
    
    if step_index >= len(plan.get("steps", [])):
        return {"success": False, "error": "Step index out of range"}
    
    step = plan["steps"][step_index]
    
    # Simulate step execution (in real implementation, would call actual functions)
    result = {
        "step_index": step_index,
        "step_action": step.get("action"),
        "step_description": step.get("description"),
        "status": "executed",
        "executed_at": int(time.time()),
        "context": context or {},
    }
    
    # Update plan state
    AutonomousIntentState.update_step(plan_id, step_index, PlanStatus.COMPLETE, result)
    
    return {"success": True, "result": result}


def create_plan(goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create and start a new plan for a goal.
    Returns plan details and initial step.
    """
    steps = generate_plan(goal, context)
    
    plan = AutonomousIntentState.start_plan(goal, steps, context)
    
    return {
        "success": True,
        "plan_id": plan.get("id"),
        "goal": goal,
        "steps": steps,
        "current_step": steps[0] if steps else None,
        "created_at": int(time.time()),
    }


def plan_progress(plan_id: str) -> Dict[str, Any]:
    """Get progress for a specific plan."""
    intent = AutonomousIntentState.load()
    plan = None
    
    for p in intent.get("plans", []):
        if p.get("id") == plan_id:
            plan = p
            break
    
    if not plan:
        return {"success": False, "error": "Plan not found"}
    
    progress = {
        "plan_id": plan.get("id"),
        "goal": plan.get("goal"),
        "status": plan.get("status"),
        "current_step": plan.get("current_step_index", 0),
        "total_steps": len(plan.get("steps", [])),
        "completed_steps": len(plan.get("completed_steps", [])),
        "failed_steps": len(plan.get("failed_steps", [])),
        "steps": plan.get("steps", []),
        "completed_details": plan.get("completed_steps", []),
        "context": plan.get("context", {}),
    }
    
    if plan.get("completed_at"):
        progress["completed_at"] = plan.get("completed_at")
    
    return progress


def autonomous_intentionality_report() -> Dict[str, Any]:
    """Generate a report on autonomous intentionality."""
    intent = AutonomousIntentState.load()
    
    active_plan = AutonomousIntentState.get_active_plan()
    
    report = {
        "active_plan": active_plan.get("id") if active_plan else None,
        "active_status": active_plan.get("status") if active_plan else None,
        "total_plans_completed": intent.get("total_plans_completed", 0),
        "plans_started": len(intent.get("plans", [])),
        "plan_history": AutonomousIntentState.get_plan_history(5),
        "progress": AutonomousIntentState.get_progress(),
    }
    
    return report
