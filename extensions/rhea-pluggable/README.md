# Rhea-Pluggable Extension (Timelabs-NPO)

This extension turns the main Rhea project into a **pluggable host** for other Timelabs-NPO repositories (`rhea-project`, `rhea-ios`, `rhea-memory`, etc.).

## Goals
1. Provide a lightweight manifest so `rhea` can discover additional repos from `https://github.com/orgs/timelabs/repositories`.
2. Offer a CLI glue script (`sync-timelabs.sh`) that fetches the requested repo, links its hooks into `scripts/rhea.sh`, and wires up shared envs (Fly, Redis, Google Cloud, Firebase, Oracle, Azure).
3. Document the lifecycle: clone → configure secrets → register with Rhea’s command center → run `flow`/`radio` loops.

## How to use
1. **Install**
   ```bash
   cd /Users/sa/rh.1
   ./extensions/rhea-pluggable/sync-timelabs.sh <repo-name>
   ```
   The script clones `https://github.com/timelabs/${repo-name}` into `extensions/${repo-name}` and updates `scripts/rhea.sh` with symbolic links to the repo’s entrypoint (for example, wiring `rhea-ios` build hooks). The list of supported repos is listed on the Timelabs org page.
2. **Register**
   After cloning, edit `extensions/registry.json` (auto-created) and add the manifest entry produced by `sync-timelabs.sh`. This tells the Governor/Flow to treat the extension as part of the same continuity mesh and share `A0` contracts.
3. **Run**
   Use `./scripts/rhea.sh flow', `radio status`, or `./extensions/rhea-pluggable/launch.sh` to start the combined stack. The extension ensures the `timelabs` repo's configurations (keys, Next.js envs, Flutter/App targets) appear in the same `fly deploy` pipeline.

## Why it matters
- The cloud stack already spans Fly, Redis, Google, Firebase, Oracle, and Azure—this extension lets you onboard another repo (like `rhea-play` or `rhea-cli`) without rewriting configuration.
- It automatically registers the repo’s telemetry channels with `Governor` and ensures the NDI/radio pipeline is aware of the new assets.
- Use this extension for rapid experiments (ex: spin up `rhea-ios` tests, capture video on `Higgsflied.ai`, and push the metrics into Governor) while staying in sync with the same multi-agent protocols you’ve already built.

## Next steps
- Add additional manifests under `extensions/rhea-pluggable/manifests/` describing the entrypoint script for each Timelabs repo.
- Build a cron job (via `scripts/rhea.sh continuity-smoke`) that verifies the extension remains registered whenever a new commit lands.
- Invite Rex to confirm the extension adds value to the `flow` pipeline; once he approves, we can showcase both the CI/CD and the price/tour storyline simultaneously.
