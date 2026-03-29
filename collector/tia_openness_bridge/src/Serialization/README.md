# Serialization-Bereich – TIA Openness Bridge (geplante Serialisierung)

## 1. Zweck des Serialization-Bereichs

Der **Serialization-Bereich** (`src/Serialization/`) enthält später die **JSON-Serialisierungs-Logik** des TIA-Collectors.

**Zweck:** Konvertierung des Contract-Baums (TiaExportContract und alle verknüpften Contracts) in ein valides JSON-Dokument, das exakt dem Schema `schemas/tia_export.schema.json` entspricht.

**Rolle im Collector:** Der Serialization-Bereich ist die **Zwischenschicht** zwischen den reinen Vertragsmodellen (DTOs) und der finalen JSON-Export-Datei. Er stellt sicher, dass die JSON-Ausgabe **strukturiert**, **schema-konform** und **serialisierungsgerecht** ist.

**Was hier umgesetzt wird:**
- JSON-Seriialisierung (mit JSON.NET oder System.Text.Json)
- Umgang mit optionalen Feldern (null → nicht serialisieren)
- Umgang mit leeren Listen (leere Arrays)
- Formatierung (indent, newlines, encoding)
- Schema-Validierung (optional, für die Export-Qualitätssicherung)

**Was hier NICHT umgesetzt wird:**
- C#-Code (erst in einem späteren Schritt)
- Dateischreib-Logik (dieser Bereich serialisiert nur in Speicher)
- Openness-Verbindungen
- Extraktions-Logik
- Logging-Schicht
- File-System-Zugriff

## 2. Geplante Verantwortlichkeiten

| Verantwortlichkeit | Beschreibung | Was **nicht** dazugehört |
|--------------------|--------------|--------------------------|
| **TiaExportContractSerializer** | Serialisiert den Root-Vertrag in JSON | File-Write, Pfad-Auflösung |
| **JsonPropertyRenamer** | Wandelt C#-Property-Namen in JSON-Schema-Namen um (z. B. `IpAddress` → `ip_address`) | Geschäftslogik |
| **OptionalFieldHandler** | Behandelt null-Werte (null → Property nicht in JSON) | Validierung |
| **EmptyListHandler** | Behandelt leere Listen (leer → `[]` anstatt `null`) | Logik |
| **JsonOutputFormatter** | Formatierung (indent, newlines, UTF-8) | Kompromisse bei Schema |

### Einzelne Verantwortlichkeiten (Zusammenfassung)

- **TiaExportContractSerializer**: Root-Seriialisierung (TiaExportContract → JSON)
- **JsonPropertyRenamer**: C#-Naming → JSON-Naming (PascalCase → snake_case)
- **OptionalFieldHandler**: null-Werte nicht serialisieren
- **EmptyListHandler**: Leere Listen als `[]` statt `null`
- **JsonOutputFormatter**: Pretty-Print (indent=2, newlines)

## 3. Abgrenzung

### Was **nicht** zum Serialization-Bereich gehört

| Bereich | Verantwortung | Warum Serialization **nicht** dazugehört |
|---------|---------------|------------------------------------------|
| **Contract-Modelle** | DTOs mit Properties | Serialization nutzt Contracts, sie sind nicht Teil von Serialization |
| **Extraktions-Logik** | Daten aus TIA lesen | Serialization serialisiert bereits extrahierte Daten |
| **ExportWriter** | Datei schreiben | Serialization schreibt nicht, sie produziert nur String/Byte[] |
| **ErrorHandler** | Exceptions | Serialization wirft keine neuen Exceptions, sie transportiert nur Daten |
| **Normalizer** | Weslr-Transformierung | Serialization ist TIA-relevant, nicht Weslr-relevant |
| **FileSystemWriter** | Datei-IO | Serialization serialisiert in Speicher, sie schreibt keine Dateien |
| **Logger** | Logging | Serialization ist rein datentransformierend, sie logt nicht |

### Klare Grenze

- **Serialization**: Konvertierung Contract → JSON-String/Byte[]
- **ExportWriter**: Konvertierung JSON-String/Byte[] → Datei
- **Normalizer**: Konvertierung JSON → Weslr Normalized Graph

## 4. Beziehung zum Schema

### Wie der Serialization-Bereich das Schema unterstützt

- **JSON-Struktur entspricht exakt dem Schema**: Jeder Contract-Vertrag hat ein JSON-Äquivalent in `schemas/tia_export.schema.json`
- **Property-Naming**: C#-PascalCase wird in JSON snake_case konvertiert (z. B. `IpAddress` → `ip_address`)
- **Null-Handling**: Optional-Felder mit null-Wert werden nicht serialisiert (kein `"property": null`)
- **Leere Listen**: Leere Listen werden als `[]` serialisiert (nicht `null`)
- **Typsicherheit**: Compile-time-Validierung durch C#-Typen verhindert Schema-Abweichungen

### Warum Contracts und Schema nicht voneinander wegdriften dürfen

- **Vertrags-Änderung** → muss auch Schema-Änderung implizieren
- **Schema-Änderung** → muss auch Vertrags-Änderung implizieren
- **JSON-Export** → muss nach Schema validierbar sein

### Konsequenzen für die Serialisierungs-Struktur

- **Keine manuellen JSON-Strings**: Serialisierung erfolgt über JSON.NET/System.Text.Json
- **Attribute/Attributes**: C#-Attribute (z. B. `[JsonPropertyName("ip_address")]`) für JSON-Naming
- **Keine Runtime-Naming-Logik**: Namenskonvertierung ist statisch (nicht dynamisch zur Laufzeit)

## 5. Read-only- und Sicherheitsbezug

### Wie die read-only Ausrichtung in der Serialisierung widerspiegeln soll

- **Keine Schreib-Operationen**: Serialization serialisiert nur in Speicher (kein File-Write in diesem Bereich)
- **Keine SPS-Referenzen**: Serialization kennt keine SPS-Objekte (nur Contracts)
- **Keine API-Abhängigkeiten**: Serialization ist unabhängig von TIA Openness API
- **Keine Runtime-Logik**: Serialization ist reine Datenkonvertierung

### Konsequenzen für die Serialisierungs-Struktur

- **Reine Funktionen**: `string Serialize(TiaExportContract export)` statt Klassen mit Status
- **Keine SPS-Objekte**: Serialization arbeitet nur mit Contract-Instanzen
- **Keine External References**: Serialization ist self-contained (keine Verweise auf TIA API)

## 6. Nächste minimale Implementierungsschritte

### Erste C#-Serialization-Dateien (nach dieser Serialisierungs-Dokumentation)

| Datei | Zweck |
|-------|-------|
| **TiaExportContractSerializer.cs** | Root-Serialisierung (TiaExportContract → JSON-String) |
| **JsonPropertyRenamer.cs** | C#-Property-Namen → JSON-Schema-Namen |
| **OptionalFieldHandler.cs** | null-Werte auslassen (nicht serialisieren) |
| **EmptyListHandler.cs** | Leere Listen als `[]` serialisieren |
| **JsonOutputFormatter.cs** | Pretty-Print (indent=2, newlines) |

### Kein Code hier

Diese Dokumentation definiert nur die **Serialization-Struktur und Verantwortlichkeiten**. Die C#-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*