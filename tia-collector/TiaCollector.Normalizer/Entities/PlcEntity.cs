using System;
using System.Collections.Generic;
using TiaCollector.Core;

namespace TiaCollector.Normalizer.Entities;

/// <summary>
/// PLC Entity (Weslr)
/// </summary>
public static class PlcEntity
{
    public static WeslrEntity FromTiaPlc(TiaPlc plc)
    {
        var aliases = new List<string>
        {
            plc.Name,
            plc.Id
        };

        var metadata = new Dictionary<string, object?>
        {
            { "source_system", "siemens-tia-v20" },
            { "created_by", "normalizer-1.0.0" },
            { "last_imported", DateTime.UtcNow.ToString("O") },
            { "hardware_type", plc.Type },
            { "firmware_version", plc.Version },
            { "rack", plc.Rack },
            { "slot", plc.Slot }
        };

        return new WeslrEntity
        {
            Id = $"plc-{plc.Id}",
            Name = plc.Name,
            Type = "plc",
            Aliases = aliases,
            Metadata = metadata
        };
    }
}
