using System.Collections.Generic;
using System.Linq;

using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Extraction;

/// <summary>
/// Ergebnis eines Topologie-/Relations-Extraktionsschritts.
/// 
/// Bündelt das Ergebnis eines konkreten Extraktionsschritts (Topology Relations).
/// Orientiert sich am Muster der bisherigen ExtractionResult-Typen.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public sealed class TopologyRelationExtractionResult
{
    /// <summary>
    /// Initialisiert einen neuen Topologie-/Relations-Extraktionsergebnis.
    /// </summary>
    /// <param name="context">Der Extraktions-Kontext.</param>
    /// <param name="topologyRelations">Die extrahierten TopologyRelationContract-Objekte.</param>
    /// <param name="diagnostics">Diagnose-Hinweise.</param>
    /// <param name="status">Status des Extraktionsschritts.</param>
    public TopologyRelationExtractionResult(
        ExtractionContext context,
        IEnumerable<TopologyRelationContract> topologyRelations,
        IEnumerable<DiagnosticEntryData>? diagnostics = null,
        ProjectExtractionStatus status = ProjectExtractionStatus.Success
    )
    {
        Context = context;
        TopologyRelations = topologyRelations.ToList();
        Diagnostics = (diagnostics ?? context.Diagnostics).ToList();
        Status = status;
    }

    /// <summary>
    /// Der Extraktions-Kontext.
    /// </summary>
    public ExtractionContext Context { get; }

    /// <summary>
    /// Die extrahierten TopologyRelationContract-Objekte.
    /// </summary>
    public List<TopologyRelationContract> TopologyRelations { get; }

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
    /// Prüft, ob mindestens eine Topologie-Relation extrahiert wurde.
    /// </summary>
    public bool HasTopologyRelations => TopologyRelations.Count > 0;

    /// <summary>
    /// Anzahl extrahierter Topologie-Relationen.
    /// </summary>
    public int TopologyRelationCount => TopologyRelations.Count;
}
