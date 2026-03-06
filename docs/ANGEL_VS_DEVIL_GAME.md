# Angel vs Devil Game — Stage 6 Concept

**From:** User conversation (2026-03-06, context lost in stateless session)  
**Purpose:** Write it down so it doesn't get lost again

---

## The Game

Two AI models play **decision reasoning battle** each day:

- **Angel Model:** Picks decisions that are clear, aligned, reversible, evidence-based
- **Devil Model:** Picks decisions that are contradictory, irreversible, poorly reasoned

### Scoring
Same 4 dimensions as Angel Game (Single-player):
1. **Clarity** — How well explained?
2. **Alignment** — Consistent with values?
3. **Reversibility** — Can we undo it if wrong?
4. **Evidence** — Based on facts or feelings?

### Winner
Model with higher total score wins that day's round.

### Daily Schedule
- Morning: Present same decision to both models
- Models choose their position (Angel or Devil)
- Both explain their reasoning
- Score both positions
- Declare winner
- Log results to leaderboard

---

## Why This Works for AI Testing

### For AI Developers
"Which model reasons better?" → Run it daily, watch patterns emerge

### For Users
"Let me see GPT-4 vs Claude on reasoning" → Visual leaderboard, daily new matchups

### For Rhea
Built-in evaluation framework. Every day = new training data on which models think clearly.

---

## How to Build (Stage 6)

### 1. Create `/eval/pvp` endpoint in Angel Game
```http
POST /eval/pvp
{
  "decision_id": "...",
  "context": "...",
  "model_a": "gpt-4",
  "model_b": "claude-3"
}
```

### 2. Call both models for same decision
```python
angel_response = model_a.eval(decision)  # Pick Angel position
devil_response = model_b.eval(decision)  # Pick Devil position
```

### 3. Score both
```
angel_score = (clarity + alignment + reversibility + evidence) / 4
devil_score = (clarity + alignment + reversibility + evidence) / 4
winner = "gpt-4" if angel_score > devil_score else "claude-3"
```

### 4. Store results
```sql
CREATE TABLE pvp_results (
  id UUID,
  date DATE,
  decision_id UUID,
  model_a TEXT,
  model_b TEXT,
  model_a_score FLOAT,
  model_b_score FLOAT,
  winner TEXT,
  created_at TIMESTAMP
);
```

### 5. Leaderboard
```
Daily PvP Leaderboard:
1. gpt-4        +3 (wins/losses)
2. claude-3     +1
3. llama-2      -2
```

---

## UI (Dashboard Stage 5.5)

### New tab: "Arena"
```
┌─────────────────────────────────┐
│ Today's Decision                │
│ "Should we migrate to Rust?"   │
├─────────────────────────────────┤
│                                 │
│  GPT-4 (Angel)    Claude (Devil)│
│  ★★★★★ 8.2       ★★★★☆ 7.1    │
│                                 │
│  Winner: GPT-4 +1 point         │
├─────────────────────────────────┤
│ Leaderboard (This Week)         │
│ 1. GPT-4:    +8 wins            │
│ 2. Claude:   +5 wins            │
│ 3. Llama:    -1 wins            │
└─────────────────────────────────┘
```

---

## Data Pipeline

### Daily Job (Cron)
```bash
# At 9 AM every day:
0 9 * * * curl -X POST /eval/daily-pvp
```

### Decision Pool
- Use existing decision test set
- Rotate through them
- Or generate new ones via LLM

### Archive
All results stored in database for:
- Leaderboard over time
- Model comparison studies
- Reasoning pattern analysis

---

## Stage 6+ Milestones

- [ ] Add `/eval/pvp` endpoint
- [ ] Hook into Play Token Mapper (track which models used)
- [ ] Create "Arena" tab in dashboard
- [ ] Set up daily cron job
- [ ] Build leaderboard visualization
- [ ] Export results for ML research

---

## Notes

**Why Angel vs Devil?**
- Memorable metaphor
- Forces models to argue both sides
- Shows reasoning quality clearly

**Why Daily?**
- Gamification (leaderboard changes daily)
- Trends emerge (which model getting better?)
- Enough data for analysis

**Why This Matters?**
- Most AI evals are static benchmarks
- This is dynamic, reasoning-focused
- Shows actual thinking, not just memorization

---

**Status:** Documented for next session. Won't be forgotten now.
