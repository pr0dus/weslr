using System;
using System.Collections.Generic;
using TiaCollector.Core;

namespace TiaCollector.Normalizer.Entities;

/// <summary>
/// Block Entity (Weslr)
/// </summary>
public static class BlockEntity
{
    public static WeslrEntity FromTiaBlock(TiaBlock block)
    {
        var aliases = new List<string>
        {
            block.Name,
            block.Id
        };

        var metadata = new Dictionary<string, object?>
        {
            { "source_system", "siemens-tia-v20" },
            { "created_by", "normalizer-1.0.0" },
            { "last_imported", DateTime.UtcNow.ToString("O") },
            { "block_type", block.Type },
            { "block_number", block.Number },
            { "network_count", block.NetworkCount },
            { "line_count", block.LineCount }
        };

        return new WeslrEntity
        {
            Id = $"block-{block.Id}",
            Name = block.Name,
            Type = "tia-block",
            Aliases = aliases,
            Metadata = metadata
        };
    }
}
