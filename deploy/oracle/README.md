# Oracle Cloud Always Free — Rhea Persistence Layer

Redis 7 on an ARM VM (Ampere A1, 4 OCPU, 24 GB RAM) — replaces Redis Cloud 30 MB free tier with effectively unlimited capacity.

## What runs here

| Service | Port | Status |
|---|---|---|
| Redis 7 | 6379 | Active (AOF + RDB, 4 GB maxmemory cap, AUTH) |
| Backup FastAPI (rhead) | 8000 | Active (fallback if Cloud Run is down) |
| Prometheus | 9090 | Commented out (uncomment in docker-compose.yml) |
| Grafana | 3001 | Commented out (uncomment in docker-compose.yml) |

---

## 1. Create Oracle Always Free account

1. Go to https://www.oracle.com/cloud/free/
2. Sign up — requires a credit card for identity verification but **will not be charged** under Always Free limits.
3. Choose a **Home Region** close to your Cloud Run region (e.g. `us-ashburn-1` for US East).
4. Complete email verification and wait for account activation (up to 24h).

---

## 2. Create the ARM VM

Oracle Console path: **Compute → Instances → Create Instance**

| Field | Value |
|---|---|
| Name | `rhea-oracle-vm` |
| Image | Oracle Linux 8 or Ubuntu 22.04 |
| Shape | **VM.Standard.A1.Flex** |
| OCPU | 4 (Always Free max) |
| Memory | 24 GB (Always Free max) |
| Network | Default VCN — create if first time |
| Subnet | Public subnet |
| Assign public IPv4 | Yes |
| SSH keys | Paste your `~/.ssh/id_ed25519.pub` |

> The A1 shape is Arm-based (Ampere). Docker images must be multi-arch or arm64. The official `redis:7-alpine` and `prom/prometheus` images are multi-arch — no changes needed.

---

## 3. Open ports in Oracle Security List

Oracle's firewall has two layers: the VM's OS firewall (handled by `setup-vm.sh`) and the **VCN Security List** (must be done in the Oracle Console).

Oracle Console path: **Networking → Virtual Cloud Networks → [your VCN] → Security Lists → Default Security List**

Add Ingress Rules:

| Source CIDR | Protocol | Port | Description |
|---|---|---|---|
| 0.0.0.0/0 | TCP | 6379 | Redis |
| 0.0.0.0/0 | TCP | 8000 | Backup API |
| 0.0.0.0/0 | TCP | 9090 | Prometheus (optional) |
| 0.0.0.0/0 | TCP | 3001 | Grafana (optional) |
| 0.0.0.0/0 | TCP | 22 | SSH (already present) |

> For production hardening, replace `0.0.0.0/0` on port 6379 with your Cloud Run egress IP range. Cloud Run uses Google's shared IP pool — easier to keep `0.0.0.0/0` and rely on Redis AUTH.

---

## 4. SSH key setup

```bash
# If you don't have a key yet:
ssh-keygen -t ed25519 -C "rhea-oracle" -f ~/.ssh/id_ed25519

# Copy your public key — paste it into the Oracle VM creation form above
cat ~/.ssh/id_ed25519.pub
```

SSH into the VM once it's running (Public IP shown in Oracle Console):

```bash
# Oracle Linux:
ssh opc@<VM_PUBLIC_IP>

# Ubuntu:
ssh ubuntu@<VM_PUBLIC_IP>
```

---

## 5. Upload and run setup-vm.sh

From your local machine (inside `rh.1/`):

```bash
# Set the VM IP
VM_IP=<VM_PUBLIC_IP>
VM_USER=ubuntu   # or opc for Oracle Linux

# Upload scripts
scp deploy/oracle/setup-vm.sh deploy/oracle/docker-compose.yml \
    ${VM_USER}@${VM_IP}:~/

# Run setup (replace the password with a real secret — 32+ chars recommended)
ssh ${VM_USER}@${VM_IP} "REDIS_PASSWORD='your-strong-secret-here' bash setup-vm.sh"
```

Setup takes 2-5 minutes (mostly Docker install + image pulls). At the end you'll see a summary with the Redis URL.

---

## 6. Connect Cloud Run to Oracle Redis

Set these environment variables in your Cloud Run service (Console or `gcloud`):

```bash
REDIS_URL=redis://:your-strong-secret-here@<VM_PUBLIC_IP>:6379
```

Cloud Run → Edit & Deploy New Revision → Variables and Secrets tab.

Or via CLI:

```bash
gcloud run services update rhea-api \
  --region us-central1 \
  --set-env-vars "REDIS_URL=redis://:your-strong-secret-here@<VM_PUBLIC_IP>:6379"
```

The app already reads `REDIS_URL` from env (`src/rhead.py` line 47, `src/rhea_bus.py`).

---

## 7. Verify connectivity

Quick test from Cloud Shell or any machine:

```bash
# Install redis-cli
apt-get install -y redis-tools   # or: brew install redis

# Test auth and latency
redis-cli -h <VM_PUBLIC_IP> -p 6379 -a 'your-strong-secret-here' PING
# Expected: PONG

redis-cli -h <VM_PUBLIC_IP> -p 6379 -a 'your-strong-secret-here' SET test ok
redis-cli -h <VM_PUBLIC_IP> -p 6379 -a 'your-strong-secret-here' GET test
# Expected: ok
```

---

## 8. Useful commands on the VM

```bash
# Check stack status
docker compose --env-file ~/.env.rhea ps

# Live Redis logs
docker logs -f rhea-redis

# Redis CLI (from VM)
docker exec -it rhea-redis redis-cli -a "$REDIS_PASSWORD"

# Redis memory usage
docker exec rhea-redis redis-cli -a "$REDIS_PASSWORD" INFO memory | grep used_memory_human

# Restart a service
docker compose --env-file ~/.env.rhea restart redis

# Full restart
sudo systemctl restart rhea-stack
```

---

## 9. Enable monitoring (optional)

When you want Prometheus + Grafana:

1. Uncomment the `prometheus` and `grafana` blocks in `docker-compose.yml`.
2. Create a minimal `prometheus.yml` config next to `docker-compose.yml`:

```yaml
# ~/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: redis
    static_configs:
      - targets: ["redis:6379"]
  - job_name: backup-api
    static_configs:
      - targets: ["backup-api:8000"]
    metrics_path: /metrics
```

3. Restart the stack:

```bash
docker compose --env-file ~/.env.rhea up -d
```

Grafana is available at `http://<VM_PUBLIC_IP>:3001` (admin / changeme).

---

## Redis persistence notes

Two persistence mechanisms run simultaneously:

- **AOF (appendonly)** — `appendfsync everysec` — at most 1 second of data loss on crash.
- **RDB snapshot** — every 5 minutes if at least 1 key changed, every 60 seconds if 100+ keys changed.

Data lives in `~/rhea-data/redis/` on the host. Survives container restarts and `docker compose down`.

Backup strategy: Oracle VM's boot volume is included in Oracle's Always Free tier — no extra cost. For offsite backup, consider a weekly `redis-cli BGSAVE` + copy of the RDB file to Oracle Object Storage (also Always Free up to 20 GB).

---

## Cost summary

Oracle Always Free (permanent, not time-limited):

| Resource | Limit | Used |
|---|---|---|
| A1.Flex VM | 4 OCPU / 24 GB | 4 OCPU / 24 GB |
| Boot volume | 200 GB | ~50 GB |
| Outbound data | 10 TB/month | Very low for Redis |
| Object Storage | 20 GB | 0 (optional backups) |

**Total cost: $0.00/month.**
