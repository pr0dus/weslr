using System;
using System.Collections.Generic;
using System.Linq;

using SiemensToWeslr.TiaCollector.Common;
using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Extraction;

/// <summary>
/// Extraktions-Kontext für den TIA-Collector.
/// 
/// Bündelt gemeinsamen Kontext für Extraktionsschritte.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public sealed class ExtractionContext
{
    /// <summary>
    /// Initialisiert einen neuen Extraktions-Kontext.
    /// </summary>
    /// <param name="exportId">Eindeutige Kennung dieses Exports (empfohlen: UUID)</param>
    /// <param name="exportTimestampUtc">UTC-Zeitpunkt des Exports (ISO 8601)</param>
    /// <param name="collectorVersion">Version des TIA-Collectors</param>
    /// <param name="sourceSystem">Quellsystem (immer "windows")</param>
    /// <param name="projectInfo">Optionale Projekt-Informationen (ProjectContract)</param>
    public ExtractionContext(
        string exportId,
        string exportTimestampUtc,
        string collectorVersion,
        string sourceSystem,
        ProjectContract? projectInfo = null
    )
    {
        ExportId = exportId;
        ExportTimestampUtc = exportTimestampUtc;
        CollectorVersion = collectorVersion;
        SourceSystem = sourceSystem;
        ProjectInfo = projectInfo;
        Diagnostics = new List<DiagnosticEntryData>();
    }

    /// <summary>
    /// Export-Metadaten für den Export.
    /// </summary>
    public ExportMetadataContract Metadata => new(
        ExportId: ExportId,
        ExportTimestampUtc: ExportTimestampUtc,
        CollectorVersion: CollectorVersion,
        SourceSystem: SourceSystem,
        TiaPortalVersion: "V20",
        ProjectId: ProjectInfo?.Id,
        ProjectName: ProjectInfo?.Name,
        SourceFile: ProjectInfo?.Path
    );

    /// <summary>
    /// Eindeutige Kennung dieses Exports.
    /// </summary>
    public string ExportId { get; }

    /// <summary>
    /// UTC-Zeitpunkt des Exports (ISO 8601).
    /// </summary>
    public string ExportTimestampUtc { get; }

    /// <summary>
    /// Version des TIA-Collectors.
    /// </summary>
    public string CollectorVersion { get; }

    /// <summary>
    /// Quellsystem (immer "windows").
    /// </summary>
    public string SourceSystem { get; }

    /// <summary>
    /// Projekt-Informationen (optional).
    /// </summary>
    public ProjectContract? ProjectInfo { get; }

    /// <summary>
    /// Diagnose-Hinweise (Fehler und Warnungen).
    /// </summary>
    public List<DiagnosticEntryData> Diagnostics { get; }

    /// <summary>
    /// Fügt einen Diagnose-Hinweis hinzu.
    /// </summary>
    /// <param name="file">Betroffene Datei</param>
    /// <param name="line">Betroffene Zeile (optional)</param>
    /// <param name="message">Meldungstext</param>
    public void AddDiagnostic(string file, int? line, string message)
    {
        Diagnostics.Add(new DiagnosticEntryData(file, line, message));
    }

    /// <summary>
    /// Erstellt CollectorDiagnosticContract aus dem aktuellen Kontext.
    /// </summary>
    /// <param name="startTime">Startzeitpunkt (ISO 8601)</param>
    /// <param name="endTime">Endzeitpunkt (ISO 8601)</param>
    /// <param name="durationMs">Dauer in Millisekunden</param>
    /// <param name="filesProcessed">Anzahl verarbeiteter Dateien</param>
    /// <param name="objectsExtracted">Anzahl extrahierter Objekte</param>
    /// <returns>CollectorDiagnosticContract.</returns>
    public CollectorDiagnosticContract ToDiagnosticContract(
        string startTime,
        string endTime,
        long durationMs,
        int filesProcessed,
        int objectsExtracted
    )
    {
        return new CollectorDiagnosticContract(
            StartTime: startTime,
            EndTime: endTime,
            DurationMs: durationMs,
            FilesProcessed: filesProcessed,
            ObjectsExtracted: objectsExtracted,
            Errors: Diagnostics
                .Where(d => d.Message.StartsWith("Error", StringComparison.OrdinalIgnoreCase))
                .Select(d => new DiagnosticEntryContract(d.File, d.Line, d.Message))
                .ToArray(),
            Warnings: Diagnostics
                .Where(d => d.Message.StartsWith("Warning", StringComparison.OrdinalIgnoreCase))
                .Select(d => new DiagnosticEntryContract(d.File, d.Line, d.Message))
                .ToArray()
        );
    }
}
