# capability_ingestion.py - Weslr Capability Discovery: Signal Ingestion
# Manual ingestion + normalization pipeline for Phase 2.
# Additive only, reversible, continuity-compatible.

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try relative import first (when run as module), fall back to absolute
try:
    from .capability_suggestion import (
        CapabilitySuggestion,
        CapabilityType,
        SuggestionStatus,
        SourceProvenance,
        CapabilitySuggestionStore,
        CapabilityDiscoveryRadar,
    )
except ImportError:
    from capability_suggestion import (
        CapabilitySuggestion,
        CapabilityType,
        SuggestionStatus,
        SourceProvenance,
        CapabilitySuggestionStore,
        CapabilityDiscoveryRadar,
    )


# ============================================================================
# SOURCE SIGNAL MODEL
# ============================================================================

class SourceKind(str, Enum):
    """Supported source kinds for ingestion."""
    REDDIT = "reddit"
    GITHUB = "github"
    MANUAL = "manual"
    OTHER = "other"


class SignalStatus(str, Enum):
    """Status of an ingested signal."""
    PENDING = "pending"
    NORMALIZED = "normalized"
    INGESTED = "ingested"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


@dataclass
class SourceSignal:
    """A source signal to be normalized and ingested."""
    id: str
    source_kind: SourceKind
    title: str
    url: Optional[str] = None
    snippet: Optional[str] = None
    body: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    detected_capability: Optional[str] = None
    source_timestamp: Optional[str] = None
    provenance: Optional[str] = None
    confidence: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    status: SignalStatus = SignalStatus.PENDING
    normalized_at: Optional[str] = None
    ingestion_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SourceSignal:
        """Deserialize from dict."""
        data["source_kind"] = SourceKind(data.get("source_kind", "other"))
        data["status"] = SignalStatus(data.get("status", "pending"))
        data["tags"] = data.get("tags", [])
        return cls(**data)

    def update_status(self, status: SignalStatus, error: Optional[str] = None) -> None:
        """Update status and timestamp."""
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if error:
            self.ingestion_error = error
        if status == SignalStatus.NORMALIZED:
            self.normalized_at = self.updated_at


# ============================================================================
# NORMALIZATION PIPELINE
# ============================================================================

class NormalizationPipeline:
    """Normalizes source signals to capability suggestions."""

    def __init__(self, radar: Optional[CapabilityDiscoveryRadar] = None):
        self.radar = radar or CapabilityDiscoveryRadar()
        self.store = self.radar.store

    def normalize(self, signal: SourceSignal) -> Dict[str, Any]:
        """Normalize a source signal to capability suggestion fields.

        Returns dict with:
        - title
        - summary
        - why_it_matters
        - improvement_area
        - capability_type
        - provenance
        - confidence
        - rank_score
        """
        # Extract capability text from title/body/snippet
        capability_text = self._extract_capability(signal)

        # Determine capability type
        capability_type = self._detect_capability_type(signal, capability_text)

        # Build normalized fields
        normalized = {
            "title": signal.title[:100],  # Truncate if too long
            "summary": self._build_summary(signal, capability_text),
            "why_it_matters": self._build_why_matters(signal, capability_type, capability_text),
            "improvement_area": capability_text or "General capability improvement",
            "capability_type": capability_type,
            "provenance": signal.source_kind.value,
            "confidence": signal.confidence if signal.confidence is not None else self._estimate_confidence(signal),
            "rank_score": self._estimate_rank_score(signal, capability_type, capability_text),
        }

        return normalized

    def _extract_capability(self, signal: SourceSignal) -> Optional[str]:
        """Extract capability text from signal."""
        # Try detected_capability first
        if signal.detected_capability:
            return signal.detected_capability.strip()

        # Try to extract from title
        if signal.title:
            # Common patterns
            patterns = [
                r"(?:improve|add|enhance|create|build|implement)\s+(.+?)(?:\s+for|\s+to|\s+in|$)",
                r"(.+?)(?:\s+capability|functionality|feature|system)",
            ]
            for pattern in patterns:
                match = re.search(pattern, signal.title, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        # Try body/snippet
        text = signal.body or signal.snippet or ""
        if text:
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        return None

    def _detect_capability_type(self, signal: SourceSignal, capability_text: Optional[str]) -> CapabilityType:
        """Detect capability type based on signal content."""
        text = (capability_text or signal.title or "").lower()
        tags = [t.lower() for t in signal.tags]

        # Type keywords
        type_keywords = {
            CapabilityType.INGESTION: ["ingest", "import", "feed", "sync", "gather", "collect"],
            CapabilityType.ANALYSIS: ["analy", "model", "predict", "forecast", "inspect", "examine"],
            CapabilityType.VISUALIZATION: ["visual", "plot", "graph", "chart", "display", "render"],
            CapabilityType.AUTOMATION: ["automat", "script", "schedule", "trigger", "workflow"],
            CapabilityType.INTEGRATION: ["integrat", "connect", "bridge", "sync", "unify"],
            CapabilityType.STORAGE: ["stor", "persist", "cache", "index", "database"],
            CapabilityType.SECURITY: ["secur", "auth", "privilege", "access", "protect", "encrypt"],
        }

        # Score each type
        scores: Dict[CapabilityType, int] = {t: 0 for t in CapabilityType}
        for cap_type, keywords in type_keywords.items():
            for kw in keywords:
                if kw in text:
                    scores[cap_type] += 1
                if kw in " ".join(tags):
                    scores[cap_type] += 1

        # Return highest scoring type
        if scores:
            best = max(scores.items(), key=lambda x: x[1])
            if best[1] > 0:
                return best[0]

        return CapabilityType.OTHER

    def _build_summary(self, signal: SourceSignal, capability_text: Optional[str]) -> str:
        """Build normalized summary."""
        parts = []

        if signal.source_kind == SourceKind.REDDIT:
            parts.append(f"Source: Reddit post '{signal.title[:50]}...'")
        elif signal.source_kind == SourceKind.GITHUB:
            parts.append(f"Source: GitHub issue/PR '{signal.title[:50]}...'")
            if signal.url:
                parts.append(f"URL: {signal.url}")
        elif signal.source_kind == SourceKind.MANUAL:
            parts.append("Source: Manual submission")
        else:
            parts.append(f"Source: {signal.source_kind.value}")

        if capability_text:
            parts.append(f"Requested: {capability_text}")

        if signal.snippet:
            parts.append(f"Context: {signal.snippet[:100]}...")

        return " ".join(parts)

    def _build_why_matters(self, signal: SourceSignal, capability_type: CapabilityType, capability_text: Optional[str]) -> str:
        """Build 'why it matters' field."""
        return f"This capability would enable {capability_type.value} improvements, potentially enhancing workflow efficiency and user experience.{' ' + capability_text if capability_text else ''}"

    def _estimate_confidence(self, signal: SourceSignal) -> float:
        """Estimate confidence in the signal quality."""
        confidence = 0.5  # Base

        # Boost for complete signals
        if signal.title:
            confidence += 0.1
        if signal.snippet or signal.body:
            confidence += 0.1
        if signal.tags:
            confidence += min(0.2, len(signal.tags) * 0.05)

        # Boost for Reddit/GitHub signals (more structured)
        if signal.source_kind in (SourceKind.REDDIT, SourceKind.GITHUB):
            confidence += 0.1

        # Cap at 1.0
        return min(1.0, round(confidence, 2))

    def _estimate_rank_score(self, signal: SourceSignal, capability_type: CapabilityType, capability_text: Optional[str]) -> int:
        """Estimate rank score for sorting."""
        score = 0

        # Base score
        score += 10

        # Source quality bonus
        if signal.source_kind == SourceKind.GITHUB:
            score += 20
        elif signal.source_kind == SourceKind.REDDIT:
            score += 10

        # Complete signal bonus
        if signal.snippet or signal.body:
            score += 5

        # Tags bonus
        score += len(signal.tags) * 2

        # Provenance bonus
        if signal.provenance == "high":
            score += 15

        return score


# ============================================================================
# INGESTION PIPELINE
# ============================================================================

class CapabilityIngestionPipeline:
    """End-to-end ingestion pipeline from signal to suggestion."""

    def __init__(self, radar: Optional[CapabilityDiscoveryRadar] = None):
        self.radar = radar or CapabilityDiscoveryRadar()
        self.store = self.radar.store
        self.normalizer = NormalizationPipeline(self.radar)

    def ingest_signal(self, signal: SourceSignal) -> Dict[str, Any]:
        """Ingest a source signal, creating a capability suggestion.

        Returns:
            Dict with:
            - signal_id: The signal ID
            - suggestion_id: The created suggestion ID (if any)
            - status: ingestion status
            - duplicate_of: If duplicate
            - error: Any error message
        """
        result = {
            "signal_id": signal.id,
            "suggestion_id": None,
            "status": signal.status.value,
            "duplicate_of": None,
            "error": None,
        }

        try:
            # Check for duplicate
            existing = self._check_duplicate(signal)
            if existing:
                signal.update_status(SignalStatus.DUPLICATE)
                result["status"] = "duplicate"
                result["duplicate_of"] = existing.id
                return result

            # Normalize
            normalized = self.normalizer.normalize(signal)

            # Map source kind to provenance
            source_to_provenance = {
                SourceKind.REDDIT: SourceProvenance.REDDIT,
                SourceKind.GITHUB: SourceProvenance.GITHUB,
                SourceKind.MANUAL: SourceProvenance.DIRECT_SUBMISSION,
                SourceKind.OTHER: SourceProvenance.OTHER,
            }
            provenance = source_to_provenance.get(signal.source_kind, SourceProvenance.OTHER)

            # Create suggestion
            suggestion = self.radar.create_suggestion(
                title=normalized["title"],
                description=normalized["summary"],
                capability_type=normalized["capability_type"],
                provenance=provenance,
                suggestion_text=signal.body or signal.snippet,
                tags=",".join(signal.tags) if signal.tags else None,
                priority=normalized["rank_score"],
                assigned_to=None,
                notes=f"Provenance: {normalized['provenance']}\nWhy it matters: {normalized['why_it_matters']}\nImprovement area: {normalized['improvement_area']}",
            )

            # Update signal status
            signal.update_status(SignalStatus.INGESTED)
            result["suggestion_id"] = suggestion.id
            result["status"] = "ingested"

        except Exception as e:
            signal.update_status(SignalStatus.REJECTED, error=str(e))
            result["status"] = "rejected"
            result["error"] = str(e)

        return result

    def _check_duplicate(self, signal: SourceSignal) -> Optional[CapabilitySuggestion]:
        """Check if signal is a duplicate."""
        # Check by URL if available (exact match)
        if signal.url:
            # Look for existing suggestions with same URL in notes
            all_suggestions = self.store.list_all(include_archived=True)
            for s in all_suggestions:
                if s.notes and signal.url in s.notes:
                    return s

        # Check by title (normalized, exact match)
        if signal.title:
            # Normalize title: lowercase, strip non-alphanumeric, collapse whitespace
            title_norm = re.sub(r"\s+", " ", signal.title.lower().strip())
            # Remove punctuation for comparison
            title_norm = re.sub(r"[^a-z0-9 ]", "", title_norm).strip()
            
            all_suggestions = self.store.list_all(include_archived=True)
            for s in all_suggestions:
                if s.title:
                    s_norm = re.sub(r"\s+", " ", s.title.lower().strip())
                    s_norm = re.sub(r"[^a-z0-9 ]", "", s_norm).strip()
                    if title_norm and s_norm and title_norm == s_norm:
                        return s

        return None

    def ingest_manual(
        self,
        title: str,
        body: Optional[str] = None,
        source_kind: SourceKind = SourceKind.MANUAL,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None,
        detected_capability: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Ingest a manual signal."""
        signal = SourceSignal(
            id=f"manual-{uuid.uuid4().hex[:8]}",
            source_kind=source_kind,
            title=title,
            body=body,
            snippet=body[:200] if body else None,
            tags=tags or [],
            url=url,
            detected_capability=detected_capability,
            confidence=confidence,
        )
        return self.ingest_signal(signal)

    def ingest_reddit(
        self,
        title: str,
        url: str,
        body: Optional[str] = None,
        tags: Optional[List[str]] = None,
        detected_capability: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Ingest a Reddit-like signal."""
        signal = SourceSignal(
            id=f"reddit-{uuid.uuid4().hex[:8]}",
            source_kind=SourceKind.REDDIT,
            title=title,
            url=url,
            body=body,
            snippet=body[:200] if body else None,
            tags=tags or [],
            detected_capability=detected_capability,
            confidence=confidence,
        )
        return self.ingest_signal(signal)

    def ingest_github(
        self,
        title: str,
        url: str,
        body: Optional[str] = None,
        tags: Optional[List[str]] = None,
        detected_capability: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Ingest a GitHub-like signal."""
        signal = SourceSignal(
            id=f"github-{uuid.uuid4().hex[:8]}",
            source_kind=SourceKind.GITHUB,
            title=title,
            url=url,
            body=body,
            snippet=body[:200] if body else None,
            tags=tags or [],
            detected_capability=detected_capability,
            confidence=confidence,
        )
        return self.ingest_signal(signal)


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI interface for ingestion."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python capability_ingestion.py <command> [args]")
        print("Commands:")
        print("  manual <title> <body>")
        print("  reddit <title> <url> [body]")
        print("  github <title> <url> [body]")
        print("  summary")
        sys.exit(1)

    command = sys.argv[1]
    pipeline = CapabilityIngestionPipeline()

    if command == "manual":
        if len(sys.argv) < 4:
            print("Usage: python capability_ingestion.py manual <title> <body>")
            sys.exit(1)
        title = sys.argv[2]
        body = " ".join(sys.argv[3:])
        result = pipeline.ingest_manual(title=title, body=body)
        print(json.dumps(result, indent=2))

    elif command == "reddit":
        if len(sys.argv) < 4:
            print("Usage: python capability_ingestion.py reddit <title> <url> [body]")
            sys.exit(1)
        title = sys.argv[2]
        url = sys.argv[3]
        body = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else None
        result = pipeline.ingest_reddit(title=title, url=url, body=body)
        print(json.dumps(result, indent=2))

    elif command == "github":
        if len(sys.argv) < 4:
            print("Usage: python capability_ingestion.py github <title> <url> [body]")
            sys.exit(1)
        title = sys.argv[2]
        url = sys.argv[3]
        body = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else None
        result = pipeline.ingest_github(title=title, url=url, body=body)
        print(json.dumps(result, indent=2))

    elif command == "summary":
        summary = pipeline.radar.get_summary()
        print(json.dumps(summary, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


# ============================================================================
# TREND SCORING ENGINE (Phase 5)
# ============================================================================

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from collections import Counter


class TrendScoringEngine:
    """Trend scoring and radar for capability discovery.
    
    Scoring combines:
    - mention count (frequency of signals)
    - source diversity (unique provenance families)
    - growth delta (comparative change from previous run)
    - science relevance (content analysis)
    - implementation impact (estimated effect)
    """

    def __init__(self, store: Optional[CapabilitySuggestionStore] = None):
        self.store = store or CapabilitySuggestionStore()
        self._last_run_cache: Optional[Dict[str, Any]] = None

    def _now(self) -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _estimate_science_relevance(self, suggestion: CapabilitySuggestion) -> float:
        """Estimate science/research relevance from suggestion content."""
        score = 0.5  # Base
        
        # Boost for science-related keywords
        science_keywords = [
            "science", "research", "paper", "study", "experiment",
            "academic", "publication", "journal", "literature",
            "scientific", "discovery", "innovation", " breakthrough"
        ]
        text = f"{suggestion.title} {suggestion.description} {suggestion.suggestion_text or ''} {suggestion.context or ''}".lower()
        
        matches = sum(1 for kw in science_keywords if kw in text)
        score += min(0.3, matches * 0.05)  # +0.05 per match, max +0.3
        
        # Boost for open source/repo mentions
        if any(x in text for x in ["github", "repository", "repo", "open source", "library"]):
            score += 0.1
        
        return round(min(1.0, score), 2)

    def _estimate_implementation_impact(self, suggestion: CapabilitySuggestion) -> int:
        """Estimate implementation effort impact (1-100)."""
        score = 20  # Base
        
        # Shorter titles often indicate clearer scope
        if len(suggestion.title) < 60:
            score += 15
        elif len(suggestion.title) < 100:
            score += 5
        
        # Automation type implies lower implementation barrier
        if suggestion.capability_type.value == "automation":
            score += 20
        
        # Integration suggests existing tooling
        if suggestion.capability_type.value == "integration":
            score += 10
        
        # Mention of existing tools (e.g., "Obsidian", "LangChain") reduces scope
        existing_tool_keywords = ["obsidian", "notion", "langchain", "openai", "aws", "docker"]
        text = f"{suggestion.title} {suggestion.description}".lower()
        if any(kw in text for kw in existing_tool_keywords):
            score += 10
        
        return min(100, score)

    def _count_mentions(self, suggestions: List[CapabilitySuggestion]) -> int:
        """Count total mentions across suggestions."""
        return sum(s.mention_count for s in suggestions)

    def _count_source_diversity(self, suggestions: List[CapabilitySuggestion]) -> int:
        """Count unique provenance families."""
        provenances = set()
        for s in suggestions:
            if s.provenance:
                provenances.add(str(s.provenance))
        return len(provenances)

    def _parse_timestamp(self, ts: Optional[str]) -> Optional[datetime]:
        """Parse ISO timestamp to datetime."""
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def update_trend_metrics(self, suggestion: CapabilitySuggestion) -> CapabilitySuggestion:
        """Update trend metrics for a suggestion from its source signals."""
        now = self._now()
        
        # Update first_seen if not set (first appearance)
        if not suggestion.first_seen:
            suggestion.first_seen = suggestion.created_at
        
        # Update last_seen to most recent
        if not suggestion.last_seen or (suggestion.last_seen and suggestion.last_seen < now):
            suggestion.last_seen = now
        
        # Calculate time delta (in hours) from first to last seen
        first_dt = self._parse_timestamp(suggestion.first_seen)
        last_dt = self._parse_timestamp(suggestion.last_seen)
        if first_dt and last_dt:
            delta_hours = (last_dt - first_dt).total_seconds() / 3600
            # Simple growth estimate: inverse of spread (faster = more trending)
            if delta_hours > 0:
                # Normalize to 0-100 scale (faster spread = higher score)
                growth_score = min(100, int(10000 / (delta_hours + 1)))
                suggestion.trend_delta = round(growth_score / 100, 2)
        
        # Update science relevance
        suggestion.science_relevance_score = self._estimate_science_relevance(suggestion)
        
        return suggestion

    def compare_with_previous_run(self, current_suggestions: List[CapabilitySuggestion]) -> Dict[str, Any]:
        """Compare current suggestions with previous run to compute deltas."""
        # For simplicity, track last_seen timestamps as proxy for run timing
        # In production, would compare against persisted snapshots
        
        # Count mentions in this batch
        total_mentions = self._count_mentions(current_suggestions)
        
        # Source diversity
        diversity = self._count_source_diversity(current_suggestions)
        
        # Priority distribution
        priorities = [s.priority for s in current_suggestions]
        avg_priority = sum(priorities) / len(priorities) if priorities else 0
        
        # Top capability types
        type_counts = Counter(s.capability_type.value for s in current_suggestions)
        
        return {
            "total_mentions": total_mentions,
            "source_diversity": diversity,
            "avg_priority": round(avg_priority, 2),
            "capability_type_distribution": dict(type_counts),
            "suggestion_count": len(current_suggestions),
        }

    def compute_trend_score(self, suggestion: CapabilitySuggestion, global_diversity: Optional[int] = None) -> Dict[str, Any]:
        """Compute complete trend score for a suggestion.
        
        Args:
            suggestion: The capability suggestion to score
            global_diversity: Optional global source diversity (count of unique provenances)
        
        Returns:
            Dict with:
            - trend_score: 0-100 overall trend score
            - rank_explanation: Human-readable ranking rationale
            - confidence: 0-1 confidence in the score
        """
        components = {}
        weights = {}
        
        # Component 1: Priority (25%)
        priority_score = min(100, suggestion.priority * 2)  # Cap at 100
        components["priority"] = priority_score
        weights["priority"] = 0.25
        
        # Component 2: Source diversity (20%)
        # Use global diversity if provided, otherwise use per-suggestion value
        diversity = global_diversity if global_diversity is not None else 1
        diversity_bonus = min(100, diversity * 25)
        components["diversity"] = diversity_bonus
        components["global_diversity"] = diversity  # Store for explanation
        weights["diversity"] = 0.20
        
        # Component 3: Growth delta (20%)
        if suggestion.trend_delta:
            growth_score = int(suggestion.trend_delta * 100)
        else:
            growth_score = 50  # Neutral
        components["growth"] = growth_score
        weights["growth"] = 0.20
        
        # Component 4: Science relevance (15%)
        if suggestion.science_relevance_score:
            science_score = int(suggestion.science_relevance_score * 100)
        else:
            science_score = 50  # Neutral
        components["science"] = science_score
        weights["science"] = 0.15
        
        # Component 5: Implementation impact (20%)
        impact_score = self._estimate_implementation_impact(suggestion)
        components["impact"] = impact_score
        weights["impact"] = 0.20
        
        # Weighted sum (exclude non-weighted components)
        trend_score = sum(components[k] * weights[k] for k in weights)
        
        # Build explanation
        explanations = []
        explanations.append(f"Priority score: {components['priority']}")
        global_div = components.get("global_diversity", 1)
        explanations.append(f"Source diversity: {components['diversity']} ({global_div} unique provenances)")
        if suggestion.trend_delta:
            explanations.append(f"Growth delta: {suggestion.trend_delta:.2f}x")
        explanations.append(f"Science relevance: {components['science']} (scored {suggestion.science_relevance_score or 0:.2f})")
        explanations.append(f"Implementation impact: {components['impact']}/100")
        
        return {
            "trend_score": round(trend_score, 1),
            "rank_explanation": "; ".join(explanations),
            "confidence": 0.85,  # Confidence in trend scoring methodology
            "components": components,
        }

    def get_top_trending(self, limit: int = 10) -> List[CapabilitySuggestion]:
        """Get top trending suggestions sorted by trend score."""
        all_suggestions = self.store.list_all(include_archived=False)
        
        # Compute global source diversity first
        global_diversity = self._count_source_diversity(all_suggestions)
        
        scored = []
        for s in all_suggestions:
            # Update metrics first
            self.update_trend_metrics(s)
            
            # Compute score with global diversity
            score_data = self.compute_trend_score(s, global_diversity)
            s.trend_score = score_data["trend_score"]
            s.rank_explanation = score_data["rank_explanation"]
            scored.append(s)
        
        # Sort by trend_score descending
        scored.sort(key=lambda x: x.trend_score, reverse=True)
        
        return scored[:limit]


# ============================================================================
# ALIAS NORMALIZATION + CONCEPT GRAPH LINKING (Phase 6)
# ============================================================================

class AliasNormalizer:
    """Normalizes aliases and generates canonical identities for tools/capabilities.
    
    Handles:
    - Canonical key generation
    - Alias detection across sources
    - Source variant preservation
    - Merging repeated identities
    """

    # Common alias patterns
    ALIAS_PATTERNS = {
        "obsidian": ["obsidianmd/obsidian", "obsidian.md", "obsidian md", "obsidian"],
        "github": ["github.com", "git hub", "github"],
        "notion": ["notion.so", "notion ai", "notion"],
        "langchain": ["langchain", "lang chain"],
        "openai": ["openai.com", "open ai"],
    }

    def __init__(self):
        self.canonical_map: Dict[str, str] = {}  # alias -> canonical_key
        self.source_variants: Dict[str, List[str]] = {}  # canonical_key -> [variants]
        self._init_alias_map()

    def _init_alias_map(self) -> None:
        """Initialize alias mappings from patterns."""
        for canonical, variants in self.ALIAS_PATTERNS.items():
            for v in variants:
                self.canonical_map[v.lower().strip()] = canonical
            self.source_variants[canonical] = variants

    def normalize(self, title: str, source_kind: Optional[SourceKind] = None) -> Dict[str, Any]:
        """Normalize a title to its canonical identity.
        
        Args:
            title: The input title
            source_kind: Optional source kind for context
            
        Returns:
            Dict with:
            - canonical_key: The canonical identity
            - detected_aliases: List of detected aliases
            - source_variants: List of source-specific variants
        """
        title_lower = title.lower().strip()
        
        # Try direct match in canonical_map
        if title_lower in self.canonical_map:
            canonical = self.canonical_map[title_lower]
            return {
                "canonical_key": canonical,
                "detected_aliases": [title_lower],
                "source_variants": self.source_variants.get(canonical, []),
            }
        
        # Try partial match
        for canonical, variants in self.ALIAS_PATTERNS.items():
            for variant in variants:
                if variant.lower() in title_lower:
                    return {
                        "canonical_key": canonical,
                        "detected_aliases": [variant.lower()],
                        "source_variants": [variant.lower()],
                    }
        
        # Default: use title as canonical (normalized)
        return {
            "canonical_key": self._normalize_to_key(title),
            "detected_aliases": [title_lower],
            "source_variants": [title_lower],
        }

    def _normalize_to_key(self, text: str) -> str:
        """Convert text to a canonical key format."""
        # Lowercase, remove special chars, collapse whitespace
        import re
        key = text.lower().strip()
        key = re.sub(r"[^a-z0-9 ]", " ", key)
        key = re.sub(r"\s+", "_", key)
        return key.strip("_")

    def merge_aliases(self, suggestions: List[CapabilitySuggestion]) -> Dict[str, List[CapabilitySuggestion]]:
        """Group suggestions by canonical identity.
        
        Returns dict mapping canonical_key -> list of suggestions.
        """
        groups: Dict[str, List[CapabilitySuggestion]] = {}
        
        for s in suggestions:
            # Use existing canonical_key if set, otherwise normalize title
            key = s.canonical_key or self._normalize_to_key(s.title)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(s)
        
        return groups


class ConceptGraphLinker:
    """Minimal Concept Graph linking for capability suggestions.
    
    Creates/links:
    - Concept nodes for tools/capabilities
    - Evidence links from suggestions to concepts
    - Backlinks for reverse lookup
    """

    def __init__(self, concept_store: Optional[Any] = None):
        self.concept_store = concept_store
        self._initialized = False

    def _init_concept_store(self) -> Any:
        """Initialize Concept Graph store if not provided."""
        if self.concept_store:
            return self.concept_store
        
        # Try to import from concept_graph module
        try:
            from weslr.concept_graph.store import ConceptStore
            self.concept_store = ConceptStore()
            return self.concept_store
        except ImportError:
            # Fallback: return None for minimal operation
            return None

    def link_suggestion_to_concept(
        self,
        suggestion: CapabilitySuggestion,
        concept_name: Optional[str] = None,
        concept_type: str = "tool",
    ) -> Optional[str]:
        """Link a suggestion to a Concept Graph node.
        
        Args:
            suggestion: The capability suggestion
            concept_name: Optional concept name (defaults to canonical_key)
            concept_type: Type of concept ("tool", "capability", "entity")
            
        Returns:
            Concept ID if linked, None otherwise
        """
        if not self.concept_store:
            self.concept_store = self._init_concept_store()
        
        if not self.concept_store:
            return None  # No concept store available
        
        # Use existing concept_link_id or create new concept
        if suggestion.concept_link_id:
            return suggestion.concept_link_id
        
        # Create or find concept
        concept_name = concept_name or suggestion.canonical_key or suggestion.title
        concept = self._find_or_create_concept(concept_name, concept_type)
        
        if concept:
            suggestion.concept_link_id = concept.id
            return concept.id
        
        return None

    def _find_or_create_concept(
        self,
        name: str,
        concept_type: str = "tool",
    ) -> Optional[Any]:
        """Find existing concept or create new one."""
        # Try to find by name
        try:
            # ConceptStore.find() may not exist, try load or search
            if hasattr(self.concept_store, "find"):
                result = self.concept_store.find(name)
                if result:
                    return result
        except Exception:
            pass
        
        # Create new concept
        try:
            from weslr.concept_graph.models import Concept
            import time
            concept = Concept(
                id=f"concept-{name.lower().replace(' ', '-')[:50]}",
                name=name,
                type=concept_type,
                description=f"Detected capability: {name}",
                aliases=[],
                tags=["capability_discovery"],
                confidence=0.5,
                is_temporary=False,
                is_ghost=False,
            )
            
            if hasattr(self.concept_store, "save"):
                self.concept_store.save(concept)
            
            return concept
        except Exception:
            return None

    def link_evidence(
        self,
        concept_id: str,
        suggestion: CapabilitySuggestion,
        confidence: float = 0.8,
    ) -> Optional[str]:
        """Link evidence from suggestion to concept.
        
        Returns link ID if successful, None otherwise.
        """
        if not self.concept_store:
            return None
        
        try:
            from weslr.concept_graph.models import Evidence, Link, LinkType
            import time
            
            # Create evidence
            evidence = Evidence(
                source_id=suggestion.id,
                source_type="capability_suggestion",
                content=f"Suggestion: {suggestion.title}",
                confidence=confidence,
                timestamp=int(time.time()),
                category="source-backed",
                traceable=True,
                reason=f"Detected from {suggestion.provenance}",
            )
            
            # Add evidence to concept
            concept = self.concept_store.load(concept_id) if hasattr(self.concept_store, "load") else None
            if concept:
                concept.add_evidence(evidence)
                if hasattr(self.concept_store, "save"):
                    self.concept_store.save(concept)
            
            return evidence.source_id
        except Exception:
            return None


# ============================================================================
# DECISION SUPPORT ENGINE (Phase 7)
# ============================================================================

class DecisionSupportEngine:
    """Decision support engine for capability suggestions.
    
    Generates explanations and recommendations based on:
    - Provenance
    - Trend score
    - Source diversity
    - Science relevance
    - Concept graph links
    - Roadmap tags
    """

    def __init__(self, store: Optional[CapabilitySuggestionStore] = None):
        self.store = store or CapabilitySuggestionStore()

    def generate_explanation(self, suggestion: CapabilitySuggestion) -> CapabilitySuggestion:
        """Generate explanation for a suggestion.
        
        Updates the suggestion with:
        - why_surfaced
        - supporting_signals_summary
        - improvement_targets
        - implementation_effort_estimate
        - risk_level
        - classification
        - decision_recommendation
        
        Returns the updated suggestion.
        """
        import re
        
        # Extract improvement targets from title/description
        targets = []
        if suggestion.title:
            if "workflow" in suggestion.title.lower():
                targets.append("automation")
            if "memory" in suggestion.title.lower():
                targets.append("context management")
            if "link" in suggestion.title.lower() or "connect" in suggestion.title.lower():
                targets.append("linked data")
            if "agent" in suggestion.title.lower():
                targets.append("agent orchestration")
        if not targets:
            targets.append("general improvement")
        
        suggestion.improvement_targets = ",".join(targets)
        
        # Generate why_surfaced based on provenance and score
        # Compute trend score if not persisted
        if not hasattr(suggestion, 'trend_score') or not suggestion.trend_score:
            from capability_ingestion import TrendScoringEngine
            engine = TrendScoringEngine(self.store)
            engine.update_trend_metrics(suggestion)
            score_data = engine.compute_trend_score(suggestion, 1)  # Local diversity
            suggestion.trend_score = score_data.get("trend_score", 50)
        
        if suggestion.provenance:
            source_type = str(suggestion.provenance).split(".")[-1].lower()
            suggestion.why_surfaced = f"Detected from {source_type} source with trend score {suggestion.trend_score}"
        
        # Supporting signals summary
        signals = []
        if suggestion.science_relevance_score and suggestion.science_relevance_score > 0.6:
            signals.append("high science relevance")
        if suggestion.source_diversity and suggestion.source_diversity > 1:
            signals.append(f"cross-source traction ({suggestion.source_diversity} sources)")
        if suggestion.mention_count > 0:
            signals.append(f"{suggestion.mention_count} mentions")
        if suggestion.concept_link_id:
            signals.append("linked to concept graph")
        if not signals:
            signals.append("standard signal detected")
        
        suggestion.supporting_signals_summary = "; ".join(signals)
        
        # Implementation effort estimate
        effort = 30  # Base
        if len(suggestion.title) < 50:
            effort += 10  # Clear scope
        if suggestion.capability_type.value in ("automation", "integration"):
            effort += 20
        if "Obsidian" in suggestion.title or "notion" in suggestion.title.lower():
            effort += 15  # Integration complexity
        suggestion.implementation_effort_estimate = min(100, effort)
        
        # Risk level
        risk = "low"
        if suggestion.capability_type.value == "security":
            risk = "high"
        elif suggestion.capability_type.value in ("automation", "analysis"):
            risk = "medium"
        suggestion.risk_level = risk
        
        # Classification: quick_win / strategic / speculative
        classification = "speculative"  # Default
        if suggestion.trend_score and suggestion.trend_score > 60:
            if suggestion.implementation_effort_estimate and suggestion.implementation_effort_estimate < 40:
                classification = "quick_win"
            else:
                classification = "strategic"
        elif suggestion.trend_score and suggestion.trend_score > 40:
            classification = "strategic"
        
        suggestion.classification = classification
        
        # Decision recommendation
        recommendation = "pending"
        if classification == "quick_win" and suggestion.risk_level != "high":
            recommendation = "accept"
        elif suggestion.risk_level == "high" or (suggestion.trend_score and suggestion.trend_score < 30):
            recommendation = "denied"
        
        suggestion.decision_recommendation = recommendation
        
        return suggestion

    def get_operator_review(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top suggestions with full explanation for operator review.
        
        Returns list of dicts with suggestion + explanation + recommendation.
        """
        from capability_suggestion import SuggestionStatus
        
        all_suggestions = self.store.list_all(status=SuggestionStatus.NEW, include_archived=False)
        
        reviewed = []
        for s in all_suggestions:
            # Generate explanation
            self.generate_explanation(s)
            
            # Build review entry
            review = {
                "suggestion": s.to_dict(),
                "explanation": {
                    "why_surfaced": s.why_surfaced,
                    "supporting_signals": s.supporting_signals_summary,
                    "improvement_targets": s.improvement_targets,
                    "effort_estimate": s.implementation_effort_estimate,
                    "risk_level": s.risk_level,
                    "classification": s.classification,
                },
                "recommendation": {
                    "decision": s.decision_recommendation,
                    "priority": s.priority,
                    "trend_score": getattr(s, 'trend_score', None),
                },
            }
            reviewed.append(review)
        
        # Sort by decision_recommendation (accept first), then by priority
        def sort_key(r):
            rec = r["recommendation"]["decision"]
            order = {"accept": 0, "pending": 1, "denied": 2, "snoozed": 3}
            return (order.get(rec, 4), -r["recommendation"]["priority"])
        
        reviewed.sort(key=sort_key)
        
        return reviewed[:limit]


if __name__ == "__main__":
    main()
