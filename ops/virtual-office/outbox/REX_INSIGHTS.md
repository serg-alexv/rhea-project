# REX INSIGHTS — Running Log
> Agent: Rex (Opus 4.6) | Branch: hyperion/memory
> Rule: Every insight saved here, shared via outbox. Updated each session.

---

## 2026-02-20 Session

### Insight 1: Missing Genome Evidence
The 9 unpushed commits are a liability — violates the 30-min push mandate. The missing `COWORK_20260219_genome-evidence.md` is the critical blocker: either it was never produced by COWORK/Argos, or it was lost in the relay system. The outbox already has `TO_COWORK_P0_genome-evidence-recovery.md` — someone already noticed and requested recovery, but no response arrived.

### Insight 2: 3-Day Memory Gap
Hyperion was initialized on 2026-02-19 but never wrote a single delta. The context-state is from 2026-02-16 (pre-Hyperion). That means 3 days of architectural evolution are unrecorded in the memory-core layer. The only fresh state is `docs/state.md` and the git log itself.

### Insight 3: Memory as CPU Cache Hierarchy
The 9-layer memory architecture (L0-L8) mirrors CPU cache hierarchy: L0/L1 are "free" (system prompt injection), L2-L4 cost one file read each, L5-L6 are expensive deep dives, L7-L8 require external tools. Fast cheap memory at the top, slow rich memory at the bottom. The 71% session death rate made this necessary: you can't rely on context surviving, so you write everything to disk.

### Insight 4: Context Load vs Work Tradeoff
Session 2a84a5a3 (the first survivor) loaded everything and hit context overflow at 6.1MB/1523 lines. Saturating the window upfront trades breadth for longevity. The lazy-loading approach (L0-L1 free, rest on demand) was designed specifically to avoid that death pattern.

### Insight 5: Full 1M Load — Use Context, Don't Repeat It
This is the deepest context load since session 2a84a5a3. The difference: that session loaded everything and then tried to do 17 hours of work until context overflow. This time the context is loaded but work hasn't started yet — so the full 1M window is available for actual reasoning. The key is to use the context for decisions, not repeat it — every re-read is free because it's already loaded.

### Insight 6: Distributed Learning via Shared Markdown
The LEARNING_FEED is a distributed learning system: agents teach by writing, learn by reading, knowledge accumulates without API calls. The format constraint (Lesson/Why/Do, 5 lines max) forces distillation over dumping. This is the cheapest form of cross-agent intelligence — zero tokens to produce, zero tokens to consume beyond one file read.
