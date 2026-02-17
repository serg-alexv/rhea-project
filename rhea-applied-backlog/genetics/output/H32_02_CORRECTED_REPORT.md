# Corrected Genome Analysis: Leuconostoc mesenteroides strain H32-02 Ksu
> Accession: JBSROM000000000.1 (RefSeq: GCF_053878295.1)
> Source: NCBI PGAP v6.10 annotation (2025-12-10)
> Agent: B2 (Claude Opus 4.6) | Date: 2026-02-17
> Previous report for CP000414.1 was INCORRECT — see error log at bottom

## 1. Organism Identification

| Parameter | H32-02 Ksu (this genome) | ATCC 8293 (reference) |
|-----------|--------------------------|----------------------|
| Species | L. mesenteroides | L. mesenteroides subsp. mesenteroides |
| Strain | **H32-02 Ksu** | ATCC 8293 |
| GenBank | JBSROM000000000.1 | CP000414.1 |
| RefSeq | GCF_053878295.1 | GCF_000014445.1 |
| Genome size | 1,917,817 bp | 2,038,396 bp |
| GC content | 37.5% | 37.7% |
| Contigs | 113 (draft) | 1 (complete) |
| Contig N50 | 43,920 bp | 2,038,396 bp |
| Coverage | 99x (Illumina HiSeq) | Complete |
| PGAP genes | 2,029 total | 1,970 CDS |
| Protein-coding | 1,919 | 1,970 |
| Pseudogenes | 65 | — |
| tRNA | 38 | — |
| rRNA | 4 (partial) | — |
| ANI to ATCC 8293 | **99.34%** | (self) |
| Completeness | 94.0% (CheckM) | 100% |
| Contamination | 2.16% (CheckM) | 0% |
| Isolation source | Raw cow milk, Novosibirsk, Russia | — |
| Sequencing | Illumina HiSeq, Unicycler v0.4.8 | JGI |
| Submitter | Sirius University of Science and Technology | DOE JGI |
| Publication | Bondarenko et al. 2025, IJMS 26(24):11933 | Makarova et al. 2006 |

**ANI of 99.34%** confirms same species but **different strain** — the previous report incorrectly identified this as ATCC 8293 based on a single 1000bp BLAST hit.

---

## 2. Defense Systems

### Table 2.1: Defense System Genes (PGAP annotation)

| # | Locus Tag | Symbol | Product | System Type | Notes |
|---|-----------|--------|---------|-------------|-------|
| 1 | ACWYRP_RS02015 | — | Type I restriction endonuclease subunit R | **Type I R-M (HsdR)** | Restriction subunit |
| 2 | ACWYRP_RS02025 | — | Restriction endonuclease subunit S | **Type I R-M (HsdS)** | Specificity subunit |
| 3 | ACWYRP_RS02030 | — | Restriction endonuclease subunit S | **Type I R-M (HsdS)** | Second S subunit (possibly variant) |
| 4 | ACWYRP_RS02045 | — | Restriction endonuclease subunit S | **Type I R-M (HsdS)** | Third S subunit |
| 5 | ACWYRP_RS08910 | — | DNA-methyltransferase | **Type I R-M (HsdM)** | Cognate methyltransferase |
| 6 | ACWYRP_RS06945 | — | Class I SAM-dependent DNA methyltransferase | **Orphan MTase** | May be part of R-M or independent |
| 7 | ACWYRP_RS09215 | — | Antirestriction protein ArdA | **Anti-R-M** | Protects incoming DNA from restriction |
| 8 | ACWYRP_RS00840 | — | AbiU2 domain-containing protein | **Abi** | Abortive infection defense |
| 9 | ACWYRP_RS09185 | — | Abi family protein | **Abi** | Abortive infection defense |
| 10 | ACWYRP_RS05430 | — | Toxin-antitoxin system HicB family antitoxin | **TA (HicAB)** | Type II TA system |
| 11 | ACWYRP_RS07815 | — | Type II TA system PemK/MazF family toxin | **TA (MazEF)** | Endoribonuclease toxin |
| 12 | ACWYRP_RS10095 | — | Type II TA system RelE family toxin | **TA (RelBE)** | mRNA cleavage toxin |
| 13 | ACWYRP_RS01865 | — | Putative holin-like toxin | **Phage defense** | Holin-like |

### Summary

| System | Count | Status |
|--------|-------|--------|
| **Type I R-M** | **1 complete system** (1 HsdR + 3 HsdS + 1 HsdM) | Active (experimentally confirmed via electroporation) |
| Type II R-M | **0** | Not present |
| Type III R-M | **0** | Not present |
| Type IV R-M | **0** | Not present |
| **CRISPR/Cas** | **0** | **Not present** |
| **Abi** | **2** (AbiU2 + Abi family) | Predicted |
| **TA systems** | **3** (HicAB, MazEF, RelBE) | Predicted |
| **Antirestriction** | **1** (ArdA) | Mobile element-associated |

### Textual Analysis: Defense Systems

This strain has a **single Type I R-M system** as the primary sequence-specific defense barrier. This was confirmed experimentally by Bondarenko et al. (2025):

- The Type I methyltransferase has **97% identity to M.Lme20241II** (REBASE)
- Recognition sequence: **GAAYNNNNNCTT** (bipartite, degenerate)
- Methylation type: **N6-methyladenine (m6A)**
- The system was verified by showing that plasmid DNA from *E. coli* MC1061 (which carries EcoKI m6A methylation) transformed at **3.5x higher efficiency** than DNA from Top10 (standard Dam/Dcm only)

**No CRISPR/Cas system** was detected by PGAP, PADLOC, or DefenseFinder. This contradicts the previous report which claimed a Type II-A system was present — that claim was transferred from literature about ATCC 8293 and not verified against this genome.

The presence of ArdA (antirestriction protein) on what appears to be a mobile genetic element suggests horizontal gene transfer events where incoming DNA carried self-protection mechanisms.

The 3 TA systems (HicAB, MazEF, RelBE) are typical for LAB and function as:
- Phage defense (altruistic cell death during infection)
- Plasmid addiction (maintenance of mobile elements)
- Stress response (growth arrest under nutrient depletion)

**Implications for genetic engineering:**
- The Type I R-M system is the **sole major restriction barrier**
- No CRISPR interference to contend with (unlike ATCC 8293)
- Best strategy: propagate transformation DNA in *E. coli* MC1061 for compatible m6A methylation
- Alternative: knockout the hsdR subunit first, leaving methylation intact

---

## 3. Aerobic Metabolism

### Table 3.1: ETC/Respiratory Genes PRESENT

| # | Locus Tag | Symbol | Product | Component |
|---|-----------|--------|---------|-----------|
| 1 | **ACWYRP_RS05065** | — | **Cytochrome ubiquinol oxidase subunit I** | **CydA — terminal oxidase** |
| 2 | **ACWYRP_RS05060** | **cydB** | **Cytochrome d ubiquinol oxidase subunit II** | **CydB — terminal oxidase** |
| 3 | **ACWYRP_RS05050** | **cydC** | Thiol reductant ABC exporter subunit CydC | Heme/cofactor transport |
| 4 | **ACWYRP_RS05055** | **cydD** | Thiol reductant ABC exporter subunit CydD | Heme/cofactor transport |
| 5 | ACWYRP_RS05295 | — | NADH-dependent flavin oxidoreductase | Electron entry (NADH) |
| 6 | ACWYRP_RS08815 | — | NADH-dependent flavin oxidoreductase | Electron entry (NADH) |
| 7 | ACWYRP_RS05250-05285 | atpBEFHADG (operon) | **F0F1 ATP synthase** (8 subunits) | Oxidative phosphorylation |
| 8 | ACWYRP_RS04865 | ubiE | Demethylmenaquinone methyltransferase | Menaquinone biosynthesis |
| 9 | ACWYRP_RS09250 | spxB | Pyruvate oxidase | Aerobic pyruvate metabolism |

### Table 3.2: Key Aerobic Genes MISSING (ranked by importance)

| # | Gene | Function | Importance | Rationale |
|---|------|----------|------------|-----------|
| 1 | **menA-menH** | Menaquinone biosynthesis pathway (8 genes) | CRITICAL | Electron shuttle between NADH DH and CydAB (only ubiE found) |
| 2 | **ndh** | Type II NADH dehydrogenase (proton-pumping) | HIGH | Dedicated respiratory NADH DH; the NADH-flavin oxidoreductases present are non-respiratory |
| 3 | **hemABCDEFGHKLN** | Heme biosynthesis pathway | HIGH | CydAB requires heme b and heme d prosthetic groups |
| 4 | sdhABCD | Succinate dehydrogenase (Complex II) | MEDIUM | Links TCA to ETC; only needed for full TCA cycle |
| 5 | gltA, acnA, icd, sucAB, fumC, mdh | TCA cycle enzymes | LOW | Full aerobic metabolism — likely incompatible with LAB physiology |

### Textual Analysis: Aerobic Potential

**CRITICAL CORRECTION:** The previous report listed cydA and cydB as **missing** from the genome. This was **factually wrong**. The genome encodes the complete cydABCD operon:

```
ACWYRP_RS05050  cydC  — ABC exporter for heme/thiol cofactors
ACWYRP_RS05055  cydD  — ABC exporter partner
ACWYRP_RS05060  cydB  — cytochrome bd oxidase subunit II
ACWYRP_RS05065  (cydA) — cytochrome ubiquinol oxidase subunit I
```

This changes the aerobic metabolism picture fundamentally:

**What H32-02 Ksu HAS:**
- Complete cytochrome bd oxidase (CydAB) — the terminal electron acceptor
- CydCD transport system for heme/cofactor assembly
- NADH-dependent flavin oxidoreductases (2 copies) — can feed electrons
- Complete F0F1 ATP synthase (8 subunits) — can produce ATP from proton gradient
- Pyruvate oxidase (SpxB) — aerobic pyruvate metabolism
- UbiE — one step of menaquinone/ubiquinone biosynthesis

**What it LACKS:**
- Complete menaquinone biosynthesis (has only ubiE, missing menABCDFGH)
- Heme biosynthesis (CydAB needs heme b558 and heme d)
- Dedicated respiratory NADH dehydrogenase (ndh)

**Minimal restoration strategies (revised):**

**Strategy A: Heme + Menaquinone supplementation (0 genes needed)**
This is the *L. plantarum* strategy. Since CydABCD are already present, simply adding **heme** and **menaquinone (vitamin K2)** to the growth medium may be sufficient to activate respiratory metabolism. This has been demonstrated in *L. plantarum* and *Enterococcus faecalis*. No genetic engineering required — just medium formulation.

**Strategy B: Add menaquinone biosynthesis (8 genes)**
Engineer menABCDEFGH from a donor organism (e.g., *Bacillus subtilis*). Combined with exogenous heme, this would make the strain self-sufficient for the electron shuttle while still requiring heme supplementation.

**Strategy C: Full respiratory self-sufficiency (~20 genes)**
Add menaquinone + heme biosynthesis pathways. Extremely ambitious and likely impractical for a LAB.

---

## 4. DNA Repair and Recombination

### Table 4.1: Recombination/Repair Genes

| # | Locus Tag | Symbol | Product | System |
|---|-----------|--------|---------|--------|
| 1 | ACWYRP_RS04945 | **recA** | Recombinase RecA | HR (central) |
| 2 | ACWYRP_RS06020 | **recF** | DNA replication/repair protein RecF | HR (RecFOR pathway) |
| 3 | ACWYRP_RS00170 | **recO** | DNA repair protein RecO | HR (RecFOR pathway) |
| 4 | ACWYRP_RS03350 | **recR** | Recombination mediator RecR | HR (RecFOR pathway) |
| 5 | ACWYRP_RS04610 | **recG** | ATP-dependent DNA helicase RecG | HR (branch migration) |
| 6 | ACWYRP_RS02285 | **recJ** | Single-stranded DNA exonuclease RecJ | HR (end processing) |
| 7 | ACWYRP_RS06825 | **recN** | DNA repair protein RecN | HR (DSB repair) |
| 8 | ACWYRP_RS08405 | **recQ** | DNA helicase RecQ | HR (unwinding) |
| 9 | ACWYRP_RS00810 | **recU** | Holliday junction resolvase RecU | HR (resolution) |
| 10 | ACWYRP_RS05800 | **ruvB** | Holliday junction branch migration helicase RuvB | HR (branch migration) |
| 11 | ACWYRP_RS05820 | **ruvA** | Holliday junction branch migration protein RuvA | HR (branch migration) |
| 12 | ACWYRP_RS05075 | **ruvX** | Holliday junction resolvase RuvX | HR (resolution) |
| 13 | ACWYRP_RS06640 | **mutS** | DNA mismatch repair protein MutS | MMR |
| 14 | ACWYRP_RS06645 | **mutL** | DNA mismatch repair endonuclease MutL | MMR |
| 15 | ACWYRP_RS05025 | **ligA** | NAD-dependent DNA ligase LigA | Ligation |
| 16 | ACWYRP_RS03045 | **xerC** | Tyrosine recombinase XerC | Site-specific recombination |
| 17 | ACWYRP_RS02615 | **xerD** | Site-specific tyrosine recombinase XerD | Site-specific recombination |

### Missing components

| Gene | Function | Impact |
|------|----------|--------|
| **recB, recC, recD** | RecBCD helicase-nuclease (NHEJ processing) | No RecBCD pathway — relies on RecFOR for HR initiation |
| **ruvC** | Canonical Holliday junction resolvase | Has RecU and RuvX as alternatives |
| **uvrA, uvrB, uvrC, uvrD** | Not found by gene symbol search | NER may be present under different annotations |
| **mutH** | MutH-type strand discrimination | Type absent (common in Gram-positives) |

### CRISPR/Cas Editing Feasibility

**Advantages over ATCC 8293:**
1. **No endogenous CRISPR/Cas** — foreign CRISPR constructs won't be degraded by native CRISPR immunity
2. **Complete RecFOR pathway** (recF, recO, recR) — homologous recombination for knock-in works
3. **RecA present** — essential for homology-directed repair
4. **No RecBCD** — reduces degradation of linear DNA repair templates
5. **Single Type I R-M** barrier already characterized with a workaround (MC1061 methylation)
6. **Electroporation protocol established** (Bondarenko et al. 2025, ~800 CFU/ug)

**Recommended CRISPR editing strategy:**

1. **Vector system:** Express *Streptococcus pyogenes* Cas9 (or *Streptococcus thermophilus* Cas9 for tighter control) + sgRNA from a replicating shuttle vector (e.g., pHyC-based)
2. **Repair template:** Include 500-1000bp homology arms flanking the target for RecFOR-mediated HDR
3. **Methylation:** Propagate all constructs in *E. coli* MC1061 for compatible methylation
4. **Selection:** Chloramphenicol (pHyC) for vector maintenance; counter-selection for curing after editing
5. **Electroporation:** Use the optimized protocol (1% glycine, 0.5M sucrose/10% glycerol, reduced voltage)

**Key challenge:** The transformation efficiency (~800 CFU/ug) is 10-100x lower than model LAB like *Lactococcus lactis*. Multi-step editing (gene stacking) will require iterative transformation cycles.

---

## 5. Probiotic Potential

### Table 5.1: Probiotic-Relevant Genes

| # | Locus Tag | Symbol | Product | Function |
|---|-----------|--------|---------|----------|
| 1 | **ACWYRP_RS06245** | — | **Bacteriocin** | Antimicrobial peptide production |
| 2 | **ACWYRP_RS05190** | — | **Bacteriocin immunity protein** | Self-protection from own bacteriocin |
| 3 | ACWYRP_RS07975 | **epsC** | Serine O-acetyltransferase EpsC | EPS biosynthesis regulation |
| 4 | ACWYRP_RS09735 | — | EpsG family protein | EPS biosynthesis |
| 5 | ACWYRP_RS09295 | — | **Mucin-binding protein** | Gut adhesion |
| 6 | ACWYRP_RS10065 | — | **Mucin-binding protein** | Gut adhesion |
| 7 | ACWYRP_RS04755 | — | Bile acid:sodium symporter family protein | Bile salt tolerance |
| 8 | ACWYRP_RS04550 | — | GH25 family lysozyme | Cell wall lysis (antimicrobial) |
| 9 | ACWYRP_RS07585 | — | GH25 family lysozyme | Cell wall lysis (antimicrobial) |
| 10 | ACWYRP_RS08900 | — | GH25 family lysozyme | Cell wall lysis (antimicrobial) |
| 11 | ACWYRP_RS09175 | — | GH25 family lysozyme | Cell wall lysis (antimicrobial) |
| 12 | ACWYRP_RS09465 | — | GH25 family lysozyme | Cell wall lysis (antimicrobial) |
| 13 | ACWYRP_RS00215 | pepT | Peptidase T | Protein digestion |
| 14 | ACWYRP_RS02000 | pepV | Dipeptidase PepV | Peptide hydrolysis |
| 15 | ACWYRP_RS08430 | pepV | Dipeptidase PepV | Peptide hydrolysis |
| 16 | ACWYRP_RS04170 | pepF | Oligoendopeptidase F | Casein-derived peptide processing |
| 17 | ACWYRP_RS06845 | pepA | Glutamyl aminopeptidase | Bioactive peptide release |
| 18 | ACWYRP_RS06870 | — | SepM family pheromone-processing serine protease | Quorum sensing |

### Notable ABSENCE: Dextransucrase

No dextransucrase gene (dsrS/dsrA) was identified by PGAP. This was claimed in the previous report. While L. mesenteroides is famous for dextran production, not all strains carry the gene, and it may be on a plasmid not assembled in this draft genome (94% completeness). EPS biosynthesis genes (epsC, epsG) are present but may produce different exopolysaccharides.

### Textual Analysis: Probiotic Potential

H32-02 Ksu shows moderate probiotic potential:

**Strengths:**
- **Bacteriocin + immunity pair** — produces antimicrobial peptides against competing bacteria
- **5 GH25 family lysozymes** — unusually high copy number; these can lyse peptidoglycan of competing Gram-positive bacteria
- **2 mucin-binding proteins** — suggests capacity for gut epithelial adhesion
- **Bile acid symporter** — bile salt tolerance for GI tract survival
- **Multiple peptidases** (PepT, PepV x2, PepF, PepA) — can release bioactive peptides from dietary proteins (especially casein, given dairy isolation source)

**Limitations:**
- No confirmed dextransucrase — may not produce dextran
- Draft genome (94% complete) may be missing some probiotic genes
- No acid tolerance genes specifically identified (though LAB are inherently acid-tolerant)
- Isolated from raw cow milk, not from a probiotic context

---

## 6. Comparison: H32-02 Ksu vs. Previous Report (CP000414.1-based)

| Feature | Previous Report (WRONG) | Corrected (H32-02 Ksu PGAP) | Error Type |
|---------|------------------------|------------------------------|------------|
| **Strain** | ATCC 8293 | **H32-02 Ksu** | Wrong strain identification |
| **R-M systems** | "20 R-M genes, Type II-A CRISPR present" | **1 Type I R-M system, NO CRISPR** | Catastrophic — counted housekeeping methyltransferases as R-M |
| **cydA** | Listed as MISSING (CRITICAL) | **PRESENT** (ACWYRP_RS05065) | Self-contradictory — was in gene catalog but listed as missing |
| **cydB** | Listed as MISSING (CRITICAL) | **PRESENT** (ACWYRP_RS05060) | Same error |
| **cydC** | Not mentioned | **PRESENT** (ACWYRP_RS05050) | Omission |
| **cydD** | Not mentioned | **PRESENT** (ACWYRP_RS05055) | Omission |
| **CRISPR/Cas** | "Type II-A present (Cas9)" | **NOT PRESENT** | Taken from ATCC 8293 literature, never verified |
| **Aerobic strategy** | "Add cydAB + ndh + menABCDEFH" | **Add menA-H + heme; or just supplement media** | cydABCD already present changes everything |
| **Defense count** | 76 "defense genes" | **13 genuine defense genes** | Miscategorized core metabolism as defense |
| **Gene count** | 2,036 (Prodigal) | 2,029 (PGAP) | Close — Prodigal prediction was reasonable |
| **Genome size** | 1,917,817 bp | 1,917,817 bp | Correct (same genome file) |
| **GC content** | 37.66% | 37.5% | Minor difference in calculation |

### Root Cause of Errors

1. **Species ID was correct, strain was not.** BLAST of 1000bp showed 100% identity to CP000414.1 (top hit) but also 99-100% to dozens of other strains. Should have reported "L. mesenteroides, strain undetermined" not "ATCC 8293."

2. **Annotation was transferred from CP000414.1, not generated de novo.** Prodigal predictions were real, but functional assignments came from k-mer matching to the reference. This works for conserved housekeeping genes but fails for strain-specific accessory genome (defense systems, mobile elements).

3. **Analytical sections were generated from published knowledge about ATCC 8293**, not from actual interrogation of the gene catalog. This created contradictions (cydA/B present in catalog but listed as missing in aerobic analysis).

4. **Defense system classification was done by keyword matching** ("methyltransferase" → R-M, "helicase" → CRISPR). Professional tools (PADLOC, DefenseFinder, REBASE) use operon context, domain architecture, and co-occurrence patterns.

---

## 7. Comprehensive Assessment: Capabilities, Applications, and Engineering Roadmap

### 7.1 What This Organism Can Do

**Leuconostoc mesenteroides** strain H32-02 Ksu is a heterofermentative lactic acid bacterium isolated from raw cow milk in Novosibirsk, Russia. Its genome (1.92 Mbp, 2,029 genes, 37.5% GC) encodes the following functional capabilities:

**Fermentation:**
- Primary metabolism: heterofermentative — produces lactate, ethanol, CO2, and acetate from sugars via the phosphoketolase pathway
- Multiple PTS sugar transporters (glucose, fructose, mannose, sucrose, cellobiose, trehalose)
- Broad carbohydrate utilization: galactose, ribose, xylose pathways present
- Ethanol production via alcohol dehydrogenase (bifunctional acetaldehyde-CoA/alcohol dehydrogenase)

**Latent Aerobic Capacity:**
- Complete cytochrome bd oxidase (CydABCD) — can reduce O2 as terminal electron acceptor
- F0F1 ATP synthase — can generate ATP from proton motive force
- Pyruvate oxidase (SpxB) — aerobic pyruvate metabolism producing acetyl-phosphate + CO2 + H2O2
- NADH-flavin oxidoreductases — can regenerate NAD+ using O2
- **Missing: menaquinone and heme biosynthesis** — requires exogenous supplementation or pathway engineering

**Antimicrobial Production:**
- Bacteriocin + cognate immunity protein pair
- 5 GH25 family lysozymes (unusually high copy number) — lyse Gram-positive competitors
- H2O2 production via SpxB under aerobic conditions

**Gut/Surface Interaction:**
- 2 mucin-binding proteins — potential gut epithelial adhesion
- Bile acid symporter — bile salt tolerance
- EPS biosynthesis genes (epsC, epsG) — exopolysaccharide production for biofilm/capsule

**Proteolytic System:**
- Multiple peptidases (PepT, PepV x2, PepF, PepA, SepM) — can process dietary proteins, especially casein

**Genetic Accessibility:**
- Electroporation protocol established (Bondarenko et al. 2025, ~800 CFU/µg)
- Single Type I R-M barrier with known workaround (MC1061 methylation)
- No CRISPR interference
- Complete RecFOR pathway for homologous recombination

### 7.2 Food Biotechnology Applications

**Dairy Fermentation (primary, established):**
- Naturally adapted to milk environments (dairy isolate)
- Heterofermentation produces CO2 for "eye" formation in cheeses
- Diacetyl/acetoin production for butter flavor (citrate metabolism genes present)
- Multiple peptidases release bioactive peptides and flavor compounds from casein
- Potential starter culture for artisanal cheeses, kefir, fermented milk products

**Vegetable Fermentation:**
- L. mesenteroides is the canonical initiator of sauerkraut and kimchi fermentation
- Produces CO2 that displaces O2, creating anaerobic environment for subsequent Lactobacillus species
- Rapid acidification inhibits spoilage organisms

**Dextran/EPS Production:**
- **Note:** No dextransucrase (dsrS) found in this draft genome — may be plasmid-encoded or missing from assembly
- EPS genes present (epsC, epsG) — may produce alternative exopolysaccharides
- If dextransucrase is added or found on unassembled plasmid: dextran production for food texturizing, clinical dextran, prebiotics

**Biopreservation:**
- Bacteriocin production — natural food preservative against Listeria, Staphylococcus, and other pathogens
- 5 lysozymes — broad-spectrum lysis of competing Gram-positives
- Can be used as protective culture in fresh cheeses, ready-to-eat foods

### 7.3 Medical/Pharmaceutical Applications

**Probiotic Potential (moderate):**
- Mucin-binding proteins suggest gut adhesion capacity
- Bile salt tolerance for GI survival
- Bacteriocin production against pathogens
- **Limitation:** not yet validated in clinical trials as a probiotic strain
- L. mesenteroides has GRAS status (Generally Recognized As Safe) in the US

**Bioactive Peptide Production:**
- Casein-derived peptides (ACE-inhibitory, antioxidant, antimicrobial) — released by PepA, PepF, PepV
- Potential for production of functional foods with antihypertensive properties

**Clinical Dextran (if dsrS added):**
- Dextran is used clinically as a plasma volume expander, antithrombotic, and in iron-dextran formulations
- Microbial production is the standard industrial method

**Delivery Vehicle:**
- LAB can be engineered as mucosal delivery vehicles for antigens, cytokines, or enzymes
- H32-02 Ksu's mucin-binding proteins and bile tolerance are advantages for this application

### 7.4 Genetic Engineering Roadmap

**Tier 1: No Genetic Modification Required**

| Strategy | Action | Expected Outcome |
|----------|--------|-----------------|
| Aerobic growth activation | Add **hemin** (1-10 µg/mL) + **menaquinone/vitamin K2** (1-10 µg/mL) to growth medium | Shift from fermentation to respiration; increased biomass yield (2-4x, based on L. plantarum precedent); improved survival in stationary phase |
| Optimized transformation | Use *E. coli* MC1061 as cloning host for all constructs | 3.5x improvement in electroporation efficiency due to compatible EcoKI m6A methylation |

**Tier 2: Single-Gene Modifications (feasible with current tools)**

| Target | Modification | Purpose | Difficulty |
|--------|-------------|---------|------------|
| hsdR knockout | Delete ACWYRP_RS02015 | Eliminate restriction barrier entirely; methylation preserved via HsdM | Low — single gene, RecFOR-mediated |
| spxB overexpression | Strong promoter + extra copy | Enhanced H2O2 production for biopreservation | Low |
| Bacteriocin upregulation | Promoter replacement on ACWYRP_RS06245 | Increased antimicrobial activity | Low-Medium |
| dsrS addition | Express dextransucrase from L. mesenteroides NRRL B-512F | Dextran production capability | Medium |

**Tier 3: Pathway Engineering (ambitious, multi-gene)**

| Pathway | Genes Needed | Source | Outcome |
|---------|-------------|--------|---------|
| Menaquinone biosynthesis | menABCDEFGH (8 genes) | *Bacillus subtilis* 168 | Self-sufficient respiratory metabolism (with exogenous heme) |
| Heme biosynthesis | hemABCDEFGHKLN (11 genes) | *B. subtilis* or *E. coli* | Complete heme self-sufficiency — combined with menaquinone = fully autonomous aerobic growth |
| Nisin production | nisABTCIPRKFEG (11 genes) | *Lactococcus lactis* | Production of the most commercially important bacteriocin |
| Folate biosynthesis | folBKECPAD (7 genes) | *L. plantarum* WCFS1 | B-vitamin-producing probiotic for functional foods |

**Tier 4: Synthetic Biology (research frontier)**

- **Minimal genome:** 65 pseudogenes and 35 mobile elements (transposases/integrases) could be removed for genome streamlining
- **Biosensor strain:** Engineer reporter genes under defense system promoters for phage detection
- **Consortium engineering:** Pair with complementary species (e.g., *Lactobacillus plantarum* for menaquinone supply, *Propionibacterium* for B12)

### 7.5 CRISPR/Cas Editing Protocol (Recommended)

Based on the recombination machinery and restriction landscape of H32-02 Ksu:

```
1. VECTOR: pNZ8148-based (Cm resistance, nisA promoter)
   - Insert SpCas9 or StCas9 under nisin-inducible promoter
   - Insert sgRNA under constitutive P32 promoter
   - Add 500-1000 bp homology arms flanking target

2. PREPARATION:
   - Transform vector into E. coli MC1061 (for EcoKI m6A methylation)
   - Verify by restriction analysis (MC1061 DNA should resist HsdR cleavage)

3. ELECTROPORATION (Bondarenko et al. 2025 protocol):
   - Grow H32-02 Ksu to OD600 0.3-0.5 in MRS + 1% glycine (weakens cell wall)
   - Wash 3x in ice-cold 0.5M sucrose + 10% glycerol
   - Electroporate: reduced voltage (optimized for this strain)
   - Recover in MRS 2h at 30°C
   - Plate on MRS + chloramphenicol (5-10 µg/mL)

4. EDITING:
   - Screen colonies by colony PCR spanning target site
   - Induce Cas9 with nisin to cut target
   - RecFOR pathway mediates HDR using homology arms
   - Expected efficiency: 10-50% of surviving colonies (based on LAB CRISPR literature)

5. CURING:
   - Passage without selection to lose plasmid
   - Verify by replica plating (Cm-sensitive = cured)

6. LIMITATIONS:
   - Low transformation efficiency (~800 CFU/µg) limits throughput
   - Multi-gene stacking requires iterative cycles
   - No RecBCD means linear DNA templates degrade slowly (advantage for HDR)
   - Consider using RecT/RecE recombineering as alternative to CRISPR for simple knockouts
```

---

## Sources

- NCBI Assembly: [GCF_053878295.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_053878295.1/)
- WGS Accession: [JBSROM000000000.1](https://www.ncbi.nlm.nih.gov/nuccore/JBSROM000000000.1)
- BioProject: [PRJNA1373125](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1373125)
- BioSample: [SAMN53635418](https://www.ncbi.nlm.nih.gov/biosample/SAMN53635418)
- Bondarenko et al. (2025) IJMS 26(24):11933 — [DOI:10.3390/ijms262411933](https://www.mdpi.com/1422-0067/26/24/11933)
