<p align="center">
  <img src="docs/readme/rhea-hero.svg" alt="Rhea — Proof Before Birth" width="100%" />
</p>

<h1 align="center">RHEA / ῬΕΑ</h1>
<p align="center"><strong>Intelligence is everywhere. Authority is the scarce resource.</strong></p>
<p align="center"><em>Make every crossing of that boundary explain itself.</em></p>

<p align="center">
  <a href="https://github.com/timelabs-npo/rhea-project/tree/rhea-project-v2">Active architecture</a> ·
  <a href="src/tribunal_api.py">Tribunal source</a> ·
  <a href="apparatus/nexus/">Nexus</a> ·
  <a href="https://blueshoes.space/rhea/">Family map</a>
</p>

Rhea is a multi-model research stack and an architecture project for systems that must justify their next state. The ambition is to make powerful reasoning available without handing its confidence the keys to everything else.

**Here today:** `main` contains the earlier Tribunal/API stack, coordination tools and application experiments. The separate **v2 workstream is `DESIGN_ONLY`**: eight stages, 55 gates `NOT_EXECUTED`, only Stage 01 contract preparation admitted. That status is pinned to [the assembly record at `accc8619`](https://github.com/timelabs-npo/rhea-project/blob/accc8619b179539c3a775844f5f077fbad80715e/v2/ASSEMBLY.json).

## One tap. Several owners.

Imagine asking from your phone: **“Save this result, then move my connection to the other path.”**

The model understands the sentence. The phone shows a button. But the storage owner must decide whether those bytes may become a revision; the network owner must decide whether that route may change. Either effect can fail while the other succeeds.

A single green tick would conceal the interesting part.

Rhea's target architecture gives each effect its own admission, execution and evidence. The screen should be able to say: **saved; route unresolved**. Honest partial progress is more useful than a fictional success.

```text
                        a person's request
                                │
                      interface / model advice
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
          storage admission             network admission
                 │                             │
          byte publication              bounded route effect
                 │                             │
          storage receipt               network receipt
```

This is the intended authority structure, not a diagram of an already qualified integration.

## Topology is who can reach the switch

**Topology** describes connections: which person, process or peer can reach which operation. A thousand helpful agents behind one unrestricted credential still leave one enormous point of control.

**Geometry** adds a chosen way to compare possibilities. Two paths to a result may differ in time, cost, evidence quality or reversibility. Those dimensions help expose tradeoffs; they do not collapse into one universal “truth score.” A cheaper answer cannot buy permission to erase a file.

**Flow** is what actually moves through the connections: questions, attention, bytes, proposals and admitted effects. A queue can starve a good idea. A hidden intermediary can tax every request. A stale memory can keep sending work toward a door that has closed.

That is the quiet power of flows: **control the crossings and you shape what can happen, even without owning what moves.** Rhea wants those crossings visible, contestable and bounded.

> **Мысль может течь свободно. Полномочия должны иметь границы.**

## The instruments on the bench

| Component | Concrete entrance | What it contributes |
|---|---|---|
| **Tribunal** | [API](src/tribunal_api.py), [provider bridge](src/rhea_bridge.py), [consensus analysis](src/consensus_analyzer.py) | Multiple model responses, disagreement and research workflows. Agreement is an observation, not a proof. |
| **Nexus** | [Profiles, schemas and checklists](apparatus/nexus/), [profile validator](apparatus/nexus/scripts/validate_profile.py) | Coordination and continuity apparatus inherited from the earlier stack. It is not the qualified v2 host. |
| **Aletheia** | [Pipeline](src/aletheia_pipeline.py), [hypotheses and proof records](friends/aletheia/) | Research into turning assertions into inspectable questions, checks and evidence. A record under `proofs/` still needs its own grounds. |
| **Ruliad / Ruliada** | [Explorer](friends/ruliad/explorer/), [research references](friends/ruliad/references/) | A lens for exploring possible states and different formal descriptions. The metaphor does not make this an implemented universal geometry or Ricci-flow engine. |
| **Memory** | [Local package](packages/rhea-memory/), [standalone project](https://github.com/timelabs-npo/rhea-memory) | Facts, timeline and compact context across sessions. Remembering a statement does not make it current. |
| **Presentation** | [Atlas](rhea-atlas/), [native experiments](ios/RheaPreview.swiftpm/), [Play](play/) | Ways to inspect and interact with the research stack. A compelling picture cannot certify the event behind it. |

These are source and research entrances. Legacy API routes also include mutation and supervisor operations; their presence does not establish the isolation required by v2.

## Eight stages. No royal shortcut.

The new workstream starts with **OMNIA-LIT-001**: a deliberately narrow contract for publishing owned immutable bytes. Content identities, conditional publication, retries and recovery must agree before higher layers depend on them.

| Stage | Responsibility | Required evidence |
|---|---|---|
| **01 · Contracts** | identities, boundaries, public vectors | reviewed contract freeze |
| **02 · Validation** | independent encoders, oracles, fault injection | oracle readiness |
| **03 · Omnia LIT** | local immutable-byte publication | publication and recovery qualification |
| **04 · Local host** | identity, admission, private access | bounded service and denial behavior |
| **05 · Rhea Play** | native presentation | honest end-to-end state |
| **06 · Advisory runtime** | isolated model and research workers | execution and non-authorizing isolation |
| **07 · Network executor** | privileged, fixed network operations | actual effects and recovery |
| **08 · Remote bridge** | authenticated cross-node composition | independent composition evidence |

At the pinned snapshot, **Stages 02–08 remain locked** and runtime enforcement is unimplemented. The missing `OMNIA-LIT-001_HANDOFF.md` and `OMNIA-LIT-001_ACCEPTANCE.json` still block contract freeze. A draft specification cannot substitute for them.

Begin with the [Stage 01 handoff](https://github.com/timelabs-npo/rhea-project/blob/accc8619b179539c3a775844f5f077fbad80715e/v2/START_HERE.md), [acceptance gates](https://github.com/timelabs-npo/rhea-project/blob/accc8619b179539c3a775844f5f077fbad80715e/v2/01_contracts/ACCEPTANCE_GATES.md) and [technical index](https://github.com/timelabs-npo/rhea-project/blob/accc8619b179539c3a775844f5f077fbad80715e/v2/docs/INDEX.md). Follow the [active branch](https://github.com/timelabs-npo/rhea-project/tree/rhea-project-v2) for subsequent changes.

## Enter through evidence

For the existing stack, start with the source links above and the [Tribunal tests](tests/test_tribunal_e2e.py), [adversarial tests](tests/test_adversarial.py) and [pipeline tests](tests/test_pipeline_e2e.py). Read each test's dependencies before execution; these files are not a report of a fresh passing run.

Earlier setup and product context remain in the [frozen baseline README](https://github.com/timelabs-npo/rhea-project/blob/75cb31e59ccc4f436a428811cb70bbc495254821/README.md). Its services, credentials and local paths require current verification. New v2 work begins inside its admitted stage, without starting legacy services as an implied prerequisite.

## A family of boundaries

| Neighbor | Place in the intended system |
|---|---|
| [Rheknel](https://github.com/timelabs-npo/rheknel) | research into a small deterministic admission boundary |
| [Omnia Playbook](https://github.com/timelabs-npo/omnia-playbook) | operational invariants, baselines and diagnostics |
| [Omnia Vault](https://github.com/timelabs-npo/omnia-vault) | state, revision and causal-preservation research |
| [Blueshoes](https://github.com/timelabs-npo/Blueshoes) | network-flow observation and bounded mutation research |
| [MBSD](https://github.com/timelabs-npo/mbsd) | the operating substrate and its physical qualification problem |

Their names describe responsibilities, not an already integrated runtime. A proposal is not a capability; admission is not execution; one owner's receipt cannot certify another owner's effect.

Rhea's old myth supplies one useful image: a future that survives an authority determined to swallow it. The engineering owes that future something firmer than mythology.

[MIT license](LICENSE) · Timelabs NPO · [Protocol and family](https://blueshoes.space/rhea/)

---

<p align="center"><strong>MAKE POWER EXPLAIN ITS PATH.</strong></p>
