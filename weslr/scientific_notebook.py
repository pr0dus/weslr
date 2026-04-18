"""Weslr Scientific Notebook Continuity (v1)

Scientific notebook continuity layer for astronomy and scientific workflows.
Parses markdown scientific observation logs and generates continuity markdown.

Architecture:
  - ScientificNotebook - Core class for scientific notebook parsing
  - Metadata extraction from markdown YAML frontmatter
  - Notes, confidence, star target, timestamps extraction
  - Auto-generated candidate continuity markdown
  - Safe markdown parsing only - no code execution

Safety Boundaries:
  - Markdown .md files only (no code execution)
  - No direct planet certainty claims
  - Output must indicate parsing/candidate status
  - Path traversal protection
  - Max file size limit (10MB)
  - Max output size limit (50KB)
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .context import ContextLabel


__all__ = [
    "ScientificNotebook",
    "ScientificNotebookError",
    "create_scientific_notebook",
    "supported_notebook_extensions",
]


# Supported scientific notebook file extensions
supported_notebook_extensions: List[str] = [
    ".md",
]


class ScientificNotebookError(Exception):
    """Raised when scientific notebook parsing fails."""
    pass


class ScientificNotebook:
    """Scientific notebook continuity layer for Weslr.
    
    Parses markdown scientific observation logs and generates continuity markdown.
    
    Usage:
        from weslr.scientific_notebook import create_scientific_notebook
        
        notebook = create_scientific_notebook()
        result = notebook.parse_markdown("/path/to/observation.md")
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize scientific notebook parser.
        
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
        return ext in supported_notebook_extensions
    
    def parse_markdown(
        self,
        filepath: str,
    ) -> Dict[str, Any]:
        """Parse scientific observation markdown file.
        
        Args:
            filepath: Path to markdown file (must be within workspace)
            
        Returns:
            Dict with parsed markdown content
        """
        # Validate path
        if not self._is_safe_path(filepath, self.workspace_dir):
            raise ScientificNotebookError(
                f"Path traversal attempt: {filepath} is outside workspace"
            )
        
        # Check file exists
        if not os.path.exists(filepath):
            raise ScientificNotebookError(f"File not found: {filepath}")
        
        # Check it's a file, not a directory
        if os.path.isdir(filepath):
            raise ScientificNotebookError(f"Is a directory, not a file: {filepath}")
        
        # Check file size
        try:
            size = os.path.getsize(filepath)
            if size > self.max_file_size:
                raise ScientificNotebookError(
                    f"File too large: {size} bytes (max {self.max_file_size})"
                )
        except Exception as e:
            raise ScientificNotebookError(f"Failed to check file size: {e}")
        
        # Read markdown file
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            raise ScientificNotebookError(f"Failed to read file: {e}")
        
        # Truncate if too large
        if len(content) > self.max_output_chars:
            content = content[:self.max_output_chars] + "\n... [truncated]"
        
        # Parse markdown content
        result = self._parse_markdown_content(content, filepath)
        
        return result
    
    def _parse_markdown_content(
        self,
        content: str,
        filepath: str,
    ) -> Dict[str, Any]:
        """Parse markdown content with YAML frontmatter.
        
        Handles:
        - YAML frontmatter (--- blocks)
        - Metadata fields (star, date, confidence, notes)
        - Continuity markdown generation
        """
        # Default result
        result: Dict[str, Any] = {
            "category": "scientific_notebook",
            "target_star": None,
            "observation_date": None,
            "notes": "",
            "confidence": None,
            "continuity_linked": False,
            "analysis_type": "markdown_parsing",
        }
        
        # Extract YAML frontmatter if present
        frontmatter = self._extract_frontmatter(content)
        
        if frontmatter:
            # Parse metadata from frontmatter
            result["target_star"] = frontmatter.get("target", frontmatter.get("star", frontmatter.get("target_star")))
            result["observation_date"] = frontmatter.get("date", frontmatter.get("observation_date"))
            
            # Parse confidence (handle percentages and floats)
            conf = frontmatter.get("confidence")
            if conf is not None:
                result["confidence"] = self._parse_confidence(conf)
            
            # Check for continuity link
            if "continuity" in frontmatter:
                result["continuity_linked"] = True
        
        # Extract notes from markdown body (everything after frontmatter)
        notes = self._extract_notes(content)
        if notes:
            result["notes"] = notes
        
        # If no notes in frontmatter, use body content
        if not result.get("body") and notes:
            result["body"] = notes
        
        # Generate continuity markdown
        continuity_markdown = self._generate_continuity_markdown(result)
        result["continuity_markdown"] = continuity_markdown
        
        # Build final result
        result["message"] = (
            f"Scientific notebook parsed: {filepath}"
        )
        
        if result.get("target_star"):
            result["message"] += f" - Target: {result['target_star']}"
        
        if result.get("continuity_linked"):
            result["message"] += " - Continuity linked"
        
        result["message"] += (
            ". Note: This is markdown parsing only - no certainty claims made."
        )
        
        return result
    
    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from markdown content.
        
        Handles both --- and +++ delimited frontmatter.
        """
        frontmatter = {}
        
        # Try to find frontmatter blocks
        patterns = [
            (r'^---\n(.*?)\n---', re.DOTALL),
            (r'^\+\+\+\n(.*?)\n\+\+\+', re.DOTALL),
        ]
        
        for pattern, flags in patterns:
            match = re.match(pattern, content, flags)
            if match:
                fm_content = match.group(1)
                frontmatter = self._parse_yaml_like(fm_content)
                break
        
        return frontmatter
    
    def _parse_yaml_like(self, content: str) -> Dict[str, Any]:
        """Parse YAML-like key-value format."""
        result = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Handle key: value format
            if ':' in line:
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Try to convert to appropriate type
                result[key] = self._parse_value(value)
        
        return result
    
    def _parse_value(self, value: str) -> Any:
        """Parse a YAML-like value to appropriate Python type."""
        if not value:
            return None
        
        # Remove quotes
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try boolean
        if value.lower() in ('true', 'yes', 'on'):
            return True
        elif value.lower() in ('false', 'no', 'off'):
            return False
        
        return value
    
    def _parse_confidence(self, value: Any) -> Optional[float]:
        """Parse confidence value (handles percentages and floats)."""
        if value is None:
            return None
        
        # If already a float/int, use directly
        if isinstance(value, (int, float)):
            val = float(value)
            # Normalize to 0-1 range
            if val > 1:
                val = val / 100  # Assume percentage
            return min(max(val, 0.0), 1.0)
        
        # If string, try to parse
        if isinstance(value, str):
            value = value.strip()
            
            # Handle percentage
            if value.endswith('%'):
                try:
                    num = float(value[:-1])
                    return min(max(num / 100, 0.0), 1.0)
                except ValueError:
                    pass
            
            # Try direct float
            try:
                num = float(value)
                if num > 1:
                    num = num / 100
                return min(max(num, 0.0), 1.0)
            except ValueError:
                pass
        
        return None
    
    def _extract_notes(self, content: str) -> str:
        """Extract notes body from markdown content."""
        # Remove frontmatter if present
        frontmatter_patterns = [
            r'^---\n.*?\n---\n',
            r'^\+\+\+\n.*?\n\+\+\+\n',
        ]
        
        body = content
        for pattern in frontmatter_patterns:
            body = re.sub(pattern, '', body, flags=re.DOTALL)
        
        # Clean up extra whitespace
        body = body.strip()
        
        return body
    
    def _generate_continuity_markdown(
        self,
        parsed_data: Dict[str, Any],
    ) -> str:
        """Generate continuity markdown for linking observations.
        
        Creates structured markdown that links related observations.
        """
        lines = []
        
        # Header
        lines.append("# Scientific Continuity Log")
        lines.append("")
        lines.append(f"**Category:** {parsed_data.get('category', 'scientific_notebook')}")
        lines.append(f"**Analysis Type:** {parsed_data.get('analysis_type', 'markdown_parsing')}")
        lines.append("")
        
        # Target star
        target = parsed_data.get('target_star')
        if target:
            lines.append(f"**Target Star:** {target}")
        else:
            lines.append("**Target Star:** (not specified)")
        lines.append("")
        
        # Observation date
        date = parsed_data.get('observation_date')
        if date:
            lines.append(f"**Observation Date:** {date}")
        else:
            lines.append("**Observation Date:** (not specified)")
        lines.append("")
        
        # Confidence
        conf = parsed_data.get('confidence')
        if conf is not None:
            lines.append(f"**Confidence:** {conf:.2%}")
        else:
            lines.append("**Confidence:** (not specified)")
        lines.append("")
        
        # Continuity link status
        linked = parsed_data.get('continuity_linked', False)
        lines.append(f"**Continuity Linked:** {'Yes' if linked else 'No'}")
        lines.append("")
        
        # Notes summary
        notes = parsed_data.get('notes', '')
        if notes:
            lines.append("## Notes Summary")
            lines.append("")
            # Truncate long notes
            if len(notes) > 1000:
                notes = notes[:1000] + "... [truncated]"
            lines.append(notes)
        else:
            lines.append("## Notes Summary")
            lines.append("")
            lines.append("(no notes found)")
        lines.append("")
        
        # Continuity warning
        lines.append("---")
        lines.append("")
        lines.append("*This is auto-generated continuity markdown for linking scientific observations.*")
        lines.append("*No planet certainty claims - candidate detection only.*")
        
        return "\n".join(lines)
    
    def generate_continuity_markdown(
        self,
        target_star: str,
        observation_date: str,
        confidence: Optional[float] = None,
        notes: str = "",
        continuity_linked: bool = False,
    ) -> str:
        """Generate continuity markdown from raw parameters.
        
        Args:
            target_star: Target star name
            observation_date: Observation date
            confidence: Confidence level (0-1 or 0-100)
            notes: Observation notes
            continuity_linked: Whether this is linked to previous observations
            
        Returns:
            Generated markdown string
        """
        parsed_data = {
            "category": "scientific_notebook",
            "target_star": target_star,
            "observation_date": observation_date,
            "confidence": confidence,
            "notes": notes,
            "continuity_linked": continuity_linked,
        }
        
        return self._generate_continuity_markdown(parsed_data)
    
    def analyze(
        self,
        filepath: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Analyze scientific notebook file.
        
        This is the main entry point for file_router integration.
        
        Args:
            filepath: Path to file (must be within workspace)
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dict with analysis result
        """
        result = self.parse_markdown(filepath)
        
        # Convert to RouterResult-compatible format
        return {
            "file_type": self._get_file_extension(filepath),
            "category": "scientific_notebook",
            "relevance": "high",
            "relevance_reason": result.get("message", "Scientific notebook parsed"),
            "metadata": {
                "source_file": Path(filepath).name,
                "parsed_successfully": True,
                "parse_error": None,
                "category": "scientific_notebook",
                "target_star": result.get("target_star"),
                "observation_date": result.get("observation_date"),
            },
            "safety": {
                "injection_risk": "low",
                "content_type": "markdown_text",
            },
            "structured_output": result.get("continuity_markdown", ""),
            "parsed_data": result,
        }


def create_scientific_notebook(workspace_dir: str = None) -> ScientificNotebook:
    """Create a scientific notebook parser instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        
    Returns:
        ScientificNotebook instance
    """
    return ScientificNotebook(workspace_dir=workspace_dir)
