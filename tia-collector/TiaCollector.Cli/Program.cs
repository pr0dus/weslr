using System;
using System.Collections.Generic;
using System.CommandLine;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using TiaCollector.Core;
using TiaCollector.TiaApi;
using TiaCollector.Export;

namespace TiaCollector.Cli;

/// <summary>
/// CLI-Optionen
/// </summary>
public class CliOptions
{
    public string InputPath { get; set; } = string.Empty;
    public string OutputPath { get; set; } = "./exports";
    public string ConfigPath { get; set; } = "./collector-config.json";
    public bool ValidateOnly { get; set; }
}

/// <summary>
/// CLI Entry Point
/// </summary>
public static class Program
{
    private static int Main(string[] args)
    {
        var rootCommand = new RootCommand
        {
            new Option<string>(
                "--input",
                getDefaultValue: () => string.Empty,
                description: "Path to TIA project file (.ap20, .ap18)"),
            new Option<string>(
                "--output",
                getDefaultValue: () => "./exports",
                description: "Output file path or directory"),
            new Option<string>(
                "--config",
                getDefaultValue: () => "./collector-config.json",
                description: "Path to configuration file"),
            new Option<bool>(
                "--validate",
                description: "Only validate project (no export)")
        };

        rootCommand.Description = "TIA Collector v1.0 - Read-only TIA Project Exporter";
        rootCommand.Handler = CommandHandler.Create<CliOptions>(RunAsync);

        return rootCommand.Invoke(args);
    }

    private static async Task<int> RunAsync(CliOptions options)
    {
        try
        {
            // Validate input
            if (string.IsNullOrWhiteSpace(options.InputPath))
            {
                Console.Error.WriteLine("Error: --input is required.");
                return 1;
            }

            if (!File.Exists(options.InputPath))
            {
                Console.Error.WriteLine($"Error: Input file not found: {options.InputPath}");
                return 1;
            }

            if (!options.InputPath.IsTiaProjectFile())
            {
                Console.Error.WriteLine($"Error: Invalid TIA project file: {options.InputPath}");
                return 1;
            }

            // Load config (simplified: direct config object for now)
            var config = LoadConfig(options.ConfigPath);

            // Ensure output directory exists
            var outputDir = Path.GetDirectoryName(options.OutputPath) ?? "./exports";
            if (!Directory.Exists(outputDir))
            {
                Directory.CreateDirectory(outputDir);
            }

            Console.WriteLine($"TIA Collector v1.0 - Reading: {options.InputPath}");

            // Initialize components
            var importer = new TiaApiImporter();
            var validator = new Validator();
            var exporter = new JsonExporter(config);

            // Create collector
            var collector = new Collector(importer, validator, exporter, config);

            // Collect
            var project = await collector.CollectAsync(options.InputPath, CancellationToken.None);

            // Validate
            var validation = validator.Validate(project);
            if (!validation.IsValid)
            {
                Console.WriteLine("Validation failed:");
                foreach (var error in validation.Errors)
                {
                    Console.WriteLine($"  - {error}");
                }
                return 1;
            }

            // Only validate mode
            if (options.ValidateOnly)
            {
                Console.WriteLine("Validation successful.");
                return 0;
            }

            // Export
            var outputPath = Path.Combine(outputDir, $"{project.Name}.json");
            await exporter.ExportToFileAsync(project, outputPath, CancellationToken.None);

            Console.WriteLine($"Export successful: {outputPath}");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error: {ex.Message}");
            return 1;
        }
    }

    private static ExportConfig LoadConfig(string configPath)
    {
        // TODO: Load from JSON file when implemented
        return new ExportConfig
        {
            Format = "neutral-json",
            Indent = true,
            IncludeMetadata = true,
            OutputDirectory = "./exports"
        };
    }
}
