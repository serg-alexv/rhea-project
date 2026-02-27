# Session Context

**Session ID:** 94aabe90-9b2d-48e7-be8c-6bf820a0b6a9

**Commit Message:** Да, потому мы должны уделять внимание well-writed full actual docs, desr

## Prompt

да, потому мы должны уделять внимание well-writed full actual docs, desriptive and friendly-short;

## Summary

Починено. Два режима:
- `python3 src/rhea_vision_check.py img.png` — один дешёвый vision → описание для Opus
- `python3 src/rhea_vision_check.py img.png --for gemini-2.5-flash-8b` — описание для слабой модели
- `python3 src/rhea_vision_check.py img.png --invariance` — все модели, сравнение

Docstring актуальный, баг с `INVARIANCE_PROMPT` убран.

## Key Actions

- - **Read**: /Users/sa/rh.1/src/rhea_vision_check.py
- - **Write**: /Users/sa/rh.1/src/rhea_vision_check.py
