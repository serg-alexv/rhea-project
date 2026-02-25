# H32-02 Ksu Genome: Heme Biosynthesis & Respiratory Gene Extraction

**Extraction Date:** 2026-02-25
**Source Files:**
- `pgap_genes_all.json` (2090 total genes)
- `categorized_sorted.json`

## Summary Statistics

| Category | Count |
|----------|-------|
| NAD-related | 106 |
| FAD-oxidoreductase | 23 |
| Iron/ferr | 3 |
| Heme/Porphyrin | 2 |
| Cytochrome | 2 |
| Quinone | 1 |
| Heme biosynthesis | 1 |
| **TOTAL** | **114** |

## Key Findings

### Critical Heme Biosynthesis Genes (1)
- **ACWYRP_RS05595** - `ferrochelatase` (315 aa)
  - Contig: NZ_JBSROM010000016.1 | Position: 9916-10863 (minus strand)
  - Final step of heme synthesis: insertion of iron into protoporphyrin IX

### Heme/Porphyrin Pathway Genes (2)
- **ACWYRP_RS04330** - `uroporphyrinogen decarboxylase family protein` (343 aa)
- **ACWYRP_RS04335** - `uroporphyrinogen decarboxylase family protein` (333 aa)
  - Both on contig NZ_JBSROM010000010.1, in tandem
  - Catalyze porphyrin ring modifications

### Respiratory Chain Cytochrome Genes (2)
- **ACWYRP_RS05060** - `cytochrome d ubiquinol oxidase subunit II` (337 aa)
- **ACWYRP_RS05065** - `cytochrome ubiquinol oxidase subunit I` (492 aa)
  - Contig: NZ_JBSROM010000013.1 | Positions: 30731-33219 (minus strand)
  - Form terminal oxidase complex for anaerobic/microaerophilic respiration

### Iron Transport Genes (2)
- **ACWYRP_RS03305** - `ferrous iron transport protein B` (704 aa)
- **ACWYRP_RS03310** - `ferrous iron transport protein A` (157 aa)
  - Contig: NZ_JBSROM010000007.1 | Positions: 26910-29501 (minus strand)

### Quinone Metabolism (1)
- **ACWYRP_RS04865** - `bifunctional demethylmenaquinone methyltransferase / 2-methoxy-6-polyprenyl-1,4-benzoquinol methylase UbiE` (236 aa)
  - Contig: NZ_JBSROM010000012.1
  - Required for ubiquinone/menaquinone synthesis

### FAD-Dependent Oxidoreductases (23)
High abundance of FAD-binding oxidoreductases suggests robust aerobic and anaerobic electron transport capabilities. Examples include:
- ACWYRP_RS02880, RS04245, RS05970, RS05990, RS08220, RS08265, RS08815, RS09590, RS09640, RS10055
- Includes NADH-dependent flavin oxidoreductases (multiple)

### NAD-Dependent Enzymes (106)
Extensive complement of NAD(P)-dependent dehydrogenases and reductases across central metabolism, including:
- **Dehydrogenases:** dihydrolipoyl, homoserine, IMP, glucose-6-phosphate, lactate/malate, phosphoglycerate
- **Reductases:** dihydrofolate, aldo/keto, acyl-CoA, ribonucleoside-diphosphate, pyrroline-5-carboxylate
- **Specialized:** NAD-dependent DNA ligase (LigA), NAD kinase

## Annotation Confidence Notes

1. **Ferrochelatase (ACWYRP_RS05595)** - Single copy, well-characterized enzyme (315 aa)
   - May have been missed if sequence divergence from reference databases
   - High priority for validation against known bacterial ferrochelatases

2. **Uroporphyrinogen Decarboxylase Duplicates** - Tandem duplication (RS04330/RS04335)
   - Unusual to have two copies; may represent functional redundancy or subfunctionalization
   - Recommend sequence comparison to identify functional divergence

3. **Cytochrome d Oxidase (RS05060/RS05065)** - Tandem genes suggest coordinated expression
   - Complete subunit I (492 aa) and II (337 aa) present
   - Characteristic of anaerobic/microaerophilic metabolism (fits K. subterranei niche)

## Output Files

- `h32_02_heme_respiratory_genes.json` - Complete JSON records with all gene attributes
- `h32_02_heme_respiratory_genes.csv` - Spreadsheet format for analysis in Excel/R
- `EXTRACTION_SUMMARY.md` - This file

## Search Patterns Used

```
FAD, oxidoreductase, NAD, dehydrogenase, reductase
heme, haem, porphyrin, coproporphyrinogen, protoporphyrin, uroporphyrinogen
ALA synthase, aminolevulin, ferrochelatase
cytochrome, quinone, menaquinone, ubiquinone
iron, ferr (excluding transferase)
glutamyl-tRNA (alternative heme synthesis pathway)
```

---
**Total Genes Screened:** 2,090
**Total Matches:** 114 (5.5%)
**Extraction Method:** Pattern-based regex search across protein_name, product, and description fields
