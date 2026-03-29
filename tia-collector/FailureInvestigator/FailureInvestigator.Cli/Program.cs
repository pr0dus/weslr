using System;
using System.CommandLine;
using System.Threading;
using System.Threading.Tasks;
using FailureInvestigator.Core;
using FailureInvestigator.Analyzer;
using FailureInvestigator.Search;
using FailureInvestigator.Output;

namespace FailureInvestigator.Cli;

/// <summary>
/// CLI-Optionen
/// </summary>
public class CliOptions
{
    public string AlarmText { get; set; } = string.Empty;
    public string ErrorCode { get; set; } = string.Empty;
    public string TagName { get; set; } = string.Empty;
    public string PlcName { get; set; } = string.Empty;
    public string StationName { get; set; } = string.Empty;
    public string LineName { get; set; } = string.Empty;
    public string BlockName { get; set; } = string.Empty;
    public string OutputPath { get; set; } = "./investigations/results.json";
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
                "--alarm",
                getDefaultValue: () => string.Empty,
                description: "Alarm text (required)"),
            new Option<string>(
                "--error-code",
                getDefaultValue: () => string.Empty,
                description: "Error code"),
            new Option<string>(
                "--tag",
                getDefaultValue: () => string.Empty,
                description: "Tag name"),
            new Option<string>(
                "--plc",
                getDefaultValue: () => string.Empty,
                description: "PLC name"),
            new Option<string>(
                "--station",
                getDefaultValue: () => string.Empty,
                description: "Station name"),
            new Option<string>(
                "--line",
                getDefaultValue: () => string.Empty,
                description: "Line name"),
            new Option<string>(
                "--block",
                getDefaultValue: () => string.Empty,
                description: "Block name"),
            new Option<string>(
                "--output",
                getDefaultValue: () => "./investigations/results.json",
                description: "Output file path")
        };

        rootCommand.Description = "Failure Investigator v1.0 - MVP Failure Investigation Tool";
        rootCommand.Handler = CommandHandler.Create<CliOptions>(RunAsync);

        return rootCommand.Invoke(args);
    }

    private static async Task<int> RunAsync(CliOptions options)
    {
        try
        {
            // Validate required input
            if (string.IsNullOrWhiteSpace(options.AlarmText))
            {
                Console.Error.WriteLine("Error: --alarm is required.");
                return 1;
            }

            // Create request
            var request = new InvestigationRequest
            {
                AlarmText = options.AlarmText,
                ErrorCode = options.ErrorCode,
                TagName = options.TagName,
                PlcName = options.PlcName,
                StationName = options.StationName,
                LineName = options.LineName,
                BlockName = options.BlockName
            };

            Console.WriteLine($"Failure Investigator v1.0 - Investigating: {options.AlarmText}");

            // Initialize components
            var searchEngine = new DirectorySearchEngine("./projects");
            var analyzer = new PlcAnalyzer(); // TODO: Use hybrid analyzer
            var outputFormatter = new JsonOutputFormatter();

            // Create investigator (skeleton)
            var investigator = new FailureInvestigator(searchEngine, analyzer, outputFormatter);

            // Investigate
            var result = await investigator.InvestigateAsync(request, CancellationToken.None);

            // Save output
            await outputFormatter.SaveToFileAsync(result, options.OutputPath, CancellationToken.None);

            Console.WriteLine($"Investigation complete. Results saved to: {options.OutputPath}");
            Console.WriteLine($"Technical Summary: {result.TechnicalSummary}");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error: {ex.Message}");
            return 1;
        }
    }
}

/// <summary>
/// FailureInvestigator (skeleton implementation)
/// </summary>
public class FailureInvestigator
{
    private readonly ISearchEngine _searchEngine;
    private readonly IAnalyzer _analyzer;
    private readonly IOutputFormatter _outputFormatter;

    public FailureInvestigator(ISearchEngine searchEngine, IAnalyzer analyzer, IOutputFormatter outputFormatter)
    {
        _searchEngine = searchEngine;
        _analyzer = analyzer;
        _outputFormatter = outputFormatter;
    }

    public async Task<InvestigationResult> InvestigateAsync(InvestigationRequest request, CancellationToken ct)
    {
        // TODO: Implement full investigation logic
        return new InvestigationResult
        {
            Success = true,
            Timestamp = DateTime.UtcNow,
            Input = NormalizeInput(request),
            RelevantPlcs = new System.Collections.Generic.List<TiaPlc>(),
            CpuInfo = new CpuInfo(),
            Devices = new System.Collections.Generic.List<TiaModule>(),
            RelatedTags = new System.Collections.Generic.List<TiaTag>(),
            RelatedBlocks = new System.Collections.Generic.List<TiaBlock>(),
            RelatedAlarms = new System.Collections.Generic.List<Alarm>(),
            SimilarFailurePatterns = new System.Collections.Generic.List<FailurePattern>(),
            AffectedSection = "Unknown",
            TechnicalSummary = "Investigation completed (skeleton)."
        };
    }

    private NormalizedInput NormalizeInput(InvestigationRequest request)
    {
        return new NormalizedInput
        {
            NormalizedAlarmText = request.AlarmText?.Trim().ToLowerInvariant() ?? string.Empty,
            NormalizedErrorCode = request.ErrorCode?.Trim().ToLowerInvariant() ?? string.Empty,
            NormalizedTagName = request.TagName?.Trim().ToLowerInvariant() ?? string.Empty,
            NormalizedPlcName = request.PlcName?.Trim().ToLowerInvariant() ?? string.Empty,
            NormalizedStationName = request.StationName?.Trim().ToLowerInvariant() ?? string.Empty,
            NormalizedLineName = request.LineName?.Trim().ToLowerInvariant() ?? string.Empty,
            NormalizedBlockName = request.BlockName?.Trim().ToLowerInvariant() ?? string.Empty
        };
    }
}
