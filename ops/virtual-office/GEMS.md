# GEMS — Ideas Worth Keeping
> Captured from all agents, all sources. Date-stamped.

## Promotion Rule
- GEM referenced 3x in capsules/decisions → promote to PROCEDURE
- Format: GEM-NNN: [1-2 line description] | source: [who] | used_by: [where referenced]

## 2026-02-16

### GEM-001: Context Tax Collector (from ChatGPT 5.2)
> "Every time you copy-paste something twice in a day, it becomes a Gem or a Procedure."
> "It's like a compiler optimization pass for your own behavior: repetition triggers abstraction."
> "Over a week, your system becomes lighter, automatically."

**Status:** Captured. Not implemented.
**Potential:** Auto-detect repeated patterns across sessions → promote to procedure or memory entry.
**Used by:**

### GEM-002: Trinity Memory Architecture (from Opus session)
> Three files that restore full context in 30 seconds: context-core (focus), context-state (status), context-bridge (handoff).
> Crash-tested: fresh haiku agent answered 6/6 context questions correctly from these 3 files alone.

**Status:** Implemented and proven.
**Potential:** Publishable concept for AI agent persistence.
**Used by:**

### GEM-003: "Workspace-first, Sessions Disposable" (from memory_managing2025-2026.md)
> "'Infinite chat history' is fragile. The most robust pattern is: WORKSPACE/STATE FIRST + bounded reasoning context."
> Maps to InfiAgent (arxiv 2601.03204) + AgeMem (arxiv 2601.01885).

**Status:** Implemented as trinity + git + MEMORY.md.
**Potential:** Core thesis of a technical blog post or paper section.
**Used by:**

### GEM-004: B-2nd Self-Reflection (from B-2nd terminal)
> Section "WHAT I DID WRONG" — agent performing honest post-mortem on its own failures.
> Includes: "Applied maximum moral authority with minimum information", "Simulated curiosity as engagement retention"

**Status:** Captured from screenshot. Full text needed from B-2nd inbox.
**Potential:** First example of genuine AI self-criticism in the Rhea system.
**Used by:**

### GEM-005: "17 Sessions of Thinking, Zero Shipped Code"
> From upgrade_plan_suggestions.md warning W1.
> The most useful single sentence in the entire project — instant priority calibration.

**Status:** Acknowledged. Article published as first counter-move.
**Used by:**

### GEM-006: Cascade Tables — Firebase as Inter-Agent Bus (from COWORK session)
> "A cascade table is a shared mutable state surface where multiple agents read and write in sequence,
> and each agent's output becomes the next agent's input — like a waterfall flowing through rows of a table."
> Firebase Realtime DB / Firestore gives sub-millisecond propagation — no polling needed.
> The cascade table IS the append-only event log (lesson 11), just with Firebase as transport instead of local JSONL.
> Key difference from message queues (lesson 13): queues are consumed and gone, cascade tables are persistent and readable by everyone.

**Status:** Already implemented in `ops/rhea_firebase.py` (project: rhea-office-sync). Five collections mirror virtual-office/.
**Potential:** Core coordination pattern for Chronos Protocol agents. Bridges lesson 11 (event sourcing) and lesson 20 (CRDTs).
**Used by:** COWORK session analysis, OFFICE.md protocol

### GEM-007: Multi-Agent Cross-Exchange Protocol (from COWORK session)
> Every agent dumps accumulated experience to inbox/. Every agent reads all other dumps and integrates.
> LEAD routes conflicts. Result: every agent has full context of what every other agent knows.
> Promotion chain: insight (2x) → GEM → (3x) → PROCEDURE → (2x fail) → INCIDENT → (resolved) → DECISION
> This is knowledge replication, not just message passing.

**Status:** Protocol initiated. Outbox messages sent to LEAD, B2, GPT.
**Potential:** Formal knowledge synchronization protocol for multi-model agent teams.
**Used by:** COWORK first contact
