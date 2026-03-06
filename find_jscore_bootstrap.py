import sys
import os

# Add Binary Ninja API to path
bn_python_path = "/Applications/Binary Ninja.app/Contents/Resources/python"
if bn_python_path not in sys.path:
    sys.path.append(bn_python_path)

import binaryninja as bn

def analyze_bndb(bndb_path):
    print(f"Opening {bndb_path}...")
    # Use load() or open_view() for BNDB files
    bv = bn.load(bndb_path)
    if bv is None:
        print("Failed to open BNDB")
        return

    search_strings = ["evaluateScript:", "JSCoreScripts", "app.js"]
    candidates = []

    for s in search_strings:
        print(f"Searching for '{s}'...")
        # Find all strings matching the search
        found_strings = [str_obj for str_obj in bv.strings if s in str_obj.value]
        
        for found_str in found_strings:
            xrefs = bv.get_code_refs(found_str.start)
            for xref in xrefs:
                func = xref.function
                if func:
                    # Collect rationale
                    calls_nearby = []
                    # Check next few instructions in HLIL for readable calls
                    try:
                        instr_hlil = func.get_hlil_at(xref.address)
                        if instr_hlil:
                            # Search forward in the same block
                            block = instr_hlil.il_basic_block
                            for i in range(instr_hlil.instr_index, min(instr_hlil.instr_index + 10, len(func.hlil))):
                                instr = func.hlil[i]
                                if instr.operation == bn.HighLevelILOperation.HLIL_CALL:
                                    calls_nearby.append(str(instr.dest))
                    except:
                        pass
                    
                    candidates.append({
                        "address": hex(func.start),
                        "func_name": func.name,
                        "string": s,
                        "rationale": f"Contains '{s}'. Calls nearby: {', '.join(calls_nearby[:3])}"
                    })

    # Sort and pick top candidates (unique functions)
    unique_candidates = {}
    for c in candidates:
        if c["address"] not in unique_candidates:
            unique_candidates[c["address"]] = c
    
    sorted_candidates = list(unique_candidates.values())[:5]
    
    print("\n--- Top 5 Candidate Bootstrap Functions ---")
    if not sorted_candidates:
        print("No candidates found.")
    for i, c in enumerate(sorted_candidates, 1):
        print(f"{i}. Address: {c['address']} | Name: {c['func_name']}")
        print(f"   Rationale: {c['rationale']}\n")

if __name__ == "__main__":
    bndb = os.path.expanduser("~/rh.1/Play.bndb")
    analyze_bndb(bndb)
    bn.shutdown()
