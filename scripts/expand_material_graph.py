#!/usr/bin/env python3
"""
scripts/expand_material_graph.py

Reads the existing material_graph.json (~21 nodes) and programmatically
expands it to ~200 nodes covering common perovskites, spinels, rutiles,
2D materials, MXenes, and MOFs. Detects substitution gaps and marks them
is_gap:true for novelty prioritization.

Outputs:
  weslr/data/material_graph_expanded.json  (new file; original unchanged)
"""

import json, re
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent.parent

# ── Element pools ──────────────────────────────────────────────────────────────

PEROVSKITE_A = ["Ca", "Sr", "Ba", "Pb", "La", "Y", "Bi", "Cs", "Rb", "K", "Na"]
PEROVSKITE_B = ["Ti", "Zr", "Sn", "Fe", "Co", "Ni", "Mn", "Al", "Ga", "In", "Nb", "Ta", "Mo", "W", "Re", "Ru", "Rh", "Cr", "V"]
PEROVSKITE_X = ["O", "S", "Se", "F", "N"]

SPINEL_A = ["Mg", "Ca", "Zn", "Fe", "Co", "Ni", "Cu", "Mn", "Li"]
SPINEL_B = ["Al", "Fe", "Cr", "Co", "Rh", "Ga", "Mn", "Ti", "V", "Mo", "W"]
SPINEL_X = ["O", "S", "Se"]

RUTILE_A = ["Ti", "Sn", "Ir", "Ru", "Mn", "Pb", "Zr", "Ge", "Mo", "W", "Nb", "Ta", "V"]
RUTILE_X = ["O", "S", "Se", "F", "Cl"]

ROCKSALT_A = ["Mg", "Ca", "Sr", "Ba", "Zn", "Cd", "Fe", "Co", "Ni", "Cu", "Mn", "Li", "Na", "K", "Al", "Ga", "In", "Ge", "Sn", "Pb", "Bi", "La", "Y", "Sc"]
ROCKSALT_X = ["O", "S", "Se", "N", "F", "Cl"]

# Known charge-balanced perovskite pairs (A_ox, B_ox)
PEROVSKITE_PAIRS: list[tuple[int, int, str, str]] = [
    (+1,+5,"Cs","Nb"),(+1,+5,"Cs","Ta"),(+1,+5,"Rb","Nb"),(+1,+5,"Rb","Ta"),
    (+1,+5,"K","Nb"),(+1,+5,"K","Ta"),(+1,+5,"Na","Nb"),(+1,+5,"Na","Ta"),
    (+2,+4,"Ca","Ti"),(+2,+4,"Ca","Zr"),(+2,+4,"Ca","Sn"),(+2,+4,"Ca","Ge"),
    (+2,+4,"Sr","Ti"),(+2,+4,"Sr","Zr"),(+2,+4,"Sr","Sn"),(+2,+4,"Sr","Ge"),
    (+2,+4,"Ba","Ti"),(+2,+4,"Ba","Zr"),(+2,+4,"Ba","Sn"),(+2,+4,"Ba","Ge"),
    (+2,+4,"Pb","Ti"),(+2,+4,"Pb","Zr"),(+2,+4,"Pb","Sn"),
    (+3,+3,"La","Al"),(+3,+3,"La","Cr"),(+3,+3,"La","Fe"),(+3,+3,"La","Mn"),
    (+3,+3,"La","Co"),(+3,+3,"La","Ga"),(+3,+3,"La","In"),(+3,+3,"La","Sc"),
    (+3,+3,"Y","Al"),(+3,+3,"Y","Cr"),(+3,+3,"Y","Fe"),
    (+3,+3,"Bi","Fe"),(+3,+3,"Bi","Al"),(+3,+3,"Bi","Mn"),
    (+2,+5,"Ca","Nb"),(+2,+5,"Ca","Ta"),(+2,+5,"Sr","Nb"),(+2,+5,"Sr","Ta"),
    (+2,+5,"Ba","Nb"),(+2,+5,"Ba","Ta"),(+2,+5,"Pb","Nb"),(+2,+5,"Pb","Ta"),
    (+3,+5,"Bi","Nb"),(+3,+5,"Bi","Ta"),
    (+1,+7,"Cs","Re"),(+2,+6,"Ca","Mo"),(+2,+6,"Ca","W"),(+2,+6,"Sr","Mo"),(+2,+6,"Sr","W"),
    (+3,+6,"La","Mo"),(+3,+6,"La","W"),
]

# 2D materials
MATERIALS_2D = [
    ("C", "graphene", 0.0),
    ("MoS2", "layered_dichalcogenide", 1.8),
    ("WS2", "layered_dichalcogenide", 1.9),
    ("MoSe2", "layered_dichalcogenide", 1.5),
    ("WSe2", "layered_dichalcogenide", 1.6),
    ("hBN", "hexagonal_BN", 5.9),
    ("BP", "phosphorene", 0.8),
    ("C3N", "carbon nitride", 2.9),
    ("TiO2", "2d_oxide", 3.2),
    ("NbS2", "layered_dichalcogenide", 1.3),
]

# MXenes (common ones from literature)
MXENES = [
    ("Ti3C2", "mxene", 0.1),
    ("Ti2C", "mxene", 0.0),
    ("V2C", "mxene", 0.3),
    ("Nb2C", "mxene", 0.4),
    ("Mo2C", "mxene", 0.5),
    ("Mo1.33C", "mxene", 0.2),
    ("Ti3CN", "mxene", 0.1),
    ("Nb4C3", "mxene", 0.3),
    ("Ta4C3", "mxine", 0.4),
    ("Cr2C", "mxene", 0.6),
    ("TiNbC", "mxene", 0.2),
    ("Mo2TiC3", "mxene", 0.4),
]

# MOFs (placeholders — no real properties, just flags)
MOFS = [
    ("MOF-5", "mof", None),
    ("HKUST-1", "mof", None),
    ("ZIF-8", "mof", None),
    ("MIL-101", "mof", None),
    ("UiO-66", "mof", None),
    ("PCN-222", "mof", None),
    ("NU-1000", "mof", None),
    ("MOF-199", "mof", None),
    ("ZIF-71", "mof", None),
    ("MIL-100", "mof", None),
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def hill_order(formula: str) -> str:
    """Canonicalize formula to Hill order (C then H then alphabetical)."""
    matches = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
    counts: dict[str,int] = {}
    for sym, n in matches:
        if not sym: continue
        counts[sym] = counts.get(sym,0) + (int(n) if n else 1)
    def hk(s):
        if s=="C": return (0,"")
        if s=="H": return (1,"")
        return (2,s)
    parts = []
    for el in sorted(counts, key=hk):
        c = counts[el]; parts.append(f"{el}{c if c>1 else ''}")
    return "".join(parts)

def bandgap_heuristic(prototype: str, elements: list[str], x_anion: str) -> float:
    """Rough bandgap estimate from prototype family and composition."""
    if prototype == "mof": return 0.0
    if prototype == "mxene": return 0.1
    if prototype == "2d_oxide": return 3.2
    if prototype == "graphene": return 0.0
    # Sulfides/selenides are narrow-gap
    if x_anion in ("S", "Se", "Te"): return round(1.2 + hash(elements[0])%40/100, 2)
    if x_anion == "F": return round(4.0 + hash(elements[0])%20/100, 2)
    if prototype == "perovskite": return round(2.2 + hash(elements[0])%60/100, 2)
    if prototype == "spinel": return round(2.0 + hash(elements[0])%80/100, 2)
    if prototype == "rutile": return round(3.2 + hash(elements[0])%40/100, 2)
    if prototype == "rocksalt": return round(3.5 + hash(elements[0])%60/100, 2)
    if prototype == "layered_dichalcogenide": return round(1.8 + hash(elements[0])%40/100, 2)
    if prototype == "phosphorene": return 0.8
    return 3.0

def substitutions_for(prototype: str, a_site: str, b_site: str | None, x_anion: str) -> dict[str,list[str]]:
    """Infer substitution neighbors from periodic table group neighbors."""
    A_GROUP = {"Ca":["Sr","Ba","Mg"],"Sr":["Ca","Ba","Rb"],"Ba":["Ca","Sr","Cs"],
               "Pb":["Ca","Sr","Bi"],"La":["Bi","Y","Sc"],"Y":["La","Sc"],
               "Bi":["La","Pb","Sb"],"Cs":["Rb","K","Ba"],"Rb":["Cs","K"],"K":["Rb","Cs"],"Na":["Li","K"]}
    B_GROUP = {"Ti":["Zr","Hf","Sn"],"Zr":["Ti","Hf"],"Sn":["Ti","Zr","Ge"],
               "Fe":["Co","Mn","Cr"],"Co":["Fe","Ni","Mn"],"Ni":["Co","Fe"],
               "Mn":["Fe","Co","Cr"],"Al":["Ga","In"],"Ga":["Al","In"],
               "In":["Ga","Al"],"Nb":["Ta","V"],"Ta":["Nb"],"Mo":["W","Cr"],
               "W":["Mo","Cr"],"V":["Nb","Ta"],"Cr":["Mo","W","V"],"Ru":["Os","Fe"],"Re":["Os","Ir"]}
    X_GROUP = {"O":["S","Se","N","F"],"S":["O","Se","Te"],"Se":["S","O"],"N":["O","P"],"F":["Cl","O"],"Cl":["F"]}
    subs: dict[str,list[str]] = {}
    if a_site in A_GROUP: subs["A"] = A_GROUP[a_site]
    if b_site and b_site in B_GROUP: subs["B"] = B_GROUP[b_site]
    if x_anion in X_GROUP: subs["X"] = X_GROUP[x_anion]
    return subs

def perovskite_formula(a: str, b: str, x: str) -> str:
    """Build ABX3 formula in conventional order (not Hill order)."""
    return f"{a}{b}{x}3"

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    src = HERE / "weslr" / "data" / "material_graph.json"
    dst = HERE / "weslr" / "data" / "material_graph_expanded.json"

    with open(src) as f:
        base = json.load(f)

    nodes: dict[str,dict] = dict(base.get("nodes", {}))
    # Track formulas we've seen (Hill-order dedup)
    seen: dict[str, bool] = {hill_order(k): True for k in nodes}

    def add_node(formula: str, data: dict, is_gap: bool = False):
        norm = hill_order(formula)
        if norm in seen:
            return
        seen[norm] = True
        data["is_gap"] = is_gap
        if "substitutions" not in data:
            proto = data.get("prototype","")
            data["substitutions"] = substitutions_for(proto, data.get("a_site",""), data.get("b_site"), data.get("x_anion","O"))
        nodes[norm] = data

    # ── 1. Perovskites ABX3 ────────────────────────────────────────────────────
    # Charge balance: A_ox + B_ox + 3*X_ox must == 0
    X_CHARGES = {"O": -2, "S": -2, "Se": -2, "F": -1, "N": -3}
    perovskite_count = 0
    for a_ox, b_ox, a, b in PEROVSKITE_PAIRS:
        for x in PEROVSKITE_X:
            x_ox = X_CHARGES.get(x, -2)
            if a_ox + b_ox + 3 * x_ox != 0:
                continue  # charge-imbalanced, skip
            formula = perovskite_formula(a, b, x)
            data = {
                "prototype": "perovskite",
                "bandgap_ev": bandgap_heuristic("perovskite", [a, b], x),
                "conductivity": "semiconductor",
                "a_site": a, "b_site": b, "x_anion": x,
                "substitutions": substitutions_for("perovskite", a, b, x),
            }
            add_node(formula, data)
            perovskite_count += 1

    # ── 2. Spinels AB2X4 ───────────────────────────────────────────────────────
    spinel_count = 0
    for a in SPINEL_A:
        for b in SPINEL_B:
            for x in SPINEL_X:
                formula = f"{a}{b}2{x}4"
                data = {
                    "prototype": "spinel",
                    "bandgap_ev": bandgap_heuristic("spinel", [a, b], x),
                    "conductivity": "semiconductor",
                    "a_site": a, "b_site": b, "x_anion": x,
                    "substitutions": substitutions_for("spinel", a, b, x),
                }
                add_node(formula, data)
                spinel_count += 1

    # ── 3. Rutiles AX2 ─────────────────────────────────────────────────────────
    rutile_count = 0
    for a in RUTILE_A:
        for x in RUTILE_X:
            formula = f"{a}{x}2"
            data = {
                "prototype": "rutile",
                "bandgap_ev": bandgap_heuristic("rutile", [a], x),
                "conductivity": "insulator",
                "a_site": a, "b_site": None, "x_anion": x,
                "substitutions": substitutions_for("rutile", a, None, x),
            }
            add_node(formula, data)
            rutile_count += 1

    # ── 4. Rocksalt AX ─────────────────────────────────────────────────────────
    rocksalt_count = 0
    for a in ROCKSALT_A:
        for x in ROCKSALT_X:
            formula = f"{a}{x}"
            data = {
                "prototype": "rocksalt",
                "bandgap_ev": bandgap_heuristic("rocksalt", [a], x),
                "conductivity": "semiconductor",
                "a_site": a, "b_site": None, "x_anion": x,
                "substitutions": substitutions_for("rocksalt", a, None, x),
            }
            add_node(formula, data)
            rocksalt_count += 1

    # ── 5. Existing 2D / MXene / MOF nodes carry over ─────────────────────────
    # Copy over any pre-existing 2D/MXene entries from base graph
    for formula, data in nodes.items():
        proto = data.get("prototype","")
        if proto in ("layered_dichalcogenide","2d_oxide","hexagonal_BN","phosphorene","carbon nitride"):
            data.setdefault("substitutions", {"A":[],"B":[],"X":[]})

    # Add canonical 2D materials
    for formula, proto, bg in MATERIALS_2D:
        if formula in seen: continue
        data = {
            "prototype": proto,
            "bandgap_ev": bg,
            "conductivity": "semiconductor",
            "a_site": formula[:2] if len(formula)>1 else formula,
            "b_site": None, "x_anion": "S" if formula in ("MoS2","WS2","MoSe2","WSe2","NbS2") else "O",
            "substitutions": {"A":[],"B":[],"X":[]},
        }
        add_node(formula, data)

    # Add MXenes
    for formula, proto, bg in MXENES:
        add_node(formula, {
            "prototype": proto, "bandgap_ev": bg,
            "conductivity": "conductor",
            "a_site": formula[:formula.index("C")-1] if "C" in formula else formula[:2],
            "b_site": None, "x_anion": "C",
            "substitutions": {"A":[],"B":[],"X":[]},
        })

    # Add MOFs
    for formula, proto, _bg in MOFS:
        add_node(formula, {
            "prototype": proto, "bandgap_ev": 0.0,
            "conductivity": "insulator",
            "a_site": "MOF", "b_site": None, "x_anion": "organic",
            "substitutions": {"A":[],"B":[],"X":[]},
        })

    # ── 6. Gap detection ───────────────────────────────────────────────────────
    # For every known perovskite, check if any A/B-site substitution neighbor is missing
    gap_nodes: dict[str,dict] = {}
    perovskite_nodes = {f:d for f,d in nodes.items() if d.get("prototype")=="perovskite"}

    for formula, data in perovskite_nodes.items():
        subs = data.get("substitutions", {})
        for site in ("A","B"):
            if site not in subs: continue
            for neighbor in subs[site]:
                # Build substituted formula
                if site == "A":
                    candidate_formula = perovskite_formula(neighbor, data["b_site"], data["x_anion"])
                else:
                    candidate_formula = perovskite_formula(data["a_site"], neighbor, data["x_anion"])
                norm = hill_order(candidate_formula)
                if norm not in seen and norm not in gap_nodes:
                    seen[norm] = True
                    gap_nodes[norm] = {
                        "prototype": "perovskite",
                        "bandgap_ev": bandgap_heuristic("perovskite", [data["a_site"], data["b_site"]], data["x_anion"]),
                        "conductivity": "semiconductor",
                        "a_site": data["a_site"] if site=="A" else neighbor,
                        "b_site": data["b_site"] if site=="B" else neighbor,
                        "x_anion": data["x_anion"],
                        "is_gap": True,
                        "gap_reason": f"substituted {site}-site from {formula}, parent node exists",
                        "substitutions": substitutions_for("perovskite",
                            data["a_site"] if site=="A" else neighbor,
                            data["b_site"] if site=="B" else neighbor,
                            data["x_anion"]),
                    }

    # Merge gap nodes
    for norm, data in gap_nodes.items():
        nodes[norm] = data

    # ── Summary ────────────────────────────────────────────────────────────────
    total = len(nodes)
    gaps = sum(1 for d in nodes.values() if d.get("is_gap"))
    gap_count = gap_nodes.__len__()

    result = {
        "metadata": {
            "version": "2.0",
            "description": f"Expanded materials graph — {total} nodes, {gaps} gap nodes",
            "families": {
                "perovskites": perovskite_count,
                "spinels": spinel_count,
                "rutiles": rutile_count,
                "rocksalt": rocksalt_count,
                "2d_materials": len(MATERIALS_2D),
                "mxenes": len(MXENES),
                "mofs": len(MOFS),
                "gap_nodes_detected": gap_count,
            }
        },
        "nodes": nodes,
    }

    with open(dst, "w") as f:
        json.dump(result, f, indent=2)

    print(f"✅ Expanded graph written to {dst}")
    print(f"   Total nodes     : {total}")
    print(f"   Gap nodes       : {gaps}")
    print(f"   Perovskites     : {perovskite_count}")
    print(f"   Spinels         : {spinel_count}")
    print(f"   Rutiles         : {rutile_count}")
    print(f"   Rocksalt        : {rocksalt_count}")
    print(f"   2D/MXene/MOF    : {len(MATERIALS_2D)+len(MXENES)+len(MOFS)}")

if __name__ == "__main__":
    main()
