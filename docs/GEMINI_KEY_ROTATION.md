# GEMINI KEY ROTATION — Operational Playbook
> For Rex · 2026-02-26 · Автоматизация ротации ключей Gemini CLI

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
