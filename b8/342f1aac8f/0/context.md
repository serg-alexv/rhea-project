# Session Context

**Session ID:** 94aabe90-9b2d-48e7-be8c-6bf820a0b6a9

**Commit Message:** Выбирай я. а я хочу видеть гарфик каждый день в режиме live/log -- кто с

## Prompt

выбирай я. а я хочу видеть гарфик каждый день в режиме live/log -- кто сколько агентских токенов потратил. если ты закончился раньше, чем все агееты -- понижение в программисты, кодь себе на здоровье всю жизнь

## Summary

Данные за вчера. Gemini сжёг 88.7% (94K токенов), Orion 9.6% (10K), Rex — 0 (все 32 вызова Anthropic упали с ошибкой авторизации).

`python3 scripts/token_burn.py --live` — обновляется каждые 10 секунд, выводит в терминал + пишет JSON в `opera/metrics/token_burn.json`.

Rex'овы собственные токены (Claude Code сессия) в bridge_calls не попадают — это отдельный биллинг Anthropic. Dashboard показывает только то, что Rex **диспатчит** другим через bridge. Чтобы трекать Rex'а самого, нужен хук на Claude Code API usage — или внешний скрипт, который дёргает Anthropic billing API.

## Key Actions

- - **Task**: Explore token tracking infrastructure
- - **Write**: /Users/sa/rh.1/scripts/token_burn.py
- - **Bash**: Show yesterday's token burn by agent
