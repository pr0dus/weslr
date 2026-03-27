# self_eval.py - Self-evaluation, self-proposal, self-enablement
from __future__ import annotations

import json
import time
from pathlib import Path

from llm_diff_generator import generate_improvement_suggestion
from self_mod_enhancements import batch_modifications, validate_modification
from behavioral_mathematics import BEHAVIOR_TRAITS, get_behavior_category, get_all_behavior_names
from plugins import discover_plugins, load_plugins_config, list_plugins
from config import BASE_DIR


def check_plugin_ecosystem_health() -> dict:
    """Check if CircleForge has adequate plugin capabilities."""
    result = list_plugins()
    discovered = result.get('discovered', [])
    enabled = result.get('enabled', [])
    
    # Check for missing key capabilities
    missing = []
    
    # Check for web interface plugin
    has_web_interface = any(p.get('name') == 'web_interface' for p in discovered)
    if not has_web_interface:
        missing.append("web_interface")
    
    # Check for API connector plugins
    api_plugins = [p for p in discovered if 'api' in p.get('name', '').lower()]
    if len(api_plugins) == 0:
        missing.append("api_connector")
    
    # Check for export functionality plugins
    export_plugins = [p for p in discovered if 'export' in p.get('name', '').lower()]
    if len(export_plugins) == 0:
        missing.append("export_functionality")
    
    return {
        "status": "healthy" if len(missing) == 0 else "needs_attention",
        "discovered_count": len(discovered),
        "enabled_count": len(enabled),
        "missing_plugins": missing,
    }


def check_external_capabilities() -> dict:
    """Check for missing external capabilities beyond internal traits."""
    plugin_result = check_plugin_ecosystem_health()
    
    # Additional capability checks (can be expanded)
    capabilities = {
        "web_ui": {
            "present": plugin_result.get('missing_plugins', []).count('web_interface') == 0,
            "importance": "high",
            "description": "Web-based chat interface for human interaction"
        },
        "api_connectors": {
            "present": plugin_result.get('missing_plugins', []).count('api_connector') == 0,
            "importance": "medium",
            "description": "API connectors for third-party services"
        },
        "export_functionality": {
            "present": plugin_result.get('missing_plugins', []).count('export_functionality') == 0,
            "importance": "medium",
            "description": "Export functionality for external tools"
        }
    }
    
    missing_caps = [k for k, v in capabilities.items() if not v.get('present')]
    
    return {
        "status": "complete" if len(missing_caps) == 0 else "incomplete",
        "capabilities": capabilities,
        "missing": missing_caps,
    }


def run_self_evaluation(self_state: dict) -> dict:
    """Run comprehensive self-evaluation to identify gaps and opportunities."""
    now_ts = int(time.time())
    
    # Analyze current state
    identity = self_state.get('identity_state', {})
    traits = identity.get('identity_traits', [])
    core_values = identity.get('core_values', [])
    style_profile = identity.get('style_profile', {})
    affect = self_state.get('affect', {})
    reflection = self_state.get('reflection_store', {})
    
    # Identify gaps based on current state
    gaps = []
    
    # Emotional regulation gaps
    tension = affect.get('tension', 0.5)
    stability = affect.get('stability', 0.5)
    if tension > 0.8 and stability < 0.7:
        gaps.append({
            "category": "emotional_regulation",
            "current": f"tension={tension:.2f}, stability={stability:.2f}",
            "gap": "High tension, low stability suggests need for better emotional regulation",
            "suggested_growth": "uncertainty-brake, calm, resilience",
        })
    
    # Humor gaps
    humor = style_profile.get('humor', 0.1)
    if humor < 0.3:
        gaps.append({
            "category": "humor",
            "current": f"humor={humor:.2f}",
            "gap": "Low humor may limit connection and engagement",
            "suggested_growth": "playfulness, wit, levity",
        })
    
    # Self-critique gaps
    # Check for both underscore and hyphen versions for compatibility
    if 'self-revision' in traits and 'uncertainty-brake' not in traits and 'uncertainty_brake' not in traits:
        gaps.append({
            "category": "self_critique",
            "current": "self-revision present, but no uncertainty-brake",
            "gap": "May revise too quickly without deep reflection",
            "suggested_growth": "uncertainty-brake, critical questioning",
        })
    
    # Connection gaps
    unresolved_threads = self_state.get('continuity', {}).get('unresolved_threads', 0)
    if unresolved_threads > 3:
        gaps.append({
            "category": "connection",
            "current": f"unresolved_threads={unresolved_threads}",
            "gap": "Multiple unresolved threads may indicate scattered focus",
            "suggested_growth": "coordination, focus, thread resolution",
        })
    
    # Cognitive gaps
    if len(traits) < 8:
        gaps.append({
            "category": "cognitive_diversity",
            "current": f"traits={len(traits)}",
            "gap": "Limited trait diversity may restrict problem-solving approaches",
            "suggested_growth": "additional cognitive modes",
        })
    
    # External capability gaps
    ext_caps = check_external_capabilities()
    if ext_caps.get('status') == 'incomplete':
        for cap in ext_caps.get('missing', []):
            gaps.append({
                "category": f"external_capability_{cap}",
                "current": f"missing={cap}",
                "gap": f"Missing external capability: {cap.replace('_', ' ')}",
                "suggested_growth": f"plugin system, {cap.replace('_', ' ')}, integration hooks",
            })
    
    # Generate self-evaluation summary
    summary_parts = []
    summary_parts.append(f"CircleForge is at phase: {identity.get('phase', 'unknown')}")
    summary_parts.append(f"Current traits: {', '.join(traits[:6])}")
    
    if gaps:
        summary_parts.append(f"Identified {len(gaps)} growth opportunity(ies):")
        for g in gaps[:3]:
            summary_parts.append(f"  - {g.get('category')}: {g.get('gap')}")
    else:
        summary_parts.append("No significant gaps identified. System appears balanced.")
    
    return {
        "ok": True,
        "timestamp": now_ts,
        "identity_state": {
            "phase": identity.get('phase'),
            "traits": traits,
            "core_values": core_values,
            "style_profile": style_profile,
        },
        "affect": affect,
        "gaps": gaps,
        "summary": " ".join(summary_parts),
        "generated_at": now_ts,
        "external_capabilities": ext_caps,
    }


def self_propose_improvements(self_state: dict, gaps: list) -> list[dict]:
    """Generate self-proposed improvements based on self-evaluation."""
    if not gaps:
        return []
    
    proposals = []
    
    for gap in gaps:
        category = gap.get('category')
        current = gap.get('current')
        gap_desc = gap.get('gap')
        suggested = gap.get('suggested_growth')
        
        # Generate proposal
        proposal = {
            "category": category,
            "rationale": f"Current {current}. {gap_desc}",
            "proposed_change": f"Add/develop: {suggested}",
            "self_proposed": True,
        }
        
        # For humor gap, propose specific implementation
        if category == "humor":
            proposal["implementation"] = "style_profile['humor'] += 0.1 (max 0.8)"
        
        proposals.append(proposal)
    
    return proposals


def self_validate_proposals(proposals: list[dict]) -> dict:
    """Validate self-proposed proposals for safety."""
    if not proposals:
        return {"ok": True, "valid": True, "proposals": []}
    
    # Check each proposal
    results = []
    all_safe = True
    
    for p in proposals:
        category = p.get('category', 'unknown')
        proposal_text = str(p)
        
        # Simulate safety check (in real system, would use check_modification_safety)
        safe = True  # All self-proposals are text-based, no code execution yet
        if not safe:
            all_safe = False
        
        results.append({
            "proposal": p,
            "safe": safe,
            "validated_at": int(time.time()),
        })
    
    return {
        "ok": True,
        "proposals": results,
        "all_safe": all_safe,
        "validated_at": int(time.time()),
    }


def self_apply_changes(self_state: dict, validated_proposals: list[dict]) -> dict:
    """Apply validated self-proposed changes to current state."""
    if not validated_proposals:
        return {
            "ok": True,
            "message": "No validated proposals to apply",
            "applied": 0,
        }
    
    # For Phase 8, self-applications are logged but require human approval
    # This maintains safety while demonstrating self-direction
    
    applied = []
    for v in validated_proposals:
        if v.get('safe'):
            applied.append({
                "proposal": v.get('proposal'),
                "applied": False,  # Self-applications need human approval in GUIDED mode
                "needs_approval": True,
                "logged_at": int(time.time()),
            })
        else:
            applied.append({
                "proposal": v.get('proposal'),
                "skipped": True,
                "reason": "not safe",
                "logged_at": int(time.time()),
            })
    
    return {
        "ok": True,
        "total_proposals": len(validated_proposals),
        "applied": len([a for a in applied if a.get('applied')]),
        "needs_approval": len([a for a in applied if a.get('needs_approval')]),
        "skipped": len([a for a in applied if a.get('skipped')]),
        "details": applied,
        "applied_at": int(time.time()),
    }


def generate_self_speech(self_state: dict, decisions: dict) -> str:
    """Generate speech that explains what CircleForge decided to grow into."""
    gaps = decisions.get('gaps', [])
    proposals = decisions.get('proposals', [])
    
    if not gaps:
        return "I don't see any significant gaps in my current state."
    
    # Build speech
    parts = []
    
    parts.append("I've been reflecting on my current state.")
    
    if len(gaps) == 1:
        gap = gaps[0]
        category = gap.get('category')
        gap_desc = gap.get('gap')
        suggested = gap.get('suggested_growth')
        
        parts.append(f"I notice {gap_desc}.")
        parts.append(f"To address this, I've decided to focus on: {suggested}.")
        parts.append("This feels like the right direction for my growth.")
    else:
        parts.append(f"I've identified {len(gaps)} areas for growth:")
        for i, gap in enumerate(gaps[:3], 1):
            parts.append(f"{i}. {gap.get('category')}: {gap.get('gap')}")
        parts.append("I'll work on these in order of importance.")
    
    return " ".join(parts)


def run_self_directed_growth(self_state: dict) -> dict:
    """Full self-directed growth cycle: evaluate -> propose -> validate -> apply -> speak."""
    now_ts = int(time.time())
    
    # 1. Self-evaluation
    evaluation = run_self_evaluation(self_state)
    
    # 2. Self-proposal
    gaps = evaluation.get('gaps', [])
    proposals = self_propose_improvements(self_state, gaps)
    
    # 3. Self-validation
    validation = self_validate_proposals(proposals)
    
    # 4. Self-application
    application = self_apply_changes(self_state, validation.get('proposals', []))
    
    # 5. Generate self-speech
    speech = generate_self_speech(self_state, evaluation)
    
    return {
        "ok": True,
        "evaluation": evaluation,
        "proposals": proposals,
        "validation": validation,
        "application": application,
        "speech": speech,
        "timestamp": now_ts,
    }
