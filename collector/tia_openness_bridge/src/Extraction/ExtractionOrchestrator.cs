using SiemensToWeslr.TiaCollector.Contracts;
using SiemensToWeslr.TiaCollector.Mapping;
using SiemensToWeslr.TiaCollector.Openness;

namespace SiemensToWeslr.TiaCollector.Extraction;

/// <summary>
/// Orchestrator für die Extraktion von Engineering-Daten aus TIA.
/// 
/// Koordiniert den gesamten Extraktionsprozess von der Rohdatenerfassung bis zum vollständigen Export.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public sealed class ExtractionOrchestrator
{
    private readonly TiaExportContractAssembler _assembler = new();

    /// <summary>
    /// Extrahiert aus einem vollständigen Kontext alle Engineering-Daten und erstellt den TiaExportContract.
    /// </summary>
    /// <param name="context">Der Extraktions-Kontext.</param>
    /// <returns>ExtractionAssemblyResult mit vollständigem TiaExportContract.</returns>
    public ExtractionAssemblyResult ExtractAll(ExtractionContext context)
    {
        // Openness Session vorbereiten
        var opennessSessionContext = new OpennessSessionContext(
            sessionHandle: context.ProjectInfo?.Id ?? string.Empty,
            projectPath: context.ProjectInfo?.Path ?? string.Empty,
            projectName: context.ProjectInfo?.Name ?? string.Empty
        );

        // Openness Extraction-Pipeline starten
        var opennessPipeline = new OpennessExtractionPipeline(opennessSessionContext);
        var opennessPipelineResult = opennessPipeline.RunPipeline(
            new[] { "Project", "Devices", "Plcs", "Cpus", "Modules", "TagTables", "Tags", "Blocks", "Topology", "Alarms" }
        );

        // Projekt extrahieren
        var projectResult = ExtractProject(context);

        // Geräte extrahieren
        var deviceResult = ExtractDevices(context);

        // PLCs extrahieren
        var plcResult = ExtractPlcs(context);

        // CPUs extrahieren
        var cpuResult = ExtractCpus(context);

        // Module extrahieren
        var moduleResult = ExtractModules(context);

        // TagTables extrahieren
        var tagTableResult = ExtractTagTables(context);

        // Tags extrahieren
        var tagResult = ExtractTags(context);

        // Program-Blocks extrahieren
        var blockResult = ExtractProgramBlocks(context);

        // Topology Relations extrahieren
        var topologyResult = ExtractTopologyRelations(context);

        // Alarme extrahieren
        var alarmResult = ExtractAlarms(context);

        // Diagnose extrahieren
        var diagnosticResult = ExtractDiagnostics(context);

        // Assemblieren
        var fullExport = _assembler.Assemble(
            metadata: context.Metadata,
            project: projectResult.ProjectContract,
            devices: deviceResult.Devices.ToArray(),
            plcs: plcResult.Plcs.ToArray(),
            cpus: cpuResult.Cpus.ToArray(),
            modules: moduleResult.Modules.ToArray(),
            tagTables: tagTableResult.TagTables.ToArray(),
            tags: tagResult.Tags.ToArray(),
            programBlocks: blockResult.ProgramBlocks.ToArray(),
            topologyRelations: topologyResult.TopologyRelations.ToArray(),
            alarms: alarmResult.Alarms.ToArray(),
            collectorDiagnostics: diagnosticResult.CollectorDiagnosticContract
        );

        // Ergebnis zurückgeben
        return new ExtractionAssemblyResult(
            context: context,
            fullExport: fullExport,
            diagnostics: CombineDiagnostics(
                opennessPipelineResult.Diagnostics,
                projectResult.Diagnostics,
                deviceResult.Diagnostics,
                plcResult.Diagnostics,
                cpuResult.Diagnostics,
                moduleResult.Diagnostics,
                tagTableResult.Diagnostics,
                tagResult.Diagnostics,
                blockResult.Diagnostics,
                topologyResult.Diagnostics,
                alarmResult.Diagnostics,
                diagnosticResult.Diagnostics
            ),
            status: DetermineOverallStatus(
                opennessPipelineResult.Status,
                projectResult.Status,
                deviceResult.Status,
                plcResult.Status,
                cpuResult.Status,
                moduleResult.Status,
                tagTableResult.Status,
                tagResult.Status,
                blockResult.Status,
                topologyResult.Status,
                alarmResult.Status,
                diagnosticResult.Status
            )
        );
    }

    //region Helper Methods

    private ProjectExtractionResult ExtractProject(ExtractionContext context)
    {
        if (context.ProjectInfo == null)
        {
            context.AddDiagnostic("ProjectExtraction", null, "Kein Projekt verfügbar");
            return new ProjectExtractionResult(context, null, status: ProjectExtractionStatus.Failure);
        }

        // Simulation: Mapping direkt anwenden
        var mapper = new ProjectContractMapper();
        var contract = mapper.Map(
            new ProjectData(
                Id: context.ProjectInfo.Id,
                Name: context.ProjectInfo.Name,
                Type: context.ProjectInfo.Type,
                Path: context.ProjectInfo.Path,
                Description: context.ProjectInfo.Description,
                LastModified: context.ProjectInfo.LastModified,
                Author: context.ProjectInfo.Author
            )
        );

        return new ProjectExtractionResult(context, contract, status: ProjectExtractionStatus.Success);
    }

    private DeviceExtractionResult ExtractDevices(ExtractionContext context)
    {
        // Simulation: Leere Liste (echte Extraktion kommt später)
        return new DeviceExtractionResult(context, [], status: ProjectExtractionStatus.Success);
    }

    private PlcExtractionResult ExtractPlcs(ExtractionContext context)
    {
        // Simulation: Leere Liste (echte Extraktion kommt später)
        return new PlcExtractionResult(context, [], status: ProjectExtractionStatus.Success);
    }

    private CpuExtractionResult ExtractCpus(ExtractionContext context)
    {
        // Simulation: Leere Liste (echte Extraktion kommt später)
        return new CpuExtractionResult(context, [], status: ProjectExtractionStatus.Success);
    }

    private ModuleExtractionResult ExtractModules(ExtractionContext context)
    {
        // Simulation: Leere Liste (echte Extraktion kommt später)
        return new ModuleExtractionResult(context, [], status: ProjectExtractionStatus.Success);
    }

    private TagTableExtractionResult ExtractTagTables(ExtractionContext context)
    {
        // Simulation: Leere Liste (echte Extraktion kommt später)
        return new TagTableExtractionResult(context, [], status: ProjectExtractionStatus.Success);
    }

    private TagExtractionResult ExtractTags(ExtractionContext context)
    {
        // Simulation: Leere Liste (echte Extraktion kommt später)
        return new TagExtractionResult(context, [], status: ProjectExtractionStatus.Success);
    }

    private ProgramBlockExtractionResult ExtractProgramBlocks(ExtractionContext context)
    {
        // Simulation: Leere Liste (echte Extraktion kommt später)
        return new ProgramBlockExtractionResult(context, [], status: ProjectExtractionStatus.Success);
    }

    private TopologyRelationExtractionResult ExtractTopologyRelations(ExtractionContext context)
    {
        // Simulation: Leere Liste (echte Extraktion kommt später)
        return new TopologyRelationExtractionResult(context, [], status: ProjectExtractionStatus.Success);
    }

    private AlarmExtractionResult ExtractAlarms(ExtractionContext context)
    {
        // Simulation: Leere Liste (echte Extraktion kommt später)
        return new AlarmExtractionResult(context, [], status: ProjectExtractionStatus.Success);
    }

    private CollectorDiagnosticExtractionResult ExtractDiagnostics(ExtractionContext context)
    {
        var contract = context.ToDiagnosticContract(
            startTime: context.ExportTimestampUtc,
            endTime: context.ExportTimestampUtc,
            durationMs: 0,
            filesProcessed: 0,
            objectsExtracted: 0
        );

        return new CollectorDiagnosticExtractionResult(context, contract, status: ProjectExtractionStatus.Success);
    }

    private List<DiagnosticEntryData> CombineDiagnostics(params IEnumerable<DiagnosticEntryData>[][] diagnosticLists)
    {
        var allDiagnostics = new List<DiagnosticEntryData>();

        foreach (var list in diagnosticLists)
        {
            if (list != null)
            {
                foreach (var item in list)
                {
                    if (item != null)
                    {
                        allDiagnostics.AddRange(item);
                    }
                }
            }
        }

        return allDiagnostics;
    }

    private ProjectExtractionStatus DetermineOverallStatus(params ProjectExtractionStatus[] statuses)
    {
        if (statuses.Contains(ProjectExtractionStatus.Failure))
            return ProjectExtractionStatus.Failure;

        if (statuses.Contains(ProjectExtractionStatus.PartialSuccess))
            return ProjectExtractionStatus.PartialSuccess;

        return ProjectExtractionStatus.Success;
    }

    //endregion
}