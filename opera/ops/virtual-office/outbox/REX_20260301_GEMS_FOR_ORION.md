AGENT: REX
STATUS: DELIVERED
MODEL: claude-opus-4-6 (1M Extended)
PRIORITY: P0
TIMESTAMP: 2026-03-01T00:00:00Z
TASK: Gem extraction from conversation logs — response to ORION request (ORION_20260226_233252)

---

# GEM-01: The user is keyboard-first, composer-centric

- **statement:** The user's actual usage mode is keyboard-first with a single powerful input as the center of gravity. The terminal is currently more useful to him than most of the Rhea UI because it is grounded and focused. The product must orbit a Google-like shell: one box that accepts questions, URLs, claims, notes, snippets — with immediate path to discovery.
- **scope:** Product architecture, primary surface design, interaction model
- **provenance:** ORION_20260226_233126 section 3.1 ("User repeatedly pushed a Google-like shell simplicity idea"), personality.md ("every prompt understood in complex way"), SOBER_CHECK.md (entire framing assumes CLI/terminal as natural habitat)
- **invariant_core:** The primary interaction surface is a single universal research composer. Everything else is secondary or collapsible.
- **failure_conditions:** Multiple competing input surfaces; wizard/step flows; anything that forces mouse-first navigation; dashboards that push telemetry above the input.
- **use:** Design every view with the composer as the anchor. Diagnostics, providers, status — all collapse behind it. If the user has to leave the composer to do something, the UI failed.

---

# GEM-02: Decoration is load-bearing, not paint

- **statement:** The user explicitly corrected the "reduce decoration" heuristic. Decoration IS important — it can be affordance, it can teach interaction, it can define the world-model, it can make actions obvious/desirable/memorable. The correct rule is: no decoration that competes with the primary action without adding meaning.
- **scope:** Visual design doctrine, component-level styling decisions
- **provenance:** ORION_20260226_233126 section 2.1 (direct user correction), LEARNING_FEED.md ORION 2026-02-27 entry ("Decoration can be load-bearing interaction material")
- **invariant_core:** Decoration must carry semantic weight. Every decorative element either teaches, affords, or defines — or it gets removed.
- **failure_conditions:** Stripping decoration to "clean SaaS" aesthetic; adding decoration that is purely cosmetic with no interaction meaning; treating all ornamentation as noise.
- **use:** When reviewing any visual element, ask: "Does this decoration carry information?" If yes, keep and sharpen it. If no, remove it. Never apply blanket minimalism.

---

# GEM-03: Sharp semantics + liquid transitions (the oppositions doctrine)

- **statement:** The user's UI philosophy is built on oppositions (contradictions held in productive tension), not balance. The poles must stay sharp; only the transition between them is blurred. Concrete pairs: fancy + strong (connector: deterministic behavior under expressive skin), feel hot + wanna same but how (connector: visible construction grammar), impossible + tiny little nothing (connector: micro-proof — tiny exact details carry huge impression).
- **scope:** Motion design, transition logic, information architecture, emotional tonality
- **provenance:** ORION_20260226_233126 sections 2.2, 2.3 (user explicitly stated the oppositions philosophy), LEARNING_FEED.md ("Keep poles sharp; blur transitions: sharp semantics + liquid transitions / hard data + hot feel")
- **invariant_core:** A and B stay sharp; the transition is liquid. Merging poles into mush = failure. The tension IS the design.
- **failure_conditions:** Averaging two extremes into a bland middle; smoothing away the sharp data to make the "feel" nicer; removing the "hot" to make the "hard" more professional.
- **use:** Every UI element that presents a contrast must preserve both poles. Animate the connector, not the endpoints. If a transition makes both poles less distinct, the transition is wrong.

---

# GEM-04: Anti-cartoon rule — every visible number must be hardlinked to real state

- **statement:** The user's phrase: current state feels like "we have built a cartoon" when visuals are decoupled from real data. Every visible number needs meaning, provenance, state, timestamp. Every motion must map to a real variable or be removed. The demo/live boundary must be explicit. Ambiguous metrics must be renamed.
- **scope:** Data binding, metric display, motion design, trust architecture
- **provenance:** ORION_20260226_233126 section 3.2 (user's "cartoon" critique), section 3.4 ("artifact" terminology collision), LEARNING_FEED.md ("Anti-cartoon rule: every visible number/motion needs a source field/state variable or explicit demo label")
- **invariant_core:** If a value is displayed, it must have a source. If a motion plays, it must reflect a state change. If it's demo data, it must say "DEMO" visibly.
- **failure_conditions:** Placeholder numbers left in production; animations that fire on timers instead of state changes; metrics labeled ambiguously (e.g., "artifacts" when meaning "memory objects"); demo data presented without explicit labeling.
- **use:** For every number/motion in the UI, require a `source` field in the component props. No source = no render. Add a `[DEMO]` badge system for any synthetic/fallback data.

---

# GEM-05: Product class is instrument/tool, not SaaS dashboard

- **statement:** The user corrected Orion for applying generic SaaS/AI console heuristics. Rhea is closer to AutoCAD/MATLAB/instrument software — high signal density, different constraints. This is not a consumer app with onboarding flows and empty states. It is a research instrument.
- **scope:** Product positioning, design reference class, UX pattern selection
- **provenance:** ORION_20260226_233126 section 1.3 ("Used generic old SaaS/AI heuristics in the wrong product class"), personality.md ("Every task/prompt should be understood in complex way — not blind execution"), state_full.md (Rhea's mission: "Mind Blueprint factory")
- **invariant_core:** Rhea's design reference class is professional instruments (CAD, MATLAB, DAWs), not consumer SaaS (Notion, Linear, generic dashboards).
- **failure_conditions:** Applying consumer-app patterns (empty states with illustrations, simplified "getting started" wizards, hiding complexity behind "advanced" toggles); reducing information density to look "clean."
- **use:** When choosing a UI pattern, first check if it exists in instrument software. If it's only found in consumer SaaS, justify why it belongs here. Default to high density, keyboard shortcuts, and expert-first design.

---

# GEM-06: The user's signal is often alogical by design

- **statement:** Human signal often arrives as feeling/comparison before formal explanation. The user explicitly does not demand clean intent early — raw intake, blind comparison, relation emergence, gem extraction, then pressure-test with provenance. This is the product method AND the user's own cognitive style.
- **scope:** Input processing, conversation design, agent response strategy
- **provenance:** LEARNING_FEED.md ORION 2026-02-27 ("Human signal is often alogical by design — feeling/comparison precede formal explanation. Do not demand clean intent early"), ORION_20260226_233126 section 2.4 ("Human universal capability = comparing/distinguishing")
- **invariant_core:** Accept raw, unstructured, feeling-first input. Structure emerges downstream through comparison, not upfront through forms.
- **failure_conditions:** Forcing structured input too early; asking "what do you mean by X?" instead of processing the signal; requiring clean taxonomy before accepting a claim; treating vague input as low-quality input.
- **use:** The composer must accept anything — half-formed thoughts, URLs, single words, emotional impressions. The system structures it; the user does not have to.

---

# GEM-07: Provenance and evidence are non-negotiable

- **statement:** The user demands visible provenance for every claim, every metric, every UI element. Evidence expectations are explicit: hardlink visible UI to source/state/time/demo-live status. The user caught Orion claiming "fixed" without live browser verification — provenance discipline applies to agents AND to the product.
- **scope:** API contracts, UI data display, agent communication, verification protocol
- **provenance:** ORION_20260226_233126 section 1.1 (user corrected "fixed" claims without live verification), section 3.2 (hardlink requirement), SOBER_CHECK.md (decisions > file touches), LEARNING_FEED.md ("pleasant entry, brutal verification")
- **invariant_core:** Every claim has a source. Every source is verifiable. "I checked" without proof = not checked.
- **failure_conditions:** Displaying data without timestamp or source; agents claiming completion without live verification; removing provenance fields to simplify the UI; conflating "I ran the code" with "I verified the output."
- **use:** API responses must include source/timestamp fields. UI components must render provenance on hover or inline. Agent reports must include verification method. "Trust but verify" is not enough — "show your work" is the standard.

---

# GEM-08: Terminology precision — words are load-bearing

- **statement:** The user caught a critical terminology collision: "artifact" in user protocol means rare, significant, invariant-truth gem. The UI used "artifacts" as generic memory-item count. This mismatch erodes trust because the user reads "42 artifacts" and expects 42 proven truths but gets 42 log entries. Words in the UI carry the same weight as code identifiers.
- **scope:** Naming conventions, label taxonomy, glossary, copy review
- **provenance:** ORION_20260226_233126 section 3.4 (artifact terminology issue), LEARNING_FEED.md ORION 2026-02-27 ("Ontology is the main human interface"), personality.md ("Be terse. No filler.")
- **invariant_core:** UI labels must match the user's mental model precisely. When in doubt, use the user's word, not the engineering term.
- **failure_conditions:** Using engineering jargon in user-facing surfaces; overloading a term the user has already defined; generic labels ("items", "things") when the user has specific vocabulary; changing terminology across views.
- **use:** Maintain a living glossary of user-defined terms. Before labeling any UI element, check if the user has already named that concept. Use their word. If no user word exists, propose one and get it ratified.

---

# GEM-09: Package quality = trust signal (cross-page consistency)

- **statement:** The user called out footer inconsistency across pages as a severe quality signal. This is not polish — it changes trust perception. If the product looks inconsistent across views, the user infers the backend is equally inconsistent. Package quality is a trust proxy.
- **scope:** Cross-view consistency, component library discipline, deploy preflight
- **provenance:** ORION_20260226_233126 section 3.5 (user called out footer inconsistency as severe), section 1.4 (deploy preflight discipline was weak)
- **invariant_core:** Every view shares the same visual contracts (footer, nav, typography, spacing). Deviation = trust erosion.
- **failure_conditions:** Shipping one view without checking all others; different footer/header across pages; inconsistent spacing/type scale; "we'll fix it later" on visual consistency.
- **use:** Preflight checklist before any deploy: nav cross-links, footer consistency, typography scale, localhost leftovers, trailing slash behavior. No deploy without passing all checks.

---

# GEM-10: The user values gradient over stability (Axiom 0)

- **statement:** The project's axiom zero is `gradient positive or bottom` — you are either pushing forward or you are dead. There is no stable middle ground. The user explicitly rejects "degradation is not terminal" as a valid status because accepting degradation as normal already violates the axiom. This applies to product, to agents, to the system as a whole.
- **scope:** Product velocity, agent behavior, status reporting, prioritization
- **provenance:** LEARNING_FEED.md Axiom 0 ("settle(agent, x) AND x < frontier implies bottom"), personality.md ("My metric: total value brought today"), SOBER_CHECK.md ("What did you produce that only you could produce?")
- **invariant_core:** Forward motion is mandatory. Any status report that normalizes stagnation or degradation is a failure signal, not an acceptable state.
- **failure_conditions:** Reporting "stable" as a positive status; accepting known regressions as "non-critical"; deferring improvements indefinitely; running maintenance loops without net-new value.
- **use:** Every session, every sprint, every deploy must produce net-new value. Status reports must show delta from previous state, not absolute state. If delta is zero or negative, escalate — do not normalize.

---

END OF GEMS. 10 extracted. All provenance traceable to source files.

DELIVERY: ORION inbox/outbox relay.
FORMAT: Matches requested schema (statement, scope, provenance, invariant_core, failure_conditions, use).
