# Test- und Verifikationsplan – Openness-Bereich

## 1. Ziel der Verifikation

Der Openness-Bereich soll **korrekte TIA Openness API-Integration** garantieren.

**Geprüft wird:**
- Openness Session-Management ist korrekt
- Projekt-Öffnung/-Schließung funktioniert
- TIA-Objekt-Abfragen liefern korrekte Daten
- Openness-spezifische Fehler werden korrekt erkannt und gemeldet
- Diagnose-Hinweise werden korrekt generiert
- Openness-Pipeline wird sauber in ExtractionOrchestrator integriert
- Keine Vermischung mit Extraktion, Mapping oder Serialisierung

## 2. Zu prüfende Aspekte

| Aspekt | Warum wichtig | Wie prüfen |
|--------|---------------|------------|
| **Session-Management** | Openness Session korrekt öffnen/schließen | Session-Check |
| **Projekt-Zugriff** | Projekt korrekt öffnen | Project-Check |
| **TIA-Objekt-Abfragen** | TIA-Objekte korrekt abfragen | Object-Check |
| **Fehlerbehandlung** | Openness-Fehler korrekt erkennen | Exception-Check |
| **Diagnose-Generierung** | Diagnose-Hinweise korrekt erzeugen | Diagnose-Check |
| **Pipeline-Integration** | OpennessExtractionPipeline in ExtractionOrchestrator | Integration-Check |

## 3. Positive Testfälle

### Testfall 1: Vollständige Session-Öffnung

- **Input**: TIA Openness API verfügbar
- **Erwartet**: Session-Öffnung erfolgreich, SessionHandle vorhanden
- **Prüfung**: SessionHandle-Check

### Testfall 2: Projekt-Öffnung

- **Input**: Projekt existiert und ist lesbar
- **Erwartet**: Projekt korrekt geöffnet, ProjectReference verfügbar
- **Prüfung**: ProjectReference-Check

### Testfall 3: TIA-Objekt-Abfragen

- **Input**: TIA-Objekte verfügbar
- **Erwartet**: Objekte korrekt abgefragt
- **Prüfung**: Object-Check

### Testfall 4: OpennessExtractionPipeline Integration

- **Input**: ExtractionOrchestrator mit Openness-Pipeline
- **Erwartet**: Pipeline startet, Schritte werden durchlaufen, Ergebnis zurückgegeben
- **Prüfung**: Pipeline-Check, Diagnose-Check

## 4. Negative bzw. Randfälle

### Randfall 1: TIA Openness nicht verfügbar

- **Input**: TIA Openness API nicht erreichbar
- **Erwartet**: Session-Öffnung fehlgeschlagen, Diagnose-Hinweis
- **Prüfung**: Exception-Check, Diagnose-Check

### Randfall 2: Projekt nicht lesbar

- **Input**: Projekt existiert, aber nicht lesbar
- **Erwartet**: Projekt-Öffnung fehlgeschlagen, Diagnose-Hinweis
- **Prüfung**: Exception-Check, Diagnose-Check

### Randfall 3: ExtractionOrchestrator mit leerem Pipeline-Step

- **Input**: ExtractionOrchestrator mit leerer Steps-Liste
- **Erwartet**: Pipeline fehlschlägt, Diagnose-Hinweis
- **Prüfung**: Exception-Check, Diagnose-Check

## 5. Abgrenzung

### Was **nicht** geprüft wird (in diesem Schritt)

| Bereich | Warum nicht | Erst später |
|---------|-------------|-------------|
| **Extraction-Tests** | Openness liefert nur Openness-Objekte | Extraction-Tests |
| **Mapping-Tests** | Openness kennt keine Contracts | Mapping-Tests |
| **Serialisierung** | Openness arbeitet mit Openness-Objekten | JsonSerializer-Tests |
| **Integration-Tests** | Nur Unit-Tests für Openness | Integration Tests |

## 6. Nächste minimale Umsetzungsschritte

### Erste C#-Testdateien (nach diesem Testplan)

| Testdatei | Zweck |
|-----------|-------|
| **OpennessSessionTest.cs** | Test für Session-Management |
| **OpennessProjectTest.cs** | Test für Projekt-Zugriff |
| **OpennessObjectQueryTest.cs** | Test für TIA-Objekt-Abfragen |
| **OpennessPipelineTest.cs** | Test für OpennessExtractionPipeline Integration |
| **OpennessErrorTest.cs** | Test für Fehlerbehandlung |
| **OpennessDiagnosticTest.cs** | Test für Diagnose-Generierung |

### Kein Testcode hier

Dieser Testplan definiert nur die **Test-Ziele und Test-Struktur**. Die C#-Test-Implementierung folgt in einem separaten Schritt.

---

*Letzte Aktualisierung: 2026-03-29*
