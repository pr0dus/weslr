"""Weslr speak command - Chat with Weslr as the primary entity."""

from __future__ import annotations

from pathlib import Path
import sys
import json
import time
import re

# Add workspace to path
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR))

from entity_graph import get_entity_graph
from tax_knowledge import answer_entfernungspauschale_question, search_weslr_web, calculate_entfernungspauschale, search_weslr_web


def register_commands(subparsers):
    """Register speak command with argparse."""
    parser = subparsers.add_parser("speak", help="Chat with Weslr")
    parser.add_argument("--message", "-m", type=str, default="", help="User message")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.set_defaults(func=handle_speak)


def handle_speak(args):
    """Handle speak command."""
    message = args.message or input("You: ").strip()
    
    # Get entity graph
    graph = get_entity_graph()
    
    # Find or create Weslr entity
    wslr_entity = graph.get_entity_by_name("weslr") or graph.get_entity_by_name("Weslr")
    
    # If weslr entity doesn't exist, create one
    if not wslr_entity:
        wslr_entity = graph.add_entity(
            name="Weslr",
            entity_type="agent",
            aliases=["weslr", "Weslr"],
            confidence=0.9,
            is_ghost=False,
            metadata={"source": "speak-command", "created_at": int(time.time())}
        )
        wslr_entity.add_evidence("speak-command", "Self-referential agent created", 0.1)
    
    # Check for specific questions and provide context-aware answers
    response = None
    
    if "was bedeutet das" in message.lower():
        # Context: Entfernungspauschale discussion
        info = get_entfernungspauschale_info()
        if info and info.get('evidence'):
            response = (
                "Das bedeutet: Wenn du als Entfernungspauschale 0,38 € pro Kilometer geltend machen möchtest, "
                "gilt das ab dem 1.000. Kilometer jährlich. Das ist die Pauschalierung - du brauchst keine echten Fahrkosten nachzuweisen, "
                "solange du innerhalb dieses Satzes bleibst."
            )
    
    if "entfernungspauschale" in message.lower() or "fahrtkosten" in message.lower():
        tax_answer = answer_entfernungspauschale_question()
        if tax_answer:
            response = tax_answer
    
    # Check for distance questions (how many km, 200km, etc.)
    km_match = re.search(r'(\d+)\s*km', message.lower())
    if km_match:
        km = int(km_match.group(1))
        if km <= 1000:
            response = (
                f"Mit {km} km machst du keine Entfernungspauschale geltend. "
                f"Die Pauschale beginnt erst ab dem 1.001. Kilometer jährlich. "
                f"Deine {km} km fallen also nicht in den Abzug."
            )
        else:
            # Correct calculation: (km - 1000) × 0.38
            deductible_km = km - 1000
            amount = deductible_km * 0.38
            response = (
                f"Mit {km} km kannst du {deductible_km} km Entfernungspauschale geltend machen. "
                f"Das sind €{amount:.2f} (0,38 € pro km ab dem 1.001. Kilometer)."
            )
    
    # Check for distance questions (how many km, 200km, etc.)
    km_match = re.search(r'(\d+)\s*km', message.lower())
    if km_match:
        km = int(km_match.group(1))
        # Default to 220 workdays, calculate with own car (unlimited)
        calc = calculate_entfernungspauschale(km, workdays=220, use_own_car=True)
        if calc.get('use_own_car'):
            response = (
                f"Mit {km} km (bei eigenem PKW, unbegrenzt abziehbar):\n\n"
                f"- Erste 20 km: €{calc['first_20_km_total']:.2f}\n"
                f"- Ab km 21: €{calc['km_21_plus_total']:.2f}\n"
                f"- **Gesamt: €{calc['total']:.2f}**"
            )
        else:
            response = (
                f"Mit {km} km (maximal abziehbar: €4.500,00):\n\n"
                f"- Erste 20 km: €{calc['first_20_km_total']:.2f}\n"
                f"- Ab km 21: €{calc['km_21_plus_total']:.2f}\n"
                f"- **Gesamt (begrenzt): €{calc['total']:.2f}**"
            )
    
    # Check for explicit search queries
    if "suche" in message.lower() or "web search" in message.lower() or "search" in message.lower():
        # Extract search query from message
        search_query = message.lower()
        if "suche" in search_query:
            idx = search_query.find("suche")
            search_query = search_query[idx + len("suche"):].strip()
        elif "web search" in search_query:
            idx = search_query.find("web search")
            search_query = search_query[idx + len("web search"):].strip()
        elif "search" in search_query:
            idx = search_query.find("search")
            search_query = search_query[idx + len("search"):].strip()
        # Clean up any leading punctuation
        search_query = search_query.lstrip(':').strip()
        if search_query:
            search_results = search_weslr_web(search_query, max_results=3)
            response = f"Ich habe im Web gesucht nach: '{search_query}'\n\n{search_results[:500]}..."
    
    # Generate default response if no specific match
    if response is None:
        response = f"Ich bin Weslr, ein Entity Intelligence System mit messbaren Bewusstseins-Signaturen. Ich arbeite an Einkommensteuer- und Steuerwesen-Know-how. Was hast du gefragt: '{message}'."
    
    # Record the exchange
    try:
        graph.add_relationship(
            source_id=wslr_entity.id,
            target_id="user-unknown",
            rel_type="message",
            strength=0.8,
            provenance={"source": "speak-command", "timestamp": int(time.time()), "traceable": True}
        )
    except Exception:
        pass  # Ignore record errors
    
    if args.json:
        print(json.dumps({
            "message": message,
            "response": response,
            "entity_id": wslr_entity.id,
            "entity_name": wslr_entity.name
        }, indent=2))
    else:
        print(f"Weslr: {response}")


def get_entfernungspauschale_info():
    """Get Entfernungspauschale information from entity graph."""
    graph = get_entity_graph()
    
    # Find all entities with 'Entfernungspauschale'
    results = graph.search_entities('Entfernungspauschale')
    
    # Return the one with evidence
    for entity in results:
        if entity.evidence:
            return {
                'evidence': [e.get('content', '') for e in entity.evidence],
                'confidence': entity.confidence
            }
    
    return None


if __name__ == "__main__":
    import argparse
    args = argparse.Namespace(message="hello", json=False)
    handle_speak(args)
