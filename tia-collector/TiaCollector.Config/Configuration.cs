using System;
using System.IO;
using Newtonsoft.Json;

namespace TiaCollector.Config;

/// <summary>
/// Gesamtkonfiguration für den Collector
/// </summary>
public class CollectorConfig
{
    public CollectorSettings Collector { get; set; } = new();
    public ExportConfig Export { get; set; } = new();
    public LoggingConfig Logging { get; set; } = new();
}

/// <summary>
/// Collector-Einstellungen
/// </summary>
public class CollectorSettings
{
    public int TimeoutSeconds { get; set; } = 300;
    public bool ReadOnly { get; set; } = true;
    public bool ValidateBeforeExport { get; set; } = true;
}

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
/// Logging-Konfiguration
/// </summary>
public class LoggingConfig
{
    public string Level { get; set; } = "Info";
    public string FilePath { get; set; } = "./logs/collector.log";
}

/// <summary>
/// Konfigurations-Reader
/// </summary>
public static class ConfigurationReader
{
    /// <summary>
    /// Lädt Konfiguration aus JSON-Datei
    /// </summary>
    public static CollectorConfig Load(string configPath)
    {
        if (!File.Exists(configPath))
        {
            // Return default config if file not found
            return new CollectorConfig();
        }

        var json = File.ReadAllText(configPath);
        var config = JsonConvert.DeserializeObject<CollectorConfig>(json) ?? new CollectorConfig();

        // Fill in defaults for null properties
        if (config.Collector == null) config.Collector = new CollectorSettings();
        if (config.Export == null) config.Export = new ExportConfig();
        if (config.Logging == null) config.Logging = new LoggingConfig();

        return config;
    }

    /// <summary>
    /// Speichert Konfiguration in JSON-Datei
    /// </summary>
    public static void Save(CollectorConfig config, string configPath)
    {
        var json = JsonConvert.SerializeObject(config, Formatting.Indented);
        File.WriteAllText(configPath, json);
    }

    /// <summary>
    /// Speichert Standard-Konfiguration in eine Datei
    /// </summary>
    public static void SaveDefaults(string configPath)
    {
        var config = new CollectorConfig
        {
            Collector = new CollectorSettings { TimeoutSeconds = 300, ReadOnly = true, ValidateBeforeExport = true },
            Export = new ExportConfig { Format = "neutral-json", Indent = true, IncludeMetadata = true, OutputDirectory = "./exports" },
            Logging = new LoggingConfig { Level = "Info", FilePath = "./logs/collector.log" }
        };

        Save(config, configPath);
    }
}
