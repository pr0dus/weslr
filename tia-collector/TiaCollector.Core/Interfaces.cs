using System;
using System.Threading;
using System.Threading.Tasks;

namespace TiaCollector.Core;

/// <summary>
/// Importer-Interface: Lädt TIA-Daten (nur read-only, kein TIA-Schreiben)
/// </summary>
public interface IImporter
{
    /// <summary>
    /// Importiert ein gesamtes TIA-Projekt
    /// </summary>
    /// <param name="tiaPath">Pfad zur TIA-Project-Datei (.ap20, .ap18)</param>
    /// <param name="ct">Cancellation Token</param>
    /// <returns>TiaProject mit allen untergeordneten Objekten</returns>
    Task<TiaProject> ImportProjectAsync(string tiaPath, CancellationToken ct);

    /// <summary>
    /// Importiert alle PLCs aus einem TIA-Projekt
    /// </summary>
    Task<IEnumerable<TiaPlc>> ImportPlcsAsync(string tiaPath, CancellationToken ct);

    /// <summary>
    /// Importiert alle Module einer PLC
    /// </summary>
    Task<IEnumerable<TiaModule>> ImportModulesAsync(string tiaPlcId, CancellationToken ct);
}

/// <summary>
/// Collector-Interface: Koordiniert Import → Validate → Export
/// </summary>
public interface ICollector
{
    /// <summary>
    /// Führt den kompletten Collect-Vorgang aus
    /// </summary>
    Task<TiaProject> CollectAsync(string tiaPath, CancellationToken ct);
}

/// <summary>
/// Exporter-Interface: Schreibt TIA-Daten in JSON (neutral, schema-basiert)
/// </summary>
public interface IExporter
{
    /// <summary>
    /// Exportiert ein Projekt als JSON-String
    /// </summary>
    Task<string> ExportToJsonAsync(TiaProject project, CancellationToken ct);

    /// <summary>
    /// Exportiert ein Projekt in eine Datei
    /// </summary>
    Task ExportToFileAsync(TiaProject project, string outputPath, CancellationToken ct);
}

/// <summary>
/// Validator-Interface: Prüft Datenintegrität (keine TIA-Modifikationen)
/// </summary>
public interface IValidator
{
    /// <summary>
    /// Validiert ein Projekt (sync)
    /// </summary>
    ValidationResult Validate(TiaProject project);

    /// <summary>
    /// Validiert ein Projekt (async)
    /// </summary>
    Task<ValidationResult> ValidateAsync(TiaProject project, CancellationToken ct);
}
