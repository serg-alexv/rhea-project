# Runtime Entry

Proven Play root entry: `app.js`.

Current host boot order:

```text
Swift host
-> JavaScriptCore
-> runtime.js
-> app.js
```

Boundary:

- `app.js` is the proven Play entry artifact.
- `runtime.js` is part of the current host boot order.
- `runtime.js` in this host is scaffold unless independently proven from Play artifacts.
