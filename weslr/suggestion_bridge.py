# suggestion_bridge.py - Weslr Capability Slice: Suggestion-to-Proposal Bridge
# Converts external suggestion requests into proposal candidates for operator review.
# Additive only, reversible, continuity-compatible.
# Does NOT auto-approve or auto-implement anything.

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .suggestion_box import SuggestionBox, RequesterType, DomainType


# ============================================================================
# PATHS & CONSTANTS
# ============================================================================

# Review queue path (matches sim.py config)
REVIEW_QUEUE_PATH = Path(__file__).resolve().parent.parent / "review_queue.json"

# Suggestion storage path (matches suggestion_box.py)
SUGGESTION_STORAGE = Path(__file__).resolve().parent.parent / "continuity" / "suggestion_box" / "requests.json"

# Public visibility protections (operator must explicitly enable export)
DEFAULT_PROTECTED = True
DEFAULT_VISIBILITY = "internal"


# ============================================================================
# BRIDGE LAYER
# ============================================================================

class SuggestionBridge:
    """Bridge from external suggestions to internal proposal candidates."""

    def __init__(
        self,
        review_queue_path: Optional[Path] = None,
        suggestion_storage_path: Optional[Path] = None,
    ):
        self.review_queue_path = review_queue_path or REVIEW_QUEUE_PATH
        self.suggestion_storage_path = suggestion_storage_path or SUGGESTION_STORAGE
        self.suggestion_box = SuggestionBox(
            storage_path=self.suggestion_storage_path,
            continuity_path=self.suggestion_storage_path.parent / "continuity.json",
        )

    # --------------------------------------------------------------------------
    # CORE OPERATIONS
    # --------------------------------------------------------------------------

    def list_suggestions(self, domain: Optional[str] = None, requester_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List suggestion requests, optionally filtered."""
        return self.suggestion_box.list_requests(domain=domain, requester_type=requester_type)

    def list_proposal_candidates(self) -> List[Dict[str, Any]]:
        """List existing proposal candidates in review queue."""
        if not self.review_queue_path.exists():
            return []
        try:
            with open(self.review_queue_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def convert_to_proposal_candidate(
        self,
        request_id: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convert a suggestion request into a proposal candidate.

        Args:
            request_id: The request ID from suggestion_box
            title: Optional custom title (defaults to "Suggestion: [capability]")
            summary: Optional custom summary (defaults to combined problem + capability)

        Returns:
            Proposal candidate dict compatible with review_queue format
        """
        # Find the request
        all_requests = self.suggestion_box.list_requests()
        request = None
        for r in all_requests:
            if r.get("request_id") == request_id:
                request = r
                break

        if request is None:
            raise ValueError(f"Request not found: {request_id}")

        # Build candidate
        if title is None:
            title = f"Suggestion: {request.get('requested_capability', 'Unknown capability')}"

        if summary is None:
            summary = (
                f"Domain: {request.get('domain', 'unknown')}\\n"
                f"Requester: {request.get('requester_type', 'unknown')}\\n"
                f"Problem: {request.get('problem_statement', 'No problem statement')}\\n"
                f"Capability: {request.get('requested_capability', 'Unknown capability')}"
            )

        candidate_id = f"ext-{uuid.uuid4().hex[:6]}"

        # Build proposal candidate in review_queue format
        candidate = {
            "id": candidate_id,
            "title": title,
            "summary": summary,
            "artifact_type": "proposal_candidate",
            "lifecycle_stage": "proposed",
            "category": "external_request",
            "path": f"suggestion_bridge/{request_id}",
            "review_status": "proposed",
            "review_notes": [
                {
                    "at": datetime.utcnow().isoformat() + "Z",
                    "by": "suggestion_bridge",
                    "action": "converted_from_suggestion",
                    "details": f"request_id={request_id}",
                }
            ],
            "sellability_score": 0.0,  # Pending operator assessment
            "human_proposed_score": 0.0,  # Pending operator assessment
            "commercial_readiness_score": 0.0,  # Pending operator assessment
            "price_band_guess": None,
            "delivery_mode": "tbd",
            "approved_for_export": False,  # Default protected
            "export_path": None,
            "public_visibility": DEFAULT_VISIBILITY,
            "source": {
                "type": "external_request",
                "subtype": "weslr_suggestion",
                "request_id": request_id,
                "original_data": {
                    "requester_type": request.get("requester_type"),
                    "domain": request.get("domain"),
                    "requested_capability": request.get("requested_capability"),
                    "problem_statement": request.get("problem_statement"),
                    "requester_id": request.get("requester_id"),
                    "contact_email": request.get("contact_email"),
                    "additional_notes": request.get("additional_notes"),
                },
            },
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }

        return candidate

    def add_proposal_candidate(
        self,
        request_id: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convert request and add to review queue.

        Does NOT auto-approve. Operator must explicitly approve via review workflow.

        Returns the added candidate.
        """
        candidate = self.convert_to_proposal_candidate(request_id, title, summary)

        # Load existing review queue
        review_queue = self.list_proposal_candidates()

        # Add candidate (append-only, additive)
        review_queue.append(candidate)

        # Save review queue
        self.review_queue_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.review_queue_path, "w", encoding="utf-8") as f:
            json.dump(review_queue, f, indent=2)

        return candidate

    def remove_proposal_candidate(self, candidate_id: str) -> bool:
        """Remove a proposal candidate from review queue (for operator cleanup)."""
        review_queue = self.list_proposal_candidates()
        original_len = len(review_queue)
        review_queue = [r for r in review_queue if r.get("id") != candidate_id]

        if len(review_queue) == original_len:
            return False

        # Save updated queue
        with open(self.review_queue_path, "w", encoding="utf-8") as f:
            json.dump(review_queue, f, indent=2)

        return True

    def mark_as_reviewed(self, candidate_id: str, status: str, notes: str = "") -> bool:
        """Mark a proposal candidate as reviewed by operator.

        Args:
            candidate_id: The candidate ID
            status: One of 'approved', 'rejected', 'needs_revision'
            notes: Optional operator notes

        Returns:
            True if updated, False if not found
        """
        review_queue = self.list_proposal_candidates()

        for item in review_queue:
            if item.get("id") == candidate_id:
                item["review_status"] = status
                item["review_notes"].append({
                    "at": datetime.utcnow().isoformat() + "Z",
                    "by": "operator",
                    "action": "review_update",
                    "details": notes,
                })
                item["updated_at"] = datetime.utcnow().isoformat() + "Z"

                # Save
                with open(self.review_queue_path, "w", encoding="utf-8") as f:
                    json.dump(review_queue, f, indent=2)

                return True

        return False

    # --------------------------------------------------------------------------
    # UTILITY METHODS
    # --------------------------------------------------------------------------

    def summarize_suggestions(self) -> Dict[str, Any]:
        """Generate summary of all suggestions."""
        return self.suggestion_box.summarize_requests()

    def summary(self) -> Dict[str, Any]:
        """Generate bridge summary (suggestions + candidates)."""
        suggestions = self.suggestion_box.summarize_requests()
        candidates = self.list_proposal_candidates()

        return {
            "total_suggestions": suggestions.get("total_requests", 0),
            "by_requester_type": suggestions.get("by_requester_type", {}),
            "by_domain": suggestions.get("by_domain", {}),
            "total_candidates": len(candidates),
            "by_status": {},
            "candidates": candidates,
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def bridge_suggestion_to_proposal(
    request_id: str,
    title: Optional[str] = None,
    summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Quick bridge from suggestion to proposal candidate."""
    bridge = SuggestionBridge()
    return bridge.add_proposal_candidate(request_id, title, summary)


def list_candidates() -> List[Dict[str, Any]]:
    """List all proposal candidates from bridge."""
    bridge = SuggestionBridge()
    return bridge.list_proposal_candidates()


def list_suggestions() -> List[Dict[str, Any]]:
    """List all suggestion requests."""
    bridge = SuggestionBridge()
    return bridge.list_suggestions()


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python suggestion_bridge.py <command> [args]")
        print("Commands:")
        print("  list_suggestions")
        print("  list_candidates")
        print("  bridge <request_id> [title] [summary]")
        print("  approve <candidate_id> [notes]")
        print("  reject <candidate_id> [notes]")
        print("  cleanup <candidate_id>")
        print("  summary")
        sys.exit(1)

    command = sys.argv[1]
    bridge = SuggestionBridge()

    if command == "list_suggestions":
        suggestions = bridge.list_suggestions()
        print(json.dumps(suggestions, indent=2))

    elif command == "list_candidates":
        candidates = bridge.list_proposal_candidates()
        print(json.dumps(candidates, indent=2))

    elif command == "bridge":
        if len(sys.argv) < 3:
            print("Usage: bridge <request_id> [title] [summary]")
            sys.exit(1)
        request_id = sys.argv[2]
        title = sys.argv[3] if len(sys.argv) > 3 else None
        summary = sys.argv[4] if len(sys.argv) > 4 else None
        candidate = bridge.add_proposal_candidate(request_id, title, summary)
        print(json.dumps(candidate, indent=2))

    elif command == "summary":
        summary = bridge.summary()
        print(json.dumps(summary, indent=2))

    elif command == "approve":
        if len(sys.argv) < 3:
            print("Usage: approve <candidate_id> [notes]")
            sys.exit(1)
        candidate_id = sys.argv[2]
        notes = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        success = bridge.mark_as_reviewed(candidate_id, "approved", notes)
        print(json.dumps({"ok": success, "candidate_id": candidate_id, "status": "approved" if success else "not_found"}))

    elif command == "reject":
        if len(sys.argv) < 3:
            print("Usage: reject <candidate_id> [notes]")
            sys.exit(1)
        candidate_id = sys.argv[2]
        notes = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        success = bridge.mark_as_reviewed(candidate_id, "rejected", notes)
        print(json.dumps({"ok": success, "candidate_id": candidate_id, "status": "rejected" if success else "not_found"}))

    elif command == "cleanup":
        if len(sys.argv) < 3:
            print("Usage: cleanup <candidate_id>")
            sys.exit(1)
        candidate_id = sys.argv[2]
        success = bridge.remove_proposal_candidate(candidate_id)
        print(json.dumps({"ok": success, "candidate_id": candidate_id, "removed": success}))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
