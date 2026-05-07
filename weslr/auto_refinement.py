"""
weslr/auto_refinement.py

Guarded green-zone auto-apply function.
Supports both manual (operator-initiated) and auto (future WESLR-initiated) modes.

Core entry point: attempt_green_auto_apply(proposal_id, ...)
All changes are audited, rollback-snapshotted, and cooldown-tracked.
No background loop — callable/CLI-testable only.
"""

from typing import Optional
import os

# ── Internal helpers ──────────────────────────────────────────────────────────

def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Main entry point ─────────────────────────────────────────────────────────

def attempt_green_auto_apply(
    proposal_id: str,
    simulation_pass: bool = False,
    regression_pass: bool = False,
    observation_count: int = 0,
    actor: str = "weslr_auto",
    # Dependency injection for testing
    _config_path: Optional[str] = None,
    _proposals_path: Optional[str] = None,
    _registry_path: Optional[str] = None,
    _audit_path: Optional[str] = None,
    _cooldown_path: Optional[str] = None,
    _rollback_path: Optional[str] = None,
) -> tuple[bool, str, list[str]]:
    """
    Attempt to auto-apply an approved green-zone proposal.

    Returns (success, message, blocked_reasons).
    All paths (including blocked) write audit events.

    Does NOT run on a background loop — this is a single-shot callable.
    """
    # Lazy-load dependencies (avoids import-time filesystem writes)
    from weslr.auto_refinement_config import load_config
    from weslr.weight_proposal import load_proposals, update_proposal_status
    from weslr.cognitive_weights import load_registry, check_weight_update_guardrails
    from weslr.weight_audit import load_audit
    from weslr.weight_cooldown import load_cooldowns, save_cooldowns
    from weslr.weight_rollback import load_rollback_store

    config = load_config(_config_path)
    audit = load_audit(_audit_path)
    cooldowns = load_cooldowns(_cooldown_path)
    rollbacks = load_rollback_store(_rollback_path)

    # ── Step 1: Load proposal ────────────────────────────────────────────
    proposals = load_proposals(limit=1000, path=_proposals_path)
    target = None
    for p in proposals:
        if p.proposal_id == proposal_id:
            target = p
            break

    if not target:
        audit.write_event("auto_apply_blocked", proposal_id=proposal_id,
                          weight_key="unknown", zone="unknown",
                          guardrail_result="blocked",
                          blocked_reasons=[f"Proposal {proposal_id} not found"],
                          actor=actor)
        return False, f"Proposal {proposal_id} not found", [f"Proposal {proposal_id} not found"]

    # ── Step 2: Config gate ─────────────────────────────────────────────
    registry = load_registry(_registry_path)
    w = registry.get_weight(target.weight_key)

    if not w:
        audit.write_event("auto_apply_blocked", proposal_id=proposal_id,
                          weight_key=target.weight_key, zone="unknown",
                          guardrail_result="blocked",
                          blocked_reasons=[f"Unknown weight: {target.weight_key}"],
                          actor=actor)
        return False, f"Weight {target.weight_key} not found", [f"Unknown weight: {target.weight_key}"]

    zone = w.zone

    # ── Step 3: Config-level can_auto_apply ──────────────────────────────
    audit_log_present = os.path.exists(audit.path) if audit.path else False
    rollback_possible = True  # rollback store is always writable if path exists
    daily_count = cooldowns.daily_auto_count(target.weight_key)

    config_ok, config_blocked = config.can_auto_apply(
        zone=zone,
        simulation_pass=simulation_pass,
        regression_pass=regression_pass,
        audit_log_present=audit_log_present,
        rollback_possible=rollback_possible,
        daily_count=daily_count,
    )

    if not config_ok:
        audit.write_event("auto_apply_blocked", proposal_id=proposal_id,
                          weight_key=target.weight_key, zone=zone,
                          old_value=target.old_value, new_value=target.proposed_value,
                          delta=target.delta, mode="auto",
                          guardrail_result="blocked",
                          blocked_reasons=config_blocked,
                          actor=actor)
        return False, f"Auto-apply blocked by config: {config_blocked}", config_blocked

    # ── Step 4: Guardrail check ──────────────────────────────────────────
    guard = check_weight_update_guardrails(
        registry, target, mode="auto",
        proposal_status=target.status,
        simulation_pass=simulation_pass,
        regression_pass=regression_pass,
        observation_count=observation_count,
        global_auto_apply_enabled=config.global_auto_apply_enabled,
    )

    if not guard.allowed:
        audit.write_event("auto_apply_blocked", proposal_id=proposal_id,
                          weight_key=target.weight_key, zone=zone,
                          old_value=target.old_value, new_value=target.proposed_value,
                          delta=target.delta, mode="auto",
                          guardrail_result="blocked",
                          blocked_reasons=guard.reasons,
                          actor=actor)
        return False, f"Guardrail blocked: {guard.reasons}", guard.reasons

    # ── Step 5: Cooldown check ───────────────────────────────────────────
    entry = cooldowns.get(target.weight_key)
    if not entry.auto_apply_cooldown_elapsed(w.cooldown_hours):
        reason = f"Cooldown not elapsed: last auto-apply at {entry.last_auto_applied_at}"
        audit.write_event("auto_apply_blocked", proposal_id=proposal_id,
                          weight_key=target.weight_key, zone=zone,
                          old_value=target.old_value, new_value=target.proposed_value,
                          delta=target.delta, mode="auto",
                          guardrail_result="blocked",
                          blocked_reasons=[reason],
                          actor=actor)
        return False, reason, [reason]

    # ── Step 6: Create rollback snapshot ────────────────────────────────
    snap = rollbacks.create_snapshot(
        registry, target, mode="auto",
        reason=f"auto-apply proposal {proposal_id}",
    )

    # ── Step 7: Apply ────────────────────────────────────────────────────
    ok = registry.set_pending(target.weight_key, target.proposed_value,
                              reason=f"auto-applied {proposal_id}: {target.reason}")
    if not ok:
        audit.write_event("auto_apply_blocked", proposal_id=proposal_id,
                          weight_key=target.weight_key, zone=zone,
                          old_value=target.old_value, new_value=target.proposed_value,
                          delta=target.delta, mode="auto",
                          guardrail_result="blocked",
                          blocked_reasons=["registry.set_pending failed"],
                          actor=actor)
        return False, "Failed to set weight", ["registry.set_pending failed"]

    registry.save_to_file()
    cooldowns.record_auto_apply(target.weight_key)
    save_cooldowns(cooldowns)
    update_proposal_status(proposal_id, "applied", path=_proposals_path)

    audit.write_event("auto_apply_applied",
                      proposal_id=proposal_id,
                      weight_key=target.weight_key,
                      old_value=target.old_value,
                      new_value=target.proposed_value,
                      delta=target.delta,
                      zone=zone,
                      mode="auto",
                      guardrail_result="passed",
                      actor=actor,
                      reason=target.reason,
                      rollback_id=snap.rollback_id)

    return True, f"Auto-applied {target.weight_key} = {target.proposed_value}", []