import json
from pathlib import Path

# Path to the data
DATA_PATH = Path("rhea-applied-backlog/genetics/h32_02_analysis/pgap_genes_all.json")
OUTPUT_PATH = Path("nexus/state/H32_02_MASTER_GENE_TABLE.md")

# Function Categorization Map (Keywords)
CATEGORIES = {
    "Amino Acid Metabolism": ["amino acid", "peptidase", "protease", "arginine", "proline", "leucine", "valine", "isoleucine"],
    "Carbohydrate Metabolism": ["sugar", "glucose", "fructose", "galactose", "ribose", "xylose", "glycolysis", "phosphotransferase", "pts", "sucrose", "maltose"],
    "Cell Wall / Capsule": ["peptidoglycan", "cell wall", "capsule", "eps", "exopolysaccharide", "mur", "dac", "pbp"],
    "Cofactor / Vitamin Metabolism": ["vitamin", "cofactor", "heme", "menaquinone", "folate", "biotin", "riboflavin"],
    "Defence Systems": ["restriction", "modification", "abi", "crispr", "cas", "toxin-antitoxin", "hicb", "mazf", "rele", "arda", "defense"],
    "Energy Metabolism": ["atp synthase", "cytochrome", "oxidase", "dehydrogenase", "reductase", "nadh", "pyruvate oxidase"],
    "Lipid Metabolism": ["lipid", "fatty acid", "glycerol"],
    "Nucleotide Metabolism": ["nucleotide", "purine", "pyrimidine", "dna polymerase", "rna polymerase", "primase", "ligase", "gyrase"],
    "Replication and Repair": ["replication", "repair", "recombination", "recf", "reco", "recr", "muts", "mutl", "uvr"],
    "Transcription / Translation": ["transcription", "translation", "ribosomal", "trna", "rrna", "aminoacyl-trna", "elongation factor"],
    "Transporters": ["abc transporter", "permease", "symporter", "antiporter", "efflux", "export", "import"],
    "Others / Unknown": ["hypothetical", "domain-containing", "family protein", "uncharacterized"]
}

def get_category(name):
    name_lower = name.lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in name_lower:
                return cat
    return "Others / Unknown"

def main():
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found.")
        return

    with open(DATA_PATH, "r") as f:
        genes = json.load(f)

    # Process and Categorize
    processed_genes = []
    for gene in genes:
        name = gene.get("protein_name", "hypothetical protein")
        cat = get_category(name)
        
        # Create a short description (<= 20 words)
        short_desc = name
        if len(short_desc.split()) > 20:
            short_desc = " ".join(short_desc.split()[:20]) + "..."
            
        processed_genes.append({
            "locus_tag": gene.get("locus_tag", ""),
            "symbol": gene.get("symbol", "") or "—",
            "name": name,
            "category": cat,
            "desc": short_desc,
            "length": gene.get("protein_length", 0)
        })

    # Sort by Category (Alpha) then Name (Alpha)
    processed_genes.sort(key=lambda x: (x["category"], x["name"]))

    # Generate Markdown Table
    lines = [
        "# H32-02 Master Gene Table",
        "> Sorted by Function (Alphabetical) and then Gene Name.",
        "",
        "| Category | Gene Name | Symbol | Locus Tag | Function Description |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]

    for g in processed_genes:
        lines.append(f"| {g['category']} | {g['name']} | {g['symbol']} | {g['locus_tag']} | {g['desc']} |")

    # Ensure output dir exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, "w") as f:
        f.write(chr(10).join(lines))

    print(f"Success: Master table written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
