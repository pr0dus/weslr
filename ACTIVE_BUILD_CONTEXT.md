# ACTIVE_BUILD_CONTEXT.md

## Aktueller Hauptbereich

`collector/tia_openness_bridge/src/Extraction`

## Aktueller Stil

Kleine openness-neutrale Rückgabetypen für Extraktionsschritte.

## Relevante Musterdateien

- `ProjectExtractionResult.cs`
- `DeviceExtractionResult.cs`
- `PlcExtractionResult.cs`
- `CpuExtractionResult.cs`
- `ModuleExtractionResult.cs`
- `TagTableExtractionResult.cs`
- `TagExtractionResult.cs`
- `ProgramBlockExtractionResult.cs`
- `TopologyRelationExtractionResult.cs`

## Aktuelle Arbeitslogik

- Gleiche Struktur und Stilrichtung wie bestehende ExtractionResult-Dateien
- Nur Standardbibliothek
- Keine Geschäftslogik
- Keine Dateilogik
- Keine JSON-Serialisierung
- Keine Openness-Logik
- Nullarme Struktur
- Namespace `SiemensToWeslr.TiaCollector.Extraction`

## Nächstes Ziel

`collector/tia_openness_bridge/src/Extraction/AlarmExtractionResult.cs`

---

*Letzte Aktualisierung: 2026-03-29*