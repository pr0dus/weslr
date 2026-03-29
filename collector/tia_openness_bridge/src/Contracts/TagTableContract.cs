namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Tag-Table-Informationen für den TIA-Roh-Export.
/// 
/// Repräsentiert Tag-Tables aus dem TIA Portal V20 (z. B. "Global-Tags").
/// Entspricht dem tag_tables-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="Id">Eindeutige ID der Tag-Table</param>
/// <param name="Name">Name der Tag-Table</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="Blocks">Liste der enthaltenen DB-Blöcke</param>
public sealed record TagTableContract(
    string Id,
    string Name,
    string PlcId,
    TagTableBlockContract[] Blocks
);

/// <summary>
/// Ein Block innerhalb einer Tag-Table (DB-Block).
/// </summary>
/// <param name="DbNumber">DB-Nummer (0-basiert)</param>
/// <param name="Name">Name des DB-Blocks</param>
/// <param name="Size">Größe des DB-Blocks in Bytes</param>
/// <param name="OrganizationBlockType">Typ des Blocks (ob, fc, fb, db, sg, dt, usw.)</param>
public sealed record TagTableBlockContract(
    int DbNumber,
    string Name,
    int Size,
    string OrganizationBlockType
);