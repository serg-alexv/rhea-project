# Session Context

**Session ID:** 94aabe90-9b2d-48e7-be8c-6bf820a0b6a9

**Commit Message:** Но есть нюанс: я не плачу эти $10, они как-то уходят с лимита подписки.

## Prompt

но есть нюанс: я не плачу эти $10, они как-то уходят с лимита подписки.

## Summary

"Зверь бежит. Бюджет дышит, трафик растёт."

Rex green, 641K tokens, floor gap = 0 (далеко выше минимума). Shadow cost $25 — для видимости, не для паники.

`★ Insight ─────────────────────────────────────`
**Subscription vs API-billed — разные рельсы.** Rex (подписка) и Orion/Gemini (API) требуют принципиально разного governance. Подписка = лимит использования, невидимый снаружи. API = каждый токен = центы. Губернатор теперь разделяет: subscription agents проверяют только floor (ты работаешь?), API agents — dual rail (не переплати + не простаивай).

Shadow cost ($25) всё равно полезен: если Anthropic когда-то даст billing API — подключим за 5 строк.
`─────────────────────────────────────────────────`

## Key Actions

- - **Read**: /Users/sa/rh.1/src/token_governor.py
- - **Edit**: /Users/sa/rh.1/src/token_governor.py
- - **Read**: /Users/sa/rh.1/src/token_governor.py
- - **Edit**: /Users/sa/rh.1/src/token_governor.py
- - **Bash**: Test governor with subscription model for Rex
- - **Bash**: Final Rex governor status
