"""
weslr/modules/transfer_analogy.py
=================================
Phase 9 — Transfer Analogy Engine: cross-domain hypothesis transfer via rules.

Author: OCC (WESLR governed intelligence) — Phase 9
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Analogy:
    """A mapping between source and target domain concepts."""
    source_domain: str
    source_concept: str
    target_domain: str
    target_concept: str
    similarity_weight: float  # ∈ (0, 1]
    provenance: str = "builtin"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if not (0.0 < self.similarity_weight <= 1.0):
            raise ValueError(f"similarity_weight must be in (0, 1], got {self.similarity_weight}")

    def __repr__(self) -> str:
        return (
            f"Analogy({self.source_concept}[{self.source_domain}] → "
            f"{self.target_concept}[{self.target_domain}], "
            f"w={self.similarity_weight:.2f})"
        )


@dataclass
class TransferredHypothesis:
    """Result of transferring a hypothesis to a new domain."""
    original_id: str
    original_title: str
    target_domain: str
    transferred_title: str
    transferred_description: str
    transferred_domain: str
    adjusted_confidence: float
    analogy_rules_used: list[str]
    provenance: list[dict]
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


# ── Tenant-aware analogy store ─────────────────────────────────────────────────

_TENANT_ANALOGIES: dict[str, list[Analogy]] = {}
_current_tenant_getter: callable = lambda: "default"

def set_tenant_getter(fn: callable) -> None:
    global _current_tenant_getter
    _current_tenant_getter = fn


def _tenant_analogies() -> list[Analogy]:
    return _TENANT_ANALOGIES.setdefault(_current_tenant_getter(), [])


# ── AnalogyEngine ──────────────────────────────────────────────────────────────

class AnalogyEngine:
    """
    Cross-domain transfer via analogy rules.

    Methods:
      add_analogy(source_domain, source_concept, target_domain, target_concept, weight)
      remove_analogy(analogy_id)
      list_analogies() -> list[Analogy]
      preload_default_analogies()
      transfer_hypothesis(source_hypothesis, target_domain) -> TransferredHypothesis
      find_applicable_analogies(source_domain, source_concept) -> list[Analogy]
    """

    def __init__(self):
        self._preloaded = False

    # ── Analogy management ─────────────────────────────────────────────────

    def add_analogy(
        self,
        source_domain: str,
        source_concept: str,
        target_domain: str,
        target_concept: str,
        similarity_weight: float = 0.8,
        provenance: str = "user",
    ) -> Analogy:
        """Add an analogy mapping to the current tenant's store."""
        analogy = Analogy(
            source_domain=source_domain,
            source_concept=source_concept,
            target_domain=target_domain,
            target_concept=target_concept,
            similarity_weight=similarity_weight,
            provenance=provenance,
        )
        _tenant_analogies().append(analogy)
        return analogy

    def remove_analogy(self, analogy_id: str) -> bool:
        """Remove an analogy by id."""
        analogies = _tenant_analogies()
        for i, a in enumerate(analogies):
            if a.id == analogy_id:
                analogies.pop(i)
                return True
        return False

    def list_analogies(self) -> list[Analogy]:
        """Return all analogies for current tenant."""
        return list(_tenant_analogies())

    def clear_analogies(self) -> None:
        """Remove all user-added analogies (keep preloaded)."""
        analogies = _tenant_analogies()
        # Keep only builtin
        for i in reversed(range(len(analogies))):
            if analogies[i].provenance == "user":
                analogies.pop(i)
        # Reset preloaded flag so fixture preload can repopulate defaults if store was emptied
        self._preloaded = False

    # ── Preloaded analogies ────────────────────────────────────────────────

    DEFAULT_ANALOGIES: list[dict] = [
        # biology → chemistry
        {"source_domain": "biology", "source_concept": "enzyme", "target_domain": "chemistry",
         "target_concept": "catalyst", "weight": 0.90},
        {"source_domain": "biology", "source_concept": "receptor", "target_domain": "chemistry",
         "target_concept": "binding_site", "weight": 0.85},
        {"source_domain": "biology", "source_concept": "gene_expression", "target_domain": "chemistry",
         "target_concept": "protein_synthesis", "weight": 0.90},
        {"source_domain": "biology", "source_concept": "cell", "target_domain": "chemistry",
         "target_concept": "compartment", "weight": 0.75},
        {"source_domain": "biology", "source_concept": "kinase", "target_domain": "chemistry",
         "target_concept": "phosphorylator", "weight": 0.80},
        {"source_domain": "biology", "source_concept": "phosphatase", "target_domain": "chemistry",
         "target_concept": "dephosphorylator", "weight": 0.80},
        {"source_domain": "biology", "source_concept": "agonist", "target_domain": "biology",
         "target_concept": "activator", "weight": 0.80},
        {"source_domain": "biology", "source_concept": "antagonist", "target_domain": "biology",
         "target_concept": "inhibitor", "weight": 0.85},
        # pharmacology ↔ chemistry
        {"source_domain": "pharmacology", "source_concept": "drug", "target_domain": "chemistry",
         "target_concept": "ligand", "weight": 0.85},
        {"source_domain": "pharmacology", "source_concept": "dose_response", "target_domain": "chemistry",
         "target_concept": "binding_curve", "weight": 0.85},
        {"source_domain": "pharmacology", "source_concept": "IC50", "target_domain": "chemistry",
         "target_concept": "Ki", "weight": 0.90},
        {"source_domain": "pharmacology", "source_concept": "bioavailability", "target_domain": "chemistry",
         "target_concept": "solubility", "weight": 0.80},
        {"source_domain": "pharmacology", "source_concept": "half_life", "target_domain": "chemistry",
         "target_concept": "decay_rate", "weight": 0.85},
        # biology → biology (cross-process)
        {"source_domain": "biology", "source_concept": "pathway", "target_domain": "biology",
         "target_concept": "reaction_network", "weight": 0.80},
        {"source_domain": "biology", "source_concept": "mutation", "target_domain": "chemistry",
         "target_concept": "defect", "weight": 0.75},
        # physics → chemistry
        {"source_domain": "physics", "source_concept": "diffusion", "target_domain": "chemistry",
         "target_concept": "transport", "weight": 0.85},
        {"source_domain": "physics", "source_concept": "entropy", "target_domain": "chemistry",
         "target_concept": "free_energy", "weight": 0.80},
    ]

    def preload_default_analogies(self) -> None:
        """Load built-in analogy set into current tenant store."""
        if self._preloaded:
            return
        for data in self.DEFAULT_ANALOGIES:
            self.add_analogy(
                data["source_domain"], data["source_concept"],
                data["target_domain"], data["target_concept"],
                data["weight"],
                provenance="builtin",
            )
        self._preloaded = True

    # ── Analogy lookup ──────────────────────────────────────────────────────

    def find_analogies_by_source_domain(
        self,
        source_domain: str,
    ) -> list[Analogy]:
        """Find all analogies from a given source domain, sorted by weight descending."""
        return self.find_applicable_analogies(source_domain=source_domain)

    def find_applicable_analogies(
        self,
        source_domain: str,
        source_concept: Optional[str] = None,
    ) -> list[Analogy]:
        """
        Find analogies matching source_domain (and optionally source_concept).
        Returns all analogies where source_domain matches and optionally concept matches.
        """
        results = []
        for a in _tenant_analogies():
            if a.source_domain != source_domain:
                continue
            if source_concept and a.source_concept != source_concept:
                continue
            results.append(a)
        # Sort by weight descending
        results.sort(key=lambda x: -x.similarity_weight)
        return results

    def find_analogies_for_hypothesis(self, hypothesis) -> list[Analogy]:
        """Find all analogies applicable to a hypothesis based on its domain."""
        domain = hypothesis.domain if hasattr(hypothesis, "domain") else str(hypothesis.get("domain", ""))
        return self.find_applicable_analogies(domain)

    # ── Hypothesis transfer ─────────────────────────────────────────────────

    def transfer_hypothesis(
        self,
        source_hypothesis,
        target_domain: str,
    ) -> Optional[TransferredHypothesis]:
        """
        Transfer a hypothesis to a new domain using applicable analogies.

        Steps:
          1. Find analogies where source_domain == hypothesis.domain
          2. Build substitution map: source_concept → target_concept
          3. Apply substitutions to title, description, metadata
          4. Adjust confidence: new_conf = original_conf * min(applicable_analogy_weights)
          5. Provenance: record each analogy used
          6. Return TransferredHypothesis (caller should save to repo)
        """
        source_domain = source_hypothesis.domain if hasattr(source_hypothesis, "domain") else "unknown"
        source_id = source_hypothesis.id if hasattr(source_hypothesis, "id") else str(source_hypothesis.get("id", ""))
        source_title = source_hypothesis.title if hasattr(source_hypothesis, "title") else str(source_hypothesis.get("title", ""))
        source_desc = source_hypothesis.description if hasattr(source_hypothesis, "description") else str(source_hypothesis.get("description", ""))
        source_conf = source_hypothesis.confidence if hasattr(source_hypothesis, "confidence") else float(source_hypothesis.get("confidence", 0.5))
        source_metadata = source_hypothesis.metadata if hasattr(source_hypothesis, "metadata") else dict(source_hypothesis.get("metadata", {}))

        analogies = self.find_applicable_analogies(source_domain)
        if not analogies:
            return None

        # Build substitution map (source → target) filtered by target_domain
        sub_map: dict[str, str] = {}
        used_analogy_ids: list[str] = []
        max_weight = 0.0

        for a in analogies:
            if a.target_domain != target_domain:
                continue
            sub_map[a.source_concept] = a.target_concept
            used_analogy_ids.append(a.id)
            max_weight = max(max_weight, a.similarity_weight)

        if not sub_map:
            return None

        # Apply substitutions
        new_title = self._substitute_text(source_title, sub_map)
        new_desc = self._substitute_text(source_desc, sub_map)

        adjusted_conf = round(source_conf * max_weight, 4)

        provenance = [
            {
                "action": "transfer",
                "source_id": source_id,
                "target_domain": target_domain,
                "analogy_id": a_id,
                "confidence_adjustment": max_weight,
            }
            for a_id in used_analogy_ids
        ]

        return TransferredHypothesis(
            original_id=source_id,
            original_title=source_title,
            target_domain=target_domain,
            transferred_title=new_title,
            transferred_description=new_desc,
            transferred_domain=target_domain,
            adjusted_confidence=adjusted_conf,
            analogy_rules_used=used_analogy_ids,
            provenance=provenance,
        )

    def _substitute_text(self, text: str, sub_map: dict[str, str]) -> str:
        """Apply substitutions to text, case-insensitive word-boundary replacement."""
        result = text
        for src, tgt in sub_map.items():
            # Replace whole-word case-insensitive
            import re
            pattern = re.compile(rf'\b{re.escape(src)}\b', re.IGNORECASE)
            result = pattern.sub(tgt, result)
        return result

    def __repr__(self) -> str:
        return f"AnalogyEngine(analogies={len(_tenant_analogies())})"