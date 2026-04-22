# podzamkom-vk-bot

Базовый каркас в стиле Clean Architecture:

- `domain/` — сущности и контракты.
- `use_cases/` — бизнес-операции без зависимостей от транспорта/SDK.
- `infrastructure/` — реализации репозиториев, миграций БД, логгера, конфигурации и composition root (`bootstrap.py`).
- `interfaces/` — входные адаптеры (точка входа VK callback handler).

## Быстрый запуск

1. Скопируйте шаблон окружения:

```bash
cp .env.example .env
```

2. Заполните `.env` своими значениями секретов.

3. Запустите приложение:

```bash
python3 main.py
```

Приложение автоматически читает `.env` при старте (если файл существует).

При старте приложения автоматически выполняются SQL-миграции из `infrastructure/db/migrations` в SQLite-базу из `DB_PATH`.

Если обязательные ENV отсутствуют, приложение завершится с понятной ошибкой (`Configuration error: Missing required environment variables: ...`).

## Временный callback endpoint для подтверждения VK (ngrok)

Для теста подтверждения сервера можно поднять временный HTTP endpoint:

```bash
python3 run_callback_server.py
```

Endpoint'ы:
- `POST /callback` — входной callback от VK.
- `GET /health` — health-check (`ok`).

Дальше можно открыть туннель, например через ngrok:

```bash
ngrok http 8000
```

И в VK Callback API указать адрес:
- `https://<ваш-ngrok-домен>/callback`

После нажатия «Подтвердить» VK пришлёт событие `confirmation`, а сервер вернёт `VK_CONFIRMATION_CODE`.

> Да, endpoint можно удалить после подтверждения. Но тогда сервер перестанет принимать реальные callback-события. Обычно его оставляют включённым постоянно в проде.
