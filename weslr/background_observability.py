from __future__ import annotations
from typing import Dict, Any, List, Optional


class BackgroundObservability:
    """In-memory background analysis observability surface (proposal-only, read-oriented).

    Captures loop state and recent proposals with optional lineage and adequacy references.
    No external effects; suitable for tests and operator views.
    """

    def __init__(self):
        self._loops: Dict[str, Dict[str, Any]] = {}

    def register_loop(self, loop_id: str, workspace_id: str, user_id: str, budget_cap: float) -> None:
        self._loops[loop_id] = {
            "loop_id": loop_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "status": "running",
            "budget_used": 0.0,
            "budget_cap": budget_cap,
            "proposals_recent": [],
            "paused": False,
            "stopped": False,
            "last_checkpoint": None,
            "updated_at": None,
        }

    def update_loop(self, loop_id: str, **kwargs) -> None:
        if loop_id not in self._loops:
            raise KeyError("loop not registered")
        self._loops[loop_id].update(kwargs)

    def record_proposal(
        self,
        loop_id: str,
        proposal_id: str,
        *,
        lineage_ref: Optional[Dict[str, Any]] = None,
        adequacy: Optional[Dict[str, Any]] = None,
    ) -> None:
        if loop_id not in self._loops:
            raise KeyError("loop not registered")
        entry = {"proposal_id": proposal_id}
        if lineage_ref:
            entry["proposal_lineage"] = lineage_ref
        if adequacy:
            entry["adequacy"] = adequacy
        self._loops[loop_id]["proposals_recent"].append(entry)

    def view(self) -> List[Dict[str, Any]]:
        return list(self._loops.values())
