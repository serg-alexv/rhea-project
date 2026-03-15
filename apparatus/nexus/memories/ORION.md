## Session 2026-03-15
- Did: Rebuilt `docs/rheakit-docs` as a Fumadocs static site, mounted it at `/docs/`, preserved the handwritten API docs at `/api-docs`, and kept `/swagger` intact.
- Did: Fixed Fly publish path by switching `config/fly/fly.toml` to `../docker/Dockerfile.platform`, declaring the existing `rhea_data` volume at `/app/data`, broadening runtime dependency installs, and using `COPY src/*.py src/`.
- Learned: Fly deploys were blocked first by stale Dockerfile config, then by missing runtime deps (`email-validator` on the startup path), then by an undeclared volume mount; once those were fixed the machine passed health and served the new docs live.
- Next: Expand deeper component pages under `docs/rheakit-docs/content/docs/components/` and keep the docs content aligned with the growing Swift package surface.

## Session 2026-03-15
- Did: Added shared-memory frame IPC to `rhea-biorenderer` with `buffer_types`, `buffer_ipc`, and reader/writer examples on macOS.
- Learned: The workspace contained a malformed duplicated `buffer_ipc.rs` heredoc transcript; a clean delete/recreate was required before `cargo check` stabilized.
- Next: If this path is consumed by Swift next, wire the reader contract into the iOS-side bridge without changing the 48-byte header layout.
