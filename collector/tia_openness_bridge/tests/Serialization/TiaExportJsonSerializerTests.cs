using SiemensToWeslr.TiaCollector.Serialization;

namespace SiemensToWeslr.TiaCollector.Tests.Serialization;

/// <summary>
/// Unit-Tests für TiaExportJsonSerializer.
/// 
/// Prüft die JSON-Serialisierung von TiaExportContract.
/// Keine Openness-Logik, keine Geschäftslogik.
/// </summary>
public class TiaExportJsonSerializerTests
{
    [Fact]
    public void Serialize_WithValidContract_ReturnsJsonString()
    {
        // Arrange
        var contract = new TiaExportContract(
            projectId: "test-project-001",
            projectName: "TestProject",
            exportTimestampUtc: new DateTime(2026, 3, 29, 12, 0, 0, DateTimeKind.Utc),
            metadata: new ExportMetadata(
                version: "1.0.0",
                generator: "TiaBridge",
                generatedAtUtc: new DateTime(2026, 3, 29, 12, 0, 0, DateTimeKind.Utc)
            ),
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
            diagnostics: Array.Empty<DiagnosticContract>()
        );

        var serializer = new TiaExportJsonSerializer();

        // Act
        var json = serializer.Serialize(contract);

        // Assert
        Assert.NotNull(json);
        Assert.Contains("test-project-001", json);
        Assert.Contains("TestProject", json);
    }

    [Fact]
    public void Deserialize_WithValidJson_ReturnsContract()
    {
        // Arrange
        var json = @"{
            ""projectId"": ""test-project-001"",
            ""projectName"": ""TestProject"",
            ""exportTimestampUtc"": ""2026-03-29T12:00:00Z"",
            ""metadata"": {
                ""version"": ""1.0.0"",
                ""generator"": ""TiaBridge"",
                ""generatedAtUtc"": ""2026-03-29T12:00:00Z""
            },
            ""project"": null,
            ""devices"": [],
            ""plcs"": [],
            ""cpus"": [],
            ""modules"": [],
            ""tagTables"": [],
            ""tags"": [],
            ""programBlocks"": [],
            ""topologyRelations"": [],
            ""alarms"": [],
            ""diagnostics"": []
        }";

        var serializer = new TiaExportJsonSerializer();

        // Act
        var contract = serializer.Deserialize(json);

        // Assert
        Assert.NotNull(contract);
        Assert.Equal("test-project-001", contract.ProjectId);
        Assert.Equal("TestProject", contract.ProjectName);
    }

    [Fact]
    public void Serialize_WithNullContract_ThrowsArgumentNullException()
    {
        // Arrange
        var serializer = new TiaExportJsonSerializer();

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => serializer.Serialize(null!));
    }

    [Fact]
    public void Deserialize_WithNullJson_ThrowsArgumentNullException()
    {
        // Arrange
        var serializer = new TiaExportJsonSerializer();

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => serializer.Deserialize(null!));
    }

    [Fact]
    public void Deserialize_WithInvalidJson_ThrowsJsonException()
    {
        // Arrange
        var serializer = new TiaExportJsonSerializer();
        var invalidJson = @"{ invalid json }";

        // Act & Assert
        Assert.Throws<JsonException>(() => serializer.Deserialize(invalidJson));
    }
}
