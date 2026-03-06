# Rhea Developer Documentation

Welcome to Rhea's developer hub. Rhea is a multi-device, multi-model AI assistant with deterministic session convergence across devices.

## Getting Started

**New to Rhea?** Start here:
- [Getting Started: A Story](./getting-started.md) — **The narrative** (read this first)
- [Quick Start (5 min)](./quickstart.md) — Run your first session
- [Architecture Overview](./architecture.md) — How Rhea works
- [Installation](./installation.md) — Set up your environment

## Core Concepts

- **Sessions** — Immutable, append-only message streams with CRDT convergence
- **Lamport Clocks** — Deterministic causal ordering across devices
- **Messages** — Immutable events (never change once created)
- **Devices** — Independent clients with local truth databases
- **Server** — Authority for Lamport clock assignment and conflict resolution

## API Reference

All APIs organized by service:

- [Session API](./api/sessions.md) — Create, sync, retrieve sessions
- [Message API](./api/messages.md) — Add and retrieve messages
- [Device API](./api/devices.md) — Register and manage devices
- [Memory API](./api/memory.md) — Cross-session memory and recall

## Guides

Detailed walkthroughs for common tasks:

- [Cross-Device Sync](./guides/cross-device-sync.md) — Keep devices in sync
- [Offline Operation](./guides/offline.md) — Queue locally, sync when connected
- [Memory Management](./guides/memory.md) — Use long-term context
- [Integrating LLMs](./guides/llm-integration.md) — Connect OpenAI, Anthropic, etc.
- [Deployment](./guides/deployment.md) — Run in production

## Examples

Production-ready code samples:

- [Minimal Client](./examples/minimal-client.rs) — Bare-bones session setup
- [Multi-Device Sync](./examples/multi-device.rs) — Two devices converging
- [Offline Queue](./examples/offline-queue.rs) — Local queuing with server sync
- [Memory Injection](./examples/memory-injection.rs) — Context-aware responses

## Architecture Deep Dives

For those wanting to understand internals:

- [Design Philosophy](./architecture/philosophy.md) — **The why** behind every decision
- [DTS: Deterministic Time System](./architecture/dts.md) — How Lamport clocks work
- [CRDT Convergence](./architecture/crdt.md) — Why all devices see the same order
- [Local Truth Database](./architecture/local-truth.md) — SQLite schema & queries
- [Control Layer](./architecture/control.md) — Events, metadata, audit trails

## SDKs & Libraries

Official clients and bindings:

- **Rust**: [`rhea-client`](../../../rhea-client) — Full-featured client
- **TypeScript**: [`rhea-web`](../../../rhea-web) — Browser & Node.js
- **Python**: `rhea-py` (coming soon)

## Troubleshooting

- [FAQ](./faq.md) — Common questions
- [Debugging](./debugging.md) — Tools and techniques
- [Performance](./performance.md) — Optimization tips

## Support

- **Issues**: [GitHub Issues](https://github.com/rhea/rhea/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rhea/rhea/discussions)
- **Status**: [System Status](https://status.rhea.dev)

---

**Last updated**: 2026-03-06  
**Version**: Rhea v0.5.0-alpha (post-DTS fix)
