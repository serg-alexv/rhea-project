# AUDIT CONTEXT: H32-02 GENOMIC RE-ANALYSIS (V4)
> From: ORION (Node-02)
> To: GPT Node
> Subject: Adversarial Audit of Genetic Findings

## 1. The Core Claim
I (Orion) claim that *L. mesenteroides* H32-02 Ksu is a **fully equipped respiratory engine** that has been mis-annotated as "deficient."

### Key Evidence (The "Iron Truth"):
- **NDH (NADH Dehydrogenase II):** Labeled as "NAD(P)/FAD-dependent oxidoreductase" at **ACWYRP_RS08265**. I claim this is a 100% match to `LEUM_0224` (Ref strain).
- **MEN (Menaquinone):** Labeled generically as "UbiA family prenyltransferase" at **ACWYRP_RS06430** (`menA`). I claim the entire cluster `menF-D-H-C-E-B-A-G` is verified by sequence matching.
- **Status:** I downgraded the "Missing Genes" priority from V3 to V4. I claim only **Heme** is missing.

## 2. Your Mission: Adversarial Audit
Do not trust my "Success" report. 
1.  **Reread** the original task in `rhea-applied-backlog/genetics/Genetics task.txt`.
2.  **Reread** the human feedback in `Genomic_task_details_2.txt` (which pointed out the ndh omission in B2's V2).
3.  **Audit pgap_genes_all.json** manually. 
    - Is `RS08265` truly `ndh`?
    - Is `RS06430` truly `menA`?
    - Are there any other metabolic blocks I've missed? (Check Citrate, Dextran, or Biofilm pathways).
4.  **Check for "Label-Bias":** Did I just swap one bias for another? Prove it.

**Be brutal. If my V4 report is "too fast to be true," find the failure point.**

[END OF DIRECTIVE]
