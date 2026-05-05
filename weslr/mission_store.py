"""
WESLR Mission Store

Per-tenant mission repository backed by .weslr/missions.jsonl.
Provides save, list, load_active, update_status operations.

V1: JSONL append-only, per-tenant filtered at read time.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional, List

from .schemas.mission import Mission, VALID_STATUSES

# Path to mission store
MISSIONS_STORE_PATH = ".weslr/missions.jsonl"


class MissionStore:
    """
    Per-tenant mission repository.

    All missions are stored in .weslr/missions.jsonl (one JSON per line).
    Tenant isolation is enforced at read time by filtering on tenant_id.
    """

    def __init__(self, store_path: str = MISSIONS_STORE_PATH):
        self.store_path = store_path

    def _ensure_store_exists(self) -> None:
        """Ensure the store directory exists."""
        directory = os.path.dirname(self.store_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _read_all(self) -> list[dict]:
        """Read all records from the store. Returns empty list if file doesn't exist."""
        if not os.path.exists(self.store_path):
            return []
        records = []
        with open(self.store_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def _write_all(self, records: list[dict]) -> None:
        """Rewrite the entire store."""
        self._ensure_store_exists()
        with open(self.store_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

    def save(self, mission: Mission) -> None:
        """
        Save a mission to the store (append).

        Args:
            mission: Mission object to save

        Raises:
            ValueError: If mission is invalid
        """
        if mission.automatic_execution:
            raise ValueError("automatic_execution must be False")
        self._ensure_store_exists()
        with open(self.store_path, "a", encoding="utf-8") as f:
            f.write(mission.to_json() + "\n")

    def list(
        self,
        tenant_id: str,
        status: Optional[str] = None,
    ) -> list[Mission]:
        """
        List missions for a tenant, optionally filtered by status.

        Args:
            tenant_id: Tenant identifier
            status: Optional status filter (draft/active/paused/closed)

        Returns:
            List of Mission objects matching the filters

        Raises:
            ValueError: If status is not a valid status
        """
        if status is not None and status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

        records = self._read_all()
        missions = []
        for record in records:
            if record.get("tenant_id") != tenant_id:
                continue
            if status is not None and record.get("status") != status:
                continue
            missions.append(Mission.from_dict(record))
        return missions

    def load_active(self, tenant_id: str) -> list[Mission]:
        """
        Load all active missions for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of active Mission objects
        """
        return self.list(tenant_id, status="active")

    def get(self, mission_id: str, tenant_id: str) -> Optional[Mission]:
        """
        Get a specific mission by ID for a tenant.

        Args:
            mission_id: Mission identifier
            tenant_id: Tenant identifier (for isolation)

        Returns:
            Mission object or None if not found
        """
        records = self._read_all()
        for record in records:
            if record.get("mission_id") == mission_id and record.get("tenant_id") == tenant_id:
                return Mission.from_dict(record)
        return None

    def update_status(self, mission_id: str, tenant_id: str, new_status: str) -> bool:
        """
        Update the status of a mission.

        Args:
            mission_id: Mission identifier
            tenant_id: Tenant identifier (for isolation)
            new_status: New status (draft/active/paused/closed)

        Returns:
            True if updated, False if mission not found

        Raises:
            ValueError: If new_status is not valid
        """
        return self.update_mission(mission_id, tenant_id, {"status": new_status})

    def update_mission(self, mission_id: str, tenant_id: str, changes: dict) -> bool:
        """
        Update arbitrary fields on a mission.

        Args:
            mission_id: Mission identifier
            tenant_id: Tenant identifier (for isolation)
            changes: Dict of field -> new value to apply

        Returns:
            True if updated, False if mission not found

        Raises:
            ValueError: If status field is set to an invalid value
        """
        # Validate status if being changed
        if "status" in changes and changes["status"] not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

        records = self._read_all()
        updated = False
        new_records = []
        for record in records:
            if record.get("mission_id") == mission_id and record.get("tenant_id") == tenant_id:
                for field, value in changes.items():
                    record[field] = value
                record["last_reviewed_at"] = datetime.now(timezone.utc).isoformat()
                updated = True
            new_records.append(record)

        if updated:
            self._write_all(new_records)
        return updated

    def count(self, tenant_id: str, status: Optional[str] = None) -> int:
        """
        Count missions for a tenant.

        Args:
            tenant_id: Tenant identifier
            status: Optional status filter

        Returns:
            Number of matching missions
        """
        return len(self.list(tenant_id, status=status))

    def exists(self, mission_id: str, tenant_id: str) -> bool:
        """
        Check if a mission exists.

        Args:
            mission_id: Mission identifier
            tenant_id: Tenant identifier

        Returns:
            True if mission exists
        """
        return self.get(mission_id, tenant_id) is not None