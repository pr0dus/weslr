using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using TiaCollector.Core;

namespace FailureInvestigator.Core;

/// <summary>
/// Input für Failure Investigation
/// </summary>
public class InvestigationRequest
{
    public string AlarmText { get; set; } = string.Empty;
    public string ErrorCode { get; set; } = string.Empty;
    public string TagName { get; set; } = string.Empty;
    public string PlcName { get; set; } = string.Empty;
    public string StationName { get; set; } = string.Empty;
    public string LineName { get; set; } = string.Empty;
    public string BlockName { get; set; } = string.Empty;
}

/// <summary>
/// Normalized Input (nach Parsing)
/// </summary>
public class NormalizedInput
{
    public string NormalizedAlarmText { get; set; } = string.Empty;
    public string NormalizedErrorCode { get; set; } = string.Empty;
    public string NormalizedTagName { get; set; } = string.Empty;
    public string NormalizedPlcName { get; set; } = string.Empty;
    public string NormalizedStationName { get; set; } = string.Empty;
    public string NormalizedLineName { get; set; } = string.Empty;
    public string NormalizedBlockName { get; set; } = string.Empty;
}

/// <summary>
/// CPU-Information
/// </summary>
public class CpuInfo
{
    public string Model { get; set; } = string.Empty;
    public string Firmware { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public int MemorySizeMB { get; set; } = 0;
}

/// <summary>
/// Alarm-Model
/// </summary>
public class Alarm
{
    public string Id { get; set; } = string.Empty;
    public string Text { get; set; } = string.Empty;
    public string Severity { get; set; } = string.Empty; // error, warning, info
    public DateTime Timestamp { get; set; }
    public string TagName { get; set; } = string.Empty;
    public string ErrorCode { get; set; } = string.Empty;
}

/// <summary>
/// Failure Pattern (ähnlicher Fehler)
/// </summary>
public class FailurePattern
{
    public string Id { get; set; } = string.Empty;
    public string Text { get; set; } = string.Empty;
    public int Frequency { get; set; } = 0;
    public DateTime LastOccurrence { get; set; }
}

/// <summary>
/// Result von Failure Investigation
/// </summary>
public class InvestigationResult
{
    public bool Success { get; set; }
    public DateTime Timestamp { get; set; }
    public NormalizedInput Input { get; set; } = new();

    public List<TiaPlc> RelevantPlcs { get; set; } = new();
    public CpuInfo CpuInfo { get; set; } = new();
    public List<TiaModule> Devices { get; set; } = new();
    public List<TiaTag> RelatedTags { get; set; } = new();
    public List<TiaBlock> RelatedBlocks { get; set; } = new();
    public List<Alarm> RelatedAlarms { get; set; } = new();
    public List<FailurePattern> SimilarFailurePatterns { get; set; } = new();
    public string AffectedSection { get; set; } = string.Empty;
    public string TechnicalSummary { get; set; } = string.Empty;
}

/// <summary>
/// Interface für Failure Investigator
/// </summary>
public interface IFailureInvestigator
{
    /// <summary>
    /// Führt eine Failure Investigation durch
    /// </summary>
    Task<InvestigationResult> InvestigateAsync(InvestigationRequest request, CancellationToken ct);
}
