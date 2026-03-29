namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Projektinformationen für den TIA-Roh-Export.
/// 
/// Repräsentiert die project-Informationen aus dem TIA Portal V20.
/// Entspricht dem project-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="Id">Eindeutige ID des TIA-Projekts (UUID)</param>
/// <param name="Name">Name des TIA-Projekts</param>
/// <param name="Type">Projekttyp (automation_project, plc_project, robotics_project)</param>
/// <param name="Path">Optional: Dateipfad zum Projekt</param>
/// <param name="Description">Optional: Beschreibung des Projekts</param>
/// <param name="LastModified">Optional: Zeitpunkt der letzten Änderung (ISO 8601)</param>
/// <param name="Author">Optional: Autor des Projekts</param>
public sealed record ProjectContract(
    string Id,
    string Name,
    string Type,
    string? Path = null,
    string? Description = null,
    string? LastModified = null,
    string? Author = null
);