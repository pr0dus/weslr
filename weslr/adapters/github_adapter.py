# github_adapter.py - GitHub source signal adapter
# Produces SourceSignal objects from GitHub data.
# Additive only, reversible, provenance-preserving.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try relative import first, fall back to absolute
try:
    from ..capability_ingestion import SourceSignal, SourceKind, SignalStatus
except ImportError:
    from capability_ingestion import SourceSignal, SourceKind, SignalStatus


# ============================================================================
# GITHUB SIGNAL MODEL
# ============================================================================

@dataclass
class GitHubSignal:
    """A GitHub issue or PR signal."""
    repo: str
    title: str
    url: str
    body: str
    author: Optional[str] = None
    labels: List[str] = None  # type: ignore
    stars: Optional[int] = None
    activity: Optional[int] = None
    timestamp: Optional[str] = None
    detected_capability: Optional[str] = None
    confidence: Optional[float] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []


# ============================================================================
# GITHUB ADAPTER
# ============================================================================

class GitHubAdapter:
    """Adapter for GitHub source signals."""

    def __init__(self, source_kind: SourceKind = SourceKind.GITHUB):
        """Initialize adapter.
        
        Args:
            source_kind: SourceKind enum (defaults to GITHUB)
        """
        self.source_kind = source_kind

    # --------------------------------------------------------------------------
    # FROM FILE
    # --------------------------------------------------------------------------

    def from_file(self, path: Path) -> List[SourceSignal]:
        """Load signals from a JSON file.
        
        Expected file format (simple list):
        [
          {
            "repo": "openclaw/openclaw",
            "title": "Add capability discovery radar",
            "url": "https://github.com/openclaw/openclaw/issues/1",
            "body": "We need a better way to track capabilities...",
            "author": "user123",
            "labels": ["enhancement", "feature"],
            "stars": 42,
            "activity": 15,
            "timestamp": "2026-04-05T10:30:00Z",
            "detected_capability": "capability discovery"
          }
        ]
        
        Args:
            path: Path to JSON file
            
        Returns:
            List of SourceSignal objects
        """
        import json

        signals = []
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Handle both list and single object
        if isinstance(data, dict):
            data = [data]
        
        for item in data:
            signal = self._from_dict(item)
            if signal:
                signals.append(signal)
        
        return signals

    # --------------------------------------------------------------------------
    # FROM DICT
    # --------------------------------------------------------------------------

    def from_dict(self, data: Dict[str, Any]) -> Optional[SourceSignal]:
        """Create a SourceSignal from a dict.
        
        Args:
            data: Dict with GitHub signal fields
            
        Returns:
            SourceSignal or None if invalid
        """
        try:
            # Required fields
            repo = data.get("repo", "unknown")
            title = data.get("title", "")
            url = data.get("url", "")
            body = data.get("body", "")
            
            if not title or not url:
                return None
            
            # Optional fields
            author = data.get("author")
            labels = data.get("labels", [])
            stars = data.get("stars")
            activity = data.get("activity")
            timestamp = data.get("timestamp")
            detected_capability = data.get("detected_capability")
            confidence = data.get("confidence")
            
            # Build signal
            signal = SourceSignal(
                id=f"github-{int(datetime.now(timezone.utc).timestamp())}-{abs(hash(title)) % 10000:04d}",
                source_kind=self.source_kind,
                title=title,
                url=url,
                body=body,
                snippet=body[:200] if body else None,
                tags=labels if labels else [],
                source_timestamp=timestamp,
                provenance=f"github:{repo}",
                detected_capability=detected_capability,
                confidence=confidence,
            )
            
            # Set detected_capability if present
            if detected_capability:
                signal.detected_capability = detected_capability.strip()
            
            return signal
            
        except Exception:
            return None

    def _from_dict(self, data: Dict[str, Any]) -> Optional[SourceSignal]:
        """Internal dict-to-signal converter."""
        return self.from_dict(data)

    # --------------------------------------------------------------------------
    # FROM GITHUB SIGNAL OBJECT
    # --------------------------------------------------------------------------

    def from_github_signal(self, signal: GitHubSignal) -> SourceSignal:
        """Create a SourceSignal from a GitHubSignal dataclass.
        
        Args:
            signal: GitHubSignal with all fields populated
            
        Returns:
            SourceSignal with all necessary fields
        """
        return SourceSignal(
            id=f"github-{int(datetime.now(timezone.utc).timestamp())}-{abs(hash(signal.title)) % 10000:04d}",
            source_kind=self.source_kind,
            title=signal.title,
            url=signal.url,
            body=signal.body,
            snippet=signal.body[:200] if signal.body else None,
            tags=signal.labels if signal.labels else [],
            source_timestamp=signal.timestamp,
            provenance=f"github:{signal.repo}",
            detected_capability=signal.detected_capability,
            confidence=signal.confidence,
        )

    # --------------------------------------------------------------------------
    # PARSING UTILITIES
    # --------------------------------------------------------------------------

    def extract_repo_from_url(self, url: str) -> Optional[str]:
        """Extract repo name from GitHub URL.
        
        Args:
            url: GitHub URL (issues, PRs, etc.)
            
        Returns:
            Repo name (owner/repo) or None
        """
        import re
        # github.com/owner/repo/...
        match = re.search(r"github\.com/([^/]+)/([^/]+)/", url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None

    def parse_timestamp(self, ts: str) -> Optional[str]:
        """Parse timestamp to ISO format.
        
        Args:
            ts: Input timestamp string
            
        Returns:
            ISO format timestamp or None
        """
        try:
            # Try ISO format first
            if "T" in ts:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pass
        
        try:
            # Try other common formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(ts, fmt)
                    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    continue
        except Exception:
            pass
        
        return None


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI interface for testing."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python github_adapter.py <command> [args]")
        print("Commands:")
        print("  from-file <path>")
        print("  from-dict <json>")
        sys.exit(1)
    
    command = sys.argv[1]
    adapter = GitHubAdapter()
    
    if command == "from-file":
        if len(sys.argv) < 3:
            print("Usage: python github_adapter.py from-file <path>")
            sys.exit(1)
        path = Path(sys.argv[2])
        signals = adapter.from_file(path)
        for s in signals:
            print(f"Signal: {s.title}")
            print(f"  ID: {s.id}")
            print(f"  URL: {s.url}")
            print(f"  Provenance: {s.provenance}")
            print()
    
    elif command == "from-dict":
        import json
        if len(sys.argv) < 3:
            print("Usage: python github_adapter.py from-dict <json>")
            sys.exit(1)
        data = json.loads(sys.argv[2])
        signal = adapter.from_dict(data)
        if signal:
            print(signal.to_dict())
        else:
            print("Invalid signal data")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
