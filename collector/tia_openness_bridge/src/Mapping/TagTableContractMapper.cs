using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für Tag-Table-Informationen in TagTableContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in TagTableContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class TagTableContractMapper
{
    /// <summary>
    /// Mapping-Methode für TagTableContract.
    /// </summary>
    /// <param name="tagTableData">Die Rohdaten für die Tag-Table.</param>
    /// <returns>TagTableContract mit befüllten Feldern.</returns>
    public static TagTableContract Map(TagTableData tagTableData)
    {
        return new TagTableContract(
            Id: tagTableData.Id,
            Name: tagTableData.Name,
            PlcId: tagTableData.PlcId,
            Blocks: tagTableData.Blocks?.ToArray() ?? []
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für Tag-Table-Informationen (innerhalb des Mappers).
/// </summary>
/// <param name="Id">Eindeutige ID der Tag-Table</param>
/// <param name="Name">Name der Tag-Table</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="Blocks">Liste der enthaltenen DB-Blöcke</param>
internal sealed record TagTableData(
    string Id,
    string Name,
    string PlcId,
    TagTableBlockData[]? Blocks = null
);

/// <summary>
/// Kleines Rohdatenmodell für Tag-Table-Blöcke (innerhalb des Mappers).
/// </summary>
/// <param name="DbNumber">DB-Nummer (0-basiert)</param>
/// <param name="Name">Name des DB-Blocks</param>
/// <param name="Size">Größe des DB-Blocks in Bytes</param>
/// <param name="OrganizationBlockType">Typ des Blocks (ob, fc, fb, db, sg, dt, usw.)</param>
internal sealed record TagTableBlockData(
    int DbNumber,
    string Name,
    int Size,
    string OrganizationBlockType
);