using SiemensToWeslr.TiaCollector.Common;
using SiemensToWeslr.TiaCollector.Openness;

namespace SiemensToWeslr.TiaCollector.Openness;

/// <summary>
/// Status des Openness Session-Schritts.
/// </summary>
public enum OpennessSessionStatus
{
    /// <summary>
    /// Session erfolgreich geöffnet.
    /// </summary>
    Success,

    /// <summary>
    /// Session fehlgeschlagen.
    /// </summary>
    Failure
}

/// <summary>
/// Ergebnis eines Openness Session-Schritts.
/// 
/// Bündelt das Ergebnis des Openness Session-Zugriffs.
/// Orientiert sich am Muster der ExtractionResult-Typen.
/// Keine Openness-Logik, keine Geschäftslogik.
/// </summary>
public sealed class OpennessSessionResult
{
    /// <summary>
    /// Initialisiert einen neuen Openness Session-Ergebnis.
    /// </summary>
    /// <param name="sessionContext">Der Openness Session-Kontext.</param>
    /// <param name="diagnostics">Diagnose-Hinweise.</param>
    /// <param name="status">Status des Session-Schritts.</param>
    public OpennessSessionResult(
        OpennessSessionContext sessionContext,
        IEnumerable<DiagnosticEntryData>? diagnostics = null,
        OpennessSessionStatus status = OpennessSessionStatus.Success
    )
    {
        SessionContext = sessionContext;
        Diagnostics = (diagnostics ?? Enumerable.Empty<DiagnosticEntryData>()).ToList();
        Status = status;
    }

    /// <summary>
    /// Der Openness Session-Kontext.
    /// </summary>
    public OpennessSessionContext SessionContext { get; }

    /// <summary>
    /// Diagnose-Hinweise (Fehler und Warnungen).
    /// </summary>
    public List<DiagnosticEntryData> Diagnostics { get; }

    /// <summary>
    /// Status des Session-Schritts.
    /// </summary>
    public OpennessSessionStatus Status { get; }

    /// <summary>
    /// Prüft, ob der Schritt erfolgreich war.
    /// </summary>
    public bool IsSuccess => Status == OpennessSessionStatus.Success;

    /// <summary>
    /// Prüft, ob der Schritt fehlgeschlagen ist.
    /// </summary>
    public bool IsFailure => Status == OpennessSessionStatus.Failure;

    /// <summary>
    /// Prüft, ob ein Session-Kontext existiert.
    /// </summary>
    public bool HasSession => SessionContext != null;
}
