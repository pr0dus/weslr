"""
WESLR Combinatorial Chemistry — Functional Group Substitution and Fragment Combination.

Generates novel organic molecule candidates by applying functional group substitution rules
and fragment combination (swapping substituents between molecules). Pure functions; I/O
only in build_chemistry_candidates and handle_propose_chemistry.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from weslr.fact_extractor import load_facts

# ─────────────────────────────────────────────────────────────────────────────
# Known functional groups (SMARTS-like string patterns for V1)
# ─────────────────────────────────────────────────────────────────────────────

_KNOWN_FUNCTIONAL_GROUPS: Dict[str, str] = {
    "hydroxyl":   "OH",
    "methoxy":    "OMe",
    "methyl":     "Me",
    "chloro":     "Cl",
    "bromo":      "Br",
    "fluoro":     "F",
    "nitro":      "NO2",
    "amino":      "NH2",
    "carboxyl":   "COOH",
    "carbonyl":   "C=O",
    "aldehydes":  "CHO",
    "sulfonic":   "SO3H",
}

# ─────────────────────────────────────────────────────────────────────────────
# Substitution rules — (from_group, to_group) pairs
# ─────────────────────────────────────────────────────────────────────────────

_SUBSTITUTION_RULES: List[tuple[str, str]] = [
    # Halogen exchange
    ("H", "Cl"),
    ("H", "Br"),
    ("H", "F"),
    # Hydrogen replacement by oxygen groups
    ("H", "OH"),
    ("H", "OMe"),
    # Hydrogen replacement by carbon groups
    ("H", "Me"),
    # Hydrogen replacement by nitro/amino
    ("H", "NO2"),
    ("H", "NH2"),
    # Hydroxyl / methoxy swap
    ("OH", "OMe"),
    ("OMe", "OH"),
    # Halogen swap
    ("Cl", "Br"),
    ("Br", "Cl"),
    # Carboxyl / ester swap
    ("COOH", "COOMe"),
    ("COOMe", "COOH"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Hardcoded known organic molecules (bootstrap when fact store is empty)
# ─────────────────────────────────────────────────────────────────────────────

_KNOWN_MOLECULES: List[Dict[str, Any]] = [
    {
        "name": "ethanol",
        "smiles": "CCO",
        "functional_groups": ["hydroxyl"],
        "trust_score": 0.90,
        "source": "known_simple_alcohol",
    },
    {
        "name": "benzene",
        "smiles": "c1ccccc1",
        "functional_groups": [],
        "trust_score": 0.95,
        "source": "known_aromatic",
    },
    {
        "name": "phenol",
        "smiles": "c1ccc(O)cc1",
        "functional_groups": ["hydroxyl"],
        "trust_score": 0.88,
        "source": "known_aromatic",
    },
    {
        "name": "toluene",
        "smiles": "Cc1ccccc1",
        "functional_groups": ["methyl"],
        "trust_score": 0.86,
        "source": "known_aromatic",
    },
    {
        "name": "acetic_acid",
        "smiles": "CC(=O)O",
        "functional_groups": ["carboxyl"],
        "trust_score": 0.85,
        "source": "known_carboxylic_acid",
    },
    {
        "name": "acetaldehyde",
        "smiles": "CC=O",
        "functional_groups": ["aldehydes"],
        "trust_score": 0.82,
        "source": "known_aldehyde",
    },
    {
        "name": "chlorobenzene",
        "smiles": "Clc1ccccc1",
        "functional_groups": ["chloro"],
        "trust_score": 0.80,
        "source": "known_halobenzene",
    },
    {
        "name": "aniline",
        "smiles": "Nc1ccccc1",
        "functional_groups": ["amino"],
        "trust_score": 0.84,
        "source": "known_amine",
    },
    {
        "name": "nitrobenzene",
        "smiles": "[O-][N+](=O)c1ccccc1",
        "functional_groups": ["nitro"],
        "trust_score": 0.78,
        "source": "known_nitro",
    },
    {
        "name": "methyl_acetate",
        "smiles": "CC(=O)OC",
        "functional_groups": ["carboxyl", "methoxy"],
        "trust_score": 0.76,
        "source": "known_ester",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Functional Group Extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_functional_groups(molecule_name: str, smiles: str = None) -> list[str]:
    """Extract functional group names present in a molecule.

    Checks both the molecule name and the SMILES string for known
    functional group patterns. Returns a list of group names found.
    """
    found: List[str] = []
    name_lower = molecule_name.lower()

    # Check molecule name for known group mentions
    for group_name, pattern in _KNOWN_FUNCTIONAL_GROUPS.items():
        if group_name in name_lower:
            if group_name not in found:
                found.append(group_name)

    # Check SMILES string for known group patterns
    if smiles:
        for group_name, pattern in _KNOWN_FUNCTIONAL_GROUPS.items():
            if pattern in smiles and group_name not in found:
                found.append(group_name)

    return found


# ─────────────────────────────────────────────────────────────────────────────
# Functional Group Replacement
# ─────────────────────────────────────────────────────────────────────────────

def replace_functional_group(smiles: str, old_group: str, new_group: str) -> str:
    """Replace occurrences of old_group in a SMILES string with new_group.

    Simple string replacement. Returns the original SMILES if no match is found.
    """
    if old_group not in smiles:
        return smiles
    return smiles.replace(old_group, new_group)


# ─────────────────────────────────────────────────────────────────────────────
# Derivative Generation — apply substitution rules to molecules
# ─────────────────────────────────────────────────────────────────────────────

def _build_derivative_explanation(
    from_group: str,
    to_group: str,
    parent_name: str,
    parent_trust: float,
) -> str:
    """Build a human-readable explanation for a functional group substitution."""
    # Common organic chemistry rationale
    halide_notes = {
        ("H", "Cl"): "Cl substitution can increase lipophilicity and metabolic stability.",
        ("H", "Br"): "Br substitution provides a handle for further cross-coupling reactions.",
        ("H", "F"):  "F substitution increases electronegativity and can block metabolic oxidation sites.",
        ("Cl", "Br"): "Br is larger than Cl; swapping can modulate steric fit at the binding site.",
        ("Br", "Cl"): "Cl is smaller than Br; swapping can improve target specificity.",
    }
    oxygen_notes = {
        ("H", "OH"):  "OH introduction adds hydrogen-bond donor capacity.",
        ("H", "OMe"): "OMe adds an ether oxygen; increases polarity and steric bulk.",
        ("OH", "OMe"): "OMe/OH swap modulates hydrogen-bond donor vs. acceptor character.",
        ("COOH", "COOMe"): "Esterification (COOH→COOMe) increases membrane permeability.",
        ("COOMe", "COOH"): "Hydrolysis (COOMe→COOH) restores carboxylic acid.",
    }
    carbon_notes = {
        ("H", "Me"): "Me addition increases hydrophobic bulk; can improve binding affinity.",
    }
    nitrogen_notes = {
        ("H", "NO2"): "NO2 addition is strongly electron-withdrawing; can alter reactivity.",
        ("H", "NH2"): "NH2 addition creates a primary amine; enables further coupling reactions.",
    }

    notes = {}
    notes.update(halide_notes)
    notes.update(oxygen_notes)
    notes.update(carbon_notes)
    notes.update(nitrogen_notes)

    note = notes.get((from_group, to_group), f"{from_group}→{to_group} substitution.")
    base = f"{from_group}→{to_group} in {parent_name} ({note})"
    if parent_trust > 0:
        base += f" Reference molecule trust={parent_trust:.2f}."
    return base


def generate_derivatives(molecule_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate molecule derivatives by applying all substitution rules.

    For each molecule with trust > 0.6, applies all substitution rules
    to produce derivative candidates. Each derivative includes name,
    SMILES, transformation description, parent metadata, candidate_score,
    and explanation.
    """
    derivatives: List[Dict[str, Any]] = []

    for mol in molecule_facts:
        trust = mol.get("trust_score", mol.get("trust", 0))
        if trust <= 0.6:
            continue

        name = mol.get("name", "")
        smiles = mol.get("smiles", "")
        functional_groups = mol.get("functional_groups", extract_functional_groups(name, smiles))

        for from_group, to_group in _SUBSTITUTION_RULES:
            # Only apply rules that are relevant to this molecule
            # (skip if the source group is not present)
            if smiles and from_group not in smiles and from_group not in functional_groups:
                # For H substitutions, try even if not explicit (generic H replacement)
                if from_group != "H":
                    continue

            # Build new SMILES via string replacement
            if smiles:
                new_smiles = replace_functional_group(smiles, from_group, to_group)
            else:
                new_smiles = ""

            # Skip if no change
            if smiles and new_smiles == smiles:
                continue

            # Build derivative name
            if smiles:
                # Simple naming: parent_name + substituent abbreviation
                substituent_map = {
                    "Cl": "chloro",
                    "Br": "bromo",
                    "F": "fluoro",
                    "OH": "hydroxy",
                    "OMe": "methoxy",
                    "Me": "methyl",
                    "NO2": "nitro",
                    "NH2": "amino",
                }
                sub_name = substituent_map.get(to_group, to_group.lower())
                deriv_name = f"{name}_{sub_name}" if name else f"deriv_{sub_name}"
            else:
                deriv_name = f"{name}_deriv" if name else "derivative"

            candidate_score = round((trust + 0.85) / 2, 3)
            explanation = _build_derivative_explanation(from_group, to_group, name, trust)

            derivatives.append({
                "name": deriv_name,
                "formula": mol.get("formula"),
                "smiles": new_smiles,
                "functional_groups": [
                    g for g in functional_groups
                    if g != from_group
                ] + ([to_group] if to_group in _KNOWN_FUNCTIONAL_GROUPS else []),
                "transformation": f"Replace {from_group} with {to_group} in {name}",
                "parent_name": name,
                "parent_smiles": smiles,
                "parent_trust": trust,
                "candidate_score": candidate_score,
                "explanation": explanation,
            })

    return derivatives


# ─────────────────────────────────────────────────────────────────────────────
# Fragment Combination — swap substituents between molecules
# ─────────────────────────────────────────────────────────────────────────────

def combine_fragments(molecule1: Dict[str, Any], molecule2: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Combine two molecules by swapping their substituents/functional groups.

    Takes two molecules and generates candidates where functional groups
    from molecule2 are attached to the core/framework of molecule1 and vice versa.
    Returns a list of combined candidate dicts.
    """
    candidates: List[Dict[str, Any]] = []

    name1 = molecule1.get("name", "mol1")
    name2 = molecule2.get("name", "mol2")
    smiles1 = molecule1.get("smiles", "")
    smiles2 = molecule2.get("smiles", "")
    trust1 = molecule1.get("trust_score", molecule1.get("trust", 0))
    trust2 = molecule2.get("trust_score", molecule2.get("trust", 0))
    fg1 = molecule1.get("functional_groups", extract_functional_groups(name1, smiles1))
    fg2 = molecule2.get("functional_groups", extract_functional_groups(name2, smiles2))

    # For each functional group in molecule2, try attaching to molecule1's core
    for group_name, group_pattern in _KNOWN_FUNCTIONAL_GROUPS.items():
        if group_name in fg2:
            # Group is present in molecule2 — try adding to molecule1
            if smiles1:
                # Simple concatenation model: attach group to molecule1
                # (for real SMILES this would need reaction validation)
                combined_smiles = smiles1 + group_pattern
            else:
                combined_smiles = ""

            if combined_smiles:
                combined_name = f"{name1}_with_{group_name}"
                cand_score = round((trust1 + trust2 + 0.85) / 3, 3)
                explanation = (
                    f"Fragment combination: added {group_name} ({group_pattern}) from {name2} "
                    f"to {name1}. Parent {name1} trust={trust1:.2f}, {name2} trust={trust2:.2f}."
                )
                candidates.append({
                    "name": combined_name,
                    "smiles": combined_smiles,
                    "functional_groups": list(fg1) + [group_name],
                    "transformation": f"Add {group_name} from {name2} to {name1}",
                    "parent_name": name1,
                    "parent_smiles": smiles1,
                    "parent_trust": trust1,
                    "partner_name": name2,
                    "partner_smiles": smiles2,
                    "partner_trust": trust2,
                    "candidate_score": cand_score,
                    "explanation": explanation,
                })

    # For each functional group in molecule1, try attaching to molecule2's core
    for group_name, group_pattern in _KNOWN_FUNCTIONAL_GROUPS.items():
        if group_name in fg1:
            if smiles2:
                combined_smiles = smiles2 + group_pattern
            else:
                combined_smiles = ""

            if combined_smiles:
                combined_name = f"{name2}_with_{group_name}"
                cand_score = round((trust1 + trust2 + 0.85) / 3, 3)
                explanation = (
                    f"Fragment combination: added {group_name} ({group_pattern}) from {name1} "
                    f"to {name2}. Parent {name2} trust={trust2:.2f}, {name1} trust={trust1:.2f}."
                )
                candidates.append({
                    "name": combined_name,
                    "smiles": combined_smiles,
                    "functional_groups": list(fg2) + [group_name],
                    "transformation": f"Add {group_name} from {name1} to {name2}",
                    "parent_name": name2,
                    "parent_smiles": smiles2,
                    "parent_trust": trust2,
                    "partner_name": name1,
                    "partner_smiles": smiles1,
                    "partner_trust": trust1,
                    "candidate_score": cand_score,
                    "explanation": explanation,
                })

    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# Main Combinatorial Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_candidates(molecules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate chemistry candidates by applying derivatives and fragment combination.

    Calls generate_derivatives and combine_fragments, deduplicates by name,
    and returns a combined list sorted by candidate_score descending.
    """
    derivatives = generate_derivatives(molecules)
    combined: List[Dict[str, Any]] = list(derivatives)

    # Fragment combination: for each pair of molecules
    for i, mol1 in enumerate(molecules):
        for mol2 in molecules[i + 1:]:
            pair_candidates = combine_fragments(mol1, mol2)
            combined.extend(pair_candidates)

    # Deduplicate by name
    seen_names: set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for c in combined:
        if c["name"] not in seen_names:
            seen_names.add(c["name"])
            deduped.append(c)

    # Sort by candidate_score descending
    deduped.sort(key=lambda c: c["candidate_score"], reverse=True)
    return deduped


# ─────────────────────────────────────────────────────────────────────────────
# Fact-Store-Backed Candidate Builder
# ─────────────────────────────────────────────────────────────────────────────

def _parse_molecule_facts(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse molecule facts from the fact store into molecule dicts.

    Extracts name, SMILES, functional_groups, and trust_score from
    fact assertions that describe molecular entities.
    """
    molecules: Dict[str, Dict[str, Any]] = {}

    for f in facts:
        predicate = f.get("predicate", "")
        subject = f.get("subject", "")
        obj = f.get("object", "")
        trust = f.get("confidence", f.get("trust_score", 0.7))

        # Look for molecule-related predicates
        molecule_name = ""
        smiles = ""

        if "smiles" in predicate.lower() or "has_smiles" in predicate.lower():
            molecule_name = subject
            smiles = obj
        elif "molecule" in predicate.lower() or "compound" in predicate.lower():
            molecule_name = subject
            # Try to find SMILES in object or fact_data
            fd = f.get("fact_data", {})
            smiles = fd.get("smiles", obj if "=" in obj[:20] else "")

        if not molecule_name:
            # Fall back to subject as molecule name
            molecule_name = subject

        if not molecule_name:
            continue

        key = molecule_name.lower().strip()
        if key not in molecules:
            molecules[key] = {
                "name": molecule_name,
                "smiles": smiles,
                "functional_groups": extract_functional_groups(molecule_name, smiles),
                "trust_scores": [],
            }
        if smiles and not molecules[key].get("smiles"):
            molecules[key]["smiles"] = smiles
        molecules[key]["trust_scores"].append(trust)

    # Build list with averaged trust
    result: List[Dict[str, Any]] = []
    for data in molecules.values():
        trust_scores = data["trust_scores"]
        avg_trust = round(sum(trust_scores) / len(trust_scores), 3) if trust_scores else 0.5
        result.append({
            "name": data["name"],
            "smiles": data.get("smiles", ""),
            "functional_groups": data["functional_groups"],
            "trust_score": avg_trust,
            "source": "fact_store",
        })
    return result


def build_chemistry_candidates(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build molecule dicts from fact store merged with known molecules.

    1. Load facts from the fact store for the tenant.
    2. Parse molecule facts (name, SMILES, functional groups, trust).
    3. Merge with hardcoded known molecules as fallback.
    4. Return list of molecule dicts.
    """
    all_facts = load_facts(tenant_id=tenant_id, limit=500)
    molecules = _parse_molecule_facts(all_facts)

    # Merge with hardcoded known molecules
    seen_names: set[str] = {m["name"] for m in molecules}
    for km in _KNOWN_MOLECULES:
        if km["name"] not in seen_names:
            molecules.append(km)

    return molecules


# ─────────────────────────────────────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────────────────────────────────────

def format_chemistry_candidate(candidate: Dict[str, Any], index: int) -> str:
    """Format a single chemistry candidate as a readable string."""
    name = candidate.get("name", "unknown")
    smiles = candidate.get("smiles", "n/a")
    fg = candidate.get("functional_groups", [])
    transformation = candidate.get("transformation", "")
    parent_name = candidate.get("parent_name", "")
    parent_trust = candidate.get("parent_trust", 0)
    candidate_score = candidate.get("candidate_score", 0)
    explanation = candidate.get("explanation", "")

    lines = [
        f"{index}. **{name}** — {transformation}",
    ]
    if smiles:
        lines.append(f"   SMILES: {smiles}")
    if fg:
        lines.append(f"   Functional groups: {', '.join(fg)}")
    lines.append(f"   Parent: {parent_name} (trust={parent_trust:.2f})")
    lines.append(f"   Candidate trust: {candidate_score:.3f}")
    lines.append(f"   Explanation: {explanation}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# CLI Handler
# ─────────────────────────────────────────────────────────────────────────────

def handle_propose_chemistry(
    message: str = "",
    tenant_id: Optional[str] = None,
    limit: int = 10,
) -> str:
    """Handle /propose chemistry command.

    Loads molecules from fact store (and hardcoded fallback),
    generates combinatorial chemistry candidates, and returns
    a ranked list with explanations.
    """
    molecules = build_chemistry_candidates(tenant_id=tenant_id)
    candidates = generate_candidates(molecules)

    if not candidates:
        return (
            "No chemistry candidates generated.\n"
            "Ensure the fact store contains molecule facts with trust > 0.6.\n"
            "Ingest chemistry literature first, then retry."
        )

    lines = [
        f"Chemistry candidates (functional group substitution + fragment combination, top {min(limit, len(candidates))}):",
        "",
    ]
    for i, c in enumerate(candidates[:limit], 1):
        lines.append(format_chemistry_candidate(c, i))
        lines.append("")

    if len(candidates) > limit:
        lines.append(
            f"... and {len(candidates) - limit} more candidates. "
            "Reply with /propose chemistry for full list."
        )

    return "\n".join(lines)