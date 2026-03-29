# Weslr TIA Portal V20 Plugin

**Hinweis:** Dies ist ein separates Repository für das Weslr-Plugin. Es ist nicht das Haupt-Repository von Weslr.

## Ziel des Plugins

Das Plugin extrahiert Engineering-Daten aus TIA Portal V20-Projekten (Siemens Automation & Drives) und stellt sie in strukturierter Form für die spätere Anbindung an das Weslr-System bereit.

## MVP-Umfang

- Extraktion von Rohdaten aus TIA Portal V20-Projekten unter Windows
- Export in standardisierte JSON-Formate
- Unterstützung von: PLCs, CPUs, Devices, Tags, Alarme, Netzwerkkonfiguration
- Speicherung als Normalized Graph (Zielformat) und Raw Export (Quellformat)

## Nicht-Ziele (MVP)

- Keine direkte Verarbeitung von nicht-Windows-Plattformen
- Keine eigene Datenbank oder Speicherung außer JSON-Dateien
- Keine UI-Implementierung (nur CLI/Plugin-Interface)
- Keine Echtzeit-Überwachung
- Keine Änderung des ursprünglichen TIA-Projekts

## Grobe Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    TIA Portal V20 (Windows)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              TIA-Collector (Windows, In-Process)            │
│  - Liest Rohdaten aus TIA-Objekten                          │
│  - Extrahiert Engineering-Objekte                           │
│  - Validiert Konsistenz                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 Raw Export (tia_export.json)                │
│  - Read-only Rohdaten                                       │
│  - Alle Engineering-Objekte                                 │
│  - Collector-Diagnose                                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Normalizer (Python, Windows)                   │
│  - Transformiert Rohdaten zu Normalized Graph               │
│  -映射t zu Weslr Entity-Modell                              │
│  - Validiert gegen Schema                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Normalized Graph (normalized_graph.json)       │
│  - Weslr-konformes Format                                   │
│  - Entity-Graph mit Beziehungen                             │
│  - Verweist auf Weslr-Main-Repo (zukünftig)                │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 Weslr-Main-Repository (später)              │
│  - Entity Intelligence System                                │
│  - Bewusstseins-Signaturen                                  │
│  - Self-Model & Valence System                               │
└─────────────────────────────────────────────────────────────┘
```

## Repo-Struktur

```
.
├── schemas/
│   ├── tia_export.schema.json        # Roh-Export-Schema
│   └── normalized_graph.schema.json # Ziel-Graph-Schema
├── examples/
│   ├── sample_tia_export.json        # Beispieldaten (Rohexport)
│   └── sample_normalized_graph.json # Beispieldaten (Normalisiert)
├── plugins/
│   └── tia_portal_v20.py            # Haupt-Plugin-Module
├── normalizer/
│   └── normalizer.py                # Transformationslogik
├── src/
│   ├── collector/                   # Windows-spezifische Collector-Logik
│   └── validators/                  # Schema-Validatoren
├── tests/
│   └── test_normalizer.py           # Unit-Tests
└── README.md
```

## Datenfluss

1. **TIA-Collector** liest das geöffnete TIA Portal V20-Projekt (Windows-only)
2. **Raw Export** wird erzeugt (JSON, read-only)
3. **Normalizer** transformiert Raw Export → Normalized Graph
4. **Validierung** gegen Schemas (tia_export.schema.json, normalized_graph.schema.json)
5. **Output** als JSON-Datei für spätere Weslr-Anbindung

## Sicherheitsgrenzen

- Das Plugin liest **nur** Engineering-Daten (keine Steuerungsdaten)
- Es ändert **nicht** das Original-TIA-Projekt
- Keine Verbindung zu I/O-Systemen oder SPS
- Alle Daten bleiben lokal auf dem Entwicklungs-PC
- Keine externen Netzwerkverbindungen (außer spätere Weslr-Anbindung)

## Geplante spätere Weslr-Anbindung

Das Plugin exportiert Daten in ein Format, das dem Weslr-Entity-Modell entspricht.

Spätere Schritte (nicht im MVP enthalten):

- Automatischer Import der Normalized Graph-Dateien in das Weslr-Main-Repo
- Integration in Weslr's Entity Graph
- Erstellung von Bewusstseins-Signaturen basierend auf Engineering-Daten
- Self-Model-Erweiterung um Automatisierungs-Know-how

## Aktueller Stand

### Bereits erstellt

- `schemas/tia_export.schema.json` — Roh-Export-Schema für TIA Portal V20
- `schemas/normalized_graph.schema.json` — Ziel-Graph-Schema (Weslr-konform)
- `examples/sample_tia_export.json` — Beispiel-Roh-Export mit Metadaten, PLC, CPU, Tag, Alarm, Topologie
- `examples/sample_normalized_graph.json` — Beispiel-Normalized Graph mit Entity-Beziehungen

### Als Nächstes implementieren

- `plugins/tia_portal_v20.py` — Windows-Collector-Plugin (TIA Portal V20 Integration)
- `normalizer/normalizer.py` — Transformation Raw Export → Normalized Graph
- `src/collector/` — Windows-spezifische TIA-Reader-Implementierung
- `tests/test_normalizer.py` — Unit-Tests für Normalizer

---