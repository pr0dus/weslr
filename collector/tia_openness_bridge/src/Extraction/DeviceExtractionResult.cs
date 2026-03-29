using System.Collections.Generic;
using System.Linq;

using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Extraction;

/// <summary>
/// Ergebnis eines Geräte-Extraktionsschritts.
/// 
/// Bündelt das Ergebnis eines konkreten Extraktionsschritts (Geräte).
/// Orientiert sich am Muster von ProjectExtractionResult.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public sealed class DeviceExtractionResult
{
    /// <summary>
    /// Initialisiert einen neuen Geräte-Extraktionsergebnis.
    /// </summary>
    /// <param name="context">Der Extraktions-Kontext.</param>
    /// <param name="devices">Die extrahierten DeviceContract-Objekte.</param>
    /// <param name="diagnostics">Diagnose-Hinweise.</param>
    /// <param name="status">Status des Extraktionsschritts.</param>
    public DeviceExtractionResult(
        ExtractionContext context,
        IEnumerable<DeviceContract> devices,
        IEnumerable<DiagnosticEntryData>? diagnostics = null,
        ProjectExtractionStatus status = ProjectExtractionStatus.Success
    )
    {
        Context = context;
        Devices = devices.ToList();
        Diagnostics = (diagnostics ?? context.Diagnostics).ToList();
        Status = status;
    }

    /// <summary>
    /// Der Extraktions-Kontext.
    /// </summary>
    public ExtractionContext Context { get; }

    /// <summary>
    /// Die extrahierten DeviceContract-Objekte.
    /// </summary>
    public List<DeviceContract> Devices { get; }

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
    /// Prüft, ob mindestens ein Gerät extrahiert wurde.
    /// </summary>
    public bool HasDevices => Devices.Count > 0;

    /// <summary>
    /// Anzahl extrahierter Geräte.
    /// </summary>
    public int DeviceCount => Devices.Count;
}
