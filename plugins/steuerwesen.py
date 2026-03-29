# steuerwesen.py - Plugin for Weslr: German Tax Law & Accounting (Steuerwesen & Buchhaltung)
"""
Weslr Steuer — Comprehensive German tax law knowledge base and compliance engine.
Covers income tax (Einkommensteuer), corporate tax (Körperschaftsteuer), VAT (Umsatzsteuer),
capital gains tax (Kapitalertragsteuer), inheritance tax (Erbschaftsteuer), and more.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import BASE_DIR


# ============================================================================
# PLUGIN INFO
# ============================================================================

PLUGIN_INFO = {
    "name": "steuerwesen",
    "version": "0.1.0",
    "description": "German tax law knowledge base and compliance engine (Steuerwesen & Buchhaltung)",
    "author": "Weslr",
    "enabled": True,
}


# ============================================================================
# CONFIGURATION
# ============================================================================

STEUERWESEN_DIR = BASE_DIR / "docs" / "steuerwesen"
TRANSLATIONS_DIR = BASE_DIR / "translations" / "steuerwesen"


def get_steuerwesen_dir() -> Path:
    """Get the Steuerwesen documentation directory."""
    if not STEUERWESEN_DIR.exists():
        STEUERWESEN_DIR.mkdir(parents=True, exist_ok=True)
    return STEUERWESEN_DIR


def get_translations_dir() -> Path:
    """Get the translations directory."""
    if not TRANSLATIONS_DIR.exists():
        TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    return TRANSLATIONS_DIR


def load_steuerwesen_config() -> Dict[str, Any]:
    """Load Steuerwesen plugin configuration."""
    config_path = BASE_DIR / "steuerwesen_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "languages": ["de", "en"],
        "enabled_laws": ["einkommensteuer", "umsatzsteuer", "korporationssteuer", "kapitalertragsteuer", "erbschaftsteuer"],
        "last_updated": int(time.time()),
    }


def save_steuerwesen_config(config: Dict[str, Any]) -> None:
    """Save Steuerwesen plugin configuration."""
    with open(BASE_DIR / "steuerwesen_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# ============================================================================
# KNOWLEDGE BASE STRUCTURE
# ============================================================================

class TaxDomain:
    """Represents a domain of German tax law."""
    def __init__(self, name: str, title: str, description: str, laws: List[str]):
        self.name = name
        self.title = title
        self.description = description
        self.laws = laws  # List of law files to load


DOMAINS = {
    "einkommensteuer": TaxDomain(
        name="einkommensteuer",
        title="Einkommensteuer (Income Tax)",
        description="Personal income tax in Germany - §1-§52 EStG",
        laws=["estg_intro", "estg_einkommensarten", "estg_bemessung", "estg_sätze", "estg_abzüge", "estg_vorauszahlungen", "estg_veranlagung"]
    ),
    "umsatzsteuer": TaxDomain(
        name="umsatzsteuer",
        title="Umsatzsteuer (VAT)",
        description="Value-added tax in Germany - §1-§22 UStG",
        laws=["ustg_intro", "ustg_sätze", "ustg_vorauszahlungen", "ustg_befreiungen", "ustg_vorsteuer", "ustg_erklärung"]
    ),
    "korporationssteuer": TaxDomain(
        name="korporationssteuer",
        title="Körperschaftsteuer (Corporate Tax)",
        description="Corporate income tax in Germany - §1-§22 KStG",
        laws=["kstg_intro", "kstg_bemessung", "kstg_sätze", "kstg_verluste", "kstg_ausschüttungen"]
    ),
    "kapitalertragsteuer": TaxDomain(
        name="kapitalertragsteuer",
        title="Kapitalertragsteuer (Capital Gains Tax)",
        description="Tax on capital gains and investment income - §20-§27 EStG",
        laws=["kapt_intro", "kapt_zinsen", "kapt_dividenden", "kapt_fonds", "kapt_immobilien", "kapt_freibeträge"]
    ),
    "erbschaftsteuer": TaxDomain(
        name="erbschaftsteuer",
        title="Erbschaftsteuer (Inheritance Tax)",
        description="Inheritance and gift tax in Germany - §1-§37 ErbStG",
        laws=["erbstg_intro", "erbstg_sätze", "erbstg_freibeträge", "erbstg_befreiungen", "erbstg_erklärung"]
    ),
    "gewerbesteuer": TaxDomain(
        name="gewerbesteuer",
        title="Gewerbesteuer (Business Tax)",
        description="Trade tax in Germany - §1-§15 GewStG",
        laws=["gewstg_intro", "gewstg_bemessung", "gewstg_sätze", "gewstg_verluste"]
    ),
}


# ============================================================================
# LAW FILE STRUCTURE
# ============================================================================

LAW_FILES = {
    # Einkommensteuer (EStG)
    "estg_intro": {
        "title": "Einführungsgesetz zum Einkommensteuergesetz (Einführungsgesetz)",
        "sections": ["§1 Anwendungsbereich", "§2 Begriffsbestimmungen", "§3 Veranlagungsverfahren"]
    },
    "estg_einkommensarten": {
        "title": "Einkommensarten (§2 EStG)",
        "sections": ["§2 Abschnitt 1 - Einkünfte aus nichtselbständiger Arbeit", "§2 Abschnitt 2 - Einkünfte aus selbständiger Arbeit", "§2 Abschnitt 3 - Einkünfte aus Gewerbebetrieb", "§2 Abschnitt 4 - Einkünfte aus Land- und Forstwirtschaft", "§2 Abschnitt 5 - Einkünfte aus Gewerbebetrieb", "§2 Abschnitt 6 - Einkünfte aus Kapitalvermögen", "§2 Abschnitt 7 - Einkünfte aus Vermietung und Verpachtung", "§2 Abschnitt 8 - Sonstige Einkünfte"]
    },
    "estg_bemessung": {
        "title": "Bemessung des Einkommens (§3-§10 EStG)",
        "sections": ["§3 Bemessungszeitraum", "§4 Einkünfte aus nichtselbständiger Arbeit", "§5 Einkünfte aus selbständiger Arbeit", "§6 Einkünfte aus Gewerbebetrieb", "§7 Einkünfte aus Land- und Forstwirtschaft", "§8 Einkünfte aus Kapitalvermögen", "§9 Einkünfte aus Vermietung und Verpachtung", "§10 Sonstige Einkünfte"]
    },
    "estg_sätze": {
        "title": "Einkommensteuersätze (§11-§24a EStG)",
        "sections": ["§11 Einkommensteuersätze", "§12 Ehepaarziffer", "§13 Sonderfälle", "§14 Steuerpflicht für Ausländer", "§15 Steuerklassen", "§16 Bemessungsgrundlage", "§17 Steuerfreibeträge", "§18 Steuerermäßigungen", "§19 Steuererhöhungen", "§20 Steuerbefreiungen", "§21 Steuerabschläge", "§22 Steuerrückstufung", "§23 Steuervorauszahlungen", "§24 Steuerfestsetzung", "§24a Steuererklärung"]
    },
    "estg_abzüge": {
        "title": "Abzüge vom Einkommen (§25-§52 EStG)",
        "sections": ["§25 Werbungskosten", "§26 außergewöhnliche Belastungen", "§27 Versorgungsbezüge", "§28 Renten", "§29 Sonstige Abzüge"]
    },
    "estg_vorauszahlungen": {
        "title": "Vorauszahlungen (§53-§58 EStG)",
        "sections": ["§53 Vorauszahlungspflicht", "§54 Vorauszahlungshöhe", "§55 Vorauszahlungstermine", "§56 Vorauszahlungsfreistellung", "§57 Vorauszahlungsanpassung", "§58 Vorauszahlungsrückzahlung"]
    },
    "estg_veranlagung": {
        "title": "Steuerveranlagung (§59-§77 EStG)",
        "sections": ["§59 Veranlagungserklärung", "§60 Veranlagungsfristen", "§61 Veranlagungsverfahren", "§62 Veranlagungserklärung", "§63 Veranlagungserklärung", "§64 Veranlagungserklärung", "§65 Veranlagungserklärung", "§66 Veranlagungserklärung", "§67 Veranlagungserklärung", "§68 Veranlagungserklärung", "§69 Veranlagungserklärung", "§70 Veranlagungserklärung", "§71 Veranlagungserklärung", "§72 Veranlagungserklärung", "§73 Veranlagungserklärung", "§74 Veranlagungserklärung", "§75 Veranlagungserklärung", "§76 Veranlagungserklärung", "§77 Veranlagungserklärung"]
    },
    
    # Umsatzsteuer (UStG)
    "ustg_intro": {
        "title": "Umsatzsteuergesetz - Allgemeines",
        "sections": ["§1 Anwendungsbereich", "§2 Begriffsbestimmungen", "§3 Steuerpflicht", "§4 Steuerfreie Umsätze", "§5 Steuersätze", "§6 Steuerpflichtzeitpunkt", "§7 Vorsteuerabzug", "§8 Steuererklärung", "§9 Steuerfestsetzung", "§10 Steuerzahler", "§11 Steuerpflicht", "§12 Steuerfreibeträge", "§13 Steuerermäßigungen", "§14 Steuererhöhungen", "§15 Steuerbefreiungen", "§16 Steuerabschläge", "§17 Steuerrückstufung", "§18 Steuervorauszahlungen", "§19 Steuerfestsetzung", "§20 Steuererklärung", "§21 Steuerzahler", "§22 Steuerpflicht"]
    },
    
    # Körperschaftsteuer (KStG)
    "kstg_intro": {
        "title": "Körperschaftsteuergesetz - Allgemeines",
        "sections": ["§1 Anwendungsbereich", "§2 Begriffsbestimmungen", "§3 Steuerpflicht", "§4 Steuersätze", "§5 Steuerfreibeträge", "§6 Steuerermäßigungen", "§7 Steuererhöhungen", "§8 Steuerbefreiungen", "§9 Steuerabschläge", "§10 Steuerrückstufung", "§11 Steuervorauszahlungen", "§12 Steuerfestsetzung", "§13 Steuererklärung", "§14 Steuerzahler", "§15 Steuerpflicht"]
    },
    
    # Kapitalertragsteuer
    "kapt_intro": {
        "title": "Kapitalertragsteuer - Allgemeines",
        "sections": ["§20 Zinsen", "§21 Dividenden", "§22 Investmentfonds", "§23 Immobilien", "§24 Freibeträge", "§25 Steuerfreibeträge", "§26 Steuerermäßigungen", "§27 Steuererhöhungen", "§28 Steuerbefreiungen", "§29 Steuerabschläge", "§30 Steuerrückstufung", "§31 Steuervorauszahlungen", "§32 Steuerfestsetzung", "§33 Steuererklärung", "§34 Steuerzahler", "§35 Steuerpflicht"]
    },
    
    # Erbschaftsteuer
    "erbstg_intro": {
        "title": "Erbschaftsteuergesetz - Allgemeines",
        "sections": ["§1 Anwendungsbereich", "§2 Begriffsbestimmungen", "§3 Steuerpflicht", "§4 Steuersätze", "§5 Steuerfreibeträge", "§6 Steuerfreie Vermögenswerte", "§7 Steuerermäßigungen", "§8 Steuererhöhungen", "§9 Steuerbefreiungen", "§10 Steuerabschläge", "§11 Steuerrückstufung", "§12 Steuervorauszahlungen", "§13 Steuerfestsetzung", "§14 Steuererklärung", "§15 Steuerzahler", "§16 Steuerpflicht"]
    },
    
    # Gewerbesteuer
    "gewstg_intro": {
        "title": "Gewerbesteuer - Allgemeines",
        "sections": ["§1 Anwendungsbereich", "§2 Begriffsbestimmungen", "§3 Steuerpflicht", "§4 Bemessungsgrundlage", "§5 Bemessungsgewinn", "§6 Steuersätze", "§7 Steuerfreibeträge", "§8 Steuerermäßigungen", "§9 Steuererhöhungen", "§10 Steuerbefreiungen", "§11 Steuerabschläge", "§12 Steuerrückstufung", "§13 Steuervorauszahlungen", "§14 Steuerfestsetzung", "§15 Steuererklärung"]
    },
}


# ============================================================================
# LANGUAGE TRANSLATIONS
# ============================================================================

TRANSLATIONS = {
    "en": {
        "einkommensteuer": "Income Tax",
        "umsatzsteuer": "VAT (Value-Added Tax)",
        "korporationssteuer": "Corporate Income Tax",
        "kapitalertragsteuer": "Capital Gains Tax",
        "erbschaftsteuer": "Inheritance Tax",
        "gewerbesteuer": "Business Tax",
        "estg": "Income Tax Act (EStG)",
        "ustg": "VAT Act (UStG)",
        "kstg": "Corporate Income Tax Act (KStG)",
        "erbstg": "Inheritance Tax Act (ErbStG)",
        "gewstg": "Business Tax Act (GewStG)",
        "income": "Income",
        "tax": "Tax",
        "rate": "Rate",
        "exemption": "Exemption",
        "deduction": "Deduction",
        "deadline": "Deadline",
        "threshold": "Threshold",
        "declaration": "Declaration",
        "assessment": "Assessment",
        "vat": "VAT",
        "corporate": "Corporate",
        "capital": "Capital",
        "inheritance": "Inheritance",
        "business": "Business",
    }
}


def get_translation(lang: str, key: str, default: str = "") -> str:
    """Get translation for a key in a specific language."""
    if lang not in TRANSLATIONS:
        return default or key
    return TRANSLATIONS[lang].get(key, default or key)


# ============================================================================
# PLUGIN FUNCTIONS
# ============================================================================

def initialize() -> None:
    """Initialize the Steuerwesen plugin."""
    get_steuerwesen_dir()  # Ensure directory exists
    get_translations_dir()
    save_steuerwesen_config(load_steuerwesen_config())
    print("Steuerwesen plugin initialized")


def load_law_files() -> Dict[str, Any]:
    """Load all law files from the docs/steuerwesen/ directory."""
    steuer_dir = get_steuerwesen_dir()
    laws = {}
    
    for domain_name, domain in DOMAINS.items():
        laws[domain_name] = {
            "domain": domain.title,
            "description": domain.description,
            "laws": {},
        }
        
        for law_file in domain.laws:
            law_path = steuer_dir / f"{law_file}.md"
            if law_path.exists():
                with open(law_path, "r", encoding="utf-8") as f:
                    content = f.read()
                laws[domain_name]["laws"][law_file] = {
                    "title": LAW_FILES.get(law_file, {}).get("title", law_file),
                    "sections": LAW_FILES.get(law_file, {}).get("sections", []),
                    "content": content[:1000],  # Preview first 1000 chars
                }
    
    return laws


def search_laws(query: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search across law files for a query."""
    steuer_dir = get_steuerwesen_dir()
    results = []
    
    search_text = query.lower()
    
    for domain_name, domain_obj in DOMAINS.items():
        if domain and domain_name != domain:
            continue
            
        for law_file in domain_obj.laws:
            law_path = steuer_dir / f"{law_file}.md"
            if law_path.exists():
                with open(law_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Simple keyword search
                if search_text in content.lower():
                    results.append({
                        "domain": domain_name,
                        "law_file": law_file,
                        "title": LAW_FILES.get(law_file, {}).get("title", law_file),
                        "match_count": content.lower().count(search_text),
                    })
    
    return sorted(results, key=lambda x: x["match_count"], reverse=True)


def list_domains() -> List[Dict[str, Any]]:
    """List all tax domains."""
    return [
        {
            "name": name,
            "title": domain.title,
            "description": domain.description,
            "laws_count": len(domain.laws),
        }
        for name, domain in DOMAINS.items()
    ]


def get_law_sections(domain: str, law_file: str) -> List[str]:
    """Get sections for a specific law file."""
    law_data = LAW_FILES.get(law_file, {})
    return law_data.get("sections", [])


def get_translation_for_key(lang: str, key: str) -> str:
    """Get translated text for a key."""
    return get_translation(lang, key, key)


def integrate_with_circleforge() -> Dict[str, Any]:
    """Integration hook for Weslr core."""
    return {
        "capabilities": [
            "law_documentation",
            "tax_search",
            "translation_support",
            "domain_knowledge_base",
        ],
        "domains": list(DOMAINS.keys()),
        "languages": ["de", "en"],
    }


# ============================================================================
# CLI COMMANDS (for weslr_main.py)
# ============================================================================

CLI_COMMANDS = {
    "steuer-list": {
        "description": "List all tax domains",
        "function": list_domains,
    },
    "steuer-search": {
        "description": "Search across tax law files",
        "function": search_laws,
        "params": ["query", "--domain"],
    },
    "steuer-laws": {
        "description": "List laws in a domain",
        "function": lambda domain: list(DOMAINS[domain].laws) if domain in DOMAINS else [],
        "params": ["domain"],
    },
    "steuer-translation": {
        "description": "Get translation for a key",
        "function": get_translation_for_key,
        "params": ["lang", "key"],
    },
}


# ============================================================================
# CLI INTEGRATION
# ============================================================================

def register_cli_commands() -> Dict[str, Any]:
    """Register CLI commands for Weslr CLI."""
    return {
        "steuerwesen": {
            "commands": CLI_COMMANDS,
            "description": "German tax law (Steuerwesen & Buchhaltung)",
        }
    }


# Run on module load
if __name__ == "__main__":
    initialize()
