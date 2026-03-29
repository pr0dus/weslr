using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using FailureInvestigator.Core;
using Newtonsoft.Json;

namespace FailureInvestigator.Output;

/// <summary>
/// IOutputFormatter-Interface
/// </summary>
public interface IOutputFormatter
{
    Task<string> FormatAsync(InvestigationResult result, CancellationToken ct);
    Task SaveToFileAsync(InvestigationResult result, string outputPath, CancellationToken ct);
}

/// <summary>
/// JSON-Output-Formatter
/// </summary>
public class JsonOutputFormatter : IOutputFormatter
{
    private readonly JsonSerializerSettings _settings;

    public JsonOutputFormatter()
    {
        _settings = new JsonSerializerSettings
        {
            Formatting = Formatting.Indented,
            NullValueHandling = NullValueHandling.Ignore,
            Converters = { new Newtonsoft.Json.Converters.StringEnumConverter() }
        };
    }

    public async Task<string> FormatAsync(InvestigationResult result, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        var output = new
        {
            success = result.Success,
            timestamp = result.Timestamp.ToString("O"),
            input = new
            {
                alarmText = result.Input.NormalizedAlarmText,
                errorCode = result.Input.NormalizedErrorCode,
                tagName = result.Input.NormalizedTagName,
                plcName = result.Input.NormalizedPlcName,
                stationName = result.Input.NormalizedStationName,
                lineName = result.Input.NormalizedLineName,
                blockName = result.Input.NormalizedBlockName
            },
            result = new
            {
                relevant_plcs = result.RelevantPlcs,
                cpu_info = result.CpuInfo,
                devices = result.Devices,
                related_tags = result.RelatedTags,
                related_blocks = result.RelatedBlocks,
                related_alarms = result.RelatedAlarms,
                similar_failure_patterns = result.SimilarFailurePatterns,
                affected_section = result.AffectedSection,
                technical_summary = result.TechnicalSummary
            }
        };

        return await Task.FromResult(JsonConvert.SerializeObject(output, _settings)).ConfigureAwait(false);
    }

    public async Task SaveToFileAsync(InvestigationResult result, string outputPath, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        var json = await FormatAsync(result, ct).ConfigureAwait(false);
        var directory = Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
        {
            Directory.CreateDirectory(directory);
        }

        await File.WriteAllTextAsync(outputPath, json, ct).ConfigureAwait(false);
    }
}
