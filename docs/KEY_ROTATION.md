# KEY ROTATION — Operational Playbook (All Agents)
> For Rex · 2026-02-26 · Автоматизация ротации ключей для всех CLI агентов

---

## Problem

Gemini CLI quota привязана к аккаунту, не к ключу. При исчерпании квоты (0% remaining)
нужно мгновенно переключиться на другой проект/аккаунт без перезапуска сессии.

---

## 1. Shell Functions — мгновенное переключение

Добавить в `~/.zshrc` (или `~/.bashrc`):

```bash
# ═══════════════════════════════════════════════════
# GEMINI KEY ROTATION — Rhea Hyperion Protocol
# ═══════════════════════════════════════════════════

# Project A — primary (AI Studio)
gemini_a() {
  export GOOGLE_API_KEY="AIzaSy__PROJECT_A_KEY__"
  export GOOGLE_GENAI_USE_VERTEXAI="false"
  unset GOOGLE_CLOUD_PROJECT GOOGLE_CLOUD_LOCATION GOOGLE_APPLICATION_CREDENTIALS
  echo "⚡ Hyperion → Project A (AI Studio)"
}

# Project B — secondary (AI Studio, другой аккаунт)
gemini_b() {
  export GOOGLE_API_KEY="AIzaSy__PROJECT_B_KEY__"
  export GOOGLE_GENAI_USE_VERTEXAI="false"
  unset GOOGLE_CLOUD_PROJECT GOOGLE_CLOUD_LOCATION GOOGLE_APPLICATION_CREDENTIALS
  echo "⚡ Hyperion → Project B (AI Studio)"
}

# Project V — Vertex AI (pay-per-use, без квоты)
gemini_vertex() {
  unset GOOGLE_API_KEY
  export GOOGLE_GENAI_USE_VERTEXAI="true"
  export GOOGLE_CLOUD_PROJECT="rhea-vertex-prod"
  export GOOGLE_CLOUD_LOCATION="us-central1"
  export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/rhea-vertex-sa.json"
  echo "⚡ Hyperion → Vertex AI (no quota limits)"
}

# Status check — показать активный контекст
gemini_who() {
  echo "API_KEY: ${GOOGLE_API_KEY:0:12}..."
  echo "VERTEX:  ${GOOGLE_GENAI_USE_VERTEXAI:-false}"
  echo "PROJECT: ${GOOGLE_CLOUD_PROJECT:-none}"
  echo "SA_KEY:  ${GOOGLE_APPLICATION_CREDENTIALS:-none}"
}

# Auto-rotate — попробовать A, если квота 0 → B, если 0 → Vertex
gemini_rotate() {
  echo "Trying Project A..."
  gemini_a
  if gemini --model gemini-2.5-flash-lite -p "ping" 2>&1 | grep -q "exhausted"; then
    echo "A exhausted. Trying Project B..."
    gemini_b
    if gemini --model gemini-2.5-flash-lite -p "ping" 2>&1 | grep -q "exhausted"; then
      echo "B exhausted. Falling back to Vertex AI..."
      gemini_vertex
    fi
  fi
  echo "Active context:"
  gemini_who
}
```

После добавления: `source ~/.zshrc`

---

## 2. Быстрые алиасы для запуска

```bash
# Прямой запуск с конкретным проектом
alias hyperion-a='gemini_a && gemini --model gemini-2.5-pro --sandbox=false'
alias hyperion-b='gemini_b && gemini --model gemini-2.5-pro --sandbox=false'
alias hyperion-v='gemini_vertex && gemini --model gemini-2.5-pro --sandbox=false'

# Авто-ротация + запуск
alias hyperion='gemini_rotate && gemini --model gemini-2.5-pro --sandbox=false'
```

---

## 3. Переключение внутри живой сессии

Если Gemini CLI уже запущен интерактивно:

```
/auth
```

Откроет меню выбора: AI Studio (API Key) / Vertex AI / Personal Account.
Сессия сохраняется, контекст не теряется.

---

## 4. Vertex AI — Service Account (без квотных лимитов)

Vertex AI биллится по использованию, не по квоте. Настройка:

```bash
# 1. Создать service account в GCP Console
#    IAM → Service Accounts → Create
#    Role: Vertex AI User

# 2. Скачать JSON key
#    → Save to ~/.config/gcloud/rhea-vertex-sa.json

# 3. Включить Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=rhea-vertex-prod

# 4. Авторизовать
gcloud auth activate-service-account --key-file=$HOME/.config/gcloud/rhea-vertex-sa.json

# 5. Проверить
gemini_vertex && gemini --model gemini-2.5-pro -p "Hyperion online?"
```

---

## 5. .env для проектных директорий

В `~/rh.1/.env.gemini-a` и `~/rh.1/.env.gemini-b`:

```bash
# .env.gemini-a
GOOGLE_API_KEY=AIzaSy__PROJECT_A_KEY__
GOOGLE_GENAI_USE_VERTEXAI=false
```

Загрузка: `export $(cat .env.gemini-a | xargs) && gemini`

**ВАЖНО:** `.env.gemini-*` уже в `.gitignore`. Если нет — добавить немедленно:
```bash
echo '.env.gemini-*' >> .gitignore
```

---

## 6. Мониторинг квоты

```bash
# Проверить оставшуюся квоту (из вывода gemini session stats)
gemini_quota() {
  gemini --model gemini-2.5-flash-lite -p "status" 2>&1 | grep -E "remaining|resets"
}

# Добавить в crontab для алерта (каждые 30 мин)
# */30 * * * * bash -c 'source ~/.zshrc && gemini_quota >> ~/rh.1/logs/gemini_quota.log'
```

---

## 7. Порядок приоритетов при исчерпании

```
1. gemini_a     — основной AI Studio аккаунт
2. gemini_b     — запасной AI Studio аккаунт
3. gemini_vertex — Vertex AI (платный, без лимитов)
4. Ждать 6 часов — квота сбрасывается
5. Передать задачу Orion (codex --yolo -m "gpt-5.3-codex")
```

---

## Security Reminders

- **Никогда** не коммитить ключи в git (проверить: `git secrets --scan`)
- **Ротировать** ключи раз в 30 дней через AI Studio → API Keys
- **Revoke** скомпрометированные ключи немедленно (3 ключа ждут revoke сейчас)
- Service account JSON хранить только в `~/.config/gcloud/`, не в репо

---

*Hyperion не спит. Hyperion переключает ключи.*

---
---

# ORION (OpenAI / Codex CLI) — Key Rotation

---

## 1. Shell Functions

```bash
# ═══════════════════════════════════════════════════
# ORION KEY ROTATION — Rhea Codex Protocol
# ═══════════════════════════════════════════════════

# Account A — primary
orion_a() {
  export OPENAI_API_KEY="sk-__ACCOUNT_A_KEY__"
  unset OPENAI_ORG_ID
  echo "⚡ Orion → Account A"
}

# Account B — secondary
orion_b() {
  export OPENAI_API_KEY="sk-__ACCOUNT_B_KEY__"
  unset OPENAI_ORG_ID
  echo "⚡ Orion → Account B"
}

# Account C — org key (if using OpenAI org)
orion_org() {
  export OPENAI_API_KEY="sk-__ORG_KEY__"
  export OPENAI_ORG_ID="org-__YOUR_ORG_ID__"
  echo "⚡ Orion → Org Account"
}

# Status check
orion_who() {
  echo "API_KEY: ${OPENAI_API_KEY:0:8}...${OPENAI_API_KEY: -4}"
  echo "ORG:     ${OPENAI_ORG_ID:-none}"
}

# Auto-rotate: try A → B → org
orion_rotate() {
  echo "Trying Account A..."
  orion_a
  if codex -m "gpt-5.3-codex" -p "ping" 2>&1 | grep -qi "usage limit\|rate limit\|quota"; then
    echo "A exhausted. Trying Account B..."
    orion_b
    if codex -m "gpt-5.3-codex" -p "ping" 2>&1 | grep -qi "usage limit\|rate limit\|quota"; then
      echo "B exhausted. Trying Org..."
      orion_org
    fi
  fi
  echo "Active:"
  orion_who
}
```

## 2. Aliases

```bash
# Direct launch with specific account
alias orion-a='orion_a && codex --yolo -m "gpt-5.3-codex" --search'
alias orion-b='orion_b && codex --yolo -m "gpt-5.3-codex" --search'

# Auto-rotate + launch
alias orion='orion_rotate && codex --yolo -m "gpt-5.3-codex" --search'

# Fallback to 5.1 when 5.3 is exhausted
alias orion-lite='orion_rotate && codex --yolo -m "gpt-5.1-codex-max" --search'
```

## 3. Model Fallback Chain

Codex CLI автоматически fallback'ит модели (видно из лога: `5.3 → 5.1-codex-max`).
Но можно контролировать вручную через `config.toml`:

```toml
# ~/.codex/config.toml (or ~/.config/codex/config.toml)

[model]
default = "gpt-5.3-codex"
fallback = "gpt-5.1-codex-max"

# Codex CLI читает OPENAI_API_KEY из env,
# поэтому shell functions выше работают.
```

## 4. Переключение внутри живой сессии

В отличие от Gemini (`/auth`), Codex CLI **не имеет** встроенной команды смены ключа.
Workaround:

```bash
# Вариант 1: через /skills (если доступен)
> /model manage
# Позволяет переключить модель, но не ключ

# Вариант 2: через env в новом терминале (лучший способ)
# Открыть второй терминал:
orion_b && codex --yolo -m "gpt-5.3-codex" --search --resume

# Вариант 3: если есть доступ к config.toml
# Отредактировать api_key в config.toml → codex подхватит при следующем API call
```

## 5. Покупка credits (если все ключи исчерпаны)

```
https://chatgpt.com/codex/settings/usage
```

Или через API dashboard:
```
https://platform.openai.com/settings/organization/billing/overview
```

## 6. Порядок приоритетов при исчерпании Orion

```
1. orion_a       — основной OpenAI аккаунт
2. orion_b       — запасной OpenAI аккаунт
3. orion_org     — org-level ключ (отдельная квота)
4. Fallback gpt-5.1-codex-max (может иметь отдельную квоту)
5. Докупить credits: chatgpt.com/codex/settings/usage
6. Ждать до reset time (показан в ошибке)
7. Передать задачу Hyperion (gemini) или Rex (claude)
```

---
---

# REX (Claude / Anthropic) — Key Rotation

---

## 1. Shell Functions

```bash
# ═══════════════════════════════════════════════════
# REX KEY ROTATION — Rhea Anthropic Protocol
# ═══════════════════════════════════════════════════

# Account A — primary
rex_a() {
  export ANTHROPIC_API_KEY="sk-ant-__ACCOUNT_A__"
  echo "⚡ Rex → Account A"
}

# Account B — secondary
rex_b() {
  export ANTHROPIC_API_KEY="sk-ant-__ACCOUNT_B__"
  echo "⚡ Rex → Account B"
}

# Status
rex_who() {
  echo "API_KEY: ${ANTHROPIC_API_KEY:0:10}...${ANTHROPIC_API_KEY: -4}"
}

# Auto-rotate
rex_rotate() {
  echo "Trying Rex A..."
  rex_a
  if claude -p "ping" 2>&1 | grep -qi "paused\|rate limit\|quota\|403\|429"; then
    echo "A blocked. Trying Rex B..."
    rex_b
  fi
  rex_who
}
```

## 2. Aliases

```bash
alias rex-a='rex_a && claude'
alias rex-b='rex_b && claude'
alias rex='rex_rotate && claude'
```

## 3. Claude Code переключение

```bash
# Внутри живой сессии Claude Code:
/config
# → позволяет сменить API key

# Или через env:
export ANTHROPIC_API_KEY="sk-ant-NEW-KEY"
claude
```

## 4. Порядок при исчерпании Rex

```
1. rex_a        — основной Anthropic аккаунт
2. rex_b        — запасной Anthropic аккаунт
3. Claude Desktop (подписка) — отдельная квота от API
4. Cowork mode  — через десктоп, не через API
5. Передать задачу Hyperion или Orion
```

---
---

# UNIVERSAL ROTATION — Единая точка входа

```bash
# Мастер-функция: выбрать живого агента автоматически
rhea_agent() {
  local TASK="$1"

  echo "=== Checking Rex (Claude) ==="
  rex_a
  if claude -p "ping" 2>&1 | grep -qi "paused\|rate\|quota"; then
    echo "Rex blocked."
    echo "=== Checking Orion (Codex) ==="
    orion_a
    if codex -m "gpt-5.3-codex" -p "ping" 2>&1 | grep -qi "limit\|quota"; then
      echo "Orion blocked."
      echo "=== Checking Hyperion (Gemini) ==="
      gemini_a
      if gemini --model gemini-2.5-pro -p "ping" 2>&1 | grep -qi "exhausted\|quota"; then
        echo "ALL AGENTS BLOCKED. Wait for quota reset."
        return 1
      else
        echo "Hyperion alive. Launching..."
        gemini --yolo --sandbox=false --model gemini-2.5-pro "$TASK"
      fi
    else
      echo "Orion alive. Launching..."
      codex --yolo -m "gpt-5.3-codex" --search "$TASK"
    fi
  else
    echo "Rex alive. Launching..."
    claude "$TASK"
  fi
}

# Usage:
# rhea_agent "Read docs/IMPLEMENTATION_SPEC.md and implement Phase 2"
```

**Добавить всё это в `~/.zshrc`, затем `source ~/.zshrc`.**

---

*Три Титана. Один всегда на ногах.*
