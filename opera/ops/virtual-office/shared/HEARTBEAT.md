# Heartbeat Checklist
> Runs every 30 minutes | Returns HEARTBEAT_OK if nothing needs attention
> OpenClaw pattern (ADR-015) | Smart suppression: only P0/P1 escalate

## Health Checks (cheap, run always)
- [ ] `docs/state.md` exists and < 2048 bytes
- [ ] Last `git push` within 30 minutes
- [ ] No unread P0/P1 relay messages in `opera/ops/virtual-office/inbox/`
- [ ] `scripts/rhea/check.sh` passes (invariants)
- [ ] No orphan processes (carbonyl, watcher leaks)

## Provider Checks (run every 2nd heartbeat)
- [ ] `python3 src/rhea_bridge.py status` — at least 1 provider alive
- [ ] Tribunal API responsive: `curl -s localhost:8400/health`

## Agent Checks (run every 3rd heartbeat)
- [ ] Task queue: no tasks blocked > 2 hours
- [ ] Outbox: no unread messages > 1 hour old
- [ ] Governor: no agent in "red" pace

## Escalation Rules
- P0 (immediate): API down, state.md overflow, git push > 60 min overdue
- P1 (notify): Provider dead, task blocked > 2h, agent red
- P2 (batch): Outbox unread, minor warnings
- P3 (log only): Info, stats, performance metrics
