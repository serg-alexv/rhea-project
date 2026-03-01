#!/usr/bin/env bash
# Tribunal API daemon — launched by launchd
set -euo pipefail
cd /Users/sa/rh.1

# Source environment
[ -f .env ] && set -a && source .env && set +a

exec python3 -u -c "
import sys; sys.path.insert(0, 'src')
import uvicorn
from tribunal_api import app
uvicorn.run(app, host='0.0.0.0', port=8400, log_level='info')
"
