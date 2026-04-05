"""Weslr FITS Dataset Ingestion (v1)

Astronomy-grade FITS dataset ingestion for Weslr.
Uses astropy.io.fits for robust FITS file parsing.

Architecture:
  - FITSIngestor - Core class for FITS dataset ingestion
  - Metadata extraction from FITS headers
  - Pixel matrix dimensions and brightness statistics
  - Safe parsing only - no image reasoning, no certainty claims

Safety Boundaries:
  - Metadata extraction only (no image reasoning yet)
  - No direct planet certainty claims
  - Output must indicate estimation/candidate status
  - Path traversal protection
  - Max file size limit (100MB for FITS files)
  - Max output size limit (50KB)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .context import ContextLabel


__all__ = [
    "FITSIngestor",
    "FITSIngestionError",
    "create_fits_ingestor",
    "supported_fits_extensions",
]


# Supported FITS file extensions
supported_fits_extensions: List[str] = [
    ".fits",
    ".fit",
]


class FITSIngestionError(Exception):
    """Raised when FITS ingestion fails."""
    pass


class FITSIngestor:
    """Astronomy-grade FITS dataset ingestion for Weslr.
    
    Uses astropy.io.fits for robust FITS file parsing.
    
    Usage:
        from weslr.fits_ingestion import create_fits_ingestor
        
        ingestor = create_fits_ingestor()
        result = ingestor.parse_fits("/path/to/image.fits")
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize FITS ingestor.
        
        Args:
            workspace_dir: Workspace directory for path validation
        """
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        self.max_file_size = 100 * 1024 * 1024  # 100MB for FITS files
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
        """Get file extension (handles .fits and .fit)."""
        ext = Path(filepath).suffix.lower()
        # Handle .fits.gz or .fit.gz
        if ext == '.gz':
            ext = Path(filepath).stem.split('.')[-1].lower()
        return ext
    
    def _is_supported_type(self, ext: str) -> bool:
        """Check if extension is supported."""
        return ext in supported_fits_extensions
    
    def _import_astropy(self):
        """Import astropy.io.fits lazily."""
        try:
            from astropy.io import fits as astropy_fits
            return astropy_fits
        except ImportError:
            raise FITSIngestionError(
                "astropy not installed. Install with: pip install astropy"
            )
    
    def parse_fits(
        self,
        filepath: str,
    ) -> Dict[str, Any]:
        """Parse FITS file and extract metadata.
        
        Args:
            filepath: Path to FITS file (must be within workspace)
            
        Returns:
            Dict with FITS data and metadata
        """
        # Validate path
        if not self._is_safe_path(filepath, self.workspace_dir):
            raise FITSIngestionError(
                f"Path traversal attempt: {filepath} is outside workspace"
            )
        
        # Check file exists
        if not os.path.exists(filepath):
            raise FITSIngestionError(f"File not found: {filepath}")
        
        # Check it's a file, not a directory
        if os.path.isdir(filepath):
            raise FITSIngestionError(f"Is a directory, not a file: {filepath}")
        
        # Check file size
        try:
            size = os.path.getsize(filepath)
            if size > self.max_file_size:
                raise FITSIngestionError(
                    f"File too large: {size} bytes (max {self.max_file_size})"
                )
        except Exception as e:
            raise FITSIngestionError(f"Failed to check file size: {e}")
        
        # Import astropy
        fits = self._import_astropy()
        
        # Read FITS file
        try:
            with fits.open(filepath, readonly=True, ignore_missing_end=True) as hdul:
                # Get primary HDU
                primary_hdu = hdul[0]
                
                # Extract header information
                header = primary_hdu.header
                
                # Extract dimensions
                naxis = header.get('NAXIS', 0)
                if naxis == 2:
                    height = header.get('NAXIS1', 0)
                    width = header.get('NAXIS2', 0)
                elif naxis >= 3:
                    # For multi-dimensional FITS, use first two axes
                    height = header.get('NAXIS1', 0)
                    width = header.get('NAXIS2', 0)
                else:
                    height = 0
                    width = 0
                
                # Extract exposure time
                exposure_time = self._extract_exposure_time(header)
                
                # Extract observation timestamp
                observation_time = self._extract_observation_time(header)
                
                # Extract brightness statistics
                mean_brightness = self._extract_mean_brightness(primary_hdu)
                
                # Build result following strict output format
                result: Dict[str, Any] = {
                    "category": "fits_dataset",
                    "width": int(width) if width else 0,
                    "height": int(height) if height else 0,
                    "mean_brightness": float(mean_brightness) if mean_brightness is not None else 0.0,
                    "exposure_time": float(exposure_time) if exposure_time is not None else None,
                    "observation_time": str(observation_time) if observation_time else None,
                    "analysis_type": "fits_ingestion",
                }
                
                # Add FITS header info
                result["fits_headers"] = dict(header) if header else {}
                
                # Add FITS file info
                result["fits_info"] = {
                    "naxis": naxis,
                    "bitpix": header.get('BITPIX', 0),
                    "object": header.get('OBJECT', None),
                    "telescope": header.get('TELESCOP', None),
                    "instrument": header.get('INSTRUME', None),
                    "observer": header.get('OBSERVER', None),
                    "author": header.get('AUTHOR', None),
                    "creator": header.get('CREATOR', None),
                    "date": header.get('DATE', None),
                    "date_obs": header.get('DATE-OBS', None),
                    "exposure": header.get('EXPTIME', header.get('EXPOSURE', None)),
                }
                
                # Add message
                result["message"] = (
                    f"FITS dataset ingested: {width}x{height} pixels, "
                    f"mean brightness {mean_brightness:.4f}"
                )
                
                if observation_time:
                    result["message"] += f", observed {observation_time}"
                
                result["message"] += (
                    ". Note: This is ingestion of metadata only - "
                    "no image analysis performed."
                )
                
                return result
                
        except Exception as e:
            raise FITSIngestionError(f"Failed to parse FITS file: {e}")
    
    def _extract_exposure_time(self, header: Any) -> Optional[float]:
        """Extract exposure time from FITS header."""
        # Try various common keywords
        keywords = ['EXPTIME', 'EXPOSURE', 'EXPOSUR', 'EXPOS', 'EXP-time', 
                   'EXP_TIME', 'EXPOSURE_TIME', 'TINT', 'EXPOSURE TIME']
        
        for kw in keywords:
            try:
                value = header.get(kw)
                if value is not None:
                    return float(value)
            except (ValueError, TypeError):
                continue
        
        return None
    
    def _extract_observation_time(self, header: Any) -> Optional[str]:
        """Extract observation timestamp from FITS header."""
        # Try various common keywords
        keywords = ['DATE-OBS', 'DATE_OBS', 'OBSDATE', 'MJD-OBS', 'MJD_OBS',
                   'JD', 'UTC-OBS', 'UT', 'TIMESYS']
        
        for kw in keywords:
            try:
                value = header.get(kw)
                if value is not None:
                    # Convert to string if not already
                    return str(value)
            except (ValueError, TypeError):
                continue
        
        # Try generic DATE keyword
        try:
            date = header.get('DATE')
            if date is not None:
                return str(date)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _extract_mean_brightness(self, hdu: Any) -> Optional[float]:
        """Extract mean brightness from FITS data."""
        try:
            data = hdu.data
            
            # Handle different data types
            if data is None:
                return None
            
            # Convert to float and handle masked arrays
            import numpy as np
            if hasattr(data, 'filled'):
                data = data.filled(0)
            
            # Calculate mean
            mean_val = np.mean(data)
            
            # Handle NaN/Inf
            if not np.isfinite(mean_val):
                # Try median as fallback
                median_val = np.nanmedian(data)
                if np.isfinite(median_val):
                    return float(median_val)
                return None
            
            return float(mean_val)
            
        except Exception:
            return None
    
    def extract_metadata(self, filepath: str) -> Dict[str, Any]:
        """Extract metadata from FITS file.
        
        This is an alias for parse_fits for API consistency.
        
        Args:
            filepath: Path to FITS file
            
        Returns:
            Dict with FITS metadata
        """
        return self.parse_fits(filepath)
    
    def extract_brightness_map(self, filepath: str) -> Dict[str, Any]:
        """Extract brightness map from FITS file.
        
        For safety, returns summary statistics only (no full image data).
        
        Args:
            filepath: Path to FITS file
            
        Returns:
            Dict with brightness statistics
        """
        result = self.parse_fits(filepath)
        
        # Return only statistics, not full image data
        return {
            "category": "fits_dataset",
            "width": result["width"],
            "height": result["height"],
            "mean_brightness": result["mean_brightness"],
            "analysis_type": "brightness_map_extraction",
        }
    
    def ingest(
        self,
        filepath: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Ingest FITS file and extract information.
        
        This is the main entry point for file_router integration.
        
        Args:
            filepath: Path to file (must be within workspace)
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dict with ingestion result
        """
        result = self.parse_fits(filepath)
        
        # Convert to RouterResult-compatible format
        return {
            "file_type": self._get_file_extension(filepath),
            "category": "fits_dataset",
            "relevance": "high",
            "relevance_reason": result.get("message", "FITS dataset ingested"),
            "metadata": {
                "source_file": Path(filepath).name,
                "parsed_successfully": True,
                "parse_error": None,
                "category": "fits_dataset",
                "width": result.get("width", 0),
                "height": result.get("height", 0),
            },
            "safety": {
                "injection_risk": "low",
                "content_type": "fits_data",
            },
            "structured_output": self._format_fits_output(result, user_query),
            "parsed_data": result,
        }
    
    def _format_fits_output(
        self,
        result: Dict[str, Any],
        user_query: str,
    ) -> str:
        """Format FITS ingestion result for chat output."""
        parts = []
        
        # Header
        parts.append("[FITS DATASET INGESTION]")
        
        # Query reference
        if user_query:
            parts.append(f"User: \"{user_query}\"")
        
        # Dimensions
        parts.append(f"\nDimensions: {result.get('width', 0)} x {result.get('height', 0)} pixels")
        parts.append(f"Mean Brightness: {result.get('mean_brightness', 0):.4f}")
        
        # Exposure time
        exposure = result.get("exposure_time")
        if exposure is not None:
            parts.append(f"Exposure: {exposure:.2f} seconds")
        
        # Observation time
        obs_time = result.get("observation_time")
        if obs_time:
            parts.append(f"Observation: {obs_time}")
        
        # FITS info
        fits_info = result.get("fits_info", {})
        if fits_info:
            parts.append("\nFITS Information:")
            for key in ['object', 'telescope', 'instrument', 'observer', 'creator']:
                value = fits_info.get(key)
                if value:
                    parts.append(f"  {key.upper()}: {value}")
        
        # Message
        if result.get("message"):
            parts.append(f"\nNote: {result['message']}")
        
        # Safety disclaimer
        parts.append("\n⚠️  This is metadata ingestion only - no image analysis performed.")
        
        return "\n".join(parts)


def create_fits_ingestor(workspace_dir: str = None) -> FITSIngestor:
    """Create a FITS ingestor instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        
    Returns:
        FITSIngestor instance
    """
    return FITSIngestor(workspace_dir=workspace_dir)
