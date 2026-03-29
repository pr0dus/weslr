using System;
using System.IO;
using Newtonsoft.Json;

namespace FailureInvestigator.Config;

/// <summary>
/// Gesamtkonfiguration für Failure Investigator
/// </summary>
public class InvestigatorConfig
{
    public InvestigationSettings Investigation { get; set; } = new();
    public SearchSettings Search { get; set; } = new();
    public OutputSettings Output { get; set; } = new();
    public LoggingSettings Logging { get; set; } = new();
}

/// <summary>
/// Investigation-Einstellungen
/// </summary>
public class InvestigationSettings
{
    public int TimeoutSeconds { get; set; } = 60;
    public bool RequireAlarmText { get; set; } = true;
    public bool GenerateTechnicalSummary { get; set; } = true;
}

/// <summary>
/// Search-Einstellungen
/// </summary>
public class SearchSettings
{
    public string BasePath { get; set; } = "./projects";
    public int MaxResults { get; set; } = 10;
    public bool IncludeSimilarAlarms { get; set; } = true;
    public bool IncludeFailurePatterns { get; set; } = true;
}

/// <summary>
/// Output-Einstellungen
/// </summary>
public class OutputSettings
{
    public string Format { get; set; } = "json";
    public bool Indent { get; set; } = true;
    public string OutputDirectory { get; set; } = "./investigations";
}

/// <summary>
/// Logging-Einstellungen
/// </summary>
public class LoggingSettings
{
    public string Level { get; set; } = "Info";
    public string FilePath { get; set; } = "./logs/investigator.log";
}

/// <summary>
/// Konfigurations-Reader
/// </summary>
public static class ConfigurationReader
{
    /// <summary>
    /// Lädt Konfiguration aus JSON-Datei
    /// </summary>
    public static InvestigatorConfig Load(string configPath)
    {
        if (!File.Exists(configPath))
        {
            // Return default config if file not found
            return new InvestigatorConfig();
        }

        var json = File.ReadAllText(configPath);
        var config = JsonConvert.DeserializeObject<InvestigatorConfig>(json) ?? new InvestigatorConfig();

        // Fill in defaults for null properties
        if (config.Investigation == null) config.Investigation = new InvestigationSettings();
        if (config.Search == null) config.Search = new SearchSettings();
        if (config.Output == null) config.Output = new OutputSettings();
        if (config.Logging == null) config.Logging = new LoggingSettings();

        return config;
    }

    /// <summary>
    /// Speichert Konfiguration in JSON-Datei
    /// </summary>
    public static void Save(InvestigatorConfig config, string configPath)
    {
        var json = JsonConvert.SerializeObject(config, Formatting.Indented);
        File.WriteAllText(configPath, json);
    }

    /// <summary>
    /// Speichert Standard-Konfiguration in eine Datei
    /// </summary>
    public static void SaveDefaults(string configPath)
    {
        var config = new InvestigatorConfig
        {
            Investigation = new InvestigationSettings { TimeoutSeconds = 60, RequireAlarmText = true, GenerateTechnicalSummary = true },
            Search = new SearchSettings { BasePath = "./projects", MaxResults = 10, IncludeSimilarAlarms = true, IncludeFailurePatterns = true },
            Output = new OutputSettings { Format = "json", Indent = true, OutputDirectory = "./investigations" },
            Logging = new LoggingSettings { Level = "Info", FilePath = "./logs/investigator.log" }
        };

        Save(config, configPath);
    }
}
