namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Export-Metadaten für den TIA-Roh-Export.
/// 
/// Repräsentiert die Header-Informationen für jeden Export
/// und entspricht dem metadata-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="ExportId">Eindeutige Kennung dieses Exports (empfohlen: UUID)</param>
/// <param name="ExportTimestampUtc">UTC-Zeitpunkt des Exports (ISO 8601)</param>
/// <param name="CollectorVersion">Version des TIA-Collectors</param>
/// <param name="SourceSystem">Quellsystem (immer "windows")</param>
/// <param name="TiaPortalVersion">TIA Portal Version (z. B. "V20")</param>
/// <param name="ProjectId">Optional: ID des extrahierten TIA-Projekts</param>
/// <param name="ProjectName">Optional: Name des extrahierten TIA-Projekts</param>
/// <param name="SourceFile">Optional: Absoluter Pfad zur Quelldatei</param>
public sealed record ExportMetadataContract(
    string ExportId,
    string ExportTimestampUtc,
    string CollectorVersion,
    string SourceSystem,
    string TiaPortalVersion,
    string? ProjectId = null,
    string? ProjectName = null,
    string? SourceFile = null
);