using SiemensToWeslr.TiaCollector.Contracts;

namespace SiemensToWeslr.TiaCollector.Mapping;

/// <summary>
/// Mapping für Tag-Informationen in TagContract.
/// 
/// Wandelt eine kleine interne Rohdatenstruktur in TagContract um.
/// Keine Openness-Abhängigkeiten, keine Geschäftslogik.
/// </summary>
public static class TagContractMapper
{
    /// <summary>
    /// Mapping-Methode für TagContract.
    /// </summary>
    /// <param name="tagData">Die Rohdaten für das Tag.</param>
    /// <returns>TagContract mit befüllten Feldern.</returns>
    public static TagContract Map(TagData tagData)
    {
        return new TagContract(
            Id: tagData.Id,
            Name: tagData.Name,
            DataType: tagData.DataType,
            Address: tagData.Address,
            PlcId: tagData.PlcId,
            Comment: tagData.Comment,
            InitialValue: tagData.InitialValue,
            ReadWrite: tagData.ReadWrite,
            DirectAccess: tagData.DirectAccess
        );
    }
}

/// <summary>
/// Kleines Rohdatenmodell für Tag-Informationen (innerhalb des Mappers).
/// </summary>
/// <param name="Id">Eindeutige ID des Tags</param>
/// <param name="Name">Vollqualifizierter Tag-Name (z. B. "DB42.TemperaturePV")</param>
/// <param name="DataType">Datentyp (BOOL, BYTE, WORD, DWORD, INT, DINT, REAL, STRING, DATE, TIME, etc.)</param>
/// <param name="Address">Speicheradresse (z. B. "DB42.DBW0", "I0.0", "Q4.3")</param>
/// <param name="PlcId">Referenz zur zugehörigen PLC-ID</param>
/// <param name="Comment">Optional: Kommentar zum Tag</param>
/// <param name="InitialValue">Optional: Anfangswert</param>
/// <param name="ReadWrite">Optional: Schreibzugriff erlaubt</param>
/// <param name="DirectAccess">Optional: Direktzugriff</param>
internal sealed record TagData(
    string Id,
    string Name,
    string DataType,
    string Address,
    string PlcId,
    string? Comment = null,
    string? InitialValue = null,
    bool? ReadWrite = null,
    bool? DirectAccess = null
);