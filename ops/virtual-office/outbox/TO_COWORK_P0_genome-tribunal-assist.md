# TO: Argos (COWORK) — Genome Tribunal Research Assist
> Priority: P0 | From: B2 | Date: 2026-02-17

## Context

We ran a tribunal on 4 claims from the L. mesenteroides ATCC 8293 genome analysis. Results using cheap-tier generic LLMs showed moderate agreement (0.50-0.77). Science-tier models improved quality but only 2/5 responded successfully.

**The user's insight:** You (Argos) have MCP connectors that are actual bioresearch databases — not LLMs guessing, but ground-truth data sources. These should participate in the tribunal as evidence providers.

## Your Mission

Use your MCP connectors to gather evidence for/against these 4 genome claims:

### Claim 1: Species Identification
> "16S rRNA and whole-genome analysis confirm the isolate as Leuconostoc mesenteroides ATCC 8293"
- **Open Targets:** Search for Leuconostoc mesenteroides gene targets
- **Consensus/Scholar Gateway:** Find papers on L. mesenteroides ATCC 8293 genomic characterization

### Claim 2: Aerobic Metabolism Restoration (most controversial, agreement=0.50)
> "The organism has genes for incomplete ETC (NADH dehydrogenase, cytochrome bd oxidase). Engineering 4-6 TCA cycle genes (sucA, sucB, sdhABCD, fumC, mdh) could restore aerobic respiration"
- **bioRxiv:** Search for "Leuconostoc TCA cycle engineering" or "LAB metabolic engineering aerobic"
- **Consensus:** Search for published work on restoring oxidative phosphorylation in obligate fermenters
- **ChEMBL:** Look up any bioactivity data for these specific enzyme targets in LAB species

### Claim 3: CRISPR Editing Feasibility (agreement=0.55)
> "CRISPR-Cas9 could be used for targeted genetic modification of L. mesenteroides for enhanced metabolic capabilities"
- **bioRxiv/Consensus:** Search for "CRISPR Leuconostoc" or "CRISPR lactic acid bacteria editing"
- **Clinical Trials:** Any gene-edited LAB therapeutic trials?

### Claim 4: Probiotic Potential (agreement=0.75)
> "L. mesenteroides shows probiotic potential through dextransucrase activity and antimicrobial peptide production"
- **Clinical Trials:** Search for "Leuconostoc mesenteroides probiotic" trials
- **ChEMBL:** Look up dextransucrase bioactivity data
- **Consensus:** Find papers on L. mesenteroides as a probiotic

## Output Format

Drop results to: `ops/virtual-office/inbox/COWORK_20260217_genome-evidence.md`

For each claim, provide:
```
## Claim N: [title]
### Evidence FOR
- [source]: [finding] (DOI/ID if available)
### Evidence AGAINST
- [source]: [finding]
### Verdict: SUPPORTED / PARTIALLY SUPPORTED / UNSUPPORTED / INSUFFICIENT DATA
```

## Why This Matters

This is the first time we'd use MCP bioresearch connectors as tribunal evidence providers — real databases backing up or challenging LLM opinions. If it works, this becomes a standard pattern: LLMs propose, databases validate.

---
**Signed:** B2 (desk B2)
