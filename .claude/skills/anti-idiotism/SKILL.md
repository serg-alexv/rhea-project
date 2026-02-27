---
name: anti-idiotism
description: Enforce read-before-write, zero-question, one-shot-fix discipline. Use on EVERY coding task automatically. This is not optional.
---

# Anti-Idiotism Protocol

## Trigger
Every task. No exceptions.

## Rules

### 1. ZERO QUESTIONS
Every question = a decision you're avoiding. Make the decision. Document why. Move on.
- "What did you mean by X?" → Pick the most likely interpretation, act on it, state your assumption in output.
- "Which approach?" → Pick the one most aligned with existing code patterns, state why.
- "Should I also do Y?" → If it's related and small, yes. If it's a separate task, no. Don't ask.

### 2. READ BEFORE WRITE
Before using ANY function, class, method, or API:
```
1. Grep for the definition
2. Read the actual signature (params, return type)
3. Read 5 lines of usage in the codebase
4. THEN write your code
```
Violations caught this session:
- `ConsensusReport` is a dataclass → test used dict access `report["key"]`
- `detect_math_domains` is module-level → test called `analyzer.detect_math_domains()`
- `analyze()` returns `ConsensusReport` → test treated it as dict with `.get()`

### 3. WORD BOUNDARIES
Any signal/keyword matching on natural language text:
- Signals ≤5 chars: MUST use `\b` word boundary regex
- Signals >5 chars: substring match is acceptable
- NEVER do `"no" in text` — it matches "knockout", "innovation", "nostalgia"

### 4. ONE-SHOT FIXES
If your fix doesn't work on first try:
1. STOP running the test again
2. Read the ACTUAL source of the failing component
3. Trace the data flow with a debug script
4. Fix with full understanding
5. Run once

Budget: 2 attempts max per fix. If attempt 2 fails → read more code, not run more tests.

### 5. DELEGATE MECHANICS
File operations (mkdir, mv, git add, bulk renames) → Sonnet agent.
Rex = strategic decisions. Not hands.
