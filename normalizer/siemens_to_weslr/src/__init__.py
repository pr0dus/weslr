"""
siemens_to_weslr – Normalizer (MVP).

Transformiert TIA Portal V20 Raw Exports in Weslr Normalized Graphs.

Öffentliche API:
- normalize_tia_export(raw: dict) -> NormalizedGraph
- to_dict(graph: NormalizedGraph) -> dict
- models: NormalizedEntity, NormalizedRelation, NormalizedGraph
"""

from .models import NormalizedEntity, NormalizedRelation, NormalizedGraph
from .normalize import normalize_tia_export, to_dict

__all__ = [
    "NormalizedEntity",
    "NormalizedRelation",
    "NormalizedGraph",
    "normalize_tia_export",
    "to_dict",
]