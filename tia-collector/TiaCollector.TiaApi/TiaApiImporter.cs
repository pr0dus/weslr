using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using TiaCollector.Core;

namespace TiaCollector.TiaApi;

/// <summary>
/// Wrapper für TIA Portal Openness API (COM)
/// Requires: TIA Portal V20+ installed
/// </summary>
public class TiaOpennessClient : IDisposable
{
    private readonly Siemens.Engineering.Application _tiaApp;
    private bool _disposed = false;

    public TiaOpennessClient()
    {
        _tiaApp = new Siemens.Engineering.Application();
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            _disposed = true;
            // Optional: Cleanup COM objects here if needed
        }
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Öffnet ein TIA-Projekt
    /// </summary>
    /// <exception cref="InvalidOperationException">Wenn TIA nicht verfügbar ist</exception>
    public Siemens.Engineering.Project OpenProject(string projectPath)
    {
        try
        {
            return _tiaApp.Projects.Open(projectPath);
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Failed to open TIA project: {projectPath}", ex);
        }
    }

    /// <summary>
    /// Schließt ein TIA-Projekt
    /// </summary>
    public void CloseProject(Siemens.Engineering.Project project)
    {
        project?.Close();
    }

    /// <summary>
    /// Listet alle PLCs in einem Projekt
    /// </summary>
    public IEnumerable<Siemens.Engineering.Plcs.Plc> GetPlcs(Siemens.Engineering.Project project)
    {
        return project.Devices.GetPlcs();
    }

    /// <summary>
    /// Listet alle Hardware-Module einer PLC
    /// </summary>
    public IEnumerable<Siemens.Engineering.Hardware.Device> GetModules(Siemens.Engineering.Plcs.Plc plc)
    {
        return plc.DeviceTree.GetDevices();
    }

    /// <summary>
    /// Listet alle Blöcke einer PLC
    /// </summary>
    public IEnumerable<Siemens.Engineering.Blocks.BlockGroup> GetBlockGroups(Siemens.Engineering.Plcs.Plc plc)
    {
        return plc.BlockGroup;
    }
}

/// <summary>
/// Importer-Implementierung via TIA Openness API
/// </summary>
public class TiaApiImporter : IImporter, IDisposable
{
    private readonly TiaOpennessClient _client;
    private bool _disposed = false;

    public TiaApiImporter()
    {
        _client = new TiaOpennessClient();
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            _client.Dispose();
            _disposed = true;
        }
        GC.SuppressFinalize(this);
    }

    public async Task<TiaProject> ImportProjectAsync(string tiaPath, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(tiaPath))
            throw new ArgumentException("Project path cannot be null or empty.", nameof(tiaPath));

        if (!tiaPath.IsTiaProjectFile())
            throw new ArgumentException("Invalid TIA project file extension.", nameof(tiaPath));

        ct.ThrowIfCancellationRequested();

        try
        {
            using var project = _client.OpenProject(tiaPath);

            var projectInfo = project.Info;
            var createdAt = projectInfo.CreationDate != DateTime.MinValue ? projectInfo.CreationDate : DateTime.Now;
            var modifiedAt = projectInfo.LastSaveDate != DateTime.MinValue ? projectInfo.LastSaveDate : (DateTime?)null;
            var owner = projectInfo.Author ?? "Unknown";
            var comment = projectInfo.Comment ?? string.Empty;

            var tiaProject = new TiaProject(
                Id: project.Id.ToString(),
                Name: project.Name,
                Version: projectInfo.Version ?? "Unknown",
                CreatedAt: createdAt,
                ModifiedAt: modifiedAt,
                Owner: owner,
                Comment: comment,
                TiaPath: tiaPath
            );

            // Import PLCs as separate step (can be large)
            var plcs = await ImportPlcsAsync(tiaPath, ct).ConfigureAwait(false);
            // TODO: Attach PLCs to TiaProject (extend model if needed)

            return tiaProject;
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Failed to import TIA project: {tiaPath}", ex);
        }
    }

    public async Task<IEnumerable<TiaPlc>> ImportPlcsAsync(string tiaPath, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        var plcs = new List<TiaPlc>();
        using var project = _client.OpenProject(tiaPath);

        foreach (var tiaPlc in _client.GetPlcs(project))
        {
            var plcId = tiaPlc.Id.ToString();
            var plcName = tiaPlc.Name;
            var plcType = tiaPlc.TypeName ?? "Unknown";
            var plcVersion = tiaPlc.Version?.ToString() ?? "Unknown";

            plcs.Add(new TiaPlc(plcId, plcName, plcType, plcVersion));
        }

        return plcs;
    }

    public async Task<IEnumerable<TiaModule>> ImportModulesAsync(string tiaPlcId, CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();

        // TODO: Implement module import (requires project context)
        // For now, return empty list as skeleton placeholder
        return new List<TiaModule>();
    }
}
