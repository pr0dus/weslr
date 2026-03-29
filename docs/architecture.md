# Architektur – Weslr TIA Portal V20 Plugin

## 1. Ziel der Architektur

Das Plugin extrahiert Engineering-Daten aus Siemens TIA Portal V20-Projekten (Windows) und stellt sie strukturiert für die spätere Anbindung an das Weslr-System bereit.

**Rolle im Weslr-Ökosystem**: Engineering-Daten-Quelle für die Entity-Intelligence von Weslr. Keine direkte Steuerung, nur lesender Zugriff und strukturierte Exporte.

## 2. Hauptkomponenten

| Komponente | Verantwortung | Eingaben | Ausgaben |
|------------|---------------|----------|----------|
| **TIA-Collector** | Windows-seitiges Auslesen von TIA-Objekten (In-Process) | Geöffnetes TIA Portal V20 Projekt (offline) | `tia_export.schema.json` (Raw Export) |
| **Normalizer** | Transformation Raw Export → Normalized Graph (Python) | `tia_export.schema.json` | `normalized_graph.schema.json` |
| **Analyzer** | (später) Failure-Investigation auf dem Graph | `normalized_graph.schema.json` | Analyse-Ergebnisse (in Weslr) |
| **Schema-Layer** | JSON-Schemas, Validierung, Dokumentation | — | `schemas/tia_export.schema.json`, `schemas/normalized_graph.schema.json` |
| **Datenartefakte** | Beispieldaten für Testing und Doku | — | `examples/sample_tia_export.json`, `examples/sample_normalized_graph.json` |

## 3. Datenfluss

```
┌────────────────────────────────────────────────────────────────┐
│ 1. TIA Portal V20 (Windows, offline)                          │
│    - Projekt-Struktur, PLCs, CPUs, Devices, Tags, Alarme      │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. TIA-Collector (In-Process, Windows)                        │
│    - Liest Engineering-Daten (nur Lesen, keine Schreib-OPs)   │
│    - Exportiert in tia_export.schema.json                     │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. Raw Export (JSON, read-only)                               │
│    - Vollständige Engineering-Daten                           │
│    - Collector-Diagnose (errors, warnings)                    │
│    - source_file, export_timestamp, collector_version        │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. Normalizer (Python, Windows)                               │
│    - Transformiert Raw Export → Normalized Graph              │
│    - Validiert gegen Schema                                   │
│    - Erstellt Weslr-konforme Entities und Relations           │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. Normalized Graph (JSON, Weslr-konform)                     │
│    - Entity-Graph mit Attributes, Relations, Confidence       │
│    -source_file → Weslr (Import/Ingest)                      │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────────┐
│ 6. Weslr (später, Main-Repo)                                  │
│    - Importiert Normalized Graph als Entity-Snapshot          │
│    - Speichert im Entity-Graph                                │
│    - Führt Failure-Investigation durch (später)               │
└────────────────────────────────────────────────────────────────┘
```

## 4. Datenmodelle

| Modell | Datei | Beschreibung |
|--------|-------|--------------|
| **Rohdaten** | `schemas/tia_export.schema.json` | Read-only Engineering-Daten aus TIA Portal V20 |
| **Normalized Graph** | `schemas/normalized_graph.schema.json` | Weslr-konformer Entity-Graph mit Relations |

**Datenartefakte:**
- `examples/sample_tia_export.json` — Beispiel-Raw Export (1 PLC, 1 Device, 1 CPU, 1 Tag, 1 Alarm, 1 Topology)
- `examples/sample_normalized_graph.json` — Beispiel-Normalized Graph (7 Entities, 3 Relations)

## 5. Integrationssicht

- **Lose Kopplung**: Plugin und Weslr-Main-Repo sind strikt getrennt.
- **Import-Pfad**: TIA → Collector → Export → Normalizer → Weslr (statische Snapshots)
- **Keine Änderungen**: Das Weslr-Main-Repo wird **nicht** verändert. Das Plugin liefert nur Daten.
- **Weslr-Anbindung**: Weslr importiert Normalized Graphs als neue Entity-Snapshots.

## 6. Sicherheits- und Betriebsgrenzen

### Sicherheitsprinzipien
- Read-only by default
- Keine Schreibzugriffe auf SPS oder TIA-Projekt
- Keine Online-Kommunikation (keine SPS-Steuerung)
- Keine Safety-Bypasses
- Keine Cloud-Übertragung (außer spätere Weslr-Anbindung)

### Betriebsgrenzen
- Nur Windows (TIA Portal V20)
- Nur Offline-Modus
- Keine Echtzeit-Überwachung
- Keine Netzwerkkommunikation (außer spätere Weslr-Anbindung)

### Ausgeschlossene Funktionen
- SPS-Steuerung (Restart, Stop, Start, Mode-Change)
- Online-Read/Write, Force, Download/Upload
- Safety-Bypass
- Auto-Konvertierung
- Cloud-Speicherung

## 7. Erweiterungspunkte

### MVP (umsetzungsreif)
- TIA-Collector (Windows, In-Process, TIA Openness)
- Normalizer (Python, Transformation Raw → Normalized)
- Schema-Layer (JSON-Schemas, Validierung)
- Beispieldaten (sample export, sample normalized graph)

### Mögliche spätere Erweiterungen (nicht MVP)
- **OPC UA**: Lesender Zugriff auf SPS-Daten (nach Safety-Review)
- **Runtime-Daten**: Logging von DB-Änderungen (nach User-Request, nicht automatisch)
- **Netzwerk-Scan**: Find PLCs in subnet (nach Sicherheits-Review)
- **TIA Portal V18/V19**: Schema-Anpassung nötig
- **HMI/Drive-Devices**: Schema-Erweiterung nötig
- **Cloud-Export**: HTTPS-Anbindung an Weslr-Backend (nach Security-Review)

---

*Letzte Aktualisierung: 2026-03-29*