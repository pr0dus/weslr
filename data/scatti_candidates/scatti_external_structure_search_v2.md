# SCATTI External Structure Search v2

**Date:** 2026-05-08  
**Target Formula:** CaSc2TiO6  
**Search Type:** Bounded external structure/source search  
**Time Limit:** 5 minutes  
**Search Limit:** 5 useful results per query family

## Sources Checked

| Source | Status | Notes |
|--------|--------|-------|
| Materials Project (web) | checked_no_hit / requires_api_key | Web search only (403 on direct access) |
| Materials Project (SearxNG) | checked_hit | Found CaTiO3 entries, no CaSc2TiO6 |
| COD (web_fetch) | accessible | Open-access crystallography database |
| COD (SearxNG) | checked_no_hit | No exact matches for CaSc2TiO6 or Ca2ScTiO6 |
| AFLOW | checked_no_hit | Previous checks showed no exact matches |
| NOMAD | checked_no_hit | Previous checks showed no exact matches |
| OQMD | timeout | HTTP 502 Bad Gateway |
| SearxNG local | accessible | Available at http://127.0.0.1:8888 |

## Exact CaSc2TiO6 Result

| Query | Source | Result | Classification |
|-------|--------|--------|----------------|
| CaSc2TiO6 site:materialsproject.org | SearxNG | 0 hits | no_hit |
| CaSc2TiO6 site:www.crystallography.net | SearxNG | 0 hits | no_hit |
| "CaSc2TiO6 crystal structure" | SearxNG | 0 hits | no_hit |
| "calcium scandium titanium oxide" | SearxNG | 0 hits | no_hit |
| "calcium scandium titanate" | SearxNG | 0 hits | no_hit |

**Conclusion:** No exact CaSc2TiO6 evidence was found in this bounded accessible-source search.  
**Status:** Unresolved. Ca2ScTiO6 was previously identified as a related parent pointer via SearxNG/OQMD evidence in Phase 1P, but no public CIF was found in this search.

## Related Parent Results

| Formula/Topic | Source | Evidence Type | CIF? | Usefulness | Notes |
|---------------|--------|---------------|------|------------|-------|
| Sc2TiO5 | SearxNG | research paper | No | High | Pseudobrookite-type structure, potential parent |
| CaSc2O4 | SearxNG | research paper | No | High | Calcium ferrite structure (Pnma), useful reference |
| Sc2Ti2O7 | SearxNG | research paper | No | Medium | Similar oxide framework, limited relevance |
| CaTiO3 (Sc-doped) | SearxNG | research paper | No | High | Sc-doped CaTiO3 published, potential template |
| Ca2ScTiO6 | previously_found | related_parent | No | high | Previously identified via SearxNG/OQMD in Phase 1P, no CIF in this search |
| CaO-Sc2O3-TiO2 phase diagram | SearxNG | research paper | No | Medium | Phase diagram references exist |

### Useful Related Structures

1. **Sc2TiO5** (pseudobrookite-type)
   - Reference: "Sc2TiO5, an entropy-stabilized pseudobrookite-type compound"
   - Space group: likely orthorhombic
   - Usefulness: High — potential parent for CaSc2TiO6 construction
   - Note: No CIF download found, but structure description available

2. **CaSc2O4** (calcium ferrite structure)
   - Space group: Pnma (No. 62)
   - Usefulness: High — provides Ca-O framework reference
   - Note: Low phonon energy (~540 cm⁻¹) mentioned

3. **CaTiO3 with Sc-doping** (perovskite)
   - Reference: "Crystal Structures and Conduction Paths of Sc-Doped CaTiO3"
   - Space group: orthorhombic
   - Usefulness: High — direct template for CaSc2TiO6 construction
   - Note: No CIF download found

## CIFs Found / Downloaded

**None.**

None of the sources provided direct CIF downloads. All results were:
- Research paper abstracts
- Database entry metadata only
- No public CIF links

## Recommendations

**For CIF Access, Priority Order:**

1. **Get Materials Project API key** — enables programmatic CIF downloads
2. **Contact authors** — request CIFs from research papers
3. **Check supplementary info** — some papers provide CIFs as supplements

**For CaSc2TiO6 Construction:**

If CIFs are unavailable, use parent structures as templates:

1. **CaSc2O4** (Pnma) — Ca-O framework
2. **Sc2TiO5** (pseudobrookite) — Sc-Ti-O framework
3. **CaTiO3** (Pnma) — perovskite template

## Required Interpretation

### Exact CaSc2TiO6 Evidence Found in Bounded Search?
**No.** No exact CaSc2TiO6 evidence found in bounded search; status remains unresolved.

### Exact CaSc2TiO6 CIF Found?
**No.** No CIF downloads available.

### Ca2ScTiO6 Status?
**Related parent pointer previously found via SearxNG/OQMD (Phase 1P), no CIF found in this search.**

### Best Related Parent Structure Found?
**Sc2TiO5** (pseudobrookite-type) and **CaSc2O4** (calcium ferrite, Pnma).

### Whether Any Parent CIF Is Available?
**No.** No public CIF downloads found.

### Whether Current Evidence Justifies Another Structure Construction Attempt?
**Yes, with caution.** Parent structures identified but CIF unavailable. Next attempt should:
- Use CaSc2O4 as Ca-O framework reference
- Use Sc2TiO5 as Sc-Ti-O framework reference
- Build new manual candidate with better coordination geometry

### Whether Materials Project Still Requires API Key?
**Yes.** No API key configured for programmatic access.

### Whether OQMD Status Inconclusive?
**Yes.** HTTP 502 timeout during this search; previous SearxNG/OQMD evidence found Ca2ScTiO6 as related parent.

## Claim Boundary

No exact CaSc2TiO6 evidence found in bounded search; status remains unresolved.  
No hit in this bounded search is not proof of absence or novelty.  
Materials Project API key required for programmatic CIF downloads.  
CIF availability for related materials does not make them exact scatti structures.

## Next Recommended Step

**Option A:** Use parent structure templates (CaSc2O4 + Sc2TiO5) to build new exact CaSc2TiO6 candidate with better geometry

**Option B:** Get Materials Project API key to enable CIF downloads

**Option C:** Try OQMD later (HTTP 502 may be transient)

## Git Status

No changes. Search only.
