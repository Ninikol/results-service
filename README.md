# ResultsService (FastAPI + PostgreSQL)

Сервис хранения и предобработки результатов завершённой парсинг-сессии:
- удаление дублей (по `fingerprint` внутри сессии),
- нормализация цен,
- нормализация единиц (`kg`, `l`, `pcs`) и расчёт `price_per_base_unit`,
- фильтрация по наличию, цене, бренду, категории, единице и JSON-атрибутам.

## Быстрый старт

### Глобальный запуск (frontend + backend + db)

Из корня репозитория:

Без сидов:
```bash
docker compose --profile frontend up --build -d
```

С сидами:
```bash
docker compose --profile frontend --profile seed up --build -d
```

Frontend: http://127.0.0.1:5173
Backend API: http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs

### Запуск только backend + db

Поднять PostgreSQL + API в Docker:

Без сидов:
```bash
docker compose up --build -d
```

С сидами:
```bash
docker compose --profile seed up --build -d
```

API: http://127.0.0.1:8000
Docs (Swagger): http://127.0.0.1:8000/docs

## Основные эндпоинты

- `POST /sessions` — создать завершённую парсинг-сессию
- `POST /sessions/{session_id}/results/bulk` — массовая загрузка результатов (с предобработкой)
- `GET /sessions/{session_id}/results` — фильтрация через query params
- `POST /sessions/{session_id}/results/filter` — расширенная фильтрация через JSON body

## Пример создания сессии

```json
{
  "source_name": "market-parser",
  "finished_at": "2026-03-06T10:30:00Z"
}
```

## Пример bulk ingest

```json
{
  "items": [
    {
      "external_id": "A-1",
      "name": "Молоко 900 мл",
      "brand": "Домик",
      "category": "Молочные",
      "url": "https://shop.test/item/1?utm=ads",
      "price": "119,90 ₽",
      "currency": "₽",
      "unit": "900 мл",
      "in_stock": "в наличии",
      "attributes": {
        "fat": "3.2%",
        "country": "RU"
      }
    }
  ]
}
```
