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

3. Загрузите переменные окружения и запустите приложение:

```bash
set -a
source .env
set +a
python3 main.py
```

При старте приложения автоматически выполняются SQL-миграции из `infrastructure/db/migrations` в SQLite-базу из `DB_PATH`.

Если обязательные ENV отсутствуют, приложение завершится с понятной ошибкой (`Configuration error: Missing required environment variables: ...`).
