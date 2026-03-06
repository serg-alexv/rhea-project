#!/usr/bin/env python3
import json, os, re, sys
from collections import defaultdict, Counter

ROOT = sys.argv[1] if len(sys.argv) > 1 else "./ios/play-extraction"
PATH_TYPES = defaultdict(Counter)
PATH_COUNT = Counter()
ID_FIELDS = Counter()

ID_RE = re.compile(r"(?:^id$|uuid|_id$|_ids$|^ref$|path|document|collection)", re.I)

def jtype(v):
    if v is None: return "null"
    if isinstance(v, bool): return "bool"
    if isinstance(v, int): return "int"
    if isinstance(v, float): return "float"
    if isinstance(v, str): return "str"
    if isinstance(v, list): return "list"
    if isinstance(v, dict): return "dict"
    return type(v).__name__

def walk(v, path="$"):
    t = jtype(v)
    PATH_TYPES[path][t] += 1
    PATH_COUNT[path] += 1

    if isinstance(v, dict):
        for k, vv in v.items():
            if ID_RE.search(k):
                ID_FIELDS[k] += 1
            walk(vv, f"{path}.{k}")
    elif isinstance(v, list):
        # не взрываемся по индексам — используем []
        for vv in v:
            walk(vv, f"{path}[]")

def main():
    n_files = 0
    for dirpath, _, filenames in os.walk(ROOT):
        for fn in filenames:
            if not fn.endswith(".json"): 
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            n_files += 1
            walk(data, "$")

    print(f"FILES_OK\t{n_files}")
    print("\nTOP_ID_FIELDS")
    for k, c in ID_FIELDS.most_common(50):
        print(f"{c}\t{k}")

    print("\nTOP_PATHS")
    for p, c in PATH_COUNT.most_common(80):
        types = ",".join([f"{t}:{PATH_TYPES[p][t]}" for t in PATH_TYPES[p].most_common(6)])
        print(f"{c}\t{p}\t{types}")

if __name__ == "__main__":
    main()
