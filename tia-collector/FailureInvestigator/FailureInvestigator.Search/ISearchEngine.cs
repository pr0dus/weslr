using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using FailureInvestigator.Core;

namespace FailureInvestigator.Search;

/// <summary>
/// ISearchEngine-Interface
/// </summary>
public interface ISearchEngine
{
    Task<List<string>> SearchProjectsAsync(string lineName, string stationName, CancellationToken ct);
    Task<List<TiaPlc>> SearchPlcsAsync(string lineName, string stationName, string plcName, CancellationToken ct);
    Task<List<TiaModule>> SearchModulesAsync(string lineName, string stationName, string plcName, CancellationToken ct);
    Task<List<TiaTag>> SearchTagsAsync(string lineName, string stationName, string tagName, CancellationToken ct);
    Task<List<Alarm>> SearchAlarmsAsync(string lineName, string alarmText, CancellationToken ct);
}

/// <summary>
/// Directory-basierte Suche
/// </summary>
public class DirectorySearchEngine : ISearchEngine
{
    private readonly string _basePath;

    public DirectorySearchEngine(string basePath = "./projects")
    {
        _basePath = basePath;
    }

    public Task<List<string>> SearchProjectsAsync(string lineName, string stationName, CancellationToken ct)
    {
        // TODO: Implement directory traversal
        return Task.FromResult(new List<string>());
    }

    public Task<List<TiaPlc>> SearchPlcsAsync(string lineName, string stationName, string plcName, CancellationToken ct)
    {
        // TODO: Implement search logic
        return Task.FromResult(new List<TiaPlc>());
    }

    public Task<List<TiaModule>> SearchModulesAsync(string lineName, string stationName, string plcName, CancellationToken ct)
    {
        // TODO: Implement search logic
        return Task.FromResult(new List<TiaModule>());
    }

    public Task<List<TiaTag>> SearchTagsAsync(string lineName, string stationName, string tagName, CancellationToken ct)
    {
        // TODO: Implement search logic
        return Task.FromResult(new List<TiaTag>());
    }

    public Task<List<Alarm>> SearchAlarmsAsync(string lineName, string alarmText, CancellationToken ct)
    {
        // TODO: Implement search logic
        return Task.FromResult(new List<Alarm>());
    }
}

/// <summary>
/// Helper für Dateisystem-Suche
/// </summary>
public static class FileSystemSearch
{
    /// <summary>
    /// Sucht nach Dateien in Verzeichnisbaum
    /// </summary>
    public static List<string> FindFiles(string basePath, string pattern, string? subDir = null)
    {
        var result = new List<string>();
        var searchPath = string.IsNullOrEmpty(subDir) ? basePath : Path.Combine(basePath, subDir);

        if (Directory.Exists(searchPath))
        {
            result.AddRange(Directory.GetFiles(searchPath, pattern, SearchOption.AllDirectories));
        }

        return result;
    }

    /// <summary>
    /// Lädt JSON-Datei und deserialisiert
    /// </summary>
    public static T? LoadJsonFile<T>(string filePath) where T : class, new()
    {
        try
        {
            if (!File.Exists(filePath)) return null;
            var json = File.ReadAllText(filePath);
            return Newtonsoft.Json.JsonConvert.DeserializeObject<T>(json);
        }
        catch
        {
            return null;
        }
    }

    /// <summary>
    /// Extrahiert Suchpfade aus NormalizedInput
    /// </summary>
    public static List<string> ExtractSearchPaths(NormalizedInput input)
    {
        var paths = new List<string>();

        if (!string.IsNullOrEmpty(input.NormalizedLineName))
        {
            paths.Add($"projects/{input.NormalizedLineName}");
        }

        if (!string.IsNullOrEmpty(input.NormalizedStationName))
        {
            paths.Add($"projects/{input.NormalizedLineName}/stations/{input.NormalizedStationName}");
        }

        if (!string.IsNullOrEmpty(input.NormalizedPlcName))
        {
            paths.Add($"projects/{input.NormalizedLineName}/stations/{input.NormalizedStationName}/plcs/{input.NormalizedPlcName}");
        }

        return paths;
    }
}
