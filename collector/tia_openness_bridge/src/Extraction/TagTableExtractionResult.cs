using System.Collections.Generic;
using System.Linq;

using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Extraction;

/// <summary>
/// Ergebnis eines TagTable-Extraktionsschritts.
/// 
/// Bündelt das Ergebnis eines konkreten Extraktionsschritts (TagTables).
/// Orientiert sich am Muster der bisherigen ExtractionResult-Typen.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public sealed class TagTableExtractionResult
{
    /// <summary>
    /// Initialisiert einen neuen TagTable-Extraktionsergebnis.
    /// </summary>
    /// <param name="context">Der Extraktions-Kontext.</param>
    /// <param name="tagTables">Die extrahierten TagTableContract-Objekte.</param>
    /// <param name="diagnostics">Diagnose-Hinweise.</param>
    /// <param name="status">Status des Extraktionsschritts.</param>
    public TagTableExtractionResult(
        ExtractionContext context,
        IEnumerable<TagTableContract> tagTables,
        IEnumerable<DiagnosticEntryData>? diagnostics = null,
        ProjectExtractionStatus status = ProjectExtractionStatus.Success
    )
    {
        Context = context;
        TagTables = tagTables.ToList();
        Diagnostics = (diagnostics ?? context.Diagnostics).ToList();
        Status = status;
    }

    /// <summary>
    /// Der Extraktions-Kontext.
    /// </summary>
    public ExtractionContext Context { get; }

    /// <summary>
    /// Die extrahierten TagTableContract-Objekte.
    /// </summary>
    public List<TagTableContract> TagTables { get; }

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
    /// Prüft, ob mindestens eine TagTable extrahiert wurde.
    /// </summary>
    public bool HasTagTables => TagTables.Count > 0;

    /// <summary>
    /// Anzahl extrahierter TagTables.
    /// </summary>
    public int TagTableCount => TagTables.Count;
}
