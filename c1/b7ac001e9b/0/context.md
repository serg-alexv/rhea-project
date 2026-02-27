# Session Context

**Session ID:** 94aabe90-9b2d-48e7-be8c-6bf820a0b6a9

**Commit Message:** В одном случае -- для Opus, в другом -- для Gemini-2.5-lite -- который д

## Prompt

в одном случае -- для Opus, в другом -- для Gemini-2.5-lite -- который даже в cli не умеет

## Summary

Вот и proof зачем нужен compress bridge. Кто-то (или ты, или предыдущая сессия) вкинул raw base64 blob прямо в промпт Opus → **AUP refusal**. Антропик фильтр увидел гигантский бинарный блоб и заблокировал как policy violation.

Это именно тот кейс: нельзя скормить картинку текстовому Opus напрямую через терминал. Нужен промежуточный слой — дешёвая vision-модель (Qwen/Gemini Flash) смотрит картинку → выдаёт текст → текст идёт Opus.

`rhea_vision_check.py` это и делает. Запустить на скриншоте?

## Key Actions

- - **Edit**: /Users/sa/rh.1/src/rhea_vision_check.py
