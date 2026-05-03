"""PubChem search adapter using PUG REST API (free, no API key required).

Provides compound name → CID lookup, molecular property fetching, and
structured search across PubChem's consolidated compound database.

Base URL: https://pubchem.ncbi.nlm.nih.gov/rest/pug
Rate limit: 5 req/s (0.2s between requests).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests

_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
_RATE_LIMIT_DELAY = 0.20  # 5 req/s


def _rate_limit_sleep():
    time.sleep(_RATE_LIMIT_DELAY)


# ──────────────────────────────────────────────────────────────────────────────
# CID Lookup
# ──────────────────────────────────────────────────────────────────────────────

def compound_name_to_cid(name: str) -> int:
    """Return PubChem CID for a compound name.

    Args:
        name: Compound name (e.g., "aspirin", "caffeine").

    Returns:
        PubChem CID as int.

    Raises:
        ValueError: If the name is not found or the request fails.
    """
    _rate_limit_sleep()
    encoded = requests.utils.quote(name)
    url = f"{_BASE_URL}/compound/name/{encoded}/cids/JSON"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    cid_list = data.get("IdentifierList", {}).get("CID", [])
    if not cid_list:
        raise ValueError(f"No CID found for compound name: {name}")
    return int(cid_list[0])


# ──────────────────────────────────────────────────────────────────────────────
# Property Fetching
# ──────────────────────────────────────────────────────────────────────────────

def fetch_compound_properties(
    cid: int,
    properties: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Fetch molecular properties for a PubChem CID.

    Args:
        cid: PubChem Compound ID.
        properties: List of property keys to request. Defaults to all
                   known properties (MolecularWeight, MolecularFormula,
                   CanonicalSMILES, IsomericSMILES, InChI, InChIKey,
                   XLogP, IUPACName, Synonyms).

    Returns:
        Dict with keys: cid, name, formula, molecular_weight, smiles,
        inchi, logp, iupac_name, synonyms, url.
    """
    if properties is None:
        properties = [
            "MolecularWeight",
            "MolecularFormula",
            "CanonicalSMILES",
            "IsomericSMILES",
            "InChI",
            "InChIKey",
            "XLogP",
            "IUPACName",
        ]

    _rate_limit_sleep()
    prop_str = ",".join(properties)
    url = f"{_BASE_URL}/compound/cid/{cid}/property/{prop_str}/JSON"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    props = data.get("PropertyTable", {}).get("Properties", [{}])[0]

    result = {
        "cid": cid,
        "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
    }

    mw = props.get("MolecularWeight")
    if mw is not None:
        result["molecular_weight"] = float(mw)

    result["formula"] = props.get("MolecularFormula", "")
    result["smiles"] = props.get("CanonicalSMILES") or props.get("IsomericSMILES", "")
    result["inchi"] = props.get("InChI", "")
    result["inchi_key"] = props.get("InChIKey", "")
    result["logp"] = props.get("XLogP")
    result["iupac_name"] = props.get("IUPACName", "")

    # Fetch synonyms separately
    synonyms = _fetch_synonyms(cid)
    if synonyms:
        result["synonyms"] = synonyms[:10]  # cap at 10

    return result


def _fetch_synonyms(cid: int) -> List[str]:
    """Fetch at most 10 synonyms for a CID."""
    try:
        _rate_limit_sleep()
        url = f"{_BASE_URL}/compound/cid/{cid}/synonyms/JSON"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        syn_list = data.get("InformationList", {}).get("Information", [{}])
        if syn_list:
            return syn_list[0].get("Synonym", [])[:10]
    except Exception:
        pass
    return []


# ──────────────────────────────────────────────────────────────────────────────
# Main Search Interface
# ──────────────────────────────────────────────────────────────────────────────

def search_pubchem(
    query: str,
    search_type: str = "name",
) -> Dict[str, Any]:
    """Search PubChem and return structured compound data.

    Args:
        query: Search term — compound name, SMILES, or molecular formula.
        search_type: One of "name" (default), "smiles", "formula".

    Returns:
        Dict with keys: cid, name, formula, molecular_weight, smiles,
        inchi, logp, url. Returns a dict with "error" key on failure.
    """
    if search_type not in ("name", "smiles", "formula"):
        return {"error": f"Invalid search_type '{search_type}'. Use 'name', 'smiles', or 'formula'."}

    try:
        if search_type == "name":
            cid = compound_name_to_cid(query)
        elif search_type == "smiles":
            cid = _smiles_to_cid(query)
        else:  # formula
            cid = _formula_to_cid(query)

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"PubChem request failed: {e}"}

    try:
        result = fetch_compound_properties(cid)
        return result
    except Exception as e:
        return {"error": f"Failed to fetch properties for CID {cid}: {e}"}


def _smiles_to_cid(smiles: str) -> int:
    """Convert a SMILES string to a PubChem CID."""
    _rate_limit_sleep()
    encoded = requests.utils.quote(smiles)
    url = f"{_BASE_URL}/compound/smiles/{encoded}/cids/JSON"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    cid_list = data.get("IdentifierList", {}).get("CID", [])
    if not cid_list:
        raise ValueError(f"No CID found for SMILES: {smiles}")
    return int(cid_list[0])


def _formula_to_cid(formula: str) -> int:
    """Convert a molecular formula to a PubChem CID.

    Note: Formula searches can return multiple CIDs. Returns the first one.
    """
    _rate_limit_sleep()
    encoded = requests.utils.quote(formula)
    url = f"{_BASE_URL}/compound/formula/{encoded}/cids/JSON"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    cid_list = data.get("IdentifierList", {}).get("CID", [])
    if not cid_list:
        raise ValueError(f"No CID found for formula: {formula}")
    return int(cid_list[0])


# ──────────────────────────────────────────────────────────────────────────────
# Display Formatting
# ──────────────────────────────────────────────────────────────────────────────

def format_compound_info(result: Dict[str, Any]) -> str:
    """Format compound data into a human-readable string."""
    if result.get("error"):
        return f"PubChem error: {result['error']}"

    lines = []
    cid = result.get("cid", "")
    name = result.get("iupac_name", result.get("name", f"CID {cid}"))
    lines.append(f"  Name: {name}")
    lines.append(f"  CID: {cid}")
    lines.append(f"  URL: https://pubchem.ncbi.nlm.nih.gov/compound/{cid}")

    formula = result.get("formula", "")
    if formula:
        lines.append(f"  Formula: {formula}")

    mw = result.get("molecular_weight")
    if mw is not None:
        lines.append(f"  Molecular Weight: {mw:.4f}")

    smiles = result.get("smiles", "")
    if smiles:
        lines.append(f"  SMILES: {smiles}")

    inchi = result.get("inchi", "")
    if inchi:
        lines.append(f"  InChI: {inchi}")

    logp = result.get("logp")
    if logp is not None:
        lines.append(f"  LogP (XLogP): {logp:.2f}")

    synonyms = result.get("synonyms", [])
    if synonyms:
        syn_str = ", ".join(synonyms[:5])
        lines.append(f"  Synonyms: {syn_str}")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Fact Storage
# ──────────────────────────────────────────────────────────────────────────────

def store_compound_fact(result: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Store compound data as a Molecule fact in the fact store.

    Args:
        result: Compound data dict from search_pubchem or fetch_compound_properties.
        tenant_id: Optional tenant ID for multi-tenant path resolution.

    Returns:
        dict with status and path from append_enriched_fact.
    """
    from weslr.fact_extractor import append_enriched_fact

    if result.get("error"):
        return {"status": "error", "error": result["error"]}

    fact: Dict[str, Any] = {
        "predicate": "has_molecular_property",
        "subject": result.get("name") or result.get("iupac_name", f"CID_{result.get('cid', 'unknown')}"),
        "object": result.get("formula", ""),
        "confidence": 0.95,
        "source_type": "pubchem",
        "domain": "chemistry",
        "source_reference": {
            "pubchem_cid": result.get("cid"),
            "url": result.get("url"),
        },
    }

    if result.get("molecular_weight"):
        fact["molecular_weight"] = result["molecular_weight"]
    if result.get("smiles"):
        fact["smiles"] = result["smiles"]
    if result.get("logp") is not None:
        fact["logp"] = result["logp"]
    if result.get("inchi"):
        fact["inchi"] = result["inchi"]
    if result.get("inchi_key"):
        fact["inchi_key"] = result["inchi_key"]

    return append_enriched_fact(fact, tenant_id=tenant_id)