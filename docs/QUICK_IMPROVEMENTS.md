# Quick Improvements — Rhea Atlas Audit
> Generated 2026-02-26 by Cowork session. Applied fixes marked with ✅.

## ✅ APPLIED

1. **Zustand import fix** — `useAtlasStore.ts`: `import create` → `import { create }` (deprecated in v4+)
2. **API_BASE extracted to env** — `useAtlasSync.ts` + `ResearchPanel.tsx`: hardcoded `localhost:8000` → `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`
3. **animate-ping → animate-pulse** — `page.tsx`: Redis status dot no longer infinite-pings (GPU saver)

## 🔧 REMAINING (for Rex)

### Frontend (rhea-atlas)

4. **PANEL_Z global mutable let** (`page.tsx` line ~19): `let PANEL_Z = 30` mutates via `++PANEL_Z`. Survives ok but resets on HMR. Consider `useRef` or store.

5. **API key hardcoded** (`ResearchPanel.tsx` line 59):
   ```ts
   'X-API-Key': 'dev-bypass'
   ```
   Move to `process.env.NEXT_PUBLIC_TRIBUNAL_KEY || 'dev-bypass'`

6. **Only 1 IsomorphismBeam** between 3 islands. Add 2 more for full graph:
   ```tsx
   <IsomorphismBeam start={...island2} end={...island3} color="#00ffff" speed={0.5} />
   <IsomorphismBeam start={...island1} end={...island3} color="#00ffff" speed={0.5} />
   ```

7. **MeshDistortMaterial segments** — `RuliadicIsland.tsx` uses `args={[1, 64, 64]}`. If adding more islands, drop to `[1, 32, 32]` — visually identical, 4x fewer polys.

8. **CrossNav hardcoded localhost link** (`page.tsx` line ~48):
   ```tsx
   href="http://localhost:8000/app"
   ```
   Use `API_BASE` env var.

### Backend

9. **CORS wildcard** (`tribunal_api.py` line 53): `allow_origins=["*"]` — restrict for prod deployment.

10. **Session history in-memory only** (`tribunal_api.py` line 68): `_session_history` resets on process restart. Persist to Redis or Firestore.

11. **Redis cache silent fail** (`rhea_bridge.py` lines 37-43): When `REDIS_URL` not set, cache silently disabled. Add explicit status to `/health` endpoint.

### Dependencies

12. **Next.js 14.0.4 → 14.2+**: Security patches + Turbopack improvements.
    ```bash
    cd rhea-atlas && npm update next
    ```

13. **Three.js 0.162 → 0.170+**: Geometry dispose fixes + WebGPU groundwork.
    ```bash
    cd rhea-atlas && npm update three @react-three/fiber @react-three/drei
    ```

### Repo hygiene

14. **firebase-debug.log** (612KB) already in `.gitignore` but file exists in working tree. Run:
    ```bash
    git rm --cached firebase-debug.log
    ```

15. **Duplicate entries in .gitignore** — `logs/`, `firebase-debug.log`, `gemini/`, `.watcher/`, `.idea/` appear twice. Deduplicate.

16. **`.env` appears twice** in `.gitignore` — harmless but messy.

## Priority order
| # | Fix | Time | Impact |
|---|-----|------|--------|
| 5 | API key to env | 1 min | Security |
| 9 | CORS restrict | 1 min | Security |
| 14 | git rm cached log | 10 sec | Repo clean |
| 6 | Add 2 more beams | 2 min | Visual completeness |
| 12-13 | Update deps | 5 min | Security + perf |
| 10 | Persist session history | 15 min | Data durability |
