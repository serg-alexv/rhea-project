# Installation

## Prerequisites

| Component | Requirement | Version |
|-----------|-------------|---------|
| Rust | Compiler & cargo | 1.70+ |
| SQLite | Embedded in rhea-client | (bundled) |
| tokio | Async runtime | (in Cargo.toml) |
| HTTP client | For server communication | (in Cargo.toml) |

## Setup: Rhea Server

**1. Clone repository**

```bash
git clone https://github.com/your-org/rhea.git
cd rhea
```

**2. Build server**

```bash
cd rhea-session-server
cargo build --release
```

Output: `target/release/server`

**3. Run server**

```bash
cargo run --release --bin server
```

Expected output:
```
🌟 Rhea Session Server running on http://127.0.0.1:3000
```

Server listens on `127.0.0.1:3000`. Change via `--bind` flag:

```bash
cargo run --release --bin server -- --bind 0.0.0.0:8080
```

## Setup: Rhea Client (Rust)

**1. Add to Cargo.toml**

```toml
[dependencies]
rhea-client = { path = "../rhea-client" }
tokio = { version = "1.50", features = ["full"] }
serde_json = "1.0"
```

**2. Create client**

```rust
use rhea_client::Client;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let client = Client::new(
        "http://127.0.0.1:3000",
        "device-id"
    ).await?;
    
    // Now use client
    Ok(())
}
```

**3. Run**

```bash
cargo run
```

## Setup: Rhea Client (TypeScript / Node.js)

Coming in Phase 2. For now, use Rust client via FFI or HTTP directly.

## Docker Setup (Optional)

**Build image**

```bash
docker build -f Dockerfile -t rhea:latest .
```

**Run container**

```bash
docker run -p 3000:3000 rhea:latest
```

Server listens on `127.0.0.1:3000` (or `0.0.0.0:3000` from container).

## Verification

**1. Check server is running**

```bash
curl http://127.0.0.1:3000/sessions
# Should return: []
```

**2. Run quick test**

```bash
cd rhea-client
cargo test --lib
```

**3. Run example**

```bash
cargo run --example minimal-client
```

Expected output:
```
✓ Created session: 550e8400-e29b-41d4-a716-446655440000
✓ Added message: 650e8400-e29b-41d4-a716-446655440001
Messages (ordered by Lamport clock):
  [LC:1] user: Hello, Rhea!
```

## Configuration

### Server Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RHEA_BIND` | `127.0.0.1:3000` | Server address |
| `RHEA_WORKERS` | `4` | Tokio worker threads |
| `RHEA_LOG_LEVEL` | `info` | Log verbosity |

**Set**:
```bash
export RHEA_BIND=0.0.0.0:8080
export RHEA_LOG_LEVEL=debug
cargo run --release --bin server
```

### Client Configuration

```rust
let client = Client::new(
    "http://rhea-server.example.com",  // Server URL
    "device-id-12345"                   // Device ID
).await?;

client.set_timeout(Duration::from_secs(30))?;
client.set_retry_count(3)?;
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Server not running | Start server: `cargo run --release --bin server` |
| `Port 3000 already in use` | Another process on port | Change port: `--bind 0.0.0.0:8081` |
| `SSL certificate error` | HTTPS without cert | Use HTTP for dev, add certs for prod |
| `Database locked` | Multiple writers | Ensure only one server instance |

## Next Steps

- [Quick Start](./quickstart.md) — Run your first session (5 min)
- [Architecture Overview](./architecture.md) — Understand the design
- [API Reference](./api/sessions.md) — Build your integration
