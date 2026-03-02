# Brain Portability + Continuity (Local-First)

Goal: move "brains" between machines without losing live continuity.

## 1) Invariants

1. Event order is the source of truth (`relay_chain.jsonl` seq).
2. Work state is transactional (`data/tasks.db` in SQLite WAL).
3. Compact memory feed is regenerated before handoff (`opera/memory/FEED.compact`).
4. Every portability bundle is hash-verifiable.
5. Restore starts from cursor (`relay_chain_seq`, task statuses), not from prose.

## 2) One-command bundle

```bash
./rhea continuity pack --label daily
```

Output:
- `archive/continuity_capsules/brain-capsule-*.tar.gz`
- same file `.sha256`
- `archive/continuity_capsules/LATEST.json`

## 3) Verify bundle integrity

```bash
./rhea continuity verify archive/continuity_capsules/brain-capsule-YYYYMMDDTHHMMSSZ-daily.tar.gz
```

Pass criteria:
- `ok: true`
- `checked == files_count`
- no `hash_mismatch` / `missing`

## 4) Live continuity cursor (cheap pulse)

```bash
./rhea continuity report
```

Key fields:
- `relay_chain_seq`
- `relay_mailbox_seq`
- `tasks.status` (`claimed/open/done/blocked`)

## 5) Cloud policy (0-cost discipline)

- Keep full long-term logs on the main machine.
- Push only continuity capsules to cloud object storage on schedule.
- Use lifecycle pruning (e.g. keep daily for 14 days, weekly for 8 weeks).
- Keep cloud CPU on-demand only (no always-on heavy workers).

This keeps cost low while preserving deterministic restart points.

