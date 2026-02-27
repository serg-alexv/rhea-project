# Session Context

**Session ID:** 94aabe90-9b2d-48e7-be8c-6bf820a0b6a9

**Commit Message:** Как это сделать

## Prompt

как это сделать?

## Summary

Вот механизм. `Dispatcher.assign("orion", objective=..., contract_path=..., code_files=[...])` → Rex вызывает GPT-5.3 через bridge API → получает unified diff → проверяет acceptance test → применяет или отбрасывает.

```python
d = Dispatcher()

# Rex dispatches to both pyramids in parallel
results = d.assign_parallel([
    {
        "agent": "orion",
        "objective": "Port consensus to TypeScript with same API shape",
        "contract_path": "contracts/consensus_to_aletheia.py",
        "code_files": ["src/consensus_analyzer.py"],
    },
    {
        "agent": "gemini",
        "objective": "Add stemming to _tokenize() — vendor Snowball, no deps",
        "contract_path": "contracts/consensus_to_aletheia.py",
        "code_files": ["src/consensus_analyzer.py"],
    },
])
```

Rex нажимает кнопки через `bridge.ask()`. Тот же HTTP call что для tribunal. Orion и Gemini не знают что ими управляет другая модель — для них это просто промпт. Но промпт содержит контракт, код и acceptance criteria.

Когда GPT-5.3 и Gemini 3.1 получат полноценные agent API (Codex swarm, Jules swarm) — `AGENT_MODELS` обновится, dispatch начнёт вызывать agent endpoint вместо completion. Dispatcher не меняется. Контракт не меняется.

## Key Actions

- - **Read**: /Users/sa/rh.1/src/rhea_bridge.py
- - **Write**: /Users/sa/rh.1/contracts/dispatch.py
