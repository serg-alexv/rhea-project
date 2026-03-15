# Known Boundaries

Facts:

- `play/project.yml` defines the host project in `play/`.
- `play/Sources/PlayApp.swift` is the current Swift host entry.
- Current host boot order is `runtime.js -> app.js`.
- `app.js` is the proven Play root entry.

Boundary:

- `play/Resources/JSCoreScripts/runtime.js` is current host scaffold unless independently proven from Play artifacts.

Not yet proven:

- Full node graph
- Component graph
- Asset rebinding model
- Complete schema contract
