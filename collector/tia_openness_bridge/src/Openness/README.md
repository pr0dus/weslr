# Openness-Bereich – TIA Openness Bridge (geplante TIA-Integration)

## 1. Zweck des Openness-Bereichs

Der **Openness-Bereich** (`src/Openness/`) enthält später die **TIA Openness API-integrierende Logik** des TIA-Collectors.

**Zweck:** Schnittstelle zu TIA Openness API, um Engineering-Daten aus TIA Portal V20 zu extrahieren.

**Rolle im Collector:** Der Openness-Bereich ist die **Schnittstelle zur TIA Openness API**. Er übernimmt die Openness-Session, öffnet Projekte, greift auf TIA-Objekte zu und übergibt Rohdaten an den Extraction-Bereich.

**Was hier umgesetzt wird:**
- TIA Openness Session-Management
- Projekt-Öffnung und -Schließung
- TIA-Objekt-Abfrage (PLCs, CPUs, Devices, etc.)
- Openness-spezifische Fehlerbehandlung

**Was hier NICHT umgesetzt wird:**
- C#-Code (erst in einem späteren Schritt)
- Extraktions-Logik (dieser Bereich ist nur für Openness-Zugriff zuständig)
- Mapping zu Contract-Objekten (dieser Bereich liefert nur Openness-Objekte)
- JSON-Serialisierung (dieser Bereich arbeitet mit Openness-Objekten)
- Dateiausgabe (dieser Bereich schreibt keine Dateien)

## 2. Geplante Verantwortlichkeiten

| Verantwortlichkeit | Beschreibung | Was **nicht** dazugehört |
|--------------------|--------------|--------------------------|
| **SessionManager** | Öffnet und verwaltet TIA Openness Session | Extraction, Mapping, Serialisierung |
| **ProjectOpener** | Öffnet TIA-Projekt über Openness API | Extraction, Mapping, Serialisierung |
| **ProjectCloser** | Schließt TIA-Projekt über Openness API | Extraction, Mapping, Serialisierung |
| **TiaObjectQuery** | Fragt TIA-Objekte über Openness API ab | Extraction, Mapping, Serialisierung |
| **OpennessErrorTranslator** | Übersetzt Openness-Exceptions in Diagnose-Hinweise | Extraction, Mapping, Serialisierung |

## 3. Abgrenzung

### Was **nicht** zum Openness-Bereich gehört

| Bereich | Verantwortung | Warum Openness **nicht** dazugehört |
|---------|---------------|-------------------------------------|
| **Extraction** | TIA-Daten extrahieren und in Rohdaten überführen | Openness liefert nur Openness-Objekte |
| **Mapping** | Rohdaten → Contract-Objekte | Openness kennt keine Contracts |
| **Serialization** | JSON-Serialisierung | Openness arbeitet mit Openness-Objekten |
| **ExportWriter** | Datei schreiben | Openness ist nur für Openness-Zugriff zuständig |

## 4. Nächste minimale Implementierungsschritte

### Erste C#-Openness-Dateien (nach dieser Openness-Dokumentation)

| Datei | Zweck |
|-------|-------|
| **SessionManager.cs** | Öffnet TIA Openness Session, verwaltet Verbindungen |
| **ProjectOpener.cs** | Öffnet TIA-Projekt über Openness API |
| **ProjectCloser.cs** | Schließt TIA-Projekt über Openness API |
| **TiaObjectQuery.cs** | Fragt TIA-Objekte über Openness API ab |
| **OpennessErrorTranslator.cs** | Übersetzt Openness-Exceptions in Diagnose-Hinweise |

### Kein Code hier

Diese Dokumentation definiert nur die **Openness-Struktur und Verantwortlichkeiten**. Die C#-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*