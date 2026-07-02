"""WESLR Primitive-Space Grid/Graph Cartographer.

Builds an in-memory primitive-space map from:
- BH80 accepted primitives
- Promoted native primitives (color_invert)
- Generated native candidate primitives
- Discovery 120 candidate-probe metadata
- Promotion maturity status

Produces coverage grids, primitive graph, gap detection (R1-R9),
gap scoring, perspicuity integration, and output artifacts.

Deterministic: same input → same output.
No file IO. No .weslr IO. No runtime/chat/UI/provider paths.
Does NOT promote primitives. Does NOT count candidates as solved.
Does NOT change BH80 or 120 scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from weslr.native_arc_candidate_generator import generate_candidates
from weslr.native_arc_language_schema import PromotionStage
from weslr.native_arc_perspicuity import (
    PROMOTED_PRIMITIVES,
    BH80_ACCEPTED_PRIMITIVES,
    SEMANTIC_SIMILARITY,
    COMPLEXITY_ESTIMATES,
    CANDIDATE_PROBE_TASKS,
    CANDIDATE_FAMILY_NOVELTY,
)
from weslr.arc_discovery_120_generator import generate_discovery_120_tasks


# ---------------------------------------------------------------------------
# Axis definitions
# ---------------------------------------------------------------------------

FAMILIES = [
    "selection", "extraction", "cropping", "color", "geometry",
    "topology", "construction", "relation", "pattern", "conditional",
    "counting", "normalization", "placement", "noise_safety",
]

TARGETS = [
    "cell", "object", "object_set", "mask", "region",
    "bounding_box", "whole_grid", "pattern", "relation", "count_output",
]

ROLES = [
    "selector", "reducer", "expander", "constructor", "modifier",
    "comparator", "normalizer", "compositor", "brancher",
]

MATURITIES = [
    "accepted_bh80", "promoted_native", "generated_candidate",
    "typed", "executable", "oracle_defined", "solver_targeted",
    "tested", "promoted", "missing",
]

# ---------------------------------------------------------------------------
# Primitive → (family, target, role) classification
# ---------------------------------------------------------------------------

# BH80 primitive classifications
BH80_CLASSIFICATION: Dict[str, Tuple[str, str, str]] = {
    "count": ("counting", "count_output", "reducer"),
    "count_objects": ("counting", "object_set", "reducer"),
    "count_or_pattern": ("counting", "whole_grid", "reducer"),
    "crop": ("cropping", "bounding_box", "reducer"),
    "crop_object": ("cropping", "object", "reducer"),
    "extract": ("extraction", "object", "selector"),
    "extract_boundary": ("extraction", "bounding_box", "selector"),
    "extract_changed_region": ("extraction", "region", "selector"),
    "extract_object": ("extraction", "object", "selector"),
    "fill_region": ("noise_safety", "whole_grid", "modifier"),
    "isolate_largest": ("selection", "object", "selector"),
    "mirror_object": ("geometry", "whole_grid", "modifier"),
    "normalize_position": ("normalization", "object", "normalizer"),
    "pattern_output": ("pattern", "whole_grid", "expander"),
    "place_back": ("placement", "whole_grid", "constructor"),
    "recolor": ("color", "whole_grid", "modifier"),
    "recolor_boundary": ("color", "bounding_box", "modifier"),
    "remove_noise": ("noise_safety", "whole_grid", "modifier"),
    "rotate": ("geometry", "whole_grid", "modifier"),
    "transform": ("geometry", "whole_grid", "modifier"),
}

# Candidate classifications (family, target, role)
CANDIDATE_CLASSIFICATION: Dict[str, Tuple[str, str, str]] = {
    # object_selector
    "sel_leftmost": ("selection", "object", "selector"),
    "sel_topmost": ("selection", "object", "selector"),
    "sel_smallest": ("selection", "object", "selector"),
    "sel_most_holes": ("selection", "object", "selector"),
    "sel_edge_touch": ("selection", "object", "selector"),
    # mask_algebra
    "mask_union": ("noise_safety", "mask", "modifier"),
    "mask_intersect": ("noise_safety", "mask", "modifier"),
    "mask_complement": ("noise_safety", "mask", "modifier"),
    "mask_border_only": ("extraction", "mask", "selector"),
    # color_transform
    "color_swap_1_2": ("color", "whole_grid", "modifier"),
    "color_gradient": ("color", "whole_grid", "expander"),
    "color_invert": ("color", "whole_grid", "modifier"),
    "color_dominant": ("color", "whole_grid", "modifier"),
    # geometry_transform
    "geom_scale_2x": ("geometry", "whole_grid", "expander"),
    "geom_translate_center": ("normalization", "whole_grid", "normalizer"),
    "geom_flip_vertical": ("geometry", "whole_grid", "modifier"),
    # topology_transform
    "topo_merge_objects": ("topology", "object_set", "constructor"),
    "topo_fill_holes": ("topology", "object", "modifier"),
    "topo_split_at_gap": ("topology", "object", "modifier"),
    # relation_transform
    "rel_align_centroids": ("relation", "object_set", "modifier"),
    "rel_swap_positions": ("relation", "object_set", "modifier"),
    "rel_order_by_size": ("relation", "relation", "modifier"),
    # construction_transform
    "constr_draw_rect_around": ("construction", "bounding_box", "constructor"),
    "constr_extend_pattern": ("construction", "pattern", "constructor"),
    "constr_connect_line": ("construction", "whole_grid", "constructor"),
    "constr_copy_to_pos": ("construction", "object", "constructor"),
    # pattern_transform
    "pat_row_alternate": ("pattern", "whole_grid", "expander"),
    "pat_block_repeat": ("pattern", "whole_grid", "expander"),
    "pat_color_cycle": ("pattern", "whole_grid", "expander"),
    # conditional_transform
    "cond_if_holes_fill": ("conditional", "whole_grid", "brancher"),
    "cond_if_multi_count": ("conditional", "count_output", "brancher"),
    "cond_if_edge_clip": ("conditional", "whole_grid", "brancher"),
}


# ---------------------------------------------------------------------------
# Primitive record
# ---------------------------------------------------------------------------

@dataclass
class PrimitiveRecord:
    primitive_id: str
    source: str  # "bh80" | "native_promoted" | "native_candidate"
    family: str
    target_domain: str
    role: str
    maturity: str
    expression: str
    promoted: bool
    can_be_counted_as_solved: bool
    appears_in_tasks: List[str]
    duplicate_risk: float
    gap_fill_score: float
    task_unlock_score: float
    risk_flags: Dict[str, Any]
    recommendation: str  # "promote_now" | "defer" | "discard" | "accepted" | "already_promoted"


# ---------------------------------------------------------------------------
# Graph structures
# ---------------------------------------------------------------------------

@dataclass
class GraphNode:
    node_id: str
    node_type: str  # "primitive" | "candidate" | "task" | "family" | "type_signature" | "invariant" | "audit" | "stage"
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    edge_type: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrimitiveGraph:
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    node_index: Dict[str, GraphNode] = field(default_factory=dict)

    def add_node(self, node: GraphNode) -> None:
        if node.node_id not in self.node_index:
            self.nodes.append(node)
            self.node_index[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)

    def neighbors(self, node_id: str, edge_type: Optional[str] = None) -> List[str]:
        result = []
        for e in self.edges:
            if e.source_id == node_id and (edge_type is None or e.edge_type == edge_type):
                result.append(e.target_id)
            elif e.target_id == node_id and (edge_type is None or e.edge_type == edge_type):
                result.append(e.source_id)
        return result

    def edges_of(self, node_id: str, edge_type: Optional[str] = None) -> List[GraphEdge]:
        result = []
        for e in self.edges:
            if (e.source_id == node_id or e.target_id == node_id) and (edge_type is None or e.edge_type == edge_type):
                result.append(e)
        return result


# ---------------------------------------------------------------------------
# Cartographer
# ---------------------------------------------------------------------------

class PrimitiveSpaceCartographer:
    """Builds the primitive-space map with coverage grids, graph, and gap analysis."""

    def __init__(self) -> None:
        self.records: List[PrimitiveRecord] = []
        self.records_by_id: Dict[str, PrimitiveRecord] = {}
        self.graph: PrimitiveGraph = PrimitiveGraph()
        self._build()

    def _build(self) -> None:
        """Build the full cartographer state deterministically."""
        candidates, families, _ = generate_candidates()
        tasks = generate_discovery_120_tasks()

        # Build task appearance map
        task_appearance: Dict[str, List[str]] = {}
        for t in tasks:
            for p in t["primitive_sequence"]:
                task_appearance.setdefault(p, []).append(t["task_id"])

        # Build candidate lookup
        candidate_lookup: Dict[str, Any] = {c.primitive_id: c for c in candidates}

        # --- Build BH80 records ---
        for pid in sorted(BH80_ACCEPTED_PRIMITIVES):
            fam, target, role = BH80_CLASSIFICATION.get(pid, ("noise_safety", "whole_grid", "modifier"))
            rec = PrimitiveRecord(
                primitive_id=pid,
                source="bh80",
                family=fam,
                target_domain=target,
                role=role,
                maturity="accepted_bh80",
                expression="",
                promoted=True,
                can_be_counted_as_solved=True,
                appears_in_tasks=task_appearance.get(pid, []),
                duplicate_risk=0.0,
                gap_fill_score=0.0,
                task_unlock_score=0.0,
                risk_flags={},
                recommendation="accepted",
            )
            self.records.append(rec)
            self.records_by_id[pid] = rec

        # --- Build promoted native records ---
        for pid in sorted(PROMOTED_PRIMITIVES):
            c = candidate_lookup.get(pid)
            fam, target, role = CANDIDATE_CLASSIFICATION.get(pid, ("color", "whole_grid", "modifier"))
            expr = c.internal_expression if c else ""
            rec = PrimitiveRecord(
                primitive_id=pid,
                source="native_promoted",
                family=fam,
                target_domain=target,
                role=role,
                maturity="promoted_native",
                expression=expr,
                promoted=True,
                can_be_counted_as_solved=True,
                appears_in_tasks=task_appearance.get(pid, []),
                duplicate_risk=0.0,
                gap_fill_score=0.0,
                task_unlock_score=0.0,
                risk_flags={},
                recommendation="already_promoted",
            )
            self.records.append(rec)
            self.records_by_id[pid] = rec

        # --- Build candidate records ---
        for c in candidates:
            pid = c.primitive_id
            if pid in PROMOTED_PRIMITIVES:
                continue  # already handled

            fam, target, role = CANDIDATE_CLASSIFICATION.get(pid, ("noise_safety", "whole_grid", "modifier"))
            dup_risk = SEMANTIC_SIMILARITY.get(pid, ("", 0.3))[1]
            oracle_cx, solver_cx = COMPLEXITY_ESTIMATES.get(pid, (0.5, 0.5))
            promo_diff = min(1.0, (oracle_cx + solver_cx) / 2.0 + 0.1)
            is_new_family = CANDIDATE_FAMILY_NOVELTY.get(pid, False)
            has_probe = pid in CANDIDATE_PROBE_TASKS
            probe_info = CANDIDATE_PROBE_TASKS.get(pid, {})
            ts_value, exp_gain = self._compute_task_space_value(pid, is_new_family, has_probe)
            reg_risk = self._compute_regression_risk(pid, dup_risk)

            # Gap fill score
            family_has_promoted = self._family_has_promoted(fam)
            if not family_has_promoted:
                gap_fill = 1.0
            elif self._cell_is_empty_or_candidate_only(fam, target, role):
                gap_fill = 0.6
            else:
                gap_fill = 0.3

            # Task unlock score
            task_unlock = float(exp_gain) / 20.0  # normalize 0-1

            # Recommendation
            rec_status, reason_codes = self._make_recommendation(
                pid, dup_risk, promo_diff, ts_value, reg_risk, has_probe, is_new_family, family_has_promoted
            )

            risk_flags = {
                "duplicate_risk": round(dup_risk, 2),
                "regression_risk": round(reg_risk, 2),
                "shortcut_risk": 0.3,  # from static scoring
                "promotion_difficulty": round(promo_diff, 2),
                "oracle_complexity": round(oracle_cx, 2),
                "solver_complexity": round(solver_cx, 2),
            }

            rec = PrimitiveRecord(
                primitive_id=pid,
                source="native_candidate",
                family=fam,
                target_domain=target,
                role=role,
                maturity="generated_candidate",
                expression=c.internal_expression,
                promoted=False,
                can_be_counted_as_solved=False,
                appears_in_tasks=task_appearance.get(pid, []),
                duplicate_risk=dup_risk,
                gap_fill_score=gap_fill,
                task_unlock_score=task_unlock,
                risk_flags=risk_flags,
                recommendation=rec_status,
            )
            self.records.append(rec)
            self.records_by_id[pid] = rec

        # --- Build graph ---
        self._build_graph(tasks, task_appearance)

    def _compute_task_space_value(self, pid: str, is_new_family: bool, has_probe: bool) -> Tuple[float, int]:
        if pid in PROMOTED_PRIMITIVES:
            return 0.0, 0
        family_bonus = 0.3 if is_new_family else 0.0
        probe_bonus = 0.2 if has_probe else 0.0
        base = 0.4 + family_bonus + probe_bonus
        expected_gain = 10 if has_probe else 5
        return min(1.0, base), expected_gain

    def _compute_regression_risk(self, pid: str, dup_risk: float) -> float:
        reg = dup_risk * 0.5
        dimension_changers = {"geom_scale_2x", "topo_split_at_gap", "constr_extend_pattern"}
        if pid in dimension_changers:
            reg += 0.2
        connectivity_changers = {"topo_merge_objects", "topo_split_at_gap", "rel_swap_positions"}
        if pid in connectivity_changers:
            reg += 0.1
        return min(1.0, reg)

    def _family_has_promoted(self, family: str) -> bool:
        for r in self.records:
            if r.family == family and (r.source == "bh80" or r.source == "native_promoted"):
                return True
        return False

    def _cell_is_empty_or_candidate_only(self, family: str, target: str, role: str) -> bool:
        has_accepted = any(
            r.family == family and r.target_domain == target and r.role == role
            and (r.source == "bh80" or r.source == "native_promoted")
            for r in self.records
        )
        return not has_accepted

    def _make_recommendation(
        self, pid: str, dup_risk: float, promo_diff: float,
        ts_value: float, reg_risk: float, has_probe: bool,
        is_new_family: bool, family_has_promoted: bool,
    ) -> Tuple[str, List[str]]:
        reasons: List[str] = []

        if dup_risk > 0.7:
            reasons.append("high_duplicate_risk")
        if promo_diff > 0.6:
            reasons.append("high_promotion_difficulty")
        if reg_risk > 0.5:
            reasons.append("high_regression_risk")
        if not has_probe:
            reasons.append("no_probe_task")
        if not family_has_promoted:
            reasons.append("fills_full_family_gap")
        if has_probe:
            reasons.append("has_probe_task")
        if is_new_family:
            reasons.append("new_family")
        if promo_diff < 0.4:
            reasons.append("low_promotion_difficulty")
        if dup_risk < 0.5:
            reasons.append("low_duplicate_risk")

        # Score estimate
        score = 0.25 * 0.8 + 0.10 * (1.0 if has_probe else 0.3) + 0.15 * (1.0 - promo_diff) + \
                0.20 * ts_value + 0.10 * (1.0 - dup_risk) + 0.10 * (1.0 - reg_risk) + 0.10 * (1.0 if not family_has_promoted else 0.0)

        if score >= 0.65 and promo_diff < 0.5:
            return "promote_now", reasons
        if score >= 0.55:
            return "defer", reasons + ["borderline_score"]
        return "discard", reasons + ["low_score"]

    # -----------------------------------------------------------------------
    # Graph construction
    # -----------------------------------------------------------------------

    def _build_graph(self, tasks: List[dict], task_appearance: Dict[str, List[str]]) -> None:
        """Build the primitive graph with nodes and edges."""
        # Add primitive/candidate nodes
        for rec in self.records:
            node_type = "primitive" if rec.promoted else "candidate"
            self.graph.add_node(GraphNode(
                node_id=f"prim:{rec.primitive_id}",
                node_type=node_type,
                label=rec.primitive_id,
                metadata={"family": rec.family, "target": rec.target_domain, "role": rec.role, "maturity": rec.maturity},
            ))

        # Add family nodes
        for fam in FAMILIES:
            self.graph.add_node(GraphNode(
                node_id=f"family:{fam}",
                node_type="family",
                label=fam,
            ))

        # Add task nodes
        for t in tasks:
            self.graph.add_node(GraphNode(
                node_id=f"task:{t['task_id']}",
                node_type="task",
                label=t["task_id"],
                metadata={"scoring_layer": t.get("scoring_layer", "scored")},
            ))

        # family_member edges
        for rec in self.records:
            self.graph.add_edge(GraphEdge(
                source_id=f"prim:{rec.primitive_id}",
                target_id=f"family:{rec.family}",
                edge_type="family_member",
            ))

        # appears_in_task edges
        for pid, task_ids in task_appearance.items():
            for tid in task_ids:
                if f"prim:{pid}" in self.graph.node_index and f"task:{tid}" in self.graph.node_index:
                    self.graph.add_edge(GraphEdge(
                        source_id=f"prim:{pid}",
                        target_id=f"task:{tid}",
                        edge_type="appears_in_task",
                    ))

        # composes_with edges (primitives that co-occur in 3-step chains)
        composes_seen: Set[Tuple[str, str]] = set()
        for t in tasks:
            prims = t["primitive_sequence"]
            for i in range(len(prims)):
                for j in range(i + 1, len(prims)):
                    pair = tuple(sorted([prims[i], prims[j]]))
                    if pair not in composes_seen:
                        composes_seen.add(pair)
                        p1, p2 = pair
                        if f"prim:{p1}" in self.graph.node_index and f"prim:{p2}" in self.graph.node_index:
                            self.graph.add_edge(GraphEdge(
                                source_id=f"prim:{p1}",
                                target_id=f"prim:{p2}",
                                edge_type="composes_with",
                                metadata={"evidence": t["task_id"]},
                            ))

        # aliases_or_duplicates edges
        for pid, (similar_to, similarity) in SEMANTIC_SIMILARITY.items():
            if similarity >= 0.4 and f"prim:{pid}" in self.graph.node_index and f"prim:{similar_to}" in self.graph.node_index:
                self.graph.add_edge(GraphEdge(
                    source_id=f"prim:{pid}",
                    target_id=f"prim:{similar_to}",
                    edge_type="aliases_or_duplicates",
                    weight=similarity,
                ))

        # has_oracle / has_solver edges
        for rec in self.records:
            if rec.source == "bh80":
                self.graph.add_edge(GraphEdge(
                    source_id=f"prim:{rec.primitive_id}",
                    target_id="audit:oracle_defined",
                    edge_type="has_oracle",
                ))
                self.graph.add_edge(GraphEdge(
                    source_id=f"prim:{rec.primitive_id}",
                    target_id="audit:solver_targeted",
                    edge_type="has_solver",
                ))
            elif rec.source == "native_promoted":
                self.graph.add_edge(GraphEdge(
                    source_id=f"prim:{rec.primitive_id}",
                    target_id="audit:oracle_defined",
                    edge_type="has_oracle",
                ))
                self.graph.add_edge(GraphEdge(
                    source_id=f"prim:{rec.primitive_id}",
                    target_id="audit:solver_targeted",
                    edge_type="has_solver",
                ))

        # Add audit nodes
        self.graph.add_node(GraphNode(node_id="audit:oracle_defined", node_type="audit", label="oracle_defined"))
        self.graph.add_node(GraphNode(node_id="audit:solver_targeted", node_type="audit", label="solver_targeted"))

        # unlocks_task edges (candidate probes → tasks)
        for pid, probe_info in CANDIDATE_PROBE_TASKS.items():
            tid = probe_info.get("task_id")
            if tid and f"prim:{pid}" in self.graph.node_index and f"task:{tid}" in self.graph.node_index:
                self.graph.add_edge(GraphEdge(
                    source_id=f"prim:{pid}",
                    target_id=f"task:{tid}",
                    edge_type="unlocks_task",
                ))

    # -----------------------------------------------------------------------
    # Coverage grids
    # -----------------------------------------------------------------------

    def coverage_grid_family_maturity(self) -> List[Dict[str, Any]]:
        """Family × Maturity coverage grid."""
        result = []
        for fam in FAMILIES:
            row = {"family": fam}
            for mat in MATURITIES[:4]:  # first 4 maturity levels
                count = sum(1 for r in self.records if r.family == fam and r.maturity == mat)
                row[mat] = count
            row["missing"] = sum(1 for r in self.records if r.family == fam and r.maturity == "missing")
            result.append(row)
        return result

    def coverage_grid_family_target(self) -> Dict[str, Dict[str, str]]:
        """Family × Target coverage grid."""
        grid: Dict[str, Dict[str, str]] = {}
        for fam in FAMILIES:
            grid[fam] = {}
            for target in TARGETS:
                accepted = sum(1 for r in self.records if r.family == fam and r.target_domain == target and r.source in ("bh80", "native_promoted"))
                promoted = sum(1 for r in self.records if r.family == fam and r.target_domain == target and r.source == "native_promoted")
                candidates = sum(1 for r in self.records if r.family == fam and r.target_domain == target and r.source == "native_candidate")
                parts = []
                if accepted > 0:
                    parts.append(f"{accepted}a")
                if promoted > 0:
                    parts.append(f"{promoted}p")
                if candidates > 0:
                    parts.append(f"{candidates}c")
                grid[fam][target] = "+".join(parts) if parts else "—"
        return grid

    def coverage_grid_family_role(self) -> Dict[str, Dict[str, str]]:
        """Family × Role coverage grid."""
        grid: Dict[str, Dict[str, str]] = {}
        for fam in FAMILIES:
            grid[fam] = {}
            for role in ROLES:
                accepted = sum(1 for r in self.records if r.family == fam and r.role == role and r.source in ("bh80", "native_promoted"))
                candidates = sum(1 for r in self.records if r.family == fam and r.role == role and r.source == "native_candidate")
                parts = []
                if accepted > 0:
                    parts.append(f"{accepted}a")
                if candidates > 0:
                    parts.append(f"{candidates}c")
                grid[fam][role] = "+".join(parts) if parts else "—"
        return grid

    # -----------------------------------------------------------------------
    # Gap detection (R1-R9)
    # -----------------------------------------------------------------------

    def detect_gaps(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run all gap detection rules R1-R9."""
        return {
            "R1_empty_high_value_cells": self._r1_empty_cells(),
            "R2_candidate_only_cells": self._r2_candidate_only(),
            "R3_overpopulated_duplicate": self._r3_overpopulated(),
            "R4_missing_inverses": self._r4_missing_inverses(),
            "R5_missing_bridges": self._r5_missing_bridges(),
            "R6_full_family_gaps": self._r6_family_gaps(),
            "R7_task_gaps": self._r7_task_gaps(),
            "R8_isolated_primitives": self._r8_isolated(),
            "R9_missing_controls": self._r9_missing_controls(),
        }

    def _r1_empty_cells(self) -> List[Dict[str, Any]]:
        """Cells that have no primitive or candidate at all."""
        gaps = []
        for fam in FAMILIES:
            for target in TARGETS:
                for role in ROLES:
                    count = sum(1 for r in self.records if r.family == fam and r.target_domain == target and r.role == role)
                    if count == 0:
                        # Check if this is a high-value cell
                        if role in ("selector", "constructor", "comparator", "brancher") or target in ("mask", "relation"):
                            gaps.append({"family": fam, "target": target, "role": role, "rule": "R1"})
        return gaps

    def _r2_candidate_only(self) -> List[Dict[str, Any]]:
        """Cells that have only candidates (no accepted/promoted)."""
        gaps = []
        for fam in FAMILIES:
            for target in TARGETS:
                for role in ROLES:
                    has_accepted = any(
                        r.family == fam and r.target_domain == target and r.role == role
                        and r.source in ("bh80", "native_promoted")
                        for r in self.records
                    )
                    has_candidate = any(
                        r.family == fam and r.target_domain == target and r.role == role
                        and r.source == "native_candidate"
                        for r in self.records
                    )
                    if has_candidate and not has_accepted:
                        candidates = [r.primitive_id for r in self.records if r.family == fam and r.target_domain == target and r.role == role and r.source == "native_candidate"]
                        gaps.append({"family": fam, "target": target, "role": role, "candidates": candidates, "rule": "R2"})
        return gaps

    def _r3_overpopulated(self) -> List[Dict[str, Any]]:
        """Cells with 3+ primitives and high mutual similarity."""
        gaps = []
        for fam in FAMILIES:
            for target in TARGETS:
                for role in ROLES:
                    recs = [r for r in self.records if r.family == fam and r.target_domain == target and r.role == role]
                    if len(recs) >= 3:
                        high_dup = [r for r in recs if r.duplicate_risk > 0.5]
                        if len(high_dup) >= 2:
                            gaps.append({"family": fam, "target": target, "role": role, "primitives": [r.primitive_id for r in recs], "high_dup_count": len(high_dup), "rule": "R3"})
        return gaps

    def _r4_missing_inverses(self) -> List[Dict[str, Any]]:
        """Primitives that have no inverse/dual."""
        inverses = {
            "rotate": "rotate_ccw",
            "mirror_object": "mirror_vertical",
            "crop_object": "expand_object",
            "recolor": "restore_color",
            "normalize_position": "denormalize",
            "fill_region": "clear_region",
        }
        gaps = []
        for prim, inverse_name in inverses.items():
            if prim in self.records_by_id:
                # Check if inverse exists (by name or semantic equivalent)
                if inverse_name not in self.records_by_id:
                    gaps.append({"primitive": prim, "missing_inverse": inverse_name, "rule": "R4"})
        return gaps

    def _r5_missing_bridges(self) -> List[Dict[str, Any]]:
        """Hub primitives that lack a composition bridge."""
        # Hubs: primitives with >= 3 composes_with edges
        hub_counts: Dict[str, int] = {}
        for edge in self.graph.edges:
            if edge.edge_type == "composes_with":
                hub_counts[edge.source_id] = hub_counts.get(edge.source_id, 0) + 1
                hub_counts[edge.target_id] = hub_counts.get(edge.target_id, 0) + 1

        hubs = [nid for nid, count in hub_counts.items() if count >= 3]
        gaps = []
        # Check if pairs of hubs compose with each other
        for i in range(len(hubs)):
            for j in range(i + 1, len(hubs)):
                h1, h2 = hubs[i], hubs[j]
                connected = any(
                    (e.source_id == h1 and e.target_id == h2) or (e.source_id == h2 and e.target_id == h1)
                    for e in self.graph.edges
                    if e.edge_type == "composes_with"
                )
                if not connected:
                    label1 = self.graph.node_index[h1].label if h1 in self.graph.node_index else h1
                    label2 = self.graph.node_index[h2].label if h2 in self.graph.node_index else h2
                    gaps.append({"hub_a": label1, "hub_b": label2, "rule": "R5"})
        return gaps

    def _r6_family_gaps(self) -> List[Dict[str, Any]]:
        """Families with 0 accepted/promoted primitives."""
        gaps = []
        for fam in FAMILIES:
            has_promoted = any(r.family == fam and r.source in ("bh80", "native_promoted") for r in self.records)
            candidate_count = sum(1 for r in self.records if r.family == fam and r.source == "native_candidate")
            if not has_promoted:
                gaps.append({"family": fam, "candidate_count": candidate_count, "rule": "R6"})
        return gaps

    def _r7_task_gaps(self) -> List[Dict[str, Any]]:
        """Families that appear in 0 scored tasks (only in probes or not at all)."""
        gaps = []
        for fam in FAMILIES:
            fam_prims = [r for r in self.records if r.family == fam]
            has_scored = False
            for r in fam_prims:
                for tid in r.appears_in_tasks:
                    # Exclude probe tasks (T120_101-T120_110)
                    if not (tid.startswith("T120_10") and len(tid) == 8 and tid[4:7] >= "101"):
                        # Check if it's a scored task (BH80 or T120 scored ranges)
                        if tid.startswith("BH80_") or tid.startswith("T120_08") or tid.startswith("T120_09") or tid.startswith("T120_11") or tid.startswith("T120_12") or tid == "T120_100":
                            has_scored = True
                            break
                if has_scored:
                    break
            if not has_scored and fam_prims:
                gaps.append({"family": fam, "rule": "R7"})
        return gaps

    def _r8_isolated(self) -> List[Dict[str, Any]]:
        """Primitives with < 2 composition edges."""
        gaps = []
        comp_counts: Dict[str, int] = {}
        for edge in self.graph.edges:
            if edge.edge_type == "composes_with":
                comp_counts[edge.source_id] = comp_counts.get(edge.source_id, 0) + 1
                comp_counts[edge.target_id] = comp_counts.get(edge.target_id, 0) + 1
        for rec in self.records:
            nid = f"prim:{rec.primitive_id}"
            count = comp_counts.get(nid, 0)
            if count < 2:
                gaps.append({"primitive": rec.primitive_id, "composition_edges": count, "rule": "R8"})
        return gaps

    def _r9_missing_controls(self) -> List[Dict[str, Any]]:
        """Primitives that may lack negative/no-op controls."""
        gaps = []
        for rec in self.records:
            if rec.source == "native_candidate" and not rec.appears_in_tasks:
                gaps.append({"primitive": rec.primitive_id, "reason": "no_task_appearance_no_control", "rule": "R9"})
        return gaps

    # -----------------------------------------------------------------------
    # Gap scoring
    # -----------------------------------------------------------------------

    GAP_WEIGHTS = {
        "cell_empty": 0.15,
        "task_space_value": 0.15,
        "family_novelty": 0.10,
        "oracle_implementability": 0.10,
        "solver_implementability": 0.10,
        "non_duplicate": 0.10,
        "non_regression": 0.10,
        "anti_cheat_value": 0.05,
        "tasks_unlocked": 0.10,
        "probe_exists": 0.05,
    }

    def gap_score(self, primitive_id: str) -> float:
        """Compute the 10-component weighted gap score for a candidate."""
        rec = self.records_by_id.get(primitive_id)
        if rec is None or rec.promoted:
            return 0.0

        # Cell empty: 1.0 if family has no promoted, 0.5 if candidate-only, 0.0 if filled
        family_has_promoted = self._family_has_promoted(rec.family)
        cell_empty = 1.0 if not family_has_promoted else (0.5 if self._cell_is_empty_or_candidate_only(rec.family, rec.target_domain, rec.role) else 0.0)

        # Task-space value
        is_new_family = CANDIDATE_FAMILY_NOVELTY.get(primitive_id, False)
        has_probe = primitive_id in CANDIDATE_PROBE_TASKS
        ts_value = min(1.0, 0.4 + (0.3 if is_new_family else 0.0) + (0.2 if has_probe else 0.0))

        # Family novelty
        family_novelty = 1.0 if is_new_family else 0.0

        # Oracle/solver implementability
        oracle_cx, solver_cx = COMPLEXITY_ESTIMATES.get(primitive_id, (0.5, 0.5))
        oracle_impl = 1.0 - oracle_cx
        solver_impl = 1.0 - solver_cx

        # Non-duplicate / non-regression
        non_dup = 1.0 - rec.duplicate_risk
        non_reg = 1.0 - self._compute_regression_risk(primitive_id, rec.duplicate_risk)

        # Anti-cheat value
        anti_cheat = 0.5  # default
        if has_probe:
            anti_cheat = 0.8  # probe provides anti-cheat evidence

        # Tasks unlocked (normalized)
        tasks_unlocked = rec.task_unlock_score

        # Probe exists
        probe_exists = 1.0 if has_probe else 0.0

        w = self.GAP_WEIGHTS
        return (
            w["cell_empty"] * cell_empty +
            w["task_space_value"] * ts_value +
            w["family_novelty"] * family_novelty +
            w["oracle_implementability"] * oracle_impl +
            w["solver_implementability"] * solver_impl +
            w["non_duplicate"] * non_dup +
            w["non_regression"] * non_reg +
            w["anti_cheat_value"] * anti_cheat +
            w["tasks_unlocked"] * tasks_unlocked +
            w["probe_exists"] * probe_exists
        )

    # -----------------------------------------------------------------------
    # Perspicuity integration
    # -----------------------------------------------------------------------

    def perspicuity_contribution(self, primitive_id: str) -> Dict[str, float]:
        """Return cartography-aware perspicuity contribution for a candidate.

        This is an additional ranking signal, not a replacement for the existing
        perspicuity model in native_arc_perspicuity.py.
        """
        rec = self.records_by_id.get(primitive_id)
        if rec is None or rec.promoted:
            return {"gap_fill": 0.0, "connectivity": 0.0, "family_gap_bonus": 0.0, "task_unlock_bonus": 0.0}

        # Gap fill: based on whether family has promoted
        family_has_promoted = self._family_has_promoted(rec.family)
        gap_fill = 1.0 if not family_has_promoted else (0.6 if self._cell_is_empty_or_candidate_only(rec.family, rec.target_domain, rec.role) else 0.3)

        # Connectivity: composes_with major hubs?
        comp_edges = self.graph.edges_of(f"prim:{primitive_id}", "composes_with")
        major_hubs = {"prim:recolor", "prim:extract"}
        hub_connections = sum(1 for e in comp_edges if e.source_id in major_hubs or e.target_id in major_hubs)
        connectivity = min(1.0, hub_connections * 0.5)

        # Family gap bonus
        family_gap_bonus = 1.0 if not family_has_promoted else 0.0

        # Task unlock bonus
        task_unlock_bonus = rec.task_unlock_score

        return {
            "gap_fill": gap_fill,
            "connectivity": connectivity,
            "family_gap_bonus": family_gap_bonus,
            "task_unlock_bonus": task_unlock_bonus,
        }

    # -----------------------------------------------------------------------
    # Batch 2 recommendation
    # -----------------------------------------------------------------------

    def batch_2_recommendation(self) -> Dict[str, Any]:
        """Produce the evidence-driven Batch 2 recommendation."""
        recommended = []
        deferred = []

        for rec in self.records:
            if rec.source != "native_candidate":
                continue
            score = self.gap_score(rec.primitive_id)
            entry = {
                "primitive_id": rec.primitive_id,
                "family": rec.family,
                "gap_score": round(score, 4),
                "recommendation": rec.recommendation,
                "duplicate_risk": round(rec.duplicate_risk, 2),
                "gap_fill_score": round(rec.gap_fill_score, 2),
                "maturity": rec.maturity,
            }
            if rec.recommendation == "promote_now":
                recommended.append(entry)
            elif rec.recommendation == "defer":
                deferred.append(entry)

        recommended.sort(key=lambda x: -x["gap_score"])

        # Batch 2 = top 4 promote_now that fill full family gaps, one per family
        # Prioritize full family gaps first, then by gap_score
        batch_2 = []
        used_families = set()

        # Get family gaps from R6 and candidate-only cells from R2
        all_gaps = self.detect_gaps()
        family_gaps = {g["family"] for g in all_gaps.get("R6_full_family_gaps", [])}
        r2_cells = all_gaps.get("R2_candidate_only_cells", [])
        r2_families = {g["family"] for g in r2_cells}

        # Priority families: full family gaps first, then candidate-only families
        priority_families = family_gaps | r2_families

        # Filter out high duplicate risk candidates from Batch 2
        batch_eligible = [e for e in recommended if e["duplicate_risk"] < 0.6]

        # First pass: fill from priority families (R6 + R2), one per family, by gap_score
        for entry in batch_eligible:
            if entry["family"] in priority_families and entry["family"] not in used_families:
                batch_2.append(entry)
                used_families.add(entry["family"])
            if len(batch_2) == 4:
                break

        # Second pass: if fewer than 4, fill from remaining eligible by score
        if len(batch_2) < 4:
            for entry in batch_eligible:
                if entry["family"] not in used_families:
                    batch_2.append(entry)
                    used_families.add(entry["family"])
                if len(batch_2) == 4:
                    break

        # Identify dropped from original batch 2
        original_batch_2 = ["mask_border_only", "geom_flip_vertical", "topo_fill_holes", "constr_draw_rect_around"]
        new_ids = {b["primitive_id"] for b in batch_2}
        dropped = [pid for pid in original_batch_2 if pid not in new_ids]

        return {
            "recommended_batch_2": batch_2,
            "dropped_from_original": dropped,
            "all_recommended": recommended,
            "all_deferred": deferred,
        }

    # -----------------------------------------------------------------------
    # Output artifacts
    # -----------------------------------------------------------------------

    def export_coverage_grid(self) -> Dict[str, Any]:
        """Export primitive coverage grid as JSON-serializable dict."""
        return {
            "family_maturity": self.coverage_grid_family_maturity(),
            "family_target": self.coverage_grid_family_target(),
            "family_role": self.coverage_grid_family_role(),
        }

    def export_graph_adjacency(self) -> Dict[str, Any]:
        """Export primitive graph adjacency list."""
        adjacency: Dict[str, List[Dict[str, Any]]] = {}
        for edge in self.graph.edges:
            adjacency.setdefault(edge.source_id, []).append({
                "target": edge.target_id,
                "type": edge.edge_type,
                "weight": edge.weight,
            })
        return {
            "nodes": [{"id": n.node_id, "type": n.node_type, "label": n.label} for n in self.graph.nodes],
            "adjacency": adjacency,
        }

    def export_gap_report(self) -> Dict[str, Any]:
        """Export gap report."""
        gaps = self.detect_gaps()
        gap_scores = {}
        for rec in self.records:
            if rec.source == "native_candidate":
                gap_scores[rec.primitive_id] = round(self.gap_score(rec.primitive_id), 4)
        return {
            "gaps": gaps,
            "gap_scores": dict(sorted(gap_scores.items(), key=lambda x: -x[1])),
        }

    def export_top_n_missing(self, n: int = 10) -> List[Dict[str, Any]]:
        """Export top-N missing cells."""
        gaps = self.detect_gaps()
        missing = gaps.get("R1_empty_high_value_cells", [])
        candidate_only = gaps.get("R2_candidate_only_cells", [])
        all_gaps = []
        for g in missing:
            all_gaps.append({"cell": f"{g['family']}×{g['target']}×{g['role']}", "type": "empty", "rule": "R1"})
        for g in candidate_only:
            all_gaps.append({"cell": f"{g['family']}×{g['target']}×{g['role']}", "type": "candidate_only", "candidates": g["candidates"], "rule": "R2"})
        return all_gaps[:n]

    def export_top_n_promotion_recommendations(self, n: int = 10) -> List[Dict[str, Any]]:
        """Export top-N promotion recommendations with gap-fill evidence."""
        results = []
        for rec in self.records:
            if rec.source != "native_candidate":
                continue
            score = self.gap_score(rec.primitive_id)
            persp = self.perspicuity_contribution(rec.primitive_id)
            results.append({
                "primitive_id": rec.primitive_id,
                "family": rec.family,
                "gap_score": round(score, 4),
                "recommendation": rec.recommendation,
                "gap_fill": persp["gap_fill"],
                "connectivity": persp["connectivity"],
                "family_gap_bonus": persp["family_gap_bonus"],
                "duplicate_risk": round(rec.duplicate_risk, 2),
                "risk_flags": rec.risk_flags,
            })
        results.sort(key=lambda x: -x["gap_score"])
        return results[:n]

    def export_duplicate_risk_report(self) -> List[Dict[str, Any]]:
        """Export duplicate-risk report."""
        report = []
        for rec in self.records:
            if rec.duplicate_risk > 0.0:
                sim = SEMANTIC_SIMILARITY.get(rec.primitive_id, ("", 0.0))
                report.append({
                    "primitive": rec.primitive_id,
                    "similar_to": sim[0] if isinstance(sim, tuple) else "",
                    "similarity": round(rec.duplicate_risk, 2),
                })
        report.sort(key=lambda x: -x["similarity"])
        return report

    def export_task_unlock_report(self) -> List[Dict[str, Any]]:
        """Export task-unlock report."""
        report = []
        for rec in self.records:
            if rec.source == "native_candidate" and rec.appears_in_tasks:
                report.append({
                    "primitive": rec.primitive_id,
                    "appears_in": rec.appears_in_tasks,
                    "task_unlock_score": round(rec.task_unlock_score, 2),
                })
        return report

    def export_family_coverage(self) -> List[Dict[str, Any]]:
        """Export family coverage summary."""
        result = []
        for fam in FAMILIES:
            accepted = sum(1 for r in self.records if r.family == fam and r.source == "bh80")
            promoted = sum(1 for r in self.records if r.family == fam and r.source == "native_promoted")
            candidates = sum(1 for r in self.records if r.family == fam and r.source == "native_candidate")
            has_promoted = (accepted + promoted) > 0
            result.append({
                "family": fam,
                "accepted": accepted,
                "promoted": promoted,
                "candidates": candidates,
                "gap_severity": "high" if not has_promoted and candidates > 0 else ("none" if has_promoted else "empty"),
            })
        return result

    def export_hub_centrality(self) -> List[Dict[str, Any]]:
        """Export hub/centrality report."""
        comp_counts: Dict[str, int] = {}
        for edge in self.graph.edges:
            if edge.edge_type == "composes_with":
                comp_counts[edge.source_id] = comp_counts.get(edge.source_id, 0) + 1
                comp_counts[edge.target_id] = comp_counts.get(edge.target_id, 0) + 1

        report = []
        for rec in self.records:
            nid = f"prim:{rec.primitive_id}"
            count = comp_counts.get(nid, 0)
            hub_type = "major" if count >= 6 else ("moderate" if count >= 4 else ("minor" if count >= 2 else "isolated"))
            report.append({
                "primitive": rec.primitive_id,
                "composition_degree": count,
                "hub_type": hub_type,
            })
        report.sort(key=lambda x: -x["composition_degree"])
        return report


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def build_cartographer() -> PrimitiveSpaceCartographer:
    """Build and return a PrimitiveSpaceCartographer instance."""
    return PrimitiveSpaceCartographer()


def get_cartographer_summary() -> Dict[str, Any]:
    """Return a summary of the cartographer state."""
    cart = build_cartographer()
    gaps = cart.detect_gaps()
    batch2 = cart.batch_2_recommendation()
    return {
        "total_records": len(cart.records),
        "bh80_count": sum(1 for r in cart.records if r.source == "bh80"),
        "promoted_count": sum(1 for r in cart.records if r.source == "native_promoted"),
        "candidate_count": sum(1 for r in cart.records if r.source == "native_candidate"),
        "graph_nodes": len(cart.graph.nodes),
        "graph_edges": len(cart.graph.edges),
        "gap_counts": {k: len(v) for k, v in gaps.items()},
        "batch_2_recommended": [b["primitive_id"] for b in batch2["recommended_batch_2"]],
        "batch_2_dropped": batch2["dropped_from_original"],
    }