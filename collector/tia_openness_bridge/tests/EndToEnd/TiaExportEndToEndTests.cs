using SiemensToWeslr.TiaCollector.Contracts;
using SiemensToWeslr.TiaCollector.Mapping;
using SiemensToWeslr.TiaCollector.Serialization;

namespace SiemensToWeslr.TiaCollector.Tests.EndToEnd;

/// <summary>
/// End-to-End-Test für TIA Export von Contract bis JSON.
/// 
/// Prüft den kompletten Ablauf: Assembler -> Serializer -> JSON.
/// Keine Openness-Logik, keine Geschäftslogik.
/// </summary>
public class TiaExportEndToEndTests
{
    [Fact]
    public void FullExportPipeline_WithValidData_ReturnsJson()
    {
        // Arrange
        var assembler = new TiaExportContractAssembler();
        var serializer = new TiaExportJsonSerializer();

        var metadata = new ExportMetadata(
            version: "1.0.0",
            generator: "TiaBridge",
            generatedAtUtc: new DateTime(2026, 3, 29, 12, 0, 0, DateTimeKind.Utc)
        );

        var project = new ProjectContract(
            id: "test-project-001",
            name: "TestProject",
            type: "AutomationProject",
            path: "/tmp/test-project",
            description: "Test project",
            lastModified: new DateTime(2026, 3, 29, 10, 0, 0, DateTimeKind.Utc),
            author: "TestUser"
        );

        // Act
        var contract = assembler.Assemble(
            metadata: metadata,
            project: project,
            devices: Array.Empty<DeviceContract>(),
            plcs: Array.Empty<PlcContract>(),
            cpus: Array.Empty<CpuContract>(),
            modules: Array.Empty<ModuleContract>(),
            tagTables: Array.Empty<TagTableContract>(),
            tags: Array.Empty<TagContract>(),
            programBlocks: Array.Empty<ProgramBlockContract>(),
            topologyRelations: Array.Empty<TopologyRelationContract>(),
            alarms: Array.Empty<AlarmContract>(),
            collectorDiagnostics: Array.Empty<DiagnosticContract>()
        );

        var json = serializer.Serialize(contract);

        // Assert
        Assert.NotNull(json);
        Assert.Contains("test-project-001", json);
        Assert.Contains("TestProject", json);
        Assert.Contains("TestUser", json);
    }

    [Fact]
    public void FullExportPipeline_WithEmptyData_ReturnsValidJson()
    {
        // Arrange
        var assembler = new TiaExportContractAssembler();
        var serializer = new TiaExportJsonSerializer();

        var metadata = new ExportMetadata(
            version: "1.0.0",
            generator: "TiaBridge",
            generatedAtUtc: new DateTime(2026, 3, 29, 12, 0, 0, DateTimeKind.Utc)
        );

        // Act
        var contract = assembler.Assemble(
            metadata: metadata,
            project: null,
            devices: Array.Empty<DeviceContract>(),
            plcs: Array.Empty<PlcContract>(),
            cpus: Array.Empty<CpuContract>(),
            modules: Array.Empty<ModuleContract>(),
            tagTables: Array.Empty<TagTableContract>(),
            tags: Array.Empty<TagContract>(),
            programBlocks: Array.Empty<ProgramBlockContract>(),
            topologyRelations: Array.Empty<TopologyRelationContract>(),
            alarms: Array.Empty<AlarmContract>(),
            collectorDiagnostics: Array.Empty<DiagnosticContract>()
        );

        var json = serializer.Serialize(contract);

        // Assert
        Assert.NotNull(json);
        Assert.Contains("\"metadata\"", json);
        Assert.Contains("\"devices\":[],", json);
        Assert.Contains("\"plcs\":[],", json);
    }

    [Fact]
    public void FullExportPipeline_JsonRoundTrip_PreservesData()
    {
        // Arrange
        var assembler = new TiaExportContractAssembler();
        var serializer = new TiaExportJsonSerializer();

        var originalMetadata = new ExportMetadata(
            version: "1.0.0",
            generator: "TiaBridge",
            generatedAtUtc: new DateTime(2026, 3, 29, 12, 0, 0, DateTimeKind.Utc)
        );

        var originalProject = new ProjectContract(
            id: "test-project-001",
            name: "TestProject",
            type: "AutomationProject",
            path: "/tmp/test-project",
            description: "Test project",
            lastModified: new DateTime(2026, 3, 29, 10, 0, 0, DateTimeKind.Utc),
            author: "TestUser"
        );

        // Act
        var originalContract = assembler.Assemble(
            metadata: originalMetadata,
            project: originalProject,
            devices: Array.Empty<DeviceContract>(),
            plcs: Array.Empty<PlcContract>(),
            cpus: Array.Empty<CpuContract>(),
            modules: Array.Empty<ModuleContract>(),
            tagTables: Array.Empty<TagTableContract>(),
            tags: Array.Empty<TagContract>(),
            programBlocks: Array.Empty<ProgramBlockContract>(),
            topologyRelations: Array.Empty<TopologyRelationContract>(),
            alarms: Array.Empty<AlarmContract>(),
            collectorDiagnostics: Array.Empty<DiagnosticContract>()
        );

        var json = serializer.Serialize(originalContract);
        var deserializedContract = serializer.Deserialize(json);

        // Assert
        Assert.NotNull(deserializedContract);
        Assert.Equal(originalContract.ProjectId, deserializedContract.ProjectId);
        Assert.Equal(originalContract.ProjectName, deserializedContract.ProjectName);
        Assert.Equal(originalContract.Metadata?.Version, deserializedContract.Metadata?.Version);
    }
}
