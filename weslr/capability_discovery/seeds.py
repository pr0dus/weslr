"""Capability Discovery Radar - Seed Source Pack.

Curated list of trusted sources to seed initial capability discovery.
This provides a controlled starting point for WESLR to understand
relevant signals before live crawling begins.

Seed categories:
- Reddit communities (relevant discussions)
- GitHub repositories (tools, projects)
- Science-relevant anchors (academic/certified sources)
- Linked-knowledge / PKM anchors (existing WESLR knowledge)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class SeedKind(str, Enum):
    """Types of seed sources."""
    REDDIT_COMMUNITY = "reddit_community"
    GITHUB_REPO = "github_repo"
    SCIENCE_SOURCE = "science_source"
    PKM_ANCHOR = "pkm_anchor"
    OTHER = "other"


class SeedStatus(str, Enum):
    """Status of a seed source."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


@dataclass
class SeedSource:
    """A seed source definition for initial discovery."""
    id: str
    name: str
    kind: SeedKind
    url: Optional[str] = None
    tags: List[str] = None
    priority: int = 0
    enabled: bool = True
    description: Optional[str] = None
    category: Optional[str] = None
    last_ingested: Optional[str] = None
    created_at: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            from datetime import datetime, timezone
            self.created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind.value,
            "url": self.url,
            "tags": self.tags,
            "priority": self.priority,
            "enabled": self.enabled,
            "description": self.description,
            "category": self.category,
            "last_ingested": self.last_ingested,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SeedSource:
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            kind=SeedKind(data["kind"]),
            url=data.get("url"),
            tags=data.get("tags", []),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
            description=data.get("description"),
            category=data.get("category"),
            last_ingested=data.get("last_ingested"),
            created_at=data.get("created_at", ""),
        )

    def enable(self):
        """Enable this seed."""
        self.enabled = True
        self.status = SeedStatus.ENABLED

    def disable(self):
        """Disable this seed."""
        self.enabled = False
        self.status = SeedStatus.DISABLED


# ============================================================================
# SEED SOURCE PACK - Curated sources for initial discovery
# ============================================================================

def get_seed_pack() -> List[SeedSource]:
    """Get the curated seed source pack."""
    return [
        # Reddit communities - relevant discussions and community feedback
        SeedSource(
            id="seed-reddit-1",
            name="r/SoftwareArchitecture",
            kind=SeedKind.REDDIT_COMMUNITY,
            url="https://reddit.com/r/SoftwareArchitecture",
            tags=["architecture", "design", "best_practices"],
            priority=10,
            enabled=True,
            description="High-quality discussions about software architecture patterns",
            category="architecture",
        ),
        SeedSource(
            id="seed-reddit-2",
            name="r/Python",
            kind=SeedKind.REDDIT_COMMUNITY,
            url="https://reddit.com/r/Python",
            tags=["python", "programming", "community"],
            priority=8,
            enabled=True,
            description="Python programming community discussions",
            category="python",
        ),
        SeedSource(
            id="seed-reddit-3",
            name="r/MachineLearning",
            kind=SeedKind.REDDIT_COMMUNITY,
            url="https://reddit.com/r/MachineLearning",
            tags=["ml", "ai", "research"],
            priority=9,
            enabled=True,
            description="Machine learning and AI research discussions",
            category="ml_ai",
        ),
        # GitHub repositories - tool anchors and project references
        SeedSource(
            id="seed-github-1",
            name="weslr/weslr",
            kind=SeedKind.GITHUB_REPO,
            url="https://github.com/weslr/weslr",
            tags=["weslr", "platform", "agent"],
            priority=10,
            enabled=True,
            description="WESLR platform source - internal tooling",
            category="weslr",
        ),
        SeedSource(
            id="seed-github-2",
            name="python/cpython",
            kind=SeedKind.GITHUB_REPO,
            url="https://github.com/python/cpython",
            tags=["python", "interpreter", "core"],
            priority=7,
            enabled=True,
            description="Python core interpreter - language features",
            category="python",
        ),
        SeedSource(
            id="seed-github-3",
            name="pydantic/pydantic",
            kind=SeedKind.GITHUB_REPO,
            url="https://github.com/pydantic/pydantic",
            tags=["python", "validation", "pydantic"],
            priority=8,
            enabled=True,
            description="Pydantic data validation library",
            category="python",
        ),
        # Science-relevant sources - academic and certified knowledge
        SeedSource(
            id="seed-science-1",
            name="arxiv",
            kind=SeedKind.SCIENCE_SOURCE,
            url="https://arxiv.org",
            tags=["academic", "research", "papers"],
            priority=9,
            enabled=True,
            description="arXiv preprint server - scientific papers",
            category="academic",
        ),
        SeedSource(
            id="seed-science-2",
            name="scholar.google.com",
            kind=SeedKind.SCIENCE_SOURCE,
            url="https://scholar.google.com",
            tags=["academic", "research", "citations"],
            priority=8,
            enabled=True,
            description="Google Scholar - academic citations",
            category="academic",
        ),
        # Linked-knowledge / PKM anchors - existing WESLR knowledge
        SeedSource(
            id="seed-pkm-1",
            name="weslr/knowledge/base",
            kind=SeedKind.PKM_ANCHOR,
            tags=["weslr", "knowledge", "documentation"],
            priority=10,
            enabled=True,
            description="WESLR internal knowledge base",
            category="weslr",
        ),
        SeedSource(
            id="seed-pkm-2",
            name="weslr/concepts/graph",
            kind=SeedKind.PKM_ANCHOR,
            tags=["weslr", "concepts", "graph"],
            priority=8,
            enabled=True,
            description="WESLR concept graph",
            category="concepts",
        ),
        # Disabled seeds (for future use)
        SeedSource(
            id="seed-disabled-1",
            name="archived-source",
            kind=SeedKind.OTHER,
            url="https://example.com/archived",
            tags=["archived", "legacy"],
            priority=1,
            enabled=False,
            description="Disabled seed for future review",
            category="legacy",
        ),
    ]


def get_enabled_seeds() -> List[SeedSource]:
    """Get only enabled seed sources."""
    return [s for s in get_seed_pack() if s.enabled]


def get_seeds_by_kind(kind: SeedKind) -> List[SeedSource]:
    """Get seeds filtered by kind."""
    return [s for s in get_seed_pack() if s.kind == kind]


def get_seeds_by_category(category: str) -> List[SeedSource]:
    """Get seeds filtered by category."""
    return [s for s in get_seed_pack() if s.category == category]
