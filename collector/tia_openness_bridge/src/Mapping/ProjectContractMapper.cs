using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für Projektinformationen in ProjectContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in ProjectContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class ProjectContractMapper
{
    /// <summary>
    /// mapping-Method für ProjectContract.
    /// </summary>
    /// <param name="projectData">Die Rohdaten für das Projekt.</param>
    /// <returns>ProjectContract mit befüllten Feldern.</returns>
    public static ProjectContract Map(ProjectData projectData)
    {
        return new ProjectContract(
            Id: projectData.Id,
            Name: projectData.Name,
            Type: projectData.Type,
            Path: projectData.Path,
            Description: projectData.Description,
            LastModified: projectData.LastModified,
            Author: projectData.Author
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für Projektinformationen (innerhalb des Mappers).
/// </summary>
/// <param name="Id">Eindeutige ID des Projekts</param>
/// <param name="Name">Name des Projekts</param>
/// <param name="Type">Projekttyp (automation_project, plc_project, robotics_project)</param>
/// <param name="Path">Optional: Dateipfad zum Projekt</param>
/// <param name="Description">Optional: Beschreibung des Projekts</param>
/// <param name="LastModified">Optional: Zeitpunkt der letzten Änderung (ISO 8601)</param>
/// <param name="Author">Optional: Autor des Projekts</param>
internal sealed record ProjectData(
    string Id,
    string Name,
    string Type,
    string? Path = null,
    string? Description = null,
    string? LastModified = null,
    string? Author = null
);