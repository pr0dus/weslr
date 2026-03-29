using System;
using TiaCollector.Normalizer.ErrorHandling;

namespace TiaCollector.Normalizer.Relationships;

/// <summary>
/// Project ↔ PLC Relationship
/// </summary>
public static class ProjectPlcRelationship
{
    public static WeslrRelationship Create(string projectId, string plcId)
    {
        return new WeslrRelationship
        {
            SourceId = $"project-{projectId}",
            TargetId = $"plc-{plcId}",
            Type = "contains-plc",
            Strength = 1.0,
            Metadata = new Dictionary<string, object?>
            {
                { "provenance", "siemens-tia-v20-normalizer-1.0.0" },
                { "created_at", DateTime.UtcNow.ToString("O") }
            }
        };
    }
}

/// <summary>
/// Project ↔ Module Relationship
/// </summary>
public static class ProjectModuleRelationship
{
    public static WeslrRelationship Create(string projectId, string moduleId)
    {
        return new WeslrRelationship
        {
            SourceId = $"project-{projectId}",
            TargetId = $"module-{moduleId}",
            Type = "contains-module",
            Strength = 1.0,
            Metadata = new Dictionary<string, object?>
            {
                { "provenance", "siemens-tia-v20-normalizer-1.0.0" },
                { "created_at", DateTime.UtcNow.ToString("O") }
            }
        };
    }
}

/// <summary>
/// PLC ↔ Module Relationship
/// </summary>
public static class PlcModuleRelationship
{
    public static WeslrRelationship Create(string plcId, string moduleId)
    {
        return new WeslrRelationship
        {
            SourceId = $"plc-{plcId}",
            TargetId = $"module-{moduleId}",
            Type = "has-module",
            Strength = 1.0,
            Metadata = new Dictionary<string, object?>
            {
                { "provenance", "siemens-tia-v20-normalizer-1.0.0" },
                { "created_at", DateTime.UtcNow.ToString("O") }
            }
        };
    }
}
