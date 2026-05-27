"""
WESLR Consolidation Promotion — V2

classify_zone()  — green / yellow / red based on candidate properties
decide_promotion() — returns PromotionDecision with auto/review/approval path
auto_promote()    — writes approved records, returns PromotionResult
audit_log()       — append-only audit entry

V1 invariant: promotion_performed=False for all candidates (digest-only).
V2 adds: zone classification + auto-promote for green when enabled.
"""

from __future__ import annotations

import json
import os
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .consolidation_config import (
    ConsolidationConfig,
    load_config,
    save_config,
)
from .public_pilot_storage_privacy_safety import reject_public_pilot_dot_weslr_path_v1

# ---------------------------------------------------------------------------
# Audit log path
# ---------------------------------------------------------------------------

_AUDIT_PATH = pathlib.Path(os.environ.get("WESLR_ROOT", pathlib.Path.home() / ".weslr")) / "consolidation_audit.jsonl"

# ---------------------------------------------------------------------------
# Zone classification
# ---------------------------------------------------------------------------

# Red-flag terms — these make a candidate doctrine / identity / governance / research truth
_RED_FLAG_TERMS = frozenset([
    "doctrine",
    "identity",
    "access_control",
    "governance",
    "safety",
    "alignment",
    "research_truth",
    "scientific_truth",
    "mission_store",
    "entity_memory",  # risky — affects entity graph
    "code",
    "external_action",
    "public_behavior",
    "self_modify",
    "self_authorize",
    "override_guard",
])

# Yellow-flag terms — medium risk, review required
_YELLOW_FLAG_TERMS = frozenset([
    "weight_proposal",
    "cognitive_anchor",
    "belief",
    "preference",
    "bias",
    "strategy",
    "mission_context",
    "relationship",
    "role_assumption",
])

# Destinations that are never auto-promoted (red regardless of flags)
_FORBIDDEN_DESTINATIONS = frozenset([
    "doctrine",
    "identity",
    "governance",
    "entity_memory",  # entity graph edits are high-stakes
    "mission_store",
    "code",
    "external_action",
    "research_truth",
    "safety",
    "alignment",
])


def classify_zone(
    destination: str,
    tags: list[str],
    cluster_id: str,
) -> str:
    """
    Classify a consolidation candidate into green / yellow / red.

    Rules (in priority order):
    1. Forbidden destination → RED
    2. Red-flag tag in tags → RED
    3. Yellow-flag tag in tags → YELLOW
    4. risk_level field explicitly set to high → RED
    5. Default → GREEN
    """
    d_lower = destination.lower()
    t_lower = [t.lower() for t in tags]

    # 1. Forbidden destination
    for forbidden in _FORBIDDEN_DESTINATIONS:
        if forbidden in d_lower:
            return "red"

    # 2. Red-flag tags
    for flag in _RED_FLAG_TERMS:
        if flag in t_lower:
            return "red"

    # 3. Yellow-flag tags
    for flag in _YELLOW_FLAG_TERMS:
        if flag in t_lower:
            return "yellow"

    # 4. Explicit high risk_level in tags
    if "risk_level:high" in t_lower or "high_risk" in t_lower:
        return "red"

    # 5. Default
    return "green"


# ---------------------------------------------------------------------------
# Promotion decision
# ---------------------------------------------------------------------------

@dataclass
class PromotionDecision:
    cluster_id: str
    zone: str  # green | yellow | red
    auto_eligible: bool       # zone is green AND config allows it
    auto_promote: bool        # actual decision to auto-promote
    blocked_reasons: list[str] = field(default_factory=list)
    destination: str = ""
    provenance: list = field(default_factory=list)
    proposed_record: dict | None = None

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "zone": self.zone,
            "auto_eligible": self.auto_eligible,
            "auto_promote": self.auto_promote,
            "blocked_reasons": self.blocked_reasons,
            "destination": self.destination,
            "provenance": self.provenance,
        }


def decide_promotion(
    cluster: dict,
    cfg: ConsolidationConfig | None = None,
) -> PromotionDecision:
    """
    Decide whether a consolidation candidate should be auto-promoted.

    V1 behavior: always auto_promote=False, blocked_reasons=["V1 — promotion disabled"]

    V2 behavior:
    - classify zone
    - if green + config.is_auto_enabled_for("green") + can_auto_apply() → auto_promote=True
    - if yellow → auto_promote=False, review required
    - if red → auto_promote=False, approval required
    """
    if cfg is None:
        cfg = load_config()

    if public_pilot_mode:
        try:
            reject_public_pilot_dot_weslr_path_v1(_AUDIT_PATH, public_pilot_mode=True)
        except ValueError as exc:
            return PromotionResult(
                cluster_id=cluster.get("cluster_id", "?"),
                promoted=False,
                zone="n/a",
                decision="blocked",
                destination=cluster.get("proposed_destination", ""),
                blocked_reasons=[str(exc), "public-pilot flows cannot use consolidation promotion paths"],
                record_written=False,
            )

    cluster_id = cluster.get("cluster_id", "?")
    destination = cluster.get("proposed_destination", "")
    provenance = cluster.get("provenance", [])
    tags = cluster.get("tags", [])
    risk_level = cluster.get("risk_level", "low")

    # V1 invariant: promotion disabled for all
    if not cfg.consolidation_auto_enabled and not cfg.green_zone_auto_promotion_enabled:
        # Check if we're in V1 mode (both off) vs V2 mode (at least one on)
        # V1: both off, no promotion ever
        # V2: at least one on, green auto-promote allowed
        pass  # fall through to zone classification

    zone = classify_zone(destination, tags, cluster_id)

    # Only green zones can ever auto-promote. Check config gate first.
    if zone == "green" and cfg.is_auto_enabled_for("green"):
        can_auto, blocked_reasons = cfg.can_auto_apply(zone, destination, provenance)
        if can_auto:
            auto_promote = True
            blocked_reasons = []
        else:
            auto_promote = False
    else:
        auto_promote = False
        # For yellow/red zones, build blocking reasons for the decision record
        if zone != "green":
            blocked_reasons = [f"zone={zone} is not eligible for auto-promotion"]
        else:
            # green but config not enabled
            blocked_reasons = ["green_zone_auto_promotion_enabled is False or zone not in enabled_zones"]

    return PromotionDecision(
        cluster_id=cluster_id,
        zone=zone,
        auto_eligible=(zone == "green" and cfg.is_auto_enabled_for("green")),
        auto_promote=auto_promote,
        blocked_reasons=blocked_reasons,  # includes yellow/red/disabled reasons from can_auto_apply
        destination=destination,
        provenance=provenance,
        proposed_record=cluster,
    )


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def audit_log(
    cluster_id: str,
    zone: str,
    decision: str,  # auto_promoted | review_required | approval_required | blocked
    destination: str,
    provenance: list,
    blocked_reasons: list[str],
    cfg: ConsolidationConfig,
) -> None:
    """
    Append an audit entry to consolidation_audit.jsonl.
    Only written if require_audit_log=True in config.
    """
    if not cfg.require_audit_log:
        return

    entry = {
        "timestamp": _now_iso(),
        "event": "consolidation_promotion",
        "cluster_id": cluster_id,
        "zone": zone,
        "decision": decision,
        "destination": destination,
        "provenance": provenance,
        "blocked_reasons": blocked_reasons,
    }

    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Apply promotion
# ---------------------------------------------------------------------------

@dataclass
class PromotionResult:
    cluster_id: str
    promoted: bool
    zone: str
    decision: str  # auto_promoted | review_required | approval_required | blocked | V1_disabled
    destination: str
    blocked_reasons: list[str]
    record_written: bool

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "promoted": self.promoted,
            "zone": self.zone,
            "decision": self.decision,
            "destination": self.destination,
            "blocked_reasons": self.blocked_reasons,
            "record_written": self.record_written,
        }


def auto_promote(
    cluster: dict,
    cfg: ConsolidationConfig | None = None,
    *,
    public_pilot_mode: bool = False,
) -> PromotionResult:
    """
    Attempt to auto-promote a consolidation candidate.

    Returns PromotionResult with:
    - promoted: True if record was written
    - decision: auto_promoted | review_required | approval_required | blocked | V1_disabled
    - record_written: True only for actual promotions
    """
    if cfg is None:
        cfg = load_config()

    if public_pilot_mode:
        try:
            reject_public_pilot_dot_weslr_path_v1(_AUDIT_PATH, public_pilot_mode=True)
        except ValueError as exc:
            return PromotionResult(
                cluster_id=cluster.get("cluster_id", "?"),
                promoted=False,
                zone="n/a",
                decision="blocked",
                destination=cluster.get("proposed_destination", ""),
                blocked_reasons=[str(exc), "public-pilot flows cannot use consolidation promotion paths"],
                record_written=False,
            )

    cluster_id = cluster.get("cluster_id", "?")
    destination = cluster.get("proposed_destination", "")
    provenance = cluster.get("provenance", [])
    tags = cluster.get("tags", [])

    # V1 check
    if not cfg.consolidation_auto_enabled and not cfg.green_zone_auto_promotion_enabled:
        # Both off = V1 mode, no promotion
        audit_log(cluster_id, "n/a", "V1_disabled", destination, provenance, [], cfg)
        return PromotionResult(
            cluster_id=cluster_id,
            promoted=False,
            zone="n/a",
            decision="V1_disabled",
            destination=destination,
            blocked_reasons=["V1 — consolidation_auto_enabled and green_zone_auto_promotion_enabled both False"],
            record_written=False,
        )

    decision = decide_promotion(cluster, cfg)

    if decision.auto_promote:
        # Write record (append-only, no external action)
        _write_destination_record(destination, cluster)

        audit_log(
            cluster_id,
            decision.zone,
            "auto_promoted",
            destination,
            provenance,
            [],
            cfg,
        )

        return PromotionResult(
            cluster_id=cluster_id,
            promoted=True,
            zone=decision.zone,
            decision="auto_promoted",
            destination=destination,
            blocked_reasons=[],
            record_written=True,
        )
    else:
        # Blocked or review/approval required
        if decision.zone == "yellow":
            dec = "review_required"
        elif decision.zone == "red":
            dec = "approval_required"
        else:
            dec = "blocked"

        audit_log(
            cluster_id,
            decision.zone,
            dec,
            destination,
            provenance,
            decision.blocked_reasons,
            cfg,
        )

        return PromotionResult(
            cluster_id=cluster_id,
            promoted=False,
            zone=decision.zone,
            decision=dec,
            destination=destination,
            blocked_reasons=decision.blocked_reasons,
            record_written=False,
        )


def _write_destination_record(destination: str, cluster: dict) -> bool:
    """
    Write the consolidation record to the appropriate destination file.
    Append-only; returns True on success.
    """
    import os

    weslr_root = pathlib.Path(os.environ.get("WESLR_ROOT", pathlib.Path.home() / ".weslr"))

    # Map destination -> file path
    destination_map = {
        "continuity_summary": weslr_root / "continuity_summaries.jsonl",
        "attention_memory": weslr_root / "attention_memory.jsonl",
        "digest_archive_marker": weslr_root / "digest_archive.jsonl",
        "procedural_note": weslr_root / "procedural_notes.jsonl",
    }

    dest_path = destination_map.get(destination)
    if not dest_path:
        return False

    record = {
        "timestamp": _now_iso(),
        "source": "consolidation_promotion",
        "cluster_id": cluster.get("cluster_id", "?"),
        "destination": destination,
        "provenance": cluster.get("provenance", []),
        "summary": cluster.get("summary", ""),
        "confidence": cluster.get("confidence", 0.5),
        "tags": cluster.get("tags", []),
    }

    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def get_auto_status(cfg: ConsolidationConfig | None = None) -> dict:
    """Return status dict for CLI status command."""
    if cfg is None:
        cfg = load_config()
    return {
        "consolidation_auto_enabled": cfg.consolidation_auto_enabled,
        "green_zone_auto_promotion_enabled": cfg.green_zone_auto_promotion_enabled,
        "enabled_zones": cfg.enabled_zones,
        "require_provenance": cfg.require_provenance,
        "require_audit_log": cfg.require_audit_log,
        "allowed_green_destinations": cfg.allowed_green_destinations,
    }


def enable_auto(cfg=None, path=None):
    """Enable auto-promotion and save config."""
    if cfg is None:
        cfg = load_config(path)
    cfg.enable()
    save_config(cfg, path)
    return cfg


def disable_auto(cfg=None, path=None):
    """Disable auto-promotion and save config."""
    if cfg is None:
        cfg = load_config(path)
    cfg.disable()
    save_config(cfg, path)
    return cfg