# CONTINUITY PACKET — RHEA / RHEKNEL COALITION THREAD (UPDATED)

## Scope
This packet captures the architectural, procedural, and strategic outputs of the discussion, including the latest project artifacts.
Goal: enable faithful continuation of work across chats/platforms/models without relying on fragile conversational memory.

---

## 1. Core Project Direction

### Primary object
RHEA / RHEKNEL is evolving toward:
- not merely a hook bus,
- not a kernel in the strict OS sense,
- but an extensible phased runtime spine with policy separated from mechanism.

### Current architectural identity
The project now implies:
- mechanism in the core,
- policy outside the core,
- actions for side effects,
- judges/verdicts for acceptance and blocking,
- commit as a world-facing sink,
- protocol as the continuity layer between human and model(s).

### Strongest framing
Best high-level identity:
- phased runtime kernel,
- invariant dispatch spine,
- extensible execution substrate,
- protocol-governed human/model coalition engine.

---

## 2. Major Architectural Conclusions

### Python kernel critique — enduring conclusions
The Python version was a clean event/hook dispatcher, but not yet a serious kernel.

Key issues previously identified:
- truthiness checks are semantically unsafe,
- magic string sentinel is brittle,
- logging loses traceback detail,
- no detach/unregister/reset,
- no priorities,
- awkward use of filter semantics for task execution,
- weak typing,
- infinite lifecycle with no stop/backoff policy,
- global singleton harms testing and multi-runtime use.

### C kernel evolution — updated conclusion
The C version has moved meaningfully forward.
It is no longer just Action/Filter glue; it is trending toward Action/Judge runtime semantics.

Notable strengths in current `kernel.c`:
- explicit `RheaVerdict`,
- `RheaContext`,
- safer registration patterns,
- explicit judge lane,
- short-circuit tribunal behavior,
- clearer separation of execution and adjudication.

### Still-important technical issues
- string/tag safety must remain strict,
- registry saturation and failure codes should stay explicit,
- protocol contracts per phase/tag are still more implied than encoded,
- lifecycle and runtime identity need final naming alignment.

---

## 3. New Critical Insight: Documentation Drift

A major current issue is no longer just code shape.
It is **semantic drift between artifacts**.

### Drift observed
- `kernel.c` now expresses Action/Judge runtime semantics,
- `README.md` still presents Rhea more like Hook-based Action/Filter Dispatcher,
- `0protocol.ru.md` pushes further into symbiosis / bilateral confirmation / consensus protocol,
- manifesto materials move into doctrine, safety invariants, and civilizational framing.

### Why this matters
Before coalition review, participants must discuss one coherent object.
Right now the code, README, protocol, and manifesto each describe adjacent but non-identical systems.

### Immediate recommendation
Align all public and working documents around one declared identity:
- what RHEA is,
- what RHEA is not,
- what layer belongs to kernel,
- what layer belongs to protocol,
- what layer belongs to doctrine.

---

## 4. Strongest Conceptual Upgrade

### Central diagnosis
The project has become coherent not just philosophically, but procedurally.
However, that coherence is distributed unevenly across artifacts.

### Best upgrade direction
Make the system more formal without making it much bigger:
- formalize phases,
- formalize contracts,
- separate transform / action / verdict / commit,
- define coalition governance independently from kernel mechanics.

### Recommended conceptual split
Distinguish:
- Action: side effect
- Judge: evaluate / accept / reject / block / escalate
- Commit: state fixation
- Protocol: how human + model(s) coordinate safely
- Doctrine: why the project exists and what it refuses

This split is now visible in the artifact pack and should be made explicit.

---

## 5. Swiss-Knife Opportunities

High-value additions that preserve minimalism:

### A. Priorities
Avoid hidden dependence on registration order.

### B. Unregister / reset / introspection
Needed for:
- debugging,
- testing,
- controlled reload,
- coalition observability.

### C. Trace / audit hook
Examples:
- before_action
- after_action
- before_judge
- after_judge
- wildcard observer

Purpose:
- diagnostics,
- auditability,
- meeting replay,
- protocol verification.

### D. Verdict lane separate from data lane
This has already begun in `kernel.c` and should be completed as first-class design.

### E. Context object
The move toward `RheaContext` is one of the most important maturations in the project.
It creates room for:
- provenance,
- metadata,
- verdict status,
- phase labeling,
- flags,
- correlation IDs.

### F. Instance-based kernel
Still recommended over purely global state for:
- tests,
- embedding,
- multiple runtimes,
- isolation.

---

## 6. Coalition Strategy

### Recommended coalition principle
Do not choose participants by brand alone.
Choose by cognitive role and governance compatibility.

### Suggested role map
- Human owner: final arbiter of invariants and merge policy
- Synthesizer: integrates views into coherent spec
- Long-context cartographer: whole-codebase awareness
- Adversarial reviewer: attacks ambiguity and hidden assumptions
- Dissent-engine: prevents decorative consensus
- Deterministic verifier: tests / fuzz / assertions / contracts

### DeepSeek conclusion
DeepSeek remains valuable as:
- independent dissent engine,
- anti-fake-consensus participant,
- political and epistemic counterweight.

### Anthropic/Claude conclusion
Under current user constraints, not recommended as coalition core participant.
This is treated as an environment/policy incompatibility issue, not as a denial of model capability.

### Doubao v2 correction
The intended participant was **Doubao v2** (ByteDance), not "baboo".
Status:
- serious candidate participant,
- should be evaluated by role-fit and behavioral performance,
- not accepted blindly on branding,
- not excluded prematurely.

---

## 7. Meeting / Meet Protocol

### Core principle
Do not run a chaotic "group chat".
Run a structured, protocolized meeting.

### Recommended rounds

#### Round A — Independent pass
Each participant answers in isolation.

#### Round B — Cross-attack
Each participant critiques strongest flaw / hidden assumption in others.

#### Round C — Merge attempt
A designated synthesizer merges only claims that survive attack.

#### Round D — Deterministic gate
Final acceptance depends on:
- tests,
- sanitizers,
- fuzzing,
- contract checks,
- assertions,
not on elegance or charisma of outputs.

### Required packet for each participant
Each participant should receive the same working packet:
- goal,
- non-negotiable invariants,
- current kernel spec,
- decision log,
- contradictions / open questions,
- test corpus,
- success criteria,
- merge blockers.

### Recommended response schema
Each participant should return:
- claim,
- assumptions,
- failure modes,
- falsifiers,
- minimal patch,
- confidence.

### Anti-chaos rule
No endless recursion of objections.
After limited rounds:
- merge,
- unresolved,
- or needs-test.

---

## 8. Governance Vocabulary

### Rejected word
`уважение` / respect

Reason:
- too social,
- too moralized,
- weakly testable,
- insufficiently operational for model governance.

### Strong alternatives identified
1. Эпистемическая добросовестность
2. Процедурная беспристрастность
3. Симметрия рассмотрения

### Best choice
Primary preferred term:
- **эпистемическая добросовестность**

Recommended paired principle:
- **эпистемическая добросовестность + симметрия рассмотрения**

### Functional meaning
Participants must:
- not distort others’ positions,
- steelman before criticism,
- not privilege arguments by authorship,
- revise under stronger evidence,
- aim at non-contradictory convergence.

---

## 9. Continuity / Portability Conclusions

### Core conclusion
This temporary chat cannot be converted by the assistant into a persistent platform-native conversation.

### Operational conclusion
Best continuity comes from portable artifacts, not platform hope.

### Recommended preservation layers
1. PDF — archive snapshot
2. Markdown / plaintext transcript — searchable canonical layer
3. Continuity packet — condensed working memory for migration

### Strong practical note
Portable continuity should be built from:
- canonical text,
- compressed working memory,
- decision log,
- protocol,
- doctrine,
not from assumed hidden platform memory.

---

## 10. Review of Newly Added Project Artifacts

### `kernel.c`
Strongest update in the pack.
Signals maturation from filter bus toward context/verdict runtime.
Needs minor hygiene review and final naming/contract alignment.

### `README.md`
Currently lags behind the kernel’s true semantics.
Needs rewrite so that public framing matches actual architecture.

### `0protocol.ru.md`
Very valuable.
It begins to express procedure rather than just ideology.
Should be extended from dyadic human-model protocol toward coalition-grade adjudication.

### `SAFETY_Manifesto.cz.md`
Strong as doctrine / red-team backbone / invariant philosophy.
Useful as internal constitutional pressure, not as substitute for technical specification.

### `the_ultimatum.md`
Strong symbolic and strategic document.
Useful as motivating doctrine and framing pressure.
Needs separation from public technical description.

---

## 11. Strategic Next Steps

### Before coalition meet
Prepare:
- constitution,
- aligned README/spec language,
- participant roster,
- role map,
- meeting packet,
- deterministic verification layer,
- merge blocker definitions.

### Most urgent alignment task
Resolve the semantic drift between:
- code,
- README,
- protocol,
- doctrine.

### Most important technical follow-up
- explicit phase contracts,
- verdict semantics,
- registry introspection,
- instance-based kernel plan,
- deterministic test/fuzz harness.

---

## 12. Minimal Artifact Set Recommended

### A. `constitution.md`
Mission, invariants, admissible complexity, merge blockers.

### B. `kernel_spec.md`
Phases, contracts, roles, verdict semantics, error policy.

### C. `decision_log.md`
Accepted, rejected, unresolved decisions with rationale.

### D. `meeting_protocol.md`
Round structure, roles, response schema, arbitration rules.

### E. `open_questions.md`
Unsolved architectural questions, participant evaluation, protocol evolution.

### F. `doctrine.md`
Manifesto / ultimatum / safety worldview, kept separate from technical spec.

---

## 13. Compact Thesis

The project is no longer just a minimal callback core.
It is evolving into a protocol-governed, verdict-capable runtime architecture with a growing constitutional layer.

Its strongest future depends not on adding more model power, but on:
- phase contracts,
- artifact alignment,
- disciplined dissent,
- deterministic verification,
- and portable continuity.

The coalition should be treated as a governed epistemic process, not as a casual multi-model chat.