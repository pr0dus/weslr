"""Weslr Launch Log (v1.0)

Audit log for launch gate decisions.
Tracks all evaluation attempts and decisions.

FORMAT:
{
  "timestamp": "ISO-8601",
  "decision": "GO_PUBLIC_TEST" | "GO_LIMITED_OPERATOR_PILOT" | "NO_GO_REMEDIATION_REQUIRED",
  "readiness_score": float,
  "evaluated_by": "operator:email",
  "categories": {...},
  "blocking_issues": [...],
  "comments": "...",
  "reviewed_by": [...],
  "approved_by": "operator:email"
}

This log is operator-only and must not be exposed to public or untrusted contexts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import filelock


__all__ = ["LaunchLog"]


class LaunchLog:
    """Audit log for Weslr launch decisions.
    
    Operator-only functionality. Not exposed to public or untrusted contexts.
    """

    def __init__(self, log_dir: str = "weslr/logs/launch"):
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "launch_log.json"
        self.lock_file = self.log_dir / "launch_log.lock"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        decision: str,
        readiness_score: float,
        evaluated_by: str,
        categories: Dict[str, Any],
        blocking_issues: List[str],
        comments: str = "",
        reviewed_by: List[str] = None,
        approved_by: str = None,
    ) -> Dict[str, Any]:
        """Log a launch decision.

        Args:
            decision: GO_PUBLIC_TEST, GO_LIMITED_OPERATOR_PILOT, or NO_GO_REMEDIATION_REQUIRED
            readiness_score: Readiness score (0-100)
            evaluated_by: Operator ID (e.g., "operator:alice@example.com")
            categories: Category scores
            blocking_issues: List of blocking issues
            comments: Optional comments
            reviewed_by: List of reviewers (for operator pilot)
            approved_by: Approving operator (for public test)

        Returns:
            Log entry dict
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "readiness_score": readiness_score,
            "evaluated_by": evaluated_by,
            "categories": categories,
            "blocking_issues": blocking_issues,
            "comments": comments,
            "reviewed_by": reviewed_by or [],
            "approved_by": approved_by,
        }

        # Acquire lock and write
        lock = filelock.FileLock(str(self.lock_file))
        with lock:
            # Load existing log
            if self.log_file.exists():
                with open(self.log_file) as f:
                    log = json.load(f)
            else:
                log = {"entries": [], "metadata": {"version": "1.0"}}

            # Add entry
            entry_id = len(log["entries"]) + 1
            entry["id"] = entry_id
            log["entries"].append(entry)

            # Write back
            with open(self.log_file, "w") as f:
                json.dump(log, f, indent=2)

        return entry

    def get_entries(
        self,
        limit: int = 100,
        decision: str = None,
        after: str = None,
    ) -> List[Dict[str, Any]]:
        """Get launch log entries.

        Args:
            limit: Maximum entries to return
            decision: Filter by decision type
            after: Filter entries after timestamp (ISO-8601)

        Returns:
            List of log entries
        """
        if not self.log_file.exists():
            return []

        with open(self.log_file) as f:
            log = json.load(f)

        entries = log.get("entries", [])

        # Apply filters
        if decision:
            entries = [e for e in entries if e.get("decision") == decision]

        if after:
            entries = [
                e for e in entries
                if e.get("timestamp", "") > after
            ]

        # Sort by timestamp descending and limit
        entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return entries[:limit]

    def get_latest(self) -> Optional[Dict[str, Any]]:
        """Get the most recent launch decision.

        Returns:
            Latest log entry or None if no entries
        """
        entries = self.get_entries(limit=1)
        return entries[0] if entries else None

    def get_statistics(self) -> Dict[str, Any]:
        """Get launch statistics.

        Returns:
            Dict with decision counts and trends
        """
        entries = self.get_entries()

        stats = {
            "total_evaluations": len(entries),
            "by_decision": {},
            "average_readiness": 0.0,
            "latest_decision": None,
            "latest_score": 0.0,
        }

        if not entries:
            return stats

        # Count by decision
        for entry in entries:
            decision = entry.get("decision", "unknown")
            stats["by_decision"][decision] = stats["by_decision"].get(decision, 0) + 1

        # Average readiness
        scores = [e.get("readiness_score", 0) for e in entries]
        if scores:
            stats["average_readiness"] = round(sum(scores) / len(scores), 1)

        # Latest
        latest = entries[0]
        stats["latest_decision"] = latest.get("decision")
        stats["latest_score"] = latest.get("readiness_score", 0)

        return stats


def main():
    """CLI interface for launch log."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Weslr Launch Log - Audit Log for Decisions"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List recent entries"
    )
    parser.add_argument(
        "--limit", "-n", type=int, default=10, help="Number of entries to list"
    )
    parser.add_argument(
        "--stats", "-s", action="store_true", help="Show statistics"
    )
    parser.add_argument(
        "--latest", action="store_true", help="Show latest entry"
    )

    args = parser.parse_args()

    log = LaunchLog()

    if args.stats:
        stats = log.get_statistics()
        print(json.dumps(stats, indent=2))
    elif args.latest:
        entry = log.get_latest()
        if entry:
            print(json.dumps(entry, indent=2))
        else:
            print("No launch decisions logged yet.")
    elif args.list:
        entries = log.get_entries(limit=args.limit)
        print(json.dumps(entries, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
