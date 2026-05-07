"""
weslr/commands/weight_commands.py

CLI for WESLR cognitive weight management.

Usage:
  python3 weslr/weight_commands.py status
  python3 weslr/weight_commands.py list [--group <group>]
  python3 weslr/weight_commands.py diff
  python3 weslr/weight_commands.py proposals [--status <status>]
  python3 weslr/weight_commands.py propose --key <key> --value <value> --reason <reason>
  python3 weslr/weight_commands.py simulate --key <key> --value <value>
  python3 weslr/weight_commands.py approve --proposal <id>
  python3 weslr/weight_commands.py reject --proposal <id>
  python3 weslr/weight_commands.py apply --proposal <id>
  python3 weslr/weight_commands.py reset --key <key>
  python3 weslr/weight_commands.py reset-all
"""

import argparse
import os
import sys
import tempfile

# Add parent of weslr/ to path for imports
_weslr_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _weslr_root)

from weslr.cognitive_weights import load_registry, CognitiveWeightRegistry, default_store_path
from weslr.weight_proposal import (
    load_proposals, save_proposal, update_proposal_status,
    WeightUpdateProposal,
)
from weslr.weight_simulation import run_simulation, save_simulation, SimulationResult
from weslr.weight_observation import load_observations, append_observation, WeightObservation

# ── Colour ─────────────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"


def colour(text: str, code: str) -> str:
    return f"{code}{text}{RESET}"


def section(title: str) -> None:
    print(f"\n{BOLD}{'=' * 56}{RESET}")
    print(f"{BOLD}{title}{RESET}")


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_status(_args: argparse.Namespace) -> None:
    """Show current registry status."""
    from weslr.cognitive_weights import GLOBAL_AUTO_APPLY_ENABLED
    registry = load_registry()
    diff = registry.diff_from_defaults()

    # Count by zone
    green = sum(1 for w in registry.weights.values() if w.zone == "green")
    yellow = sum(1 for w in registry.weights.values() if w.zone == "yellow")
    red = sum(1 for w in registry.weights.values() if w.zone == "red")
    print(f"\n{BOLD}Registry status{RESET}")
    print(f"  Total weights: {len(registry.weights)}")
    print(f"  Zones: {GREEN}green={green}{RESET}  {YELLOW}yellow={yellow}{RESET}  {RED}red={red}{RESET}")
    print(f"  Modified from default: {len(diff)}")
    print(f"  Store: {default_store_path()}")
    auto_status = colour("ENABLED", GREEN) if GLOBAL_AUTO_APPLY_ENABLED else colour("DISABLED", RED)
    print(f"  Global auto-apply: {auto_status}")
    if diff:
        print(f"\n{YELLOW}Modified weights:{RESET}")
        for k, d in diff.items():
            print(f"  {k}: {d['default']} → {d['current']}  ({d['delta']:+.4f})  [{d['reason']}]")
    else:
        print(f"\n{GREEN}All weights at default.{RESET}")


def cmd_list(args: argparse.Namespace) -> None:
    """List weights, optionally filtered by group prefix."""
    registry = load_registry()
    group = getattr(args, "group", None)
    printed_header = False
    for key, w in registry.weights.items():
        if group and not key.startswith(group):
            continue
        if not printed_header:
            section(f"Weight group: {group or 'all'}")
            printed_header = True
        zone_col = {"green": GREEN, "yellow": YELLOW, "red": RED}.get(w.zone, "")
        zone_str = colour(w.zone.upper(), zone_col)
        lock_str = colour(" [LOCKED]", RED) if w.locked else ""
        auto_str = colour(" auto", GREEN) if w.auto_apply_allowed else ""
        marker = ""
        if abs(w.value - w.default_value) > 1e-9:
            marker = colour(" *", YELLOW)
        print(f"  {key}{marker}{lock_str}{auto_str}")
        print(f"    value={w.value}  default={w.default_value}  range=[{w.min_value}, {w.max_value}]")
        print(f"    zone={zone_str}  auto_apply={w.auto_apply_allowed}  max_auto_delta={w.max_auto_delta}  max_manual_delta={w.max_manual_delta}")
        print(f"    {w.description}")
        if w.last_updated:
            print(f"    {DIM}updated={w.last_updated}  reason={w.update_reason or '-'}{RESET}")


def cmd_diff(_args: argparse.Namespace) -> None:
    """Show weights that differ from defaults."""
    registry = load_registry()
    diff = registry.diff_from_defaults()
    if not diff:
        print(f"{GREEN}No weights differ from defaults.{RESET}")
        return
    section("Weights differing from defaults")
    for k, d in diff.items():
        sign = "+" if d["delta"] > 0 else ""
        print(f"  {k}")
        print(f"    {d['default']} → {d['current']}  ({sign}{d['delta']:.4f})")
        print(f"    reason: {d['reason'] or '(none)'}")


def cmd_proposals(args: argparse.Namespace) -> None:
    """List proposals, optionally filtered by status, with guardrail analysis."""
    from weslr.cognitive_weights import check_weight_update_guardrails
    status_filter = getattr(args, "status", None)
    proposals = load_proposals(status=status_filter)
    if not proposals:
        print(f"{DIM}No proposals found.{RESET}")
        return
    section(f"Proposals{(' — ' + status_filter) if status_filter else ''}")
    for p in proposals:
        colour_code = GREEN if p.status == "approved" else (
            RED if p.status == "rejected" else YELLOW)
        status_str = colour(p.status.upper(), colour_code)
        print(f"\n  [{p.proposal_id}] {status_str}  {p.weight_key}")
        print(f"    {p.old_value} → {p.proposed_value}  ({p.delta:+.4f})")
        print(f"    reason: {p.reason[:80]}")
        print(f"    benefit: {p.expected_benefit[:80]}")
        print(f"    risk: {p.possible_risk[:80]}")
        if p.decided_by:
            print(f"    {DIM}decided by {p.decided_by} at {p.decided_at}{RESET}")

        # Guardrail analysis (show for all non-applied, non-rejected proposals)
        if p.status in ("proposed", "approved"):
            registry = load_registry()
            guard = check_weight_update_guardrails(
                registry, p, mode="manual", proposal_status=p.status)
            zone_col = {"green": GREEN, "yellow": YELLOW, "red": RED}.get(guard.zone, "")
            zone_str = colour(f"zone={guard.zone}", zone_col)

            # Manual-apply assessment
            if p.status == "approved" and guard.allowed:
                print(f"    {GREEN}→ manual-apply allowed{RESET}  {zone_str}")
            elif p.status == "approved" and not guard.allowed:
                print(f"    {RED}→ manual-apply blocked{RESET}  {zone_str}")
                for r in guard.reasons:
                    print(f"      {RED}!{RESET} {r}")
            else:
                # proposed
                auto_guard = check_weight_update_guardrails(
                    registry, p, mode="auto", proposal_status="proposed")
                manual_guard = guard
                print(f"    {DIM}guardrails (proposed):{RESET}")
                print(f"      {zone_str}  manual_blocked={not manual_guard.allowed}")
                if not manual_guard.allowed:
                    for r in manual_guard.reasons:
                        print(f"      {YELLOW}! manual:{RESET} {r}")


def cmd_propose(args: argparse.Namespace) -> None:
    """Create a new weight-change proposal."""
    registry = load_registry()
    key = getattr(args, "key", None)
    value = getattr(args, "value", None)
    reason = getattr(args, "reason", "")

    if not key or value is None:
        print(f"{RED}Error: --key and --value are required{RESET}", file=sys.stderr)
        return

    try:
        value = float(value)
    except ValueError:
        print(f"{RED}Error: --value must be a number{RESET}", file=sys.stderr)
        return

    w = registry.get_weight(key)
    if not w:
        print(f"{RED}Error: unknown weight key: {key}{RESET}", file=sys.stderr)
        return

    proposal = WeightUpdateProposal.create(
        weight_key=key,
        old_value=w.value,
        proposed_value=value,
        reason=reason,
        supporting_observations=[],
        expected_benefit="TBD",
        possible_risk="TBD",
        tests_to_run=["test_cognitive_weight_refinement"],
    )
    save_proposal(proposal)
    print(f"{GREEN}Proposal created: [{proposal.proposal_id}]{RESET}")
    print(f"  {key}: {proposal.old_value} → {proposal.proposed_value}")
    print(f"  Status: {proposal.status} (must be approved before applying)")


def cmd_simulate(args: argparse.Namespace) -> None:
    """Simulate a proposed weight change against eval phrases."""
    key = getattr(args, "key", None)
    value = getattr(args, "value", None)

    if not key or value is None:
        print(f"{RED}Error: --key and --value required{RESET}", file=sys.stderr)
        return

    try:
        value = float(value)
    except ValueError:
        print(f"{RED}Error: --value must be a number{RESET}", file=sys.stderr)
        return

    registry = load_registry()
    w = registry.get_weight(key)
    if not w:
        print(f"{RED}Error: unknown weight key: {key}{RESET}", file=sys.stderr)
        return

    print(f"Simulating: {key}: {w.value} → {value}")
    print(f"{DIM}Running eval phrases through meaning-vector path...{RESET}\n")

    sim_result = run_simulation(key, w.value, value)
    save_simulation(sim_result)

    colour_code = GREEN if sim_result.pass_fail == "pass" else (
        RED if sim_result.pass_fail == "fail" else YELLOW)
    pf = colour(sim_result.pass_fail.upper(), colour_code)
    print(f"Result: {pf}")
    print(f"Recommendation: {sim_result.recommendation}")

    if sim_result.behavior_changes:
        print(f"\n{YELLOW}Behavior changes ({len(sim_result.behavior_changes)}):{RESET}")
        for change in sim_result.behavior_changes:
            print(f"  {DIM}{change}{RESET}")
    else:
        print(f"\n{DIM}No behavior changes detected.{RESET}")

    if sim_result.regressions_detected:
        print(f"\n{RED}Regressions:{RESET}")
        for r in sim_result.regressions_detected:
            print(f"  {r}")


def cmd_auto_status(_args: argparse.Namespace) -> None:
    """Show auto-apply readiness and green-lane status."""
    from weslr.cognitive_weights import (
        GLOBAL_AUTO_APPLY_ENABLED,
        CognitiveWeightRegistry,
        check_weight_update_guardrails,
    )
    registry = CognitiveWeightRegistry.load_defaults()

    green = [k for k, w in registry.weights.items() if w.zone == "green"]
    yellow = [k for k, w in registry.weights.items() if w.zone == "yellow"]
    red = [k for k, w in registry.weights.items() if w.zone == "red"]

    print(f"\n{BOLD}Auto-apply readiness{RESET}")
    print(f"  Global auto-apply:  {colour('DISABLED', RED)} (GLOBAL_AUTO_APPLY_ENABLED=False)")
    print(f"  {BOLD}Green zone:{RESET} {len(green)} weight(s) defined (future auto-apply lane)")
    for k in green:
        w = registry.get_weight(k)
        delta_str = f"max_auto_delta={w.max_auto_delta}"
        print(f"    {GREEN}{k}{RESET}  {delta_str}")
        print(f"      auto_apply_allowed={w.auto_apply_allowed}  "
              f"min_obs={w.min_observations}  cooldown={w.cooldown_hours}h")
        print(f"      sim={w.requires_simulation_pass}  reg={w.requires_regression_pass}  "
              f"rollback={w.rollback_required}")
    if not green:
        print(f"    {DIM}No green weights defined yet.{RESET}")

    print(f"\n  {BOLD}Yellow zone:{RESET} {len(yellow)} weight(s) — manual approval required")
    print(f"  {BOLD}Red zone:{RESET} {len(red)} weight(s) — auto-apply blocked in this phase")

    # Demonstrate guardrail blocking a green proposal
    print(f"\n  {BOLD}Guardrail proof (green, all flags passing):{RESET}")
    if green:
        gk = green[0]
        # Simulate a valid-looking proposal with all evidence passing
        r = check_weight_update_guardrails(
            registry, gk, mode="auto",
            simulation_pass=True, regression_pass=True, observation_count=10)
        blocked = not r.allowed
        print(f"    {gk} in auto mode (all evidence passing): "
              f"allowed={r.allowed}  {colour('BLOCKED' if blocked else 'PASS', RED if blocked else GREEN)}")
        if blocked:
            for reason in r.reasons:
                print(f"      {RED}!{RESET} {reason}")

    print(f"\n  {BOLD}To enable auto-apply (future):{RESET}")
    print(f"    1. Set GLOBAL_AUTO_APPLY_ENABLED=True in cognitive_weights.py")
    print(f"    2. Confirm green weights are properly tested")
    print(f"    3. Ensure all guardrail conditions can be met")
    print(f"    4. Monitor auto-apply audit log after enabling")
    print(f"\n  Current: auto-apply is structurally possible but globally disabled.{RESET}")


def cmd_approve(args: argparse.Namespace) -> None:
    """Approve a proposal by ID."""
    pid = getattr(args, "proposal", None) or getattr(args, "id", None)
    if not pid:
        print(f"{RED}Error: --proposal <id> required{RESET}", file=sys.stderr)
        return
    ok = update_proposal_status(pid, "approved")
    if ok:
        print(f"{GREEN}Proposal [{pid}] approved.{RESET}")
    else:
        print(f"{RED}Error: proposal [{pid}] not found{RESET}", file=sys.stderr)


def cmd_reject(args: argparse.Namespace) -> None:
    """Reject a proposal by ID."""
    pid = getattr(args, "proposal", None) or getattr(args, "id", None)
    if not pid:
        print(f"{RED}Error: --proposal <id> required{RESET}", file=sys.stderr)
        return
    ok = update_proposal_status(pid, "rejected")
    if ok:
        print(f"{YELLOW}Proposal [{pid}] rejected.{RESET}")
    else:
        print(f"{RED}Error: proposal [{pid}] not found{RESET}", file=sys.stderr)


def cmd_apply(args: argparse.Namespace) -> None:
    """Apply an approved proposal to the live registry. Guardrails checked before apply."""
    from weslr.cognitive_weights import check_weight_update_guardrails

    pid = getattr(args, "proposal", None) or getattr(args, "id", None)
    if not pid:
        print(f"{RED}Error: --proposal <id> required{RESET}", file=sys.stderr)
        return

    proposals = load_proposals(limit=1000)
    target = None
    for p in proposals:
        if p.proposal_id == pid:
            target = p
            break

    if not target:
        print(f"{RED}Error: proposal [{pid}] not found{RESET}", file=sys.stderr)
        return

    if target.status != "approved":
        print(f"{RED}Error: proposal [{pid}] is {target.status}, not approved.{RESET}")
        return

    registry = load_registry()

    # Run guardrail check in manual mode
    guardrail = check_weight_update_guardrails(
        registry, target, mode="manual", proposal_status=target.status
    )

    if not guardrail.allowed:
        print(f"{RED}Apply blocked by guardrails:{RESET}")
        for r in guardrail.reasons:
            print(f"  {RED}-{RESET} {r}")
        if guardrail.required_actions:
            print(f"{YELLOW}Required actions to unblock:{RESET}")
            for a in guardrail.required_actions:
                print(f"  {YELLOW}  →{RESET} {a}")
        print(f"\n  zone={guardrail.zone}  delta={guardrail.actual_delta:.4f}")
        return

    ok = registry.set_pending(target.weight_key, target.proposed_value,
                               reason=f"applied proposal [{pid}]: {target.reason}")
    if not ok:
        print(f"{RED}Error: could not set weight {target.weight_key}{RESET}", file=sys.stderr)
        return

    registry.save_to_file()
    update_proposal_status(pid, "applied")
    print(f"{GREEN}Applied proposal [{pid}]: {target.weight_key} = {target.proposed_value}{RESET}")


def cmd_reset(args: argparse.Namespace) -> None:
    """Reset a weight to its default value."""
    key = getattr(args, "key", None)
    if not key:
        print(f"{RED}Error: --key <key> required{RESET}", file=sys.stderr)
        return
    registry = load_registry()
    ok = registry.reset(key)
    if not ok:
        print(f"{RED}Error: unknown weight key: {key}{RESET}", file=sys.stderr)
        return
    registry.save_to_file()
    print(f"{GREEN}Reset {key} to default ({registry.get(key)}).{RESET}")


def cmd_reset_all(args: argparse.Namespace) -> None:
    """Reset all weights to defaults."""
    registry = load_registry()
    registry.reset_all()
    registry.save_to_file()
    print(f"{GREEN}All weights reset to defaults.{RESET}")


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="WESLR cognitive weight management")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show registry status")
    list = sub.add_parser("list", help="List all weights")
    list.add_argument("--group", help="Filter by weight group prefix (e.g. meaning, obligation)")
    sub.add_parser("diff", help="Show weights differing from defaults")
    sub.add_parser("proposals", help="List proposals")

    propose = sub.add_parser("propose", help="Create a weight-change proposal")
    propose.add_argument("--key", required=True, help="Weight key")
    propose.add_argument("--value", required=True, help="Proposed value")
    propose.add_argument("--reason", required=True, help="Reason for change")

    sim = sub.add_parser("simulate", help="Simulate a weight change")
    sim.add_argument("--key", required=True, help="Weight key")
    sim.add_argument("--value", required=True, help="Proposed value")

    approve = sub.add_parser("approve", help="Approve a proposal")
    approve.add_argument("--proposal", required=True, help="Proposal ID")

    reject = sub.add_parser("reject", help="Reject a proposal")
    reject.add_argument("--proposal", required=True, help="Proposal ID")

    apply = sub.add_parser("apply", help="Apply an approved proposal")
    apply.add_argument("--proposal", required=True, help="Proposal ID")

    reset = sub.add_parser("reset", help="Reset a weight to default")
    reset.add_argument("--key", required=True, help="Weight key")

    sub.add_parser("reset-all", help="Reset all weights to defaults")

    auto_status_parser = sub.add_parser("auto-status", help="Show auto-apply readiness")

    args = parser.parse_args()

    COMMAND_MAP = {
        "status": cmd_status,
        "list": cmd_list,
        "diff": cmd_diff,
        "proposals": cmd_proposals,
        "propose": cmd_propose,
        "simulate": cmd_simulate,
        "approve": cmd_approve,
        "reject": cmd_reject,
        "apply": cmd_apply,
        "reset": cmd_reset,
        "reset-all": cmd_reset_all,
        "auto-status": cmd_auto_status,
    }

    cmd = COMMAND_MAP.get(args.command)
    if cmd:
        cmd(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
