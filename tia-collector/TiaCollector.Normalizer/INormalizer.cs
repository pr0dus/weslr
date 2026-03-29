using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using TiaCollector.Core;

namespace TiaCollector.Normalizer;

/// <summary>
/// Interface für Siemens → Weslr Normalizer
/// </summary>
public interface INormalizer
{
    /// <summary>
    /// Konvertiert TIA-Project in Weslr Entity-Graph
    /// </summary>
    Task<WeslrEntityGraph> NormalizeAsync(TiaProject project, CancellationToken ct);

    /// <summary>
    /// Konvertiert Liste von PLCs in Weslr Entities
    /// </summary>
    Task<List<WeslrEntity>> NormalizePlcsAsync(IEnumerable<TiaPlc> plcs, CancellationToken ct);

    /// <summary>
    /// Konvertiert Liste von Modulen in Weslr Entities
    /// </summary>
    Task<List<WeslrEntity>> NormalizeModulesAsync(IEnumerable<TiaModule> modules, CancellationToken ct);
}

/// <summary>
/// Weslr Entity Graph
/// </summary>
public class WeslrEntityGraph
{
    public List<WeslrEntity> Entities { get; set; } = new();
    public List<WeslrRelationship> Relationships { get; set; } = new();
}

/// <summary>
/// Weslr Entity (basierend auf Python-Entitätsmodell)
/// </summary>
public class WeslrEntity
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public List<string> Aliases { get; set; } = new();
    public Dictionary<string, object?> Metadata { get; set; } = new();
}

/// <summary>
/// Weslr Relationship
/// </summary>
public class WeslrRelationship
{
    public string SourceId { get; set; } = string.Empty;
    public string TargetId { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public double Strength { get; set; } = 1.0;
    public Dictionary<string, object?> Metadata { get; set; } = new();
}
