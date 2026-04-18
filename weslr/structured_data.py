"""Weslr Structured Data Understanding (v1)

Context-aware structured data (JSON, YAML, CSV) understanding for Weslr.
Produces contextual summaries and relevant excerpts, not raw dumps.

Architecture:
  - StructuredData - Core class for structured data understanding
  - Supported types: JSON, YAML, CSV
  - Safe parsing only - no code execution

Safety Boundaries:
  - No code execution from data content
  - Path traversal protection
  - Max file size limit (10MB)
  - Max output size limit (50KB)
  - Structured data only - no arbitrary file types
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .context import ContextLabel


__all__ = [
    "StructuredData",
    "StructuredDataError",
    "create_structured_data",
    "supported_structured_types",
]


# Supported structured data file extensions
supported_structured_types: List[str] = [
    ".json",
    ".yaml",
    ".yml",
    ".csv",
]


class StructuredDataError(Exception):
    """Raised when structured data understanding fails."""
    pass


class StructuredData:
    """Context-aware structured data understanding for Weslr.
    
    Usage:
        from weslr.structured_data import create_structured_data
        
        sd = create_structured_data()
        result = sd.understand("/path/to/data.json", "What is this?")
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize structured data understanding.
        
        Args:
            workspace_dir: Workspace directory for path validation
        """
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_output_chars = 50000  # 50KB
    
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
    
    def _is_supported_type(self, ext: str) -> bool:
        """Check if extension is supported."""
        return ext in supported_structured_types
    
    def _assess_relevance(
        self,
        structured_data: Dict[str, Any],
        user_query: str,
        task_context: Dict[str, Any],
    ) -> tuple[str, str]:
        """Assess relevance of structured data to user query and task."""
        if not structured_data:
            return "none", "No structured data available"
        
        # Flatten dict for text search
        def flatten(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, str]:
            items = []
            if isinstance(d, dict):
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten(v, new_key, sep).items())
                    elif isinstance(v, list):
                        items.append((new_key, str(v)))
                    else:
                        items.append((new_key, str(v)))
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    new_key = f"{parent_key}[{i}]"
                    if isinstance(v, dict):
                        items.extend(flatten(v, new_key, sep).items())
                    elif isinstance(v, list):
                        items.append((new_key, str(v)))
                    else:
                        items.append((new_key, str(v)))
            return dict(items)
        
        flat_data = flatten(structured_data)
        text_lower = " ".join(flat_data.values()).lower()
        query_lower = user_query.lower() if user_query else ""
        task_type = task_context.get("type", "")
        task_focus = task_context.get("focus", "")
        
        # Check if query terms appear in data
        if query_lower:
            query_words = [w for w in query_lower.split() if len(w) > 2]
            matching_words = [w for w in query_words if w in text_lower]
            
            if matching_words:
                return "high", f"Query terms found in data: {', '.join(matching_words[:3])}"
        
        # Check task context relevance
        if task_type:
            task_terms = [task_type.lower(), task_focus.lower()]
            matching = [t for t in task_terms if t and t in text_lower]
            
            if matching:
                return "high", f"Task-relevant content found: {', '.join(matching)}"
        
        # Default: medium relevance if data exists
        return "medium", "Structured data available, no specific query match"
    
    def _summarize_structure(
        self,
        data: Any,
        max_depth: int = 3,
        indent: int = 0,
    ) -> str:
        """Create a compact summary of structured data structure."""
        if indent > max_depth:
            return "... [nested structure truncated]"
        
        if isinstance(data, dict):
            if not data:
                return "{}"
            items = []
            for k, v in list(data.items())[:10]:  # Limit to first 10 keys
                if isinstance(v, (dict, list)):
                    summary = self._summarize_structure(v, max_depth, indent + 1)
                    items.append(f"{k}: {summary}")
                else:
                    val_str = str(v)[:50]
                    if len(str(v)) > 50:
                        val_str = val_str[:47] + "..."
                    items.append(f"{k}: {val_str}")
            if len(data) > 10:
                items.append("... [and more]")
            return "{" + ", ".join(items) + "}"
        elif isinstance(data, list):
            if not data:
                return "[]"
            if len(data) > 5:
                items = [str(d)[:50] for d in data[:3]]
                items.append("... [and more]")
                return "[" + ", ".join(items) + "]"
            return "[" + ", ".join(str(d)[:50] for d in data) + "]"
        else:
            val_str = str(data)[:50]
            if len(str(data)) > 50:
                val_str = val_str[:47] + "..."
            return val_str
    
    def understand(
        self,
        filepath: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Understand structured data file in context.
        
        Args:
            filepath: Path to file (must be within workspace)
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dict with understanding result
        """
        # Validate path
        if not self._is_safe_path(filepath, self.workspace_dir):
            raise StructuredDataError(
                f"Path traversal attempt: {filepath} is outside workspace"
            )
        
        # Check file exists
        if not os.path.exists(filepath):
            raise StructuredDataError(f"File not found: {filepath}")
        
        # Check it's a file, not a directory
        if os.path.isdir(filepath):
            raise StructuredDataError(f"Is a directory, not a file: {filepath}")
        
        # Check file size
        try:
            size = os.path.getsize(filepath)
            if size > self.max_file_size:
                raise StructuredDataError(
                    f"File too large: {size} bytes (max {self.max_file_size})"
                )
        except Exception as e:
            raise StructuredDataError(f"Failed to check file size: {e}")
        
        # Read file
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            raise StructuredDataError(f"Failed to read file: {e}")
        
        # Truncate if too large
        if len(content) > self.max_output_chars:
            content = content[:self.max_output_chars] + "\n... [truncated]"
        
        # Parse based on extension
        ext = self._get_file_extension(filepath)
        parsed_data = None
        parse_error = None
        
        try:
            if ext == ".json":
                parsed_data = json.loads(content)
            elif ext in (".yaml", ".yml"):
                try:
                    import yaml
                    parsed_data = yaml.safe_load(content)
                except ImportError:
                    raise StructuredDataError(
                        "PyYAML not installed. Install with: pip install pyyaml"
                    )
            elif ext == ".csv":
                parsed_data = self._parse_csv(content)
            else:
                raise StructuredDataError(f"Unsupported file type: {ext}")
        except Exception as e:
            parse_error = str(e)
        
        # Assess relevance
        relevance, relevance_reason = self._assess_relevance(
            parsed_data or {},
            user_query,
            task_context or {},
        )
        
        # Create structured output
        result = {
            "file_type": ext,
            "category": "structured",
            "relevance": relevance,
            "relevance_reason": relevance_reason,
            "metadata": {
                "source_file": Path(filepath).name,
                "file_size": size if os.path.exists(filepath) else 0,
                "parsed_successfully": parse_error is None,
                "parse_error": parse_error,
            },
            "safety": {
                "injection_risk": "low",
                "content_type": "structured",
            },
        }
        
        # Add parsed data if successful
        if parsed_data is not None:
            result["parsed_data"] = parsed_data
            result["summary"] = self._summarize_structure(parsed_data)
            
            # Get relevant fields based on query
            relevant_fields = self._extract_relevant_fields(
                parsed_data,
                user_query,
                task_context or {},
            )
            result["relevant_fields"] = relevant_fields
            
            # Get structured output for chat
            result["structured_output"] = self._format_structured_output(
                parsed_data,
                user_query,
                task_context or {},
            )
        
        return result
    
    def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse CSV content to list of dicts."""
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)
    
    def _extract_relevant_fields(
        self,
        data: Dict[str, Any],
        user_query: str,
        task_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract fields relevant to user query and task."""
        if not data or not isinstance(data, dict):
            return {}
        
        query_lower = user_query.lower() if user_query else ""
        task_type = task_context.get("type", "")
        task_focus = task_context.get("focus", "")
        
        relevant = {}
        
        # Direct key matching
        for key, value in data.items():
            key_lower = key.lower()
            if query_lower and any(w in key_lower for w in query_lower.split() if len(w) > 2):
                relevant[key] = value
            elif task_focus and task_focus.lower() in key_lower:
                relevant[key] = value
        
        # If nothing found, return top-level keys
        if not relevant:
            relevant = {k: v for k, v in list(data.items())[:5]}
        
        return relevant
    
    def _format_structured_output(
        self,
        data: Any,
        user_query: str,
        task_context: Dict[str, Any],
    ) -> str:
        """Format structured data for chat output."""
        parts = []
        
        # Header
        if isinstance(data, dict):
            parts.append(f"[STRUCTURED DATA - {len(data)} key(s)]")
        elif isinstance(data, list):
            parts.append(f"[STRUCTURED DATA - {len(data)} item(s)]")
        else:
            parts.append("[STRUCTURED DATA]")
        
        # Query reference
        if user_query:
            parts.append(f"User: \"{user_query}\"")
        
        # Summary
        summary = self._summarize_structure(data)
        parts.append(f"\nStructure summary:")
        parts.append(summary)
        
        # Relevant fields
        relevant = self._extract_relevant_fields(data, user_query, task_context)
        if relevant:
            parts.append(f"\nRelevant fields:")
            for k, v in relevant.items():
                parts.append(f"  {k}: {str(v)[:100]}")
        
        return "\n".join(parts)


def create_structured_data(workspace_dir: str = None) -> StructuredData:
    """Create a structured data understanding instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        
    Returns:
        StructuredData instance
    """
    return StructuredData(workspace_dir=workspace_dir)
