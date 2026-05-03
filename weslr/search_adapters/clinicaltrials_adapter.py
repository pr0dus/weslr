"""
ClinicalTrials.gov Search Adapter — Phase 4.4

Provides structured clinical trial search using the ClinicalTrials.gov API v2.
Produces evidence packets and pre-structured fact assertions.

API: GET https://clinicaltrials.gov/api/v2/studies?query.term=<q>&pageSize=<n>
Response: JSON with studies[].protocolSection.{identificationModule, statusModule,
  designModule, armsInterventionsModule, outcomesModule, eligibilityModule}

No raw prompts stored. No hidden learning. No automatic execution.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from weslr.tenant_context import get_current_tenant, resolve_path

DEFAULT_API_BASE = "https://clinicaltrials.gov/api/v2"


def _make_request(url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """Make an HTTP GET request and return parsed JSON, or None on error."""
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _strip_html(text: str) -> str:
    """Remove basic HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _normalize_trial_id(nct_id: str) -> str:
    """Normalize NCT ID to lowercase without prefix."""
    return nct_id.lower().replace("nct", "").strip()


def _map_phase(phase_str: Optional[str]) -> str:
    """Map phase string to normalized predicate.

    Checks are ordered from most specific to least specific to avoid
    substring collisions (e.g., 'IV' contains 'I', 'III' contains 'II').
    """
    if not phase_str:
        return "phase_unknown"
    p = phase_str.upper()
    if "PHASE IV" in p or "PHASE 4" in p:
        return "phase_iv"
    if "PHASE III" in p or "PHASE 3" in p:
        return "phase_iii"
    if "PHASE II" in p or "PHASE 2" in p:
        return "phase_ii"
    if "PHASE I" in p or "PHASE 1" in p:
        return "phase_i"
    return "phase_unknown"


# ──────────────────────────────────────────────────────────────────────────────
# Main API
# ──────────────────────────────────────────────────────────────────────────────

def search_clinicaltrials(
    query: str,
    max_results: int = 10,
    tenant_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search ClinicalTrials.gov and return a list of study dicts.

    Args:
        query: Natural language query (e.g., "BRCA1 breast cancer")
        max_results: Max number of studies to return (default 10)
        tenant_id: Optional tenant for evidence packet path resolution

    Returns:
        List of study dicts with keys: nct_id, title, status, phase, enrollment,
        interventions, primary_outcome, eligibility, brief_summary, source_url
    """
    encoded_q = urllib.parse.quote(query)
    url = f"{DEFAULT_API_BASE}/studies?query.term={encoded_q}&pageSize={max_results}&format=json"

    data = _make_request(url)
    if not data or "studies" not in data:
        return []

    studies: List[Dict[str, Any]] = []
    for study in data.get("studies", [])[:max_results]:
        ident = study.get("protocolSection", {}).get("identificationModule", {})
        status_mod = study.get("protocolSection", {}).get("statusModule", {})
        design = study.get("protocolSection", {}).get("designModule", {})
        arms_int = study.get("protocolSection", {}).get("armsInterventionsModule", {})
        outcomes = study.get("protocolSection", {}).get("outcomesModule", {})
        eligibility = study.get("protocolSection", {}).get("eligibilityModule", {})
        desc = study.get("protocolSection", {}).get("descriptionModule", {})

        nct_id = ident.get("nctId", "unknown")
        title = _strip_html(ident.get("briefTitle", ""))
        overall_status = status_mod.get("overallStatus", "UNKNOWN")
        phase_list = design.get("phases", [])
        phase_str = phase_list[0] if phase_list else None

        enrollment_info = design.get("enrollmentInfo", {})
        enrollment_count = enrollment_info.get("count") if enrollment_info else None

        interventions = []
        for arm in arms_int.get("armInterventions", []):
            itype = arm.get("type", "OTHER")
            name = _strip_html(arm.get("name", ""))
            if name:
                interventions.append(f"{itype}: {name}")

        primary_outcomes = []
        for mo in outcomes.get("primaryOutcomes", [])[:3]:
            measure = _strip_html(mo.get("measure", ""))
            if measure:
                primary_outcomes.append(measure)

        eligibility_criteria = ""
        if eligibility.get("eligibilityCriteria"):
            criteria_text = _strip_html(eligibility["eligibilityCriteria"])
            # Truncate to first 300 chars
            eligibility_criteria = criteria_text[:300] + ("..." if len(criteria_text) > 300 else "")

        brief_summary = _strip_html(desc.get("briefSummary", ""))[:500]

        studies.append({
            "nct_id": nct_id,
            "title": title,
            "status": overall_status,
            "phase": phase_str,
            "phase_normalized": _map_phase(phase_str),
            "enrollment_count": enrollment_count,
            "interventions": interventions,
            "primary_outcomes": primary_outcomes,
            "eligibility_criteria": eligibility_criteria,
            "brief_summary": brief_summary,
            "source_url": f"https://clinicaltrials.gov/study/{nct_id}",
            "api_source": "clinicaltrials.gov",
            "search_query": query,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        })

    return studies


# ──────────────────────────────────────────────────────────────────────────────
# Fact Extraction from Structured Data
# ──────────────────────────────────────────────────────────────────────────────

def extract_trial_facts(study: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert a structured study dict into fact assertion dicts.

    Each fact has subject (trial ID), predicate, object, and fact_data with
    structured fields from the trial record.
    """
    facts: List[Dict[str, Any]] = []
    nct_id = study.get("nct_id", "")
    nct_normalized = _normalize_trial_id(nct_id)

    # Phase fact
    if study.get("phase_normalized"):
        facts.append({
            "subject": nct_normalized,
            "predicate": "phase",
            "object": study["phase_normalized"],
            "fact_data": {"phase": study.get("phase", ""), "phase_normalized": study["phase_normalized"]},
            "source_type": "clinicaltrials_structured",
            "source_reference": {"type": "clinicaltrials.gov", "nct_id": nct_id},
            "trust_score": 0.88,
        })

    # Enrollment fact
    if study.get("enrollment_count") is not None:
        enrollment = study["enrollment_count"]
        try:
            enrollment = int(enrollment)
            facts.append({
                "subject": nct_normalized,
                "predicate": "enrollment",
                "object": str(enrollment),
                "fact_data": {"enrollment_count": enrollment},
                "source_type": "clinicaltrials_structured",
                "source_reference": {"type": "clinicaltrials.gov", "nct_id": nct_id},
                "trust_score": 0.88,
            })
        except (ValueError, TypeError):
            pass

    # Primary endpoint
    for outcome in study.get("primary_outcomes", [])[:2]:
        facts.append({
            "subject": nct_normalized,
            "predicate": "primary_endpoint",
            "object": outcome[:120],
            "fact_data": {"endpoint": outcome},
            "source_type": "clinicaltrials_structured",
            "source_reference": {"type": "clinicaltrials.gov", "nct_id": nct_id},
            "trust_score": 0.85,
        })

    # Trial status
    if study.get("status"):
        facts.append({
            "subject": nct_normalized,
            "predicate": "trial_status",
            "object": study["status"].lower(),
            "fact_data": {"status": study["status"]},
            "source_type": "clinicaltrials_structured",
            "source_reference": {"type": "clinicaltrials.gov", "nct_id": nct_id},
            "trust_score": 0.90,
        })

    # Has drug relationship (for each intervention)
    for intervention in study.get("interventions", []):
        if ":" in intervention:
            itype, name = intervention.split(":", 1)
            itype = itype.strip().lower()
            name = name.strip()
            if itype in ("drug", "biologic", "vaccine") and name:
                # Drug fact
                drug_normalized = name.lower().replace(" ", "_")
                facts.append({
                    "subject": nct_normalized,
                    "predicate": "has_drug",
                    "object": drug_normalized,
                    "fact_data": {"drug_name": name, "intervention_type": itype},
                    "source_type": "clinicaltrials_structured",
                    "source_reference": {"type": "clinicaltrials.gov", "nct_id": nct_id},
                    "trust_score": 0.85,
                })

    return facts


# ──────────────────────────────────────────────────────────────────────────────
# Evidence Packet Writing
# ──────────────────────────────────────────────────────────────────────────────

def write_trial_evidence_packet(
    studies: List[Dict[str, Any]],
    query: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Write a clinical trial evidence packet to external_evidence_packets.jsonl.

    Returns dict with packet_id, study_count, path.
    """
    from weslr.search_adapters.evidence_packet_store import append_evidence_packet

    packet = {
        "packet_id": f"ctgov_{int(time.time())}",
        "query": query,
        "source": "clinicaltrials.gov",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "study_count": len(studies),
        "studies": studies,
    }

    result = append_evidence_packet(packet, tenant_id=tenant_id)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Combined Search Function
# ──────────────────────────────────────────────────────────────────────────────

def search_trials(
    query: str,
    max_results: int = 10,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a clinical trials search and return structured results + evidence packet.

    Returns:
        dict with keys: studies (list), fact_count (int), packet_id (str),
        summary (str for display)
    """
    studies = search_clinicaltrials(query, max_results, tenant_id)
    if not studies:
        return {
            "studies": [], "fact_count": 0, "packet_id": None,
            "summary": f"No clinical trial results for '{query}'.",
        }

    all_facts: List[Dict[str, Any]] = []
    for study in studies:
        all_facts.extend(extract_trial_facts(study))

    # Write evidence packet
    packet_result = write_trial_evidence_packet(studies, query, tenant_id)
    packet_id = packet_result.get("packet_id", "unknown")

    # Write facts to fact store
    from weslr.fact_extractor import append_enriched_fact
    written = 0
    for fact in all_facts:
        append_enriched_fact(fact, tenant_id=tenant_id)
        written += 1

    # Build summary
    phases = {}
    for s in studies:
        p = s.get("phase_normalized", "unknown")
        phases[p] = phases.get(p, 0) + 1

    lines = [
        f"ClinicalTrials.gov search: '{query}'",
        f"{len(studies)} study/studies, {written} facts extracted",
        f"Packet: {packet_id}",
        "",
    ]
    for study in studies[:5]:
        nct = study.get("nct_id", "")
        phase = study.get("phase", "")
        status = study.get("status", "")
        title = study.get("title", "")[:60]
        interventions = study.get("interventions", [])
        drugs = [i.split(":")[1].strip() for i in interventions if i.startswith("Drug:")][:2]
        lines.append(f"  {nct}  [{phase or '?'}] {status}")
        lines.append(f"    {title}")
        if drugs:
            lines.append(f"    Drugs: {', '.join(drugs)}")

    return {
        "studies": studies,
        "fact_count": written,
        "packet_id": packet_id,
        "summary": "\n".join(lines),
    }