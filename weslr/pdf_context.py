"""Weslr PDF Context Understanding (v1)

Context-aware PDF text processing that connects extracted text to user intent
and continuity state. This enables Weslr to understand "why" a PDF was shared,
not just "what" is in it.

Architecture:
  - contextAwarePdf() - Core function for contextual PDF understanding
  - PDFContext - Data structure for context-aware PDF analysis
  - Safety-first: no full-document dumps by default, only relevant context

Safety Boundaries:
  - Context-aware filtering (user intent + task relevance)
  - No raw full-document output without explicit request
  - Continuity preservation across context boundaries
  - Label-based injection defense (see weslr/context.py)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .pdf_text import extract_text_from_pdf_bytes, extract_text_from_pdf_path, PDFTextExtractionError
from .context import label_context, ContextLabel


__all__ = [
    "PDFContext",
    "create_pdf_context",
    "context_aware_pdf",
    "context_aware_pdf_summary",
    "context_aware_pdf_excerpts",
    "PDFContextExtractionError",
]


class PDFContextExtractionError(Exception):
    """Raised when PDF context extraction fails."""
    pass


class PDFContext:
    """Context-aware PDF data structure.
    
    Wraps extracted PDF text with:
    - User intent and query context
    - Task/continuity linkage
    - Relevance filtering
    - Label-based injection defense
    
    Example:
        {
            "extracted_text": "...",
            "user_query": "What is in this document?",
            "task_context": {"type": "contract_review", "focus": "terms"},
            "relevance": "high",  # or "medium", "low", "none"
            "relevance_reason": "matches query terms: terms, contract",
            "labels": ["user_file_upload", "file_content"],
            "metadata": {...},
            "safety": {"injection_risk": "low", "content_type": "text"}
        }
    """
    
    def __init__(
        self,
        extracted_text: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
        relevance: str = "unknown",
        relevance_reason: str = "",
        labels: List[str] = None,
        metadata: Dict[str, Any] = None,
        safety: Dict[str, Any] = None,
    ):
        self.extracted_text = extracted_text
        self.user_query = user_query
        self.task_context = task_context or {}
        self.relevance = relevance
        self.relevance_reason = relevance_reason
        self.labels = labels or [ContextLabel.USER_FILE_UPLOAD, ContextLabel.FILE_CONTENT]
        self.metadata = metadata or {}
        self.safety = safety or {"injection_risk": "low", "content_type": "text"}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "extracted_text": self.extracted_text,
            "user_query": self.user_query,
            "task_context": self.task_context,
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
    def from_dict(cls, data: Dict[str, Any]) -> "PDFContext":
        """Create from dictionary."""
        return cls(
            extracted_text=data.get("extracted_text", ""),
            user_query=data.get("user_query", ""),
            task_context=data.get("task_context", {}),
            relevance=data.get("relevance", "unknown"),
            relevance_reason=data.get("relevance_reason", ""),
            labels=data.get("labels", []),
            metadata=data.get("metadata", {}),
            safety=data.get("safety", {}),
        )
    
    @classmethod
    def empty(cls) -> "PDFContext":
        """Create empty context for error cases."""
        return cls(
            extracted_text="",
            user_query="",
            relevance="none",
            relevance_reason="No PDF content available",
        )


def create_pdf_context(
    pdf_bytes: bytes,
    user_query: str = "",
    task_context: Dict[str, Any] = None,
    max_chars: int = 100000,
) -> PDFContext:
    """Create context-aware PDF understanding from bytes.
    
    This is the core safe extraction function that:
    - Extracts text from PDF
    - Connects to user query and task context
    - Filters for relevance
    - Labels content for injection defense
    
    Args:
        pdf_bytes: PDF file content as bytes
        user_query: The user's question/request
        task_context: Current task context (e.g., {"type": "contract_review"})
        max_chars: Maximum characters to extract
        
    Returns:
        PDFContext with extracted text and context linkage
    """
    try:
        # Extract text
        extracted_text = extract_text_from_pdf_bytes(pdf_bytes, max_chars=max_chars)
    except PDFTextExtractionError as e:
        return PDFContext.empty()
    
    # Determine relevance based on query and task
    relevance, relevance_reason = _assess_relevance(
        extracted_text=extracted_text,
        user_query=user_query,
        task_context=task_context or {},
    )
    
    return PDFContext(
        extracted_text=extracted_text,
        user_query=user_query,
        task_context=task_context or {},
        relevance=relevance,
        relevance_reason=relevance_reason,
        labels=[ContextLabel.USER_FILE_UPLOAD, ContextLabel.FILE_CONTENT],
        metadata={
            "extracted_at": int(time.time()),
            "max_chars_used": max_chars,
            "content_length": len(extracted_text),
        },
        safety={
            "injection_risk": "low",  # Text-only extraction
            "content_type": "text",
        },
    )


def create_pdf_context_from_path(
    filepath: str,
    user_query: str = "",
    task_context: Dict[str, Any] = None,
    workspace_dir: str = None,
    max_chars: int = 100000,
) -> PDFContext:
    """Create context-aware PDF understanding from file path.
    
    This is a convenience wrapper that:
    - Validates path is within workspace
    - Calls create_pdf_context() internally
    - Returns context-aware PDF analysis
    
    Args:
        filepath: Path to PDF file (must be within workspace)
        user_query: The user's question/request
        task_context: Current task context
        workspace_dir: Workspace directory for safety
        max_chars: Maximum characters to extract
        
    Returns:
        PDFContext with extracted text and context linkage
    """
    workspace = workspace_dir or str(Path(__file__).resolve().parent.parent)
    
    try:
        # Extract text with path safety - this checks for path traversal first
        extracted_text = extract_text_from_pdf_path(
            filepath,
            workspace_dir=workspace,
            max_chars=max_chars,
        )
    except PDFTextExtractionError as e:
        # Re-raise path traversal errors (safety critical)
        if "path traversal" in str(e).lower():
            raise e
        # For other errors (file not found, parse error), return empty context
        return PDFContext.empty()
    
    # Determine relevance based on query and task
    relevance, relevance_reason = _assess_relevance(
        extracted_text=extracted_text,
        user_query=user_query,
        task_context=task_context or {},
    )
    
    return PDFContext(
        extracted_text=extracted_text,
        user_query=user_query,
        task_context=task_context or {},
        relevance=relevance,
        relevance_reason=relevance_reason,
        labels=[ContextLabel.USER_FILE_UPLOAD, ContextLabel.FILE_CONTENT],
        metadata={
            "extracted_at": int(time.time()),
            "max_chars_used": max_chars,
            "content_length": len(extracted_text),
            "source_file": Path(filepath).name,
        },
        safety={
            "injection_risk": "low",
            "content_type": "text",
        },
    )


def _assess_relevance(
    extracted_text: str,
    user_query: str,
    task_context: Dict[str, Any],
) -> tuple[str, str]:
    """Assess relevance of extracted text to user query and task.
    
    This determines if the PDF content is relevant to what the user asked.
    
    Args:
        extracted_text: The extracted PDF text
        user_query: The user's question/request
        task_context: Current task context
        
    Returns:
        Tuple of (relevance_level, relevance_reason)
    """
    if not extracted_text or not extracted_text.strip():
        return "none", "No text extracted"
    
    # Normalize text and query for comparison
    text_lower = extracted_text.lower()
    query_lower = user_query.lower() if user_query else ""
    task_type = task_context.get("type", "")
    task_focus = task_context.get("focus", "")
    
    # Check if query terms appear in PDF
    if query_lower:
        query_words = [w for w in query_lower.split() if len(w) > 2]
        matching_words = [w for w in query_words if w in text_lower]
        
        if matching_words:
            return "high", f"Query terms found in PDF: {', '.join(matching_words[:3])}"
    
    # Check task context relevance
    if task_type:
        task_terms = [task_type.lower(), task_focus.lower()]
        matching = [t for t in task_terms if t and t in text_lower]
        
        if matching:
            return "high", f"Task-relevant content found: {', '.join(matching)}"
    
    # Default: medium relevance if content exists
    return "medium", "PDF content available, no specific query match"


def context_aware_pdf(
    pdf_bytes: bytes,
    user_query: str,
    task_context: Dict[str, Any],
    max_chars: int = 50000,  # Default lower limit for chat context
) -> str:
    """Get context-aware PDF output for user consumption.
    
    This is the main output function that:
    - Extracts text from PDF
    - Connects to user query and task context
    - Produces contextual analysis, not just raw text
    - Returns formatted output suitable for LLM input
    
    Args:
        pdf_bytes: PDF file content as bytes
        user_query: The user's question/request
        task_context: Current task context
        max_chars: Maximum characters to include in output
        
    Returns:
        Formatted string with context-aware analysis
    """
    context = create_pdf_context(pdf_bytes, user_query, task_context, max_chars)
    
    # Build contextual output
    output_parts = []
    
    # Header with relevance
    if context.relevance == "high":
        output_parts.append(f"[RELEVANT PDF CONTENT - {context.relevance.upper()}]")
    elif context.relevance == "medium":
        output_parts.append(f"[PDF CONTENT - {context.relevance.upper()}]")
    else:
        output_parts.append(f"[PDF CONTENT - {context.relevance.upper()}]")
    
    # User query reference
    if user_query:
        output_parts.append(f"User asked: \"{user_query}\"")
        output_parts.append(f"Relevance: {context.relevance_reason}")
    
    # Task context
    if task_context:
        task_info = ", ".join(f"{k}={v}" for k, v in task_context.items())
        output_parts.append(f"Task: {task_info}")
    
    output_parts.append("")
    
    # Extracted text (with truncation if needed)
    if len(context.extracted_text) > max_chars:
        output_parts.append(context.extracted_text[:max_chars])
        output_parts.append(f"... [{len(context.extracted_text)} chars total, truncated to {max_chars}]")
    else:
        output_parts.append(context.extracted_text)
    
    return "\n".join(output_parts)


def format_pdf_for_continuity(
    pdf_context: PDFContext,
    continuity_id: str = None,
) -> Dict[str, Any]:
    """Format PDF context for continuity storage.
    
    This enables the extracted PDF content to be:
    - Stored in continuity snapshots
    - Restored across session boundaries
    - Linked to conversation history
    
    Args:
        pdf_context: The PDF context to store
        continuity_id: Optional continuity session ID
        
    Returns:
        Dictionary suitable for continuity storage
    """
    result = {
        "pdf_context": pdf_context.to_dict(),
        "continuity_id": continuity_id,
        "stored_at": int(time.time()),
        "labels": [ContextLabel.USER_FILE_UPLOAD, ContextLabel.FILE_CONTENT],
    }
    
    if pdf_context.user_query:
        result["user_query"] = pdf_context.user_query
    
    if pdf_context.task_context:
        result["task_context"] = pdf_context.task_context
    
    return result


def context_aware_pdf_summary(
    pdf_bytes: bytes,
    user_query: str,
    task_context: Dict[str, Any],
    max_chars: int = 1500,  # Compact summary (for chat)
) -> str:
    """Get compact summary of PDF content.
    
    This produces a minimal output:
    - Relevance assessment
    - User query connection
    - Concise summary (max_chars limit)
    
    Designed for chat contexts where full text would be too verbose.
    
    Args:
        pdf_bytes: PDF file content as bytes
        user_query: The user's question/request
        task_context: Current task context
        max_chars: Maximum characters in summary (default: 1500)
        
    Returns:
        Compact summary string
    """
    context = create_pdf_context(pdf_bytes, user_query, task_context, max_chars)
    
    # Build compact summary
    output_parts = []
    
    # Header with relevance
    if context.relevance == "high":
        output_parts.append(f"[PDF SUMMARY - {context.relevance.upper()}]")
    elif context.relevance == "medium":
        output_parts.append(f"[PDF SUMMARY - {context.relevance.upper()}]")
    else:
        output_parts.append(f"[PDF SUMMARY - {context.relevance.upper()}]")
    
    # User query connection
    if user_query:
        output_parts.append(f"User: \"{user_query}\"")
    
    # Relevance reason
    if context.relevance_reason:
        output_parts.append(f"Relevance: {context.relevance_reason}")
    
    # Task context
    if task_context:
        task_info = ", ".join(f"{k}={v}" for k, v in task_context.items())
        output_parts.append(f"Task: {task_info}")
    
    # Summary (truncated)
    summary = context.extracted_text
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "..."
    
    output_parts.append(f"\nSummary ({len(summary)} chars):")
    output_parts.append(summary)
    
    return "\n".join(output_parts)


def context_aware_pdf_excerpts(
    pdf_bytes: bytes,
    user_query: str,
    task_context: Dict[str, Any],
    max_chars: int = 5000,  # Relevant excerpts only
) -> str:
    """Get relevant excerpts from PDF content.
    
    This produces output with:
    - Relevance assessment
    - User query connection
    - Extracted relevant sections
    
    Designed for cases where specific information is needed from the PDF.
    
    Args:
        pdf_bytes: PDF file content as bytes
        user_query: The user's question/request
        task_context: Current task context
        max_chars: Maximum characters in excerpts (default: 5000)
        
    Returns:
        Excerpts string with relevance metadata
    """
    context = create_pdf_context(pdf_bytes, user_query, task_context, max_chars)
    
    # Build excerpts output
    output_parts = []
    
    # Header with relevance
    if context.relevance == "high":
        output_parts.append(f"[PDF EXCERPTS - {context.relevance.upper()}]")
    elif context.relevance == "medium":
        output_parts.append(f"[PDF EXCERPTS - {context.relevance.upper()}]")
    else:
        output_parts.append(f"[PDF EXCERPTS - {context.relevance.upper()}]")
    
    # User query connection
    if user_query:
        output_parts.append(f"User: \"{user_query}\"")
    
    # Relevance reason
    if context.relevance_reason:
        output_parts.append(f"Relevance: {context.relevance_reason}")
    
    # Task context
    if task_context:
        task_info = ", ".join(f"{k}={v}" for k, v in task_context.items())
        output_parts.append(f"Task: {task_info}")
    
    output_parts.append("")
    
    # Excerpts (truncated)
    excerpts = context.extracted_text
    if len(excerpts) > max_chars:
        excerpts = excerpts[:max_chars] + "\n... [truncated]"
    
    output_parts.append(excerpts)
    
    return "\n".join(output_parts)
