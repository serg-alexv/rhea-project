import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rhea_langcache import RheaLangCache

def verify():
    print("Initializing RheaLangCache...")
    with RheaLangCache() as rl:
        if not rl.cache:
            print("FAILED: Cache not initialized (check API key)")
            return

        print("Testing SET operation...")
        prompt = "Verification test " + os.urandom(4).hex()
        response = "Verified ok"
        res = rl.set(prompt, response)
        print(f"SET Result: {res}")

        print("Testing SEARCH operation...")
        matches = rl.search(prompt)
        print(f"SEARCH Result: {matches}")
        
        if matches:
            print("SUCCESS: LangCache is functional.")
        else:
            print("FAILED: Search returned no results.")

if __name__ == "__main__":
    verify()
