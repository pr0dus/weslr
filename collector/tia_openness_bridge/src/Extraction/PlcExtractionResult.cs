using System.Collections.Generic;
using System.Linq;

using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Extraction;

/// <summary>
/// Ergebnis eines PLC-Extraktionsschritts.
/// 
/// Bündelt das Ergebnis eines konkreten Extraktionsschritts (PLCs).
/// Orientiert sich am Muster von ProjectExtractionResult und DeviceExtractionResult.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public sealed class PlcExtractionResult
{
    /// <summary>
    /// Initialisiert einen neuen PLC-Extraktionsergebnis.
    /// </summary>
    /// <param name="context">Der Extraktions-Kontext.</param>
    /// <param name="plcs">Die extrahierten PlcContract-Objekte.</param>
    /// <param name="diagnostics">Diagnose-Hinweise.</param>
    /// <param name="status">Status des Extraktionsschritts.</param>
    public PlcExtractionResult(
        ExtractionContext context,
        IEnumerable<PlcContract> plcs,
        IEnumerable<DiagnosticEntryData>? diagnostics = null,
        ProjectExtractionStatus status = ProjectExtractionStatus.Success
    )
    {
        Context = context;
        Plcs = plcs.ToList();
        Diagnostics = (diagnostics ?? context.Diagnostics).ToList();
        Status = status;
    }

    /// <summary>
    /// Der Extraktions-Kontext.
    /// </summary>
    public ExtractionContext Context { get; }

    /// <summary>
    /// Die extrahierten PlcContract-Objekte.
    /// </summary>
    public List<PlcContract> Plcs { get; }

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
    /// Prüft, ob mindestens eine PLC extrahiert wurde.
    /// </summary>
    public bool HasPlcs => Plcs.Count > 0;

    /// <summary>
    /// Anzahl extrahierter PLCs.
    /// </summary>
    public int PlcCount => Plcs.Count;
}
