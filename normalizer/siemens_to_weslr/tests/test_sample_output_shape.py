"""
Tests für die Form der Normalizer-Ausgabe (Strukturvergleich mit Sample).

Diese Tests prüfen, dass die erzeugte Normalized Graph Struktur
mit der erwarteten Form (sample_normalized_graph.json) übereinstimmt.
"""

import json
import pathlib

from siemens_to_weslr.src.normalize import normalize_tia_export, to_dict


# Pfade zu Beispiel-Dateien
EXAMPLES_DIR = pathlib.Path(__file__).parent.parent / "examples"
SAMPLE_RAW_EXPORT = EXAMPLES_DIR / "sample_tia_export.json"
SAMPLE_NORMALIZED_GRAPH = EXAMPLES_DIR / "sample_normalized_graph.json"


def test_to_dict_liefert_erwartete_hauptschluessel():
    """
    Test 1: Prüfen, dass to_dict(...) ein Dictionary mit erwarteten Hauptschlüsseln liefert.
    
    Erwartet: keys = {"entities", "relations", "metadata"}
    """
    # Arrange
    raw_data = json.loads(SAMPLE_RAW_EXPORT.read_text(encoding="utf-8"))
    
    # Act
    output = to_dict(normalize_tia_export(raw_data))
    
    # Assert
    assert isinstance(output, dict)
    assert "entities" in output
    assert "relations" in output
    assert "metadata" in output


def test_entities_relations_sind_listen():
    """
    Test 2: Prüfen, dass entities und relations Listen sind und bei nichtleerer Eingabe nicht leer sind.
    
    Erwartet: type(entities) == list, type(relations) == list
              len(entities) > 0, len(relations) >= 0 (akzeptiert)
    """
    # Arrange
    raw_data = json.loads(SAMPLE_RAW_EXPORT.read_text(encoding="utf-8"))
    
    # Act
    output = to_dict(normalize_tia_export(raw_data))
    
    # Assert
    assert isinstance(output["entities"], list), "entities muss eine Liste sein"
    assert isinstance(output["relations"], list), "relations muss eine Liste sein"
    
    # Beispiel-Datei enthält Entities, daher erwarten wir > 0
    assert len(output["entities"]) > 0, "entities Liste ist leer, obwohl Eingabedaten vorhanden sind"


def test_entities_have_grundlegende_felder():
    """
    Test 3: Prüfen, dass jede Entity mindestens grundlegende Felder besitzt.
    
    Erwartet: für jede Entity: id, type, attributes, confidence
    Erwartet: für jede Relation: id, source_id, target_id, type
    """
    # Arrange
    raw_data = json.loads(SAMPLE_RAW_EXPORT.read_text(encoding="utf-8"))
    output = to_dict(normalize_tia_export(raw_data))
    
    # Assert Entities
    for entity in output["entities"]:
        assert "id" in entity, f"Entity fehlt id: {entity}"
        assert "type" in entity, f"Entity fehlt type: {entity}"
        assert "attributes" in entity, f"Entity fehlt attributes: {entity}"
        assert "confidence" in entity, f"Entity fehlt confidence: {entity}"
    
    # Assert Relations
    for relation in output["relations"]:
        assert "id" in relation, f"Relation fehlt id: {relation}"
        assert "source_id" in relation, f"Relation fehlt source_id: {relation}"
        assert "target_id" in relation, f"Relation fehlt target_id: {relation}"
        assert "type" in relation, f"Relation fehlt type: {relation}"


def test_output_hat_groben_strukturvergleich_mit_sample():
    """
    Test 4: Vergleiche grob die Struktur mit sample_normalized_graph.json.
    
    Prüft nur auf Form- und Hauptschlüsselebene (kein vollständiger Vergleich).
    
    Erwartet: sample hat keys ["entities", "relations", "metadata"]
              output muss dieselben Hauptschlüssel haben
    """
    # Arrange
    raw_data = json.loads(SAMPLE_RAW_EXPORT.read_text(encoding="utf-8"))
    output = to_dict(normalize_tia_export(raw_data))
    
    sample_data = json.loads(SAMPLE_NORMALIZED_GRAPH.read_text(encoding="utf-8"))
    
    # Assert: Hauptschlüssel-Vergleich
    output_keys = set(output.keys())
    sample_keys = set(sample_data.keys())
    
    assert output_keys >= {"entities", "relations", "metadata"}, "output fehlen Hauptschlüssel"
    assert sample_keys >= {"entities", "relations", "metadata"}, "sample fehlen Hauptschlüssel"
    
    # Prüfen, dass sample auch entities und relations als Listen hat
    assert isinstance(sample_data["entities"], list), "sample entities ist keine Liste"
    assert isinstance(sample_data["relations"], list), "sample relations ist keine Liste"
    
    # Prüfen, dass output auch entities und relations als Listen hat
    assert isinstance(output["entities"], list), "output entities ist keine Liste"
    assert isinstance(output["relations"], list), "output relations ist keine Liste"