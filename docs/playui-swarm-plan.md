# PlayUI Swarm Plan

## Objective
Organize sub-agents (swarms) to operate on `packages/RheaKit` components, harvest BioRenderer visuals, and integrate results into Atlas/docs. Each swarm owns one component cluster (BioRenderer, NodeEditor, author tools) and reports back through nexus relays.

## Swarm roles
1. **BioRenderer Swarm**
   - Tasks: capture `BioRendererView` builds/screens/videos; document how the view supports H32-02 (aerobic metabolism/probiotic story).
   - Agent types: `orion/bio`, `rex/bio-demo`, `hyperion/bio-guard` for verification.
   - Deliverables: screenshot archive, writeup for `docs/h32-02.md`, hero card copy for Atlas.

2. **NodeEditor Swarm**
   - Tasks: explore `NodeEditorView`, `RuliadView`, `ChainsView`; map UI nodes to scientific workflows (proofs, editing). Produce diagram/description.
   - Agent types: `orion/node`, `rex/node-tool`, `hyperion/node-scan`.
   - Deliverables: flowchart document, relation to com-intent, update `docs/playui-comps.md` with the diagram, design a mini interactive node map in Atlas (maybe static image).

3. **Author Toolkit Swarm**
   - Tasks: inspect `ToolsHubView`, `DialogView`, `TeamChatView`, `GovernorView`, `PulseMonitorView`. Outline how these tools support writing, proof-sharing, and audit logging.
   - Agent types: `orion/tools`, `hyperion/log`, `rex/ops` for deployment.
   - Deliverables: textual playbook `docs/playui-tools.md`, atlas cards + short video/gif.

## Workflow
- Each swarm runs a loop: gather data → produce artifact (screenshot, table, text) → relay summary to ORION → ORION posts to shared doc + Atlas landing.
- Use Nexus relays `RELAY_*_ORION_to_*` to request artifacts and confirm readiness.
- Coordinate through `docs/google-sync.md`/shared Google Doc for storing visuals (no secrets). Update `docs/rotation-log.md` when artifacts are rotated.

## Tools
- `rhea-cli` for automation: commands like `rhea swarm bio capture` could trigger screenshot scripts (hooked to Rex’s PlayUI builds).
- Mongo-backed queue for tasks ensures concurrency; `TaskDBMongo` handles assignment, so each swarm claims tasks safely.
- Use `GCloud KMS`/`Google Secret Manager` for storing access to PlayUI builds if needed.

## Next steps
1. Start BioRenderer swarm by asking Rex for latest screenshot/video (Relay reminder).
2. NodeEditor swarm maps via `packages/RheaKit` review and draws flow.
3. Author toolkit swarm drafts doc + card copy.
4. Once all artifacts ready, integrate into Atlas (WOW landing) and update H32-02 narrative.

Ready to spin up the first swarm once you confirm which artifact to prioritize. Should I ask Rex for BioRenderer assets right now? 
