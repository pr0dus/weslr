using System;
using System.Collections.Generic;
using TiaCollector.Core;

namespace TiaCollector.Normalizer.Entities;

/// <summary>
/// Module Entity (Weslr)
/// </summary>
public static class ModuleEntity
{
    public static WeslrEntity FromTiaModule(TiaModule module)
    {
        var aliases = new List<string>
        {
            module.Name,
            module.Id
        };

        var metadata = new Dictionary<string, object?>
        {
            { "source_system", "siemens-tia-v20" },
            { "created_by", "normalizer-1.0.0" },
            { "last_imported", DateTime.UtcNow.ToString("O") },
            { "hardware_type", module.Type },
            { "slot", module.Slot },
            { "serial_number", module.SerialNumber },
            { "part_number", module.PartNumber }
        };

        return new WeslrEntity
        {
            Id = $"module-{module.Id}",
            Name = module.Name,
            Type = "hardware-module",
            Aliases = aliases,
            Metadata = metadata
        };
    }
}
