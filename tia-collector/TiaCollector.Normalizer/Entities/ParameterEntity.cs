using System;
using System.Collections.Generic;
using TiaCollector.Core;

namespace TiaCollector.Normalizer.Entities;

/// <summary>
/// Parameter Entity (Weslr)
/// </summary>
public static class ParameterEntity
{
    public static WeslrEntity FromTiaParameter(TiaParameter parameter)
    {
        var aliases = new List<string>
        {
            parameter.Name,
            parameter.Id
        };

        var metadata = new Dictionary<string, object?>
        {
            { "source_system", "siemens-tia-v20" },
            { "created_by", "normalizer-1.0.0" },
            { "last_imported", DateTime.UtcNow.ToString("O") },
            { "data_type", parameter.DataType },
            { "value", parameter.Value?.ToString() },
            { "is_read_only", parameter.IsReadOnly },
            { "is_protected", parameter.IsProtected }
        };

        return new WeslrEntity
        {
            Id = $"parameter-{parameter.Id}",
            Name = parameter.Name,
            Type = "configuration-parameter",
            Aliases = aliases,
            Metadata = metadata
        };
    }
}
