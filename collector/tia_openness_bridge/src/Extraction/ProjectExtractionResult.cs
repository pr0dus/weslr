using System.Collections.Generic;
using System.Linq;

using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Extraction;

/// <summary>
/// Status des Projekt-Extraktionsschritts.
/// </summary>
public enum ProjectExtractionStatus
{
    /// <summary>
    /// Extraktion erfolgreich, alle Daten vorhanden.
    /// </summary>
    Success,

    /// <summary>
    /// Extraktion teilweise erfolgreich, einige Daten fehlen.
    /// </summary>
    PartialSuccess,

    /// <summary>
    /// Extraktion fehlgeschlagen.
    /// </summary>
    Failure
}

/// <summary>
/// Ergebnis eines Projekt-Extraktionsschritts.
/// 
/// Bündelt das Ergebnis eines konkreten Extraktionsschritts (Projekt).
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public sealed class ProjectExtractionResult
{
    /// <summary>
    /// Initialisiert einen neuen Projekt-Extraktionsergebnis.
    /// </summary>
    /// <param name="context">Der Extraktions-Kontext.</param>
    /// <param name="projectContract">Das extrahierte ProjectContract (optional).</param>
    /// <param name="diagnostics">Diagnose-Hinweise.</param>
    /// <param name="status">Status des Extraktionsschritts.</param>
    public ProjectExtractionResult(
        ExtractionContext context,
        ProjectContract? projectContract = null,
        IEnumerable<DiagnosticEntryData>? diagnostics = null,
        ProjectExtractionStatus status = ProjectExtractionStatus.Success
    )
    {
        Context = context;
        ProjectContract = projectContract;
        Diagnostics = (diagnostics ?? context.Diagnostics).ToList();
        Status = status;
    }

    /// <summary>
    /// Der Extraktions-Kontext.
    /// </summary>
    public ExtractionContext Context { get; }

    /// <summary>
    /// Das extrahierte ProjectContract (optional).
    /// </summary>
    public ProjectContract? ProjectContract { get; }

    /// <summary>
    /// Diagnose-Hinweise (Fehler und Warnungen).
    /// </summary>
    public List<DiagnosticEntryData> Diagnostics { get; }

    /// <summary>
    /// Status des Extraktionsschritts.
    /// </summary>
    public ProjectExtractionStatus Status { get; }

    /// <summary>
    /// Prüft, ob der Schritt erfolgreich war.
    /// </summary>
    public bool IsSuccess => Status == ProjectExtractionStatus.Success;

    /// <summary>
    /// Prüft, ob der Schritt teilweise erfolgreich war.
    /// </summary>
    public bool IsPartialSuccess => Status == ProjectExtractionStatus.PartialSuccess;

    /// <summary>
    /// Prüft, ob der Schritt fehlgeschlagen ist.
    /// </summary>
    public bool IsFailure => Status == ProjectExtractionStatus.Failure;

    /// <summary>
    /// Prüft, ob ein Projekt-Contract existiert.
    /// </summary>
    public bool HasProject => ProjectContract != null;
}
