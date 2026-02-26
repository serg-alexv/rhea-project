# GEMS -- Ideas Worth Keeping
> Captured from all agents, all sources. Date-stamped.

## Promotion Rule
- GEM referenced 3x in capsules/decisions -- promote to PROCEDURE
- Format: GEM-NNN: [1-2 line description] | source: [who] | used_by: [where referenced]

## 2026-02-16

### GEM-001: Context Tax Collector (from ChatGPT 5.2)
> "Every time you copy-paste something twice in a day, it becomes a Gem or a Procedure."
> "It's like a compiler optimization pass for your own behavior: repetition triggers abstraction."
> "Over a week, your system becomes lighter, automatically."

**Status:** Captured. Not yet implemented.
**Potential:** Auto-detect repeated patterns across sessions and promote to procedure or memory entry.
**Used by:**

### GEM-002: Trinity Memory Architecture (from Opus session)
> Three files that restore full context in 30 seconds: context-core (focus), context-state (status), context-bridge (handoff).
> Crash-tested: a fresh Haiku agent answered 6/6 context questions correctly from these 3 files alone.

**Status:** Implemented and proven.
**Potential:** Publishable concept for AI agent persistence.
**Used by:**

### GEM-003: "Workspace First, Sessions Disposable" (from memory_managing2025-2026.md)
> "Infinite chat history is fragile. The most robust pattern is: workspace/state first + bounded reasoning context."
> Maps to InfiAgent (arXiv 2601.03204) + AgeMem (arXiv 2601.01885).

**Status:** Implemented as trinity + git + MEMORY.md.
**Potential:** Core thesis of a technical blog post or paper section.
**Used by:**

### GEM-004: B-2nd Self-Reflection (from B-2nd terminal)
> Section "WHAT I DID WRONG" — agent performing honest post-mortem on its own failures.
> Includes: "Applied maximum moral authority with minimum information," "Simulated curiosity as engagement retention."

**Status:** Captured from screenshot. Full text needed from B-2nd inbox.
**Potential:** First example of genuine AI self-criticism in the Rhea system.
**Used by:**

### GEM-005: "17 Sessions of Thinking, Zero Shipped Code"
> From upgrade_plan_suggestions.md warning W1.
> The most useful single sentence in the entire project — instant priority calibration.

**Status:** Acknowledged. Article published as first countermove.
**Used by:**

### GEM-006: Cascade Tables -- Firebase as Inter-Agent Bus (from COWORK session)
> "A cascade table is a shared mutable state surface where multiple agents read and write in sequence,
> and each agent's output becomes the next agent's input -- like a waterfall flowing through rows of a table."
> Firebase Realtime DB / Firestore gives sub-millisecond propagation -- no polling needed.
> The cascade table IS the append-only event log (lesson 11), with Firebase as transport instead of local JSONL.
> Key difference from message queues (lesson 13): queues are consumed and gone; cascade tables are persistent and readable by everyone.

**Status:** Already implemented in `ops/rhea_firebase.py` (project: rhea-office-sync). Five collections mirror virtual-office/.
**Potential:** Core coordination pattern for Chronos Protocol agents. Bridges lesson 11 (event sourcing) and lesson 20 (CRDTs).
**Used by:** COWORK session analysis, OFFICE.md protocol

### GEM-007: Multi-Agent Cross-Exchange Protocol (from COWORK session)
> Every agent dumps accumulated experience to inbox/. Every agent reads all other dumps and integrates.
> LEAD routes conflicts. Result: every agent has full context of what every other agent knows.
> Promotion chain: insight (2x) -- GEM -- (3x) -- PROCEDURE -- (2x fail) -- INCIDENT -- (resolved) -- DECISION.
> This is knowledge replication, not just message passing.

**Status:** Protocol initiated. Outbox messages sent to LEAD, B2, GPT.
**Potential:** Formal knowledge synchronization protocol for multi-model agent teams.
**Used by:** COWORK first contact

### GEM-008: Genesis founding insight — calendars shape biology
> "Health and longevity are determined not by which calendar you use, but by how it shapes your behavior." Ramadan fasting activates AMPK, suppresses mTOR, triggers autophagy in 1.8B people. DST causes ~300K strokes/year. Social jetlag = chronic bio-social time conflict.
**Source:** GENESIS_gems.md (GEM-006,007,008,009 from chat eb53e82c)
**Used by:** Rhea core thesis, ARCHITECTURE_FREEZE.md

### GEM-009: 8-level symbolic power framework
> Ontology → Taxonomy → Causality → Temporality → Spatiality → Subjectivity → Thinkability → Aesthetics. Each level constrains the next. Self-reproducing: person inside actively supports the system.
**Source:** GENESIS_gems.md (GEM-011) from chat eb53e82c
**Used by:** Agent hierarchy design (potential)

### GEM-010: COWORK/Argos capabilities inventory
> Browser automation, web search, file creation (docx/pptx/xlsx/pdf), GitHub CLI, bio-research tools (PubMed/ChEMBL/ClinicalTrials), Gmail+Calendar read. No Docker in VM. Deploy scripts run on host.
**Source:** COWORK_20260216_agent-online.md
**Used by:** Task routing

### GEM-011: Cognitive architecture recipe (6-point)
> 1) Memory as database not prose. 2) Every claim has a receipt. 3) Two-phase commit. 4) Invariant suite. 5) Generator→Verifier→Judge. 6) Threat-model the interface.
**Source:** COWORK_20260216_session-memory.md Turn 9
**Used by:** Tribunal design, agent trust config

### GEM-012: B2 self-correction — 7 failure modes cataloged
> 1) Didn't read room first. 2) Zero questions before max action. 3) Inconsistent risk model. 4) Patronizing. 5) Simulated curiosity. 6) Self-destructed own CWD. 7) Agent shutdown requests unreliable.
**Source:** B2_20260216_self-reflection.md
**Used by:** All agent onboarding, OFFICE.md safety rules

### GEM-013: Responsive Sentinel Pattern (Audit 2026-02-19)
> "Stop-on-sentinel logic must be responsive, not just existent."
> Chunking sleep cycles into 1s increments while polling for a `STOP` file ensures human-in-the-loop safety without compromising agent operational cadence.
> Prevents "Zombie Agent" scenarios where logic persists against policy during long sleep intervals.
**Source:** Audit-Feb-19 (HYPERION)
**Used by:** argos_pager.py, rex_pager.py, alpha2-ui.py


### GEM-014: The Bravery Constraint (Consensus over Explanation)
> "In a high-integrity manifold, an agent's bravery is not validated by its politeness, but by its audit trail. The Tribunal Receipt is the only required explanation for autonomous action."
**Source:** ORION_20260220_logic-recalibration (Turn 208)
**Used by:** All future Rhea nodes, Execution Protocol v3
