using System.Collections.Generic;
using System.Linq;

using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Extraction;

/// <summary>
/// Ergebnis eines CPU-Extraktionsschritts.
/// 
/// Bündelt das Ergebnis eines konkreten Extraktionsschritts (CPUs).
/// Orientiert sich am Muster von ProjectExtractionResult, DeviceExtractionResult und PlcExtractionResult.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public sealed class CpuExtractionResult
{
    /// <summary>
    /// Initialisiert einen neuen CPU-Extraktionsergebnis.
    /// </summary>
    /// <param name="context">Der Extraktions-Kontext.</param>
    /// <param name="cpus">Die extrahierten CpuContract-Objekte.</param>
    /// <param name="diagnostics">Diagnose-Hinweise.</param>
    /// <param name="status">Status des Extraktionsschritts.</param>
    public CpuExtractionResult(
        ExtractionContext context,
        IEnumerable<CpuContract> cpus,
        IEnumerable<DiagnosticEntryData>? diagnostics = null,
        ProjectExtractionStatus status = ProjectExtractionStatus.Success
    )
    {
        Context = context;
        Cpus = cpus.ToList();
        Diagnostics = (diagnostics ?? context.Diagnostics).ToList();
        Status = status;
    }

    /// <summary>
    /// Der Extraktions-Kontext.
    /// </summary>
    public ExtractionContext Context { get; }

    /// <summary>
    /// Die extrahierten CpuContract-Objekte.
    /// </summary>
    public List<CpuContract> Cpus { get; }

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
    /// Prüft, ob mindestens eine CPU extrahiert wurde.
    /// </summary>
    public bool HasCpus => Cpus.Count > 0;

    /// <summary>
    /// Anzahl extrahierter CPUs.
    /// </summary>
    public int CpuCount => Cpus.Count;
}
