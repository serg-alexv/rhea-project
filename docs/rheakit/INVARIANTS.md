# Invariants

- INVARIANT: Play exposes a JavaScriptCore boundary and a proven `app.js` root entry.
  EVIDENCE: `strings /Applications/Play.app/Contents/MacOS/Play` contains `JSCoreScripts/app.js` (`37223`, `144287`), `evaluateScript:` (`80603`, `187606`), `@"JSContext"` and `@"JSValue"` (`37376`, `144440`), `So9JSContextCSg` (`94580`, `229573`), `So7JSValueCSg` (`99136`, `234129`); `docs/rheakit/ARTIFACT_INDEX.md:3`; `docs/rheakit/RUNTIME_ENTRY.md:3`.
  STATUS: PROVEN / REIMPLEMENTATION-CRITICAL

- INVARIANT: The current host boot chain is `Swift host -> JavaScriptCore -> runtime.js -> app.js`.
  EVIDENCE: `play/Sources/PlayApp.swift:11-13`; `play/Sources/PlayRuntimeLoader.swift:15-19`; `play/Sources/PlayRuntimeLoader.swift:25-33`; `docs/rheakit/RUNTIME_ENTRY.md:5-18`.
  STATUS: PROVEN / REIMPLEMENTATION-CRITICAL

- INVARIANT: The current host loads scripts from `JSCoreScripts` and evaluates them with `JSContext`.
  EVIDENCE: `play/Sources/PlayRuntimeLoader.swift:41-52`; `play/Sources/PlayRuntimeLoader.swift:78-85`; `play/Sources/PlayRuntimeLoader.swift:63-75`.
  STATUS: PROVEN / REIMPLEMENTATION-CRITICAL

- INVARIANT: The proven Play `app.js` path and the local host JS files are different artifact classes.
  EVIDENCE: `docs/rheakit/ARTIFACT_INDEX.md:3`; `docs/rheakit/ARTIFACT_INDEX.md:33-37`; `docs/rheakit/KNOWN_BOUNDARIES.md:5-12`; `play/Resources/JSCoreScripts/runtime.js:2`.
  STATUS: PROVEN / REIMPLEMENTATION-CRITICAL

- INVARIANT: Proven subsystem names present in Play binary strings include `PlayNodes`, `PlayPlayMode`, `PlayImages`, and `PlayMacEditor`.
  EVIDENCE: `strings /Applications/Play.app/Contents/MacOS/Play` contains `PlayNodes` (`535`), `PlayPlayMode` (`3787`), `PlayImages` (`5011`), `PlayMacEditor` (`5915`).
  STATUS: PROVEN

- INVARIANT: Proven Play vocabulary includes `node`, `component`, `prefab`, `project`, and `json`.
  EVIDENCE: `strings /Applications/Play.app/Contents/MacOS/Play` contains `NodeViewEvent` (`771`), `ComponentEvent` (`780`), `Prefabable` (`830`), `PrefabActionable` (`900`), `PrefabTriggerable` (`909`), `PrefabSettings` (`912`), `JSONAssetModel` (`970`), `CreateProjectPayload` (`197`), `PatchProjectPayload` (`199`), `ProjectMeta` (`1389`), `ProjectNodeEvent` (`1405`), `ProjectSettings` (`1417`), `ProjectModel` (`1426`), `index.json` (`2174`), `prefabTriggers` (`2179`), `RuntimeFetchJSONAction` (`3989`), `JSONHandler` (`4965`), `JSONParseError` (`263267`).
  STATUS: PROVEN

- INVARIANT: The current local `runtime.js` and `app.js` do not contain `node`, `component`, `project`, `prefab`, or `json` vocabulary.
  EVIDENCE: Full file contents are `play/Resources/JSCoreScripts/runtime.js:1-6` and `play/Resources/JSCoreScripts/app.js:1-8`; `rg -ni "node|component|project|prefab|json" play/Resources/JSCoreScripts/runtime.js play/Resources/JSCoreScripts/app.js` returned no matches.
  STATUS: PROVEN

- INVARIANT: The current local `runtime.js` only establishes a placeholder runtime marker and load list.
  EVIDENCE: `play/Resources/JSCoreScripts/runtime.js:1-6`.
  STATUS: PROVEN

- INVARIANT: The current local `app.js` only checks for `PlayRuntime`, appends `app.js` to `loadedScripts`, sets `entrypoint = "app.js"`, and logs completion.
  EVIDENCE: `play/Resources/JSCoreScripts/app.js:1-8`.
  STATUS: PROVEN

- INVARIANT: The current host build is recorded as a successful unsigned build.
  EVIDENCE: `docs/rheakit/HOST_BUILD.md:3-18`.
  STATUS: PROVEN
