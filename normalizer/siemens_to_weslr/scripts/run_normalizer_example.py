#!/usr/bin/env python3
"""
Beispielskript für den MVP-Normalizer.

Lädt eine Beispiel-TIA-Export-Datei, normalisiert die Daten
und gibt das Ergebnis als formatiertes JSON aus.

Zweck: Veranschaulichung der Normalizer-Nutzung (kein generisches CLI).
"""

import json
import pathlib
import sys

# Füge das src-Verzeichnis zum Python-Pfad hinzu (für Importe ohne Installation)
SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from siemens_to_weslr import normalize_tia_export, to_dict


def main():
    """Main-Funktion: Beispiel-Normalizer-Aufruf."""
    # Pfade
    script_dir = pathlib.Path(__file__).parent
    examples_dir = script_dir.parent / "examples"
    input_file = examples_dir / "sample_tia_export.json"
    
    # Input laden
    with open(input_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # Normalisieren
    graph = normalize_tia_export(raw_data)
    
    # In dict umwandeln (für JSON-Serialization)
    output_dict = to_dict(graph)
    
    # Formatierter JSON ausgeben
    print(json.dumps(output_dict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()