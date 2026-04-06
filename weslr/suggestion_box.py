# suggestion_box.py - Weslr Capability Slice: Suggestion / Request Intake Layer
# Intended for institutions, universities, labs, companies, and individuals to submit capability requests.
# Additive only, reversible (single file removal + storage revert), continuity compatible.

from pathlib import Path
import json
import uuid
from datetime import datetime
from typing import Optional, Literal, Union
from dataclasses import dataclass, asdict


# Self-Architecture Core v6: Scenario comparison entry point
from .scenario_model import (
    Scenario,
    ScenarioProposal,
    RoadmapTradeoffEngine,
    create_scenario,
    create_quick_win_scenario,
    create_strategic_scenario,
)


RequesterType = Literal["individual", "university", "laboratory", "company", "institution"]
DomainType = str  # free-text scientific/technical domain
Status = Literal["submitted", "reviewed", "approved", "rejected", "implemented"]


@dataclass
class SuggestionRequest:
    category: str
    request_id: str
    timestamp: str
    requester_type: RequesterType
    domain: DomainType
    requested_capability: str
    problem_statement: str
    requester_id: Optional[str] = None
    contact_email: Optional[str] = None
    additional_notes: Optional[str] = None
    status: Status = "submitted"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


VALID_REQUESTER_TYPES: set[str] = {
    "individual",
    "university",
    "laboratory",
    "company",
    "institution",
}

VALID_STATUSES: set[str] = {
    "submitted",
    "reviewed",
    "approved",
    "rejected",
    "implemented",
}

DEFAULT_CATEGORY = "suggestion_request"


class SuggestionBox:
    def __init__(
        self,
        storage_path: Optional[Union[str, Path]] = None,
        continuity_path: Optional[Union[str, Path]] = None,
    ):
        # Default storage location
        self.storage_path = Path(storage_path or "continuity/suggestion_box/requests.json")
        self.continuity_path = Path(continuity_path or "continuity/suggestion_box/continuity.json")

        # Ensure storage directories exist
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.continuity_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing requests or initialize empty list
        self.requests: list[dict] = []
        self._load_requests()

    def _load_requests(self) -> None:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.requests = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.requests = []

    def _save_requests(self) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.requests, f, indent=2)

    def _generate_request_id(self) -> str:
        return f"req-{uuid.uuid4().hex[:6]}"

    def submit_request(self, request_data: dict) -> SuggestionRequest:
        """Accept a structured request entry and store it."""
        # Validate requester type
        requester_type = request_data.get("requester_type")
        if requester_type not in VALID_REQUESTER_TYPES:
            raise ValueError(
                f"Invalid requester_type '{requester_type}'. "
                f"Must be one of: {sorted(VALID_REQUESTER_TYPES)}"
            )

        # Validate domain is present
        domain = request_data.get("domain")
        if not domain:
            raise ValueError("domain is required")

        # Validate required fields
        required_fields = ["requested_capability", "problem_statement"]
        missing = [f for f in required_fields if f not in request_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Build request object
        request_id = self._generate_request_id()
        timestamp = datetime.utcnow().isoformat() + "Z"

        req = SuggestionRequest(
            category=DEFAULT_CATEGORY,
            request_id=request_id,
            timestamp=timestamp,
            requester_type=requester_type,
            domain=domain,
            requested_capability=request_data["requested_capability"],
            problem_statement=request_data["problem_statement"],
            requester_id=request_data.get("requester_id"),
            contact_email=request_data.get("contact_email"),
            additional_notes=request_data.get("additional_notes"),
        )

        # Persist
        self.requests.append(req.to_dict())
        self._save_requests()

        # Update continuity
        self._update_continuity("submitted", request_id, requester_type, domain)

        return req

    def list_requests(
        self,
        domain: Optional[str] = None,
        requester_type: Optional[str] = None,
    ) -> list[dict]:
        """List requests, optionally filtered by domain and/or requester_type."""
        results = self.requests

        if domain:
            results = [r for r in results if r.get("domain", "").lower() == domain.lower()]

        if requester_type:
            results = [r for r in results if r.get("requester_type") == requester_type]

        return results

    def summarize_requests(self) -> dict:
        """Generate a summary of all requests."""
        total = len(self.requests)
        by_status: dict[str, int] = {}
        by_domain: dict[str, int] = {}
        by_requester: dict[str, int] = {}

        for req in self.requests:
            status = req.get("status", "submitted")
            by_status[status] = by_status.get(status, 0) + 1

            domain = req.get("domain", "unknown")
            by_domain[domain] = by_domain.get(domain, 0) + 1

            rtype = req.get("requester_type", "unknown")
            by_requester[rtype] = by_requester.get(rtype, 0) + 1

        return {
            "total_requests": total,
            "by_status": by_status,
            "by_domain": by_domain,
            "by_requester_type": by_requester,
        }

    def _update_continuity(self, action: str, request_id: str, requester_type: str, domain: str) -> None:
        """Update continuity log for audit/reversibility."""
        continuity = {}
        if self.continuity_path.exists():
            try:
                with open(self.continuity_path, "r", encoding="utf-8") as f:
                    continuity = json.load(f)
            except (json.JSONDecodeError, IOError):
                continuity = {}

        continuity.setdefault("actions", []).append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "request_id": request_id,
            "requester_type": requester_type,
            "domain": domain,
        })

        with open(self.continuity_path, "w", encoding="utf-8") as f:
            json.dump(continuity, f, indent=2)

    def rollback(self) -> bool:
        """Remove the last submitted request (simple rollback)."""
        if not self.requests:
            return False

        # Remove last entry
        self.requests.pop()
        self._save_requests()

        # Remove last continuity entry
        continuity = {}
        if self.continuity_path.exists():
            try:
                with open(self.continuity_path, "r", encoding="utf-8") as f:
                    continuity = json.load(f)
            except (json.JSONDecodeError, IOError):
                continuity = {}

        if continuity.get("actions"):
            continuity["actions"].pop()
            with open(self.continuity_path, "w", encoding="utf-8") as f:
                json.dump(continuity, f, indent=2)

        return True


# Convenience function for CLI usage
def submit_suggestion(
    requester_type: RequesterType,
    domain: str,
    requested_capability: str,
    problem_statement: str,
    requester_id: Optional[str] = None,
    contact_email: Optional[str] = None,
    additional_notes: Optional[str] = None,
) -> dict:
    """Quick submit via CLI/function call."""
    box = SuggestionBox()
    req = box.submit_request({
        "requester_type": requester_type,
        "domain": domain,
        "requested_capability": requested_capability,
        "problem_statement": problem_statement,
        "requester_id": requester_id,
        "contact_email": contact_email,
        "additional_notes": additional_notes,
    })
    return req.to_dict()


if __name__ == "__main__":
    # Example usage / CLI
    import sys
    import json

    if len(sys.argv) < 3:
        print("Usage: python suggestion_box.py <command> [args]")
        print("Commands:")
        print("  submit <type> <domain> <capability> <problem>")
        print("  list [--domain <d>] [--type <t>]")
        print("  summarize")
        print("  scenario-compare <a_json> <b_json>  # Compare two roadmap scenarios")
        sys.exit(1)

    command = sys.argv[1]
    box = SuggestionBox()

    if command == "submit":
        if len(sys.argv) < 6:
            print("Usage: submit <type> <domain> <capability> <problem>")
            sys.exit(1)
        req = box.submit_request({
            "requester_type": sys.argv[2],
            "domain": sys.argv[3],
            "requested_capability": sys.argv[4],
            "problem_statement": sys.argv[5],
        })
        print(req.to_json())

    elif command == "list":
        domain = None
        rtype = None
        args = sys.argv[2:]
        while args:
            if args[0] == "--domain" and len(args) > 1:
                domain = args[1]
                args = args[2:]
            elif args[0] == "--type" and len(args) > 1:
                rtype = args[1]
                args = args[2:]
            else:
                args = args[1:]

        results = box.list_requests(domain=domain, requester_type=rtype)
        print(json.dumps(results, indent=2))

    elif command == "summarize":
        summary = box.summarize_requests()
        print(json.dumps(summary, indent=2))

    elif command == "scenario-compare":
        # Compare two roadmap scenarios
        if len(sys.argv) < 4:
            print("Usage: scenario-compare <scenario_a_json> <scenario_b_json>")
            sys.exit(1)
        try:
            with open(sys.argv[2], "r") as f:
                data_a = json.load(f)
            with open(sys.argv[3], "r") as f:
                data_b = json.load(f)
            
            scenario_a = Scenario.from_dict(data_a)
            scenario_b = Scenario.from_dict(data_b)
            
            result = RoadmapTradeoffEngine.compare_scenarios(scenario_a, scenario_b)
            print(json.dumps(result.to_dict(), indent=2))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
