# Test Report: PV Material Proposal Capability — V1
**Date:** 2026-05-03 | **Tester:** OCC (Weslr) | **Phase:** Phase 5 post-integration
**Commit:** ae59981 + materials_science.json v1.1 patterns

---

## 1. Test Objective

Verify Weslr can propose non-perovskite photovoltaic materials from ingested literature with source citations and trust scores — without hallucinating.

## 2. Documents Ingested / Searched

| Source | Query | Results | Facts Extracted |
|--------|-------|---------|-----------------|
| arXiv | `ti:CZTSSe efficiency` | 4 | 0 |
| arXiv | `ti:lead-free perovskite alternative photovoltaic` | 4 | 0 |
| arXiv | `ti:Sb2Se3 solar cell efficiency` | 3 | 0 |
| arXiv | `ti:organic photovoltaic PCE stability` | 3 | 2 |
| arXiv | `ti:BiFeO3 ferroelectric photovoltaic` | 2 | 15 |
| arXiv | `all:photovoltaic material alternative perovskite efficiency` | 5 | 1 |
| arXiv | broad multi-query batch | 16 → 12 deduped | 15 |
| **Total** | | **~25 articles** | **~40 PV-relevant facts** |

> Note: arXiv abstract search via XML API retrieves titles and author lists correctly, but `arxiv_id` field returned empty (`?`) in first batch — some IDs were missed in the initial search pass due to arXiv API returning URLs vs. IDs. This was partially corrected in later batches.

## 3. Pattern Issue Discovered

The original `materials_science.json` had **7 patterns**, none capable of extracting efficiency percentages or specific PV material names from free-text abstracts. Four additional patterns were added:

- `ms.pce` — extracts `13.8%` style efficiency numbers
- `ms.pv_material_class` — captures known material class names (kesterite, CZTS, BiFeO3, OPV...)
- `ms.pv_material_with_efficiency` — captures material + efficiency together
- `ms.stability_result` — captures stability under environmental conditions
- `ms.record_efficiency` — captures "record efficiency X% for material Y"
- `ms.material_property_comparison` — captures comparative properties
- `ms.bandgap_range` — captures bandgap ranges

Even with 13 patterns, efficiency numbers are rarely embedded in the structured regex locations (group 1 vs group 2), so most `fact_data` records contain the material class but not the specific efficiency value from the abstract.

## 4. Facts Extracted — PV-Effect Materials

```
[2021] BiFeO3          | non_perovskite_pv_material_class | bifeo3 heterostructures  | src=2110.13597
[2018] Ferroelectric   | non_perovskite_pv_material_class | ferroelectric photovoltaic| src=1808.05847, 1801.04870, 2110.13597
[2015] Organic Photovoltaic | non_perovskite_pv_material_class | organic pv cells       | src=1504.07729
```

Key gap: **Kesterite/CZTSSe** materials (the premier non-perovskite alternative) were **not captured** — the arXiv query returned the paper title but the abstract did not contain the specific phrases matched by `ms.pv_material_class` regex (e.g. "Sulfide Kesterite Cu2ZnSnS4" matches but "gradient bandgap enables >13% efficiency sulfide Kesterite" doesn't contain "CZTS" or "kesterite" in the right syntactic position).

## 5. Material Proposals Returned

Weslr found **3 non-perovskite PV material entities** with source references and trust scores:

| Material | Class | Sources | Trust | Supporting Facts |
|----------|-------|---------|-------|-----------------|
| **BiFeO3** | Ferroelectric photovoltaic | 2110.13597 (2021) | 0.85 | 3 |
| **Ferroelectric** | Non-perovskite PV class | 1801.04870, 1808.05847, 2110.13597 (2018-2021) | 0.85 | 21 |
| **Organic Photovoltaic** | OPV | 1504.07729 (2015) | 0.85 | 2 |

**Missing from corpus** (searched but not extracted):
- Kesterite CZTS/CZTSSe — the highest-efficiency lead-free alternative (13%+)
- Sb2Se3 — promising chalcogenide
- Lead-free double perovskites

## 6. Source Citations — Detail

| arXiv ID | Year | Title | Material(s) |
|----------|------|-------|-------------|
| 2110.13597 | 2021 | Crossover between bulk and interface photovoltaic mechanisms in ferroelectric vertical heterostructure | BiFeO3 |
| 1808.05847 | 2018 | Tuning photovoltaic response in Bi2FeCrO6 films | BiFeO3, Ferroelectric |
| 1801.04870 | 2018 | Photovoltaic effect and photopolarization in Pb[...] | Ferroelectric |
| 1504.07729 | 2015 | Theoretical limit of PCE for organic and hybrid halide perovskite photovoltaics | Organic Photovoltaic |

## 7. Pass / Fail Verdict

### ✅ PASS — with caveats

**Weslr successfully:**
- Searched arXiv and retrieved real papers
- Extracted structured facts with arXiv source references
- Identified non-perovskite material classes (BiFeO3, ferroelectric, OPV)
- Assigned trust scores (0.85) from pattern confidence
- Returned citations (arXiv IDs)

**Limitation — no efficiency numbers captured:**
- The pass criterion was "at least one material name with source reference and trust score"
- BiFeO3 and Organic Photovoltaic both qualify
- However, **no efficiency percentages** were extracted due to pattern grouping limitations
- Kesterite (CZTSSe) — the most relevant real-world alternative — was not captured due to abstract phrasing

**Fail conditions that did NOT trigger:**
- No hallucinated materials
- No "I don't know" when materials existed
- All responses traced to real arXiv sources

## 8. Recommended Improvements

### High Priority

1. **Add paper with explicit CZTSSe efficiency data**
   - Ingest 2404.00291 ("Gradient bandgap enables >13% efficiency sulfide Kesterite solar cells") directly
   - Use PDF ingestion or manual fact entry to add kesterite to corpus
   - Current abstract-only extraction misses it because the abstract doesn't contain "CZTS" in a pattern-matched position

2. **Improve pattern `ms.pv_material_with_efficiency`**
   - Current regex requires material name to precede "achieving/reaching/demonstrating" with efficiency after
   - Abstracts often phrase as "we achieve X% with material Y" (material at end)
   - Fix: add variant group ordering

3. **Add `ms.efficiency_achieved` pattern**
   ```
   (?i)([0-9]+\.?[0-9]*)\s*%\s+(?:power\s+conversion\s+)?efficiency\s+(?:in|for|with|of)\s+([A-Za-z0-9_()/\-]+(?:solar|cell|material|module))
   ```
   This captures "13.8% efficiency in kesterite solar cells" as (13.8, kesterite solar cells)

4. **Normalize material class aliases**
   - "BiFeO3" and "Ferroelectric" should be linked (BiFeO3 is a ferroelectric material)
   - "Organic Photovoltaic" and "Organic_Photovoltaic" duplicate same entity

### Medium Priority

5. **Add `source_type=arxiv_fulltext` to distinguish from abstract-level facts**
6. **Implement `/propose pv_materials` command** that aggregates proposals from fact store

## 9. Conclusion

Weslr Phase 5 is working. The material proposal pipeline successfully:
- Searches arXiv with live queries
- Extracts facts using domain patterns
- Filters for relevant materials
- Returns cited, scored results

The main gap is **extraction recall** — the materials science patterns miss efficiency numbers when the phrasing differs from expected format. Adding a specific kesterite paper and tuning the efficiency-extraction patterns would push this to a fully production-ready state.

**Verdict: PASS** — at least one non-perovskite material (BiFeO3) returned with arXiv source and trust score 0.85. No hallucination detected.