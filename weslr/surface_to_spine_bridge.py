# surface_to_spine_bridge.py — WESLR Surface-to-Spine Bridge, Slice 1
# Artifact-originated weakness signal -> Step 1 inadequacy event
#
# Status: SLICE 1 + PATCH 1 (proof-aware urgency refinement)
# Authoritative for: docs/SURFACE_TO_SPINE_BRIDGE_V1.md
#
# PATCH 1: Proof-aware urgency — human_approvals >= 1 lowers urgency by
# one level. urgency_note added to ProvenanceRecord to surface the reason.
#
# What this module does:
# - Provides canonical bridge entry from artifact evaluation to Step 1
# - Preview mode: reads artifact, builds bridge object, validates, prints preview (no writes)
# - Confirm mode: same + calls record_inadequacy_event() to enter the spine
#
# What this module does NOT do:
# - No execution beyond Step 1
# - No CDI bundle creation
# - No proposal generation
# - No routing changes
# - No automatic triggering
# - No background scanning

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Artifact loading — use existing sim.py infrastructure
# ---------------------------------------------------------------------------
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sim import (
    find_meta_file_by_id,
    read_json_file,
    build_artifact_explainability,
    update_artifact_scores,
    connect,
    get_artifact_proof,
)

from weslr.inadequacy_persistence import record_inadequacy_event


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BRIDGE_VERSION = "1.0"
MAX_SIGNAL_AGE_DAYS = 30
SURFACE_TYPE = "artifact_weakness"

# Urgency -> runtime_state mapping (from SURFACE_TO_SPINE_BRIDGE_V1.md Section 8)
URGENCY_RUNTIME_STATE_MAP = {
    "high": "unavailable",
    "medium": "degraded",
    "low": "fallback_used",
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceRecord:
    original_item_id: str
    original_item_type: str
    confidence: float
    urgency: str  # "low" | "medium" | "high"
    requires_review: bool = True
    urgency_note: Optional[str] = None  # e.g. "lowered due to human approval signal"


@dataclass
class ArtifactWeaknessPayload:
    artifact_id: str
    internal_strength: List[str]
    external_proof: List[str]
    risk_count: int
    recurring_limitation: Optional[str]
    matched_interest_ids: List[str] = field(default_factory=list)


@dataclass
class SurfaceBridgeObject:
    bridge_version: str = BRIDGE_VERSION
    signal_id: str = ""
    source_surface: str = SURFACE_TYPE
    surface_ref: str = ""
    created_at: str = ""
    operator_triggered: bool = True
    operator_trigger_id: str = ""
    payload: Optional[ArtifactWeaknessPayload] = None
    spine_target: str = "step1_inadequacy_signal"
    provenance: Optional[ProvenanceRecord] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bridge_version": self.bridge_version,
            "signal_id": self.signal_id,
            "source_surface": self.source_surface,
            "surface_ref": self.surface_ref,
            "created_at": self.created_at,
            "operator_triggered": self.operator_triggered,
            "operator_trigger_id": self.operator_trigger_id,
            "payload": self.payload.__dict__ if self.payload else None,
            "spine_target": self.spine_target,
            "provenance": self.provenance.__dict__ if self.provenance else None,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SurfaceBridgeObject":
        payload = None
        if d.get("payload"):
            payload = ArtifactWeaknessPayload(**d["payload"])
        provenance = None
        if d.get("provenance"):
            provenance = ProvenanceRecord(**d["provenance"])
        return cls(
            bridge_version=d.get("bridge_version", BRIDGE_VERSION),
            signal_id=d.get("signal_id", ""),
            source_surface=d.get("source_surface", SURFACE_TYPE),
            surface_ref=d.get("surface_ref", ""),
            created_at=d.get("created_at", ""),
            operator_triggered=d.get("operator_triggered", True),
            operator_trigger_id=d.get("operator_trigger_id", ""),
            payload=payload,
            spine_target=d.get("spine_target", "step1_inadequacy_signal"),
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class BridgeValidationError(Exception):
    pass


# ---------------------------------------------------------------------------
# Artifact loading
# ---------------------------------------------------------------------------

def load_artifact_metadata(artifact_id: str) -> Dict[str, Any]:
    """Load artifact metadata by ID using existing sim.py infrastructure."""
    meta_file = find_meta_file_by_id(artifact_id)
    if meta_file is None:
        raise BridgeValidationError(f"No artifact found with id: {artifact_id}")
    meta = read_json_file(meta_file, {})
    if not meta:
        raise BridgeValidationError(f"Artifact file is empty or unreadable: {artifact_id}")
    return meta


def get_artifact_evaluation(artifact_id: str) -> Dict[str, Any]:
    """Get complete evaluation for an artifact using existing score + explainability paths."""
    meta = load_artifact_metadata(artifact_id)

    # PATCH 1 FIX: `update_artifact_scores` queries SQLite for proof_signals,
    # which returns 0 for untracked artifacts, overwriting the real meta values.
    # Capture original proof_signals BEFORE calling update_artifact_scores.
    original_proof = meta.get("proof_signals", {})

    # Apply existing score pipeline (update_artifact_scores uses existing sim.py logic)
    conn = connect()
    try:
        scored = update_artifact_scores(meta, conn)
    finally:
        conn.close()

    # build_artifact_explainability uses scored meta dict
    explainability = build_artifact_explainability(scored)

    # Restore original proof_signals so urgency derivation is accurate
    proof = original_proof

    return {
        "artifact_id": artifact_id,
        "meta": meta,
        "scored": scored,
        "explainability": explainability,
        "proof": proof,
    }


# ---------------------------------------------------------------------------
# Urgency derivation
# ---------------------------------------------------------------------------

# Urgency level order for reduction logic
URGENCY_LEVELS = ["low", "medium", "high"]

def _lower_urgency(urgency: str, note: str) -> tuple[str, str]:
    """Reduce urgency by one level. Returns (new_urgency, urgency_note)."""
    try:
        idx = URGENCY_LEVELS.index(urgency)
    except ValueError:
        return urgency, note
    if idx > 0:
        new_urgency = URGENCY_LEVELS[idx - 1]
        return new_urgency, note
    return urgency, note  # already at lowest


def _urgency_from_evaluation(evaluation: Dict[str, Any]) -> tuple[str, str]:
    """Determine urgency from evaluation data.

    Returns (urgency, urgency_note) tuple.

    Rules (PATCH 1 — proof-aware):
    - Recurring limitation detected → high (unchanged)
    - human_approvals >= 1 → lower urgency one level, note it
    - handoff_acceptances >= 1 → lower urgency one level, note it
    - real_usage_hits >= 1 → lower urgency one level, note it
    - Absent external proof + reasonable internal strength → medium
    - No strong internal signals → high
    - Otherwise → medium

    The urgency_note is surfaced in preview output so the operator sees why
    the urgency was adjusted down from the default.
    """
    explainability = evaluation.get("explainability", {})
    proof = evaluation.get("proof", {})
    internal_strength_list = explainability.get("internal_strength", [])
    external_proof_list = explainability.get("external_proof", [])
    risks = explainability.get("risks", [])

    # Start at medium as base
    urgency = "medium"
    urgency_note = ""

    # Strong recurring limitation signal → high (never reduced below medium)
    if any(
        "thin" in s.lower()
        or "substance" in s.lower()
        or "rejected" in s.lower()
        for s in risks
    ):
        urgency = "high"
        urgency_note = "recurring limitation"
    else:
        # PATCH 1: proof signals lower urgency by one level per signal type
        # Only one reduction per signal type; the strongest proof signal wins
        proof_note_parts: List[str] = []

        if int(proof.get("human_approvals", 0)) >= 1:
            urgency, urgency_note = _lower_urgency(urgency, "human approval signal")
            proof_note_parts.append("human approval")
        elif int(proof.get("handoff_acceptances", 0)) >= 1:
            urgency, urgency_note = _lower_urgency(urgency, "handoff acceptance signal")
            proof_note_parts.append("handoff acceptance")
        elif int(proof.get("real_usage_hits", 0)) >= 1:
            urgency, urgency_note = _lower_urgency(urgency, "real usage signal")
            proof_note_parts.append("real usage")

        if proof_note_parts:
            urgency_note = f"lowered due to: {', '.join(proof_note_parts)}"

    # Absent external proof with reasonable internal strength → push toward high
    # if we are already at medium/low due to proof
    no_external = (
        not external_proof_list
        or external_proof_list == ["no durable external proof yet"]
    )
    if no_external and internal_strength_list and urgency == "low":
        # Strong proof found, but still no external durable proof
        # Keep current proof-based level (don't re-escalate)
        pass

    # Check for low internal strength (no strong signals at all) → escalate to high
    if not internal_strength_list or internal_strength_list == [
        "early artifact with partial internal signals"
    ]:
        # If we already have proof signals, don't override to high
        if not proof.get("human_approvals") and not proof.get("handoff_acceptances") and not proof.get("real_usage_hits"):
            urgency = "high"
            urgency_note = "early-stage artifact, no proof signals"

    return urgency, urgency_note


def _confidence_from_evaluation(evaluation: Dict[str, Any]) -> float:
    """Compute signal confidence from evaluation data (0.0-1.0)."""
    explainability = evaluation.get("explainability", {})
    proof = evaluation.get("proof", {})
    internal_strength_list = explainability.get("internal_strength", [])
    external_proof_list = explainability.get("external_proof", [])
    risks = explainability.get("risks", [])

    confidence = 0.5

    # Proof signals increase confidence for actionability
    if int(proof.get("human_approvals", 0)) >= 1:
        confidence += 0.15
    if int(proof.get("real_usage_hits", 0)) >= 1:
        confidence += 0.2

    # Stronger internal signals increase confidence
    if len(internal_strength_list) >= 2:
        confidence += 0.15
    if any(s for s in internal_strength_list if "human-facing" in s or "internal" in s):
        confidence += 0.1

    # Absent external proof slightly reduces confidence for actionability
    if not external_proof_list or external_proof_list == ["no durable external proof yet"]:
        confidence -= 0.1

    # Risks lower confidence for reliability
    if risks and risks != ["no major explainability risks flagged"]:
        confidence -= 0.1 * min(len(risks), 3)

    return max(0.0, min(1.0, confidence))


def build_artifact_bridge_object(
    artifact_id: str,
    operator_trigger_id: str,
    urgency: Optional[str] = None,
) -> SurfaceBridgeObject:
    """Build a canonical SurfaceBridgeObject from an artifact evaluation."""
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    signal_id = f"bridge_{uuid.uuid4().hex[:8]}"

    # Load artifact + evaluation
    evaluation = get_artifact_evaluation(artifact_id)
    meta = evaluation.get("meta", {})
    explainability = evaluation.get("explainability", {})
    proof = evaluation.get("proof", {})

    # Urgency: explicit override or auto-derived (proof-aware)
    if urgency is None:
        urgency, urgency_note = _urgency_from_evaluation(evaluation)
    else:
        urgency_note = ""
    if urgency not in URGENCY_RUNTIME_STATE_MAP:
        raise BridgeValidationError(
            f"Invalid urgency: {urgency}. Must be one of: low, medium, high"
        )

    # Recurring limitation detection
    risks = explainability.get("risks", [])
    recurring_limitation = None
    if risks and risks != ["no major explainability risks flagged"]:
        recurring_limitation = "; ".join(risks[:3])

    # Build provenance
    confidence = _confidence_from_evaluation(evaluation)
    provenance = ProvenanceRecord(
        original_item_id=artifact_id,
        original_item_type="artifact",
        confidence=confidence,
        urgency=urgency,
        requires_review=True,
        urgency_note=urgency_note or None,
    )

    # Build payload
    payload = ArtifactWeaknessPayload(
        artifact_id=artifact_id,
        internal_strength=explainability.get("internal_strength", []),
        external_proof=explainability.get("external_proof", []),
        risk_count=len(risks) if risks and risks != ["no major explainability risks flagged"] else 0,
        recurring_limitation=recurring_limitation,
        matched_interest_ids=[],
    )

    # Build bridge object
    bridge = SurfaceBridgeObject(
        signal_id=signal_id,
        source_surface=SURFACE_TYPE,
        surface_ref=artifact_id,
        created_at=now_iso,
        operator_triggered=True,
        operator_trigger_id=operator_trigger_id,
        payload=payload,
        provenance=provenance,
    )

    return bridge


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_bridge_object(
    bridge: SurfaceBridgeObject,
    operator_trigger_id: str,
) -> List[str]:
    """Validate a bridge object. Returns list of error messages (empty = valid)."""
    errors: List[str] = []

    # Required fields
    if not bridge.signal_id:
        errors.append("signal_id is required")
    if not bridge.source_surface:
        errors.append("source_surface is required")
    if not bridge.surface_ref:
        errors.append("surface_ref (artifact_id) is required")
    if not bridge.created_at:
        errors.append("created_at is required")
    if not bridge.operator_trigger_id:
        errors.append("operator_trigger_id is required")

    # operator_triggered must be True (no auto-injection)
    if not bridge.operator_triggered:
        errors.append("operator_triggered must be True — no automatic signal injection")

    # source_surface must be allowed
    allowed_surfaces = {SURFACE_TYPE}  # Slice 1: artifact_weakness only
    if bridge.source_surface not in allowed_surfaces:
        errors.append(
            f"source_surface '{bridge.source_surface}' not in allowed list: {allowed_surfaces}"
        )

    # Timestamp must not be stale (>30 days)
    if bridge.created_at:
        try:
            created_dt = datetime.fromisoformat(bridge.created_at.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - created_dt).total_seconds() / 86400
            if age_days > MAX_SIGNAL_AGE_DAYS:
                errors.append(
                    f"Signal timestamp is stale ({age_days:.1f} days old). "
                    f"Max allowed: {MAX_SIGNAL_AGE_DAYS} days."
                )
        except ValueError:
            errors.append(f"created_at has invalid format: {bridge.created_at}")

    # Confidence must be in range
    if bridge.provenance:
        conf = bridge.provenance.confidence
        if not (0.0 <= conf <= 1.0):
            errors.append(f"provenance.confidence must be 0.0-1.0, got {conf}")

    # Urgency must be valid
    if bridge.provenance:
        if bridge.provenance.urgency not in URGENCY_RUNTIME_STATE_MAP:
            errors.append(
                f"provenance.urgency must be one of {list(URGENCY_RUNTIME_STATE_MAP.keys())}, "
                f"got {bridge.provenance.urgency}"
            )

    # Payload must be present
    if not bridge.payload:
        errors.append("payload is required")
    else:
        if not bridge.payload.artifact_id:
            errors.append("payload.artifact_id is required")

    return errors


# ---------------------------------------------------------------------------
# Mapping to Step 1
# ---------------------------------------------------------------------------

def bridge_to_inadequacy_metadata(bridge: SurfaceBridgeObject) -> Dict[str, Any]:
    """Map a validated SurfaceBridgeObject to record_inadequacy_event() parameters.

    From SURFACE_TO_SPINE_BRIDGE_V1.md Section 8:
    - source = "surface_bridge"
    - runtime_state = urgency_to_runtime_state(urgency)
    - category = derived from payload
    - event_id = signal_id
    - message = "[source_surface] surface_ref: original_item_id"
    - evidence_refs = [original_item_id, source_surface, operator_trigger_id]
    """
    payload = bridge.payload
    provenance = bridge.provenance
    urgency = provenance.urgency if provenance else "medium"
    runtime_state = URGENCY_RUNTIME_STATE_MAP.get(urgency, "degraded")

    # Derive category from evaluation
    explainability = {}
    if payload and hasattr(payload, "internal_strength"):
        # Use stored values
        internal_strength = payload.internal_strength or []
        risks_count = payload.risk_count or 0
    else:
        internal_strength = []
        risks_count = 0

    if risks_count > 0:
        category = "artifact_weakness:elevated_risk"
    elif internal_strength and internal_strength != ["early artifact with partial internal signals"]:
        category = "artifact_weakness:partial_proof"
    else:
        category = "artifact_weakness:early_stage"

    runtime_state_reason = (
        f"artifact evaluation: {payload.recurring_limitation or 'weakness signal'} "
        f"(confidence {provenance.confidence:.2f})"
        if payload and provenance else "artifact evaluation signal"
    )

    metadata = {
        "source": "surface_bridge",
        "runtime_state": runtime_state,
        "runtime_state_reason": runtime_state_reason,
        "path": f"artifacts/{bridge.surface_ref}" if bridge.surface_ref else "unknown",
        "provider": "artifact_evaluation",
        "fallback_used": False,
        "rescue_used": False,
        "category": category,
        # Store bridge signal_id in request_fingerprint for audit traceability
        "request_fingerprint": bridge.signal_id,
        # Additional evidence refs
        "_bridge_source_surface": bridge.source_surface,
        "_bridge_operator_trigger_id": bridge.operator_trigger_id,
        "_bridge_created_at": bridge.created_at,
    }

    return metadata


# ---------------------------------------------------------------------------
# Preview / Confirm entry points
# ---------------------------------------------------------------------------

def preview_bridge(artifact_id: str, operator_trigger_id: str = "manual", urgency: Optional[str] = None) -> Dict[str, Any]:
    """Preview what a bridge signal would look like without writing anything.

    Reads artifact, builds bridge object, validates, prints preview.
    Returns a dict with preview information. Does NOT call record_inadequacy_event().
    """
    # Load artifact (will raise if not found)
    evaluation = get_artifact_evaluation(artifact_id)
    meta = evaluation.get("meta", {})
    explainability = evaluation.get("explainability", {})
    proof = evaluation.get("proof", {})

    # Build bridge object
    bridge = build_artifact_bridge_object(
        artifact_id=artifact_id,
        operator_trigger_id=operator_trigger_id,
        urgency=urgency,
    )

    # Validate
    errors = validate_bridge_object(bridge, operator_trigger_id)
    if errors:
        raise BridgeValidationError("Validation failed: " + "; ".join(errors))

    # Map to Step 1 parameters for preview
    inadequacy_metadata = bridge_to_inadequacy_metadata(bridge)

    return {
        "mode": "preview",
        "signal_id": bridge.signal_id,
        "artifact_id": artifact_id,
        "artifact_title": meta.get("title", "unknown"),
        "urgency": bridge.provenance.urgency if bridge.provenance else "unknown",
        "urgency_note": bridge.provenance.urgency_note if bridge.provenance else "",
        "runtime_state": inadequacy_metadata["runtime_state"],
        "category": inadequacy_metadata["category"],
        "confidence": bridge.provenance.confidence if bridge.provenance else 0.0,
        "internal_strength": explainability.get("internal_strength", []),
        "external_proof": explainability.get("external_proof", []),
        "risks": explainability.get("risks", []),
        "next_actions": explainability.get("next_actions", []),
        "proof_signals": {
            "human_approvals": proof.get("human_approvals", 0),
            "handoff_acceptances": proof.get("handoff_acceptances", 0),
            "real_usage_hits": proof.get("real_usage_hits", 0),
        },
        "bridge_object": bridge.to_dict(),
        "step1_parameters": inadequacy_metadata,
        "spine_target": bridge.spine_target,
        "confirm_command": f"weslr spine bridge --from-artifact {artifact_id} --urgency {bridge.provenance.urgency if bridge.provenance else 'medium'} --confirm",
        "writes": [],  # Preview mode: no writes
    }


def confirm_bridge(artifact_id: str, operator_trigger_id: str = "manual", urgency: Optional[str] = None) -> Dict[str, Any]:
    """Confirm and submit a bridge signal to Step 1 of the canonical spine.

    Reads artifact, builds bridge object, validates, calls record_inadequacy_event().
    Returns confirmation information. Does NOT run later spine steps.
    """
    # Build bridge object
    bridge = build_artifact_bridge_object(
        artifact_id=artifact_id,
        operator_trigger_id=operator_trigger_id,
        urgency=urgency,
    )

    # Validate
    errors = validate_bridge_object(bridge, operator_trigger_id)
    if errors:
        raise BridgeValidationError("Validation failed: " + "; ".join(errors))

    # Map to Step 1 parameters
    inadequacy_metadata = bridge_to_inadequacy_metadata(bridge)

    # Call Step 1 — record inadequacy event
    record_inadequacy_event(inadequacy_metadata)

    # Load evaluation for response
    evaluation = get_artifact_evaluation(artifact_id)
    meta = evaluation.get("meta", {})

    return {
        "mode": "confirmed",
        "signal_id": bridge.signal_id,
        "artifact_id": artifact_id,
        "artifact_title": meta.get("title", "unknown"),
        "urgency": bridge.provenance.urgency if bridge.provenance else "unknown",
        "urgency_note": bridge.provenance.urgency_note if bridge.provenance else "",
        "runtime_state": inadequacy_metadata["runtime_state"],
        "category": inadequacy_metadata["category"],
        "event_recorded": True,
        "spine_target": bridge.spine_target,
        "step1_parameters": inadequacy_metadata,
        "confirm_message": (
            f"Signal {bridge.signal_id} recorded. "
            f"Will be processed through the canonical self-improvement spine. "
            f"Operator review required before any execution."
        ),
    }


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

def main(argv: List[str]) -> int:
    """CLI entry point for the surface-to-spine bridge.

    Usage:
        weslr spine bridge --from-artifact <id> [--urgency low|medium|high] [--confirm]
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="weslr spine bridge",
        description="Surface-to-Spine Bridge — Slice 1: Artifact Weakness to Step 1",
    )
    parser.add_argument(
        "--from-artifact",
        dest="artifact_id",
        required=True,
        help="Artifact ID to bridge into the self-improvement spine",
    )
    parser.add_argument(
        "--urgency",
        choices=["low", "medium", "high"],
        default=None,
        help="Override urgency level (default: auto-derived from evaluation)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm and submit the bridge signal (without this flag, preview mode is used)",
    )
    parser.add_argument(
        "--operator-id",
        dest="operator_id",
        default="manual",
        help="Operator trigger ID (default: manual)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args(argv)

    try:
        if args.confirm:
            result = confirm_bridge(
                artifact_id=args.artifact_id,
                operator_trigger_id=args.operator_id,
                urgency=args.urgency,
            )
        else:
            result = preview_bridge(
                artifact_id=args.artifact_id,
                operator_trigger_id=args.operator_id,
                urgency=args.urgency,
            )

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            _print_human_output(result)

        return 0

    except BridgeValidationError as e:
        if args.json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def _print_human_output(result: Dict[str, Any]) -> None:
    """Print human-readable output for non-JSON mode."""
    mode = result.get("mode", "unknown")
    print(f"\n{'='*60}")
    print(f"Surface-to-Spine Bridge — {mode.upper()}")
    print(f"{'='*60}")

    if mode == "preview":
        print(f"\nSignal ID:     {result.get('signal_id')}")
        print(f"Artifact ID:   {result.get('artifact_id')}")
        print(f"Title:         {result.get('artifact_title', 'unknown')}")
        print(f"Urgency:       {result.get('urgency')}")
        if result.get("urgency_note"):
            print(f"  ({result.get('urgency_note')})")
        print(f"Runtime State: {result.get('runtime_state')}")
        print(f"Category:      {result.get('category')}")
        print(f"Confidence:    {result.get('confidence', 0.0):.2f}")
        print(f"\nInternal Strength:")
        for s in result.get("internal_strength", []):
            print(f"  - {s}")
        print(f"\nExternal Proof:")
        for s in result.get("external_proof", []):
            print(f"  - {s}")
        print(f"\nRisks:")
        for s in result.get("risks", []):
            print(f"  - {s}")
        print(f"\nNext Actions:")
        for s in result.get("next_actions", []):
            print(f"  - {s}")
        print(f"\nProof Signals:")
        ps = result.get("proof_signals", {})
        print(f"  Human approvals:    {ps.get('human_approvals', 0)}")
        print(f"  Handoff accepts:   {ps.get('handoff_acceptances', 0)}")
        print(f"  Real usage hits:    {ps.get('real_usage_hits', 0)}")
        print(f"\nConfirm command:")
        print(f"  {result.get('confirm_command')}")
        print(f"\n[PREVIEW MODE — no signal recorded]")
        print(f"{'='*60}\n")

    elif mode == "confirmed":
        print(f"\nSignal ID:     {result.get('signal_id')}")
        print(f"Artifact ID:   {result.get('artifact_id')}")
        print(f"Title:         {result.get('artifact_title', 'unknown')}")
        print(f"Urgency:       {result.get('urgency')}")
        print(f"Event Recorded: {result.get('event_recorded')}")
        print(f"\n{result.get('confirm_message')}")
        print(f"\n{'='*60}\n")


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
