# PlayUI / RheaKit Component Map

**Goal**: treat `packages/RheaKit` as the canonical PlayUI toolkit and surface its BioRenderer/author tools across Atlas/docs. No new UI stack—just reuse these Swift components and document their intents.

| Component | Purpose | Atlas/Documentation story |
| --- | --- | --- |
| `BioRendererView` | 3D rendering engine for authoring biological narratives (aerobic metab, probiotic signals). | Capture a screenshot/video, embed it as the “BioRenderer author tool” highlight in the Atlas landing and/or a doc card.
| `DPIView` / `DPIBypassEngine` | Dynamic DPI mesh visuals + performance bypass controller. | Use gradient/pulse motifs from DPI in Atlas hero and create a short explanation card ("DPI harness") in `rhea-atlas`.
| `NodeEditorView` | Node-based workflow editor (chains, proofs, tasks). | Build a static “Ruliad node map” for docs (maybe in `docs/playui-flow.md`) and accent it on the WOW page.
| `GovernorView`, `PulseMonitorView`, `TasksView`, `ProcessesView` | Agent/governor dashboards showing states, health, tasks. | Transform into Atlas “instrument cluster” visual block and describe how BioRenderer feeds these panels.
| `ToolsHubView`, `DialogView`, `TeamChatView` | Communication hubs for agents (chat, tool selection). | Document as “author workspace” for writing science articles; list features + export/publish buttons.
| `AtlasWebView`, `MonitorWebView`, `OfficeView`, `OpsView` | Embedded browser/tool surfaces inside PlayUI. | Mention as “web orchestration canvas” in docs and show placeholder images.
| `AletheiaView`, `ChainsView`, `RuliadView`, `ModelsView` | Scientific proof/chain interfaces. | Use to illustrate “How to capture proofs for H32-02” and pair with textual descriptions in `docs/h32-02.md`.

## Immediate tasks
1. **Capture visuals**: relay to Rex requesting high-res screenshots/videos of `BioRendererView`, `NodeEditorView`, and the governor cluster (instant screenshot for documentation). Keep artifacts stored privately (Google Drive).
2. **Document workflow**: update `docs/h32-02.md` describing the “Aerobic metabolism / protection / probiotic gene” author story using these components. Reference the previous `Downloads/Genetics task.txt` as context.
3. **Atlas integration**: embed at least one PlayUI visual card into the WOW landing (via existing `rhea-atlas` sections or a new component block) to highlight BioRenderer’s author toolset.
4. **Agent teams/swarms**: create a `plans/playui-swarm.md` (optional) outlining how subagents can run component tests or capture proofs; each subagent handles one component (Bio, NodeEditor, ToolsHub).

## Relay actions
- Finish PlayUI asset request (Relay p4) — confirm once Rex uploads files to Google Drive or shared folder.
- Once assets arrive, log their location in `docs/google-sync.md` for the team.

Ready for the next step: create visuals, author docs, and integrate them into Atlas. Let me know which task you want me to begin first.
