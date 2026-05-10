"""Weslr Archive Package Ingestion (v1)

Read-only archive/package manifest inspection for Weslr.
Uses stdlib zipfile/tarfile only.

Safety Boundaries:
  - No extraction to disk
  - No execution
  - No nested parsing
  - Metadata/manifest summary only
  - Bounded output
"""

from __future__ import annotations

import os
import re
import tarfile
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, Iterable, List, Tuple

__all__ = [
    "ArchiveIngestionError",
    "ArchiveIngestor",
    "create_archive_ingestor",
    "supported_archive_extensions",
    "inspect_archive_package",
]

supported_archive_extensions = [".zip", ".tar", ".tgz", ".tar.gz"]

_MAX_FILE_SIZE = 250 * 1024 * 1024
_MAX_ENTRIES = 50
_MAX_TOP_LEVELS = 20
_MAX_EXTENSIONS = 20


class ArchiveIngestionError(Exception):
    """Raised when archive inspection fails."""


class ArchiveIngestor:
    def __init__(self, workspace_dir: str | None = None):
        self.workspace_dir = workspace_dir or str(Path(__file__).resolve().parent.parent)

    def _is_safe_path(self, filepath: str, workspace_dir: str) -> bool:
        try:
            workspace = Path(workspace_dir).resolve()
            path = Path(filepath).resolve()
            return str(path).startswith(str(workspace) + os.sep) or path == workspace
        except Exception:
            return False

    def _archive_format(self, filepath: str) -> str:
        name = Path(filepath).name.lower()
        if name.endswith(".tar.gz") or name.endswith(".tgz"):
            return "tar"
        if name.endswith(".tar"):
            return "tar"
        if name.endswith(".zip"):
            return "zip"
        raise ArchiveIngestionError(f"Unsupported archive type: {filepath}")

    def inspect(self, filepath: str) -> Dict[str, Any]:
        if not self._is_safe_path(filepath, self.workspace_dir):
            raise ArchiveIngestionError(
                f"Path traversal attempt: {filepath} is outside workspace"
            )
        if not os.path.exists(filepath):
            raise ArchiveIngestionError(f"File not found: {filepath}")
        if os.path.isdir(filepath):
            raise ArchiveIngestionError(f"Is a directory, not a file: {filepath}")

        size = os.path.getsize(filepath)
        if size > _MAX_FILE_SIZE:
            raise ArchiveIngestionError(
                f"File too large: {size} bytes (max {_MAX_FILE_SIZE})"
            )

        archive_format = self._archive_format(filepath)
        if archive_format == "zip":
            return self._inspect_zip(filepath)
        return self._inspect_tar(filepath)

    def _inspect_zip(self, filepath: str) -> Dict[str, Any]:
        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                infos = zf.infolist()
                entries = [
                    {
                        "name": info.filename,
                        "is_dir": info.is_dir(),
                        "size": int(info.file_size),
                    }
                    for info in infos
                ]
        except Exception as e:
            raise ArchiveIngestionError(f"Failed to inspect ZIP archive: {e}")

        return self._build_result(filepath, "zip", entries)

    def _inspect_tar(self, filepath: str) -> Dict[str, Any]:
        try:
            with tarfile.open(filepath, "r:*") as tf:
                members = tf.getmembers()
                entries = [
                    {
                        "name": member.name,
                        "is_dir": member.isdir(),
                        "size": int(member.size or 0),
                    }
                    for member in members
                ]
        except Exception as e:
            raise ArchiveIngestionError(f"Failed to inspect TAR archive: {e}")

        return self._build_result(filepath, "tar", entries)

    def _build_result(
        self,
        filepath: str,
        archive_format: str,
        entries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        warnings: List[str] = []
        unsafe_entries: List[str] = []
        top_levels: List[str] = []
        extension_counts: Counter[str] = Counter()
        package_signals = {
            "industrial_tia_export_candidate": False,
            "scientific_dataset_bundle_candidate": False,
            "source_code_bundle_candidate": False,
            "document_bundle_candidate": False,
        }

        normalized_entries: List[Dict[str, Any]] = []
        total_size = 0
        for entry in entries:
            name = str(entry.get("name", ""))
            is_dir = bool(entry.get("is_dir", False))
            size = int(entry.get("size", 0) or 0)
            total_size += max(size, 0)

            normalized_entries.append({
                "name": name,
                "is_dir": is_dir,
                "size": size,
            })

            if self._is_unsafe_entry(name):
                unsafe_entries.append(name)

            if not name or is_dir:
                continue

            top = self._top_level(name)
            if top and top not in top_levels:
                top_levels.append(top)

            ext = Path(name).suffix.lower() or "[no_ext]"
            extension_counts[ext] += 1
            self._update_package_signals(name.lower(), package_signals)

        if unsafe_entries:
            warnings.append(
                f"Detected {len(unsafe_entries)} unsafe archive entr{'y' if len(unsafe_entries) == 1 else 'ies'}; manifest only, no extraction performed."
            )

        summary = self._format_summary(
            archive_format=archive_format,
            file_count=sum(1 for e in normalized_entries if not e["is_dir"]),
            total_size=total_size,
            top_levels=top_levels,
            extension_counts=extension_counts,
            warnings=warnings,
            entries=normalized_entries,
            package_signals=package_signals,
        )

        return {
            "type": "archive_package",
            "archive_format": archive_format,
            "read_only": True,
            "file_count": sum(1 for e in normalized_entries if not e["is_dir"]),
            "total_uncompressed_size": total_size,
            "entries": normalized_entries[:_MAX_ENTRIES],
            "top_level_directories": top_levels[:_MAX_TOP_LEVELS],
            "extension_counts": dict(extension_counts.most_common(_MAX_EXTENSIONS)),
            "warnings": warnings,
            "unsafe_entries": unsafe_entries[:_MAX_ENTRIES],
            "unsafe_entry_count": len(unsafe_entries),
            "package_hints": [k for k, v in package_signals.items() if v],
            "summary": summary,
        }

    def _format_summary(
        self,
        archive_format: str,
        file_count: int,
        total_size: int,
        top_levels: List[str],
        extension_counts: Counter[str],
        warnings: List[str],
        entries: List[Dict[str, Any]],
        package_signals: Dict[str, bool],
    ) -> str:
        parts = [
            f"[ARCHIVE_PACKAGE] format={archive_format}",
            "read_only: true",
            f"file_count: {file_count}",
            f"total_uncompressed_size: {total_size}",
        ]
        if top_levels:
            parts.append("top_level_directories: " + ", ".join(top_levels[:_MAX_TOP_LEVELS]))
        if extension_counts:
            rendered = ", ".join(
                f"{ext}:{count}" for ext, count in extension_counts.most_common(_MAX_EXTENSIONS)
            )
            parts.append(f"extension_counts: {rendered}")
        hints = [k for k, v in package_signals.items() if v]
        if hints:
            parts.append("package_hints: " + ", ".join(hints))
        if warnings:
            parts.append("warnings: " + " | ".join(warnings))
        if entries:
            parts.append("entries:")
            for entry in entries[:_MAX_ENTRIES]:
                kind = "dir" if entry["is_dir"] else "file"
                parts.append(f"- {entry['name']} ({kind}, {entry['size']} bytes)")
        return "\n".join(parts)

    def _top_level(self, name: str) -> str:
        pure = PurePosixPath(name)
        parts = [p for p in pure.parts if p not in ("", ".")]
        if not parts:
            return ""
        return parts[0]

    def _is_unsafe_entry(self, name: str) -> bool:
        lowered = name.replace("\\", "/")
        if lowered.startswith("/"):
            return True
        if re.match(r"^[a-zA-Z]:[/\\]", name):
            return True
        parts = [p for p in PurePosixPath(lowered).parts if p not in ("", ".")]
        if any(part == ".." for part in parts):
            return True
        windows_parts = [p for p in PureWindowsPath(name).parts if p not in ("", ".")]
        if any(part == ".." for part in windows_parts):
            return True
        return False

    def _update_package_signals(self, name: str, signals: Dict[str, bool]) -> None:
        tia_markers = (
            "tia/", "plc/", "devices/", "projectdata/", "tags.json", "device.json", "export.json"
        )
        scientific_markers = (
            "structures/", ".cif", ".xyz", ".fits", ".fit", ".fts", "poscar", "contcar", "materials/"
        )
        code_markers = (
            ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", "src/", "package.json", "pyproject.toml", "setup.py"
        )
        document_markers = (
            ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".md", ".rtf"
        )

        if any(marker in name for marker in tia_markers):
            signals["industrial_tia_export_candidate"] = True
        if any(marker in name for marker in scientific_markers):
            signals["scientific_dataset_bundle_candidate"] = True
        if any(marker in name for marker in code_markers):
            signals["source_code_bundle_candidate"] = True
        if any(marker in name for marker in document_markers):
            signals["document_bundle_candidate"] = True

    def ingest(self, filepath: str, user_query: str = "", task_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        result = self.inspect(filepath)
        return {
            "file_type": self._file_type(filepath),
            "category": "archive_package",
            "relevance": "high",
            "relevance_reason": "Archive package manifest inspected",
            "metadata": {
                "source_file": Path(filepath).name,
                "parsed_successfully": True,
                "parse_error": None,
                "archive_format": result["archive_format"],
                "file_count": result["file_count"],
                "unsafe_entry_count": result["unsafe_entry_count"],
                "package_hints": result["package_hints"],
            },
            "safety": {
                "injection_risk": "low",
                "content_type": "structured",
            },
            "structured_output": result["summary"],
            "parsed_data": result,
        }

    def _file_type(self, filepath: str) -> str:
        name = Path(filepath).name.lower()
        if name.endswith(".tar.gz"):
            return ".tar.gz"
        if name.endswith(".tgz"):
            return ".tgz"
        if name.endswith(".tar"):
            return ".tar"
        return Path(filepath).suffix.lower()


def create_archive_ingestor(workspace_dir: str | None = None) -> ArchiveIngestor:
    return ArchiveIngestor(workspace_dir=workspace_dir)


def inspect_archive_package(filepath: str, workspace_dir: str | None = None) -> Dict[str, Any]:
    return create_archive_ingestor(workspace_dir=workspace_dir).inspect(filepath)
