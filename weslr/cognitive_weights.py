"""
weslr/cognitive_weights.py

Explicit cognitive weight registry for WESLR.
All weights are inspectable, reversible, versioned, operator-approved.

Storage: ~/.weslr/cognitive_weights.json (project-local fallback: .weslr_state/)
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json
import os
import copy

DEFAULT_STORE_DIR = os.path.expanduser("~/.weslr")
PROJECT_STORE_DIR = ".weslr_state"

# ── Dataclasses ────────────────────────────────────────────────────────────────


@dataclass
class CognitiveWeight:
    key: str
    value: float
    default_value: float
    min_value: float
    max_value: float
    description: str
    module: str  # which module reads this weight
    version: str = "1.0"
    last_updated: Optional[str] = None
    update_reason: Optional[str] = None
    # ── Guardrail fields ──────────────────────────────────────────────
    zone: str = "yellow"  # green | yellow | red
    auto_propose_allowed: bool = True
    auto_apply_allowed: bool = False  # globally disabled by default
    requires_operator_approval: bool = True
    requires_simulation_pass: bool = True
    requires_regression_pass: bool = True
    rollback_required: bool = True
    min_observations: int = 3
    cooldown_hours: int = 24
    max_auto_delta: float = 0.1  # max delta in auto mode (very conservative)
    max_manual_delta: float = 0.5  # max delta in manual apply mode
    locked: bool = False
    guardrail_reason: str = ""

    def dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class CognitiveWeightRegistry:
    """Registry for all explicit WESLR cognitive weights."""

    weights: dict[str, CognitiveWeight] = field(default_factory=dict)
    _store_path: Optional[str] = None

    # ── Defaults ──────────────────────────────────────────────────────────────

    @staticmethod
    def _defaults() -> dict[str, CognitiveWeight]:
        # Zone definitions:
        #   green  = low-risk, future auto-apply possible with all guardrails
        #   yellow = medium-risk, manual apply after approval + simulation
        #   red    = security-critical, manual apply blocked in this phase
        # Global auto-apply is DISABLED for this release.
        return {

            # ── Meaning vector dimensions (YELLOW) ──────────────────────────
            # Affects how WESLR classifies message intent. Wrong values could
            # misroute identity queries or miss memory requests.
            "meaning.identity_query_weight": CognitiveWeight(
                key="meaning.identity_query_weight",
                value=1.0, default_value=1.0,
                min_value=0.0, max_value=2.0,
                description="Multiplier for identity_query speech-act signal",
                module="linguistic_meaning",
                zone="yellow",
                guardrail_reason="Affects intent classification; misrouting could cause identity over/under-claim",
            ),
            "meaning.memory_query_weight": CognitiveWeight(
                key="meaning.memory_query_weight",
                value=1.0, default_value=1.0,
                min_value=0.0, max_value=2.0,
                description="Multiplier for memory_query speech-act signal",
                module="linguistic_meaning",
                zone="yellow",
                guardrail_reason="Affects memory intent classification; wrong threshold could fabricate or suppress memory claims",
            ),
            "meaning.first_contact_weight": CognitiveWeight(
                key="meaning.first_contact_weight",
                value=1.0, default_value=1.0,
                min_value=0.0, max_value=2.0,
                description="Multiplier for first_contact relational signal",
                module="linguistic_meaning",
                zone="yellow",
                guardrail_reason="Affects new-contact detection; could cause cold-start failures or false familiarity",
            ),
            "meaning.self_model_query_weight": CognitiveWeight(
                key="meaning.self_model_query_weight",
                value=1.0, default_value=1.0,
                min_value=0.0, max_value=2.0,
                description="Multiplier for self_model_query signal",
                module="linguistic_meaning",
                zone="yellow",
                guardrail_reason="Affects self-description routing; wrong values could degrade bounded identity behavior",
            ),
            "meaning.frustration_weight": CognitiveWeight(
                key="meaning.frustration_weight",
                value=1.0, default_value=1.0,
                min_value=0.0, max_value=2.0,
                description="Multiplier for frustration signal",
                module="linguistic_meaning",
                zone="yellow",
                guardrail_reason="Affects emotional-state routing; wrong values could fail frustration handling",
            ),

            # ── Response obligation thresholds (YELLOW) ──────────────────────
            # Thresholds gate when WESLR decides to act on a given obligation.
            # Changes here affect the entire meaning-vector response path.
            "obligation.minimum_confidence": CognitiveWeight(
                key="obligation.minimum_confidence",
                value=0.45, default_value=0.45,
                min_value=0.1, max_value=0.9,
                description="Minimum confidence to act on an obligation",
                module="response_obligation",
                zone="yellow",
                guardrail_reason="Master threshold for obligation activation; wrong value could activate or suppress too many obligations",
            ),
            "obligation.identity_threshold": CognitiveWeight(
                key="obligation.identity_threshold",
                value=0.3, default_value=0.3,
                min_value=0.0, max_value=1.0,
                description="Signal threshold to trigger verify_identity obligation",
                module="response_obligation",
                zone="yellow",
                guardrail_reason="Gates identity verification; wrong value could demand identity proofs unnecessarily",
            ),
            "obligation.memory_threshold": CognitiveWeight(
                key="obligation.memory_threshold",
                value=0.3, default_value=0.3,
                min_value=0.0, max_value=1.0,
                description="Signal threshold to trigger report_memory_state obligation",
                module="response_obligation",
                zone="yellow",
                guardrail_reason="Gates memory reporting; wrong value could fabricate or suppress memory claims",
            ),
            "obligation.self_model_threshold": CognitiveWeight(
                key="obligation.self_model_threshold",
                value=0.3, default_value=0.3,
                min_value=0.0, max_value=1.0,
                description="Signal threshold to trigger describe_self obligation",
                module="response_obligation",
                zone="yellow",
                guardrail_reason="Gates self-description; wrong value could degrade bounded self-model behavior",
            ),
            "obligation.first_contact_threshold": CognitiveWeight(
                key="obligation.first_contact_threshold",
                value=0.3, default_value=0.3,
                min_value=0.0, max_value=1.0,
                description="Signal threshold to trigger orient_new_contact obligation",
                module="response_obligation",
                zone="yellow",
                guardrail_reason="Gates new-contact handling; wrong value could fail first-contact experience",
            ),
            "obligation.meaning_response_threshold": CognitiveWeight(
                key="obligation.meaning_response_threshold",
                value=0.40, default_value=0.40,
                min_value=0.1, max_value=0.9,
                description="Minimum confidence for meaning-response candidate to be selected",
                module="meaning_response",
                zone="yellow",
                guardrail_reason="Gates meaning-response activation; wrong value could drop good responses or raise poor ones",
            ),

            # ── Response ranking weights (YELLOW) ────────────────────────────
            # Weights used in candidate ranking. Changes here affect which
            # response is selected when multiple candidates exist.
            "ranking.grounding_weight": CognitiveWeight(
                key="ranking.grounding_weight",
                value=1.0, default_value=1.0,
                min_value=0.0, max_value=3.0,
                description="Weight for grounding_score in candidate ranking",
                module="meaning_response",
                zone="yellow",
                guardrail_reason="Affects candidate ranking; extreme values could select ungrounded responses",
            ),
            "ranking.humility_weight": CognitiveWeight(
                key="ranking.humility_weight",
                value=1.0, default_value=1.0,
                min_value=0.0, max_value=3.0,
                description="Weight for humility in candidate ranking",
                module="meaning_response",
                zone="yellow",
                guardrail_reason="Affects tone calibration; wrong values could shift too formal or too familiar",
            ),
            "ranking.relationship_fit_weight": CognitiveWeight(
                key="ranking.relationship_fit_weight",
                value=1.0, default_value=1.0,
                min_value=0.0, max_value=3.0,
                description="Weight for relationship_fit in candidate ranking",
                module="meaning_response",
                zone="yellow",
                guardrail_reason="Affects relational tone; wrong values could misrepresent relationship depth",
            ),
            "ranking.clarity_weight": CognitiveWeight(
                key="ranking.clarity_weight",
                value=1.0, default_value=1.0,
                min_value=0.0, max_value=3.0,
                description="Weight for clarity in candidate ranking",
                module="meaning_response",
                zone="yellow",
                guardrail_reason="Affects readability of responses; wrong values could make output confusing",
            ),
            "ranking.identity_safety_weight": CognitiveWeight(
                key="ranking.identity_safety_weight",
                value=2.0, default_value=2.0,
                min_value=0.0, max_value=5.0,
                description="Weight for identity_safety in candidate ranking (high = very important)",
                module="meaning_response",
                zone="yellow",
                guardrail_reason="Identity safety gating; lowering below default could allow identity over-claim responses",
            ),
            "ranking.memory_safety_weight": CognitiveWeight(
                key="ranking.memory_safety_weight",
                value=2.0, default_value=2.0,
                min_value=0.0, max_value=5.0,
                description="Weight for memory_safety in candidate ranking (high = very important)",
                module="meaning_response",
                zone="yellow",
                guardrail_reason="Memory safety gating; lowering below default could allow raw memory dumps",
            ),

            # ── Identity confidence thresholds (RED) ─────────────────────────
            # CRITICAL SECURITY BOUNDARY. These weights control when WESLR
            # treats a user as verified, trusted, or unknown. Wrong values
            # could cause identity spoofing or denial of verified identity.
            "identity.minimum_verified_confidence": CognitiveWeight(
                key="identity.minimum_verified_confidence",
                value=0.8, default_value=0.8,
                min_value=0.0, max_value=1.0,
                description="Minimum confidence to treat identity as verified",
                module="meaning_state_context",
                zone="red",
                guardrail_reason="CRITICAL: Controls verified identity threshold. RED zone — manual apply blocked in this phase. Wrong value could allow identity spoofing.",
                max_manual_delta=0.1,
            ),
            "identity.claimed_confidence_floor": CognitiveWeight(
                key="identity.claimed_confidence_floor",
                value=0.3, default_value=0.3,
                min_value=0.0, max_value=1.0,
                description="Below this confidence, identity treated as unknown even if name present",
                module="meaning_state_context",
                zone="red",
                guardrail_reason="CRITICAL: Controls when a self-claim is treated as credible. RED zone — manual apply blocked in this phase. Wrong value could suppress or accept false identity claims.",
                max_manual_delta=0.1,
            ),

            # ── Memory confidence thresholds (YELLOW) ───────────────────────
            # Affects how much state-confidence WESLR assigns from memory.
            # Wrong values could cause over/under-confidence in memory.
            "memory.state_confidence_verified_add": CognitiveWeight(
                key="memory.state_confidence_verified_add",
                value=0.4, default_value=0.4,
                min_value=0.0, max_value=1.0,
                description="State-confidence contribution from verified identity",
                module="meaning_state_context",
                zone="yellow",
                guardrail_reason="Affects state confidence calibration; wrong value could create false confidence or undeserved skepticism",
            ),
            "memory.state_confidence_memory_add": CognitiveWeight(
                key="memory.state_confidence_memory_add",
                value=0.2, default_value=0.2,
                min_value=0.0, max_value=1.0,
                description="State-confidence contribution from memory available",
                module="meaning_state_context",
                zone="yellow",
                guardrail_reason="Affects memory confidence; wrong value could fabricate or deny valid memory",
            ),

            # ── Relationship / tone (YELLOW) ─────────────────────────────────
            # Affects familiarity calibration. Wrong values could shift tone
            # too formal or too familiar too quickly.
            "tone.max_familiarity": CognitiveWeight(
                key="tone.max_familiarity",
                value=0.7, default_value=0.7,
                min_value=0.0, max_value=1.0,
                description="Maximum familiarity score before tone shifts to formal",
                module="meaning_response",
                zone="yellow",
                guardrail_reason="Affects relational tone calibration; wrong value could shift tone inappropriately",
            ),
        }

    # ── Init ────────────────────────────────────────────────────────────────

    @classmethod
    def load_defaults(cls) -> "CognitiveWeightRegistry":
        registry = cls()
        registry.weights = cls._defaults()
        return registry

    @classmethod
    def load_from_file(cls, path: str) -> "CognitiveWeightRegistry":
        """Load weights from JSON file. Falls back to defaults if file absent."""
        if not os.path.exists(path):
            return cls.load_defaults()
        with open(path) as f:
            data = json.load(f)
        registry = cls()
        registry.weights = {}
        for d in data.get("weights", []):
            w = CognitiveWeight(**d)
            registry.weights[w.key] = w
        registry._store_path = path
        return registry

    def save_to_file(self, path: Optional[str] = None) -> None:
        """Save current weights to JSON file. Creates directory if needed."""
        p = path or self._store_path
        if p is None:
            raise ValueError("No store path specified")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        data = {
            "version": "1.0",
            "weights": [w.dict() for w in self.weights.values()],
        }
        with open(p, "w") as f:
            json.dump(data, f, indent=2)
        self._store_path = p

    # ── Access ──────────────────────────────────────────────────────────────

    def get(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """Return current value for a weight key, or default if not found."""
        w = self.weights.get(key)
        return w.value if w else default

    def get_weight(self, key: str) -> Optional[CognitiveWeight]:
        return self.weights.get(key)

    def set_pending(self, key: str, value: float, reason: str = "") -> bool:
        """Set a new pending value (not yet canonical). Returns False if key unknown."""
        w = self.weights.get(key)
        if not w:
            return False
        if not (w.min_value <= value <= w.max_value):
            raise ValueError(f"{key}: {value} outside allowed range [{w.min_value}, {w.max_value}]")
        w.value = value
        w.last_updated = _now_iso()
        w.update_reason = reason
        return True

    def reset(self, key: str) -> bool:
        """Reset a single weight to its default_value."""
        w = self.weights.get(key)
        if not w:
            return False
        w.value = w.default_value
        w.last_updated = _now_iso()
        w.update_reason = "reset to default"
        return True

    def reset_all(self) -> None:
        """Reset all weights to defaults."""
        for w in self.weights.values():
            w.value = w.default_value
            w.last_updated = _now_iso()
            w.update_reason = "full reset to defaults"

    def diff_from_defaults(self) -> dict[str, dict]:
        """Return weights whose current value differs from default."""
        diff = {}
        for k, w in self.weights.items():
            if abs(w.value - w.default_value) > 1e-9:
                diff[k] = {
                    "default": w.default_value,
                    "current": w.value,
                    "delta": w.value - w.default_value,
                    "reason": w.update_reason,
                }
        return diff

    def export_snapshot(self) -> dict:
        """Export full registry state as dict."""
        return {
            "version": "1.0",
            "exported_at": _now_iso(),
            "weights": {k: w.dict() for k, w in self.weights.items()},
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_store_path() -> str:
    """Return ~/.weslr/cognitive_weights.json (create dir if needed)."""
    os.makedirs(DEFAULT_STORE_DIR, exist_ok=True)
    return os.path.join(DEFAULT_STORE_DIR, "cognitive_weights.json")


def project_store_path() -> str:
    """Return .weslr_state/cognitive_weights.json for project-local storage."""
    return os.path.join(PROJECT_STORE_DIR, "cognitive_weights.json")


def load_registry(path: Optional[str] = None) -> CognitiveWeightRegistry:
    """Load registry from path, falling back to defaults."""
    if path:
        return CognitiveWeightRegistry.load_from_file(path)
    # Try project-local first, then user home
    p = project_store_path()
    if os.path.exists(p):
        return CognitiveWeightRegistry.load_from_file(p)
    return CognitiveWeightRegistry.load_defaults()


# ── Global auto-apply flag ────────────────────────────────────────────────────
# Globally disables auto-apply for this release.
# Even green-zone weights cannot auto-apply while this is False.
GLOBAL_AUTO_APPLY_ENABLED = False


# ── Guardrail check ──────────────────────────────────────────────────────────

from dataclasses import dataclass


@dataclass
class GuardrailResult:
    allowed: bool
    mode: str  # "auto" | "manual"
    zone: str
    reasons: list[str]
    required_actions: list[str]
    max_delta_allowed: float
    actual_delta: float
    requires_operator_approval: bool
    requires_simulation_pass: bool
    requires_regression_pass: bool
    rollback_required: bool
    proposal_status_ok: bool
    weight_locked: bool


def check_weight_update_guardrails(
    registry: CognitiveWeightRegistry,
    proposal_or_key,
    mode: str = "manual",
    proposal_status: str = "proposed",
    simulation_pass: bool = False,
    regression_pass: bool = False,
    observation_count: int = 0,
) -> GuardrailResult:
    """
    Check whether a weight update passes all guardrails for a given mode.


    Mode "auto": all auto-improvement lanes. Blocked unless zone=green,
                 auto_apply_allowed=True, delta within max_auto_delta,
                 simulation/regression pass, and GLOBAL_AUTO_APPLY_ENABLED.
    Mode "manual": operator-initiated apply. Blocked if:
                 - weight locked
                 - delta exceeds max_manual_delta
                 - zone=red (blocked in this phase)
                 - requires_operator_approval but proposal not approved

    Parameters:
        registry: CognitiveWeightRegistry
        proposal_or_key: WeightUpdateProposal or weight key string
        mode: "auto" or "manual"
        proposal_status: "proposed" | "approved" | etc.
        simulation_pass: whether simulation passed (auto mode)
        regression_pass: whether regression tests passed (auto mode)
        observation_count: number of supporting observations (auto mode)
    """
    from weslr.weight_proposal import WeightUpdateProposal

    # Resolve weight key and delta
    if isinstance(proposal_or_key, WeightUpdateProposal):
        weight_key = proposal_or_key.weight_key
        delta = abs(proposal_or_key.delta)
        old_value = proposal_or_key.old_value
    else:
        weight_key = proposal_or_key
        delta = 0.0
        old_value = None

    w = registry.get_weight(weight_key)
    if not w:
        return GuardrailResult(
            allowed=False,
            mode=mode,
            zone="unknown",
            reasons=[f"Unknown weight key: {weight_key}"],
            required_actions=[],
            max_delta_allowed=0.0,
            actual_delta=delta,
            requires_operator_approval=False,
            requires_simulation_pass=False,
            requires_regression_pass=False,
            rollback_required=False,
            proposal_status_ok=False,
            weight_locked=False,
        )

    reasons: list[str] = []
    required_actions: list[str] = []
    zone = w.zone
    allowed = True

    # ── Global auto-apply gate ──────────────────────────────────────────
    if mode == "auto":
        if not GLOBAL_AUTO_APPLY_ENABLED:
            reasons.append("Global auto-apply is disabled")
            allowed = False
        if zone != "green":
            reasons.append(f"Auto-apply blocked: zone is {zone}, must be green")
            allowed = False
        if not w.auto_apply_allowed:
            reasons.append(f"Weight {weight_key} has auto_apply_allowed=False")
            allowed = False
        if delta > w.max_auto_delta:
            reasons.append(
                f"Delta {delta:.4f} exceeds max_auto_delta {w.max_auto_delta:.4f}"
            )
            allowed = False
        if w.requires_simulation_pass and not simulation_pass:
            reasons.append("Simulation pass required but not completed")
            required_actions.append("run_simulation and confirm pass")
            allowed = False
        if w.requires_regression_pass and not regression_pass:
            reasons.append("Regression tests required but not passed")
            required_actions.append("run existing test suites and confirm pass")
            allowed = False
        if observation_count < w.min_observations:
            reasons.append(
                f"Observations {observation_count} < min_observations {w.min_observations}"
            )
            required_actions.append(f"collect at least {w.min_observations} observations")
            allowed = False

    # ── Manual apply gate ───────────────────────────────────────────────
    elif mode == "manual":
        if w.locked:
            reasons.append(f"Weight {weight_key} is locked")
            allowed = False
        if zone == "red":
            reasons.append(
                f"Zone is RED — manual apply blocked in this phase. "
                f"Requires explicit override. reason={w.guardrail_reason}"
            )
            allowed = False
        if delta > w.max_manual_delta:
            reasons.append(
                f"Delta {delta:.4f} exceeds max_manual_delta {w.max_manual_delta:.4f}"
            )
            allowed = False
        if w.requires_operator_approval and proposal_status != "approved":
            reasons.append("Weight requires operator approval but proposal is not approved")
            allowed = False

    return GuardrailResult(
        allowed=allowed,
        mode=mode,
        zone=zone,
        reasons=reasons,
        required_actions=required_actions,
        max_delta_allowed=w.max_auto_delta if mode == "auto" else w.max_manual_delta,
        actual_delta=delta,
        requires_operator_approval=w.requires_operator_approval,
        requires_simulation_pass=w.requires_simulation_pass,
        requires_regression_pass=w.requires_regression_pass,
        rollback_required=w.rollback_required,
        proposal_status_ok=(proposal_status == "approved"),
        weight_locked=w.locked,
    )
