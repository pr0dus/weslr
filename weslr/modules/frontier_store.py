"""
WESLR Frontier Proposal Store V1

Persistent JSONL-backed store for frontier proposals.
Per-tenant: each tenant has their own .weslr/<tenant>/frontier_proposals.jsonl
file. Status lifecycle: new → under_review → refining → experiment_planned → completed | discarded

Uses deterministic UUID v5 derived from tenant + formula + date-hour.
"""

from __future__ import annotations
import json
import os
import uuid as uuid_lib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from weslr.modules.frontier_proposer import FrontierProposal
from weslr.tenant_context import get_current_tenant, resolve_path

STORE_FILENAME = "frontier_proposals.jsonl"


def _store_path(tenant_id: Optional[str] = None) -> Path:
    tid = tenant_id or get_current_tenant() or "default"
    # Ensure .weslr dir exists for this tenant
    dir_path = resolve_path(".weslr", tid)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / STORE_FILENAME


def _make_proposal_id(tenant_id: str, formula: str, created_at: datetime) -> str:
    """Deterministic UUID v5: same inputs always produce the same ID."""
    hour = created_at.replace(minute=0, second=0, microsecond=0)
    ns = uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, f"weslr:{tenant_id}:{hour.isoformat()}")
    return str(uuid_lib.uuid5(ns, formula))


def _proposal_to_dict(p: FrontierProposal, tenant_id: str) -> dict:
    return {
        "tenant_id": tenant_id,
        "proposal_id": p.id,
        "status": getattr(p, "status", "new"),
        "retry_count": getattr(p, "retry_count", 0),
        "last_novelty_check": getattr(p, "last_novelty_check", None),
        "mission_id": getattr(p, "mission_id", None),
        "created_at": p.created_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "data": {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "domain": p.domain,
            "novelty_score": p.novelty_score,
            "feasibility_score": p.feasibility_score,
            "risk_score": p.risk_score,
            "impact_score": p.impact_score,
            "difficulty_level": p.difficulty_level,
            "proposed_experiment_summary": p.proposed_experiment_summary,
            "literature_check": p.literature_check,
            "provenance": p.provenance,
            "created_at": p.created_at,
            "strangeness_score": getattr(p, "strangeness_score", 0.0),
            "breakthrough_potential": getattr(p, "breakthrough_potential", 0.0),
            "toxic_elements": getattr(p, "toxic_elements", []),
            "dual_use": getattr(p, "dual_use", False),
        }
    }


def _dict_to_proposal(record: dict) -> FrontierProposal:
    """Reconstitute a FrontierProposal from a store record."""
    d = record["data"]
    # Handle missing fields gracefully
    return FrontierProposal(
        id=d["id"],
        title=d["title"],
        description=d["description"],
        domain=d["domain"],
        novelty_score=d["novelty_score"],
        feasibility_score=d["feasibility_score"],
        risk_score=d["risk_score"],
        impact_score=d["impact_score"],
        difficulty_level=d["difficulty_level"],
        proposed_experiment_summary=d["proposed_experiment_summary"],
        literature_check=d["literature_check"],
        provenance=d["provenance"],
        created_at=d["created_at"],
        strangeness_score=d.get("strangeness_score", 0.0),
        breakthrough_potential=d.get("breakthrough_potential", 0.0),
        toxic_elements=d.get("toxic_elements", []),
        dual_use=d.get("dual_use", False),
        status=record.get("status", "new"),
        retry_count=record.get("retry_count", 0),
        last_novelty_check=record.get("last_novelty_check"),
        mission_id=record.get("mission_id"),
    )


class FrontierProposalStore:
    """Per-tenant persistent frontier proposal store."""

    def __init__(self, tenant_id: Optional[str] = None):
        self._tenant_id = tenant_id or get_current_tenant() or "default"
        self._path = _store_path(self._tenant_id)
        self._write_lock = __import__("threading").Lock()

    def add(self, proposal: FrontierProposal) -> str:
        """Store a proposal. Returns the proposal_id."""
        proposal_id = _make_proposal_id(self._tenant_id, proposal.title, datetime.now(timezone.utc))
        proposal.id = proposal_id
        record = _proposal_to_dict(proposal, self._tenant_id)
        record["proposal_id"] = proposal_id
        with self._write_lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return proposal_id

    def get(self, proposal_id: str) -> Optional[FrontierProposal]:
        """Retrieve a proposal by ID."""
        if not self._path.exists():
            return None
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("proposal_id") == proposal_id:
                        return _dict_to_proposal(rec)
                except json.JSONDecodeError:
                    continue
        return None

    def list(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all proposals, optionally filtered by status.

        Returns list of dict summaries (not full proposals).
        """
        if not self._path.exists():
            return []
        results = []
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if status_filter and rec.get("status") != status_filter:
                        continue
                    results.append({
                        "proposal_id": rec["proposal_id"],
                        "title": rec["data"]["title"],
                        "domain": rec["data"]["domain"],
                        "status": rec.get("status", "new"),
                        "breakthrough_potential": rec["data"].get("breakthrough_potential", 0.0),
                        "strangeness_score": rec["data"].get("strangeness_score", 0.0),
                        "novelty_score": rec["data"]["novelty_score"],
                        "created_at": rec["created_at"],
                    })
                except (json.JSONDecodeError, KeyError):
                    continue
        results.sort(key=lambda x: x.get("breakthrough_potential", 0), reverse=True)
        return results

    def update_status(self, proposal_id: str, new_status: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update the status of a proposal. Returns True if found and updated."""
        if not self._path.exists():
            return False
        records = []
        found = False
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("proposal_id") == proposal_id:
                        rec["status"] = new_status
                        rec["updated_at"] = datetime.now(timezone.utc).isoformat()
                        if metadata:
                            rec["metadata"] = metadata
                        found = True
                    records.append(rec)
                except json.JSONDecodeError:
                    records.append(line)

        if not found:
            return False

        with self._write_lock:
            with open(self._path, "w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True

    def count(self, status_filter: Optional[str] = None) -> int:
        """Count proposals, optionally filtered by status."""
        return len(self.list(status_filter=status_filter))
