"""
elastic_memory.py - Elastic interaction memory for Weslr voice layer

Tracks interaction history with recency-weighted significance.
Learns what matters to this human vs. what doesn't.
Not a log — a memory that evolves.

v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class InteractionRecord:
    """A single interaction event."""
    timestamp: str
    interaction_type: str  # "greeting", "insight", "question", "response", "dismissal"
    content_summary: str   # Brief description, not full text
    human_reaction: str    # "received", "dismissed", "engaged", "ignored", "positive", "negative"
    context_tags: List[str] = field(default_factory=list)  # ["evening", "tired", "busy"]
    weslr_confidence: float = 0.5
    significance: float = 0.5  # How important was this interaction
    archived: bool = False


@dataclass
class RelationshipState:
    """Evolving model of the human's relationship with Weslr."""
    interaction_count: int = 0
    positive_reactions: int = 0
    dismissals: int = 0
    ignored: int = 0
    engagement_depth: float = 0.5  # 0.0-1.0, how deeply human engages
    trust_level: float = 0.5       # 0.0-1.0, learned from behavior
    topics_engaged: List[str] = field(default_factory=list)    # Topics human responds to
    topics_dismissed: List[str] = field(default_factory=list)  # Topics human dismisses
    preferred_greeting_style: str = "standard"  # "standard", "warm", "minimal", "absent"
    response_style: str = "balanced"  # "brief", "balanced", "detailed"
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_count": self.interaction_count,
            "positive_reactions": self.positive_reactions,
            "dismissals": self.dismissals,
            "ignored": self.ignored,
            "engagement_depth": round(self.engagement_depth, 3),
            "trust_level": round(self.trust_level, 3),
            "topics_engaged": self.topics_engaged,
            "topics_dismissed": self.topics_dismissed,
            "preferred_greeting_style": self.preferred_greeting_style,
            "response_style": self.response_style,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RelationshipState:
        return cls(**data)


@dataclass
class ElasticMemory:
    """
    Elastic memory store — interaction history with recency weighting.
    
    Unlike a plain log, this module learns from interactions and 
    adjusts future behavior accordingly.
    """
    tenant_id: str
    interactions: List[InteractionRecord] = field(default_factory=list)
    relationship: RelationshipState = field(default_factory=RelationshipState)
    unresolved_threads: List[Dict[str, Any]] = field(default_factory=list)  # Topics Weslr started but hasn't concluded
    things_to_follow_up: List[Dict[str, Any]] = field(default_factory=list)  # Things to mention later
    
    # Memory parameters
    recency_weight_span_hours: int = 168       # 1 week — interactions older than this have reduced impact
    significance_half_life: float = 0.85        # Each interaction's significance decays by this factor
    max_interactions_stored: int = 500        # Prune oldest when exceeded
    dismissal_threshold: float = 0.4           # Below this ratio of positive/dismissal → reduce topic frequency
    
    # Cooldown decay fields
    consecutive_ignored: int = 0
    cooldown_multiplier: float = 1.0

    def record(
        self,
        interaction_type: str,
        content_summary: str,
        human_reaction: str,
        context_tags: Optional[List[str]] = None,
        significance: float = 0.5,
        weslr_confidence: float = 0.5,
    ) -> None:
        """Record an interaction and update relationship model."""
        record = InteractionRecord(
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            interaction_type=interaction_type,
            content_summary=content_summary,
            human_reaction=human_reaction,
            context_tags=context_tags or [],
            significance=significance,
            weslr_confidence=weslr_confidence,
        )
        self.interactions.append(record)
        
        # Update relationship model
        self._update_relationship(record)
        
        # Prune if needed
        if len(self.interactions) > self.max_interactions_stored:
            self._prune_interactions()

    def _update_relationship(self, record: InteractionRecord) -> None:
        """Update relationship state based on new interaction."""
        self.relationship.interaction_count += 1
        
        if record.human_reaction in ("positive", "engaged", "received"):
            self.relationship.positive_reactions += 1
            # Increase engagement depth slightly
            self.relationship.engagement_depth = min(1.0, self.relationship.engagement_depth + 0.01)
            self.relationship.trust_level = min(1.0, self.relationship.trust_level + 0.005)
        elif record.human_reaction in ("dismissed"):
            self.relationship.dismissals += 1
            self.relationship.engagement_depth = max(0.0, self.relationship.engagement_depth - 0.02)
        elif record.human_reaction in ("ignored"):
            self.relationship.ignored += 1
            self.relationship.engagement_depth = max(0.0, self.relationship.engagement_depth - 0.01)
        
        # Track topics
        if record.interaction_type in ("insight", "question") and record.content_summary:
            if record.human_reaction in ("positive", "engaged", "received"):
                if record.content_summary not in self.relationship.topics_engaged:
                    self.relationship.topics_engaged.append(record.content_summary)
            elif record.human_reaction in ("dismissed", "ignored"):
                if record.content_summary not in self.relationship.topics_dismissed:
                    self.relationship.topics_dismissed.append(record.content_summary)
        
        self.relationship.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _prune_interactions(self) -> None:
        """Remove oldest interactions beyond max limit, keeping significant ones."""
        if len(self.interactions) <= self.max_interactions_stored:
            return
        
        # Sort by significance, keep top half of the max
        keep_count = self.max_interactions_stored // 2
        by_significance = sorted(self.interactions, key=lambda x: x.significance, reverse=True)
        self.interactions = by_significance[:keep_count]

    def get_recent_interactions(self, hours: int = 24, limit: int = 20) -> List[InteractionRecord]:
        """Get recent interactions within time window."""
        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        recent = []
        for interaction in reversed(self.interactions):
            try:
                ts = datetime.fromisoformat(interaction.timestamp.replace("Z", "+00:00")).timestamp()
                if ts >= cutoff:
                    recent.append(interaction)
                    if len(recent) >= limit:
                        break
            except Exception:
                continue
        return recent

    def weighted_recent_significance(self, hours: int = 168) -> float:
        """
        Calculate weighted significance of recent interactions.
        More recent = higher weight. Higher significance = higher weight.
        Returns 0.0-1.0.
        """
        interactions = self.get_recent_interactions(hours=hours, limit=100)
        if not interactions:
            return 0.0
        
        now = datetime.now(timezone.utc).timestamp()
        total_weighted = 0.0
        total_weight = 0.0
        
        for interaction in interactions:
            try:
                ts = datetime.fromisoformat(interaction.timestamp.replace("Z", "+00:00")).timestamp()
                age_hours = (now - ts) / 3600
                recency_factor = max(0.0, 1.0 - (age_hours / hours))
                weight = recency_factor * interaction.significance
                total_weighted += weight
                total_weight += recency_factor
            except Exception:
                continue
        
        if total_weight == 0:
            return 0.0
        return round(total_weighted / total_weight, 3)

    def should_surface_topic(self, topic: str) -> tuple[bool, float]:
        """
        Should Weslr bring up this topic?
        Returns (should_surface, confidence).
        Checks if topic has been dismissed recently and engagement depth.
        """
        # Check dismissal history
        for interaction in self.interactions[-50:]:  # Last 50 interactions
            if topic in interaction.content_summary and interaction.human_reaction == "dismissed":
                return False, 0.3
        
        # Check engagement depth
        if self.relationship.engagement_depth < 0.3:
            return False, 0.2
        
        # Check significance weight
        sig = self.weighted_recent_significance(hours=168)
        if sig < 0.3:
            return False, 0.4
        
        return True, round(sig * self.relationship.trust_level, 2)

    def add_unresolved_thread(self, topic: str, context: str, initiated_at: str) -> None:
        """Add a topic Weslr raised but hasn't concluded."""
        self.unresolved_threads.append({
            "topic": topic,
            "context": context,
            "initiated_at": initiated_at,
            "mentions": 1,
        })

    def resolve_unresolved_thread(self, topic: str) -> None:
        """Mark a thread as resolved."""
        self.unresolved_threads = [t for t in self.unresolved_threads if t["topic"] != topic]

    def add_follow_up(self, content: str, priority: str = "normal", expires_at: Optional[str] = None) -> None:
        """
        Add something to follow up on later.
        Priority: "low", "normal", "high"
        """
        self.things_to_follow_up.append({
            "content": content,
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at,
            "mentioned": 0,
        })

    def get_ignored_count_24h(self) -> int:
        """Count interactions marked 'ignored' in the last 24 hours."""
        recent = self.get_recent_interactions(hours=24)
        return sum(1 for i in recent if i.human_reaction == "ignored")


    def record_outcome(self, outcome: str) -> None:
        """
        Record the outcome of a surface attempt.
        outcome: "spoken", "ignored", "dismissed", "acknowledged"
        """
        if outcome == "spoken":
            # Positive reaction after speaking — reset decay state
            self.consecutive_ignored = 0
            self.cooldown_multiplier = 1.0
        elif outcome == "ignored":
            self.consecutive_ignored += 1
            self.cooldown_multiplier = min(3.0, 1.0 + self.consecutive_ignored * 0.25)
        elif outcome == "acknowledged":
            self.consecutive_ignored = 0
        elif outcome == "dismissed":
            self.consecutive_ignored += 0.5
            self.cooldown_multiplier = min(3.0, 1.0 + self.consecutive_ignored * 0.25)


    def get_cooldown_multiplier(self) -> float:
        """Return the current cooldown multiplier for adaptive cooldown."""
        return self.cooldown_multiplier

    def get_follow_ups(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get follow-up items that haven't been mentioned too often."""
        now = datetime.now(timezone.utc).timestamp()
        available = []
        for item in self.things_to_follow_up:
            if item["mentioned"] >= 3:  # Max 3 mentions
                continue
            if item.get("expires_at"):
                try:
                    exp = datetime.fromisoformat(item["expires_at"].replace("Z", "+00:00")).timestamp()
                    if now > exp:
                        continue
                except Exception:
                    pass
            available.append(item)
        
        # Sort by priority
        priority_order = {"high": 0, "normal": 1, "low": 2}
        available.sort(key=lambda x: priority_order.get(x["priority"], 1))
        return available[:max_results]

    def acknowledge_follow_up(self, content: str) -> None:
        """Increment mention count for a follow-up."""
        for item in self.things_to_follow_up:
            if item["content"] == content:
                item["mentioned"] += 1
                break

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "interactions": [
                {
                    "timestamp": i.timestamp,
                    "interaction_type": i.interaction_type,
                    "content_summary": i.content_summary,
                    "human_reaction": i.human_reaction,
                    "context_tags": i.context_tags,
                    "weslr_confidence": i.weslr_confidence,
                    "significance": i.significance,
                    "archived": i.archived,
                }
                for i in self.interactions
            ],
            "relationship": self.relationship.to_dict(),
            "unresolved_threads": self.unresolved_threads,
            "things_to_follow_up": self.things_to_follow_up,
            "consecutive_ignored": self.consecutive_ignored,
            "cooldown_multiplier": self.cooldown_multiplier,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ElasticMemory:
        interactions = [
            InteractionRecord(
                timestamp=i["timestamp"],
                interaction_type=i["interaction_type"],
                content_summary=i["content_summary"],
                human_reaction=i["human_reaction"],
                context_tags=i.get("context_tags", []),
                weslr_confidence=i.get("weslr_confidence", 0.5),
                significance=i.get("significance", 0.5),
                archived=i.get("archived", False),
            )
            for i in data.get("interactions", [])
        ]
        relationship = RelationshipState.from_dict(data.get("relationship", {}))
        return cls(
            tenant_id=data.get("tenant_id", "default"),
            interactions=interactions,
            relationship=relationship,
            unresolved_threads=data.get("unresolved_threads", []),
            things_to_follow_up=data.get("things_to_follow_up", []),
            consecutive_ignored=data.get("consecutive_ignored", 0),
            cooldown_multiplier=data.get("cooldown_multiplier", 1.0),
        )


# ============================================================================
# ELASTIC MEMORY STORE (thread-safe singleton per tenant)
# ============================================================================

_memory_store: Dict[str, ElasticMemory] = {}
_store_lock = threading.Lock()


def get_elastic_memory(tenant_id: str, storage_path: Optional[Path] = None) -> ElasticMemory:
    """
    Get or create elastic memory for tenant.
    Thread-safe. Persists to disk.
    """
    global _memory_store
    
    with _store_lock:
        if tenant_id in _memory_store:
            return _memory_store[tenant_id]
    
    # Try to load from disk
    if storage_path:
        mem_file = storage_path / f"elastic_memory_{tenant_id}.json"
        if mem_file.exists():
            try:
                data = json.loads(mem_file.read_text())
                memory = ElasticMemory.from_dict(data)
                with _store_lock:
                    _memory_store[tenant_id] = memory
                return memory
            except Exception:
                pass
    
    # Create new
    memory = ElasticMemory(tenant_id=tenant_id)
    with _store_lock:
        _memory_store[tenant_id] = memory
    return memory


def save_elastic_memory(memory: ElasticMemory, storage_path: Optional[Path] = None) -> None:
    """Persist elastic memory to disk."""
    if not storage_path:
        return
    mem_file = storage_path / f"elastic_memory_{memory.tenant_id}.json"
    mem_file.write_text(json.dumps(memory.to_dict(), indent=2))