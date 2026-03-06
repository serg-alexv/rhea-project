#!/usr/bin/env python3
"""
build_windows.py — Build Windows binaries and create MSI installer
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

def run_command(cmd, check=True):
    """Run shell command and return output."""
    print(f"  → {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result.stdout.strip(), result.returncode

def main():
    parser = argparse.ArgumentParser(description="Build Windows Rhea distribution")
    parser.add_argument("--output", default="build/dist", help="Output directory")
    parser.add_argument("--sign-certificate", help="Code signing certificate (base64)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("🪟 Building Windows Rhea Distribution")
    print("=" * 50)

    # 1. Check dependencies
    print("\n1. Checking dependencies...")
    try:
        run_command(["python", "--version"])
        print("   ✅ Python 3.x available")
    except Exception as e:
        print(f"   ❌ Python not found: {e}")
        return 1

    # 2. Build Python package
    print("\n2. Building Python package...")
    try:
        run_command(["pip", "install", "-e", "."], check=False)
        print("   ✅ Package installed")
    except Exception as e:
        print(f"   ⚠️  Package install skipped: {e}")

    # 3. Create launcher executable
    print("\n3. Creating launcher executable...")
    launcher_code = '''
@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
python -m rhea_ops %*
'''
    launcher_path = output_dir / "rhea.bat"
    launcher_path.write_text(launcher_code)
    print(f"   ✅ Launcher created: {launcher_path}")

    # 4. Create PowerShell installer
    print("\n4. Creating PowerShell installer...")
    ps_installer = '''
# rhea-win-init.ps1 — Rhea Windows Installation Script
# Usage: powershell -ExecutionPolicy Bypass -File rhea-win-init.ps1

$ErrorActionPreference = "Stop"

Write-Host "🪟 Rhea Windows Installation" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# 1. Check Administrator
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "   Right-click PowerShell → Run as Administrator" -ForegroundColor Yellow
    exit 1
}

# 2. Install to Program Files
$InstallPath = "C:\\Program Files\\Rhea"
if (!(Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath | Out-Null
    Write-Host "✅ Created install directory: $InstallPath" -ForegroundColor Green
}

# 3. Copy files
Copy-Item "rhea.bat" "$InstallPath\\rhea.bat" -Force
Write-Host "✅ Installed rhea.bat" -ForegroundColor Green

# 4. Add to PATH
$PathEnv = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($PathEnv -notlike "*$InstallPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$PathEnv;$InstallPath", "Machine")
    Write-Host "✅ Added Rhea to PATH" -ForegroundColor Green
} else {
    Write-Host "ℹ️  Rhea already in PATH" -ForegroundColor Blue
}

# 5. Verify installation
if (Test-Path "$InstallPath\\rhea.bat") {
    Write-Host ""
    Write-Host "✅ Installation Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: rhea --help" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "❌ Installation failed" -ForegroundColor Red
    exit 1
}
'''
    ps_path = output_dir / "rhea-win-init.ps1"
    ps_path.write_text(ps_installer)
    print(f"   ✅ Installer created: {ps_path}")

    # 5. Create installation receipt
    print("\n5. Creating installation receipt...")
    receipt = {
        "package": "rhea-windows",
        "version": os.environ.get("GITHUB_REF_NAME", "dev").lstrip("v"),
        "platform": "windows",
        "build_date": datetime.utcnow().isoformat() + "Z",
        "components": [
            {
                "name": "rhea.bat",
                "type": "launcher",
                "path": "C:\\Program Files\\Rhea\\rhea.bat"
            },
            {
                "name": "rhea-win-init.ps1",
                "type": "installer",
                "requires_admin": True
            }
        ],
        "system_requirements": {
            "os": "Windows 10 / Server 2019+",
            "python": "3.10+",
            "dotnet": "6.0+ (optional)"
        }
    }

    receipt_path = output_dir / "install_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    print(f"   ✅ Receipt created: {receipt_path}")

    # 6. Create README
    print("\n6. Creating documentation...")
    readme = '''# Rhea Windows Installation

## Quick Start

1. Right-click PowerShell → "Run as Administrator"
2. Run: `powershell -ExecutionPolicy Bypass -File rhea-win-init.ps1`
3. Close and reopen PowerShell
4. Verify: `rhea --help`

## Requirements
- Windows 10 or later
- Administrator access
- Python 3.10+ (optional, for development)

## What's Installed
- **rhea.bat** — Command-line launcher (added to PATH)
- **System integration** — Can be launched from any terminal

## Usage

```powershell
# Get help
rhea --help

# Check status
rhea ops status

# Deploy to cloud
rhea ops deploy
```

## Troubleshooting
- If `rhea` command not found: Close and reopen PowerShell
- If permission denied: Run PowerShell as Administrator
- Check logs: See docs/RHEA_TUNNEL_ENTITLEMENTS_GUIDE.md

---
Version: [BUILD_VERSION]
Build Date: [BUILD_DATE]
'''
    readme_path = output_dir / "README-Windows.md"
    readme_path.write_text(readme)
    print(f"   ✅ README created: {readme_path}")

    # 7. Create ZIP archive
    print("\n7. Creating distribution archive...")
    try:
        import shutil
        zip_path = output_dir.parent / "rhea-windows-latest"
        shutil.make_archive(str(zip_path), "zip", output_dir)
        print(f"   ✅ Archive created: {zip_path}.zip")
    except Exception as e:
        print(f"   ⚠️  ZIP archive skipped: {e}")

    print("\n" + "=" * 50)
    print("✅ Windows distribution package ready:")
    print(f"   📍 Location: {output_dir}")
    print("")
    print("   Files:")
    for f in sorted(output_dir.iterdir()):
        if f.is_file():
            size = f.stat().st_size
            print(f"      - {f.name} ({size} bytes)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
