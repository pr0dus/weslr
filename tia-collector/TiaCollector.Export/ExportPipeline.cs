using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using TiaCollector.Core;

namespace TiaCollector.Export;

/// <summary>
/// Export-Konfiguration
/// </summary>
public class ExportConfig
{
    public string Format { get; set; } = "neutral-json";
    public bool Indent { get; set; } = true;
    public bool IncludeMetadata { get; set; } = true;
    public string OutputDirectory { get; set; } = "./exports";
}

/// <summary>
/// JSON-Exporter für TIA-Projekte
/// </summary>
public class JsonExporter : IExporter
{
    private readonly ExportConfig _config;

    public JsonExporter(ExportConfig? config = null)
    {
        _config = config ?? new ExportConfig();
    }

    /// <summary>
    /// Exportiert ein Projekt als JSON-String
    /// </summary>
    public async Task<string> ExportToJsonAsync(TiaProject project, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        // Create neutral JSON representation
        var exportModel = new
        {
            project.Id,
            project.Name,
            project.Version,
            project.CreatedAt,
            ModifiedAt = project.ModifiedAt,
            Owner = project.Owner,
            Comment = project.Comment,
            TiaPath = project.TiaPath,
            Metadata = _config.IncludeMetadata ? new
            {
                ExportedAt = DateTime.UtcNow,
                Format = _config.Format,
                ExporterVersion = "1.0.0"
            } : null,
            // TODO: Add PLCs, Modules, Parameters when available
            // Plcs = project.Plcs,
            // Modules = project.Modules,
            // Parameters = project.Parameters
        };

        var settings = new JsonSerializerSettings
        {
            Formatting = _config.Indent ? Formatting.Indented : Formatting.None,
            NullValueHandling = NullValueHandling.Ignore,
            Converters = { new StringEnumConverter() }
        };

        return await Task.FromResult(JsonConvert.SerializeObject(exportModel, settings)).ConfigureAwait(false);
    }

    /// <summary>
    /// Exportiert ein Projekt in eine Datei
    /// </summary>
    public async Task ExportToFileAsync(TiaProject project, string outputPath, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        var json = await ExportToJsonAsync(project, ct).ConfigureAwait(false);

        // Ensure output directory exists
        var directory = Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
        {
            Directory.CreateDirectory(directory);
        }

        await File.WriteAllTextAsync(outputPath, json, ct).ConfigureAwait(false);
    }

    /// <summary>
    /// Helper: Exportiert in Output-Verzeichnis mit automatischem Dateinamen
    /// </summary>
    public async Task ExportToOutputDirAsync(TiaProject project, CancellationToken ct)
    {
        var outputPath = Path.Combine(_config.OutputDirectory, $"{project.Name}.json");
        await ExportToFileAsync(project, outputPath, ct).ConfigureAwait(false);
    }
}

/// <summary>
/// Validator-Implementierung (Read-Only)
/// </summary>
public class Validator : IValidator
{
    public ValidationResult Validate(TiaProject project)
    {
        var result = new ValidationResult();

        if (project is null)
        {
            result.Errors.Add("Project is null.");
            return result;
        }

        if (string.IsNullOrWhiteSpace(project.Id))
            result.Errors.Add("Project ID is missing.");

        if (string.IsNullOrWhiteSpace(project.Name))
            result.Errors.Add("Project Name is missing.");

        if (project.CreatedAt == default)
            result.Errors.Add("Project CreatedAt is missing.");

        // Check TIA path if present
        if (!string.IsNullOrWhiteSpace(project.TiaPath) && !File.Exists(project.TiaPath))
            result.Warnings.Add($"TIA path does not exist: {project.TiaPath}");

        result.IsValid = result.Errors.Count == 0;
        return result;
    }

    public async Task<ValidationResult> ValidateAsync(TiaProject project, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        return Validate(project);
    }
}

/// <summary>
/// Collector-Implementierung (Orchestrierung)
/// </summary>
public class Collector : ICollector
{
    private readonly IImporter _importer;
    private readonly IValidator _validator;
    private readonly IExporter _exporter;
    private readonly ExportConfig _config;

    public Collector(IImporter importer, IValidator validator, IExporter exporter, ExportConfig? config = null)
    {
        _importer = importer ?? throw new ArgumentNullException(nameof(importer));
        _validator = validator ?? throw new ArgumentNullException(nameof(validator));
        _exporter = exporter ?? throw new ArgumentNullException(nameof(exporter));
        _config = config ?? new ExportConfig();
    }

    public async Task<TiaProject> CollectAsync(string tiaPath, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        // 1. Import
        var project = await _importer.ImportProjectAsync(tiaPath, ct).ConfigureAwait(false);

        // 2. Validate
        var validation = _validator.Validate(project);
        if (!validation.IsValid)
        {
            throw new InvalidOperationException($"Validation failed: {string.Join("; ", validation.Errors)}");
        }

        // 3. Export (optional, if caller wants to save)
        // NOTE: Export is caller's responsibility (separation of concerns)

        return project;
    }
}
