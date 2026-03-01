# Tailscale iOS Integration: Technical Research Report

**Date**: 2026-03-01
**Scope**: Embedding Tailscale's Go networking stack into an iOS PacketTunnelProvider Network Extension
**Status**: Research complete — all six areas investigated

---

## 1. License Audit

### Tailscale Core (`tailscale/tailscale`)
- **License**: BSD-3-Clause
- **Copyright**: Tailscale Inc & contributors (2020)
- **Commercial embedding**: PERMITTED. BSD-3-Clause allows redistribution in source and binary forms, with or without modification. Only requirements: retain copyright notice, don't use Tailscale's name to endorse derived products without permission.
- **Dependencies**: All compatible with BSD-3-Clause (verified via `go-licenses` tool in the repo's `licenses/` directory).

### libtailscale (`tailscale/libtailscale`)
- **License**: BSD-3-Clause
- **Commercial embedding**: PERMITTED.

### TailscaleKit (Swift bindings in `libtailscale/swift/`)
- **License**: BSD-3-Clause (inherits from libtailscale)
- **Commercial embedding**: PERMITTED.

### wireguard-go (`WireGuard/wireguard-go`)
- **License**: MIT
- **Copyright**: Jason A. Donenfeld
- **Commercial embedding**: PERMITTED. MIT is maximally permissive.
- **Note**: The wireguard-go GitHub page says "MIT". Wikipedia and some older sources list GPL-2 for the *kernel module* — the userspace Go implementation is MIT.

### wireguard-apple (`WireGuard/wireguard-apple`)
- **License**: MIT (SPDX-License-Identifier: MIT in source files, copyright WireGuard LLC 2018-2023)
- **Commercial embedding**: PERMITTED.
- **Trademark**: "WireGuard" is a registered trademark of Jason A. Donenfeld. You cannot call your product "WireGuard" but can use the protocol.

### Headscale (`juanfont/headscale`)
- **License**: BSD-3-Clause
- **Copyright**: Juan Font (2020)
- **Commercial use**: PERMITTED.

### DERP relay (`tailscale.com/cmd/derper`)
- **License**: BSD-3-Clause (part of tailscale/tailscale repo)
- **Self-hosting**: PERMITTED.

### Verdict
**All components needed for a fully self-hosted Tailscale stack are BSD-3-Clause or MIT. No GPL contamination in the userspace path. Safe for commercial iOS App Store distribution.**

---

## 2. Tailscale iOS Architecture

### How the Official Tailscale iOS App Works

The Tailscale iOS app is a **Network Extension** (`NEPacketTunnelProvider`) with a proprietary Swift GUI shell wrapping an open-source Go networking core.

#### Component Map

```
┌─────────────────────────────────────────────┐
│  Tailscale iOS App (PROPRIETARY — not OSS)  │
│  ├── Swift UI (Settings, Status, Login)     │
│  └── IPNExtension target                    │
│       ├── IPNPacketTunnelProvider.swift      │
│       │   (extends NEPacketTunnelProvider)   │
│       └── ipn-go-bridge                     │
│            (gomobile-generated Go→Swift)     │
├─────────────────────────────────────────────┤
│  Open Source Go Core (BSD-3-Clause)          │
│  ├── ipn/ipnlocal (LocalBackend)            │
│  ├── wgengine (WireGuard engine)            │
│  ├── wgengine/netstack (userspace TCP/IP)   │
│  ├── magicsock (NAT traversal, DERP)        │
│  ├── control/controlclient (coord server)   │
│  └── derp (relay protocol)                  │
└─────────────────────────────────────────────┘
```

#### Go → iOS Compilation

Tailscale uses **gomobile** (`golang.org/x/mobile`) to compile the Go codebase:

1. **gomobile bind** produces an `.xcframework` containing a static library (`libwg-go.a` or equivalent) for arm64 (device) and x86_64/arm64 (simulator).
2. The Go code is compiled with `CGO_ENABLED=1` using the iOS SDK as the sysroot.
3. Tailscale maintains a **Go fork** for release builds (optimized linker, reduced binary size), but the fork is NOT required — stock Go works.
4. Key Go runtime tuning for iOS Network Extension:
   - `GOMAXPROCS=1` (single-threaded — reduces memory overhead)
   - Aggressive `debug.SetGCPercent` (Network Extensions get only ~15 MB RAM, vs ~5 GB for normal apps)
   - Linker patches to reduce `__DATA_CONST` from 1568 KB to 708 KB

#### IPNExtension Target

- `IPNPacketTunnelProvider.swift` extends `NEPacketTunnelProvider`
- Communicates with Go backend via **ipn-go-bridge** (a gomobile-generated bridge)
- Route table configured via JSON blob from Go side → `NEPacketTunnelNetworkSettings.ipv4Settings` / `.ipv6Settings`
- The Go `ipn/ipnlocal.LocalBackend` is the central coordinator: manages control plane communication, WireGuard engine, DNS, and peer state

#### Open Source vs. Proprietary Boundary

| Component | License | Notes |
|-----------|---------|-------|
| Go daemon (tailscaled core) | BSD-3-Clause | Open source |
| DERP relay server | BSD-3-Clause | Open source |
| Android client + GUI | BSD-3-Clause | Fully open source |
| Linux client + GUI | BSD-3-Clause | Fully open source |
| iOS/macOS GUI shell | PROPRIETARY | Not open source |
| iOS/macOS IPNExtension Swift code | PROPRIETARY | Not open source |
| Windows GUI | PROPRIETARY | Not open source |
| Coordination server | PROPRIETARY | Not open source (Headscale is the OSS replacement) |

**Key implication**: You cannot reuse Tailscale's `IPNPacketTunnelProvider.swift`. You must write your own Swift NetworkExtension shell, but you can use all the Go packages underneath.

---

## 3. Headscale (Self-Hosted Control Plane)

### Overview
- **Repo**: https://github.com/juanfont/headscale
- **License**: BSD-3-Clause (verified)
- **Purpose**: Drop-in replacement for Tailscale's proprietary coordination server
- **Implements**: The Tailscale coordination protocol — key exchange, node registration, ACL distribution, DERP map distribution, DNS configuration

### Can It Replace Tailscale's Server Entirely?
**Yes**, with caveats:
- Node registration, key exchange, peer discovery — all work
- ACL policy — supported
- DNS (MagicDNS equivalent) — supported
- DERP map distribution — supported (configurable via URL or local YAML file)
- **Not supported**: Tailscale Funnel, Tailscale SSH certificates, some enterprise features
- iOS official Tailscale client supports Headscale since version **1.38.1** via "Alternate Coordination Server URL" in iOS Settings

### Connecting Clients to Headscale

**Official Tailscale iOS app**:
1. Install from App Store (v1.38.1+)
2. Settings → Tailscale → "ALTERNATE COORDINATION SERVER URL" → enter `https://your-headscale.example.com`
3. Or: in-app → Account icon → Log in → Options → "Use custom coordination server"

**tsnet (embedded Go)**:
```go
srv := &tsnet.Server{
    Hostname:   "my-node",
    ControlURL: "https://your-headscale.example.com",
    AuthKey:    "your-preauthkey",
}
```

### Deployment on Fly.io

**Proven feasible** — multiple production deployments exist.

**Architecture**:
- Single Fly.io machine (`shared-cpu-1x`, 256 MB RAM)
- SQLite database on Fly.io persistent volume (mounted at `/data`)
- Optional: Litestream replication to Tigris S3 for backup
- **Cost**: ~$2/month for up to ~100 nodes

**Key config (`fly.toml`)**:
```toml
[build]
  image = "headscale/headscale:latest"

[mounts]
  source = "headscale_data"
  destination = "/data"

[[services]]
  internal_port = 8080
  protocol = "tcp"
  [services.concurrency]
    type = "connections"
    hard_limit = 25
    soft_limit = 20
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
  [[services.ports]]
    port = 80
    handlers = ["http"]
```

**Headscale config changes for Fly.io**:
- `db_path: /data/headscale.sqlite3`
- `server_url: https://your-app.fly.dev`
- DERP map: can use Tailscale's default (`https://controlplane.tailscale.com/derpmap/default`) or self-hosted

**Reference repos**:
- https://github.com/luislavena/homelab-headscale (Apache-2.0, Litestream backup)
- https://github.com/NiklasRosenstein/headscale-fly-io (Litestream + Tigris)

---

## 4. DERP Relay Servers

### What DERP Does
DERP (Designated Encrypted Relay for Packets) provides:
- **NAT traversal fallback**: when direct UDP hole-punching fails, traffic relays through DERP
- **Always-on connectivity**: ensures peers can always reach each other
- **End-to-end encrypted**: DERP sees only encrypted WireGuard packets, cannot read traffic

### Self-Hosting DERP

**Yes, fully supported and open source.**

**Installation**:
```bash
go install tailscale.com/cmd/derper@latest
```

**Port requirements**:
- TCP 443 (HTTPS for DERP protocol)
- TCP 80 (HTTP for captive portal checks)
- UDP 3478 (STUN for NAT detection)

**Key flags**:
- `--verify-clients` — only allow authenticated Tailscale/Headscale clients (requires `tailscaled` running on same machine, must be same git revision)
- `--hostname` — public hostname for TLS certificate (auto-provisions Let's Encrypt)
- `--certdir` — directory for TLS certificates
- `--stun` — enable STUN server (default: true)

**Resource requirements**: Very lightweight — ~100 MB RAM for 50 concurrent peers. A $5/month VM handles most deployments.

**DERP map configuration in Headscale** (`config.yaml`):
```yaml
derp:
  # Use Tailscale's default DERP servers:
  urls:
    - https://controlplane.tailscale.com/derpmap/default
  # OR use local DERP map file:
  paths:
    - /etc/headscale/derp.yaml
  # Custom DERP map:
  # RegionIDs 900+ for custom servers (1-899 reserved for Tailscale)
```

**Custom DERP map YAML**:
```yaml
regions:
  900:
    regionid: 900
    regioncode: "myderp"
    regionname: "My DERP"
    nodes:
      - name: "900a"
        regionid: 900
        hostname: "derp.example.com"
        stunport: 3478
        stunonly: false
        derpport: 443
```

### Running Without Tailscale Control Plane
DERP servers are protocol-level relays. They work with **any** Tailscale-compatible control plane (Headscale included). The `--verify-clients` flag requires a running `tailscaled`, but without it, the DERP server accepts any Tailscale client.

---

## 5. wireguard-go and wireguard-apple

### wireguard-go
- **Repo**: https://github.com/WireGuard/wireguard-go (mirror; official: git.zx2c4.com)
- **License**: MIT
- **Purpose**: Userspace WireGuard implementation in Go
- **iOS compilation**: via CGo cross-compilation (`GOOS=darwin GOARCH=arm64`) producing a static library

### wireguard-apple (WireGuardKit)
- **Repo**: https://github.com/WireGuard/wireguard-apple
- **License**: MIT
- **Purpose**: Complete WireGuard VPN client for iOS and macOS using NetworkExtension framework

#### Architecture

```
┌─────────────────────────────────────────┐
│  PacketTunnelProvider                    │
│  (extends NEPacketTunnelProvider)        │
│  ├── startTunnel() → WireGuardAdapter   │
│  ├── stopTunnel()  → wgTurnOff()        │
│  └── handleAppMessage()                 │
├─────────────────────────────────────────┤
│  WireGuardAdapter (Swift)               │
│  ├── Manages tunnel file descriptor     │
│  ├── Creates NEPacketTunnelNetworkSettings│
│  ├── Monitors NWPath changes            │
│  └── Calls C bridge functions           │
├─────────────────────────────────────────┤
│  wireguard-go-bridge (C API)            │
│  ├── wgTurnOn(settings, tunFd)          │
│  ├── wgTurnOff(handle)                  │
│  ├── wgSetConfig(handle, config)        │
│  ├── wgGetConfig(handle) → string       │
│  ├── wgBumpSockets(handle)              │
│  └── wgVersion() → string              │
├─────────────────────────────────────────┤
│  wireguard-go (Go)                      │
│  └── device.Device — encryption/decrypt │
└─────────────────────────────────────────┘
```

#### How wireguard-go-bridge Builds for iOS

1. `api-apple.go` is a CGo wrapper exposing Go functions as C symbols
2. Built via Makefile as `c-archive` → produces `libwg-go.a`
3. Universal binary for arm64 + x86_64
4. A runtime patch (`goruntime-boottime-over-monotonic.diff`) handles iOS sleep states
5. Output `libwg-go.a` is linked into the Swift NetworkExtension target

#### Xcode Integration Steps (WireGuardKit as Swift Package)

1. Add WireGuardKit Swift package dependency
2. Create External Build System target named `WireGuardGoBridgeiOS`:
   - Build tool: `/usr/bin/make`
   - Directory: `${BUILD_DIR%Build/*}SourcePackages/checkouts/wireguard-apple/Sources/WireGuardKitGo`
   - SDKROOT: `iphoneos`
3. Add `WireGuardGoBridgeiOS` as dependency to your Network Extension target
4. Link `WireGuardKit` in "Link with Binary Libraries"
5. Disable Bitcode (`ENABLE_BITCODE = NO`)
6. Set Go path in build settings if auto-detection fails

#### Packet Flow

**Outbound**: App → iOS network stack → PacketTunnelProvider → WireGuardAdapter → wireguard-go-bridge → Go device (encrypt) → UDP to peer/DERP

**Inbound**: UDP from peer → Go device (decrypt) → wireguard-go-bridge → WireGuardAdapter → PacketTunnelProvider → iOS network stack → App

---

## 6. Minimum Viable Integration

### Goal
WireGuard tunnel + NAT traversal + self-hosted control plane + iOS PacketTunnelProvider. No Tailscale account.

### Two Approaches

#### Approach A: TailscaleKit (Recommended)

**Use `tailscale/libtailscale` with Swift bindings (`libtailscale/swift/TailscaleKit`).**

This is the path of least resistance. TailscaleKit wraps the full Tailscale stack (WireGuard + NAT traversal + control plane client) into a single Swift framework.

**Required packages** (all BSD-3-Clause):
- `tailscale.com/tsnet` — embedded Tailscale server
- `tailscale.com/wgengine` — WireGuard engine
- `tailscale.com/wgengine/netstack` — userspace TCP/IP (gVisor-based)
- `tailscale.com/control/controlclient` — coordination server client
- `tailscale.com/derp` — DERP relay client
- `tailscale.com/net/magicsock` — NAT traversal (STUN + DERP fallback)

**Build**:
```bash
cd libtailscale/swift
make ios        # → build/Build/Products/TailscaleKit.framework (arm64)
make ios-sim    # → simulator variant
make ios-fat    # → universal (both architectures)
```
Requires Xcode 16.1+, Swift 6, Go 1.25+.

**Swift integration**:
```swift
import TailscaleKit

let config = Configuration(
    hostName: "my-rhea-node",
    path: FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: "group.com.example.app")!.path,
    authKey: "tskey-auth-...",   // pre-auth key from Headscale
    controlURL: "https://your-headscale.fly.dev",
    ephemeral: false
)

let node = TailscaleNode(config: config, logger: myLogger)
try await node.up()

// Make HTTP requests to other tailnet nodes:
let sessionConfig = try await node.tailscaleSession(node)
let session = URLSession(configuration: sessionConfig)
let (data, _) = try await session.data(from: URL(string: "http://100.64.x.x:8080/api")!)
```

**Caveats**:
- TailscaleKit is pre-v1.0, API may change
- iOS sandbox: `os.Executable()` fails → patched to fallback to "tsnet"
- Memory limit: 15 MB for Network Extension — requires `GOMAXPROCS=1` and aggressive GC
- TailscaleKit does NOT run as a PacketTunnelProvider by default — it creates an embedded node with userspace networking. For system-wide VPN (all apps tunneled), you need to write your own `NEPacketTunnelProvider` subclass that wraps TailscaleKit or the Go engine.

#### Approach B: Custom Stack (More Control, More Work)

Build your own integration using lower-level components:

1. **WireGuard tunnel**: Use `WireGuardKit` from `wireguard-apple` (MIT license)
   - Provides `PacketTunnelProvider` + `WireGuardAdapter` out of the box
   - Handles tunnel FD management, network path monitoring

2. **NAT traversal**: Use Tailscale's `magicsock` package
   - Implements ICE-like connectivity: tries direct UDP, falls back to DERP relay
   - You would need to bridge this into the WireGuardKit flow

3. **Control plane**: Connect to self-hosted Headscale
   - Use `tailscale.com/control/controlclient` for the coordination protocol
   - Or implement the simpler approach: generate WireGuard configs from Headscale and load them into WireGuardKit directly (no Tailscale code needed, but loses dynamic peer discovery)

4. **DERP relay**: Self-host `cmd/derper`, configure in Headscale DERP map

**This approach is significantly harder** because you need to integrate magicsock with WireGuardKit's bridge layer, which Tailscale's official iOS app does internally but that code is proprietary.

### Recommendation

**Use Approach A (TailscaleKit) with Headscale.**

| Component | Solution | License |
|-----------|----------|---------|
| WireGuard tunnel | Tailscale's built-in `wgengine` via TailscaleKit | BSD-3-Clause |
| NAT traversal | Tailscale's `magicsock` (STUN + DERP) via TailscaleKit | BSD-3-Clause |
| Control plane | Headscale on Fly.io ($2/mo) | BSD-3-Clause |
| DERP relay | Self-hosted `cmd/derper` OR Tailscale's free public relays | BSD-3-Clause |
| iOS integration | TailscaleKit.framework + custom PacketTunnelProvider | BSD-3-Clause |
| Userspace networking | gVisor netstack via TailscaleKit | Apache-2.0 |

### iOS Memory Budget

The 15 MB Network Extension limit is the hardest constraint. Tailscale's mitigations:
- `GOMAXPROCS=1`
- Aggressive GC (`debug.SetGCPercent` low)
- Linker optimizations (contributed upstream to Go 1.18+)
- Mobile connection limit: 1,024 concurrent TCP connections (vs 8,192 on Linux)

### Minimum Deployment Checklist

1. Deploy Headscale on Fly.io (persistent volume + SQLite)
2. Generate pre-auth keys via `headscale preauthkeys create --user default`
3. Build TailscaleKit.framework for iOS (`make ios` in `libtailscale/swift/`)
4. Create Xcode project with Network Extension target
5. Subclass `NEPacketTunnelProvider`, instantiate `TailscaleNode` in `startTunnel()`
6. Configure `controlURL` to point to Headscale instance
7. Optional: deploy self-hosted DERP server for lower latency / data sovereignty
8. App Group container for shared state between main app and extension

---

## Sources

- [tailscale/tailscale](https://github.com/tailscale/tailscale) — BSD-3-Clause, core Go daemon
- [tailscale/libtailscale](https://github.com/tailscale/libtailscale) — BSD-3-Clause, C/Swift library for embedding
- [Tailscale LICENSE](https://github.com/tailscale/tailscale/blob/main/LICENSE) — BSD-3-Clause
- [Tailscale Open Source page](https://tailscale.com/opensource)
- [Tailscale Go linker blog post](https://tailscale.com/blog/go-linker) — iOS memory constraints, build pipeline
- [tsnet Go package docs](https://pkg.go.dev/tailscale.com/tsnet) — embedded Tailscale API
- [libtailscale Go package docs](https://pkg.go.dev/github.com/tailscale/libtailscale) — C library API
- [libtailscale iOS sandbox issue #15410](https://github.com/tailscale/tailscale/issues/15410)
- [WireGuard/wireguard-go](https://github.com/WireGuard/wireguard-go) — MIT license
- [WireGuard/wireguard-apple](https://github.com/WireGuard/wireguard-apple) — MIT license, WireGuardKit
- [WireGuard embedding guide](https://www.wireguard.com/embedding/)
- [juanfont/headscale](https://github.com/juanfont/headscale) — BSD-3-Clause
- [Headscale Apple client docs](https://headscale.net/stable/usage/connect/apple/)
- [Headscale DERP config](https://headscale.net/stable/ref/derp/)
- [Tailscale DERP server docs](https://tailscale.com/kb/1232/derp-servers)
- [DERP server README](https://github.com/tailscale/tailscale/blob/main/cmd/derper/README.md)
- [luislavena/homelab-headscale](https://github.com/luislavena/homelab-headscale) — Fly.io deployment
- [NiklasRosenstein/headscale-fly-io](https://github.com/NiklasRosenstein/headscale-fly-io) — Fly.io + Litestream
- [Tailscale custom control server docs](https://tailscale.com/kb/1507/custom-control-server)
- [DeepWiki: Tailscale userspace networking](https://deepwiki.com/tailscale/tailscale/5-userspace-network-stack)
- [DeepWiki: wireguard-apple architecture](https://deepwiki.com/WireGuard/wireguard-apple)
- [FR: Open source iOS/macOS GUI wrappers #13717](https://github.com/tailscale/tailscale/issues/13717)
