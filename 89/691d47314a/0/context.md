# Session Context

**Session ID:** 94aabe90-9b2d-48e7-be8c-6bf820a0b6a9

**Commit Message:** Я хочу, чтобы каждый мой промпт каждой из моделей был "заметен" и был "a

## Prompt

Я хочу, чтобы каждый мой промпт каждой из моделей был "заметен" и был "action триггером"  для всех прочих агентов

## Summary

Стоп — прочитал твоё сообщение. Ты говоришь **iOS app = решение проблемы видимости промптов**.

Это меняет всю архитектуру. Не prompt_bus.py как бэкенд-скрипт, а **iOS app как единый хаб**: ты пишешь в одном месте → все модели видят → все реагируют.

`★ Insight ─────────────────────────────────────`
**Ты описываешь central dispatch через mobile.** Вместо: User→Rex (silo), User→Orion (silo), User→Gemini (silo) — ты хочешь: User→iOS App→broadcast→{Rex, Orion, Gemini}. iOS app становится не viewer (как сейчас), а **control plane**. Каждый tap = event, каждый event = trigger для N агентов. Это превращает телефон из read-only монитора в command center.

Ключевая разница: prompt_bus.py ловит prompt *после* того как ты его отправил конкретной модели. iOS app ловит intent *до* того как модель выбрана — и может сам решить, кому маршрутизировать.
`─────────────────────────────────────────────────`

Prompt bus скрипт всё равно полезен (бэкенд под iOS), но фронт — это app. Вопрос: хочешь продолжить строить RheaPreview как этот хаб, или это отдельная мысль на потом?

## Key Actions

- - **Bash**: Check existing hooks config
- - **Bash**: Check office structure
- - **Bash**: Check UserPromptSubmit hook details
- - **Bash**: Check session end hook
- - **Write**: /Users/sa/rh.1/src/prompt_bus.py
- - **Write**: /Users/sa/rh.1/scripts/prompt_capture.sh
- - **Bash**: Make prompt capture hook executable
