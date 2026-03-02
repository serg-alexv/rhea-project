#!/bin/bash
# Rhea Docker entrypoint — seed proof.db if volume is empty, then start server

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

exec python3 src/tribunal_api.py
