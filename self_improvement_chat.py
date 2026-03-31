"""Weslr Safe Capability Evolution Engine - Chat Control Layer.

Phase 1: Minimal text-chat control for proposal workflows.
Direct Python function calls, explicit approval required.
"""

from __future__ import annotations

import time
from pathlib import Path

from self_improvement_proposal import load_proposals, get_proposal, approve_proposal, deny_proposal, create_proposal
from self_improvement_apply import apply_proposal_with_tests, build_apply_report
from self_improvement_observation import load_observations
from proactive_state import load_proactive_state, save_proactive_state, load_cooldowns, save_cooldowns, get_pattern_key


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


def parse_chat_intent(message: str, relationships: dict, proactive: dict | None = None) -> dict:
    """Parse chat message into intent object.

    Args:
        message: User's chat message
        relationships: Current relationships state
        proactive: Proactive pattern info (optional, for yes/no responses)

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

    # Check for "show failing proposals"
    if msg == "show failing proposals" or ("failing" in msg and "proposals" in msg):
        return {
            "intent": "show_failing",
            "cli_action": "show_failing",
        }

    # Check for "show rollback guidance for prop-123" (specific, must be first)
    if "show rollback guidance for" in msg:
        parts = message.split()
        for part in parts:
            if part.startswith("prop-"):
                return {
                    "intent": "show_rollback_for_id",
                    "proposal_id": part,
                    "cli_action": "show_rollback_for_id",
                }
        return {
            "intent": "error",
            "error": "no_proposal_id",
            "cli_action": "error_no_proposal_id",
        }
    
    # Check for "rollback guidance for prop-123" (alternative, must be before generic rollback guidance)
    if "rollback guidance for" in msg:
        parts = message.split()
        for part in parts:
            if part.startswith("prop-"):
                return {
                    "intent": "show_rollback_for_id",
                    "proposal_id": part,
                    "cli_action": "show_rollback_for_id",
                }
        return {
            "intent": "error",
            "error": "no_proposal_id",
            "cli_action": "error_no_proposal_id",
        }

    # Check for "show rollback guidance" (generic, no specific ID)
    if msg == "show rollback guidance" or ("rollback" in msg and "guidance" in msg and "for" not in msg):
        current_id = get_current_proposal_id(relationships)
        return {
            "intent": "show_rollback",
            "proposal_id": current_id,
            "cli_action": "show_rollback",
        }
    
    # Check for proactive "yes" response (explicit consent to create proposal)
    if msg in ("yes", "yes show it", "show it", "prepare it", "create it", "approve"):
        return {
            "intent": "proactive_approve",
            "cli_action": "proactive_approve",
            "proactive": proactive,
        }
    
    # Check for proactive "no" response (deny pattern)
    if msg in ("no", "no thank you", "no thanks", "deny", "don't", "never mind"):
        return {
            "intent": "proactive_deny",
            "cli_action": "proactive_deny",
            "proactive": proactive,
        }

    # Unknown intent
    return {
        "intent": "unknown",
        "cli_action": "unknown",
    }


def execute_intent(intent: dict, relationships: dict, human_name: str = "human", proactive: dict | None = None) -> dict:
    """Execute intent via direct Python function calls.

    Args:
        intent: Parsed intent object
        relationships: Current relationships state
        human_name: Name of human user
        proactive: Proactive pattern info (optional, for proactive intents)

    Returns:
        dict with execution result
    """
    # If proactive data is provided in intent, prefer that
    if not proactive and intent.get("proactive"):
        proactive = intent.get("proactive")
    
    intent_type = intent.get("intent")

    if intent_type == "show_pending":
        proposals = load_proposals()
        # Show only "proposed" proposals (pending approval)
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

    elif intent_type in ("show_failing", "show_rollback", "show_rollback_for_id"):
        if intent_type == "show_failing":
            proposals = load_proposals()
            # Filter to applied_with_failures status
            failing = [p for p in proposals if p.get("status") == "applied_with_failures"]
            return {
                "ok": True,
                "total": len(failing),
                "proposals": failing,
                "intent": "show_failing",
            }

        elif intent_type == "show_rollback":
            # For "show rollback guidance" without specific ID, show error
            proposal_id = intent.get("proposal_id")
            if not proposal_id:
                return {
                    "ok": False,
                    "error": "No active proposal. Use 'show pending proposals' first.",
                    "intent": intent_type,
                }
            prop = get_proposal(proposal_id)
            if not prop:
                return {
                    "ok": False,
                    "error": f"Proposal not found: {proposal_id}",
                    "intent": intent_type,
                }
            return {
                "ok": True,
                "proposal": prop,
                "intent": intent_type,
            }

        elif intent_type == "show_rollback_for_id":
            proposal_id = intent.get("proposal_id")
            prop = get_proposal(proposal_id)
            if not prop:
                return {
                    "ok": False,
                    "error": f"Proposal not found: {proposal_id}",
                    "intent": intent_type,
                }
            return {
                "ok": True,
                "proposal": prop,
                "intent": intent_type,
            }

    elif intent_type in ("proactive_approve", "proactive_deny"):
        # Proactive intent handlers require proactive pattern data
        proactive = intent.get("proactive")
        if not proactive:
            return {
                "ok": False,
                "error": "No proactive pattern available.",
                "intent": intent_type,
            }
        
        if intent_type == "proactive_approve":
            # Create proposal using existing create_proposal
            result = create_proposal(
                observation_ids=proactive.get("observation_ids", []),
                title=f"Fix: {proactive.get('pattern', 'repeated weakness')}",
                problem=f"Repeated occurrence of: {proactive.get('pattern', 'weakness')}",
                likely_cause="Pattern detected in repeated observations",
                files_to_change=[],
                expected_benefit=f"Reduce {proactive.get('pattern', 'repeated weakness')} by implementing automated fix",
                risk_level="low",
                rollback_command=None,
            )
            
            # Mark as surfaced
            from proactive_state import set_surfaced_pattern
            set_surfaced_pattern(proactive.get("pattern"), proactive.get("source_layer"))
            
            return {
                "ok": result.get("ok"),
                "proposal_id": result.get("proposal_id"),
                "status": "proposed",
                "intent": "proactive_approve",
            }
        
        elif intent_type == "proactive_deny":
            # Record denial in cooldown
            from proactive_state import set_denied_pattern, get_pattern_key
            pattern = proactive.get("pattern")
            source = proactive.get("source_layer")
            if pattern and source:
                set_denied_pattern(pattern, source)
            return {
                "ok": True,
                "pattern": pattern,
                "source_layer": source,
                "intent": "proactive_deny",
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


def format_response(result: dict, intent: dict, proactive: dict | None = None) -> str:
    """Format result as natural language response.

    Args:
        result: Execution result
        intent: Original intent object
        proactive: Proactive pattern info (optional, for proactive messages)

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

    elif intent_type in ("show_failing", "show_rollback", "show_rollback_for_id"):
        if intent_type == "show_failing":
            total = result.get("total", 0)
            proposals = result.get("proposals", [])
            if total == 0:
                return "No failing proposals found."
            lines = [f"Found {total} failing proposal(s):"]
            for prop in proposals:
                pid = prop.get("id", "unknown")
                title = prop.get("title", "Untitled")
                status = prop.get("status", "unknown")
                lines.append(f"- [{pid}] {title} (status: {status})")
            return "\n".join(lines)

        elif intent_type in ("show_rollback", "show_rollback_for_id"):
            if not result.get("ok"):
                return f"Error: {result.get('error', 'Unknown error')}"
            prop = result.get("proposal", {})
            pid = prop.get("id", "unknown")
            title = prop.get("title", "Untitled")
            status = prop.get("status", "unknown")
            rollback_cmd = prop.get("rollback_command")
            checkpoints = prop.get("checkpoint_names", [])

            if not rollback_cmd:
                return f"Proposal {pid}: No rollback command available."

            lines = [
                f"📋 Rollback Guidance for: {title}",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"Proposal ID: {pid}",
                f"Status: {status}",
                f"Rollback Command: {rollback_cmd}",
            ]

            if checkpoints:
                lines.append("Checkpoints Available:")
                for cp in checkpoints:
                    lines.append(f"  - {cp}")

            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("Note: Execute rollback command manually.")
            return "\n".join(lines)

    elif intent_type == "error":
        return result.get("error", "Unknown error")
    
    elif intent_type in ("proactive_approve", "proactive_deny"):
        if intent_type == "proactive_approve":
            if result.get("ok"):
                pid = result.get("proposal_id", "unknown")
                return f"✅ Proposal created: {pid}\nStatus: proposed\n\nYou must explicitly say 'approve it' to approve, and 'apply it' to apply."
            else:
                return f"Error creating proposal: {result.get('error', 'Unknown error')}"
        elif intent_type == "proactive_deny":
            return "Got it. Won't surface this pattern for 24h."
    
    # Proactive message - only if we have proactive data and no other response
    if proactive and proactive.get("pattern"):
        pattern = proactive.get("pattern")
        count = proactive.get("count", 0)
        source = proactive.get("source_layer", "")
        source_display = source if source else "the system"
        
        # Natural, helpful wording - vary phrasing based on pattern type
        pattern_lower = pattern.lower()
        
        if "fallback" in pattern_lower:
            return f"I think I've been hitting the same fallback weakness a few times. I can prepare a safe proposal to fix it. Want me to show it?"
        elif "concept mismatch" in pattern_lower or "concept" in pattern_lower:
            return f"I seem to be repeating the same kind of concept mismatch. I can draft a bounded fix proposal if you want."
        elif "user dissatisf" in pattern_lower or "dissatisf" in pattern_lower:
            return f"It looks like I've been missing the mark on your questions a few times. I can put together a proposal to improve this. Want me to show it?"
        elif "generic" in pattern_lower or "generic response" in pattern_lower:
            return f"I think I've been giving too many generic answers lately. I can draft a proposal to make my responses more helpful. Want me to show it?"
        else:
            # Generic but still improved
            return f"I've been hitting the same pattern in {source_display} a few times. I can prepare a safe proposal to fix it. Want me to show it?"
    
    else:
        return "I didn't understand that. Try 'show pending proposals' to see available proposals."


def find_proactive_pattern(relationships: dict) -> dict | None:
    """Find a qualifying proactive pattern to surface.
    
    Returns pattern info dict if found, None otherwise.
    
    Criteria:
    - Same pattern observed 3+ times
    - First occurrence > 1 hour ago
    - No active proposal for this pattern
    - Not in cooldown (not denied in 24h)
    - User hasn't disabled proactive
    - Not recently surfaced
    """
    now = int(time.time())  # Current time in seconds
    
    # Load data
    observations = load_observations()
    proposals = load_proposals()
    state = load_proactive_state()
    cooldowns = load_cooldowns()
    
    # Check if user disabled
    chat_settings = relationships.get("chat_settings", {})
    if chat_settings.get("auto_proposal_disabled"):
        return None
    
    # Group observations by pattern + source_layer
    pattern_counts = {}
    for obs in observations:
        pattern = obs.get("pattern", "")
        source = obs.get("source_layer", "")
        if not pattern or not source:
            continue
        key = get_pattern_key(pattern, source)
        if key not in pattern_counts:
            pattern_counts[key] = {
                "pattern": pattern,
                "source_layer": source,
                "count": 0,
                "first_seen": obs.get("created_at", 0),
                "observation_ids": []
            }
        pattern_counts[key]["count"] += 1
        pattern_counts[key]["observation_ids"].append(obs.get("id"))
    
    # Filter for qualifying patterns
    for key, info in pattern_counts.items():
        # Check count >= 3
        if info["count"] < 3:
            continue
        
        # Convert first_seen from milliseconds to seconds if needed
        first_seen = info["first_seen"]
        if first_seen > 10000000000:  # Approximate Unix timestamp in milliseconds
            first_seen = first_seen // 1000  # Convert ms to seconds
        
        # Check first occurrence > 1 hour ago
        if (now - first_seen) < 3600:
            continue
        
        # Check not recently surfaced
        if key in state.get("last_surfaced_patterns", {}):
            last_time = state["last_surfaced_patterns"][key]
            if (now - last_time) < 86400:  # 24h cooldown in seconds
                continue
        
        # Check not in cooldown (denied in 24h)
        if key in cooldowns:
            last_denial = cooldowns[key]
            if (now - last_denial) < 86400:
                continue
        
        # Check no active proposal for this pattern
        found_proposal = False
        for prop in proposals:
            obs_ids = prop.get("observation_ids", [])
            if set(info["observation_ids"]).intersection(set(obs_ids)):
                found_proposal = True
                break
        if found_proposal:
            continue
        
        # Found a qualifying pattern
        return {
            "pattern": info["pattern"],
            "source_layer": info["source_layer"],
            "count": info["count"],
            "observation_ids": info["observation_ids"]
        }
    
    return None


def handle_chat_intent(message: str, relationships: dict, human_name: str = "human") -> tuple[dict, str]:
    """Handle chat intent: parse, execute, format response.

    Args:
        message: User's chat message
        relationships: Current relationships state
        human_name: Name of human user

    Returns:
        Tuple of (intent object, natural language response)
    """
    # Check for proactive pattern to surface
    proactive = find_proactive_pattern(relationships)
    
    intent = parse_chat_intent(message, relationships, proactive=proactive)
    if proactive:
        intent["proactive"] = proactive
    result = execute_intent(intent, relationships, human_name, proactive=proactive)
    response = format_response(result, intent, proactive=proactive)
    
    # If we created a proactive proposal, mark it as surfaced
    if proactive and result.get("intent") == "proactive_approve":
        from proactive_state import set_surfaced_pattern
        set_surfaced_pattern(proactive["pattern"], proactive["source_layer"])
    
    return intent, response
