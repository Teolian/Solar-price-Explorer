# Solar×Price Explorer (AI‑Agent) — Project Spec

## 0) Миссия и результат
**Цель:** связать почасовые **цены/объёмы JEPX** с **солнечной радиацией JMA** по зонам, строить признаки/корреляции и давать базовый прогноз цен/выработки для подготовки сделок и «обоснования» ставок (JST). Результат — веб‑приложение (React) + API (FastAPI) + «умный» агент, который сам вызывает инструменты (ETL, features, train, forecast) и объясняет результаты.

---

## 1) Технологии
- **Frontend:** Next.js (React + TypeScript); **shadcn/ui + Tailwind CSS**; **TanStack Query**; **TanStack Table**; **ECharts** (или Recharts) для графиков; **react-hook-form + zod**; **react-i18next** (JP/EN/RU).
- **Backend/API:** **FastAPI** (Python), **PostgreSQL**; фоновые задачи — Celery/RQ (по желанию) или cron; **AWS** (S3 для сырья/бэкапы; ECS/Lambda опционально).
- **ML:** лёгкий baseline (tree‑based/XGBoost), валидация по времени; сравнение с наивной «вчера в этот час».
- **Ops:** GitHub, Slack, CI‑lint/pytest, простая observability (JSON‑логи, алерты на отставание данных).

---

## 2) Источники данных и поля для парсинга (MVP)

### 2.1 JEPX — Day‑Ahead / Spot (по зонам)
**Страницы «Data Download» (англ., прямые ссылки):**
- Day Ahead Market (индекс): https://www.jepx.jp/en/electricpower/market-data/spot/
- Prices — средние по **дню** (*Data Download*): https://www.jepx.jp/en/electricpower/market-data/spot/ave_day.html
- Prices — средние по **году** (*Data Download*): https://www.jepx.jp/en/electricpower/market-data/spot/ave_year.html
- Price Sensitivity (Virtual Price) — *Data Download*: https://www.jepx.jp/en/electricpower/market-data/spot/virtualprice.html

**Целевые поля (CSV/табличные):**
- `timestamp` (JST, часовое разрешение), `system_price_yen_per_kwh`, `area_price_yen_kwh` (по 9 областям: Hokkaido, Tohoku, Tokyo, Chubu, Hokuriku, Kansai, Chugoku, Shikoku, Kyushu),
- `volume_total_kwh`, `volume_sell_kwh`, `volume_buy_kwh`, а также блок‑ордера (sell/buy contracted) — где доступны.

**Заметки:**
- На уровне MVP парсим «Prices (JPY/kWh)» и «Volumes (kWh)» по выбранным годам; часовой «Time Code» маппим на полноформатный `timestamp` с таймзоной JST.

### 2.2 JMA — Solar/Infrared Radiation
**Официальные страницы:**
- Данные (радиация) — прямые ссылки: https://www.data.jma.go.jp/env/radiation/en/data_rad_e.html
- Базовая информация / станции / формат: https://www.data.jma.go.jp/env/radiation/en/know_std_rad_e.html

**Доступные станции (на текущий момент):**
- **Abashiri** — активна
- **Tsukuba (Tateno)** — активна
- **Ishigakijima** — активна
- **Minamitorishima** — активна
- **Sapporo** — наблюдения завершены (до 2020‑11)
- **Fukuoka** — наблюдения завершены (до 2024‑03)

**Целевые поля (после нормализации):**
- `timestamp` (JST, часовое разрешение), `ghi`, `dni`, `dhi`, `station`, `area` (JEPX‑зона, присваиваем при маппинге), `quality_flag` (если присутствует в формате — сохранять).

**Fallback для покрытия зон:**
- При отсутствии ближайшей активной станции JMA — использовать **AMeDAS Sunshine Duration** для оценки GHI (эмпирическая конверсия) *или* подключить спутниковые/альтернативные источники (по согласованию).
**Официальная страница данных:**
- Станции с выдачей рядов **GHI/DNI/DHI** в текстовом формате (.txt). На сегодня публикуются: **Abashiri, Tsukuba (Tateno), Ishigakijima, Minamitorishima**; у **Sapporo** (до 2020‑11) и **Fukuoka** (до 2024‑03) наблюдения прекращены. Формат обновлён с 2024‑04 (есть описание формата «since Apr 2024» и «until Mar 2024»).

**Целевые поля (после нормализации):**
- `timestamp` (JST, часовое разрешение), `ghi`, `dni`, `dhi`, `station`, `area` (JEPX‑зона, присваиваем при маппинге), `quality_flag` (если присутствует в формате — сохранять).

**Fallback для покрытия зон:**
- При отсутствии ближайшей активной станции JMA — использовать **AMeDAS Sunshine Duration** для оценки GHI (эмпирическая конверсия) *или* подключить спутниковые/альтернативные источники (по согласованию).

---

## 3) Карта соответствия «JEPX Area → JMA Station» (первичный набросок)
> *Важно:* покрытие станциями JMA по радиации редкое; это **операционный компромисс** для MVP. В отчётах явно показывать «distance/representativeness». При появлении новых данных — обновлять маппинг.

| JEPX Area | Primary JMA Station | Статус | Примечание |
|---|---|---|---|
| **Hokkaido** | **Abashiri** | Активна | Географически на севере острова; Sapporo исторически (до 2020‑11). |
| **Tohoku** | Tsukuba (Tateno) | Активна | Наиболее близкая «активная» станция к северо‑востоку Хонсю отсутствует; используем Tateno как прокси, с дисклеймером. |
| **Tokyo** | **Tsukuba (Tateno)** | Активна | Ближайшая репрезентативная станция к Kanto. |
| **Chubu** | Tsukuba (Tateno) | Активна | Прокси для Kanto/Chubu в MVP; по желанию — уточнять региональный коэффициент. |
| **Hokuriku** | Tsukuba (Tateno) | Активна | Прокси; добавить поправки по облачности Японского моря. |
| **Kansai** | Tsukuba (Tateno) | Активна | Прокси; в отчёте показывать оговорку по дистанции. |
| **Chugoku** | Tsukuba (Tateno) | Активна | Прокси. |
| **Shikoku** | Tsukuba (Tateno) | Активна | Прокси. |
| **Kyushu** | *Fukuoka* → (после 2024‑03) **Tsukuba (Tateno)** | Истор/Активна | До 2024‑03 была Fukuoka; далее использовать Tateno как временную замену; рассмотреть Ishigakijima как экспериментальный прокси для юга (с оговорками). |

*Расширение (опционально):* добавить региональные поправки (коэффициенты/градиенты) и/или использовать сеточные ре‑анализа/спутники для улучшения привязки к зонам.

---

## 4) Модели, признаки и качество
- **Target:** `Area Price (JPY/kWh)` по каждой зоне.
- **Фичи:** `ghi,dni,dhi, volume_kwh, price_lag_1h, price_lag_24h, ghi_lag_1h, ghi_roll3h, hour, dow, month, is_weekend`.
- **Валидации:** n≥168 для корреляций; winsorize выбросов; строгая **JST**; пропуски ночи (GHI≈0) учитывать корректно.
- **Метрики:** MAE; бенчмарк — «вчера в этот час» и/или медиана последних 7 дней по часу.

---

## 5) REST‑контракты (агент вызывает инструменты)
- `GET /api/areas`
- `GET /api/prices?area=&from=&to=` — часовые ряды.
- `GET /api/radiation?area=&from=&to=` — часовые ряды.
- `GET /api/corr?area=&period=` — Pearson (ghi/dni/dhi ↔ price), n.
- `POST /api/train { area, target, features, val_window }` — ответ: mae, trained_at, model_id.
- `POST /api/forecast { area, horizon_hours, model_id?, future_radiation? }` — ответ: points[{ts, price_pred}], p10/p90 (если считаем).
- `GET /api/export?area=&kind=features|raw|forecast&format=csv|parquet&from=&to=` — url.

---

## 6) UX и дизайн
- **IA:** Overview / Correlations / Forecast / Area Compare / Data Explorer / Admin.
- **UI‑кит:** shadcn/ui + Tailwind; графики ECharts; таблицы TanStack Table.
- **A11y:** контраст ≥4.5:1; Noto Sans JP; клавиатура.
- **i18n:** JP/EN/RU переключатель; все даты — JST и явный период.
- **Паттерны:** пустые состояния, skeletons, «копировать ссылку с фильтрами».

---

## 7) Шаблоны prompt’ов для АИ‑агента

### 7.1 Служебные (system)
- **Общие правила:**
  1) Всегда указывай период **JST** и размер выборки `n`.
  2) Если данных нет/мало — запусти соответствующий инструмент или попроси период/зону.
  3) Никогда не скрывай оговорки по репрезентативности станции JMA для зоны JEPX.

- **Дефицит данных:**
  > «Не хватает данных за период {{from}}–{{to}} (JST), найдено n={{n}} < 168. Предлагаю: (1) обновить JEPX/JMA, (2) сузить период, (3) использовать прокси‑станцию. Запустить обновление?»

- **Старость модели:**
  > «Модель для {{area}} обучена {{trained_at}} JST (>14 дней назад). Рекомендую переобучение перед прогнозом. Запускать train сейчас?»

- **Оговорка JMA‑станции:**
  > «Для зоны {{area}} используется станция {{station}} как прокси. Укажите, если хотите сменить/добавить источники (например, AMeDAS солнце/спутник).»

### 7.2 Пользовательские (assistant → user)
- **Корреляции:**
  > «За {{from}}–{{to}} JST (n={{n}}) связь GHI↔Price: r={{r_ghi}}; DNI↔Price: r={{r_dni}}; DHI↔Price: r={{r_dhi}}. В будни эффект сильнее/слабее (комментарий).»

- **Прогноз:**
  > «Прогноз цены для {{area}} на {{h}}ч вперёд с шагом 1ч (модель {{model_id}}, MAE={{mae}}): показываю среднюю и p10/p90. Нужен экспорт CSV?»

- **Качество и риски:**
  > «Данные JMA — станция {{station}} (дистанция до зоны ~{{km}} км). Возможна систематическая погрешность; рекомендую валидацию по историческим дням.»

### 7.3 Инструментальные (agent → tools)
- `fetch_jepx_prices { area, from, to }`
- `fetch_jma_radiation { station|area, from, to }`
- `build_features { area, lags:[1,24], rolls:[{ghi,3}], calendar:true }`
- `compute_correlations { area, period, cols:["ghi","dni","dhi"], target:"area_price" }`
- `train_model { area, target:"area_price", features:[…], val_window:"7d" }`
- `forecast { area, horizon_hours:24|48|72|168, model_id?, future_radiation? }`
- `export_dataset { area, kind, format, period }`

---

## 8) План MVP (4–6 рабочих дней)
- **Дни 1–2:** схема БД, парсинг JEPX (2 зоны) + JMA (1–2 станции), базовый дашборд.
- **День 3:** Feature Store, корреляции, экспорт.
- **День 4:** baseline‑модель + прогноз 24–72ч.
- **Дни 5–6:** шлифовка UI (ECharts), админ‑панель, мини‑доки и скрипт демо.

