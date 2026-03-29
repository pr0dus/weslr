# Weslr Steuer - German Tax Law Knowledge Base

**Version:** 0.1.0  
**Last Updated:** 2026-03-29  
**License:** AGPLv3

## Overview

Weslr Steuer is a comprehensive German tax law knowledge base and compliance engine integrated into Weslr. It covers all major areas of German taxation:

- **Einkommensteuer** (Income Tax)
- **Umsatzsteuer** (VAT)
- **Körperschaftsteuer** (Corporate Tax)
- **Kapitalertragsteuer** (Capital Gains Tax)
- **Erbschaftsteuer** (Inheritance Tax)
- **Gewerbesteuer** (Business Tax)

## Features

- **Domain-specific knowledge base** with structured tax law documentation
- **Language support** (German + English)
- **Search functionality** across all tax domains
- **CLI integration** for Weslr users
- **Entity graph integration** for tax-related entities

## Structure

```
plugins/steuerwesen.py          # Core plugin module
docs/steuerwesen/               # Tax law documentation (.md files)
translations/steuerwesen/       # Language translations
steuerwesen_config.json         # Plugin configuration
```

## Usage

### Load the Plugin

```python
import importlib.util
spec = importlib.util.spec_from_file_location("steuerwesen", "plugins/steuerwesen.py")
steuerwesen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(steuerwesen)

# Initialize
steuerwesen.initialize()

# Search tax laws
results = steuerwesen.search_laws("income tax", domain="einkommensteuer")

# List domains
domains = steuerwesen.list_domains()
```

### CLI Commands

Weslr Steuer registers the following commands with `weslr_main.py`:

- `steuer-list` — List all tax domains
- `steuer-search <query>` — Search across tax law files
- `steuer-laws <domain>` — List laws in a domain
- `steuer-translation <lang> <key>` — Get translation for a key

## Tax Domains

### Einkommensteuer (Income Tax)

- Personal income tax for natural persons
- Progressive tax rates (14%-45%)
- 8 income categories (Einkommensarten)
- Annual tax return (Steuererklärung)

### Umsatzsteuer (VAT)

- Multi-stage consumption tax
- Standard rate: 19%, reduced rate: 7%
- Input tax credit system (Vorsteuerabzug)
- VAT returns (Umsatzsteuer-Voranmeldung)

### Körperschaftsteuer (Corporate Tax)

- Flat rate: 25% on taxable income
- Applies to legal entities (GmbH, AG, etc.)
- Group relief and loss carryforwards
- Dividend taxation rules

### Kapitalertragsteuer (Capital Gains Tax)

- 25% tax on capital income
- Includes interest, dividends, capital gains
- Investment fund taxation
- Tax-free allowances (Sparer-Pauschbetrag)

### Erbschaftsteuer (Inheritance Tax)

- Progressive rates (7%-50%)
- Family and business exemptions
- Tax-free allowances (Freibeträge)
- Gift tax (Schenkungsteuer) integrated

### Gewerbesteuer (Business Tax)

- Municipal trade tax
- Rates: 14-17% (business income)
- Local variance (Hebesätze)
- Loss carryforwards

## Documentation Files

### German Documentation

- `einkommensteuer.md` — Income tax laws
- `umsatzsteuer.md` — VAT laws
- `korporationssteuer.md` — Corporate tax laws
- `kapitalertragsteuer.md` — Capital gains tax
- `erbschaftsteuer.md` — Inheritance tax
- `gewerbesteuer.md` — Business tax

### English Translations (Available)

- All documentation translated to English
- Language-specific documentation in `translations/steuerwesen/`

## Configuration

### steuerwesen_config.json

```json
{
  "enabled": true,
  "languages": ["de", "en"],
  "domains": ["einkommensteuer", "umsatzsteuer", "korporationssteuer", "kapitalertragsteuer", "erbschaftsteuer", "gewerbesteuer"],
  "enabled_laws": [...],
  "last_updated": 1774928100,
  "documentation_dir": "docs/steuerwesen",
  "translations_dir": "translations/steuerwesen"
}
```

## Integration with Weslr Core

### Entity Graph Integration

Tax-related entities can be added to the Weslr entity graph:

- **Tax authorities** (Finanzämter, Bundeszentralamt für Steuern)
- **Tax laws** (EStG, UStG, KStG, etc.)
- **Taxpayers** (individuals, corporations)
- **Tax transactions** (declarations, payments)

### Search Integration

- Full-text search across all tax documentation
- Domain-specific filtering
- Keyword-based tax advice

### CLI Integration

Commands registered with Weslr CLI framework:

- Dynamic command discovery
- Automatic help text generation
- Parameter validation

## Updates and Maintenance

### Adding New Tax Laws

1. Create markdown file in `docs/steuerwesen/`
2. Add to `LAW_FILES` in `steuerwesen.py`
3. Update `DOMAINS` configuration
4. Update language translations

### Updating Tax Rates

- Review official Bundesanzeiger publications
- Update rate tables in documentation
- Update plugin configuration
- Test with sample scenarios

## Future Enhancements

- **Interactive tax calculator** (simulation engine)
- **Tax scenario analysis** (what-if queries)
- **Compliance checklist generator**
- **Tax law alerts** (new legislation monitoring)
- **Cross-border tax guidance** (international treaties)

## License

This plugin is part of the Weslr project and follows the AGPLv3 license.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Documentation:** Ensure all tax laws are properly sourced
2. **Accuracy:** Verify rates and thresholds with official sources
3. **Language:** Maintain both German and English translations
4. **Structure:** Follow existing file organization

## Support

- **GitHub Issues:** Report bugs or request features
- **Documentation:** See `docs/steuerwesen/` for detailed tax information
- **Weslr Community:** Join Discord for community support

## Acknowledgments

Weslr Steuer is based on official German tax legislation:
- **Einkommensteuergesetz (EStG)**
- **Umsatzsteuergesetz (UStG)**
- **Körperschaftsteuergesetz (KStG)**
- **Erbschaftsteuergesetz (ErbStG)**
- **Gewerbesteuergesetz (GewStG)**

---

*Built with ❤️ for the Weslr community*
