DECISION MEMO — Agentic chatflow w/ multi-month context + controllable external memory

Core takeaway:
- “Infinite chat history” is fragile. The most robust pattern in 2026 is:
  WORKSPACE/STATE FIRST (files, snapshots, artifacts) + bounded reasoning context,
  with memory as explicit operations and strict gating on when to recall.

What to build (recommended blueprint):
1) Workspace-first state (InfiAgent pattern)
   - Persist EVERYTHING important as files/objects:
     /goals, /plans, /decisions, /tasks, /artifacts, /logs, /profiles
   - Each step: load workspace index + the few relevant files + last N actions.
   - Version everything (git-like). Make “memory edits” diffable + revertible.
   Link: https://arxiv.org/abs/2601.03204

2) Memory as tool-actions (AgeMem pattern, even without RL)
   - Expose explicit ops: STORE / RETRIEVE / UPDATE / SUMMARIZE / DISCARD
   - Require the agent to log “why” for each memory op (auditability).
   Link: https://arxiv.org/abs/2601.01885

3) Safety + relevance gating (PersistBench lesson)
   - Add a gate: “should LTM be used in this turn?” + domain tags.
   - Block cross-domain recall by default; allow only with explicit justification.
   Link: https://arxiv.org/abs/2602.01146

4) Long-input handling beyond context windows (RLMs option)
   - For huge logs/docs: procedural scanning + recursive calls instead of stuffing context.
   Link: https://arxiv.org/abs/2512.24601

5) Prevent summary-loss (Revisitable Memory)
   - Keep pointers to sources; allow “revisit/callback” when uncertain or conflicting.
   Link: https://arxiv.org/abs/2509.23040

6) Upgrade path for “relationship-heavy” memory: graphs
   - Add memory graph (entities/decisions/dependencies) when projects interlock.
   - Use graph retrieval/rerank for causal chains and multi-hop dependencies.
   AriGraph: https://www.ijcai.org/proceedings/2025/0002.pdf
   REMem:   https://openreview.net/forum?id=fugnQxbvMm

Decision guide (pick based on your constraints):
- If you want MAX stability over months: Workspace-first (InfiAgent) + strict gating.
- If you want MAX autonomy: add memory tool-actions (AgeMem-style) + audit logs.
- If you have dense dependency webs: add memory graphs (AriGraph/REMem).
- If your “context” is mostly huge documents/logs: add RLM-style recursive scanning.
- If you fear memory corruption: enforce diffable memory + confidence/source fields + revert.

Reading list (no fluff, highest signal):
- AgeMem (policy-integrated memory ops): https://arxiv.org/abs/2601.01885
- InfiAgent (file-centric infinite horizon): https://arxiv.org/abs/2601.03204
- PersistBench (when memory should be forgotten): https://arxiv.org/abs/2602.01146
- RLMs (arbitrarily long prompt via recursion): https://arxiv.org/abs/2512.24601
- ReMemR1 / Revisitable Memory: https://arxiv.org/abs/2509.23040
- AriGraph (memory graph + planning): https://www.ijcai.org/proceedings/2025/0002.pdf
- REMem (episodic memory graph retrieval): https://openreview.net/forum?id=fugnQxbvMm
- MIRIX (modular multi-agent memory system): https://arxiv.org/abs/2507.07957

Bottom-line recommendation:
Build Workspace-first + gated retrieval as the default.
Then add (a) memory tool-actions for controllability, (b) revisitable pointers for fidelity,
and (c) a graph layer only when inter-project dependencies start to bite.