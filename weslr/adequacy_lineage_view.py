from __future__ import annotations
from typing import Dict, Any, Optional


def build_proposal_view(proposal_id: str, *, lineage_ref: Optional[Dict[str, Any]] = None, adequacy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compose a proposal view entry with optional lineage and adequacy references."""
    entry = {"proposal_id": proposal_id}
    if lineage_ref:
        entry["proposal_lineage"] = lineage_ref
    if adequacy:
        entry["adequacy"] = adequacy
    return entry
