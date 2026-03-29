using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für Diagnose-Informationen in CollectorDiagnosticContract.
/// 
/// Wandelt kleine interne Rohdatenstrukturen in CollectorDiagnosticContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class CollectorDiagnosticContractMapper
{
    /// <summary>
    /// Mapping-Methode für CollectorDiagnosticContract.
    /// </summary>
    /// <param name="diagnosticData">Die Rohdaten für die Diagnose.</param>
    /// <returns>CollectorDiagnosticContract mit befüllten Feldern.</returns>
    public static CollectorDiagnosticContract Map(DiagnosticData diagnosticData)
    {
        return new CollectorDiagnosticContract(
            StartTime: diagnosticData.StartTime,
            EndTime: diagnosticData.EndTime,
            DurationMs: diagnosticData.DurationMs,
            FilesProcessed: diagnosticData.FilesProcessed,
            ObjectsExtracted: diagnosticData.ObjectsExtracted,
            Errors: diagnosticData.Errors?.ToArray() ?? [],
            Warnings: diagnosticData.Warnings?.ToArray() ?? []
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für Diagnose-Informationen (innerhalb des Mappers).
/// </summary>
/// <param name="StartTime">Startzeitpunkt des Exports (ISO 8601)</param>
/// <param name="EndTime">Endzeitpunkt des Exports (ISO 8601)</param>
/// <param name="DurationMs">Dauer in Millisekunden</param>
/// <param name="FilesProcessed">Anzahl verarbeiteter Dateien</param>
/// <param name="ObjectsExtracted">Anzahl extrahierter Objekte</param>
/// <param name="Errors">Liste der Fehler</param>
/// <param name="Warnings">Liste der Warnungen</param>
internal sealed record DiagnosticData(
    string StartTime,
    string EndTime,
    long DurationMs,
    int FilesProcessed,
    int ObjectsExtracted,
    DiagnosticEntryData[]? Errors = null,
    DiagnosticEntryData[]? Warnings = null
);

/// <summary>
/// Kleines Rohdatenmodell für Diagnose-Einträge (Fehler oder Warnung) (innerhalb des Mappers).
/// </summary>
/// <param name="File">Betroffene Datei</param>
/// <param name="Line">Betroffene Zeile (optional)</param>
/// <param name="Message">Meldungstext</param>
internal sealed record DiagnosticEntryData(
    string File,
    int? Line = null,
    string Message = ""
);