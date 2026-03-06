import os
import json
import re
from pathlib import Path

# Heuristic: strings that look like JSON objects with at least 5 colons
JSON_LIKE_PATTERN = re.compile(r'\{[^{}]*:[^{}]*:[^{}]*:[^{}]*:[^{}]*\}')

def extract_blobs(file_path):
    try:
        content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
        matches = JSON_LIKE_PATTERN.findall(content)
        valid_blobs = []
        for m in matches:
            try:
                # Attempt to normalize common JS object shorthand
                # This is a very rough heuristic
                blob = json.loads(m)
                if isinstance(blob, dict) and len(blob) > 2:
                    valid_blobs.append(blob)
            except:
                continue
        return valid_blobs
    except Exception as e:
        return []

def main():
    base_dir = Path("docs/restore")
    out_dir = Path("artifacts/extracted_json_blobs")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    js_files = list(base_dir.glob("**/*.js*"))
    print(f"Processing {len(js_files)} JS/JSON files...")
    
    for js in js_files:
        blobs = extract_blobs(js)
        if blobs:
            safe_name = str(js).replace("/", "_").replace(".", "_") + ".json"
            (out_dir / safe_name).write_text(json.dumps(blobs, indent=2))

if __name__ == "__main__":
    main()
