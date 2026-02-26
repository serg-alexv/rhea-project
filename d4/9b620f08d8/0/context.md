# Session Context

**Session ID:** 261278d3-25c3-4789-93e7-bfcc23c40cd5

**Commit Message:** I'd loke to have a local copy of the whole aletheia -- and using it tota

## Prompt

i'd loke to have a local copy of the whole aletheia -- and using it totally freely -- isnt this obvy?

## Summary

Full pipeline works. Submit → classify (0.88 = "proof" tier) → markdown written to `friends/aletheia/proofs/chronobiology/` → stored in `proof.db` → verification healthy.

`★ Insight ─────────────────────────────────────`
**Dual-persistence pattern**: The proof library has two complementary storage layers. SQLite (`proof.db`) gives you fast queries, search, aggregation, chains — the engine. Markdown files (`friends/aletheia/`) give you human-readable, git-diffable, browseable copies — the archive. Neither replaces the other. The DB can be rebuilt from markdown if lost; the markdown is regenerated from DB on each capture. This is the "local-first" pattern — zero cloud dependency, your data, your machine.
`─────────────────────────────────────────────────`

Your Aletheia library is fully local and free to use:

```
# CLI
python3 src/aletheia_pipeline.py stats          # library overview
python3 src/aletheia_pipeline.py search "cortisol"  # keyword search
python3 src/aletheia_pipeline.py recent          # latest proofs
python3 src/aletheia_pipeline.py export          # dump to JSON
python3 src/aletheia_pipeline.py verify          # DB ↔ files check

# API (when rhead is running on :8000)
GET  /aletheia/stats
GET  /aletheia/proofs
GET  /aletheia/proofs/{id}
GET  /aletheia/search?q=keyword
POST /aletheia/submit          # manual entry
POST /aletheia/verify

# Browse directly
ls friends/aletheia/proofs/     # by ontology folders
ls friends/aletheia/hypotheses/
```

## Key Actions

- - **Bash**: Check current friends/aletheia structure
- - **Grep**: friends/aletheia|ALETHEIA_ROOT
- - **Bash**: Test Aletheia CLI
- - **Bash**: Seed test proof through full pipeline
- - **Read**: /Users/sa/rh.1/friends/aletheia/proofs/chronobiology/0650a31a247b77e6a719f701.md
