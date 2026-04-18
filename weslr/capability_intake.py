from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Capability:
    name: str
    description: str
    risk: str = "medium"  # low/medium/high
    tags: List[str] = field(default_factory=list)


def validate_capability(cap: Dict[str, Any]) -> None:
    if not cap.get("name"):
        raise ValueError("name required")
    if cap.get("risk") not in (None, "low", "medium", "high"):
        raise ValueError("invalid risk")


def ingest_capabilities(caps: List[Dict[str, Any]]) -> List[Capability]:
    validated: List[Capability] = []
    for cap in caps:
        validate_capability(cap)
        validated.append(Capability(**{**cap, "risk": cap.get("risk", "medium"), "tags": cap.get("tags", [])}))
    return validated
