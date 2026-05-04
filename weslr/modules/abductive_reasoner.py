"""
weslr/modules/abductive_reasoner.py
===================================
Phase 9 — Abductive Reasoner: backward-chaining explanation generation.

Author: OCC (WESLR governed intelligence) — Phase 9
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Explanation:
    """A candidate explanation for an observation."""

    hypothesis: str           # human-readable explanation text
    rules_used: list[str]     # rule names in chain
    confidence: float         # product of rule confidences
    rule_chain: list[tuple]   # [(antecedent, consequent, conf), ...]
    provenance: list[dict]    # how each rule was derived
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def score(self, domain_relevance: float = 1.0) -> float:
        """Score = confidence * parsimony_bonus * domain_relevance."""
        parsimony = 1.0 / (1.0 + 0.1 * len(self.rules_used))
        return self.confidence * parsimony * domain_relevance


@dataclass
class Rule:
    """A rule in form: antecedent → consequent, with confidence."""

    antecedent: str
    consequent: str
    confidence: float  # ∈ [0, 1]
    source: str = "unknown"  # e.g. "causality", "discovery", "user"
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = f"{self.antecedent}→{self.consequent}"

    def __repr__(self):
        return f"Rule({self.antecedent}→{self.consequent}, conf={self.confidence:.2f})"


# ── Tenant-aware rule store ──────────────────────────────────────────────────

_TENANT_RULES: dict[str, list[Rule]] = {}
_current_tenant_getter: callable = lambda: "default"

def set_tenant_getter(fn: callable) -> None:
    global _current_tenant_getter
    _current_tenant_getter = fn

def _tenant_rules() -> list[Rule]:
    return _TENANT_RULES.setdefault(_current_tenant_getter(), [])


# ── AbductiveReasoner ─────────────────────────────────────────────────────────

class AbductiveReasoner:
    """
    Backward-chaining abductive reasoner.

    Main methods:
      add_rule(antecedent, consequent, confidence, source)  — register a rule
      explain(observation, max_explanations)                 — find explanations
      load_from_causality(causal_graph)                     — import causal edges as rules
      load_from_correlations(correlations)                  — correlations → weak rules
    """

    def __init__(self, max_depth: int = 3, max_rules: int = 200):
        self.max_depth = max_depth
        self.max_rules = max_rules

    # ── Rule management ─────────────────────────────────────────────────────

    def add_rule(
        self,
        antecedent: str,
        consequent: str,
        confidence: float,
        source: str = "user",
    ) -> Rule:
        """Add a rule to the current tenant's rule base."""
        rules = _tenant_rules()
        if len(rules) >= self.max_rules:
            raise RuntimeError(f"Rule limit ({self.max_rules}) reached")
        rule = Rule(antecedent, consequent, max(0.0, min(1.0, confidence)), source)
        rules.append(rule)
        return rule

    def clear_rules(self) -> None:
        """Remove all rules for current tenant."""
        _tenant_rules().clear()

    def list_rules(self) -> list[Rule]:
        """Return all rules for current tenant."""
        return list(_tenant_rules())

    # ── Backward chaining (BFS) ─────────────────────────────────────────────

    def explain(
        self,
        observation: str,
        max_explanations: int = 3,
        domain: Optional[str] = None,
    ) -> list[Explanation]:
        """
        Find plausible explanations for `observation` by backward chaining.

        Algorithm:
          1. Find all rules R where R.consequent matches observation (depth 0).
          2. For each matched rule, recursively find rules that produce R.antecedent.
          3. Build explanation chains up to max_depth.
          4. Score and return top max_explanations.

        Ties broken deterministically by explanation id.
        """
        rules = _tenant_rules()
        observation_lower = observation.lower()

        # BFS queue: (current_node, chain_so_far)
        queue: list[tuple[str, list[Rule]]] = []
        completed: list[Explanation] = []

        # Seed: find rules that directly produce the observation
        for rule in rules:
            if self._match(rule.consequent, observation):
                queue.append((rule.antecedent, [rule]))

        visited: set[str] = set()

        while queue and len(completed) < max_explanations * 2:
            node, chain = queue.pop(0)
            node_lower = node.lower()

            if len(chain) >= self.max_depth:
                # Terminal explanation (reached depth limit)
                conf = self._chain_confidence(chain)
                rules_used = [r.name for r in chain]
                provenance = [
                    {"source": r.source, "rule": r.name, "conf": r.confidence}
                    for r in chain
                ]
                expl = Explanation(
                    hypothesis=chain[0].antecedent if chain else node,
                    rules_used=rules_used,
                    confidence=round(conf, 4),
                    rule_chain=[(r.antecedent, r.consequent, r.confidence) for r in chain],
                    provenance=provenance,
                )
                completed.append(expl)
                continue

            if node_lower in visited:
                continue
            visited.add(node_lower)


            # Find rules that produce this node
            expanded = False
            for rule in rules:
                if self._match(rule.consequent, node):
                    new_chain = chain + [rule]
                    queue.append((rule.antecedent, new_chain))
                    expanded = True

            if not expanded:
                # Leaf node — no rules can expand further; add as terminal explanation
                conf = self._chain_confidence(chain)
                rules_used = [r.name for r in chain]
                provenance = [
                    {"source": r.source, "rule": r.name, "conf": r.confidence}
                    for r in chain
                ]
                expl = Explanation(
                    hypothesis=chain[0].antecedent if chain else node,
                    rules_used=rules_used,
                    confidence=round(conf, 4),
                    rule_chain=[(r.antecedent, r.consequent, r.confidence) for r in chain],
                    provenance=provenance,
                )
                completed.append(expl)
                continue

        # Score and sort
        for e in completed:
            e.confidence = round(e.confidence, 4)
        completed.sort(
            key=lambda e: (-e.score(), e.id)  # descending score, then id tiebreak
        )
        return completed[:max_explanations]

    def _match(self, pattern: str, text: str) -> bool:
        """Case-insensitive substring match."""
        return pattern.lower() in text.lower() or text.lower() in pattern.lower()

    def _chain_confidence(self, chain: list[Rule]) -> float:
        """Product of all rule confidences in chain."""
        conf = 1.0
        for r in chain:
            conf *= r.confidence
        return conf

    # ── Load rules from external sources ────────────────────────────────────

    def load_from_causality(self, causal_graph: dict[tuple, float]) -> int:
        """
        Convert causal graph edges to abduction rules.

        causal_graph: {(cause, effect): confidence}
        Each edge becomes: cause → effect (with confidence)
        """
        count = 0
        for (cause, effect), conf in causal_graph.items():
            try:
                self.add_rule(str(cause), str(effect), float(conf), source="causality")
                count += 1
            except Exception:
                continue
        return count

    def load_from_correlations(
        self, correlations: dict[str, float], min_strength: float = 0.3
    ) -> int:
        """
        Convert correlation patterns to weak rules.

        correlations: {variable_pair: r_value}
        Both directions are added (A–B implies A→B and B→A).
        """
        count = 0
        for pair, r in correlations.items():
            if not isinstance(pair, str):
                continue
            # Parse "X vs Y" or "X , Y" or "X-Y"
            parts = [p.strip() for p in pair.replace(" vs ", ",").replace(" vs ", ",").split(",")]
            if len(parts) < 2:
                parts = pair.replace("-", " ").split()
            if len(parts) < 2:
                continue
            a, b = parts[0], parts[1]
            strength = abs(r)
            if strength < min_strength:
                continue
            try:
                self.add_rule(a, b, strength, source="correlation")
                self.add_rule(b, a, strength, source="correlation")
                count += 2
            except Exception:
                continue
        return count

    # ── Helpers ─────────────────────────────────────────────────────────────

    def get_rules_for_antecedent(self, antecedent: str) -> list[Rule]:
        """Return all rules that could produce the given antecedent."""
        return [r for r in _tenant_rules() if self._match(r.consequent, antecedent)]

    def __repr__(self) -> str:
        return f"AbductiveReasoner(rules={len(_tenant_rules())}, max_depth={self.max_depth})"