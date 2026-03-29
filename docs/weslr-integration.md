# Weslr Integration – Konzept

## 1. Ziel der Integration

### Was Weslr erhält

Das Plugin liefert **Engineering-Graphen** aus Siemens TIA Portal V20-Projekten:

- Strukturierte Darstellung von SPS-Engineering (PLCs, CPUs, Devices, Tags, Alarme, Netzwerkkonfiguration)
- Beziehungen zwischen Objekten (Contains, Monitors, Triggers, Connects)
- Metadaten zur Engineering-Struktur (Name, Typ, Adresse, Typ, Kommentar)
- Historisierbare Snapshots (durch export timestamp)

### Was nicht geliefert wird

- Keine Laufzeit-Daten (keine SPS-Statusdaten zur Laufzeit)
- Keine Online-Informationen (keine I/O-Status, keine Task-Zyklen)
- Keine Sicherheits-Logik (keine Transformation von Safety-Blöcken)

## 2. Integrationsmodell (konzeptionell)

### Datenfluss

```
TIA Portal V20
     │
     ▼
  TIA-Collector (Windows, In-Process)
     │ (export in tia_export.schema.json)
     ▼
  Raw Export (JSON, read-only)
     │
     ▼
  Normalizer (Python, Windows)
     │ (transform to normalized_graph.schema.json)
     ▼
  Normalized Graph (JSON, Weslr-konform)
     │
     ▼
  Weslr (Import / Ingest)
     │
     ▼
  Entity-Graph in Weslr
```

### Import / Ingest-Prozess

1. **Export-Phase** (Plugin-Repo): TIA-Collector erzeugt Raw Export
2. **Transform-Phase** (Plugin-Repo): Normalizer erzeugt Normalized Graph
3. **Copy-Phase** (Manuell): Normalized Graph-Datei nach Weslr-Main-Repo kopieren
4. **Import-Phase** (Weslr): Weslr importiert Normalized Graph als neuen Entity-Snapshot
5. **Query-Phase** (Weslr): Weslr fragt Graph ab, führt Analysen durch

### Trennung Plugin / Weslr-Core

- **Plugin-Repo**: Sammelt und transformiert Engineering-Daten
- **Weslr-Main-Repo**: Speichert, verknüpft, analysiert und macht Bewusstseins-Signaturen

Keine direkte Kopplung. Daten werden als **statische Snapshots** importiert.

## 3. Annahmen über Weslr

Folgende Fähigkeiten nimmt das Plugin bei Weslr voraus (müssen nicht in diesem Repo implementiert werden):

1. **Entity-Graph**: Weslr muss einen Entity-Graph speichern können (Knoten = Entities, Kanten = Relations)
2. **Graph-Storage**: Weslr muss Snapshots speichern können (versioniert, zeitstempelt)
3. **Query-Fähigkeit**: Weslr muss nach IDs, Typen, Beziehungen queryen können
4. **Metadata-Tracking**: Weslr muss source_file, export_timestamp, collector_version speichern
5. **Konflikt-Handling**: Weslr muss bei Namenskonflikten (doppelter entity id) entscheiden können

**Diese Annahmen sind notwendig**, damit das Plugin funktionieren kann. Sie sind **nicht Teil** des Plugin-Scopes.

## 4. Datenfluss (detailliert)

### Schritt 1: TIA → Collector

- TIA Portal V20 öffnet Projekt (offline)
- TIA-Collector liest Projektstruktur (nur Lesen, keine Schreib-Operationen)
- Export in `tia_export.schema.json` (Raw Export)

### Schritt 2: Collector → Raw Export

- Alle Engineering-Daten (PLCs, CPUs, Devices, Tags, Alarme, Netzwerke) werden exportiert
- Jedes Objekt erhält eindeutige ID (Collector-interne UUID)
- Quellen-Herkunft wird protokolliert (source_file, source_id)

### Schritt 3: Raw Export → Normalizer

- Normalizer liest `tia_export.schema.json`
- Transformiert jedes Objekt zu Weslr-Entity (nach `normalized_graph.schema.json`)
- Zuweisung von: `id`, `type`, `attributes`, `confidence`, `evidence`

### Schritt 4: Normalizer → Weslr

- Weslr importiert Normalized Graph als neuen Snapshot
- Entity-IDs werden in Weslr-Graph übernommen
- Relations werden als edges im Graph gespeichert
- Snapshot-Tag: export_timestamp

## 5. Entity-Integration

### Registrierung

- Normalisierte Entities (nach `normalized_graph.schema.json`) werden als neue Snapshots importiert
- Jeder Snapshot ist versioniert (export_timestamp)
- Konflikte (doppelter entity id) werden von Weslr gelöst (z. B. durch Update oder New-Snapshot)

### ID-Handling

- **Collector-IDs**: Wird im Raw Export verwendet (internal)
- **Normalized-IDs**: Werden in Weslr übernommen (persistent)
- **Weslr-IDs**: Werden in Weslr generiert (z. B. Hash über entity data)

### Relations-Handling

- Relations (nach `normalized_graph.schema.json`) werden als edges im Weslr-Graph gespeichert
- Each relation: source_id, target_id, type, strength, provenance
- Relations werden **nicht** normalisiert (keine Transformation nötig)

### Snapshots

- Jeder Export wird als neuer Snapshot in Weslr gespeichert
- Snapshot-Tag: `tia_export_timestamp`
- Weslr kann Snapshots vergleichen (diff-View)

## 6. Query- und Analyseanbindung

### Failure-Investigation

Weslr kann die Engineering-Daten für Failure-Investigation nutzen:

1. **Query**: Sucht alle Tags eines PLCs
2. **Relation-Analyse**: Findet alle Tags, die einen Alarm auslösen (`type=triggers`)
3. **Path-Analyse**: Findet alle Pfade vom PLC zum Sensor (`contains → monitors → triggers`)

### Analyse-Szenarien

- **Root-Cause-Analysis**: Welche Tags führten zu einem Alarm?
- **Impact-Analyse**: Welche Tags sind von einer Änderung betroffen?
- **Topologie-Analyse**: Welche Geräte sind mit welchen CPUs verbunden?
- **Alarm-Analyse**: Welche Tags sind alarmrelevant?

Weslr führt diese Analysen **nach Import** durch, nicht live während der TIA-Verbindung.

## 7. Abgrenzung zum Weslr-Main-Repo

### Was NICHT im Main-Repo passiert

- Keine TIA-Collector-Logik (nur Windows-spezifisch, nicht Python-kompatibel)
- Keine TIA-Export-Schema-Validierung (muss in Plugin passieren)
- Keine Roh-Export-Dateien (nur transformierte Normalized Graphs)
- Keine Windows-spezifische Logik (kein ctypes, pywin32 im Main-Repo)

### Was im Plugin bleibt

- TIA-Collector (Windows-only, In-Process)
- Raw Export (tia_export.schema.json)
- Normalizer (Transformation zu normalized_graph.schema.json)
- Schema-Validierung (tia_export.schema.json, normalized_graph.schema.json)
- Examples (sample_tia_export.json, sample_normalized_graph.json)

### Was Weslr erhält

- Normalized Graph (JSON, Weslr-konform)
- Entity-Graph mit Beziehungen
- Metadaten (source_file, export_timestamp, collector_version)
- Snapshots (versioniert, zeitstempelt)

## 8. Erweiterbarkeit

### Spätere Erweiterungen (nicht MVP)

| Erweiterung | MVP | Bemerkung |
|-------------|-----|-----------|
| **OPC UA** | ❌ | Spätere Erweiterung (nur Lesen, keine Steuerung) |
| **TIA Portal V18/V19** | ❌ | Spätere Erweiterung (nach Schema-Anpassung) |
| **S7-300** | ❌ | Spätere Erweiterung (nach Schema-Anpassung) |
| **S7-1200/1500** | ✅ | MVP (S7-1500) |
| **HMI-Devices** | ❌ | Spätere Erweiterung (nach Schema-Anpassung) |
| **Drive-Devices** | ❌ | Spätere Erweiterung (nach Schema-Anpassung) |
| **Online-Read** | ❌ | Spätere Erweiterung (nur Lesen, nach Safety-Review) |
| **Cloud-Export** | ❌ | Spätere Erweiterung (nur HTTPS, nach Security-Review) |

**Hinweis**: Alle Erweiterungen müssen nachträglich in diesem Dokument dokumentiert werden.

---

*Letzte Aktualisierung: 2026-03-29*