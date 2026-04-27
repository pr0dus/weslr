from datetime import datetime
import json
from pathlib import Path

# adjust path if needed
COOC_PATH = Path("weslr/entity_cooccurrence.json")


def reset():
    """Clear co-occurrence store (clean lab state)."""
    COOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    COOC_PATH.write_text(json.dumps({"pairs": {}}, indent=2))
    print("RESET COMPLETE")


def inject(entity_a, entity_b):
    """Inject one co-occurrence signal (simulates M0 output)."""
    now = datetime.utcnow().isoformat() + "Z"

    if not COOC_PATH.exists():
        reset()

    data = json.loads(COOC_PATH.read_text())
    pairs = data.setdefault("pairs", {})

    key = "|".join(sorted([entity_a.lower(), entity_b.lower()]))

    if key not in pairs:
        pairs[key] = {
            "count": 0,
            "first_seen": now,
            "last_seen": now,
        }

    pairs[key]["count"] += 1
    pairs[key]["last_seen"] = now

    COOC_PATH.write_text(json.dumps(data, indent=2))
    print(f"INJECTED: {entity_a} ↔ {entity_b}")


def show():
    """Print current co-occurrence state."""
    if not COOC_PATH.exists():
        print("EMPTY")
        return

    data = json.loads(COOC_PATH.read_text())
    print(json.dumps(data, indent=2))


def summary(entity):
    """Use your real M8.3 function."""
    from interpretation import get_entity_cooccurrence_summary
    print(get_entity_cooccurrence_summary(entity))


def proposals():
    """Use your real M6 + M8.4 layer."""
    from interpretation import generate_relationship_proposals
    from interpretation import list_proposals_by_classification

    generate_relationship_proposals()
    print(list_proposals_by_classification(status=None))
