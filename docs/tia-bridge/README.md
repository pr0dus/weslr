# TIA Bridge Plugin - Weslr Integration

## Private Repository

**Location:** https://github.com/pr0dus/weslr-tia-openness-bridge  
**Status:** PRIVATE (only visible to owner and invited collaborators)

## Purpose

The TIA Bridge plugin extracts engineering data from Siemens TIA Portal V20 projects on Windows and prepares it for integration into the Weslr entity intelligence system.

## What It Does

1. **Reads** TIA Portal V20 project data (read-only, offline access)
2. **Extracts** engineering objects: PLCs, CPUs, devices, tags, alarms, topology
3. **Exports** to normalized JSON format matching Weslr entity model
4. **Does NOT**:
   - Modify the original TIA project
   - Communicate with live SPS/IO systems
   - Execute or change any control logic
   - Upload data to any external servers

## Technical Details

- **Platform:** Windows-only (TIA Portal V20 integration)
- **Access:** Windows API via Siemens Openness API
- **Output:** JSON export (normalized graph format)
- **Integration:** Weslr entity graph mapping

## Commercial Use

This plugin is part of **Weslr commercial offerings**:
- Product website: https://www.weslr.de
- Available for purchase as part of Weslr premium modules
- Integration with Siemens automation systems

## Repository Structure

```
weslr-tia-openness-bridge/
├── src/               # Windows collector implementation
├── tests/             # Unit tests and integration tests
├── schemas/           # JSON schema definitions
│   ├── tia_export.schema.json
│   └── normalized_graph.schema.json
├── examples/          # Sample data files
└── README.md          # This file
```

## Access

This repository is private. Access is granted to:
- Owner: pr0dus
- Collaborators: invited by owner

## Integration with Main Weslr Repo

The TIA bridge plugin is **not embedded** in the main Weslr repository (`github.com/pr0dus/weslr`). It exists as a separate private repository and is integrated via:

1. **Plugin system** (runtime loading)
2. **External references** (configuration files)
3. **Documentation links** (www.weslr.de)

## License

This plugin is proprietary software, part of the Weslr commercial product suite.

---

**Note:** For commercial inquiries, visit https://www.weslr.de
