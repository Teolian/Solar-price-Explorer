# Deployment Guide — Solar×Price Explorer (Free Tier)

> Цель: выложить демо бесплатно (или почти бесплатно), с «живыми» данными и плановыми ETL. Стек: **Next.js (React+TS)**, **FastAPI (Python)**, **PostgreSQL (Neon)**, планировщик — **GitHub Actions** (или **Vercel Cron** как альтернатива). Таймзона — **JST (UTC+9)**.

---

## 1) Архитектура (обзор)
```
[Users] ──HTTPS──> [Vercel: Next.js Frontend]
                          │
                          └───────────────▶  [Backend API: FastAPI]
                                              (Railway / Render  Free Tier)
                                                  │
                                                  └────────────▶  [PostgreSQL]
                                                                   (Neon Free)

[GitHub Actions (cron)] ──▶  запускает ETL (JEPX/JMA) → пишет в Neon
  (альтернатива: Vercel Cron → POST /api/etl/…)
```

**Почему так:**
- Vercel идеально подходит для Next.js и бесплатного демо.
- Railway/Render дают бесплатный слой для Python API; возможна «спячка» (первый запрос чуть дольше).
- Neon — serverless Postgres с бесплатным тарифом, удобен для демо и веток.
- GitHub Actions — удобный бесплатный cron для публичного репозитория.

---

## 2) Компоненты и бесплатные планы
| Компонент | Роль | Бесплатный план | Примечания |
|---|---|---|---|
| **Vercel** | Frontend (Next.js) | Да | Ограничения на билд/функции; для SPA/SSR демо обычно хватит. |
| **Railway** *(или Render)* | Backend (FastAPI) | Да | Free-планы с автосном; можно выбрать любой. |
| **Neon** | Postgres | Да | Serverless; следить за storage/credits. |
| **GitHub Actions** | Плановый ETL | Да (публичный репо) | Cron, логи, секреты. |
| **Vercel Cron** | Альтернатива Actions | Да | Вызов защищённого ETL-эндпоинта API. |

**Запасные варианты:**
- Backend: **HuggingFace Spaces (Docker)**, **Fly.io**, **Deta Space** — если Railway/Render ограничены.
- Хранилище сырья: **Cloudflare R2 (free)**, либо просто GitHub Releases для CSV снапшотов.

---

## 3) Репозиторий и структура
```
repo/
  apps/
    frontend/   # Next.js + TS (Vite/Next—на выбор; тут — Next)
    api/        # FastAPI (uvicorn)
    etl/        # скрипты: jepx_ingest.py, jma_ingest.py, build_features.py
  db/
    migrations/ # SQL или Alembic (опционально)
  .github/workflows/
    etl.yml     # расписания ETL
  README.md
```

---

## 4) Переменные окружения

### 4.1 Общие
- `DATABASE_URL` — строка подключения к Neon (формат `postgresql://...`).
- `API_TOKEN` — секрет для защищённых ETL-эндпоинтов (если используете Vercel Cron).
- `TZ` — `Asia/Tokyo` (для явной фиксации TZ при ETL).

### 4.2 Frontend (Vercel)
- `NEXT_PUBLIC_API_BASE` — базовый URL бэкенда, например: `https://solar-api.up.railway.app`.

### 4.3 Backend (Railway/Render)
- `DATABASE_URL` — из Neon.
- `ALLOWED_ORIGINS` — список доменов фронта (например, `https://solar-price-explorer.vercel.app`).
- `API_TOKEN` — общий секрет для /api/etl/*.

> **Совет:** заведите `.env.example` и задокументируйте все ключи.

---

## 5) База данных (Neon)
1) Создать проект + базу; получить `DATABASE_URL`.
2) Применить миграции (минимум): `prices`, `radiation`, `features`, `models`.
3) Включить pooling (по умолчанию у Neon есть proxy); следить за лимитами.
4) Настроить роли/права: создать пользователя только на чтение (опционально) для диаграмм.

**Retention:** free-слой ограничен по storage — раз в N недель выгружайте старые ряды в CSV (S3/R2/GitHub Releases) и чистите таблицы (архивация).

---

## 6) Backend API (Railway/Render)
**Шаги:**
1) Импорт проекта из GitHub.
2) Build & Start команду выставить (например): `uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers`.
3) ENV: `DATABASE_URL`, `ALLOWED_ORIGINS`, `API_TOKEN`.
4) Healthcheck: `/healthz` (вернуть 200 OK).
5) Включить CORS: разрешить домен Vercel.
6) Проверить автосон: первый запрос после простоя может быть 5–10 секунд — ок для демо.

**Домены:** можно использовать дефолтный Railway/Render-домен или подключить свой.

---

## 7) Frontend (Vercel)
**Шаги:**
1) Import Project → выбрать `apps/frontend`.
2) Framework: Next.js (auto-detect).
3) ENV: `NEXT_PUBLIC_API_BASE`.
4) Build: по умолчанию (`next build`).
5) Проверить CORS: запросы уходят на домен API, который разрешён на бэке.
6) *(Опционально)* Настроить **Vercel Cron** (см. ниже).

**Статика данных (fallback):** если API недоступен, можно показывать демо-данные из `/public/data/*.json` и кнопку «Переподключиться к API».

---

## 8) Плановый ETL — два подхода

### Вариант A: GitHub Actions (рекомендовано)
- Бесплатно для публичного репо; отличные логи; легко ретраить.
- Настроить расписание с учётом JST (UTC+9). Пример: 05:00 и 17:00 UTC ≈ **14:00** и **02:00** JST.

**Пример `/.github/workflows/etl.yml`:**
```yaml
name: ETL JEPX/JMA

on:
  schedule:
    - cron: '0 5,17 * * *'   # 05:00 и 17:00 UTC → 14:00/02:00 JST
  workflow_dispatch:

jobs:
  run-etl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r apps/api/requirements.txt
      - env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          TZ: Asia/Tokyo
        run: |
          python apps/etl/jepx_ingest.py --areas TOKYO,TOHOKU
          python apps/etl/jma_ingest.py  --areas TOKYO,TOHOKU
          python apps/etl/build_features.py --areas TOKYO,TOHOKU
```

### Вариант B: Vercel Cron → защищённые эндпоинты API
- Создать в Vercel Cron задания, бьющие по `POST https://<api>/etl/run?source=jepx` и `/etl/run?source=jma`.
- На бэкенде реализовать проверку заголовка `Authorization: Bearer <API_TOKEN>`.
- Плюс: один провайдер для фронта и cron; минус: логи задач менее удобны.

---

## 9) CORS и сеть
- На бэкенде включить CORS для домена Vercel (и, при необходимости, локальной разработки):
  - `https://<project>.vercel.app`
  - `http://localhost:3000`
- Проксировать запросы не обязательно; но можно сделать `/api` прокси на фронте для единообразия URL.

---

## 10) Логи и мониторинг
- **Vercel Analytics** — базовые метрики фронта.
- **Railway/Render Logs** — запросы/ошибки FastAPI; включить структурные JSON-логи.
- **Neon Dashboard** — активные подключения, запросы, storage; включить *query logging* для отладки.
- Healthchecks: `/healthz` (API), тестовый `SELECT 1` при старте.

---

## 11) Безопасность
- Секреты хранить в: GitHub (Actions secrets), Vercel Project Settings, Railway/Render ENV.
- Ограничить CORS/Origins; в ETL-эндпоинтах — обязательный bearer-токен.
- Rate-limit (если нужно): на FastAPI через middleware/реализацию в прокси.
- Не хранить приватные ключи источников в репозитории.

---

## 12) Производительность и лимиты
- Использовать connection pooling Neon (по умолчанию) и короткие тайм-ауты запросов.
- Индексы по `(area, ts)` для всех таймсерийных таблиц.
- Кэширование «последней недели» в памяти API (опционально) или CDN Vercel для GET-эндпоинтов (stale‑while‑revalidate).
- Понимать, что free backend может «засыпать»: держать пользователю заметку про «первый ответ может занять до 10 с».

---

## 13) Домены и SSL
- Vercel даёт SSL/домен вида `*.vercel.app`.
- Railway/Render дают SSL/сабдомен для API.
- Подключение кастомного домена — опционально.

---

## 14) Демо-режим (fallback без сервера)
- Хранить 7–14 дней JSON/CSV в `apps/frontend/public/data/`.
- Фича-флаг `NEXT_PUBLIC_DEMO_MODE=true` — UI читает локальную статику.
- Кнопка «Подключиться к live API» (переключает на `NEXT_PUBLIC_API_BASE`).

---

## 15) Резерв/откат
- Регулярно `pg_dump` из Neon (или snapshot/branch) → хранить в Releases/S3.
- Для аварийного отката: создать новую Neon-ветку от снапшота и перекинуть `DATABASE_URL` на неё.

---

## 16) Путь к «продакшену» (при росте)
- Backend → AWS ECS/Fargate или EC2; DB → RDS Postgres; очереди → SQS; секреты → AWS Secrets Manager.
- Плановый ETL → Amazon EventBridge + Lambda/ECS tasks.
- Логи → CloudWatch/OpenSearch; мониторинг → Prometheus/Grafana (или Datadog).

---

## 17) Чек‑лист перед демо
- [ ] Заполнены ENV на Vercel/Backend/Actions.
- [ ] Создана база Neon, применены миграции, есть базовые ряды на 7–14 дней.
- [ ] Пройдён CORS-тест (Vercel → API).
- [ ] Cron (Actions или Vercel Cron) выполнен хотя бы один раз успешно.
- [ ] Страница Overview показывает график Price vs GHI (JST), есть блок Insights.
- [ ] На вкладке Forecast работает 24–72h прогноз; экспорт CSV.
- [ ] Healthcheck `/healthz` возвращает 200.

