# Rhea+UI Start Here Playbook

Status: active  
Updated: 2026-02-28

Goal: convert a user question into value fast, with verifiable evidence in UI (`seq/ack/status`, task updates, or explicit outputs).

## Fast Protocol
1. Open app, pick route, enter one base query.
2. Confirm first useful output in Dialog.
3. Only then reveal extra controls (Governor/Tasks/full cockpit).

## Executable Examples

| Role | Intent | Input | Expected Output | Evidence Check |
|---|---|---|---|---|
| biochemist | Triage hypothesis | `Give 3 testable hypotheses for [target pathway] with minimal assay set.` | 3 ranked hypotheses + minimal experiments | Dialog response contains ranked list + explicit assay names |
| biochemist | Literature sprint | `Summarize strongest 5 papers on [topic], then extract disagreements.` | Structured consensus/disagreement summary | Output includes at least 5 references and contradiction section |
| biochemist | Protocol refinement | `Improve this protocol for reproducibility and failure points: ...` | Stepwise protocol with risk controls | Response includes failure modes + mitigation per step |
| biochemist | Data sanity check | `Given this readout, what are likely artifacts vs biological signal?` | Split into likely artifact vs likely signal | Output explicitly labels both classes |
| operator | P0 queue control | `List all P0 tasks, owner, blocker, next action.` | Compact action board | `Tasks` tab and/or queue output shows same IDs and owners |
| operator | Silent relay proof | `Send wake ping to REX and report seq/ack.` | Delivery metadata | Radio shows relay event with `seq` and ack/delivery state |
| operator | Incident containment | `Current top risk in system health and immediate containment.` | 1 risk + 1 containment action | Governor/flow pulse reflects new action or status |
| investor | Progress proof | `What changed in last 90 min with objective evidence?` | Diff-style changelog with concrete artifacts | Mentions file paths / task IDs / status changes visible in app |
| investor | Capacity audit | `Team token burn vs available capacity today.` | Utilization summary + bottleneck | Governor metrics and logs match reported bottleneck |
| investor | Cost mode check | `Which workloads run on subscription vs API billing now?` | Split by provider + mode | Governor or policy docs show matching mode labels |
| mixed | Share ingress | Share screenshot from iOS -> Rhea target agent | Screenshot enters relay path | Radio/Team feed shows inbound event with timestamp |
| mixed | New user onboarding | `I am new. Give me one useful thing in <30s.` | Single actionable next step | User can complete step without opening expert tabs |

## Role Defaults

- `biochemist`: reveal level `L1` (Dialog-first)
- `operator`: reveal level `L2` (+Governor +Tasks)
- `investor`: reveal level `L2` with proof-oriented prompts
- `expert`: reveal level `L3` (full cockpit)

## Anti-Overload Rules

1. One base query before cockpit.
2. One screen, one dominant action.
3. Show proof separately from reasoning text.
4. Escalate complexity by intent, not by default.
