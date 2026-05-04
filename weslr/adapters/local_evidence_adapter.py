"""
WESLR Local Evidence Adapter

Reads local evidence files for the Research Work Loop V1.
Allowed paths: weslr/docs/, weslr/data/, weslr/observatory.jsonl, weslr/phase_registry.jsonl

V1: Local-only. No external calls. No web requests.
"""

import os
import json
from pathlib import Path
from typing import Optional

# Allowed base directories for evidence reading
ALLOWED_DIRECTORIES = [
    "weslr/docs",
    "weslr/data",
    ".weslr",
]

# Allowed file extensions
ALLOWED_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".csv"}

# Blocked file patterns (never read these)
BLOCKED_PATTERNS = [
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".weslr/pending_messages.jsonl",  # Don't read own output as evidence
]


class LocalEvidenceAdapter:
    """
    Reads local evidence files for research missions.

    V1 constraints:
    - Only reads from allowed directories (weslr/docs, weslr/data, .weslr)
    - Only reads allowed file types (.md, .txt, .json, .jsonl, .csv)
    - Never reads blocked patterns
    - No external calls, no web requests
    - Returns structured evidence records
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.getcwd()
        self._allowed_dirs = [os.path.join(self.workspace_root, d) for d in ALLOWED_DIRECTORIES]

    def _is_path_safe(self, rel_path: str) -> bool:
        """
        Check if a relative path is safe to read.

        Args:
            rel_path: Relative path (e.g., "docs/test.md" or ".weslr/missions.jsonl")

        Returns:
            True if safe, False if blocked
        """
        abs_path = os.path.abspath(os.path.join(self.workspace_root, rel_path))

        # Check against blocked patterns
        for pattern in BLOCKED_PATTERNS:
            if pattern in abs_path:
                return False

        # Check against allowed directories
        for allowed_dir in self._allowed_dirs:
            if abs_path.startswith(allowed_dir):
                return True

        return False

    def _has_allowed_extension(self, path: str) -> bool:
        """Check if file has an allowed extension."""
        ext = os.path.splitext(path)[1].lower()
        return ext in ALLOWED_EXTENSIONS

    def read(self, evidence_links: list[str]) -> dict[str, dict]:
        """
        Read evidence from a list of file paths/links.

        Args:
            evidence_links: List of file paths or URLs (file:// only)

        Returns:
            Dict mapping link -> evidence record with keys:
              - content: str (text content)
              - type: str (file type)
              - size: int (bytes)
              - safe: bool
              - error: str | None
        """
        results = {}

        for link in evidence_links:
            # Only handle file:// or plain paths
            if link.startswith("file://"):
                path = link[7:]
            else:
                path = link

            results[link] = self._read_single(path)

        return results

    def _read_single(self, rel_path: str) -> dict:
        """
        Read a single file safely.

        Returns:
            Evidence record dict
        """
        if not self._is_path_safe(rel_path):
            return {
                "content": "",
                "type": "unknown",
                "size": 0,
                "safe": False,
                "error": "Path not allowed",
            }

        if not self._has_allowed_extension(rel_path):
            return {
                "content": "",
                "type": "unknown",
                "size": 0,
                "safe": False,
                "error": "File type not allowed",
            }

        abs_path = os.path.join(self.workspace_root, rel_path)

        if not os.path.exists(abs_path):
            return {
                "content": "",
                "type": "unknown",
                "size": 0,
                "safe": False,
                "error": "File not found",
            }

        try:
            # Read based on file type
            ext = os.path.splitext(rel_path)[1].lower()
            if ext == ".jsonl":
                lines = []
                with open(abs_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if i >= 100:  # Limit to first 100 lines for safety
                            break
                        lines.append(line.strip())
                content = "\n".join(lines)
            elif ext == ".json":
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()

            size = os.path.getsize(abs_path)

            return {
                "content": content[:50000],  # Cap at 50k chars
                "type": ext,
                "size": size,
                "safe": True,
                "error": None,
            }
        except Exception as e:
            return {
                "content": "",
                "type": "unknown",
                "size": 0,
                "safe": False,
                "error": str(e),
            }

    def list_available(self, directory: str = "weslr/docs") -> list[str]:
        """
        List available evidence files in a directory.

        Args:
            directory: Relative directory path

        Returns:
            List of relative file paths
        """
        if not self._is_path_safe(directory):
            return []

        abs_dir = os.path.join(self.workspace_root, directory)
        if not os.path.isdir(abs_dir):
            return []

        files = []
        for root, dirs, filenames in os.walk(abs_dir):
            # Skip blocked directories
            dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", ".pytest_cache"]]

            for filename in filenames:
                if self._has_allowed_extension(filename):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, self.workspace_root)
                    files.append(rel_path)

        return sorted(files)

    def evidence_summary(self, evidence_links: list[str]) -> str:
        """
        Get a plain-text summary of available evidence.

        Args:
            evidence_links: List of evidence links

        Returns:
            Human-readable summary string
        """
        if not evidence_links:
            return "No evidence links provided."

        results = self.read(evidence_links)
        lines = []
        for link, result in results.items():
            if result["safe"]:
                lines.append(f"  {link}: {result['type']}, {result['size']} bytes")
            else:
                lines.append(f"  {link}: BLOCKED — {result['error']}")

        return "\n".join(lines) if lines else "No evidence found."