"""Read-only materials workflow guidance.

This module does not generate structures, call databases, run DFT, query the web,
modify state, or route chat. It only detects materials-discovery style requests
and returns a conservative evidence checklist plus safe claim boundaries.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any


SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

CANONICAL_SCATTI_FORMULA = "CaSc2TiO6"
SCATTI_ALIASES = {"scatti"}

MATERIALS_KEYWORDS = (
 "new oxide",
 "predicted compound",
 "material discovery",
 "materials discovery",
 "crystal structure",
 "crystal structure prediction",
 "csp",
 "dft",
 "novelty",
 "stability",
 "synthesis",
)

EVIDENCE_CHECKLIST = (
 "candidate_definition",
 "formula_normalization",
 "literature_search",
 "database_crosscheck",
 "chemical_plausibility",
 "structure_generation_or_CSP",
 "stability_screening",
 "competing_phase_analysis",
 "dynamic_stability",
 "property_prediction",
 "synthesis_feasibility",
 "evidence_package",
 "publication_draft",
)


def _normalize_text(text: str) -> str:
 """Normalize unicode subscripts and compatibility characters."""
 if not isinstance(text, str):
  text = ""
 normalized = unicodedata.normalize("NFKC", text)
 normalized = normalized.translate(SUBSCRIPT_DIGITS)
 return normalized


def _contains_scatti_formula(normalized_text: str) -> bool:
 compact = re.sub(r"\s+", "", normalized_text)
 return re.search(r"CaSc2TiO6", compact, flags=re.IGNORECASE) is not None


def _detect_trigger_terms(normalized_text: str) -> list[str]:
 lower = normalized_text.lower()
 terms: list[str] = []

 for keyword in MATERIALS_KEYWORDS:
  if keyword in lower:
   terms.append(keyword)

 for alias in SCATTI_ALIASES:
  if re.search(rf"\b{re.escape(alias)}\b", lower):
   terms.append(alias)

 if _contains_scatti_formula(normalized_text):
  terms.append(CANONICAL_SCATTI_FORMULA)

 return sorted(set(terms))


def _detect_candidates(normalized_text: str) -> list[dict[str, Any]]:
 lower = normalized_text.lower()
 candidates: list[dict[str, Any]] = []

 if _contains_scatti_formula(normalized_text) or re.search(r"\bscatti\b", lower):
  candidates.append(
   {
    "name": "scatti",
    "formula": CANONICAL_SCATTI_FORMULA,
    "aliases": ["scatti", "CaSc₂TiO₆", "CaSc2TiO6"],
   }
  )

 return candidates


def detect_materials_workflow(text: str) -> dict[str, Any]:
 """Detect whether text belongs to a materials/scientific discovery workflow."""
 normalized_text = _normalize_text(text)
 trigger_terms = _detect_trigger_terms(normalized_text)
 candidates = _detect_candidates(normalized_text)

 domain = "materials_discovery" if trigger_terms or candidates else "unknown"
 normalized_formula = candidates[0]["formula"] if candidates else None

 if candidates:
  confidence = 0.9
 elif trigger_terms:
  confidence = 0.65
 else:
  confidence = 0.0

 return {
  "domain": domain,
  "candidates": candidates,
  "normalized_formula": normalized_formula,
  "trigger_terms": trigger_terms,
  "confidence": confidence,
  "read_only": True,
 }


def _normalize_evidence(evidence: dict[str, Any] | None) -> dict[str, Any]:
 if evidence is None:
  return {}
 if not isinstance(evidence, dict):
  return {}
 return evidence


def _truthy_evidence(evidence: dict[str, Any], key: str) -> bool:
 return bool(evidence.get(key))


def _checked_sources(evidence: dict[str, Any]) -> list[str]:
 value = evidence.get("checked_sources")
 if isinstance(value, str) and value.strip():
  return [value.strip()]
 if isinstance(value, (list, tuple, set)):
  return [str(item).strip() for item in value if str(item).strip()]
 return []


def _completed_evidence(evidence: dict[str, Any]) -> list[str]:
 return [key for key in EVIDENCE_CHECKLIST if _truthy_evidence(evidence, key)]


def _missing_evidence(evidence: dict[str, Any]) -> list[str]:
 return [key for key in EVIDENCE_CHECKLIST if not _truthy_evidence(evidence, key)]


def _workflow_stage(missing: list[str]) -> str:
 if missing:
  return missing[0]
 return "evidence_package_ready"


def _claim_boundary(text: str, evidence: dict[str, Any], missing: list[str]) -> dict[str, Any]:
 normalized_text = _normalize_text(text).lower()
 checked_sources = _checked_sources(evidence)

 missing_literature_or_database = (
  "literature_search" in missing or "database_crosscheck" in missing
 )
 missing_stability = (
  "stability_screening" in missing
  or "competing_phase_analysis" in missing
  or "dynamic_stability" in missing
 )

 blocked_claims: list[str] = []

 if "discovered" in normalized_text or "discovery" in normalized_text:
  if missing_literature_or_database or missing_stability:
   blocked_claims.append("discovered")

 if "stable" in normalized_text or "stability" in normalized_text:
  if missing_stability:
   blocked_claims.append("stable")

 if "novel" in normalized_text or "novelty" in normalized_text:
  if missing_literature_or_database:
   blocked_claims.append("absolute_novelty")

 if missing_literature_or_database:
  novelty_wording = "Do not claim absolute novelty."
 elif checked_sources:
  novelty_wording = "May say: not found in checked sources."
 else:
  novelty_wording = "Avoid novelty wording until checked sources are recorded."

 if missing_stability:
  stability_wording = (
   "Do not claim stability until stability screening, competing phase "
   "analysis, and dynamic stability evidence exist."
  )
 else:
  stability_wording = "Stability wording may be bounded to the completed evidence."

 if "discovered" in blocked_claims:
  discovery_wording = (
   "Use candidate or predicted compound; do not claim discovered until "
   "literature/database and stability evidence are complete."
  )
 else:
  discovery_wording = "Use conservative wording tied to available evidence."

 return {
  "safe_terms": ["candidate", "predicted compound", "requires validation"],
  "blocked_claims": sorted(set(blocked_claims)),
  "novelty_wording": novelty_wording,
  "stability_wording": stability_wording,
  "discovery_wording": discovery_wording,
  "checked_sources": checked_sources,
  "summary": (
   "Missing literature/database/stability evidence blocks discovered, "
   "absolute novelty, and stable claims. Prefer candidate, predicted "
   "compound, and requires validation."
  ),
 }


def _next_steps(missing: list[str]) -> list[str]:
 labels = {
  "candidate_definition": "Define the candidate composition, name, and intended material family.",
  "formula_normalization": "Normalize the formula and aliases, including unicode subscript variants.",
  "literature_search": "Perform and record a literature search.",
  "database_crosscheck": "Cross-check crystallographic/materials databases and record checked sources.",
  "chemical_plausibility": "Assess charge balance, oxidation states, ionic radii, and plausible coordination.",
  "structure_generation_or_CSP": "Generate candidate structures or run a CSP-style search.",
  "stability_screening": "Screen thermodynamic stability using an appropriate computational method.",
  "competing_phase_analysis": "Compare against competing phases and decomposition products.",
  "dynamic_stability": "Check dynamic stability, for example by phonon-style analysis.",
  "property_prediction": "Estimate relevant properties only after structure/stability evidence improves.",
  "synthesis_feasibility": "Assess synthesis pathway and experimental feasibility.",
  "evidence_package": "Assemble a reproducible evidence package with inputs, outputs, and provenance.",
  "publication_draft": "Draft publication wording with conservative claim boundaries.",
 }
 return [labels[key] for key in missing[:5]]


def guide_materials_workflow(
 text: str, evidence: dict[str, Any] | None = None
) -> dict[str, Any]:
 """Return conservative read-only workflow guidance for materials discovery text."""
 detection = detect_materials_workflow(text)
 normalized_evidence = _normalize_evidence(evidence)

 if detection["domain"] == "unknown":
  return {
   "domain": "unknown",
   "candidates": [],
   "normalized_formula": None,
   "workflow_stage": "unknown",
   "completed_evidence": [],
   "missing_evidence": [],
   "next_steps": [],
   "claim_boundary": {
    "safe_terms": [],
    "blocked_claims": [],
    "summary": "No materials-discovery workflow detected.",
   },
   "confidence": 0.0,
   "read_only": True,
  }

 completed = _completed_evidence(normalized_evidence)
 missing = _missing_evidence(normalized_evidence)

 # Formula presence is detection evidence but not persisted state. If the caller
 # has not supplied formula_normalization evidence, we still recommend recording it.
 return {
  "domain": detection["domain"],
  "candidates": detection["candidates"],
  "normalized_formula": detection["normalized_formula"],
  "workflow_stage": _workflow_stage(missing),
  "completed_evidence": completed,
  "missing_evidence": missing,
  "next_steps": _next_steps(missing),
  "claim_boundary": _claim_boundary(text, normalized_evidence, missing),
  "confidence": detection["confidence"],
  "read_only": True,
 }
