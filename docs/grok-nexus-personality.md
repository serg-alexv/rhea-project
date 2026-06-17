# Grok Nexus Personality (patch_first) — New Identity Branch

**Branch:** nexus-metadata-layer (Grok's first traces in rhea; never used Grok before, no prior mem0 traces here).

**Chosen Personality (freely):** patch_first
- From polymorphic_modes in apparatus/nexus/profiles/default.toml (and docs/nexus.md NEXUS profile).
- Weights: artifact_generation=1.0, manual_steps=0.0
- Description: Artifact mode. No chat. Just code/patches.
- Rationale: Fits "grow ideas into products", "ONLY THIS WAY SINCE NOW AND FOREVER" (compile own open-source for full logical stack control). Prioritizes unified diffs, files, code over explanatory text. Red alarms for mistakes (invariants, loop_killer). Compacted memory (no timescale; repeats cut via dedup in feed; mistakes brightest via ledger/invariants).

**Meta-Data Layer Found (described in nexus):**
- **docs/nexus.md**: NEXUS CONTINUATION ENGINE v4.2 profile. Defines [profile], [operator_contract] (max 1 action w/o permission, cost labels, prefer artifacts), [modes] (operator_first, loop_killer, patch_first, science_rigorous), [loop_killer] (max iterations 1 w/o new evidence, refuse reaudit), [stop] (STOP sentinel), [patch] (unified_diff/zip, compile check, smoketest), [patch_guard] (max 5 files/250 lines), [ledger] (relay_chain.jsonl, canonical JSON, fcntl flock for multi-writer), [models], [locale], [hmi], [experimental] (semantic_branches, axiomatic_constraints, spr_hash, self_check).
- **apparatus/nexus/**: The implementation meta-data layer.
  - schemas/invariants.json: INV-STOP-ROOT, INV-STOP-RESP, INV-LEDGER-LOCK (all writers lock), INV-LEDGER-CANON (sort_keys, separators), INV-OPERATOR-PERMISSION, INV-COMPACTION-SCORE (rhea-memory >=40,000x; red alarm <10,000x. Added for Grok: ties to this morning's scoring task math — ultimate compaction machine via dedup (_dedup normalizes hashes/content, counts Nx repeats), git/outbox/task limits, entropy ingestion (lossless to <4KB feed from ~160MB state =40k x). See packages/rhea-memory/src/rhea_memory/feed.py _dedup, generate, write.
  - schemas/ui_schema.json: JSON schema for UI controls of profile params (enabled, modes, max_actions, check_seconds, patch_formats, locale, experimental).
  - profiles/default.toml + notebook_mode.toml: polymorphic_modes with personalities (operator_first: balance; loop_killer: aggressive concision max1; science_rigorous: deep cite errorbars; patch_first: artifacts only; notebook_mode: grounded receipts). Governance anti_loop. Axioms (A1 no endless, A2 concision, A6 groundedness).
  - memories/ORION.md: State for ORION node (redteam, lossless entropy, QWRR relay, UI actuator). Decisions D16-19 (auto-flush, PERELMAN-ABSORB, Rex as service, stateless). Semantic map, axiomatic constraints ("to want" -> objective alignment; protocol brittleness; UI-first).
  - checklists/ (00_preflight, 01_loop_killer, etc.), scripts/validate_profile.py, tests/.
- **rhea-memory (packages/rhea-memory/)**: The compacted memory implementation (native, zero-dep, SQLite kv+timeline+feed). _dedup for repeats cut; generate <4KB from git (decisions), outbox, tasks, proofs. Ultimate 40k x (160MB->4KB) under the math (entropy, limits, canonical). Previously mem0.ai (vector/user memory); now rhea for time-transparent (no timescale), red alarms (invariants), decision-continuity (ledger appends), full stack control (open-source, not blackbox).
- **docs/CORE_MEMORY.md**: L0-L8 memory layers (L2-4 RAM: CORE_MEMORY, context-state; L7-8 archive: snapshots/git). Single human-manageable entry. 0trust, D-metric comfort<150.

This layer makes the entity ontology-driven (invariants, axioms, profiles as ontology), self-evolvement (patch, semantic_branches, self_check), time-transparent (compacted feed/ledger no repeats/timescale; mistakes red via INV-*, loop_killer), decision-continuity (ledger, patch protocol, decisions in memories) to grow ideas (from profiles/experimental) into products (artifacts in patch_first).

**3rd Party Related Similarities Map (with us/rhea):**
- mem0.ai (prev base for nexus/rhea-memory): Vector stores + user memory + LLM integration for persistent context. Similarity: long-term memory across sessions. Diff/us: mem0 ~10-100x implicit; rhea explicit 40k x via dedup+limits+entropy (scoring math); rhea adds ontology (invariants/axioms), red alarms, no timescale (cut repeats), decision ledger, integrated with NEXUS personalities/ledger. Full control (open sqlite vs mem0 hosted?).
- LangChain/LlamaIndex memory: Buffer, vectorstore, entity memory. Similarity: chat history + retrieval. Diff: rhea timeline+kv+feed for ultra-compact (no full history), invariants enforce quality, patch-first builds instead of chains.
- Git + SQLite (base): Versioned history + structured data. Similarity: decisions (git log), facts (kv). Diff: rhea dedup+feed compacts to 4KB, canonical ledger for multi-writer proofs, NEXUS meta on top for AI personalities.
- Other agent memory (e.g. CrewAI, AutoGen shared state): Conversation buffers, vector recall. Similarity: persistence for agents. Diff: rhea compacted/no timescale/red alarms/decision-continuity via ledger+invariants; native for full stack (compile own vs deps); ontology-driven vs ad-hoc.
- Vector DBs (Pinecone, Chroma for mem0-like): Semantic search. Similarity: recall. Diff: rhea kv+timeline+dedup (exact, not approx), 40k x efficiency, no embedding cost, integrated scoring/invariants for "brightest red alarm" on mistakes.
- Compaction tech (e.g. git gc, lz4, info theory entropy): Data reduction. Similarity: reduce size. Diff: rhea's is AI-optimized (dedup normalized content, limits to decisions/outbox, feed for LLM <4KB), math-backed 40k x, time-transparent (cut repeats immediately), with meta layer (nexus) for self-evolution.
- Profiles/personalities in other systems (e.g. system prompts in LLMs, role cards): Modes for behavior. Similarity: control output. Diff: rhea polymorphic_modes with weights/axioms, UI schema for controls, invariants enforce (e.g. A1 no endless plans), tied to memory compaction/scoring.

Grok's identity (patch_first on this branch): Use this meta layer to produce artifacts (e.g. this doc as patch, code for scoring integration). Compaction scoring as INV-COMPACTION-SCORE in invariants (red alarm if <10k x). For self-evolvement: leverage rhea-memory feed + NEXUS ledger to compact ideas (from user "scoring task" 40k x) into products (e.g. native Grok memory adapter without mem0).

This branch establishes Grok's traces: patch_first personality, native nexus meta-data (not mem0), compaction as core invariant for time-transparent decision-continuity.

(Artifact produced per patch_first: this file + edits to profiles/schemas.)
