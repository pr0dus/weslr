"""Weslr Materials Science Analysis (v1)

Materials/nanotechnology analysis for Weslr.
Candidate ranking for material/property datasets without simulation claims.

Architecture:
  - MaterialsAnalyzer - Core class for materials analysis
  - Supports CSV, JSON, YAML input formats
  - Detects material/property columns
  - Ranks materials against user criteria
  - Safe parsing only - no simulation, no invention claims

Safety Boundaries:
  - Structured numeric/property datasets only
  - No chemistry simulation
  - No image reasoning
  - No invention claims
  - Candidate ranking only
  - Path traversal protection
  - Max file size limit (10MB)
  - Max output size limit (50KB)
"""

from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .context import ContextLabel


__all__ = [
    "MaterialsAnalyzer",
    "MaterialsAnalysisError",
    "create_materials_analyzer",
    "supported_materials_extensions",
]


# Supported materials data file extensions
supported_materials_extensions: List[str] = [
    ".csv",
    ".json",
    ".yaml",
    ".yml",
]


class MaterialsAnalysisError(Exception):
    """Raised when materials analysis fails."""
    pass


class MaterialsAnalyzer:
    """Materials/nanotechnology analysis for Weslr.
    
    Performs candidate ranking for material datasets.
    
    Usage:
        from weslr.materials_analysis import create_materials_analyzer
        
        analyzer = create_materials_analyzer()
        result = analyzer.analyze_candidates("/path/to/materials.csv", "high thermal resistance")
    """
    
    def __init__(self, workspace_dir: str = None):
        """Initialize materials analyzer.
        
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
        return ext in supported_materials_extensions
    
    def _load_materials_data(self, filepath: str) -> List[Dict[str, Any]]:
        """Load materials data from file.
        
        Returns list of material records as dicts.
        """
        ext = self._get_file_extension(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            raise MaterialsAnalysisError(f"Failed to read file: {e}")
        
        # Truncate if too large
        if len(content) > self.max_output_chars:
            content = content[:self.max_output_chars] + "\n... [truncated]"
        
        data: List[Dict[str, Any]] = []
        
        try:
            if ext == ".csv":
                reader = csv.DictReader(io.StringIO(content))
                for row in reader:
                    # Convert numeric strings to floats
                    record = {}
                    for k, v in row.items():
                        v = v.strip() if v else ""
                        if v:
                            try:
                                record[k] = float(v)
                            except ValueError:
                                record[k] = v
                        else:
                            record[k] = None
                    data.append(record)
            elif ext == ".json":
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    data = parsed
                elif isinstance(parsed, dict):
                    # Try to find list in dict
                    for v in parsed.values():
                        if isinstance(v, list):
                            data = v
                            break
            elif ext in (".yaml", ".yml"):
                try:
                    import yaml as yaml_module
                    parsed = yaml_module.safe_load(content)
                    if isinstance(parsed, list):
                        data = parsed
                    elif isinstance(parsed, dict):
                        for v in parsed.values():
                            if isinstance(v, list):
                                data = v
                                break
                except ImportError:
                    raise MaterialsAnalysisError(
                        "PyYAML not installed. Install with: pip install pyyaml"
                    )
        except Exception as e:
            raise MaterialsAnalysisError(f"Failed to parse materials data: {e}")
        
        return data
    
    def _detect_material_columns(self, records: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Detect material identifier columns vs property columns.
        
        Returns:
            (material_columns, property_columns)
        """
        if not records:
            return [], []
        
        # Common material identifier patterns
        material_keywords = [
            'material', 'material_name', 'name', 'id', 'composition',
            'compound', 'formula', 'specimen', 'sample', 'batch'
        ]
        
        # Common property patterns
        property_keywords = [
            'property', 'value', 'strength', 'resistance', 'density',
            'thermal', 'electrical', 'mechanical', 'optical',
            'hardness', 'tensile', 'compressive', 'flexural',
            'modulus', 'conductivity', 'conductance', 'permeability',
            'elasticity', 'viscosity', 'solubility', 'absorbance'
        ]
        
        # Get all unique keys
        all_keys = set()
        for record in records:
            all_keys.update(record.keys())
        
        material_cols = []
        property_cols = []
        
        for key in all_keys:
            key_lower = key.lower()
            # Check if it's a material identifier
            is_material = any(kw in key_lower for kw in material_keywords)
            # Check if it's a property
            is_property = any(kw in key_lower for kw in property_keywords)
            
            if is_material and not is_property:
                material_cols.append(key)
            elif is_property or is_material and not any(kw in key_lower for kw in material_keywords):
                property_cols.append(key)
        
        # Default behavior: if no material column detected, use first column
        if not material_cols:
            if records:
                first_key = list(records[0].keys())[0]
                material_cols = [first_key]
        
        # If no property columns, use all non-material columns
        if not property_cols:
            for key in all_keys:
                if key not in material_cols:
                    property_cols.append(key)
        
        return material_cols, property_cols
    
    def _extract_criteria_from_query(self, query: str) -> List[str]:
        """Extract material criteria from user query.
        
        Args:
            query: User's description of desired properties
            
        Returns:
            List of criteria names
        """
        if not query:
            return ["general_performance"]
        
        query_lower = query.lower()
        criteria = []
        
        # Property keywords
        property_terms = {
            "thermal resistance": "thermal_resistance",
            "thermal conductivity": "thermal_conductivity",
            "thermal stability": "thermal_stability",
            "high strength": "tensile_strength",
            "tensile strength": "tensile_strength",
            "compressive strength": "compressive_strength",
            "hardness": "hardness",
            "density": "density",
            "lightweight": "low_density",
            "high density": "high_density",
            "electrical conductivity": "electrical_conductivity",
            "electrical resistivity": "electrical_resistivity",
            "optical properties": "optical_properties",
            "mechanical properties": "mechanical_properties",
            "flexibility": "flexibility",
            "elasticity": "elasticity",
            "viscosity": "viscosity",
            "solubility": "solubility",
            "absorbance": "absorbance",
            "biocompatibility": "biocompatibility",
            "corrosion resistance": "corrosion_resistance",
            "stability": "stability",
        }
        
        for term, criterion in property_terms.items():
            if term in query_lower:
                criteria.append(criterion)
        
        # Default if no criteria found
        if not criteria:
            criteria = ["general_performance"]
        
        return criteria
    
    def _calculate_material_score(
        self,
        material_record: Dict[str, Any],
        criteria: List[str],
        property_columns: List[str],
    ) -> float:
        """Calculate a composite score for a material.
        
        Args:
            material_record: Material data dict
            criteria: List of criteria to optimize
            property_columns: List of property columns
            
        Returns:
            Score between 0 and 1
        """
        if not material_record:
            return 0.0
        
        scores = []
        
        for criterion in criteria:
            # Try to find matching property in record
            best_match = 0.0
            criterion_lower = criterion.lower()
            
            for prop in property_columns:
                prop_lower = prop.lower()
                # Check if property matches criterion
                if criterion_lower in prop_lower or prop_lower in criterion_lower:
                    value = material_record.get(prop)
                    if isinstance(value, (int, float)):
                        # Normalize to 0-1 (assuming typical material property ranges)
                        # This is a simple normalization - can be improved
                        normalized = self._normalize_property_value(value, prop)
                        best_match = max(best_match, normalized)
                        break
            
            if best_match > 0:
                scores.append(best_match)
        
        # If no criteria matched, use average of all numeric properties
        if not scores:
            numeric_values = []
            for prop in property_columns:
                value = material_record.get(prop)
                if isinstance(value, (int, float)):
                    numeric_values.append(self._normalize_property_value(value, prop))
            
            if numeric_values:
                scores = [sum(numeric_values) / len(numeric_values)]
        
        # Return average score
        if scores:
            return sum(scores) / len(scores)
        
        return 0.0
    
    def _normalize_property_value(self, value: float, property_name: str) -> float:
        """Normalize a property value to 0-1 range.
        
        Uses heuristic based on property name.
        """
        if value is None:
            return 0.0
        
        value = float(value)
        
        # Simple normalization heuristics based on property type
        property_lower = property_name.lower()
        
        # Density: typical range 0.1-20 g/cm³
        if 'density' in property_lower:
            return min(max(value / 10, 0.0), 1.0)
        
        # Thermal conductivity: typical range 0.1-1000 W/mK
        elif 'thermal' in property_lower and 'conduct' in property_lower:
            return min(max(value / 100, 0.0), 1.0)
        
        # Electrical conductivity: typical range 1e-6-1e8 S/m
        elif 'electrical' in property_lower and 'conduct' in property_lower:
            import math
            log_val = math.log10(max(value, 1e-6))
            return min(max((log_val + 6) / 14, 0.0), 1.0)
        
        # Hardness: typical range 1-100
        elif 'hardness' in property_lower:
            return min(max(value / 100, 0.0), 1.0)
        
        # Tensile/compressive strength (check for strength without other modifiers)
        elif 'strength' in property_lower and 'tensile' not in property_lower and 'compressive' not in property_lower:
            return min(max(value / 1000, 0.0), 1.0)
        
        # Tensile strength: typical range 1-10000 MPa
        elif 'tensile' in property_lower and 'strength' in property_lower:
            return min(max(value / 1000, 0.0), 1.0)
        
        # Compressive strength
        elif 'compressive' in property_lower and 'strength' in property_lower:
            return min(max(value / 1000, 0.0), 1.0)
        
        # Generic: assume value is already normalized or use simple scaling
        else:
            return min(max(value, 0.0), 1.0)
    
    def rank_materials(
        self,
        records: List[Dict[str, Any]],
        criteria: List[str],
    ) -> List[Dict[str, Any]]:
        """Rank materials based on criteria.
        
        Args:
            records: List of material records
            criteria: List of criteria to optimize
            
        Returns:
            Sorted list of {material, score} dicts
        """
        if not records:
            return []
        
        # Detect columns
        material_cols, property_cols = self._detect_material_columns(records)
        
        # Calculate scores for each material
        scored_materials = []
        
        for record in records:
            # Get material identifier
            material_name = self._get_material_name(record, material_cols)
            
            # Calculate score
            score = self._calculate_material_score(record, criteria, property_cols)
            
            scored_materials.append({
                "material": material_name,
                "score": round(score, 4),
                "properties": {k: v for k, v in record.items() if v is not None},
            })
        
        # Sort by score descending
        scored_materials.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_materials
    
    def _get_material_name(self, record: Dict[str, Any], material_cols: List[str]) -> str:
        """Get material identifier from record."""
        if not material_cols:
            return "Material-{}".format(hash(json.dumps(record, sort_keys=True)) % 10000)
        
        for col in material_cols:
            value = record.get(col)
            if value is not None:
                return str(value)
        
        return "Unknown"
    
    def analyze_candidates(
        self,
        filepath: str,
        query: Optional[str] = None,
        task_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze materials dataset and rank candidates.
        
        Args:
            filepath: Path to materials data file
            query: User's request/requirements
            task_context: Current task context
            
        Returns:
            Dict with analysis result
        """
        # Validate path
        if not self._is_safe_path(filepath, self.workspace_dir):
            raise MaterialsAnalysisError(
                f"Path traversal attempt: {filepath} is outside workspace"
            )
        
        # Check file exists
        if not os.path.exists(filepath):
            raise MaterialsAnalysisError(f"File not found: {filepath}")
        
        # Check it's a file, not a directory
        if os.path.isdir(filepath):
            raise MaterialsAnalysisError(f"Is a directory, not a file: {filepath}")
        
        # Check file size
        try:
            size = os.path.getsize(filepath)
            if size > self.max_file_size:
                raise MaterialsAnalysisError(
                    f"File too large: {size} bytes (max {self.max_file_size})"
                )
        except Exception as e:
            raise MaterialsAnalysisError(f"Failed to check file size: {e}")
        
        # Load data
        try:
            records = self._load_materials_data(filepath)
        except MaterialsAnalysisError:
            raise
        except Exception as e:
            raise MaterialsAnalysisError(f"Failed to load materials data: {e}")
        
        if not records:
            return {
                "category": "materials_analysis",
                "top_candidate": None,
                "ranking": [],
                "criteria_used": [],
                "analysis_type": "candidate_ranking",
                "message": "No materials data found in file",
            }
        
        # Extract criteria from query
        criteria = self._extract_criteria_from_query(query or "")
        
        # Rank materials
        ranking = self.rank_materials(records, criteria)
        
        # Get top candidate
        top_candidate = None
        if ranking:
            top_candidate = ranking[0]["material"]
        
        # Build result
        result: Dict[str, Any] = {
            "category": "materials_analysis",
            "top_candidate": top_candidate,
            "ranking": ranking,
            "criteria_used": criteria,
            "analysis_type": "candidate_ranking",
            "material_count": len(records),
            "property_columns_used": self._detect_material_columns(records)[1],
        }
        
        result["message"] = (
            f"Materials analysis complete: {len(records)} materials evaluated, "
            f"top candidate: {top_candidate or 'N/A'}"
        )
        
        return result
    
    def analyze(
        self,
        filepath: str,
        user_query: str = "",
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Analyze materials file for file router integration.
        
        Args:
            filepath: Path to file (must be within workspace)
            user_query: User's question/request
            task_context: Current task context
            
        Returns:
            Dict with analysis result
        """
        result = self.analyze_candidates(filepath, user_query, task_context)
        
        # Convert to RouterResult-compatible format
        return {
            "file_type": self._get_file_extension(filepath),
            "category": "materials_analysis",
            "relevance": "high",
            "relevance_reason": result.get("message", "Materials analysis complete"),
            "metadata": {
                "source_file": Path(filepath).name,
                "parsed_successfully": result.get("material_count", 0) > 0,
                "parse_error": None,
                "category": "materials_analysis",
            },
            "safety": {
                "injection_risk": "low",
                "content_type": "material_properties",
            },
            "structured_output": self._format_materials_output(result, user_query),
            "parsed_data": result,
        }
    
    def _format_materials_output(
        self,
        result: Dict[str, Any],
        user_query: str,
    ) -> str:
        """Format materials analysis for chat output."""
        lines = []
        
        # Header
        lines.append("[MATERIALS ANALYSIS - Candidate Ranking]")
        
        # Query reference
        if user_query:
            lines.append(f"User: \"{user_query}\"")
        
        # Top candidate
        top = result.get("top_candidate")
        if top:
            lines.append(f"\nTop Candidate: {top}")
        else:
            lines.append("\nNo candidates identified")
        
        # Criteria used
        criteria = result.get("criteria_used", [])
        if criteria:
            lines.append(f"\nCriteria: {', '.join(criteria)}")
        
        # Ranking summary
        lines.append("\nRanking:")
        ranking = result.get("ranking", [])
        for i, item in enumerate(ranking[:5], 1):  # Show top 5
            lines.append(f"  {i}. {item.get('material', 'Unknown')}: {item.get('score', 0):.2%}")
        
        # Message
        if result.get("message"):
            lines.append(f"\nNote: {result['message']}")
        
        # Safety disclaimer
        lines.append("\n⚠️  This is candidate ranking only - no invention claims made.")
        
        return "\n".join(lines)


def create_materials_analyzer(workspace_dir: str = None) -> MaterialsAnalyzer:
    """Create a materials analyzer instance.
    
    Args:
        workspace_dir: Workspace directory for path validation
        
    Returns:
        MaterialsAnalyzer instance
    """
    return MaterialsAnalyzer(workspace_dir=workspace_dir)
