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


if __name__ == "__main__":
    main()
