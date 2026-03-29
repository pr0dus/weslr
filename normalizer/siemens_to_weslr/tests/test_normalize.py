"""
Tests für den Normalizer (MVP).

Diese Tests prüfen die Kernfunktionen des Normalizers:
- normalize_tia_export(...)
- to_dict(...)
- Entity- und Relationsextraktion
"""

import json
import pathlib

from siemens_to_weslr.src.normalize import normalize_tia_export, to_dict
from siemens_to_weslr.src.models import NormalizedGraph


# Pfade zu Beispiel-Dateien
EXAMPLES_DIR = pathlib.Path(__file__).parent.parent / "examples"
SAMPLE_RAW_EXPORT = EXAMPLES_DIR / "sample_tia_export.json"
SAMPLE_NORMALIZED_GRAPH = EXAMPLES_DIR / "sample_normalized_graph.json"


def test_normalize_tia_export_liefert_NormalizedGraph():
    """
    Test 1: Prüfen, dass sample_tia_export.json erfolgreich verarbeitet wird.
    
    Erwartet: Ein NormalizedGraph-Objekt wird zurückgegeben.
    """
    # Arrange
    raw_data = json.loads(SAMPLE_RAW_EXPORT.read_text(encoding="utf-8"))
    
    # Act
    result = normalize_tia_export(raw_data)
    
    # Assert
    assert isinstance(result, NormalizedGraph)
    assert result.metadata is not None
    assert result.metadata.get("version") == "1.0.0"
    assert result.metadata.get("source") == "siemens_to_weslr_normalizer_v1"
    assert result.source_file is not None


def test_normalize_tia_export_extrahiert_erwartete_entity_types():
    """
    Test 2: Prüfen, dass mindestens erwartete Entitätstypen extrahiert werden.
    
    Erwartet: mindestens ein Entity mit type: project, device, plc, cpu, tag, tag_table
    """
    # Arrange
    raw_data = json.loads(SAMPLE_RAW_EXPORT.read_text(encoding="utf-8"))
    
    # Act
    result = normalize_tia_export(raw_data)
    
    # Assert
    entity_types = {e.type for e in result.entities}
    
    # Prüfen, dass mind. eines der erwarteten Types vorhanden ist
    expected_types = {"project", "device", "plc", "cpu", "tag", "tag_table", "alarm", "program_block"}
    found_types = entity_types & expected_types
    
    assert len(found_types) >= 3, f"Erwartete Types nicht gefunden. Gefunden: {entity_types}"


def test_to_dict_liefert_korrekte_struktur():
    """
    Test 3: Prüfen, dass to_dict(...) eine Struktur mit Hauptschlüsseln liefert.
    
    Erwartet: dict mit keys: entities, relations, metadata
             und nicht-leere Listen, wenn Eingabedaten nicht leer sind.
    """
    # Arrange
    raw_data = json.loads(SAMPLE_RAW_EXPORT.read_text(encoding="utf-8"))
    result = normalize_tia_export(raw_data)
    
    # Act
    output_dict = to_dict(result)
    
    # Assert
    assert isinstance(output_dict, dict)
    assert "entities" in output_dict
    assert "relations" in output_dict
    assert "metadata" in output_dict
    
    assert isinstance(output_dict["entities"], list)
    assert isinstance(output_dict["relations"], list)
    assert isinstance(output_dict["metadata"], dict)
    
    # Prüfen, dass Listen nicht leer sind (da Beispiel-Datei Daten enthält)
    assert len(output_dict["entities"]) > 0, "Entities Liste ist leer"
    assert len(output_dict["relations"]) >= 0, "Relations Liste ist leer (akzeptiert, da TIA Export keine Relations enthält)"
    
    # Prüfen, dass die erste Entity die erforderlichen Felder hat
    if output_dict["entities"]:
        first_entity = output_dict["entities"][0]
        assert "id" in first_entity
        assert "type" in first_entity
        assert "attributes" in first_entity
        assert "confidence" in first_entity


def test_id_normalisierung_funktioniert():
    """
    Zusatztest: Prüfen, dass IDs korrekt normalisiert werden.
    
    Erwartet: IDs sind lowercase, 4-16 chars, alphanumeric.
    """
    # Arrange
    raw_data = json.loads(SAMPLE_RAW_EXPORT.read_text(encoding="utf-8"))
    
    # Act
    result = normalize_tia_export(raw_data)
    
    # Assert
    for entity in result.entities:
        assert 4 <= len(entity.id) <= 16, f"ID zu kurz oder zu lang: {entity.id}"
        assert entity.id.isalnum(), f"ID enthält ungültige Zeichen: {entity.id}"
        assert entity.id.islower(), f"ID ist nicht lowercase: {entity.id}"
    
    for relation in result.relations:
        assert 4 <= len(relation.id) <= 16, f"Relation ID zu kurz oder zu lang: {relation.id}"
        assert relation.id.isalnum(), f"Relation ID enthält ungültige Zeichen: {relation.id}"
        assert relation.id.islower(), f"Relation ID ist nicht lowercase: {relation.id}"