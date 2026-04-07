"""Weslr CLI - Self-modification commands.

Commands moved here from main.py:
- SCI (Safe Capability Evolution) commands:
  - cmd_sci_observations_list, cmd_sci_observations_record
  - cmd_sci_proposals_create, cmd_sci_proposals_list
  - cmd_sci_proposals_approve, cmd_sci_proposals_deny
  - cmd_sci_apply, cmd_sci_status, cmd_sci_proposal_show, cmd_sci_proposal_rollback
- Self-evaluation commands:
  - cmd_self_eval, cmd_self_grow, cmd_self_speak

This module holds self-modification and capability evolution engine commands.
"""

from __future__ import annotations

import json
from pathlib import Path

from self_improvement_proposal import (
    create_proposal, list_proposals, approve_proposal, deny_proposal,
    get_proposal, build_proposal_report as build_sci_proposal_report, load_proposals
)
from self_improvement_apply import (
    apply_proposal, apply_proposal_with_tests, build_apply_report, rollback_proposal, load_apply_log
)
from self_improvement_observation import record_observation, list_observations, load_observations
from self_eval import run_self_evaluation, run_self_directed_growth, generate_self_speech


def emit(data):
    """Emit JSON to stdout."""
    print(json.dumps(data, indent=2))


def register_commands(subparsers):
    """Register self-modification command parsers."""
    
    # === Safe Capability Evolution Engine (SCI) ===
    sci_parser = subparsers.add_parser("sci", help="safe capability evolution engine commands")
    sci_sub = sci_parser.add_subparsers(dest="sci_cmd", required=True)

    # SCI observations
    sci_obs_list_parser = sci_sub.add_parser("observations-list", help="list recorded observations")
    sci_obs_list_parser.add_argument("--type", default="", help="filter by observation type")
    sci_obs_list_parser.add_argument("--source", default="", help="filter by source layer")
    sci_obs_list_parser.add_argument("--limit", type=int, default=50, help="max results")
    sci_obs_list_parser.set_defaults(func=cmd_sci_observations_list)

    sci_obs_record_parser = sci_sub.add_parser("observations-record", help="record a new observation")
    sci_obs_record_parser.add_argument("--type", required=True, help="observation type")
    sci_obs_record_parser.add_argument("--pattern", required=True, help="pattern description")
    sci_obs_record_parser.add_argument("--source", required=True, help="source layer")
    sci_obs_record_parser.set_defaults(func=cmd_sci_observations_record)

    # SCI proposals
    sci_prop_create_parser = sci_sub.add_parser("proposals-create", help="create a new improvement proposal")
    sci_prop_create_parser.add_argument("--observation-ids", default="", help="comma-separated observation IDs")
    sci_prop_create_parser.add_argument("--title", required=True, help="proposal title")
    sci_prop_create_parser.add_argument("--problem", default="", help="problem description")
    sci_prop_create_parser.add_argument("--likely-cause", default="", help="root cause analysis")
    sci_prop_create_parser.add_argument("--files", required=True, help="comma-separated files to change")
    sci_prop_create_parser.add_argument("--expected-benefit", default="", help="expected improvement")
    sci_prop_create_parser.add_argument("--risk-level", default="low", help="risk level: low|medium|high")
    sci_prop_create_parser.add_argument("--test-prompts", default="", help="JSON test prompts array")
    sci_prop_create_parser.add_argument("--rollback", default="", help="rollback shell command")
    sci_prop_create_parser.add_argument("--patch-plan", default="", help="JSON patch plan")
    sci_prop_create_parser.set_defaults(func=cmd_sci_proposals_create)

    sci_prop_list_parser = sci_sub.add_parser("proposals-list", help="list proposals")
    sci_prop_list_parser.add_argument("--status", default="", help="filter by status")
    sci_prop_list_parser.add_argument("--limit", type=int, default=50, help="max results")
    sci_prop_list_parser.set_defaults(func=cmd_sci_proposals_list)

    sci_prop_approve_parser = sci_sub.add_parser("proposals-approve", help="approve a proposal")
    sci_prop_approve_parser.add_argument("--proposal-id", required=True, help="proposal ID")
    sci_prop_approve_parser.add_argument("--by", default="human", help="approving entity")
    sci_prop_approve_parser.set_defaults(func=cmd_sci_proposals_approve)

    sci_prop_deny_parser = sci_sub.add_parser("proposals-deny", help="deny a proposal")
    sci_prop_deny_parser.add_argument("--proposal-id", required=True, help="proposal ID")
    sci_prop_deny_parser.add_argument("--reason", required=True, help="reason for denial")
    sci_prop_deny_parser.set_defaults(func=cmd_sci_proposals_deny)

    sci_apply_parser = sci_sub.add_parser("apply", help="apply an approved proposal with real tests")
    sci_apply_parser.add_argument("--proposal-id", required=True, help="proposal ID")
    sci_apply_parser.add_argument("--by", default="human", help="applying entity")
    sci_apply_parser.set_defaults(func=cmd_sci_apply)

    sci_status_parser = sci_sub.add_parser("status", help="show safe capability evolution engine status")
    sci_status_parser.set_defaults(func=cmd_sci_status)

    sci_prop_show_parser = sci_sub.add_parser("proposal-show", help="show detailed proposal info")
    sci_prop_show_parser.add_argument("--proposal-id", required=True, help="proposal ID")
    sci_prop_show_parser.set_defaults(func=cmd_sci_proposal_show)

    sci_prop_rollback_parser = sci_sub.add_parser("proposal-rollback", help="rollback an applied proposal")
    sci_prop_rollback_parser.add_argument("--proposal-id", required=True, help="proposal ID")
    sci_prop_rollback_parser.add_argument("--by", default="human", help="rolling back entity")
    sci_prop_rollback_parser.set_defaults(func=cmd_sci_proposal_rollback)

    # === Self-Evaluation Commands ===
    self_eval_parser = subparsers.add_parser("self-eval", help="run self-evaluation to identify gaps and opportunities")
    self_eval_parser.set_defaults(func=cmd_self_eval)

    self_grow_parser = subparsers.add_parser("self-grow", help="run full self-directed growth cycle")
    self_grow_parser.set_defaults(func=cmd_self_grow)

    self_speak_parser = subparsers.add_parser("self-speak", help="generate speech explaining Weslr's self-decisions")
    self_speak_parser.add_argument("--gaps", default="[]", help="gaps to speak about")
    self_speak_parser.set_defaults(func=cmd_self_speak)


# ============================================================================
# SCI Observation Commands
# ============================================================================

def cmd_sci_observations_list(args):
    """List recorded observations."""
    limit = args.limit or 50
    obs_type = args.type
    source = args.source

    result = list_observations(type=obs_type, source_layer=source, limit=limit)
    emit(result)

    if not result.get("ok"):
        print(f"\nError: {result.get('error', 'unknown error')}")
        return

    print(f"\n--- Observations ({result.get('total', 0)} found) ---")
    for obs in result.get("observations", []):
        print(f"[{obs.get('id')}] Type: {obs.get('type')}, Source: {obs.get('source_layer')}")
        print(f"  Pattern: {obs.get('pattern')}")
        print(f"  Count: {obs.get('count')}, Last: {obs.get('last_seen')}")


def cmd_sci_observations_record(args):
    """Record a new observation of repeated weakness."""
    obs_type = args.type
    pattern = args.pattern
    source = args.source

    if not obs_type or not pattern or not source:
        emit({"error": "Missing required fields: --type, --pattern, and --source are required."})
        return

    result = record_observation(type=obs_type, pattern=pattern, source_layer=source)

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n✅ Observation recorded: {result.get('observation_id')}")


# ============================================================================
# SCI Proposal Commands
# ============================================================================

def cmd_sci_proposals_create(args):
    """Create a new improvement proposal."""
    obs_ids = args.observation_ids.split(",") if args.observation_ids else []
    title = args.title
    problem = args.problem
    likely_cause = args.likely_cause
    files_to_change = args.files.split(",") if args.files else []
    expected_benefit = args.expected_benefit
    risk_level = args.risk_level or "low"
    test_prompts = args.test_prompts
    rollback = args.rollback
    patch_plan = args.patch_plan

    if not files_to_change or not title:
        emit({"error": "Missing required fields: --files and --title are required."})
        return

    # Parse test prompts as JSON if provided
    parsed_prompts = []
    if test_prompts:
        try:
            parsed_prompts = json.loads(test_prompts)
        except json.JSONDecodeError:
            emit({"error": "Invalid JSON in --test-prompts"})
            return

    # Parse rollback command
    rollback_cmd = None
    if rollback:
        rollback_cmd = rollback

    # Parse patch plan as JSON if provided
    parsed_patch = None
    if patch_plan:
        try:
            parsed_patch = json.loads(patch_plan)
        except json.JSONDecodeError:
            emit({"error": "Invalid JSON in --patch-plan"})
            return

    result = create_proposal(
        observation_ids=obs_ids,
        title=title,
        problem=problem or f"Proposed improvement: {title}",
        likely_cause=likely_cause or "Human analysis",
        files_to_change=files_to_change,
        expected_benefit=expected_benefit or "Self-improvement",
        risk_level=risk_level,
        test_prompts=parsed_prompts,
        rollback_command=rollback_cmd,
        patch_plan=parsed_patch,
    )

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n✅ Proposal created: {result.get('proposal_id')}")


def cmd_sci_proposals_list(args):
    """List proposals."""
    status = args.status
    limit = args.limit or 50

    result = load_proposals(status=status, limit=limit)
    emit(result)

    if not result.get("ok"):
        print(f"\nError: {result.get('error', 'unknown error')}")
        return

    print(f"\n--- Proposals ({result.get('total', 0)} found) ---")
    for prop in result.get("proposals", []):
        print(f"[{prop.get('id')}] {prop.get('title')} ({prop.get('status')})")
        print(f"  Files: {', '.join(prop.get('files_to_change', []))}")
        print(f"  Risk: {prop.get('risk_level')}, Benefit: {prop.get('expected_benefit', 'N/A')}")


def cmd_sci_proposals_approve(args):
    """Approve a proposal."""
    proposal_id = args.proposal_id
    approved_by = args.by

    result = approve_proposal(proposal_id=proposal_id, approved_by=approved_by)
    emit(result)

    if result.get("ok"):
        print(f"\n✅ Approved: {proposal_id} by {approved_by}")
    else:
        print(f"\n❌ Approval failed: {result.get('error', 'unknown error')}")


def cmd_sci_proposals_deny(args):
    """Deny a proposal."""
    proposal_id = args.proposal_id
    reason = args.reason

    result = deny_proposal(proposal_id=proposal_id, reason=reason)
    emit(result)

    if result.get("ok"):
        print(f"\n✅ Denied: {proposal_id} - {reason}")
    else:
        print(f"\n❌ Denial failed: {result.get('error', 'unknown error')}")


def cmd_sci_apply(args):
    """Apply an approved proposal with real tests."""
    proposal_id = args.proposal_id
    applied_by = args.by

    result = apply_proposal_with_tests(proposal_id=proposal_id, applied_by=applied_by)
    emit(result)

    if result.get("ok"):
        print(f"\n✅ Applied: {proposal_id} by {applied_by}")
        if result.get("tests_passed"):
            print(f"   Tests passed: {result.get('tests_passed')}")
        if result.get("tests_failed"):
            print(f"   Tests failed: {result.get('tests_failed')}")
    else:
        print(f"\n❌ Apply failed: {result.get('error', 'unknown error')}")


def cmd_sci_status(args):
    """Show safe capability evolution engine status."""
    proposals = load_proposals(status="active", limit=10)
    observations = list_observations(limit=10)
    apply_log = load_apply_log(limit=10)

    emit({
        "proposals_active": proposals.get("total", 0),
        "proposals": proposals.get("proposals", [])[:5],
        "observations_recent": observations.get("total", 0),
        "observations": observations.get("observations", [])[:5],
        "apply_log_last": len(apply_log.get("records", [])),
    })


def cmd_sci_proposal_show(args):
    """Show detailed proposal info."""
    proposal_id = args.proposal_id

    result = get_proposal(proposal_id=proposal_id)
    emit(result)

    if not result.get("ok"):
        print(f"\nError: {result.get('error', 'unknown error')}")
        return

    prop = result.get("proposal", {})
    print(f"\n--- Proposal: {prop.get('title')} ---")
    print(f"ID: {prop.get('id')}")
    print(f"Status: {prop.get('status')}")
    print(f"Files: {', '.join(prop.get('files_to_change', []))}")
    print(f"Problem: {prop.get('problem', 'N/A')}")
    print(f"Likely Cause: {prop.get('likely_cause', 'N/A')}")
    print(f"Expected Benefit: {prop.get('expected_benefit', 'N/A')}")
    print(f"Risk Level: {prop.get('risk_level', 'N/A')}")
    if prop.get("patch_plan"):
        print(f"Patch Plan: {json.dumps(prop.get('patch_plan'), indent=2)}")


def cmd_sci_proposal_rollback(args):
    """Rollback an applied proposal."""
    proposal_id = args.proposal_id
    rolled_back_by = args.by

    result = rollback_proposal(proposal_id=proposal_id, rolled_back_by=rolled_back_by)
    emit(result)

    if result.get("ok"):
        print(f"\n✅ Rolled back: {proposal_id} by {rolled_back_by}")
    else:
        print(f"\n❌ Rollback failed: {result.get('error', 'unknown error')}")


# ============================================================================
# Self-Evaluation Commands
# ============================================================================

def cmd_self_eval(args):
    """Run self-evaluation to identify gaps and opportunities."""
    result = run_self_evaluation()
    emit(result)
    if result.get("ok"):
        print(f"\nGaps: {result.get('gaps', [])}")
        print(f"Opportunities: {result.get('opportunities', [])}")


def cmd_self_grow(args):
    """Run full self-directed growth cycle."""
    result = run_self_directed_growth()
    emit(result)
    if result.get("ok"):
        print(f"\n✅ Growth cycle complete")
        print(f"New gaps: {result.get('new_gaps', [])}")
        print(f"New opportunities: {result.get('new_opportunities', [])}")


def cmd_self_speak(args):
    """Generate speech explaining Weslr's self-decisions."""
    gaps = args.gaps
    if gaps:
        try:
            gaps = json.loads(gaps)
        except json.JSONDecodeError:
            emit({"error": "Invalid JSON in --gaps"})
            return

    result = generate_self_speech(gaps=gaps)
    emit(result)
    if result.get("ok"):
        print(f"\n{result.get('speech', 'No speech generated')}")
