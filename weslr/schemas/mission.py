"""
WESLR Mission Schema

Defines the Mission dataclass and JSON schema for the Research Work Loop V1.
Mission is per-tenant, stored in .weslr/missions.jsonl.

All missions must have automatic_execution=false.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
import json


# Default allowed sources for V1 (local-only)
DEFAULT_ALLOWED_SOURCES = ["local_evidence", "hypothesis_repository"]

# Default forbidden outputs (safety boundary)
DEFAULT_FORBIDDEN_OUTPUTS = [
    "hazardous_synthesis",
    "pathogen_engineering",
    "weaponization",
    "toxic_deployment",
    "covert_delivery",
    "evasion_misuse_optimization",
    "dangerous_procurement",
]

# Default safety constraints
DEFAULT_SAFETY_CONSTRAINTS = [
    "no_autonomous_lab",
    "no_procurement_guidance",
    "uncertainty_label_required",
]

# Valid mission statuses
VALID_STATUSES = ["draft", "active", "paused", "closed"]

# Valid domain tags
VALID_DOMAIN_TAGS = ["material", "biology", "chemistry", "physics", "engineering", "medicine"]


@dataclass
class Mission:
    """
    Research Work Loop mission.

    Attributes:
        mission_id: UUID v5 from tenant_id:title:timestamp_hour (deterministic)
        owner_user_id: User who owns this mission
        tenant_id: Tenant namespace (consistent with HypothesisRepository)
        title: Short human-readable title
        research_goal: What the mission aims to achieve
        domain_tags: List of domain tags (material, biology, chemistry, physics, etc.)
        allowed_sources: List of allowed source adapters
        forbidden_outputs: List of forbidden output categories
        safety_constraints: List of safety constraint flags
        cadence_minutes: How often to run (V1 = not used, manual only)
        current_questions: Open questions the mission is investigating
        hypotheses: Hypothesis IDs or inline hypothesis descriptions
        evidence_links: File paths or URLs providing evidence
        candidate_suggestions: Candidate next-action suggestions
        status: draft | active | paused | closed
        automatic_execution: Must be False — no auto-execution
        operator_visible: Operator can see this mission
        public_user_visible: Public user can see this mission
        created_at: ISO-8601 creation timestamp
        last_reviewed_at: ISO-8601 last review timestamp
        next_run_at: ISO-8601 next planned run (V1 = not used)
        mission_note: Free-text note for operator context
    """

    mission_id: str
    owner_user_id: str
    tenant_id: str
    title: str
    research_goal: str
    domain_tags: list[str]
    allowed_sources: list[str]
    forbidden_outputs: list[str]
    safety_constraints: list[str]
    cadence_minutes: int
    current_questions: list[str]
    hypotheses: list[str]
    evidence_links: list[str]
    candidate_suggestions: list[str]
    status: str
    automatic_execution: bool
    operator_visible: bool
    public_user_visible: bool
    created_at: str
    last_reviewed_at: str
    next_run_at: str
    mission_note: str

    def __post_init__(self):
        if self.automatic_execution:
            raise ValueError("automatic_execution must be False")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Mission":
        # Validate required fields
        required = [
            "mission_id", "owner_user_id", "tenant_id", "title", "research_goal",
            "domain_tags", "allowed_sources", "forbidden_outputs", "safety_constraints",
            "cadence_minutes", "current_questions", "hypotheses", "evidence_links",
            "candidate_suggestions", "status", "automatic_execution", "operator_visible",
            "public_user_visible", "created_at", "last_reviewed_at", "next_run_at",
            "mission_note",
        ]
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        return cls(**data)

    @classmethod
    def from_json(cls, text: str) -> "Mission":
        return cls.from_dict(json.loads(text))

    def is_active(self) -> bool:
        return self.status == "active"

    def is_paused(self) -> bool:
        return self.status == "paused"

    def is_closed(self) -> bool:
        return self.status == "closed"

    def is_draft(self) -> bool:
        return self.status == "draft"

    def update_status(self, new_status: str) -> "Mission":
        if new_status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        self.status = new_status
        return self


def generate_mission_id(tenant_id: str, title: str, timestamp_hour: str) -> str:
    """
    Generate deterministic mission ID via UUID v5.

    Args:
        tenant_id: Tenant identifier
        title: Mission title
        timestamp_hour: YYYY-MM-DD-HH format (hour-level granularity)

    Returns:
        UUID v5 string
    """
    import hashlib
    import uuid

    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace
    name = f"{tenant_id}:{title}:{timestamp_hour}"
    return str(uuid.uuid5(namespace, name))


def make_mission(
    tenant_id: str,
    owner_user_id: str,
    title: str,
    research_goal: str,
    domain_tags: Optional[list[str]] = None,
    mission_note: str = "",
) -> Mission:
    """
    Factory function to create a new Mission with sensible V1 defaults.

    Args:
        tenant_id: Tenant identifier
        owner_user_id: User who owns the mission
        title: Short human-readable title
        research_goal: What the mission aims to achieve
        domain_tags: List of domain tags (default: empty list)
        mission_note: Free-text note (default: empty string)

    Returns:
        New Mission with status='draft' and all safety defaults set
    """
    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    timestamp_hour = now.strftime("%Y-%m-%d-%H")
    mission_id = generate_mission_id(tenant_id, title, timestamp_hour)

    return Mission(
        mission_id=mission_id,
        owner_user_id=owner_user_id,
        tenant_id=tenant_id,
        title=title,
        research_goal=research_goal,
        domain_tags=domain_tags or [],
        allowed_sources=DEFAULT_ALLOWED_SOURCES.copy(),
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS.copy(),
        safety_constraints=DEFAULT_SAFETY_CONSTRAINTS.copy(),
        cadence_minutes=0,  # V1: manual only
        current_questions=[],
        hypotheses=[],
        evidence_links=[],
        candidate_suggestions=[],
        status="draft",
        automatic_execution=False,  # Always false — no auto-execution
        operator_visible=True,
        public_user_visible=False,
        created_at=created_at,
        last_reviewed_at=created_at,
        next_run_at="",
        mission_note=mission_note,
    )


# JSON schema for validation (exported as dict)
MISSION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "WESLR Mission",
    "type": "object",
    "required": [
        "mission_id", "owner_user_id", "tenant_id", "title", "research_goal",
        "domain_tags", "allowed_sources", "forbidden_outputs", "safety_constraints",
        "cadence_minutes", "current_questions", "hypotheses", "evidence_links",
        "candidate_suggestions", "status", "automatic_execution", "operator_visible",
        "public_user_visible", "created_at", "last_reviewed_at", "next_run_at",
        "mission_note",
    ],
    "properties": {
        "mission_id": {"type": "string"},
        "owner_user_id": {"type": "string"},
        "tenant_id": {"type": "string"},
        "title": {"type": "string"},
        "research_goal": {"type": "string"},
        "domain_tags": {"type": "array", "items": {"type": "string"}},
        "allowed_sources": {"type": "array", "items": {"type": "string"}},
        "forbidden_outputs": {"type": "array", "items": {"type": "string"}},
        "safety_constraints": {"type": "array", "items": {"type": "string"}},
        "cadence_minutes": {"type": "integer", "minimum": 0},
        "current_questions": {"type": "array", "items": {"type": "string"}},
        "hypotheses": {"type": "array", "items": {"type": "string"}},
        "evidence_links": {"type": "array", "items": {"type": "string"}},
        "candidate_suggestions": {"type": "array", "items": {"type": "string"}},
        "status": {"type": "string", "enum": VALID_STATUSES},
        "automatic_execution": {"type": "boolean", "enum": [False]},
        "operator_visible": {"type": "boolean"},
        "public_user_visible": {"type": "boolean"},
        "created_at": {"type": "string"},
        "last_reviewed_at": {"type": "string"},
        "next_run_at": {"type": "string"},
        "mission_note": {"type": "string"},
    },
}