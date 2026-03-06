# Play — Product Guide
**Token Allocation for Multi-Component AI Systems**

---

## What is Play?

Play manages token budgets across your AI components dynamically.

```
You have 1000 tokens to spend.
You have 4 components (BioRenderer, NodeEditor, Governor, TeamChat).
Play decides: "Give BioRenderer 250, NodeEditor 200, Governor 300, TeamChat 250."
All based on priorities you set.
```

---

## Core Concepts

### Components
Each service in your system = one component.
```
Component = { id, name, priority }

Example:
{
  "id": "biorenderer",
  "name": "BioRenderer", 
  "priority": 9
}
```

**Priority**: 1-10 scale. Higher = gets more tokens.
- Priority 10 = VIP (gets most)
- Priority 5 = Normal
- Priority 1 = Background

### Token Budget
Total tokens you have to distribute per request.
```
budget: 1000
```

### Allocation
How tokens split across components.
```
{
  "biorenderer": 250,
  "nodeeditor": 200,
  "governor": 300,
  "teamchat": 250
}
```

---

## Quick Start

### 1. See Your Components
```bash
curl http://localhost:3006/components
```

Response:
```json
[
  {"id": "bio", "name": "BioRenderer", "priority": 9},
  {"id": "node", "name": "NodeEditor", "priority": 8},
  {"id": "gov", "name": "Governor", "priority": 7},
  {"id": "chat", "name": "TeamChat", "priority": 6}
]
```

### 2. Add New Component (On the Fly!)
```bash
curl -X POST http://localhost:3006/components \
  -H "Content-Type: application/json" \
  -d '{
    "id": "atlas",
    "name": "Atlas",
    "priority": 10
  }'
```

No rebuild. No restart. Instant.

### 3. Allocate Tokens
```bash
curl -X POST http://localhost:3006/allocate \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 1000,
    "components": ["atlas", "bio", "node"]
  }'
```

Response (highest priority first):
```json
{
  "allocations": [
    ["atlas", 350],
    ["bio", 301],
    ["node", 349]
  ]
}
```

### 4. Remove Component
```bash
curl -X DELETE http://localhost:3006/components/atlas
```

---

## Common Tasks

### Task: Add a new LLM model
```bash
curl -X POST http://localhost:3006/components \
  -H "Content-Type: application/json" \
  -d '{
    "id": "gpt5",
    "name": "GPT-5",
    "priority": 10
  }'
```

### Task: Give BioRenderer more tokens
Change priority: 9 → 10
```bash
# Delete old
curl -X DELETE http://localhost:3006/components/bio

# Create new (higher priority)
curl -X POST http://localhost:3006/components \
  -d '{
    "id": "bio",
    "name": "BioRenderer",
    "priority": 10
  }'
```

### Task: See allocation for your exact components
```bash
curl -X POST http://localhost:3006/allocate \
  -d '{
    "budget": 5000,
    "components": ["bio", "node", "gov", "chat", "atlas"]
  }' | jq '.allocations'
```

---

## API Reference

### GET /health
Check if Play is running.
```bash
curl http://localhost:3006/health
# Response: "OK"
```

### GET /components
List all components.
```bash
curl http://localhost:3006/components
```

### POST /components
Create new component.
```bash
curl -X POST http://localhost:3006/components \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-service",
    "name": "My Service",
    "priority": 8
  }'
```

**Request:**
```json
{
  "id": "string (unique)",
  "name": "string (human-readable)",
  "priority": "number 1-10"
}
```

**Response:**
```json
{
  "id": "my-service",
  "name": "My Service",
  "priority": 8
}
```

### DELETE /components/:id
Remove component.
```bash
curl -X DELETE http://localhost:3006/components/my-service
```

### POST /allocate
Distribute tokens across components.
```bash
curl -X POST http://localhost:3006/allocate \
  -d '{
    "budget": 1000,
    "components": ["bio", "node"]
  }'
```

**Request:**
```json
{
  "budget": "number (total tokens)",
  "components": ["array of component ids"]
}
```

**Response:**
```json
{
  "allocations": [
    ["component_id", tokens],
    ["another_id", tokens]
  ],
  "total_allocated": 1000
}
```

---

## How Allocation Works

**Algorithm:** Priority-weighted distribution

```
For each component (sorted by priority, highest first):
  allocation = budget × (component_priority / sum_of_priorities)
  budget -= allocation
```

**Example (1000 tokens, 2 components):**
```
BioRenderer (priority 9) + NodeEditor (priority 8) = 17 total

BioRenderer gets: 1000 × (9/17) = 529 tokens ✓ (highest priority wins)
NodeEditor gets:  1000 × (8/17) = 471 tokens

Total: 1000 ✓
```

---

## Troubleshooting

### Problem: Play not responding
**Check if running:**
```bash
curl http://localhost:3006/health
```

**If dead, restart:**
```bash
./play-token-mapper/target/release/play-token-mapper &
```

### Problem: Component not in allocation
**Cause:** Component ID in request doesn't match what's in Play.

**Fix:** Check components:
```bash
curl http://localhost:3006/components | jq '.[].id'
```

Match exactly. IDs are case-sensitive.

### Problem: Allocation seems unfair
**Check priorities:**
```bash
curl http://localhost:3006/components | jq '.[] | {id, priority}'
```

Higher priority = more tokens. By design.

---

## Examples

### Multi-LLM Router
3 LLM models compete for tokens. Higher priority = better model = more tokens.

```bash
# Create models
curl -X POST http://localhost:3006/components \
  -d '{"id":"gpt5","name":"GPT-5","priority":10}'

curl -X POST http://localhost:3006/components \
  -d '{"id":"claude","name":"Claude","priority":9}'

curl -X POST http://localhost:3006/components \
  -d '{"id":"llama","name":"Llama","priority":7}'

# Allocate 10K tokens
curl -X POST http://localhost:3006/allocate \
  -d '{
    "budget": 10000,
    "components": ["gpt5", "claude", "llama"]
  }'

# Result: GPT-5 gets ~4000, Claude ~3000, Llama ~2000
```

### Dynamic Load Balancing
Add/remove components based on demand.

```bash
# High demand → add fast inference service
curl -X POST http://localhost:3006/components \
  -d '{"id":"fast","name":"FastInference","priority":8}'

# Low demand later → remove it
curl -X DELETE http://localhost:3006/components/fast
```

---

## Best Practices

1. **Keep priorities meaningful**
   - 9-10: Critical path (BioRenderer, primary LLM)
   - 7-8: Important (NodeEditor, fallback LLM)
   - 5-6: Nice-to-have (Governor, TeamChat)
   - 1-4: Background (logging, indexing)

2. **Test allocations before deploying**
   ```bash
   curl -X POST http://localhost:3006/allocate \
     -d '{"budget": 10000, "components": ["..."]}'
   ```

3. **Monitor component load over time**
   - Which components always get starved?
   - Which consistently get overprovisioned?
   - Adjust priorities monthly

4. **Document why priorities matter**
   - "BioRenderer=10 because scientific accuracy > speed"
   - "TeamChat=6 because collaborative context is nice-to-have"

---

## Maintenance

See **PLAY_MAINTENANCE_GUIDE.md** for:
- Weekly health checks
- Monthly cost reconciliation
- Quarterly rebalancing
- Known issues + fixes

---

**Built for:** You. Your product. Your rules.
**Status:** Production-ready. Dynamic. Yours to own.

---

*Last updated: 2026-03-06 04:15 UTC*
