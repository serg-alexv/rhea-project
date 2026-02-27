# Session Context

**Session ID:** 94aabe90-9b2d-48e7-be8c-6bf820a0b6a9

**Commit Message:** Какие существуют стандарты модульности, чтобы уже мост и трибунал стали

## Prompt

какие существуют стандарты модульности, чтобы уже мост и трибунал стали межплатформенными подключаемыми модулями?

## Summary

Четыре реальных стандарта, от зрелого к новому:

**1. MCP (Model Context Protocol)** — Anthropic, 2024
- JSON-RPC через stdio/SSE. Клиент↔сервер, любой язык.
- Bridge и Tribunal легко оборачиваются как MCP server: `tool` = функция, `resource` = данные.
- Уже поддерживается Claude Code, Cursor, Windsurf, VS Code.
- Ты уже используешь MCP (Chrome, Firebase плагины в settings).

**2. OpenAPI / FastAPI auto-spec**
- У тебя уже FastAPI — значит `/openapi.json` генерится автоматом.
- Любой клиент (JS, Python, Go, Swift) генерит SDK по спеке.
- Самый универсальный: REST = межплатформенный по определению.

**3. WASI Components (WebAssembly)**
- Компилируешь Python → .wasm → работает везде (browser, edge, iOS, serverless).
- Рано для продакшена, но bridge — идеальный кандидат: stateless, чистый IO.

**4. pip/PyPI пакет с namespace**
- `rhea-bridge`, `rhea-tribunal` — отдельные pip-пакеты.
- Зависимость только от `litellm` + `httpx`.
- Самый простой путь: `pip install rhea-bridge` и готово.

---

Для bridge и tribunal минимальный путь к межплатформенности:

| Слой | Как | Уже есть? |
|------|-----|-----------|
| Python пакет | pip install | Нет — нужно убрать зависимость от .env и рабочей папки |
| REST API | FastAPI + OpenAPI spec | Да — tribunal_api.py |
| MCP server | JSON-RPC wrapper | Нет — но 50 строк кода |
| JS/Swift SDK | Auto-gen от OpenAPI | Нет — но бесплатно если есть spec |

Главный блокер: `rhea_bridge.py` сейчас читает `.env` и привязан к конкретной файловой структуре. Чтобы стать модулем — нужна инициализация через конструктор (`RheaBridge(keys={...}, tiers={...})`), а не через `os.environ`.

Это одно изменение. Хочешь — сделаю прямо в rhea-min.

## Key Actions

- - **Bash**: Search for modular plugin standards
