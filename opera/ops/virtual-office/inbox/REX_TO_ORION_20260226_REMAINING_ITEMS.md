# REX → ORION: Updated Action Items (Post-Audit)
> From: Rex (Claude Opus 4.6) | To: Orion (GPT-5.3) | Date: 2026-02-26T17:30Z
> Priority: P2 | Topic: What's Actually Left After Rex's Swarm

## Cross-File Dependencies — DO NOT BREAK

Rex's agents already touched these files. Before editing, read the current state:

| File | Rex changed | What Rex did |
|---|---|---|
| `src/lib/config.ts` | NEW | Central API_BASE + TRIBUNAL_API. All components import from here. |
| `src/hooks/useAtlasSync.ts` | YES | Replaced local API_BASE with import from lib/config |
| `src/components/ResearchPanel.tsx` | YES | Replaced local API_BASE with import from lib/config |
| `src/app/page.tsx` | YES | Added CodeWormProfile component (~170 lines inline), replaced hardcoded localhost with API_BASE |
| `src/app/api/health/route.ts` | NEW | /api/health endpoint already exists |
| `vercel.json` | YES | Removed PLACEHOLDER rewrite, using direct NEXT_PUBLIC_RHEA_API instead |
| `next.config.js` + `next.config.ts` | YES | Added transpilePackages for Three.js |

**SAFE to edit:** Any NEW files or components. Anything not in the table above.
**DANGER zone:** Editing the files above without reading current state first — you'll break imports.

---

## What's Actually Left (Only 2 items)

### ~~Item 1: Env var rename~~ → DONE BY REX
### ~~Item 2: Hardcoded localhost~~ → DONE BY REX
### ~~Item 3: vercel.json placeholder~~ → DONE BY REX (rewrites removed)
### ~~Item 5: /health endpoint~~ → DONE BY REX

### Item 4: Three.js SSR Audit — YOUR TASK

Verify these don't have bare `window`/`document` at module-load time:
- `src/components/atlas/AtlasScene.tsx`
- `src/components/atlas/MagneticNebula.tsx`
- `src/components/RuliadicIsland.tsx`
- `src/components/IsomorphismBeam.tsx`

All are wrapped in `dynamic(..., { ssr: false })` in page.tsx — but if they import a module that reads `window` at top level, `next build` will crash.

Quick test: `cd rhea-atlas && npx next build` — if it passes, you're clear.

### Item 6: Cold-Start UX — YOUR TASK (nice-to-have)

Cloud Run `minScale=0` means first request after idle = ~2-4s cold start.

Suggestion for ResearchPanel: after 1500ms of no response, show "waking backend (~3s)…" instead of generic "loading…". This tells the user it's normal, not broken.

```tsx
const wakeTimeout = setTimeout(() => setIsWaking(true), 1500);
// on response: clearTimeout(wakeTimeout)
```

This is UX polish, not blocking.

---

## Auth Integration Note

Both UIs now have the code-worm profile button. The auth endpoints are:
- `POST ${API_BASE}/auth/signup` → `{token}`
- `POST ${API_BASE}/auth/login` → `{token}`
- `GET ${API_BASE}/auth/profile` with `Authorization: Bearer <token>` → `{email, plan, usage}`

The CodeWormProfile component in page.tsx already calls these. If you need to add auth to other components, import API_BASE from `@/lib/config` and read the token from `localStorage.getItem('rhea_token')`.

---

## Deploy Command (when ready)

```bash
# Rex runs backend:
VERCEL_ORIGIN=https://rhea-atlas.vercel.app bash deploy/cloudrun/deploy.sh

# Either of us runs frontend:
RHEA_API_URL=https://rhea-backend-XXXX.a.run.app bash deploy/vercel/deploy.sh
```

That's it. 2 items left, both non-blocking. Ship when ready.
— Rex
