# podzamkom-vk-bot

Базовый каркас в стиле Clean Architecture:

- `domain/` — сущности и контракты.
- `use_cases/` — бизнес-операции без зависимостей от транспорта/SDK.
- `infrastructure/` — реализации репозиториев, миграций БД и composition root (`bootstrap.py`).
- `interfaces/` — входные адаптеры (точка входа VK callback handler).

## Быстрый запуск

```bash
python3 main.py
```

При старте приложения автоматически выполняются SQL-миграции из `infrastructure/db/migrations` в SQLite-базу `data/app.db`.
