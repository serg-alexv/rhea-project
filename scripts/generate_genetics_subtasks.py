import json
from pathlib import Path

DATA_PATH = Path("rhea-applied-backlog/genetics/h32_02_analysis/pgap_genes_all.json")
OUTPUT_DIR = Path("nexus/state/")

# Defined Sub-Tasks
TASKS = {
    "Aerobic_Metabolism": {
        "present": ["cytochrome", "cyd", "atp synthase", "pyruvate oxidase", "spxb", "superoxide dismutase", "catalase", "peroxidase"],
        "missing_crucial": [
            ("ndh", "NADH:quinone oxidoreductase (Type II)", "Primary entry point for electrons into the ETC."),
            ("menaquinone biosynthesis (menA-G)", "Menaquinone biosynthesis pathway", "Essential electron carrier in the membrane."),
            ("heme biosynthesis (hemA-L)", "Heme biosynthesis pathway", "Essential cofactor for cytochrome bd oxidase function.")
        ]
    },
    "Defence_Systems": {
        "present": ["restriction", "modification", "hsd", "abi", "toxin-antitoxin", "hic", "maz", "rel", "arda"],
        "missing": ["crispr", "cas", "type II restriction", "type III restriction"]
    },
    "Repair_and_Recombination": {
        "present": ["recf", "reco", "recr", "reca", "uvr", "muts", "mutl", "gyrase", "ligase", "polA"],
        "missing": ["recbcd", "addab"] # Common in some but maybe not all LAB
    },
    "Probiotic_Potential": {
        "present": ["bacteriocin", "immunity", "mucin-binding", "bile acid", "peptidase", "lysozyme", "eps"],
        "missing": ["dextransucrase", "dsrs"]
    }
}

def main():
    with open(DATA_PATH, "r") as f:
        genes = json.load(f)

    for task_name, criteria in TASKS.items():
        present_genes = []
        for gene in genes:
            name = gene.get("protein_name", "").lower()
            symbol = gene.get("symbol", "").lower()
            match = False
            for kw in criteria["present"]:
                if kw in name or kw in symbol:
                    match = True
                    break
            if match:
                present_genes.append(gene)

        # Generate Table
        output_file = OUTPUT_DIR / f"H32_02_{task_name}.md"
        lines = [f"# H32-02 {task_name.replace('_', ' ')} Analysis", ""]
        
        lines.append("## Present Genes")
        lines.append("| Locus Tag | Symbol | Product | Function |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for g in present_genes:
            lines.append(f"| {g['locus_tag']} | {g['symbol'] or '—'} | {g['protein_name']} | {g['protein_name'][:50]} |")
        
        if "missing_crucial" in criteria:
            lines.append("\n## Missing Genes (Ranged by Cruciality)")
            lines.append("| Gene/Pathway | Name | Function | Priority |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for i, (gene, name, func) in enumerate(criteria["missing_crucial"]):
                lines.append(f"| {gene} | {name} | {func} | {i+1} (Highest) |")
        elif "missing" in criteria:
            lines.append("\n## Missing Components")
            for m in criteria["missing"]:
                lines.append(f"- {m}")

        with open(output_file, "w") as f:
            f.write("\n".join(lines))
        print(f"Generated {output_file}")

if __name__ == "__main__":
    main()
