# Play Token Mapper — Maintenance & Sustainability

You own this now. It's unique. It's hard to maintain. Here's how to survive it.

---

## 🎬 What Play Does (Simple Version)

```
Prompt (500 tokens) 
  ↓
Allocate: 250→BioRenderer, 150→NodeEditor, 100→Governor  
  ↓
Track cost + forecast budget  
  ↓
Return allocation plan
```

---

## ⚠️ What Will Break (Ranked by Pain)

### CRITICAL (Monthly)
**Token allocation drift**
- priorities hardcoded (BioRenderer=9, NodeEditor=8, Governor=7, TeamChat=6)
- If real-world allocation changes → must edit src/main.rs
- No config file = manual rebuild every time
- **Fix:** Move priorities to YAML config (2 hours)

**Cost tracking divergence**
- cost_per_token hardcoded (0.001, 0.0008, 0.0005, 0.0005)
- Real API costs change monthly
- Forecasts become wrong
- **Fix:** Update costs monthly from API bills (15 min)

**Memory leak from allocation history**
- Each prompt = new record in Vec<>
- 100 prompts/day × 30 days = 3000 records in memory
- No cleanup ever
- **Fix:** Add SQLite + TTL policy (4 hours) OR clean up manually

### HIGH (Quarterly)
**New components can't be added dynamically**
- Want to add "Atlas" component? Edit Cargo.toml, rebuild, redeploy
- 30 min+ per new component
- **Fix:** Move components to database (6 hours)

**Service discovery hardcoded**
- All 7 services on fixed ports (3000, 3001, 3002...)
- Move Session Server to 3100? Play still tries 3000
- **Fix:** Service registry (Consul/Eureka) = 2 days work OR simple .env file (1 hour)

### MEDIUM (Yearly)
**Allocation algorithm fairness**
- Assumes equal tokens/component
- Reality: BioRenderer uses 60%, others use 40%
- Over time, unfair allocation = user complaints
- **Fix:** Add weighted allocation model (8 hours)

---

## 📋 Weekly Checklist (10 minutes)

```bash
# 1. Services still running?
for port in 3000 3001 3002 3003 3004 3005 3006; do
  echo "Port $port: $(curl -s http://localhost:$port/health || echo 'DOWN')"
done

# 2. Quick allocation test
curl -s -X POST http://localhost:3006/allocate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "test",
    "total_budget": 1000,
    "components": ["biorenderer", "nodeeditor", "governor"]
  }' | jq '.allocations'
```

---

## 💰 True Maintenance Cost

| Task | Frequency | Time | Notes |
|------|-----------|------|-------|
| Health checks | Weekly | 10 min | Run curl tests |
| Cost reconciliation | Monthly | 30 min | Check bills vs forecast |
| Component tuning | Quarterly | 2 hours | Rebalance priorities |
| Bug fixes | Ad-hoc | 1-4 hours | When users report issues |
| New component onboarding | Yearly | 1-2 hours | Add to system |

**Total: 10-15 hours/month or ~0.25 FTE**

---

## 🚨 Critical Issues & Fixes

### Issue: Allocation unfair (one component starves)
```rust
// Current (broken):
let allocated = (remaining * priority as f64 / 100.0) as usize;

// Fixed:
let priority_sum: u8 = sorted.iter().map(|c| c.priority).sum();
let share = (remaining as f64 * component.priority as f64 / priority_sum as f64) as usize;
```

### Issue: Play crashes, loses all allocation history
**Temporary:** Restart service (state rebuilds)
**Permanent:** Add SQLite persistence (4 hours work)

### Issue: Forecasts wrong (say $10/day, bill $50/day)
1. Check: `curl http://localhost:3006/forecast` 
2. Compare to actual API usage
3. Update cost_per_token in source code
4. Rebuild: `cargo build --release`
5. Restart service

---

## 🎯 Sustainability Roadmap

**Month 1 (NOW):** Accept the burden, run weekly health checks  
**Month 2:** Move costs to config file (not hardcoded)  
**Month 3:** Add SQLite persistence  
**Month 6:** Add service registry (auto-discover session server, etc.)  
**Month 12:** Consider outsourcing to managed service

---

## 💡 If It Becomes Unbearable

**Option A:** Simplify
- Remove dynamic allocation → fixed split (25% each)
- Remove forecasting → just track actuals
- 80% less code to maintain

**Option B:** Hire help
- $500-1000/month junior dev (10 hrs/month)
- They handle maintenance, you run product

**Option C:** Managed service
- AWS Lambda + DynamoDB
- Scales automatically, no maintenance
- Cost: +$100-200/month

---

**Reality check:** Your situation is common. Many products are hard to maintain. The key is *accepting* the burden and *budgeting* for it.

You're not alone.
