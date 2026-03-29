using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für Programmbaustein-Informationen in ProgramBlockContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in ProgramBlockContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class ProgramBlockContractMapper
{
    /// <summary>
    /// Mapping-Methode für ProgramBlockContract.
    /// </summary>
    /// <param name="blockData">Die Rohdaten für den Block.</param>
    /// <returns>ProgramBlockContract mit befüllten Feldern.</returns>
    public static ProgramBlockContract Map(ProgramBlockData blockData)
    {
        return new ProgramBlockContract(
            Id: blockData.Id,
            Name: blockData.Name,
            Type: blockData.Type,
            PlcId: blockData.PlcId,
            Number: blockData.Number,
            Networks: blockData.Networks?.ToArray() ?? [],
            Interface: blockData.Interface,
            Comment: blockData.Comment
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für Programmbaustein-Informationen (innerhalb des Mappers).
/// </summary>
/// <param name="Id">Eindeutige ID des Blocks</param>
/// <param name="Name">Name des Blocks</param>
/// <param name="Type">Block-Typ (ob, fc, fb, db, sg, dt, usw.)</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="Number">Block-Nummer (z. B. OB1, FC10, DB42)</param>
/// <param name="Networks">Liste der Netzwerke im Block</param>
/// <param name="Interface">Optionale Schnittstelle (input, output, in_out, temp, static, constant)</param>
/// <param name="Comment">Optional: Kommentar zum Block</param>
internal sealed record ProgramBlockData(
    string Id,
    string Name,
    string Type,
    string PlcId,
    int Number,
    NetworkData[]? Networks = null,
    BlockInterfaceData? Interface = null,
    string? Comment = null
);

/// <summary>
/// Kleines Rohdatenmodell für Netzwerke (innerhalb des Mappers).
/// </summary>
/// <param name="NetworkNumber">Netzwerk-Nummer</param>
/// <param name="NetworkName">Name des Netzwerks</param>
/// <param name="NetworkContent">Inhalt des Netzwerks (STL-Quellcode)</param>
internal sealed record NetworkData(
    int NetworkNumber,
    string? NetworkName = null,
    string? NetworkContent = null
);

/// <summary>
/// Kleines Rohdatenmodell für Block-Schnittstelle (innerhalb des Mappers).
/// </summary>
/// <param name="Input">Optionale Input-Liste</param>
/// <param name="Output">Optionale Output-Liste</param>
/// <param name="InOut">Optionale InOut-Liste</param>
/// <param name="Temp">Optionale Temp-Liste</param>
/// <param name="Static">Optionale Static-Liste</param>
/// <param name="Constant">Optionale Constant-Liste</param>
internal sealed record BlockInterfaceData(
    BlockInterfaceFieldData[]? Input = null,
    BlockInterfaceFieldData[]? Output = null,
    BlockInterfaceFieldData[]? InOut = null,
    BlockInterfaceFieldData[]? Temp = null,
    BlockInterfaceFieldData[]? Static = null,
    BlockInterfaceFieldData[]? Constant = null
);

/// <summary>
/// Kleines Rohdatenmodell für Block-Schnittstellen-Felder (innerhalb des Mappers).
/// </summary>
/// <param name="Name">Name des Felds</param>
/// <param name="DataType">Datentyp</param>
/// <param name="InitialValue">Optionaler Anfangswert</param>
internal sealed record BlockInterfaceFieldData(
    string Name,
    string DataType,
    string? InitialValue = null
);