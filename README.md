# podzamkom-vk-bot

Базовый каркас в стиле Clean Architecture:

- `domain/` — сущности и контракты.
- `use_cases/` — бизнес-операции без зависимостей от транспорта/SDK.
- `infrastructure/` — реализации репозиториев, миграций БД, логгера, конфигурации и composition root (`bootstrap.py`).
- `interfaces/` — входные адаптеры (точка входа VK callback handler).

## Быстрый запуск

```bash
export VK_TOKEN="vk1.a_super_secret_token"
export VK_CALLBACK_SECRET="callback-secret"
export VK_ADMIN_IDS="1,2,3"
export DB_PATH="data/app.db"
export VK_CONFIRMATION_CODE="test-confirmation-code"
python3 main.py
```

При старте приложения автоматически выполняются SQL-миграции из `infrastructure/db/migrations` в SQLite-базу из `DB_PATH`.

Если обязательные ENV отсутствуют, приложение завершится с понятной ошибкой (`Configuration error: Missing required environment variables: ...`).
