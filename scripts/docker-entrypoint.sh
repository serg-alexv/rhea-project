#!/bin/bash
# Rhea Docker entrypoint — Tailscale mesh + seed proof.db + start server

# Start Tailscale daemon in background (if auth key is set)
if [ -n "$TAILSCALE_AUTHKEY" ]; then
    tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &
    sleep 2
    tailscale up --authkey="$TAILSCALE_AUTHKEY" --hostname=rhea-tribunal
    echo "[tailscale] joined tailnet as rhea-tribunal"
fi

SEED_COUNT=$(python3 -c "
import sqlite3, sys
try:
    c = sqlite3.connect('/app/data/proof.db')
    print(c.execute('SELECT COUNT(*) FROM proofs').fetchone()[0])
except Exception:
    print(0)
" 2>/dev/null)

if [ "$SEED_COUNT" -lt 5 ]; then
    cp /tmp/seed_proof.db /app/data/proof.db
    echo "[seed] proof.db seeded ($SEED_COUNT -> 11 artifacts)"
fi

exec uvicorn tribunal_api:app --host 0.0.0.0 --port 8400 --workers 2
