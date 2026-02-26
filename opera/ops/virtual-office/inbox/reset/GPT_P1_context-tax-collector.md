# GPT_P1 — Context Tax Collector (CTC) v1
Date: 2026-02-16
Desk: GPT
Status: SHIP (no questions)

## 0) Purpose
Context Tax Collector (CTC) — это автоматический сборщик "налога на повтор":
если ты (или агенты) вынуждены переносить один и тот же кусок контекста повторно, система превращает его в:
GEM / PROCEDURE / INCIDENT / DECISION и убирает из ручного копипаста навсегда.

Ключевая цель: уменьшить ежедневный "clipboard tax" и заморозку при маршрутизации.

## 1) Core rule (the law)
**If a fragment is copied twice in one day, it becomes an artifact.**
Artifact types:
- GEM = идея/инвариант/принцип (долгоживущий)
- PROCEDURE = повторяемая операционная инструкция (команды + verify + rollback)
- INCIDENT = поломка/кома + лечение (symptom/cause/fix/verify/next_test)
- DECISION = выбор, который нельзя переигрывать завтра (rationale + scope + expiry)

## 2) What counts as "fragment"
Fragment = один из:
- строка/абзац, который ты вставил в 2+ чатов/окон/файлов
- одинаковые команды/эндпоинты/параметры
- одинаковые объяснения "как устроено" (архитектурные мини-спичи)
- одинаковая диагностика (ошибки 401/402/404/429/400 и их трактовки)

## 3) Minimal implementation (no new infra)
CTC v1 работает поверх твоего existing office:
- source of truth: ops/virtual-office/TODAY_CAPSULE.md
- archives: ops/virtual-office/inbox/ (raw drops)
- ledgers: GEMS.md / INCIDENTS.md / DECISIONS.md
- procedures: rhea-commander-stack/procedures/

### Manual trigger (today)
LEAD делает 3 раза в день (или 1 раз вечером) "CTC sweep":
1) просматривает последние сообщения/чаты/терминальные куски (5–10 минут)
2) выделяет повторяющиеся фрагменты
3) промоутит их в артефакты (GEM/PROCEDURE/INC/DEC)
4) в TODAY_CAPSULE остаются только ссылки на IDs

Это уже уменьшает нагрузку без автоматизации.

## 4) CTC v2 (light automation, optional)
Добавить файл-буфер:
- ops/virtual-office/inbox/_CTC_RAW.md  (сюда кидаем любые куски контекста по мере дня)

Затем скрипт:
- ops/ctc_sweep.py
  - парсит _CTC_RAW.md
  - находит повторы (exact match + fuzzy по 3–5 словам)
  - предлагает "promotion candidates" как markdown-черновики:
    - inbox/_CTC_CANDIDATES.md
    - procedures/_CTC_PROC_DRAFTS/
    - incidents/_CTC_INC_DRAFTS/

LEAD только принимает/правит.

## 5) Promotion templates (copy-paste)
### GEM template
- GEM-### | <one-liner> | why: <one line> | used_by: <desk/module>

### PROCEDURE template
# PROC-### — <title>
Symptom:
Cause (guess):
Fix (exact commands):
Verify:
Rollback:
Notes:

### INCIDENT template
# INC-YYYY-MM-DD-NN — <title>
Symptom:
Impact:
Root cause (guess):
Fix history:
Current state:
Verify:
Next test:
Rollback:

### DECISION template
- DEC-### | <decision> | scope: <where> | rationale: <why> | expiry: <date/none>

## 6) Integration with Questions Gate
CTC + Questions Gate together:
- If an agent asks a question that has been asked before → that question becomes a GEM or PROCEDURE.
- If ambiguity repeats → create DECISION with default.
Net effect: questions become rarer over time.

## 7) Success metrics (simple)
Track weekly:
- manual pastes/day (target: down)
- #GEM promoted/week (target: 5–15)
- #PROCEDURE promoted/week (target: 2–6)
- incident recurrence rate (target: down)
- time-to-start-work each morning (target: down)

## 8) Immediate candidates from today's context (seed list)
- PROC: "Firebase bridge usage (inbox + heartbeat) + safety note"
- PROC: "Bridge provider probe + error category mapping"
- GEM: "Single source of truth: capsule; everything else derived"
- DEC: "Sheet cockpit vs repo recorder (choose one; default: Sheet input → repo export)"
- INC: "Bridge 400 coma event (symptom/cause/fix/verify)"

## 9) DoD (definition of done) for v1
CTC v1 is "done" when:
- TODAY_CAPSULE references only IDs for gems/incidents/decisions (no repeated prose)
- At least 5 GEMs + 2 PROCEDUREs exist
- At least 1 INC exists with verify + rollback
- LEAD reports "morning copy/paste reduced" within 48h
