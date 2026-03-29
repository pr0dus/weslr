using System;
using System.Collections.Generic;
using System.IO;

namespace TiaCollector.Core;

/// <summary>
/// ValidationResult für Validierungs-Resultate
/// </summary>
public class ValidationResult
{
    public bool IsValid { get; set; }
    public List<string> Warnings { get; set; } = new();
    public List<string> Errors { get; set; } = new();

    public static ValidationResult Success() => new() { IsValid = true };
    public static ValidationResult Failure(params string[] errors) => new() { IsValid = false, Errors = new List<string>(errors) };
}

/// <summary>
/// TIA Project Model (core data structure)
/// </summary>
public record TiaProject(
    string Id,
    string Name,
    string Version,
    DateTime CreatedAt,
    DateTime? ModifiedAt = null,
    string? Owner = null,
    string? Comment = null,
    string? TiaPath = null);

/// <summary>
/// TIA PLC Model
/// </summary>
public record TiaPlc(
    string Id,
    string Name,
    string Type,
    string Version,
    int? Rack = null,
    int? Slot = null);

/// <summary>
/// TIA Module Model (Hardware Module)
/// </summary>
public record TiaModule(
    string Id,
    string Name,
    string Type,
    int Slot,
    string? SerialNumber = null,
    string? PartNumber = null);

/// <summary>
/// TIA Parameter Model (Configuration Parameter)
/// </summary>
public record TiaParameter(
    string Id,
    string Name,
    string DataType,
    object? Value,
    bool IsReadOnly = false,
    bool IsProtected = false);

/// <summary>
/// TIA Tag Model (Process Tag)
/// </summary>
public record TiaTag(
    string Id,
    string Name,
    string DataType,
    string Address,
    bool IsRetain = false,
    bool IsPermanent = false);

/// <summary>
/// TIA Block Model (OB, FB, FC, SFB, SFC)
/// </summary>
public record TiaBlock(
    string Id,
    string Name,
    string Type,       // OB, FB, FC, SFB, SFC
    int Number,
    int? NetworkCount = null,
    int? LineCount = null);

/// <summary>
/// Helper: TIA Openness API Error Codes
/// </summary>
public static class TiaApiErrors
{
    public const int E_FAIL = -2147467259;
    public const int E_ACCESSDENIED = -2147024891;
    public const int E_INVALIDARG = -2147024809;
    public const int E_NOTIMPL = -2147467283;
}

/// <summary>
/// Helper: Extension Methods
/// </summary>
public static class Extensions
{
    /// <summary>
    /// Prüft, ob die Datei eine gültige TIA-Project-Datei ist
    /// </summary>
    public static bool IsTiaProjectFile(this string path)
    {
        if (string.IsNullOrWhiteSpace(path)) return false;
        return Path.GetExtension(path.ToLowerInvariant()) is ".ap18" or ".ap20" or ".ap21";
    }

    /// <summary>
    /// Erstellt Output-Pfad basierend auf Input-Dateiname
    /// </summary>
    public static string ToOutputPath(this string inputPath, string outputDir, string extension = ".json")
    {
        var fileName = Path.GetFileNameWithoutExtension(inputPath);
        return Path.Combine(outputDir, $"{fileName}{extension}");
    }
}
