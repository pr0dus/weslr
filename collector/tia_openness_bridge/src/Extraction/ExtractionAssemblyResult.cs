using System.Collections.Generic;
using System.Linq;

using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Extraction;

/// <summary>
/// Ergebnis der Extraktionsassemblierung.
/// 
/// Bündelt alle Extraktionsergebnisse zu einem vollständigen TiaExportContract.
/// Orientiert sich am Muster der bisherigen ExtractionResult-Typen.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public sealed class ExtractionAssemblyResult
{
    /// <summary>
    /// Initialisiert einen neuen Extraktionsassemblierungsergebnis.
    /// </summary>
    /// <param name="context">Der Extraktions-Kontext.</param>
    /// <param name="fullExport">Der vollständige TiaExportContract.</param>
    /// <param name="diagnostics">Diagnose-Hinweise.</param>
    /// <param name="status">Status des Assemblierungsschritts.</param>
    public ExtractionAssemblyResult(
        ExtractionContext context,
        TiaExportContract fullExport,
        IEnumerable<DiagnosticEntryData>? diagnostics = null,
        ProjectExtractionStatus status = ProjectExtractionStatus.Success
    )
    {
        Context = context;
        FullExport = fullExport;
        Diagnostics = (diagnostics ?? context.Diagnostics).ToList();
        Status = status;
    }

    /// <summary>
    /// Der Extraktions-Kontext.
    /// </summary>
    public ExtractionContext Context { get; }

    /// <summary>
    /// Der vollständige TiaExportContract.
    /// </summary>
    public TiaExportContract FullExport { get; }

    /// <summary>
    /// Diagnose-Hinweise (Fehler und Warnungen).
    /// </summary>
    public List<DiagnosticEntryData> Diagnostics { get; }

    /// <summary>
    /// Status des Assemblierungsschritts.
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
    /// Prüft, ob ein vollständiger Export existiert.
    /// </summary>
    public bool HasFullExport => FullExport != null;
}
