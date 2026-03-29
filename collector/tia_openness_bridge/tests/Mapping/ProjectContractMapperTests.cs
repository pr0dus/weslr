using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Tests.Mapping;

/// <summary>
/// Unit-Tests für ProjectContractMapper.
/// 
/// Prüft das Mapping von ProjectData zu ProjectContract.
/// Keine Openness-Logik, keine Geschäftslogik.
/// </summary>
public class ProjectContractMapperTests
{
    private readonly ProjectContractMapper _mapper = new();

    [Fact]
    public void Map_WithValidData_ReturnsContract()
    {
        // Arrange
        var projectData = new ProjectData(
            Id: "test-project-001",
            Name: "TestProject",
            Type: "AutomationProject",
            Path: "/tmp/test-project",
            Description: "Test project for automation",
            LastModified: new DateTime(2026, 3, 29, 10, 0, 0, DateTimeKind.Utc),
            Author: "TestUser"
        );

        // Act
        var contract = _mapper.Map(projectData);

        // Assert
        Assert.NotNull(contract);
        Assert.Equal("test-project-001", contract.Id);
        Assert.Equal("TestProject", contract.Name);
        Assert.Equal("AutomationProject", contract.Type);
        Assert.Equal("/tmp/test-project", contract.Path);
        Assert.Equal("Test project for automation", contract.Description);
        Assert.Equal(new DateTime(2026, 3, 29, 10, 0, 0, DateTimeKind.Utc), contract.LastModified);
        Assert.Equal("TestUser", contract.Author);
    }

    [Fact]
    public void Map_WithNullData_ThrowsArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => _mapper.Map(null!));
    }

    [Fact]
    public void Map_WithEmptyProjectId_ReturnsContractWithEmptyId()
    {
        // Arrange
        var projectData = new ProjectData(
            Id: "",
            Name: "TestProject",
            Type: "AutomationProject",
            Path: "/tmp/test-project",
            Description: "Test project for automation",
            LastModified: new DateTime(2026, 3, 29, 10, 0, 0, DateTimeKind.Utc),
            Author: "TestUser"
        );

        // Act
        var contract = _mapper.Map(projectData);

        // Assert
        Assert.NotNull(contract);
        Assert.Equal("", contract.Id);
    }

    [Fact]
    public void Map_WithNullDescription_ReturnsContractWithNullDescription()
    {
        // Arrange
        var projectData = new ProjectData(
            Id: "test-project-001",
            Name: "TestProject",
            Type: "AutomationProject",
            Path: "/tmp/test-project",
            Description: null,
            LastModified: new DateTime(2026, 3, 29, 10, 0, 0, DateTimeKind.Utc),
            Author: "TestUser"
        );

        // Act
        var contract = _mapper.Map(projectData);

        // Assert
        Assert.NotNull(contract);
        Assert.Null(contract.Description);
    }
}
