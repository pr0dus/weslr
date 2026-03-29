"""Tax knowledge base integration for Weslr chat system.

Based on official BMF (Bundesministerium der Finanzen) LStH 2025 documentation:
https://esth.bundesfinanzministerium.de/lsth/2025/B-Anhaenge/Anhang-14/inhalt.html
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add workspace to path
WORKSPACE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE_DIR))

from entity_graph import get_entity_graph

# Import search_web from research
try:
    from research import search_web
except ImportError:
    search_web = None


def get_entfernungspauschale_info() -> Dict[str, Any]:
    """Get Entfernungspauschale information from entity graph and official sources."""
    graph = get_entity_graph()
    
    # Find all entities with 'Entfernungspauschale' in their name or aliases
    results = graph.search_entities('Entfernungspauschale')
    
    # Return the one with the most evidence
    best_entity = None
    for entity in results:
        if not best_entity or len(entity.evidence) > len(best_entity.evidence):
            best_entity = entity
    
    if best_entity:
        evidence = best_entity.evidence
        # Get the most specific evidence
        specific_evidence = []
        for ev in evidence:
            content = ev.get('content', '')
            if 'Euro pro km' in content or 'km' in content.lower():
                specific_evidence.append(content)
        
        # Add official BMF documentation info
        official_info = {
            'source': 'BMF LStH 2025',
            'link': 'https://esth.bundesfinanzministerium.de/lsth/2025/B-Anhaenge/Anhang-14/inhalt.html',
            'rates': {
                'first_20_km': '0.30 €/km',
                'km_21_2021_2023': '0.35 €/km',
                'km_21_2024_2026': '0.38 €/km',
                'max_deductible_4500': '4,500 €/year (if using own car: unlimited)'
            },
            'calculation': 'For distances > 20 km: 20 km × 0.30 € + remaining km × 0.38 € (2024-2026)'
        }
        
        return {
            'name': best_entity.name,
            'aliases': best_entity.aliases,
            'confidence': best_entity.confidence,
            'evidence': specific_evidence if specific_evidence else [e.get('content', '') for e in evidence],
            'official_info': official_info,
            'entity_id': best_entity.id
        }
    
    return None


def answer_entfernungspauschale_question() -> Optional[str]:
    """Generate a direct answer to Entfernungspauschale questions based on official BMF rules."""
    info = get_entfernungspauschale_info()
    if not info:
        return None
    
    # Extract rates from official info
    rates = info.get('official_info', {}).get('rates', {})
    
    return (
        "Die Entfernungspauschale für 2025 beträgt:\n\n"
        f"- **Erste 20 km:** {rates.get('first_20_km', '0.30 €/km')}\n"
        f"- **Ab km 21:** {rates.get('km_21_2024_2026', '0.38 €/km')}\n"
        f"- **Maximal abziehbar:** {rates.get('max_deductible_4500', '4,500 €/Jahr')} (bei eigenem PKW: unbegrenzt)\n\n"
        "Beispiel Berechnung für 1500 km (220 Arbeitstage):\n"
        "220 × 20 km × 0,30 € = 1.320 €\n"
        "220 × 1480 km × 0,38 € = 123.680 €\n"
        "Gesamt: 125.000 € (bei eigenem PKW unbegrenzt abziehbar, sonst max 4.500 €)"
    )


def calculate_entfernungspauschale(km: int, workdays: int = 220, use_own_car: bool = True) -> Dict[str, Any]:
    """Calculate Entfernungspauschale based on official BMF rules for 2024-2026."""
    # Rates for 2024-2026 (per BMF LStH 2025)
    rate_first_20_km = 0.30
    rate_21_plus = 0.38
    
    # Calculate
    first_20_km_amount = min(km, 20) * rate_first_20_km * workdays
    
    if km > 20:
        km_21_plus = km - 20
        km_21_plus_amount = km_21_plus * rate_21_plus * workdays
    else:
        km_21_plus_amount = 0
    
    total = first_20_km_amount + km_21_plus_amount
    
    # Apply max limit if not using own car
    max_deductible = 4500
    if not use_own_car and total > max_deductible:
        total = max_deductible
    
    return {
        'distance_km': km,
        'workdays': workdays,
        'rate_first_20_km': f'{rate_first_20_km} €/km',
        'rate_21_plus': f'{rate_21_plus} €/km',
        'first_20_km_total': round(first_20_km_amount, 2),
        'km_21_plus_total': round(km_21_plus_amount, 2),
        'total': round(total, 2),
        'max_deductible': max_deductible if not use_own_car else 'unbegrenzt',
        'use_own_car': use_own_car
    }


def search_weslr_web(query: str, max_results: int = 3) -> str:
    """Search the web using Weslr's built-in search."""
    if search_web is None:
        return "Weslr's web search is not available."
    
    result = search_web(query, limit=max_results, project_name="Weslr", version="0.1.0")
    
    if not result.get("results"):
        return f"No results found for: {query}"
    
    summary = f"Web search for '{query}' returned {len(result['results'])} results:\n\n"
    
    for i, r in enumerate(result['results'][:max_results], 1):
        title = r.get('title', 'No title')
        url = r.get('url', '')
        summary += f"{i}. [{title}]({url})\n"
    
    return summary


if __name__ == "__main__":
    result = get_entfernungspauschale_info()
    print("Entfernungspauschale info:", result)
    print()
    answer = answer_entfernungspauschale_question()
    print("Generated answer:", answer)
    print()
    # Test calculation
    calc = calculate_entfernungspauschale(1500, 220, use_own_car=True)
    print("Calculation for 1500 km:", calc)
