# Агрегационная система рейтингов китайских производителей (MVP)

Веб-приложение: пользователи оставляют отзывы о заказах из Китая, оценивая по 4 критериям
(сервис, продавец, товар, доставка). Поиск выдаёт релевантные отзывы с рекомендательным
ранжированием (content-based фильтрация — Этап A алгоритма из статьи) и сортировкой
по релевантности / баллам / дате. Есть древовидные комментарии, обратная связь и аналитика.

**Стек:** Python 3.12 · FastAPI · SQLAlchemy · SQLite (по умолчанию) / PostgreSQL (деплой) ·
встроенный веб-интерфейс (HTML/JS). Развёртывание — Docker Compose.

---

## Вариант 1. Запуск локально (самый быстрый, без установки БД)

Нужен только установленный Python 3.11+.

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Затем открой в браузере:
- **http://127.0.0.1:8000** — веб-интерфейс (поиск, аналитика, вход);
- **http://127.0.0.1:8000/docs** — авто-документация API (Swagger).

При первом запуске БД (файл `app.db`) автоматически создаётся и наполняется
демо-данными (5 площадок, 100 товаров, 500 отзывов).

**Демо-аккаунт:** `user1@example.com` / `password123`

---

## Вариант 2. Деплой через Docker (с PostgreSQL) — одной командой

Нужен установленный Docker.

```bash
cd china-reviews
docker compose up --build
```

Открой **http://localhost:8000** (интерфейс) и **http://localhost:8000/docs** (API).

Остановить: `Ctrl+C`, удалить данные: `docker compose down -v`.

> ⚠️ Перед боевым деплоем поменяй `SECRET_KEY` в `docker-compose.yml` на длинную случайную строку.

---

## Тесты

```bash
cd backend
pytest
```

---

## Структура

```
china-reviews/
├── docker-compose.yml          # деплой backend + PostgreSQL
├── README.md
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── .env.example
    └── app/
        ├── main.py             # точка входа FastAPI
        ├── config.py           # настройки (.env)
        ├── database.py         # подключение к БД
        ├── models.py           # таблицы (ORM)
        ├── schemas.py          # валидация (Pydantic)
        ├── auth.py             # регистрация, JWT
        ├── seed.py             # демо-данные
        ├── routers/            # эндпоинты (users, reviews, comments, search, feedback, analytics)
        ├── reco/               # рекомендательное ядро (aggregate + CBF + pipeline)
        └── static/index.html   # веб-интерфейс
```

---

## Основные эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/register` | регистрация |
| POST | `/auth/login` | вход (выдаёт JWT) |
| GET | `/search` | поиск + рекомендации (`q, category, sort, order`) |
| POST | `/reviews` | создать отзыв (4 оценки) |
| GET | `/products/{id}/reviews` | отзывы по товару |
| POST | `/comments` | комментарий / ответ |
| GET | `/reviews/{id}/comments` | дерево комментариев |
| POST | `/feedback` | «отзыв полезен» |
| GET | `/analytics/by-platform` | средние по площадкам |
| GET | `/analytics/criteria-avg` | средние по 4 критериям |

---

## Как развит алгоритм рекомендаций

Сейчас реализован **Этап A** из статьи (Лобанов, Сибиряков): агрегация многокритериальных
оценок с учётом авторитетности пользователей + content-based фильтрация (взвешенная
критериальная оценка `Score_crit` и косинусная близость профилей) + текстовая релевантность.
Итоговый ранг: `rank = α·sim + β·Score_crit + γ·relevance` (веса в `config.py`).

Поля `feedback`, `profile_attrs`, `crit_weights` уже заложены в БД для развития до
**Этапа B (Factorization Machine)** и **Этапа C (ANFIS)** — см. `Backend_подробный_план.md`.
