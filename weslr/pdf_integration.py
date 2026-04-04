"""Weslr PDF Integration Contract (v1)

Integration contract for future chat/file routing to access PDF understanding
without exposing raw implementation details.

This module defines the stable API surface for:
- PDF extraction
- Context-aware understanding
- Output formatting (summary/excerpts/full)

Architecture:
  - PDFIntegration - Main class for PDF operations
  - OutputMode enum for mode selection
  - Safe factory functions for integration

Safety Boundaries:
  - No raw file system access - paths validated internally
  - No code execution - text-only extraction only
  - No full-document dumps by default
  - Relevance-based filtering
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union


__all__ = [
    "OutputMode",
    "PDFIntegration",
    "create_pdf_integration",
]


class OutputMode(Enum):
    """Output mode for PDF extraction."""
    SUMMARY = "summary"     # Compact summary (1500 chars)
    EXCERPTS = "excerpts"   # Relevant excerpts (5000 chars)
    FULL = "full"           # Full content (50000 chars)


class PDFIntegration:
    """Stable API for PDF understanding operations.
    
    This is the integration contract for future chat/file routing.
    It hides implementation details and provides a stable API surface.
    
    Usage:
        from weslr.pdf_integration import create_pdf_integration
        
        pdf = create_pdf_integration()
        result = pdf.summarize("/path/to/file.pdf", "What is this?")
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize PDF integration.
        
        Args:
            workspace_dir: Workspace directory for path validation
                          (defaults to parent of this file)
        """
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        
        # Lazy import to avoid circular dependencies
        self._context = None
        self._text = None
    
    def _import_modules(self):
        """Import required modules lazily."""
        if self._context is None:
            import weslr.pdf_context as pdf_context
            self._context = pdf_context
        
        if self._text is None:
            import weslr.pdf_text as pdf_text
            self._text = pdf_text
    
    def summarize(
        self,
        pdf_path: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
        max_chars: int = 1500,
    ) -> str:
        """Get compact summary of PDF content.
        
        Args:
            pdf_path: Path to PDF file
            user_query: User's question/request
            task_context: Current task context
            max_chars: Maximum summary length
            
        Returns:
            Compact summary string
        """
        self._import_modules()
        
        try:
            # Read bytes directly to avoid encoding issues
            full_path = Path(self.workspace_dir) / pdf_path
            if not full_path.exists():
                full_path = Path(pdf_path)  # Try relative path
            
            with open(full_path, 'rb') as f:
                pdf_bytes = f.read()
            
            ctx = self._context.create_pdf_context(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context or {},
                max_chars=max_chars,
            )
            
            if not ctx.extracted_text:
                return "[PDF SUMMARY - NONE] No content available"
            
            return self._context.context_aware_pdf_summary(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context or {},
                max_chars=max_chars,
            )
        except self._text.PDFTextExtractionError as e:
            return f"[PDF ERROR] {e}"
        except Exception as e:
            return f"[PDF ERROR] Unexpected error: {e}"
    
    def get_excerpts(
        self,
        pdf_path: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
        max_chars: int = 5000,
    ) -> str:
        """Get relevant excerpts from PDF content.
        
        Args:
            pdf_path: Path to PDF file
            user_query: User's question/request
            task_context: Current task context
            max_chars: Maximum excerpt length
            
        Returns:
            Excerpts string with relevance metadata
        """
        self._import_modules()
        
        try:
            # Read bytes directly to avoid encoding issues
            full_path = Path(self.workspace_dir) / pdf_path
            if not full_path.exists():
                full_path = Path(pdf_path)  # Try relative path
            
            with open(full_path, 'rb') as f:
                pdf_bytes = f.read()
            
            ctx = self._context.create_pdf_context(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context or {},
                max_chars=max_chars,
            )
            
            if not ctx.extracted_text:
                return "[PDF EXCERPTS - NONE] No content available"
            
            return self._context.context_aware_pdf_excerpts(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context or {},
                max_chars=max_chars,
            )
        except self._text.PDFTextExtractionError as e:
            return f"[PDF ERROR] {e}"
        except Exception as e:
            return f"[PDF ERROR] Unexpected error: {e}"
    
    def get_full(
        self,
        pdf_path: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
        max_chars: int = 50000,
    ) -> str:
        """Get full content of PDF.
        
        Args:
            pdf_path: Path to PDF file
            user_query: User's question/request
            task_context: Current task context
            max_chars: Maximum content length
            
        Returns:
            Full content string with relevance metadata
        """
        self._import_modules()
        
        try:
            # Read bytes directly to avoid encoding issues
            full_path = Path(self.workspace_dir) / pdf_path
            if not full_path.exists():
                full_path = Path(pdf_path)  # Try relative path
            
            with open(full_path, 'rb') as f:
                pdf_bytes = f.read()
            
            ctx = self._context.create_pdf_context(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context or {},
                max_chars=max_chars,
            )
            
            if not ctx.extracted_text:
                return "[PDF FULL - NONE] No content available"
            
            return self._context.context_aware_pdf(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context or {},
                max_chars=max_chars,
            )
        except self._text.PDFTextExtractionError as e:
            return f"[PDF ERROR] {e}"
        except Exception as e:
            return f"[PDF ERROR] Unexpected error: {e}"
    
    def to_dict(
        self,
        pdf_path: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Get PDF context as dictionary for storage/serialization.
        
        This is useful for:
        - Continuity storage
        - JSON serialization
        - Cross-session preservation
        
        Args:
            pdf_path: Path to PDF file
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dictionary suitable for JSON storage
        """
        self._import_modules()
        
        try:
            ctx = self._context.create_pdf_context_from_path(
                pdf_path,
                user_query=user_query,
                task_context=task_context or {},
                workspace_dir=self.workspace_dir,
                max_chars=100000,  # Full context for storage
            )
            
            return {
                "extracted_text": ctx.extracted_text,
                "user_query": user_query,
                "task_context": task_context or {},
                "relevance": ctx.relevance,
                "relevance_reason": ctx.relevance_reason,
                "labels": ctx.labels,
                "safety": ctx.safety,
                "metadata": ctx.metadata,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def format_for_continuity(
        self,
        pdf_dict: Dict[str, Any],
        continuity_id: str = None,
    ) -> Dict[str, Any]:
        """Format PDF context for continuity storage.
        
        Args:
            pdf_dict: PDF context dictionary (from to_dict())
            continuity_id: Optional continuity session ID
            
        Returns:
            Dictionary suitable for continuity snapshots
        """
        self._import_modules()
        
        return self._context.format_pdf_for_continuity(
            self._context.PDFContext.from_dict(pdf_dict),
            continuity_id=continuity_id,
        )


def create_pdf_integration(workspace_dir: str = None) -> PDFIntegration:
    """Create a PDF integration instance.
    
    This is the recommended factory function for getting a PDFIntegration
    instance. It provides a stable API surface for future integration.
    
    Args:
        workspace_dir: Workspace directory for path validation
        
    Returns:
        PDFIntegration instance
    """
    return PDFIntegration(workspace_dir=workspace_dir)
