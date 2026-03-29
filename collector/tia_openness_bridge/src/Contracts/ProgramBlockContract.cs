namespace SiemensToWeslr.TiaCollector.Contracts;

/// <summary>
/// Programmbaustein-Informationen für den TIA-Roh-Export.
/// 
/// Repräsentiert Blocks (OB, FC, FB, DB) aus dem TIA Portal V20.
/// Entspricht dem program_blocks-Bereich in schemas/tia_export.schema.json.
/// 
/// Verwendet sealed record für unveränderliche, strukturierte Daten.
/// </summary>
/// <param name="Id">Eindeutige ID des Blocks</param>
/// <param name="Name">Name des Blocks</param>
/// <param name="Type">Block-Typ (ob, fc, fb, db, sg, dt, usw.)</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="Number">Block-Nummer (z. B. OB1, FC10, DB42)</param>
/// <param name="Networks">Liste der Netzwerke im Block</param>
/// <param name="Interface">Optional: Schnittstelle (input, output, in_out, temp, static, constant)</param>
/// <param name="Comment">Optional: Kommentar zum Block</param>
public sealed record ProgramBlockContract(
    string Id,
    string Name,
    string Type,
    string PlcId,
    int Number,
    NetworkContract[] Networks,
    BlockInterfaceContract? Interface = null,
    string? Comment = null
);

/// <summary>
/// Ein Netzwerk innerhalb eines Blocks.
/// </summary>
/// <param name="NetworkNumber">Netzwerk-Nummer</param>
/// <param name="NetworkName">Name des Netzwerks</param>
/// <param name="NetworkContent">Inhalt des Netzwerks (STL-Quellcode)</param>
public sealed record NetworkContract(
    int NetworkNumber,
    string? NetworkName = null,
    string? NetworkContent = null
);

/// <summary>
/// Schnittstelle eines Blocks (input, output, in_out, temp, static, constant).
/// </summary>
/// <param name="Input">Optionale Input-Liste</param>
/// <param name="Output">Optionale Output-Liste</param>
/// <param name="InOut">Optionale InOut-Liste</param>
/// <param name="Temp">Optionale Temp-Liste</param>
/// <param name="Static">Optionale Static-Liste</param>
/// <param name="Constant">Optionale Constant-Liste</param>
public sealed record BlockInterfaceContract(
    BlockInterfaceFieldContract[]? Input = null,
    BlockInterfaceFieldContract[]? Output = null,
    BlockInterfaceFieldContract[]? InOut = null,
    BlockInterfaceFieldContract[]? Temp = null,
    BlockInterfaceFieldContract[]? Static = null,
    BlockInterfaceFieldContract[]? Constant = null
);

/// <summary>
/// Ein Feld in der Block-Schnittstelle.
/// </summary>
/// <param name="Name">Name des Felds</param>
/// <param name="DataType">Datentyp</param>
/// <param name="InitialValue">Optionaler Anfangswert</param>
public sealed record BlockInterfaceFieldContract(
    string Name,
    string DataType,
    string? InitialValue = null
);