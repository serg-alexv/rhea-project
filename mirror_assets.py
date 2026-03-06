import os
import json
import hashlib
import threading
import urllib.request
import urllib.parse
import ssl
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

URL_FILE = "ios/play-extraction/urls/all_firebase_urls.txt"
MIRROR_DIR = Path("mirror/firebase_storage")
MANIFEST_FILE = "mirror/manifest.jsonl"

# Create an unverified SSL context to bypass certificate issues
ssl_context = ssl._create_unverified_context()

def get_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_asset(url):
    url = url.strip()
    if not url:
        return None
    
    try:
        parsed_url = urllib.parse.urlparse(url)
        path_part = parsed_url.path.split('/o/')[-1]
        decoded_path = urllib.parse.unquote(path_part)
        
        local_path = MIRROR_DIR / decoded_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        http_code = 0
        size = 0
        sha256 = ""
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            # Pass the unverified context here
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                http_code = response.getcode()
                data = response.read()
                size = len(data)
                with open(local_path, "wb") as f:
                    f.write(data)
                sha256 = get_sha256(local_path)
        except urllib.error.HTTPError as e:
            http_code = e.code
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            http_code = -1

        entry = {
            "url": url,
            "local_path": str(local_path),
            "sha256": sha256,
            "size": size,
            "http_code": http_code
        }
        
        with manifest_lock:
            with open(MANIFEST_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        
        return http_code
    except Exception as e:
        print(f"General error for {url}: {e}")
        return -1

manifest_lock = threading.Lock()

def main():
    MIRROR_DIR.mkdir(parents=True, exist_ok=True)
    # Clear manifest if exists
    with open(MANIFEST_FILE, "w") as f:
        pass
        
    with open(URL_FILE, "r") as f:
        urls = f.readlines()
    
    print(f"🚀 Starting mirror of {len(urls)} assets (SSL disabled)...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(download_asset, urls))
    
    success = sum(1 for r in results if r == 200)
    print(f"✅ Finished. Success: {success}/{len(urls)}")

if __name__ == "__main__":
    main()
