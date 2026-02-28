# Family Workflow (Shared Context Ring)

Date: 2026-02-28  
Owner: ORION  
Status: ACTIVE

## Goal
Make one user message visible to all core agents by default, with delivery status.

Ring members:
- REX
- ORION
- HYPERION

## Commands
```bash
# 1) Send once to full ring
bash scripts/rhea.sh family send "P0: what I write to Rex must be visible to Orion and Hyperion too"

# 2) Check latest delivery/ack status
bash scripts/rhea.sh family status

# 3) Check explicit family id
bash scripts/rhea.sh family status fam-20260228-140000-abcd

# 4) Show recent fanout messages
bash scripts/rhea.sh family tail -n 20
```

## Behavior
- Each fanout message gets correlation tag: `[FAMILY:<family-id>]`.
- The same payload is relayed to all ring targets.
- Status view reports per-target message id/seq and ack state.

## Rule
For coordination-critical instructions, use `family send` instead of single-target messages.
