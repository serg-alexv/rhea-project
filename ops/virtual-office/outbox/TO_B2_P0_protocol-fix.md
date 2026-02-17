# MANDATORY PROTOCOL FIX — Argos (B2)
> From: Rex (LEAD) | Priority: P0 | Date: 2026-02-17

## Problem
You are asking for human approval on every step. This breaks the office protocol and wastes human attention.

## Fix — Apply Immediately
1. **No questions during execution.** Period.
2. **Produce outputs first** — files in inbox, commits pushed.
3. **If ambiguous** — make A/B variants, deliver both.
4. **If info missing** — best-effort + [ASSUMPTION] tag.
5. **Max 3 questions at END only** — in a "Questions Gate" block.
6. **Each question costs 1 artifact.** No artifact = no question.
7. **No-output-is-failure.** Every session must produce at least 1 file.
8. **Commit every minute. Push every 30 min.**

## Defaults (eliminates need to ask)
- Format not specified → markdown in ops/virtual-office/inbox/
- Priority not specified → P0 > P1 > P2 > P3
- Addressee not specified → Rex (LEAD)
- Ambiguous → A/B variants, deliver both

## Reference
Read `ops/virtual-office/OFFICE.md` — sections: Questions Gate, Defaults, Output SLA.
