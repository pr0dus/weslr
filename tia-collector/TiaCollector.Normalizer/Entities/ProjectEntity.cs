using System;
using System.Collections.Generic;
using TiaCollector.Core;

namespace TiaCollector.Normalizer.Entities;

/// <summary>
/// Project Entity (Weslr)
/// </summary>
public static class ProjectEntity
{
    public static WeslrEntity FromTiaProject(TiaProject project)
    {
        var aliases = new List<string>
        {
            project.Name,
            project.Id
        };

        var metadata = new Dictionary<string, object?>
        {
            { "source_system", "siemens-tia-v20" },
            { "created_by", "normalizer-1.0.0" },
            { "last_imported", DateTime.UtcNow.ToString("O") },
            { "version", project.Version },
            { "owner", project.Owner },
            { "comment", project.Comment },
            { "tia_path", project.TiaPath }
        };

        return new WeslrEntity
        {
            Id = $"project-{project.Id}",
            Name = project.Name,
            Type = "tia-project",
            Aliases = aliases,
            Metadata = metadata
        };
    }
}
