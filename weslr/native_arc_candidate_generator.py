"""WESLR Native ARC Primitive Candidate Generator.

Generates candidate PrimitiveContract objects using the native ARC language schema.
Candidates are NOT promoted. Candidates CANNOT be counted as solved.
No oracle/solver implementations are added here.

Deterministic: same input → same candidate list.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from weslr.native_arc_language_schema import (
    PrimitiveContract, PromotionStage, TypeSignature,
    make_primitive_contract, compute_content_hash,
    is_promotion_eligible, validate_promotion_eligibility,
    BH80_REGRESSION_POLICY,
)

# ---------------------------------------------------------------------------
# Candidate family definitions
# ---------------------------------------------------------------------------

@dataclass
class CandidateFamily:
    family_id: str
    description: str
    candidates: List[PrimitiveContract] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Perspicuity scoring (deterministic, no model calls)
# ---------------------------------------------------------------------------

@dataclass
class PerspicuityScore:
    clarity: float          # internal validity (1.0 if typed and hashable)
    minimality: float      # shorter expression = higher
    non_duplication: float  # 1.0 if no duplicate, 0.0 if duplicate
    compositional_depth: float  # depth of expression
    testability: float     # 1.0 if deterministic and typed
    expected_usefulness: float  # heuristic based on family
    shortcut_risk: float    # lower = better (harder to shortcut)

    @property
    def total(self) -> float:
        return (self.clarity + self.minimality + self.non_duplication +
                self.compositional_depth + self.testability +
                self.expected_usefulness + (1.0 - self.shortcut_risk)) / 7.0


def _score_candidate(expr: str, family: str, is_duplicate: bool) -> PerspicuityScore:
    clarity = 1.0  # all typed candidates are internally clear
    minimality = max(0.0, 1.0 - len(expr) / 200.0)  # shorter = better
    non_dup = 0.0 if is_duplicate else 1.0
    depth = min(1.0, expr.count("→") / 5.0 + expr.count("⇒") / 5.0 + 0.3)
    testability = 1.0  # deterministic + typed
    # Family-based usefulness heuristic
    family_usefulness = {
        "object_selector": 0.7, "mask_algebra": 0.8, "color_transform": 0.6,
        "geometry_transform": 0.7, "topology_transform": 0.5, "relation_transform": 0.6,
        "construction_transform": 0.8, "pattern_transform": 0.7, "conditional_transform": 0.5,
    }
    expected_usefulness = family_usefulness.get(family, 0.5)
    shortcut_risk = 0.3  # default; lower = harder to shortcut
    if "identity" in expr.lower() or "noop" in expr.lower():
        shortcut_risk = 0.8
    return PerspicuityScore(
        clarity=clarity, minimality=minimality, non_duplication=non_dup,
        compositional_depth=depth, testability=testability,
        expected_usefulness=expected_usefulness, shortcut_risk=shortcut_risk,
    )


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def _content_hash_of(expr: str) -> str:
    return compute_content_hash(expr)


def _detect_duplicates(contracts: List[PrimitiveContract]) -> Set[str]:
    seen = set()
    duplicates = set()
    for c in contracts:
        if c.content_hash in seen:
            duplicates.add(c.content_hash)
        seen.add(c.content_hash)
    return duplicates


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------

def _make_candidate(
    primitive_id: str,
    expr: str,
    input_type: str = "Grid",
    output_type: str = "Grid",
    params: Optional[List[Dict[str, str]]] = None,
    preconditions: Optional[List[str]] = None,
    invariants_preserved: Optional[List[str]] = None,
    invariants_changed: Optional[List[str]] = None,
    human_summary: Optional[str] = None,
) -> PrimitiveContract:
    contract = make_primitive_contract(
        primitive_id=primitive_id,
        internal_expression=expr,
        input_type=input_type,
        output_type=output_type,
        parameters=params,
        preconditions=preconditions,
        invariants_preserved=invariants_preserved,
        invariants_changed=invariants_changed,
        human_summary=human_summary,
    )
    # Set to generated stage
    contract.promotion_stage = PromotionStage.GENERATED
    contract.completed_stages = {PromotionStage.GENERATED}
    return contract


def generate_candidates() -> Tuple[List[PrimitiveContract], List[CandidateFamily], Dict[str, PerspicuityScore]]:
    """Generate all candidate primitives deterministically.

    Returns:
        - list of all candidate PrimitiveContract objects
        - list of CandidateFamily objects
        - dict of primitive_id -> PerspicuityScore
    """
    families: List[CandidateFamily] = []
    all_candidates: List[PrimitiveContract] = []

    # 1. Object selector compositions
    obj_selectors = [
        ("sel_leftmost", "λG.Σ[obj|argmin(col)]⇒extract", "Select leftmost object"),
        ("sel_topmost", "λG.Σ[obj|argmin(row)]⇒extract", "Select topmost object"),
        ("sel_smallest", "λG.Σ[obj|argmin(area)]⇒extract", "Select smallest object"),
        ("sel_most_holes", "λG.Σ[obj|max(holes)]⇒extract", "Select object with most holes"),
        ("sel_edge_touch", "λG.Σ[obj|touches_border]⇒extract", "Select object touching border"),
    ]
    fam1 = CandidateFamily("object_selector", "Object selection rules")
    for pid, expr, summary in obj_selectors:
        c = _make_candidate(pid, expr, "Grid", "Grid",
                           preconditions=["grid has at least one non-background cell"],
                           invariants_preserved=["grid dimensions"],
                           invariants_changed=["cell values in non-selected regions set to background"],
                           human_summary=summary)
        fam1.candidates.append(c)
        all_candidates.append(c)
    families.append(fam1)

    # 2. Mask algebra transforms
    mask_ops = [
        ("mask_union", "Ω(mask_A∨mask_B)⇢overlay", "Union of two masks"),
        ("mask_intersect", "Ω(mask_A∧mask_B)⇢highlight", "Intersection of two masks"),
        ("mask_complement", "Ω(¬mask)⇢invert", "Complement of mask"),
        ("mask_border_only", "Ω(mask∧border)⇢color(2)", "Border cells of mask"),
    ]
    fam2 = CandidateFamily("mask_algebra", "Mask algebra operations")
    for pid, expr, summary in mask_ops:
        c = _make_candidate(pid, expr, "Grid", "Grid",
                           invariants_preserved=["grid dimensions"],
                           invariants_changed=["cell values in masked region"],
                           human_summary=summary)
        fam2.candidates.append(c)
        all_candidates.append(c)
    families.append(fam2)

    # 3. Color transforms
    color_ops = [
        ("color_swap_1_2", "κ(swap(1,2))⇒recolor", "Swap colors 1 and 2"),
        ("color_gradient", "κ(gradient(0→9))⇒fill", "Apply gradient fill"),
        ("color_invert", "κ(invert)⇒recolor", "Invert all colors"),
        ("color_dominant", "κ(dominant→2)⇒recolor", "Recolor dominant color to 2"),
    ]
    fam3 = CandidateFamily("color_transform", "Color space transforms")
    for pid, expr, summary in color_ops:
        c = _make_candidate(pid, expr, "Grid", "Grid",
                           invariants_preserved=["grid dimensions"],
                           invariants_changed=["cell color values"],
                           human_summary=summary)
        fam3.candidates.append(c)
        all_candidates.append(c)
    families.append(fam3)

    # 4. Geometry transforms
    geom_ops = [
        ("geom_scale_2x", "γ(scale(2.0))⇒resize", "Scale grid by 2x"),
        ("geom_translate_center", "γ(translate(centroid→center))⇒move", "Translate to center"),
        ("geom_flip_vertical", "γ(flip(axis=row))⇒reflect", "Flip vertically"),
    ]
    fam4 = CandidateFamily("geometry_transform", "Geometric transforms")
    for pid, expr, summary in geom_ops:
        c = _make_candidate(pid, expr, "Grid", "Grid",
                           invariants_preserved=["grid topology"],
                           invariants_changed=["cell positions", "grid dimensions (for scale)"],
                           human_summary=summary)
        fam4.candidates.append(c)
        all_candidates.append(c)
    families.append(fam4)

    # 5. Topology transforms
    topo_ops = [
        ("topo_merge_objects", "τ(merge(all_objects))⇒connect", "Merge all objects"),
        ("topo_fill_holes", "τ(fill(holes))⇒solid", "Fill all holes in objects"),
        ("topo_split_at_gap", "τ(split(narrowest_gap))⇒separate", "Split object at narrowest gap"),
    ]
    fam5 = CandidateFamily("topology_transform", "Topology transforms")
    for pid, expr, summary in topo_ops:
        c = _make_candidate(pid, expr, "Grid", "Grid",
                           invariants_preserved=["grid dimensions"],
                           invariants_changed=["object connectivity"],
                           human_summary=summary)
        fam5.candidates.append(c)
        all_candidates.append(c)
    families.append(fam5)

    # 6. Relation transforms
    rel_ops = [
        ("rel_align_centroids", "Φ(rel(centroid_align),objset)⇒translate", "Align objects by centroid"),
        ("rel_swap_positions", "Φ(rel(swap),obj_A,obj_B)⇒translate", "Swap positions of two objects"),
        ("rel_order_by_size", "Φ(rel(size_order),objset)⇒arrange", "Order objects by size"),
    ]
    fam6 = CandidateFamily("relation_transform", "Relational transforms")
    for pid, expr, summary in rel_ops:
        c = _make_candidate(pid, expr, "Grid", "Grid",
                           invariants_preserved=["grid dimensions"],
                           invariants_changed=["object positions"],
                           human_summary=summary)
        fam6.candidates.append(c)
        all_candidates.append(c)
    families.append(fam6)

    # 7. Construction transforms
    constr_ops = [
        ("constr_draw_rect_around", "ξ(draw(rect,bbox(obj)))⇒overlay", "Draw rectangle around object"),
        ("constr_extend_pattern", "ξ(extend(pattern,row))⇒fill", "Extend row pattern to canvas"),
        ("constr_connect_line", "ξ(line(centroid_A→centroid_B))⇒draw", "Draw line connecting two objects"),
        ("constr_copy_to_pos", "ξ(copy(obj,(r,c)))⇒place", "Copy object to position"),
    ]
    fam7 = CandidateFamily("construction_transform", "Construction transforms")
    for pid, expr, summary in constr_ops:
        c = _make_candidate(pid, expr, "Grid", "Grid",
                           invariants_preserved=["existing objects unchanged"],
                           invariants_changed=["new cells drawn"],
                           human_summary=summary)
        fam7.candidates.append(c)
        all_candidates.append(c)
    families.append(fam7)

    # 8. Pattern transforms
    pat_ops = [
        ("pat_row_alternate", "π(row_alternate(1,2))⇒pattern", "Row-alternating pattern"),
        ("pat_block_repeat", "π(block_repeat(2x2))⇒tile", "2x2 block repetition"),
        ("pat_color_cycle", "π(cycle(1→2→3))⇒fill", "Cycling color pattern"),
    ]
    fam8 = CandidateFamily("pattern_transform", "Pattern transforms")
    for pid, expr, summary in pat_ops:
        c = _make_candidate(pid, expr, "Grid", "Grid",
                           invariants_preserved=["grid dimensions"],
                           invariants_changed=["cell colors following pattern"],
                           human_summary=summary)
        fam8.candidates.append(c)
        all_candidates.append(c)
    families.append(fam8)

    # 9. Conditional transforms
    cond_ops = [
        ("cond_if_holes_fill", "κ(count(holes)>0)?fill_holes:identity", "If has holes, fill them"),
        ("cond_if_multi_count", "κ(count(obj)>2)?count:pattern", "If >2 objects, count; else pattern"),
        ("cond_if_edge_clip", "κ(touches_edge)?crop:identity", "If touches edge, crop"),
    ]
    fam9 = CandidateFamily("conditional_transform", "Conditional transforms")
    for pid, expr, summary in cond_ops:
        c = _make_candidate(pid, expr, "Grid", "Grid",
                           preconditions=["grid is non-empty"],
                           invariants_preserved=["grid dimensions (unless conditional modifies)"],
                           invariants_changed=["depends on condition"],
                           human_summary=summary)
        fam9.candidates.append(c)
        all_candidates.append(c)
    families.append(fam9)

    # Duplicate detection
    dup_hashes = _detect_duplicates(all_candidates)

    # Perspicuity scoring
    scores: Dict[str, PerspicuityScore] = {}
    for c in all_candidates:
        is_dup = c.content_hash in dup_hashes
        family_id = next((f.family_id for f in families if c in f.candidates), "unknown")
        scores[c.primitive_id] = _score_candidate(c.internal_expression, family_id, is_dup)

    return all_candidates, families, scores


# ---------------------------------------------------------------------------
# Export helpers (in-memory only)
# ---------------------------------------------------------------------------

def list_candidate_summaries(candidates: List[PrimitiveContract]) -> List[Dict[str, str]]:
    """Return lightweight summaries of all candidates."""
    return [
        {
            "primitive_id": c.primitive_id,
            "content_hash": c.content_hash[:12],
            "type": f"{c.type_signature.input}→{c.type_signature.output}",
            "stage": c.promotion_stage.value,
            "human_summary": c.human_summary or "(no summary)",
        }
        for c in candidates
    ]


def list_audit_ready_fields(candidates: List[PrimitiveContract]) -> List[Dict[str, Any]]:
    """Return audit-ready contract fields for each candidate."""
    return [c.to_dict() for c in candidates]