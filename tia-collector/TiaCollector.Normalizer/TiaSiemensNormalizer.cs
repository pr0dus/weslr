using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using TiaCollector.Core;
using TiaCollector.Normalizer.ErrorHandling;
using TiaCollector.Normalizer.Entities;

namespace TiaCollector.Normalizer;

/// <summary>
/// Siemens → Weslr Normalizer Implementation
/// </summary>
public class TiaSiemensNormalizer : INormalizer, IDisposable
{
    private readonly List<WeslrEntity> _entities = new();
    private readonly List<WeslrRelationship> _relationships = new();
    private bool _disposed = false;

    public async Task<WeslrEntityGraph> NormalizeAsync(TiaProject project, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        // Reset state
        _entities.Clear();
        _relationships.Clear();

        // Map project
        var projectEntity = ProjectEntity.FromTiaProject(project);
        _entities.Add(projectEntity);

        // Map PLCs (if available)
        // NOTE: In skeleton, PLCs are not yet imported from TIA-Collector
        // Uncomment when TIA-Collector implements ImportPlcsAsync
        // var plcs = await ImportPlcsAsync(project.TiaPath, ct).ConfigureAwait(false);
        // foreach (var plc in plcs)
        // {
        //     _entities.Add(PlcEntity.FromTiaPlc(plc));
        //     _relationships.Add(new WeslrRelationship
        //     {
        //         SourceId = projectEntity.Id,
        //         TargetId = plcEntity.Id,
        //         Type = "contains-plc",
        //         Strength = 1.0
        //     });
        // }

        // Map Modules (if available)
        // foreach (var module in modules)
        // {
        //     _entities.Add(ModuleEntity.FromTiaModule(module));
        // }

        // Map Parameters (if available)
        // foreach (var parameter in parameters)
        // {
        //     _entities.Add(ParameterEntity.FromTiaParameter(parameter));
        // }

        // Map Tags (if available)
        // foreach (var tag in tags)
        // {
        //     _entities.Add(TagEntity.FromTiaTag(tag));
        // }

        // Map Blocks (if available)
        // foreach (var block in blocks)
        // {
        //     _entities.Add(BlockEntity.FromTiaBlock(block));
        // }

        return new WeslrEntityGraph
        {
            Entities = _entities,
            Relationships = _relationships
        };
    }

    public async Task<List<WeslrEntity>> NormalizePlcsAsync(IEnumerable<TiaPlc> plcs, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        var entities = new List<WeslrEntity>();
        foreach (var plc in plcs)
        {
            entities.Add(PlcEntity.FromTiaPlc(plc));
        }

        return entities;
    }

    public async Task<List<WeslrEntity>> NormalizeModulesAsync(IEnumerable<TiaModule> modules, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        var entities = new List<WeslrEntity>();
        foreach (var module in modules)
        {
            entities.Add(ModuleEntity.FromTiaModule(module));
        }

        return entities;
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            _entities.Clear();
            _relationships.Clear();
            _disposed = true;
        }
        GC.SuppressFinalize(this);
    }
}
