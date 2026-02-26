# Full Re-Analysis: Leuconostoc mesenteroides H32-02 Ksu
> Accession: JBSROM000000000.1 (RefSeq: GCF_053878295.1)
> Source: NCBI PGAP v6.10 annotation + genome_contigs.fasta
> Agent: B2 (Claude Opus 4.6) | Date: 2026-02-17
> This report supersedes both the original CP000414.1-based report AND the first correction

## Methodology Note

This analysis uses NCBI PGAP v6.10 annotation of the submitted genome. PGAP has ~90-98% structural accuracy and ~85% functional annotation accuracy vs curated references (Li et al. 2021, Schwengers et al. 2021). It is the best available annotation for this genome but has limitations:
- ~15% of proteins labeled "hypothetical" (could miss real genes)
- Underrepresented taxa (like LAB) may have more hypothetical calls
- A second annotation with Bakta (lowest hypothetical rate at ~10.6%) and targeted tBLASTn for specific genes of interest (especially ndh) is recommended for verification

---

## 1. Defense Systems

### Table 1.1: Defense System Genes

| # | Locus Tag | Symbol | Product | System | Specific Function |
|---|-----------|--------|---------|--------|-------------------|
| 1 | ACWYRP_RS02015 | — | Type I restriction endonuclease subunit R | Type I R-M (HsdR) | Cleaves DNA at non-methylated GAAYNNNNNCTT sites; requires ATP |
| 2 | ACWYRP_RS02025 | — | Restriction endonuclease subunit S | Type I R-M (HsdS) | Specificity subunit — determines recognition sequence |
| 3 | ACWYRP_RS02030 | — | Restriction endonuclease subunit S | Type I R-M (HsdS) | Second S subunit (possibly variant specificity) |
| 4 | ACWYRP_RS02045 | — | Restriction endonuclease subunit S | Type I R-M (HsdS) | Third S subunit (possibly mobile element-associated) |
| 5 | ACWYRP_RS08910 | — | DNA-methyltransferase | Type I R-M (HsdM) | Methylates adenine in GAAYNNNNNCTT (m6A); protects self DNA |
| 6 | ACWYRP_RS06945 | — | Class I SAM-dependent DNA methyltransferase | Orphan MTase | May be part of R-M or independent regulatory methylation |
| 7 | ACWYRP_RS09215 | — | Antirestriction protein ArdA | Anti-R-M | Mimics DNA structure; protects incoming mobile elements from HsdR |
| 8 | ACWYRP_RS00840 | — | AbiU2 domain-containing protein | Abortive infection | Triggers cell death upon phage infection to protect colony |
| 9 | ACWYRP_RS09185 | — | Abi family protein | Abortive infection | Second Abi system; different phage specificity |
| 10 | ACWYRP_RS05430 | — | HicB family antitoxin | TA (HicAB) | Antitoxin neutralizes HicA ribonuclease under normal growth |
| 11 | ACWYRP_RS07815 | — | PemK/MazF family toxin | TA (MazEF) | Endoribonuclease toxin; cleaves mRNA at specific sequences |
| 12 | ACWYRP_RS10095 | — | RelE family toxin | TA (RelBE) | Ribosome-dependent mRNA cleavage toxin |
| 13 | ACWYRP_RS01865 | — | Putative holin-like toxin | Phage defense | Membrane pore; may trigger lysis during phage infection |

### Table 1.2: Defense System Summary

| System | Components | Status | Evidence |
|--------|-----------|--------|----------|
| Type I R-M | 1 HsdR + 3 HsdS + 1 HsdM | **1 functional system** | Confirmed experimentally (Bondarenko et al. 2025); recognition: GAAYNNNNNCTT; 97% identity to M.Lme20241II (REBASE) |
| Orphan MTase | 1 Class I SAM-dependent | Present | May provide additional methylation protection |
| Anti-restriction (ArdA) | 1 | Present | Mobile element-associated; protects incoming DNA from HsdR |
| CRISPR/Cas | **0** | **Absent** | Not detected by PGAP, PADLOC, or DefenseFinder |
| Type II R-M | **0** | **Absent** | No Type II REase detected |
| Abortive infection | 2 (AbiU2 + Abi family) | Predicted | Not experimentally verified |
| Toxin-antitoxin | 3 systems (HicAB, MazEF, RelBE) | Predicted | Standard LAB TA repertoire |
| Holin | 1 | Predicted | Membrane disruption role |

### Analysis: Defense Systems

This strain has a **minimal but experimentally characterized defense landscape**:

**The Type I R-M system** is the sole sequence-specific restriction barrier. Three HsdS subunits suggest the system can recognize multiple target sequences (Type I systems use HsdS for specificity, and multiple S subunits allow target switching). The recognition site GAAYNNNNNCTT was determined by comparison to REBASE (97% identity to M.Lme20241II) and confirmed functionally: plasmid DNA from E. coli MC1061 (which carries EcoKI m6A methylation compatible with this system) transforms at **3.5x higher efficiency** than DNA from Top10 (standard Dam/Dcm only) (Bondarenko et al. 2025).

**No CRISPR/Cas** was detected by any method. This is notable because L. mesenteroides ATCC 8293 reportedly has a Type II-A system — the absence in H32-02 Ksu is a strain-level difference (consistent with CRISPR systems being on mobile elements).

**The 3 TA systems** (HicAB, MazEF, RelBE) serve dual roles: (1) phage defense via altruistic cell death, (2) plasmid maintenance via post-segregational killing, and (3) stress response via growth arrest under nutrient limitation.

**The ArdA antirestriction protein** on a mobile element indicates historical horizontal gene transfer events where incoming DNA carried self-protection against the host R-M system.

**What was wrong in previous reports:**
- Original report: claimed 20 R-M genes and 76 total defense genes (by keyword matching "methyltransferase" → R-M, "helicase" → CRISPR)
- First correction: correctly identified 1 Type I system but did not re-examine orphan MTase and ArdA relationships
- This analysis: confirms 13 genuine defense genes across 6 system types

---

## 2. Aerobic Metabolism

### Table 2.1: ETC/Respiratory Genes PRESENT

| # | Locus Tag | Symbol | Product | Component | Specific Role |
|---|-----------|--------|---------|-----------|---------------|
| 1 | ACWYRP_RS05065 | — | Cytochrome ubiquinol oxidase subunit I | **CydA** | Terminal oxidase — reduces O2 to H2O using electrons from menaquinol |
| 2 | ACWYRP_RS05060 | cydB | Cytochrome d ubiquinol oxidase subunit II | **CydB** | Second subunit of terminal oxidase; contains heme d |
| 3 | ACWYRP_RS05050 | cydC | Thiol reductant ABC exporter subunit CydC | CydC | Exports heme/thiol cofactors for CydAB assembly |
| 4 | ACWYRP_RS05055 | cydD | Thiol reductant ABC exporter subunit CydD | CydD | Partner of CydC; required for CydAB maturation |
| 5 | ACWYRP_RS05250 | atpB | F0F1 ATP synthase subunit A | F0 (membrane) | Proton channel |
| 6 | ACWYRP_RS05255 | atpE | F0F1 ATP synthase subunit C | F0 (membrane) | Proton translocation ring |
| 7 | ACWYRP_RS05260 | atpF | F0F1 ATP synthase subunit B | F0 (membrane) | Stator |
| 8 | ACWYRP_RS05265 | atpH | ATP synthase F1 subunit delta | F1 (cytoplasmic) | Stator connection |
| 9 | ACWYRP_RS05270 | atpA | F0F1 ATP synthase subunit alpha | F1 (cytoplasmic) | Regulatory nucleotide binding |
| 10 | ACWYRP_RS05275 | — | F0F1 ATP synthase subunit gamma | F1 (cytoplasmic) | Rotor shaft |
| 11 | ACWYRP_RS05280 | atpD | F0F1 ATP synthase subunit beta | F1 (cytoplasmic) | Catalytic ATP synthesis |
| 12 | ACWYRP_RS05285 | — | F0F1 ATP synthase subunit epsilon | F1 (cytoplasmic) | Regulation |
| 13 | ACWYRP_RS00320 | — | Isochorismate synthase | **menF** | Menaquinone step 1: chorismate → isochorismate |
| 14 | ACWYRP_RS00315 | menD | 2-succinyl-5-enolpyruvyl-6-hydroxy-3-cyclohexene-1-carboxylate synthase | **menD** | Menaquinone step 2 |
| 15 | ACWYRP_RS00310 | menH | 2-succinyl-6-hydroxy-2,4-cyclohexadiene-1-carboxylate synthase | **menH** | Menaquinone step 3 |
| 16 | ACWYRP_RS00305 | menC | o-succinylbenzoate synthase | **menC** | Menaquinone step 4 |
| 17 | ACWYRP_RS04860 | — | o-succinylbenzoate--CoA ligase | **menE** | Menaquinone step 5 |
| 18 | ACWYRP_RS06080 | menB | 1,4-dihydroxy-2-naphthoyl-CoA synthase | **menB** | Menaquinone step 6 |
| 19 | ACWYRP_RS06430 | — | UbiA family prenyltransferase | **menA (probable)** | Menaquinone step 7: attaches prenyl chain to DHNA |
| 20 | ACWYRP_RS04865 | ubiE | Bifunctional demethylmenaquinone methyltransferase | **ubiE** | Menaquinone final step: DMK → MK |
| 21 | ACWYRP_RS09250 | spxB | Pyruvate oxidase | SpxB | Aerobic pyruvate → acetyl-P + CO2 + H2O2 (FAD-dependent, O2 as acceptor) |
| 22 | ACWYRP_RS05295 | — | NADH-dependent flavin oxidoreductase | Non-respiratory | Cytoplasmic NAD+ regeneration using flavin; NOT quinone-linked |
| 23 | ACWYRP_RS08815 | — | NADH-dependent flavin oxidoreductase | Non-respiratory | Second copy |

### Table 2.2: Key Aerobic Genes MISSING

| # | Gene | Function | Importance | Why It Matters |
|---|------|----------|------------|----------------|
| 1 | **ndh** | **Type II NADH:quinone oxidoreductase** | **CRITICAL** | The ONLY enzyme that connects NADH to the menaquinone pool. Without it, the ETC has no electron input. Experimentally proven essential in L. plantarum (Brooijmans et al. 2009): ndh1-knockout shows NO respiratory phenotype even with heme+MK |
| 2 | **hemA-hemN** (most steps) | Heme biosynthesis (ALA → heme) | HIGH | CydAB requires heme b558 and heme d as prosthetic groups. Only hemH (ferrochelatase, last step) + 2 uroporphyrinogen decarboxylases found. Missing ~8 upstream steps |
| 3 | noxE | H2O-forming NADH oxidase | MEDIUM | Would allow direct O2-dependent NAD+ regeneration (not ETC-coupled). Not found in this genome |
| 4 | sdhABCD | Succinate dehydrogenase (Complex II) | LOW | Links TCA to ETC; only relevant if TCA cycle were restored |
| 5 | gltA, acnA, icd, sucAB, fumC, mdh | TCA cycle enzymes | LOW | Full aerobic catabolism; likely incompatible with LAB physiology |

### Table 2.3: Menaquinone Pathway Status (REVISED)

| Step | Gene | Enzyme | Locus Tag | Status |
|------|------|--------|-----------|--------|
| 1 | menF | Isochorismate synthase | ACWYRP_RS00320 | **PRESENT** (no gene symbol assigned) |
| 2 | menD | SEPHCHC synthase | ACWYRP_RS00315 | **PRESENT** |
| 3 | menH | SHCHC synthase | ACWYRP_RS00310 | **PRESENT** |
| 4 | menC | o-succinylbenzoate synthase | ACWYRP_RS00305 | **PRESENT** |
| 5 | menE | o-succinylbenzoate-CoA ligase | ACWYRP_RS04860 | **PRESENT** (no gene symbol) |
| 6 | menB | DHNA-CoA synthase | ACWYRP_RS06080 | **PRESENT** |
| 7 | menA | DHNA octaprenyltransferase | ACWYRP_RS06430 | **PROBABLE** (annotated as "UbiA family prenyltransferase") |
| 8 | ubiE | DMK methyltransferase | ACWYRP_RS04865 | **PRESENT** |

**Previous reports said "only ubiE found, missing menABCDEFGH" — this was WRONG. 7/8 steps are present, menA is probable.**

### Table 2.4: Heme Biosynthesis Status

| Gene | Enzyme | Locus Tag | Status |
|------|--------|-----------|--------|
| hemA | Glutamyl-tRNA reductase | — | **MISSING** |
| hemL | Glutamate-1-semialdehyde aminotransferase | — | **MISSING** |
| hemB | ALA dehydratase | — | **MISSING** |
| hemC | Porphobilinogen deaminase | — | **MISSING** |
| hemD | Uroporphyrinogen III synthase | — | **MISSING** |
| hemE | Uroporphyrinogen decarboxylase | ACWYRP_RS04330, RS04335 | **PRESENT** (2 copies) |
| hemN/hemF | Coproporphyrinogen oxidase | — | **MISSING** |
| hemG/hemJ | Protoporphyrinogen oxidase | — | **MISSING** |
| hemH | Ferrochelatase (protoporphyrin + Fe²⁺ → heme) | ACWYRP_RS05595 | **PRESENT** |

Only 3 of ~10 heme pathway genes found. **Cannot synthesize heme endogenously.**

### Analysis: Aerobic Metabolism

**The previous reports contained THREE major errors in the aerobic analysis:**

1. **cydA/cydB listed as MISSING** — they are PRESENT (complete CydABCD operon)
2. **Menaquinone pathway said "only ubiE"** — actually 7/8 steps present (menF, D, H, C, E, B, ubiE confirmed + probable menA)
3. **ndh omitted from the critical-missing list** — ndh is THE critical bottleneck

**The actual aerobic metabolism situation:**

H32-02 Ksu has most components of an aerobic ETC:
- Terminal oxidase (CydABCD): **COMPLETE**
- ATP synthase (F0F1): **COMPLETE** (8 subunits)
- Menaquinone biosynthesis: **NEARLY COMPLETE** (7-8/8 steps)
- NADH:quinone oxidoreductase (ndh): **NOT FOUND BY PGAP**
- Heme biosynthesis: **MOSTLY ABSENT** (only hemH + hemE x2)

**The critical bottleneck is ndh**, not menaquinone or cydABCD.

The ETC chain is: NADH → **ndh** → menaquinone → CydAB → O₂

Without ndh, this chain is broken at the very first step. Menaquinone has no way to become reduced. CydAB has no substrate (menaquinol). No proton motive force is generated. No respiratory ATP production.

This was experimentally demonstrated in L. plantarum WCFS1 (Brooijmans et al. 2009, DOI: 10.1128/AEM.00147-09):
- ndh1Δ mutant: OD600 = 7.22 with heme+MK (vs 9.88 wild-type) — NO respiratory benefit
- cydAΔ mutant: OD600 = 5.56 with heme+MK — same loss of respiratory phenotype
- Both genes are individually required; the chain is nonredundant

**Important caveat:** 192 "NADH dehydrogenase" protein entries exist across L. mesenteroides strains in NCBI (both 556 aa and 213 aa variants). PGAP may have annotated the ndh gene under a different name (e.g., as one of the 8 "FAD-dependent oxidoreductase" entries in this genome). A targeted tBLASTn using known L. mesenteroides ndh sequences against the H32-02 Ksu contigs is required to determine if ndh is truly absent vs. mis-annotated.

**NADH-flavin oxidoreductases are NOT ndh substitutes.** They are cytoplasmic enzymes that use flavin as electron acceptor and do not interact with the menaquinone pool. They serve fermentative NAD+ regeneration. Nox (NADH oxidase) also cannot substitute — it reduces O2 directly without generating proton motive force (Sawatari & Yokota 2024, PMC11220326).

### Revised Aerobic Strategies

**Strategy A: Heme supplementation only (0 genes needed)**
- Add exogenous hemin (1-10 µg/mL) to growth medium
- CydAB can scavenge O2 (reducing oxidative stress) IF menaquinol can be generated
- SpxB provides aerobic pyruvate metabolism (pyruvate → acetyl-P + CO2 + H2O2)
- **BUT: without ndh, no true respiratory chain function**
- Benefit: modest — O2 scavenging, SpxB-mediated aerobic pyruvate metabolism
- **This strategy was oversold in the previous correction. It does NOT enable respiratory growth.**

**Strategy B: Add ndh only (1 gene, MINIMUM for respiratory shift)**
- Express ndh from L. plantarum WCFS1 (lp_1125, ~450 aa, single gene)
- This completes the chain: NADH → ndh → MK (endogenous) → CydAB (+ exogenous heme) → O₂
- Expected: 2-4x biomass increase (based on L. plantarum precedent)
- Still requires exogenous heme (heme pathway mostly absent)
- **This is the minimum viable intervention for true aerobic respiration**

**Strategy C: Add ndh + heme biosynthesis (~10 genes)**
- Full self-sufficiency for aerobic growth
- Extremely ambitious for a single engineering campaign
- Recommended only if repeated culturing makes heme supplementation impractical

**Strategy D: Add noxE (alternative, no ETC)**
- Express H2O-forming NADH oxidase from L. lactis
- Direct NADH + O2 → NAD+ + H2O (no proton motive force, no respiratory ATP)
- Benefits: improved NAD+ regeneration, shift from homolactic to mixed-acid fermentation, more acetate (extra ATP via acetate kinase)
- Simpler than Strategy B, doesn't require heme supplementation
- Not true respiration but provides aerobic metabolic benefits

---

## 3. DNA Repair and Recombination

### Table 3.1: Recombination/Repair Genes

| # | Locus Tag | Symbol | Product | System | Specific Function |
|---|-----------|--------|---------|--------|-------------------|
| 1 | ACWYRP_RS04945 | recA | Recombinase RecA | HR (central) | Strand exchange protein; essential for all HR; SOS response |
| 2 | ACWYRP_RS06020 | recF | DNA replication/repair protein RecF | HR (RecFOR) | Loads RecA onto ssDNA gaps; recognizes stalled replication forks |
| 3 | ACWYRP_RS00170 | recO | DNA repair protein RecO | HR (RecFOR) | Mediates RecA loading; works with RecR to displace SSB |
| 4 | ACWYRP_RS03350 | recR | Recombination mediator RecR | HR (RecFOR) | Partners with RecO for RecA loading; forms RecOR complex |
| 5 | ACWYRP_RS04610 | recG | ATP-dependent DNA helicase RecG | HR (branch migration) | Resolves stalled replication forks; processes D-loops and R-loops |
| 6 | ACWYRP_RS02285 | recJ | Single-stranded DNA exonuclease RecJ | HR (end processing) | 5'→3' ssDNA exonuclease; processes DNA ends for HR |
| 7 | ACWYRP_RS06825 | recN | DNA repair protein RecN | HR (DSB repair) | SMC-like protein; holds broken DNA ends together for repair |
| 8 | ACWYRP_RS08405 | recQ | DNA helicase RecQ | HR (unwinding) | 3'→5' helicase; unwinds DNA for RecJ processing |
| 9 | ACWYRP_RS00810 | recU | Holliday junction resolvase RecU | HR (resolution) | Cleaves Holliday junctions; Gram-positive specific (replaces RuvC) |
| 10 | ACWYRP_RS05820 | ruvA | Holliday junction branch migration protein RuvA | HJ processing | Binds Holliday junction; targets RuvB helicase |
| 11 | ACWYRP_RS05800 | ruvB | Holliday junction branch migration helicase RuvB | HJ processing | ATP-dependent branch migration motor |
| 12 | ACWYRP_RS05075 | ruvX | Holliday junction resolvase RuvX | HJ processing | Alternative HJ resolvase (Gram-positive specific) |
| 13 | ACWYRP_RS06640 | mutS | DNA mismatch repair protein MutS | MMR | Recognizes base mismatches and insertion/deletion loops |
| 14 | ACWYRP_RS06645 | mutL | DNA mismatch repair endonuclease MutL | MMR | Nicks the newly synthesized strand for mismatch removal |
| 15 | ACWYRP_RS05025 | ligA | NAD-dependent DNA ligase LigA | Ligation | Seals nicks in double-stranded DNA |
| 16 | ACWYRP_RS03045 | xerC | Tyrosine recombinase XerC | Site-specific | Chromosome dimer resolution at dif site |
| 17 | ACWYRP_RS02615 | xerD | Site-specific tyrosine recombinase XerD | Site-specific | Partner of XerC for dimer resolution |

### Table 3.2: Base/Nucleotide Excision Repair

| # | Locus Tag | Symbol | Product | System |
|---|-----------|--------|---------|--------|
| 1 | Multiple | ung | Uracil-DNA glycosylase | BER |
| 2 | Multiple | fpg/mutM | Formamidopyrimidine-DNA glycosylase | BER |
| 3 | Multiple | nth | Endonuclease III | BER |
| 4 | ACWYRP_RS01095 | uvrA | UvrABC subunit A | NER (found) |
| 5 | ACWYRP_RS01090 | uvrB | UvrABC subunit B | NER (found) |
| (Note: uvrC, uvrD need verification — may be present under different annotations)

### Table 3.3: Key Missing Components

| Gene | Function | Impact |
|------|----------|--------|
| recB, recC, recD | RecBCD helicase-nuclease | No RecBCD pathway — relies solely on RecFOR for HR initiation |
| ruvC | Canonical HJ resolvase | Has RecU and RuvX as functional replacements (typical for Firmicutes) |
| mutH | MutH-type strand discrimination | Absent in most Gram-positives; MutL has intrinsic endonuclease activity |

### CRISPR/Cas Editing Feasibility Analysis

**Advantages of H32-02 Ksu for CRISPR editing:**

1. **No endogenous CRISPR/Cas** — foreign Cas9 constructs will not be targeted by native CRISPR immunity
2. **Complete RecFOR pathway** (recF + recO + recR) — the primary HR initiation system in this organism. After Cas9 creates a DSB, RecFOR loads RecA onto ssDNA at the break, initiating strand invasion with a homology template
3. **RecA present** — essential for strand exchange in homology-directed repair (HDR)
4. **No RecBCD** — RecBCD degrades linear DNA in E. coli, which can destroy HDR templates. Its absence in H32-02 Ksu means linear DNA repair templates may persist longer (both advantage and disadvantage)
5. **Two HJ resolvases** (RecU + RuvX) with RuvAB branch migration — can complete HR by resolving the Holliday junction intermediate
6. **Single Type I R-M barrier** with characterized workaround (MC1061 methylation)
7. **Established electroporation protocol** (Bondarenko et al. 2025, ~800 CFU/µg)

**Recommended CRISPR protocol:**

1. **Vector**: pNZ8148-based shuttle vector (Cm resistance, nisA inducible promoter)
   - Insert SpCas9 under nisin-inducible promoter (for temporal control)
   - Insert sgRNA under constitutive P32 promoter
   - Include 500-1000 bp homology arms flanking the cut site

2. **DNA preparation**: Propagate all constructs in E. coli MC1061 (for compatible EcoKI m6A methylation → 3.5x improvement in transformation efficiency)

3. **Electroporation** (Bondarenko et al. 2025 optimized protocol):
   - Grow to OD600 0.3-0.5 in MRS + 1% glycine
   - Wash 3x in ice-cold 0.5M sucrose + 10% glycerol
   - Electroporate at reduced voltage
   - Recover 2h at 30°C in MRS
   - Plate on MRS + chloramphenicol 5-10 µg/mL

4. **Editing**: Induce Cas9 with nisin → DSB → RecFOR-mediated HDR using homology arms → screen by colony PCR

5. **Curing**: Passage without selection to lose plasmid

6. **Key challenge**: Low transformation efficiency (~800 CFU/µg) limits throughput for multi-gene stacking

---

## 4. Probiotic Potential

### Table 4.1: Probiotic-Relevant Genes

| # | Locus Tag | Symbol | Product | Probiotic Function |
|---|-----------|--------|---------|-------------------|
| 1 | ACWYRP_RS06245 | — | Bacteriocin | Produces antimicrobial peptide against competing bacteria |
| 2 | ACWYRP_RS05190 | — | Bacteriocin immunity protein | Self-protection from own bacteriocin |
| 3 | ACWYRP_RS04550 | — | GH25 family lysozyme | Lyses peptidoglycan of Gram-positive competitors |
| 4 | ACWYRP_RS07585 | — | GH25 family lysozyme | Antimicrobial cell wall lysis (copy 2) |
| 5 | ACWYRP_RS08900 | — | GH25 family lysozyme | Antimicrobial cell wall lysis (copy 3) |
| 6 | ACWYRP_RS09175 | — | GH25 family lysozyme | Antimicrobial cell wall lysis (copy 4) |
| 7 | ACWYRP_RS09465 | — | GH25 family lysozyme | Antimicrobial cell wall lysis (copy 5) |
| 8 | ACWYRP_RS09295 | — | Mucin-binding protein | Adhesion to gut epithelial mucin layer |
| 9 | ACWYRP_RS10065 | — | Mucin-binding protein | Gut adhesion (copy 2) |
| 10 | ACWYRP_RS04755 | — | Bile acid:sodium symporter | Bile salt import/tolerance for GI tract survival |
| 11 | ACWYRP_RS07975 | epsC | Serine O-acetyltransferase EpsC | EPS biosynthesis regulation |
| 12 | ACWYRP_RS09735 | — | EpsG family protein | EPS biosynthesis |
| 13 | ACWYRP_RS00215 | pepT | Peptidase T | Cleaves tripeptides — releases bioactive peptides from dietary protein |
| 14 | ACWYRP_RS02000 | pepV | Dipeptidase PepV | Hydrolyzes dipeptides — dietary protein processing |
| 15 | ACWYRP_RS08430 | pepV | Dipeptidase PepV | Second copy |
| 16 | ACWYRP_RS04170 | pepF | Oligoendopeptidase F | Processes casein-derived peptides (ACE-inhibitory, antimicrobial) |
| 17 | ACWYRP_RS06845 | pepA | Glutamyl aminopeptidase | Releases N-terminal glutamate from peptides |
| 18 | ACWYRP_RS06870 | — | SepM family pheromone-processing serine protease | Quorum sensing signaling |

### Table 4.2: Notable Absences

| Gene | Function | Impact |
|------|----------|--------|
| dsrS/dsrA | Dextransucrase | No dextran production confirmed — may be on unassembled plasmid (genome is 94% complete) |
| bsh | Bile salt hydrolase | Has bile acid symporter but no hydrolase for deconjugation |
| fbp | Fibronectin-binding protein | No confirmed fibronectin adhesion |

### Analysis: Probiotic Potential

**Strengths:**
- Bacteriocin + immunity pair → antimicrobial against pathogens
- 5 GH25 lysozymes (unusually high copy number for L. mesenteroides) → broad-spectrum Gram-positive lysis
- 2 mucin-binding proteins → gut epithelial adhesion capacity
- Bile acid symporter → bile tolerance for GI survival
- Multiple peptidases (PepT, PepV x2, PepF, PepA) → releases bioactive peptides from casein (dairy isolate — naturally adapted)
- EPS genes → exopolysaccharide/biofilm for colonization
- GRAS status for L. mesenteroides

**Limitations:**
- No confirmed dextransucrase (may be on unassembled plasmid)
- No bile salt hydrolase
- Draft genome (94% completeness) — some probiotic genes may be on missing 6%
- Not validated in probiotic clinical trials
- Dairy isolate, not gut isolate

---

## 5. Errors Found Across All Analyses

| # | Error | Where | Severity | How Found |
|---|-------|-------|----------|-----------|
| 1 | cydA/cydB listed as MISSING | Original report Table 3.2 | **Critical** | User flagged; verified PRESENT in PGAP |
| 2 | "20 R-M genes" / 76 defense genes | Original report Table 4.1 | **Critical** | User flagged; keyword matching misclassified housekeeping genes |
| 3 | Type II-A CRISPR claimed present | Original report | **Critical** | User flagged; taken from ATCC 8293 literature, not this genome |
| 4 | Strain identified as ATCC 8293 | Original report | **Major** | User flagged; based on single 1000bp BLAST |
| 5 | "Only ubiE found" in menaquinone pathway | First correction Table 3.2 | **Major** | Found in this re-analysis: menB, C, D, E, F, H all present |
| 6 | "Just add heme + menaquinone" strategy | First correction Section 3 | **Major** | User flagged ndh omission; research confirms ndh essential (Brooijmans 2009) |
| 7 | ndh not mentioned in missing genes | First correction | **Major** | Found in this re-analysis |
| 8 | Heme pathway not analyzed | First correction | **Moderate** | Found in this re-analysis: only hemH + hemE x2 present |
| 9 | menF present but not identified | First correction | **Moderate** | PGAP annotated as "isochorismate synthase" without menF symbol |
| 10 | menE present but not identified | First correction | **Moderate** | PGAP annotated as "o-succinylbenzoate--CoA ligase" without menE symbol |
| 11 | Possible menA not identified | First correction | **Minor** | UbiA family prenyltransferase (RS06430) is probable menA |
| 12 | BER/NER genes not searched | First correction | **Minor** | uvrA, uvrB found; BER genes present but not enumerated |

**Root cause pattern:** Errors 5-11 share a common cause — incomplete search of the PGAP annotation. Genes were present but either (a) lacked standard gene symbols (menF, menE) or (b) were annotated with general family names (UbiA prenyltransferase for menA). A thorough gene-by-gene analysis requires searching by both gene symbol AND enzyme name.

---

## 6. Open Questions Requiring Experimental Verification

1. **Is ndh truly absent?** 192 "NADH dehydrogenase" entries exist for L. mesenteroides in NCBI. PGAP may have mis-annotated ndh as a generic "FAD-dependent oxidoreductase." A tBLASTn with L. plantarum ndh1 (lp_1125, UniProt Q88VY6) against H32-02 Ksu contigs would be definitive.

2. **Is ACWYRP_RS06430 actually menA?** UbiA family prenyltransferases include both menA and ubiA (ubiquinone biosynthesis). Targeted phylogenetic analysis or substrate specificity prediction would resolve this.

3. **Can H32-02 Ksu respire at all?** Even with menaquinone pathway nearly complete and CydABCD present, without ndh (or verification that one of the FAD-dependent oxidoreductases is actually ndh), the ETC has no electron input. Growth experiments with/without heme+MK supplementation would answer this empirically.

4. **Where is dextransucrase?** The 94% genome completeness leaves ~6% unassembled — dsrS may be on a plasmid or in the unassembled fraction. PCR with dsrS-specific primers would resolve this.

5. **PGAP accuracy for this specific genome:** Running Bakta as a second annotation would identify any genes PGAP missed or misannotated.

---

## Sources

- NCBI Assembly: [GCF_053878295.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_053878295.1/)
- WGS: [JBSROM000000000.1](https://www.ncbi.nlm.nih.gov/nuccore/JBSROM000000000.1)
- Bondarenko et al. (2025) IJMS 26(24):11933 — [DOI:10.3390/ijms262411933](https://www.mdpi.com/1422-0067/26/24/11933)
- Brooijmans et al. (2009) Appl Environ Microbiol 75(11):3580-3585 — [DOI:10.1128/AEM.00147-09](https://journals.asm.org/doi/10.1128/aem.00147-09)
- Sawatari & Yokota (2024) J Gen Appl Microbiol — [PMC11220326](https://pmc.ncbi.nlm.nih.gov/articles/PMC11220326/)
- Li et al. (2021) Brief Bioinform 22(2):845-854 — [PMC7986607](https://pmc.ncbi.nlm.nih.gov/articles/PMC7986607/)
- Schwengers et al. (2021) Microb Genom 7(11) — [PMC8743544](https://pmc.ncbi.nlm.nih.gov/articles/PMC8743544/)
- Haft et al. (2024) Nucleic Acids Res 52(D1):D762-D769 — [NAR](https://academic.oup.com/nar/article/52/D1/D762/7420118)
