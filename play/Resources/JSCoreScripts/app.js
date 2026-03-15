if (!globalThis.PlayRuntime) {
  throw new Error("PlayRuntime missing before app.js");
}

globalThis.PlayRuntime.loadedScripts.push("app.js");
globalThis.PlayRuntime.entrypoint = "app.js";

console.log("app.js loaded");
