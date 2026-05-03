"""
weslr/modules/hypothesis_repository.py
======================================
Phase 7 — Hypothesis Repository: store, version, compare hypotheses per tenant.

Author: OCC (WESLR governed intelligence) — Phase 7
"""

from __future__ import annotations

import uuid
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# ── Tenant isolation ────────────────────────────────────────────────────────

# In a real system this would come from the auth context. Here we use a module-
# level getter so tests can override it without patching every call site.

_TENANT_GETTER: callable = lambda: "default"


def set_tenant_getter(fn: callable) -> None:
    """Override the tenant-ID getter (for testing)."""
    global _TENANT_GETTER
    _TENANT_GETTER = fn


def get_current_tenant_id() -> str:
    """Return the current tenant ID from the configured getter."""
    return _TENANT_GETTER()


def _make_hypothesis_id(tenant_id: str, title: str, created_at: datetime) -> str:
    """Generate a deterministic UUID v5 for a hypothesis.

    Same tenant + title + UTC hour → same ID across restarts.
    """
    hour_iso = created_at.replace(minute=0, second=0, microsecond=0).isoformat()
    namespace = uuid.uuid5(uuid.NAMESPACE_DNS, f"{tenant_id}:{hour_iso}")
    return str(uuid.uuid5(namespace, title))


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class Hypothesis:
    """A single hypothesis with provenance tracking.

    Parameters
    ----------
    title : str
        Short human-readable title.
    description : str
        Detailed description of the hypothesis.
    domain : str
        One of: discovery, causality, simulation, spatial, temporal, quantum, mixed.
    confidence : float
        Confidence score in [0, 1].
    provenance : list[dict]
        List of provenance entries. Each entry is a dict with keys:
        source (module name), timestamp (ISO str), action (str),
        parameters (dict), result (optional dict).
    created_at : datetime
        UTC creation timestamp.
    updated_at : datetime
        UTC last-update timestamp.
    status : str
        One of: draft, active, deprecated.
    metadata : dict
        Module-specific data. Known keys:
        - causal_graph: {(cause, effect): confidence} dict
        - correlation: {variable_pair: r_value} dict
        - simulation_model: str
        - simulation_params: dict
        - forecast_horizon: int (days)
        - spatial_geometry: dict
        - quantum_circuit: str
    id : str
        UUID v5, auto-generated.
    """

    title: str
    description: str = ""
    domain: str = "mixed"
    confidence: float = 0.5
    provenance: list[dict] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "draft"
    metadata: dict = field(default_factory=dict)
    id: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at
        # ID is assigned by HypothesisRepository.add() for determinism
        # (uses tenant context at add-time). Default to empty until stored.
        if not self.id:
            self.id = ""

    # ── Provenance helpers ────────────────────────────────────────────────

    def update_provenance(
        self,
        action: str,
        source: str = "unknown",
        parameters: Optional[dict] = None,
        result: Optional[dict] = None,
    ) -> None:
        """Append a provenance entry."""
        self.provenance.append(
            {
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "parameters": parameters or {},
                "result": result or {},
            }
        )
        self.updated_at = datetime.now(timezone.utc)

    def add_evidence(self, key: str, value, source: str = "unknown") -> None:
        """Add a piece of evidence to metadata.evidence list."""
        self.metadata.setdefault("evidence", []).append(
            {"key": key, "value": value, "source": source, "added_at": datetime.now(timezone.utc).isoformat()}
        )


@dataclass
class HypothesisComparison:
    """Result of comparing two hypotheses."""

    id1: str
    id2: str
    title1: str
    title2: str
    confidence_delta: float  # positive = id2 higher
    status_match: bool
    domain_match: bool
    jaccard_overlap: float  # keyword overlap 0–1
    shared_keywords: list[str]
    unique_to_1: list[str]
    unique_to_2: list[str]
    provenance_common: list[str]  # sources present in both
    narrative: str


# ── Repository ──────────────────────────────────────────────────────────────

# Re-export for convenience
HypothesisOrID = str  # either a Hypothesis object or its string ID


class HypothesisRepository:
    """Per-tenant in-memory hypothesis store.

    All methods are tenant-aware via get_current_tenant_id().
    Storage is a flat dict: tenant_id → {hypothesis_id: Hypothesis}
    """

    def __init__(self):
        # {tenant_id: {hypothesis_id: Hypothesis}}
        self._store: dict[str, dict[str, Hypothesis]] = {}

    # ── Internal ─────────────────────────────────────────────────────────

    def _tenant_store(self) -> dict[str, Hypothesis]:
        tid = get_current_tenant_id()
        if tid not in self._store:
            self._store[tid] = {}
        return self._store[tid]

    # ── CRUD ─────────────────────────────────────────────────────────────

    def add(self, hypothesis: Hypothesis) -> Hypothesis:
        """Store a hypothesis. Returns the hypothesis (with final id)."""
        store = self._tenant_store()
        hypothesis.id = _make_hypothesis_id(
            get_current_tenant_id(),
            hypothesis.title,
            hypothesis.created_at or datetime.now(timezone.utc),
        )
        store[hypothesis.id] = hypothesis
        return hypothesis

    def get(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Retrieve by ID, or None if not found / wrong tenant."""
        return self._tenant_store().get(hypothesis_id)

    def list(
        self,
        status: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> list[Hypothesis]:
        """List all hypotheses, optionally filtered by status or domain."""
        hypotheses = list(self._tenant_store().values())
        if status:
            hypotheses = [h for h in hypotheses if h.status == status]
        if domain:
            hypotheses = [h for h in hypotheses if h.domain == domain]
        return sorted(hypotheses, key=lambda h: h.created_at, reverse=True)

    def update(self, hypothesis_id: str, **changes) -> Optional[Hypothesis]:
        """Merge changes into an existing hypothesis."""
        h = self.get(hypothesis_id)
        if h is None:
            return None
        for key, value in changes.items():
            if hasattr(h, key) and key not in ("id", "created_at"):
                setattr(h, key, value)
        h.updated_at = datetime.now(timezone.utc)
        return h

    def delete(self, hypothesis_id: str) -> bool:
        """Remove a hypothesis. Returns True if found and deleted."""
        store = self._tenant_store()
        if hypothesis_id in store:
            del store[hypothesis_id]
            return True
        return False

    def get_active(self) -> Optional[Hypothesis]:
        """Return the currently active hypothesis, if any."""
        candidates = self.list(status="active")
        return candidates[0] if candidates else None

    def set_active(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Deprecate any current active; set this one as active."""
        # Deprecate current active
        current = self.get_active()
        if current and current.id != hypothesis_id:
            self.update(current.id, status="deprecated")
        # Set new active
        return self.update(hypothesis_id, status="active")

    # ── Comparison ───────────────────────────────────────────────────────

    @staticmethod
    def _keywords(hypothesis: Hypothesis) -> set[str]:
        """Extract a normalised keyword set from title + description."""
        text = f"{hypothesis.title} {hypothesis.description}".lower()
        # Split on whitespace + punctuation
        words = set(
            w.strip(".,!?;:()[]{}")
            for w in text.split()
            if len(w) > 2
        )
        return words

    def compare(self, id1: str, id2: str) -> Optional[HypothesisComparison]:
        """Compare two hypotheses. Returns None if either ID not found."""
        h1 = self.get(id1)
        h2 = self.get(id2)
        if h1 is None or h2 is None:
            return None

        kw1 = self._keywords(h1)
        kw2 = self._keywords(h2)
        shared = kw1 & kw2
        union = kw1 | kw2
        jaccard = len(shared) / len(union) if union else 0.0

        provenance_sources_1 = {p["source"] for p in h1.provenance}
        provenance_sources_2 = {p["source"] for p in h2.provenance}
        common_sources = list(provenance_sources_1 & provenance_sources_2)

        conf_delta = round(h2.confidence - h1.confidence, 4)

        if conf_delta > 0:
            narrative = (
                f"'{h2.title}' has higher confidence (+{conf_delta}) than "
                f"'{h1.title}'. "
            )
        elif conf_delta < 0:
            narrative = (
                f"'{h1.title}' has higher confidence ({abs(conf_delta)}) than "
                f"'{h2.title}'. "
            )
        else:
            narrative = f"Both hypotheses have equal confidence ({h1.confidence}). "

        if shared:
            narrative += f"Shared keywords: {', '.join(sorted(shared)[:10])}."
        if common_sources:
            narrative += f" Both share evidence from: {', '.join(sorted(common_sources))}."

        return HypothesisComparison(
            id1=id1,
            id2=id2,
            title1=h1.title,
            title2=h2.title,
            confidence_delta=conf_delta,
            status_match=h1.status == h2.status,
            domain_match=h1.domain == h2.domain,
            jaccard_overlap=round(jaccard, 4),
            shared_keywords=sorted(shared),
            unique_to_1=sorted(kw1 - kw2),
            unique_to_2=sorted(kw2 - kw1),
            provenance_common=common_sources,
            narrative=narrative.strip(),
        )

    # ── Formatting ────────────────────────────────────────────────────────

    @staticmethod
    def format_hypothesis(h: Hypothesis) -> str:
        """Render a hypothesis as a readable string."""
        domain_emoji = {
            "discovery": "🔍",
            "causality": "🔗",
            "simulation": "🧪",
            "spatial": "🗺",
            "temporal": "⏱",
            "quantum": "⚛",
            "mixed": "🔬",
        }
        emoji = domain_emoji.get(h.domain, "🔬")
        lines = [
            f"{emoji} Hypothesis: {h.title}",
            f"   ID: {h.id}",
            f"   Status: {h.status.upper()}  |  Domain: {h.domain}  |  Confidence: {h.confidence:.2f}",
        ]
        if h.description:
            lines.append(f"   Description: {textwrap.fill(h.description, width=70, subsequent_indent='   ')}")
        if h.provenance:
            lines.append("   Provenance:")
            for p in h.provenance[-3:]:  # show last 3 entries
                lines.append(
                    f"     • [{p['source']}] {p['action']} "
                    f"({p.get('timestamp', '')[:16]})"
                )
        if h.metadata:
            meta_keys = list(h.metadata.keys())
            lines.append(f"   Metadata keys: {', '.join(meta_keys)}")
        return "\n".join(lines)

    @staticmethod
    def format_comparison(c: HypothesisComparison) -> str:
        """Render a hypothesis comparison as a table."""
        lines = [
            "Hypothesis Comparison",
            "=" * 60,
            f"{'Field':<20} {'Hypothesis 1':<30} {'Hypothesis 2':<30}",
            "-" * 60,
            f"{'ID':<20} {c.id1:<30} {c.id2:<30}",
            f"{'Title':<20} {c.title1[:29]:<30} {c.title2[:29]:<30}",
            f"{'Confidence':<20} {'':<30} {c.confidence_delta:+.4f}",
            f"{'Status match':<20} {'YES' if c.status_match else 'NO':<30}",
            f"{'Domain match':<20} {'YES' if c.domain_match else 'NO':<30}",
            f"{'Jaccard overlap':<20} {c.jaccard_overlap:.4f}",
        ]
        if c.shared_keywords:
            lines.append(f"{'Shared keywords':<20} {', '.join(c.shared_keywords[:8])}")
        if c.unique_to_1:
            lines.append(f"{'Unique to 1':<20} {', '.join(c.unique_to_1[:8])}")
        if c.unique_to_2:
            lines.append(f"{'Unique to 2':<20} {', '.join(c.unique_to_2[:8])}")
        lines.extend(["", c.narrative])
        return "\n".join(lines)

    @staticmethod
    def format_list(hypotheses: list[Hypothesis]) -> str:
        """Render a list of hypotheses as a compact table."""
        if not hypotheses:
            return "No hypotheses found."
        lines = [f"{'ID':<38} {'Title':<35} {'Status':<8} {'Conf'}"]
        lines.append("-" * 95)
        for h in hypotheses:
            title = (h.title[:33] + "…") if len(h.title) > 34 else h.title
            lines.append(f"{h.id:<38} {title:<35} {h.status:<8} {h.confidence:.2f}")
        return "\n".join(lines)