"""Weslr File Router (v1)

Unified file routing contract for Weslr.
Routes files to appropriate understanding modules based on type.

Architecture:
  - FileRouter - Main class for unified file routing
  - Supported types: PDF, text-based files, SQLite databases, scientific structure files, FITS datasets
  - Normalized result structure for downstream code

Safety Boundaries:
  - All routing through workspace directory
  - Path traversal protection
  - No code execution
  - Text-only output
  - Relevance-based filtering
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union


__all__ = [
    "FileRouter",
    "FileRouterError",
    "RouterResult",
    "create_file_router",
]


# Structured data file extensions (special handling with context-aware understanding)
STRUCTURED_EXTENSIONS = {".json", ".yaml", ".yml", ".csv"}


# Supported file extensions per category
PDF_EXTENSIONS = {".pdf"}
FITS_EXTENSIONS = {".fits", ".fit", ".fts"}
SQLITE_EXTENSIONS = {".sqlite", ".sqlite3", ".db"}
SCIENTIFIC_STRUCTURE_EXTENSIONS = {".xyz", ".cif", ".vasp"}
SCIENTIFIC_STRUCTURE_FILENAMES = {"POSCAR", "CONTCAR"}
TEXT_EXTENSIONS = {
    ".txt", ".md",
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".hpp",
    ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".sh", ".bash", ".zsh",
    ".sql", ".html", ".xml", ".log",
    ".ini", ".cfg", ".conf",
}


class FileRouterError(Exception):
    """Raised when file routing fails."""
    pass


class RouterResult:
    """Result of a file routing operation.
    
    Normalized result structure for downstream code.
    """
    
    def __init__(
        self,
        file_type: str,
        category: str,  # "pdf", "text"
        content: str,
        content_type: str,
        relevance: str = "unknown",
        relevance_reason: str = "",
        read_only: bool = True,
        labels: list = None,
        metadata: Dict[str, Any] = None,
        safety: Dict[str, Any] = None,
    ):
        self.file_type = file_type
        self.category = category
        self.content = content
        self.content_type = content_type
        self.relevance = relevance
        self.relevance_reason = relevance_reason
        self.read_only = read_only
        self.labels = labels or ["user_file_upload", "file_content"]
        self.metadata = metadata or {}
        self.safety = safety or {"injection_risk": "low", "content_type": "text"}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_type": self.file_type,
            "category": self.category,
            "content": self.content,
            "content_type": self.content_type,
            "relevance": self.relevance,
            "relevance_reason": self.relevance_reason,
            "read_only": self.read_only,
            "labels": self.labels,
            "metadata": self.metadata,
            "safety": self.safety,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RouterResult":
        """Create from dictionary."""
        return cls(
            file_type=data.get("file_type", ""),
            category=data.get("category", ""),
            content=data.get("content", ""),
            content_type=data.get("content_type", ""),
            relevance=data.get("relevance", "unknown"),
            relevance_reason=data.get("relevance_reason", ""),
            read_only=data.get("read_only", True),
            labels=data.get("labels", []),
            metadata=data.get("metadata", {}),
            safety=data.get("safety", {}),
        )
    
    @classmethod
    def empty(cls) -> "RouterResult":
        """Create empty result for error cases."""
        return cls(
            file_type="",
            category="",
            content="",
            content_type="",
            relevance="none",
            relevance_reason="No file content available",
            read_only=True,
        )


class StructuredDataResultAdapter:
    """Adapter to convert StructuredData output to RouterResult format."""
    
    @staticmethod
    def to_router_result(sd_result: Dict[str, Any]) -> RouterResult:
        """Convert structured data result to RouterResult."""
        content = sd_result.get("structured_output", "")
        if not content:
            content = sd_result.get("summary", "")
        
        return RouterResult(
            file_type=sd_result.get("file_type", ""),
            category="structured",
            content=content,
            content_type="structured",
            relevance=sd_result.get("relevance", "unknown"),
            relevance_reason=sd_result.get("relevance_reason", ""),
            read_only=sd_result.get("read_only", True),
            labels=["user_file_upload", "file_content", "structured_data"],
            metadata={
                "source_file": sd_result.get("metadata", {}).get("source_file", ""),
                "parsed_successfully": sd_result.get("metadata", {}).get("parsed_successfully", False),
                "parse_error": sd_result.get("metadata", {}).get("parse_error"),
                "category": "structured",
                "read_only": sd_result.get("read_only", True),
            },
            safety={
                "injection_risk": "low",
                "content_type": "structured",
            },
        )


class FileRouter:
    """Unified file router for Weslr.
    
    Routes files to appropriate understanding modules:
    - PDF files → PDF understanding (weslr/pdf_context.py)
    - Structured data (JSON/YAML/CSV) → Structured data understanding (weslr/structured_data.py)
    - Text-based files → Generic ingestion (weslr/file_ingestion.py)
    - SQLite databases → Read-only SQLite inspection (weslr/sqlite_ingestion.py)
    - Scientific structure files → Read-only structure inspection (weslr/scientific_structure_ingestion.py)
    - FITS files → Read-only FITS metadata ingestion (weslr/fits_ingestion.py)
    
    Usage:
        from weslr.file_router import create_file_router
        
        router = create_file_router()
        result = router.route("/path/to/file.pdf", "What is this?")
        result = router.route("/path/to/data.json", "What does this contain?")
        result = router.route("/path/to/file.txt", "What is this?")
        
    Safety Boundaries:
        - All routing through workspace directory
        - Path traversal protection
        - No code execution
        - Text-only output
        - Relevance-based filtering
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize file router.
        
        Args:
            workspace_dir: Workspace directory for path validation
        """
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        self._pdf_context = None
        self._structured_data = None
        self._file_ingestion = None
        self._fits_ingestion = None
        self._sqlite_ingestion = None
        self._scientific_structure_ingestion = None
    
    def _import_modules(self):
        """Import required modules lazily."""
        if self._pdf_context is None:
            import weslr.pdf_context as pdf_context
            self._pdf_context = pdf_context
        
        if self._structured_data is None:
            import weslr.structured_data as structured_data
            self._structured_data = structured_data
        
        if self._file_ingestion is None:
            import weslr.file_ingestion as file_ingestion
            self._file_ingestion = file_ingestion

        if self._fits_ingestion is None:
            import weslr.fits_ingestion as fits_ingestion
            self._fits_ingestion = fits_ingestion

        if self._sqlite_ingestion is None:
            import weslr.sqlite_ingestion as sqlite_ingestion
            self._sqlite_ingestion = sqlite_ingestion

        if self._scientific_structure_ingestion is None:
            import weslr.scientific_structure_ingestion as scientific_structure_ingestion
            self._scientific_structure_ingestion = scientific_structure_ingestion
    
    def _get_file_extension(self, filepath: str) -> str:
        """Get file extension."""
        return Path(filepath).suffix.lower()

    def _is_scientific_structure_file(self, filepath: str) -> bool:
        path = Path(filepath)
        return (
            path.suffix.lower() in SCIENTIFIC_STRUCTURE_EXTENSIONS
            or path.name in SCIENTIFIC_STRUCTURE_FILENAMES
        )
    
    def _is_safe_path(self, filepath: str, workspace_dir: str) -> bool:
        """Check if filepath is within workspace directory."""
        try:
            workspace = Path(workspace_dir).resolve()
            path = Path(filepath).resolve()
            return str(path).startswith(str(workspace) + os.sep) or path == workspace
        except Exception:
            return False
    
    def route(
        self,
        filepath: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> RouterResult:
        """Route a file to appropriate understanding module.
        
        Args:
            filepath: Path to file (must be within workspace)
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            RouterResult with normalized structure
        """
        # Validate path
        if not self._is_safe_path(filepath, self.workspace_dir):
            raise FileRouterError(
                f"Path traversal attempt: {filepath} is outside workspace"
            )
        
        # Check file exists
        if not os.path.exists(filepath):
            raise FileRouterError(f"File not found: {filepath}")
        
        # Get file extension
        ext = self._get_file_extension(filepath)
        
        # Determine category and route
        if ext in PDF_EXTENSIONS:
            return self._route_pdf(filepath, user_query, task_context)
        elif ext in FITS_EXTENSIONS:
            return self._route_fits(filepath, user_query, task_context)
        elif ext in SQLITE_EXTENSIONS:
            return self._route_sqlite(filepath, user_query, task_context)
        elif self._is_scientific_structure_file(filepath):
            return self._route_scientific_structure(filepath, user_query, task_context)
        elif ext in STRUCTURED_EXTENSIONS:
            return self._route_structured(filepath, user_query, task_context)
        elif ext in TEXT_EXTENSIONS:
            return self._route_text(filepath, user_query, task_context)
        else:
            raise FileRouterError(
                f"Unsupported file type: {ext}. "
                f"Supported: {PDF_EXTENSIONS | FITS_EXTENSIONS | TEXT_EXTENSIONS | STRUCTURED_EXTENSIONS | SQLITE_EXTENSIONS | SCIENTIFIC_STRUCTURE_EXTENSIONS} plus {SCIENTIFIC_STRUCTURE_FILENAMES}"
            )
    
    def _route_pdf(
        self,
        filepath: str,
        user_query: str,
        task_context: Dict[str, Any],
    ) -> RouterResult:
        """Route PDF file to PDF understanding."""
        self._import_modules()
        
        try:
            with open(filepath, 'rb') as f:
                pdf_bytes = f.read()
            
            ctx = self._pdf_context.create_pdf_context(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context or {},
                max_chars=100000,
            )
            
            if not ctx.extracted_text:
                return RouterResult.empty()
            
            # Get summary output as normalized content
            output = self._pdf_context.context_aware_pdf_summary(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context or {},
                max_chars=100000,
            )
            
            ext = self._get_file_extension(filepath)
            return RouterResult(
                file_type=ext,
                category="pdf",
                content=output,
                content_type="text",
                relevance=ctx.relevance,
                relevance_reason=ctx.relevance_reason,
                read_only=True,
                labels=["user_file_upload", "file_content"],
                metadata={
                    "source_file": Path(filepath).name,
                    "content_length": len(ctx.extracted_text),
                    "max_chars_used": 100000,
                    "read_only": True,
                },
                safety={"injection_risk": "low", "content_type": "text"},
            )
        except Exception as e:
            raise FileRouterError(f"PDF routing failed: {e}")
    
    def _route_fits(
        self,
        filepath: str,
        user_query: str,
        task_context: Dict[str, Any],
    ) -> RouterResult:
        """Route FITS file to read-only FITS ingestion."""
        self._import_modules()

        try:
            ingestor = self._fits_ingestion.create_fits_ingestor(
                workspace_dir=self.workspace_dir
            )
            result = ingestor.ingest(filepath, user_query, task_context or {})
            parsed = result.get("parsed_data", {})
            fits_info = parsed.get("fits_info", {}) if isinstance(parsed, dict) else {}

            return RouterResult(
                file_type=result.get("file_type", self._get_file_extension(filepath)),
                category="fits",
                content=result.get("structured_output", result.get("relevance_reason", "")),
                content_type="structured",
                relevance=result.get("relevance", "high"),
                relevance_reason=result.get("relevance_reason", "FITS dataset inspection available"),
                read_only=True,
                labels=["user_file_upload", "file_content", "fits_dataset"],
                metadata={
                    "source_file": Path(filepath).name,
                    "read_only": True,
                    "parsed_successfully": result.get("metadata", {}).get("parsed_successfully", False),
                    "parse_error": result.get("metadata", {}).get("parse_error"),
                    "width": parsed.get("width", result.get("metadata", {}).get("width", 0)),
                    "height": parsed.get("height", result.get("metadata", {}).get("height", 0)),
                    "analysis_type": parsed.get("analysis_type"),
                    "naxis": fits_info.get("naxis"),
                    "object": fits_info.get("object"),
                    "telescope": fits_info.get("telescope"),
                    "instrument": fits_info.get("instrument"),
                },
                safety={"injection_risk": "low", "content_type": "structured"},
            )
        except self._fits_ingestion.FITSIngestionError as e:
            raise FileRouterError(f"FITS routing failed: {e}")
        except Exception as e:
            raise FileRouterError(f"Unexpected FITS routing error: {e}")

    def _route_text(
        self,
        filepath: str,
        user_query: str,
        task_context: Dict[str, Any],
    ) -> RouterResult:
        """Route text-based file to generic ingestion."""
        self._import_modules()
        
        try:
            ingestor = self._file_ingestion.create_file_ingestor(
                workspace_dir=self.workspace_dir
            )
            
            result = ingestor.ingest(filepath, user_query, task_context or {})
            
            return RouterResult(
                file_type=result.file_type,
                category="text",
                content=result.content,
                content_type="text",
                relevance=result.relevance,
                relevance_reason=result.relevance_reason,
                read_only=True,
                labels=["user_file_upload", "file_content"],
                metadata={
                    "source_file": Path(filepath).name,
                    "content_length": len(result.content),
                    "read_only": True,
                },
                safety={"injection_risk": "low", "content_type": "text"},
            )
        except self._file_ingestion.IngestionError as e:
            raise FileRouterError(f"Text routing failed: {e}")
        except Exception as e:
            raise FileRouterError(f"Unexpected routing error: {e}")
    
    def _route_structured(
        self,
        filepath: str,
        user_query: str,
        task_context: Dict[str, Any],
    ) -> RouterResult:
        """Route structured data file to structured data understanding."""
        self._import_modules()
        
        try:
            sd = self._structured_data.create_structured_data(
                workspace_dir=self.workspace_dir
            )
            
            result = sd.understand(filepath, user_query, task_context or {})
            
            return StructuredDataResultAdapter.to_router_result(result)
        except self._structured_data.StructuredDataError as e:
            raise FileRouterError(f"Structured data routing failed: {e}")
        except Exception as e:
            raise FileRouterError(f"Unexpected structured data error: {e}")

    def _route_sqlite(
        self,
        filepath: str,
        user_query: str,
        task_context: Dict[str, Any],
    ) -> RouterResult:
        """Route SQLite file to read-only SQLite inspection."""
        self._import_modules()

        try:
            result = self._sqlite_ingestion.inspect_sqlite_database(
                filepath,
                workspace_dir=self.workspace_dir,
            )
            return RouterResult(
                file_type=self._get_file_extension(filepath),
                category="sqlite",
                content=result.get("structured_output", result.get("summary", "")),
                content_type="structured",
                relevance="high",
                relevance_reason="SQLite database inspection available",
                read_only=True,
                labels=["user_file_upload", "file_content", "sqlite_database"],
                metadata={
                    "source_file": Path(filepath).name,
                    "category": "sqlite",
                    "read_only": True,
                    "table_count": result.get("table_count", 0),
                    "parsed_successfully": result.get("metadata", {}).get("parsed_successfully", False),
                    "parse_error": result.get("metadata", {}).get("parse_error"),
                },
                safety={"injection_risk": "low", "content_type": "structured"},
            )
        except self._sqlite_ingestion.SQLiteInspectionError as e:
            raise FileRouterError(f"SQLite routing failed: {e}")
        except Exception as e:
            raise FileRouterError(f"Unexpected SQLite routing error: {e}")

    def _route_scientific_structure(
        self,
        filepath: str,
        user_query: str,
        task_context: Dict[str, Any],
    ) -> RouterResult:
        """Route scientific structure file to read-only inspection."""
        self._import_modules()

        try:
            result = self._scientific_structure_ingestion.inspect_scientific_structure_file(
                filepath,
                workspace_dir=self.workspace_dir,
            )
            return RouterResult(
                file_type=self._get_file_extension(filepath) or Path(filepath).name,
                category="scientific_structure",
                content=result.get("structured_output", result.get("summary", "")),
                content_type="structured",
                relevance="high",
                relevance_reason="Scientific structure inspection available",
                read_only=True,
                labels=["user_file_upload", "file_content", "scientific_structure"],
                metadata={
                    "source_file": Path(filepath).name,
                    "category": "scientific_structure",
                    "read_only": True,
                    "atom_count": result.get("atom_count", 0),
                    "formula": result.get("formula", ""),
                    "parsed_successfully": result.get("metadata", {}).get("parsed_successfully", False),
                    "parse_error": result.get("metadata", {}).get("parse_error"),
                },
                safety={"injection_risk": "low", "content_type": "structured"},
            )
        except self._scientific_structure_ingestion.ScientificStructureInspectionError as e:
            raise FileRouterError(f"Scientific structure routing failed: {e}")
        except Exception as e:
            raise FileRouterError(f"Unexpected scientific structure routing error: {e}")


def create_file_router(workspace_dir: str = None) -> FileRouter:
    """Create a file router instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        
    Returns:
        FileRouter instance
    """
    return FileRouter(workspace_dir=workspace_dir)


def _is_structured_extension(ext: str) -> bool:
    """Check if extension is a structured data type."""
    return ext in STRUCTURED_EXTENSIONS


def _is_text_extension(ext: str) -> bool:
    """Check if extension is a text-based type."""
    return ext in TEXT_EXTENSIONS
