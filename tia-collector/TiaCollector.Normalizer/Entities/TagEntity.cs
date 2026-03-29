using System;
using System.Collections.Generic;
using TiaCollector.Core;

namespace TiaCollector.Normalizer.Entities;

/// <summary>
/// Tag Entity (Weslr)
/// </summary>
public static class TagEntity
{
    public static WeslrEntity FromTiaTag(TiaTag tag)
    {
        var aliases = new List<string>
        {
            tag.Name,
            tag.Id
        };

        var metadata = new Dictionary<string, object?>
        {
            { "source_system", "siemens-tia-v20" },
            { "created_by", "normalizer-1.0.0" },
            { "last_imported", DateTime.UtcNow.ToString("O") },
            { "data_type", tag.DataType },
            { "address", tag.Address },
            { "is_retain", tag.IsRetain },
            { "is_permanent", tag.IsPermanent }
        };

        return new WeslrEntity
        {
            Id = $"tag-{tag.Id}",
            Name = tag.Name,
            Type = "process-tag",
            Aliases = aliases,
            Metadata = metadata
        };
    }
}
