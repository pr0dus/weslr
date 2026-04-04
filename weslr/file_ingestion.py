"""Weslr File Ingestion (v1)

Safe text-based document/file ingestion for Weslr.
Supports safe text-first formats for contextual understanding.

Architecture:
  - FileIngestor - Core class for file ingestion
  - supported_extensions - List of supported file extensions
  - IngestionResult - Data structure for ingestion results

Supported File Types:
  - .txt (plain text)
  - .md (markdown)
  - .json (JSON)
  - .yaml, .yml (YAML)
  - .py, .js, .ts, .java, .cpp, .c, .h (source code - text only)

Safety Boundaries:
  - Only text-based formats allowed
  - No code execution from file content
  - Path traversal protection
  - Max file size limit (10MB)
  - Max output size limit (100KB)
  - No binary data returned
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .context import ContextLabel, label_context


__all__ = [
    "FileIngestor",
    "IngestionResult",
    "IngestionError",
    "supported_extensions",
    "create_file_ingestor",
]


# Supported text-based file extensions
supported_extensions: List[str] = [
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    # Source code files (text-only, no execution)
    ".py",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".sh",
    ".bash",
    ".zsh",
    ".sql",
    ".html",
    ".xml",
    ".csv",
    ".log",
    ".ini",
    ".cfg",
    ".conf",
]


class IngestionError(Exception):
    """Raised when file ingestion fails."""
    pass


class IngestionResult:
    """Result of a file ingestion operation."""
    
    def __init__(
        self,
        file_path: str,
        file_type: str,
        content: str,
        content_type: str,
        relevance: str = "unknown",
        relevance_reason: str = "",
        labels: List[str] = None,
        metadata: Dict[str, Any] = None,
        safety: Dict[str, Any] = None,
    ):
        self.file_path = file_path
        self.file_type = file_type
        self.content = content
        self.content_type = content_type
        self.relevance = relevance
        self.relevance_reason = relevance_reason
        self.labels = labels or [ContextLabel.USER_FILE_UPLOAD, ContextLabel.FILE_CONTENT]
        self.metadata = metadata or {}
        self.safety = safety or {"injection_risk": "low", "content_type": "text"}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "file_type": self.file_type,
            "content": self.content,
            "content_type": self.content_type,
            "relevance": self.relevance,
            "relevance_reason": self.relevance_reason,
            "labels": self.labels,
            "metadata": self.metadata,
            "safety": self.safety,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IngestionResult":
        """Create from dictionary."""
        return cls(
            file_path=data.get("file_path", ""),
            file_type=data.get("file_type", ""),
            content=data.get("content", ""),
            content_type=data.get("content_type", ""),
            relevance=data.get("relevance", "unknown"),
            relevance_reason=data.get("relevance_reason", ""),
            labels=data.get("labels", []),
            metadata=data.get("metadata", {}),
            safety=data.get("safety", {}),
        )
    
    @classmethod
    def empty(cls) -> "IngestionResult":
        """Create empty result for error cases."""
        return cls(
            file_path="",
            file_type="",
            content="",
            content_type="",
            relevance="none",
            relevance_reason="No file content available",
        )


class FileIngestor:
    """Safe text-based file ingestion for Weslr.
    
    Usage:
        from weslr.file_ingestion import create_file_ingestor
        
        ingestor = create_file_ingestor()
        result = ingestor.ingest("/path/to/file.txt", "What is this?")
        
    Safety Boundaries:
        - Only text-based formats allowed
        - No code execution from file content
        - Path traversal protection
        - Max file size limit (10MB)
        - Max output size limit (100KB)
        - No binary data returned
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize file ingestor.
        
        Args:
            workspace_dir: Workspace directory for path validation
        """
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_output_chars = 100000  # 100KB
    
    def _is_safe_path(self, filepath: str, workspace_dir: str) -> bool:
        """Check if filepath is within workspace directory."""
        try:
            workspace = Path(workspace_dir).resolve()
            path = Path(filepath).resolve()
            return str(path).startswith(str(workspace) + os.sep) or path == workspace
        except Exception:
            return False
    
    def _get_file_extension(self, filepath: str) -> str:
        """Get file extension."""
        return Path(filepath).suffix.lower()
    
    def _is_supported_extension(self, ext: str) -> bool:
        """Check if extension is supported."""
        return ext in supported_extensions
    
    def _is_safe_file(self, filepath: str) -> Tuple[bool, str]:
        """Check if file is safe to ingest.
        
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check extension
        ext = self._get_file_extension(filepath)
        if not self._is_supported_extension(ext):
            return False, f"Unsupported file extension: {ext}"
        
        # Check file exists
        if not os.path.exists(filepath):
            return False, f"File not found: {filepath}"
        
        # Check it's a file, not a directory
        if os.path.isdir(filepath):
            return False, f"Is a directory, not a file: {filepath}"
        
        # Check file size
        try:
            size = os.path.getsize(filepath)
            if size > self.max_file_size:
                return False, f"File too large: {size} bytes (max {self.max_file_size})"
        except Exception as e:
            return False, f"Failed to check file size: {e}"
        
        return True, "File is safe"
    
    def _read_text_file(self, filepath: str) -> str:
        """Read text file safely.
        
        Args:
            filepath: Path to file
            
        Returns:
            File content as string
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(self.max_output_chars)
        except Exception as e:
            raise IngestionError(f"Failed to read file: {e}")
    
    def _assess_relevance(
        self,
        content: str,
        user_query: str,
        task_context: Dict[str, Any],
    ) -> Tuple[str, str]:
        """Assess relevance of content to user query and task."""
        if not content or not content.strip():
            return "none", "No content available"
        
        text_lower = content.lower()
        query_lower = user_query.lower() if user_query else ""
        task_type = task_context.get("type", "")
        task_focus = task_context.get("focus", "")
        
        # Check if query terms appear in content
        if query_lower:
            query_words = [w for w in query_lower.split() if len(w) > 2]
            matching_words = [w for w in query_words if w in text_lower]
            
            if matching_words:
                return "high", f"Query terms found in file: {', '.join(matching_words[:3])}"
        
        # Check task context relevance
        if task_type:
            task_terms = [task_type.lower(), task_focus.lower()]
            matching = [t for t in task_terms if t and t in text_lower]
            
            if matching:
                return "high", f"Task-relevant content found: {', '.join(matching)}"
        
        # Default: medium relevance if content exists
        return "medium", "File content available, no specific query match"
    
    def ingest(
        self,
        filepath: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> IngestionResult:
        """Ingest a text-based file for contextual understanding.
        
        Args:
            filepath: Path to file (must be within workspace)
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            IngestionResult with content and relevance
        """
        # Validate path
        if not self._is_safe_path(filepath, self.workspace_dir):
            raise IngestionError(
                f"Path traversal attempt: {filepath} is outside workspace"
            )
        
        # Check file is safe
        is_safe, reason = self._is_safe_file(filepath)
        if not is_safe:
            raise IngestionError(reason)
        
        # Read file
        try:
            content = self._read_text_file(filepath)
        except Exception as e:
            raise IngestionError(f"Failed to read file: {e}")
        
        # Truncate if too large
        if len(content) > self.max_output_chars:
            content = content[:self.max_output_chars] + "\n... [truncated]"
        
        # Assess relevance
        relevance, relevance_reason = self._assess_relevance(
            content, user_query, task_context or {}
        )
        
        # Get file extension
        ext = self._get_file_extension(filepath)
        
        return IngestionResult(
            file_path=filepath,
            file_type=ext,
            content=content,
            content_type="text",
            relevance=relevance,
            relevance_reason=relevance_reason,
            labels=[ContextLabel.USER_FILE_UPLOAD, ContextLabel.FILE_CONTENT],
            metadata={
                "extracted_at": int(os.path.getmtime(filepath) if os.path.exists(filepath) else 0),
                "source_file": Path(filepath).name,
                "file_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                "max_output_chars": self.max_output_chars,
            },
            safety={
                "injection_risk": "low",
                "content_type": "text",
            },
        )


def create_file_ingestor(workspace_dir: str = None) -> FileIngestor:
    """Create a file ingestor instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        
    Returns:
        FileIngestor instance
    """
    return FileIngestor(workspace_dir=workspace_dir)
