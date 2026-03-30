"""Weslr Safe Capability Evolution Engine - Chat Control Layer.

Phase 1: Minimal text-chat control for proposal workflows.
Direct Python function calls, explicit approval required.
"""

from __future__ import annotations

import time
from pathlib import Path

from self_improvement_proposal import load_proposals, get_proposal, approve_proposal, deny_proposal
from self_improvement_apply import apply_proposal_with_tests, build_apply_report
from self_improvement_observation import load_observations


BASE_DIR = Path(__file__).resolve().parent


def get_context_key() -> str:
    """Get the context storage key for current_proposal_id."""
    return "chat_state"


def load_chat_context(relationships: dict) -> dict:
    """Load chat context from relationships."""
    context = relationships.get(get_context_key(), {})
    if not isinstance(context, dict):
        context = {}
    return context


def save_chat_context(relationships: dict, context: dict) -> None:
    """Save chat context to relationships."""
    relationships[get_context_key()] = context


def get_current_proposal_id(relationships: dict) -> str | None:
    """Get current proposal ID from chat context."""
    context = load_chat_context(relationships)
    return context.get("current_proposal_id")


def set_current_proposal_id(relationships: dict, proposal_id: str | None) -> None:
    """Set current proposal ID in chat context."""
    context = load_chat_context(relationships)
    context["current_proposal_id"] = proposal_id
    context["last_intent"] = "show_proposal"
    context["last_intent_time"] = int(time.time() * 1000)
    save_chat_context(relationships, context)


def clear_current_proposal_id(relationships: dict) -> None:
    """Clear current proposal ID from chat context."""
    context = load_chat_context(relationships)
    context["current_proposal_id"] = None
    context["last_intent"] = None
    context["last_intent_time"] = None
    save_chat_context(relationships, context)


def parse_chat_intent(message: str, relationships: dict) -> dict:
    """Parse chat message into intent object.

    Args:
        message: User's chat message
        relationships: Current relationships state

    Returns:
        dict with intent details
    """
    msg = message.strip().lower()

    # Check for "show pending proposals"
    if "show pending" in msg and "proposals" in msg:
        return {
            "intent": "show_pending",
            "cli_action": "show_pending_proposals",
        }

    # Check for "show proposal <id>" pattern
    if "show proposal" in msg:
        # Extract proposal ID from message
        parts = message.split()
        for part in parts:
            if part.startswith("prop-"):
                return {
                    "intent": "show_proposal",
                    "proposal_id": part,
                    "cli_action": "show_proposal_by_id",
                }
        # No ID found - return error intent
        return {
            "intent": "error",
            "error": "no_proposal_id",
            "cli_action": "error_no_proposal_id",
        }

    # Check for "approve it"
    if msg == "approve it" or "approve it" in msg:
        current_id = get_current_proposal_id(relationships)
        if not current_id:
            return {
                "intent": "error",
                "error": "no_active_proposal",
                "cli_action": "error_no_active_proposal",
            }
        return {
            "intent": "approve_proposal",
            "proposal_id": current_id,
            "cli_action": "approve_proposal",
        }

    # Check for "deny it"
    if msg == "deny it" or "deny it" in msg:
        current_id = get_current_proposal_id(relationships)
        if not current_id:
            return {
                "intent": "error",
                "error": "no_active_proposal",
                "cli_action": "error_no_active_proposal",
            }
        return {
            "intent": "deny_proposal",
            "proposal_id": current_id,
            "cli_action": "deny_proposal",
        }

    # Check for "apply it"
    if msg == "apply it" or "apply it" in msg:
        current_id = get_current_proposal_id(relationships)
        if not current_id:
            return {
                "intent": "error",
                "error": "no_active_proposal",
                "cli_action": "error_no_active_proposal",
            }
        return {
            "intent": "apply_proposal",
            "proposal_id": current_id,
            "cli_action": "apply_proposal",
        }

    # Check for "show status"
    if msg == "show status" or "status" in msg:
        return {
            "intent": "show_status",
            "cli_action": "show_status",
        }

    # Unknown intent
    return {
        "intent": "unknown",
        "cli_action": "unknown",
    }


def execute_intent(intent: dict, relationships: dict, human_name: str = "human") -> dict:
    """Execute intent via direct Python function calls.

    Args:
        intent: Parsed intent object
        relationships: Current relationships state
        human_name: Name of human user

    Returns:
        dict with execution result
    """
    intent_type = intent.get("intent")

    if intent_type == "show_pending":
        proposals = load_proposals()
        # Show only "proposed" proposals (pending approval)
        # "approved" proposals should be applied, not shown in pending
        pending = [p for p in proposals if p.get("status") == "proposed"]
        return {
            "ok": True,
            "total": len(pending),
            "proposals": pending,
            "intent": "show_pending",
        }

    elif intent_type == "show_proposal":
        proposal_id = intent.get("proposal_id")
        prop = get_proposal(proposal_id)
        if not prop:
            return {
                "ok": False,
                "error": f"Proposal not found: {proposal_id}",
                "intent": "show_proposal",
            }
        # Set current proposal ID in context
        set_current_proposal_id(relationships, proposal_id)
        return {
            "ok": True,
            "proposal": prop,
            "intent": "show_proposal",
        }

    elif intent_type == "approve_proposal":
        proposal_id = intent.get("proposal_id")
        result = approve_proposal(proposal_id=proposal_id, approved_by=human_name)
        # Update current proposal ID to show new status
        set_current_proposal_id(relationships, proposal_id)
        return {
            "ok": result.get("ok"),
            "proposal_id": proposal_id,
            "status": result.get("status"),
            "intent": "approve_proposal",
            "result": result,
        }

    elif intent_type == "deny_proposal":
        proposal_id = intent.get("proposal_id")
        result = deny_proposal(proposal_id=proposal_id, reason="user request")
        # Update current proposal ID to show new status
        set_current_proposal_id(relationships, proposal_id)
        return {
            "ok": result.get("ok"),
            "proposal_id": proposal_id,
            "status": result.get("status"),
            "intent": "deny_proposal",
            "result": result,
        }

    elif intent_type == "apply_proposal":
        proposal_id = intent.get("proposal_id")
        result = apply_proposal_with_tests(proposal_id=proposal_id, applied_by=human_name)
        # Update current proposal ID to show new status
        set_current_proposal_id(relationships, proposal_id)
        return {
            "ok": result.get("ok"),
            "proposal_id": proposal_id,
            "status": result.get("status"),
            "all_tests_passed": result.get("all_tests_passed"),
            "intent": "apply_proposal",
            "result": result,
        }

    elif intent_type == "show_status":
        proposals = load_proposals()
        observations = load_observations()

        # Count by status
        status_counts = {
            "proposed": 0,
            "approved": 0,
            "applied": 0,
            "applied_with_failures": 0,
            "rolled_back": 0,
            "rejected": 0,
        }
        for p in proposals:
            status = p.get("status", "unknown")
            if status in status_counts:
                status_counts[status] += 1

        # Count observation types
        obs_types = {}
        for obs in observations:
            obs_type = obs.get("type")
            if obs_type:
                obs_types[obs_type] = obs_types.get(obs_type, 0) + 1

        return {
            "ok": True,
            "proposals": {
                "total": len(proposals),
                "by_status": status_counts,
            },
            "observations": {
                "total": len(observations),
                "types": obs_types,
            },
            "timestamp": int(time.time() * 1000),
            "intent": "show_status",
        }

    elif intent_type == "error":
        error_type = intent.get("error")
        if error_type == "no_active_proposal":
            return {
                "ok": False,
                "error": "No active proposal. Use 'show pending proposals' first.",
                "intent": "error",
            }
        elif error_type == "no_proposal_id":
            return {
                "ok": False,
                "error": "No proposal ID provided. Use format: 'show proposal prop-123'",
                "intent": "error",
            }
        else:
            return {
                "ok": False,
                "error": f"Unknown error: {error_type}",
                "intent": "error",
            }

    else:
        return {
            "ok": False,
            "error": f"Unknown intent: {intent_type}",
            "intent": "unknown",
        }


def format_response(result: dict, intent: dict) -> str:
    """Format result as natural language response.

    Args:
        result: Execution result
        intent: Original intent object

    Returns:
        Natural language response string
    """
    intent_type = intent.get("intent")

    if intent_type == "show_pending":
        total = result.get("total", 0)
        proposals = result.get("proposals", [])
        if total == 0:
            return "No pending proposals found."

        lines = [f"Found {total} pending proposal(s):"]
        for prop in proposals[:10]:  # Show first 10
            status = prop.get("status", "unknown")
            title = prop.get("title", "Untitled")
            pid = prop.get("id", "unknown")
            files = ", ".join(prop.get("files_to_change", []))
            lines.append(f"- [{pid}] {title} (status: {status})")
            if files:
                lines.append(f"  Files: {files}")
        return "\n".join(lines)

    elif intent_type == "show_proposal":
        if not result.get("ok"):
            return f"Error: {result.get('error', 'Unknown error')}"

        prop = result.get("proposal", {})
        pid = prop.get("id", "unknown")
        title = prop.get("title", "Untitled")
        status = prop.get("status", "unknown")
        problem = prop.get("problem", "N/A")
        files = ", ".join(prop.get("files_to_change", []))
        risk = prop.get("risk_level", "N/A")

        lines = [
            f"📋 Proposal: {title}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"ID: {pid}",
            f"Status: {status}",
            f"Files: {files}",
            f"Risk: {risk}",
            f"Problem: {problem}",
        ]

        # Add test info if present
        test_prompts = prop.get("test_prompts", [])
        if test_prompts:
            lines.append("Tests:")
            for i, test in enumerate(test_prompts):
                prompt = test.get("prompt", "N/A")
                exp_type = test.get("expected_type", "N/A")
                lines.append(f"  {i+1}. {prompt} (type: {exp_type})")

        # Add rollback command if present
        rollback = prop.get("rollback_command")
        if rollback:
            lines.append(f"Rollback: {rollback}")

        # Status-aware action hints
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        status = prop.get("status", "unknown")
        if status == "proposed":
            lines.append("Available actions: [approve it] [deny it]")
        elif status == "approved":
            lines.append("Available actions: [apply it] [deny it]")
        elif status == "applied_with_failures":
            lines.append("Status: applied_with_failures")
            lines.append("Rollback guidance: See rollback_command above")
            lines.append("Note: Tests failed after apply. Execute rollback manually.")
        elif status == "applied":
            lines.append("Status: applied")
            lines.append("Note: Proposal successfully applied.")
        else:
            lines.append(f"Unknown status: {status}")
        return "\n".join(lines)

    elif intent_type in ("approve_proposal", "deny_proposal", "apply_proposal"):
        if not result.get("ok"):
            return f"Error: {result.get('error', 'Unknown error')}"

        status = result.get("status", "unknown")
        pid = result.get("proposal_id", "unknown")

        if intent_type == "approve_proposal":
            return f"✅ Proposal approved: {pid}\nStatus: {status}"
        elif intent_type == "deny_proposal":
            return f"❌ Proposal denied: {pid}\nStatus: {status}"
        elif intent_type == "apply_proposal":
            all_passed = result.get("all_tests_passed", False)
            if all_passed:
                return f"✅ Proposal applied successfully: {pid}\nStatus: {status}"
            else:
                failing = result.get("result", {}).get("failing_tests", [])
                return f"⚠️  Proposal applied with failures: {pid}\nStatus: {status}\nFailing tests: {failing}"

    elif intent_type == "show_status":
        if not result.get("ok"):
            return f"Error: {result.get('error', 'Unknown error')}"

        proposals = result.get("proposals", {})
        obs = result.get("observations", {})

        lines = [
            "--- Safe Capability Evolution Engine Status ---",
            f"Observations recorded: {obs.get('total', 0)}",
        ]
        for obs_type, count in obs.get("types", {}).items():
            lines.append(f"  - {obs_type}: {count}")

        lines.append(f"\nProposals: {proposals.get('total', 0)} total")
        lines.append("  By status:")
        for status, count in proposals.get("by_status", {}).items():
            if count > 0:
                lines.append(f"    - {status}: {count}")

        return "\n".join(lines)

    elif intent_type == "error":
        return result.get("error", "Unknown error")

    else:
        return "I didn't understand that. Try 'show pending proposals' to see available proposals."


def handle_chat_intent(message: str, relationships: dict, human_name: str = "human") -> tuple[dict, str]:
    """Handle chat intent: parse, execute, format response.

    Args:
        message: User's chat message
        relationships: Current relationships state
        human_name: Name of human user

    Returns:
        Tuple of (intent object, natural language response)
    """
    intent = parse_chat_intent(message, relationships)
    result = execute_intent(intent, relationships, human_name)
    response = format_response(result, intent)
    return intent, response
