# Phase 2 Development Plan

## Что уже сделано ✅

### Phase 0 (Quick Wins - 3 hours)
- ✅ Scatter plot visualization на correlation page
- ✅ Time series charts на data explorer
- ✅ Live dashboard с KPI метриками
- ✅ DateRangePicker component (создан, но не интегрирован)

### Phase 1 (Core Analytics - 5 hours)
- ✅ Backend: `/api/stats/hourly-patterns` endpoint
- ✅ Backend: `/api/stats/multi-area-comparison` endpoint
- ✅ Backend: `/api/stats/summary` endpoint
- ✅ Frontend: Hourly Patterns page с dual-axis chart
- ✅ Frontend: Multi-Area Comparison page
- ✅ Frontend: Correlations page с Key Findings секцией
- ✅ Frontend: Forecast page с инструкциями
- ✅ Performance: Dashboard оптимизирован (3 дня вместо 7)

### Улучшения UX
- ✅ Убраны emoji иконки, профессиональный стиль
- ✅ Исправлен correlation chart (price field bug)
- ✅ Добавлены выводы и интерпретация результатов

---

## Phase 2 - Приоритеты для Демо 🎯

### Приоритет 1: Критические для презентации (2-3 часа)

#### 1.1 Data Export Features ⭐⭐⭐
**Зачем:** Компания хочет работать с данными в Excel/PowerPoint

**Backend:**
- [ ] Add CSV export endpoint: `GET /api/export/prices?area=TOKYO&format=csv`
- [ ] Add Excel export endpoint: `GET /api/export/prices?area=TOKYO&format=xlsx`
- [ ] Add export для корреляций, hourly patterns

**Frontend:**
- [ ] Добавить кнопки "Export CSV" / "Export Excel" на все страницы с данными
- [ ] Data Explorer: export button для таблиц
- [ ] Correlations: export scatter plot data
- [ ] Hourly Patterns: export hourly stats
- [ ] Compare Areas: export comparison table

**Время:** ~2 часа

---

#### 1.2 Data Quality Indicators ⭐⭐⭐
**Зачем:** Показать что данные надежные

**Backend:**
- [ ] Endpoint `/api/stats/data-quality`:
  - Coverage % (сколько данных есть vs сколько должно быть)
  - Missing hours/days
  - Last update timestamp
  - Data freshness indicator

**Frontend:**
- [ ] Добавить badge на dashboard "Data Quality: Excellent/Good/Fair"
- [ ] Показывать coverage % для каждой области
- [ ] Warning если данных не хватает

**Время:** ~1 час

---

### Приоритет 2: Полезные для анализа (3-4 часа)

#### 2.1 Date Range Picker Integration ⭐⭐
**Зачем:** Пользователи хотят выбирать свой период анализа

**Задачи:**
- [ ] Интегрировать DateRangePicker component в:
  - [ ] Data Explorer page
  - [ ] Correlations page
  - [ ] Hourly Patterns page
  - [ ] Compare Areas page
- [ ] Заменить простые dropdown'ы на DateRangePicker
- [ ] Добавить preset ranges: Last 7/14/30/60/90 days + Custom

**Время:** ~1.5 часа

---

#### 2.2 Price Forecasting - Demo Mode ⭐⭐
**Зачем:** Показать ML capabilities без реального обучения

**Опции:**

**Option A: Mock Forecast (быстро - 30 мин)**
- [ ] Создать mock forecast endpoint для демо
- [ ] Возвращает "пример" прогноза на основе исторических паттернов
- [ ] Показывает как будет выглядеть forecast UI

**Option B: Quick Train Model (2 часа)**
- [ ] Скрипт для быстрого обучения модели на существующих данных
- [ ] `make train-model-tokyo` - обучает модель для TOKYO
- [ ] Сохраняет модель в БД
- [ ] После этого forecast page работает реально

**Рекомендация:** Option A для демо, Option B если есть время

**Время:** 0.5-2 часа (в зависимости от опции)

---

#### 2.3 Advanced Visualizations ⭐⭐
**Зачем:** Более глубокий анализ данных

**Задачи:**
- [ ] Heatmap visualization для hourly patterns (цена по дням недели × часам)
- [ ] Box plots для price volatility по областям
- [ ] Seasonal decomposition chart (тренд + сезонность + остатки)

**Время:** ~2 часа

---

### Приоритет 3: Оптимизация (2-3 часа)

#### 3.1 React Query Migration ⭐
**Зачем:** Кеширование, меньше повторных запросов

**Задачи:**
- [ ] Установить @tanstack/react-query
- [ ] Создать queryClient configuration
- [ ] Мигрировать API calls на useQuery hooks
- [ ] Добавить stale time, cache time settings
- [ ] Показывать cached data indicators

**Время:** ~2 часа

---

#### 3.2 Performance Improvements ⭐
**Зачем:** Быстрее загрузка при большом объеме данных

**Задачи:**
- [ ] Pagination для Data Explorer tables
- [ ] Virtual scrolling для больших таблиц
- [ ] Lazy loading для charts (загрузка по требованию)
- [ ] Backend: add pagination support to API endpoints

**Время:** ~2 часа

---

### Приоритет 4: Nice-to-Have (опционально)

#### 4.1 ML Model Confidence Intervals
- [ ] Forecast page: показывать доверительные интервалы (±σ, ±2σ)
- [ ] Визуализация uncertainty в прогнозах

#### 4.2 Data Quality Dashboard
- [ ] Отдельная страница `/quality` с детальной статистикой
- [ ] Missing data heatmap
- [ ] Data availability timeline
- [ ] Outlier detection

#### 4.3 Real-time Data Updates
- [ ] WebSocket для real-time updates
- [ ] Auto-refresh для dashboard
- [ ] Notifications о новых данных

---

## Рекомендуемый План на 6-8 часов

### День 1 (4 часа): Критические функции
1. ✅ **Data Export** (2 часа)
   - CSV/Excel export endpoints
   - Export buttons на всех страницах
   - Тестирование экспорта

2. ✅ **Data Quality Indicators** (1 час)
   - Quality endpoint
   - Badges на UI

3. ✅ **DateRangePicker Integration** (1 час)
   - Интеграция в 2-3 основные страницы

### День 2 (3-4 часа): Полезные улучшения
4. ✅ **Forecast Demo Mode** (0.5-2 часа)
   - Mock forecast или быстрое обучение модели

5. ✅ **Advanced Visualizations** (2 часа)
   - Heatmap или Box plots
   - Seasonal chart

6. ⏸️ **Performance** (опционально)
   - React Query если есть время

---

## Что НЕ делаем в Phase 2

❌ **Не критично для демо:**
- Сложный ML backtesting
- Real-time WebSocket updates
- Полная React Query миграция (можно частично)
- Все опциональные Nice-to-Have функции

---

## Итого: Phase 2 Timeline

**Минимум (критичное для демо):** 3-4 часа
- Data Export ✅
- Data Quality ✅
- Basic DateRangePicker ✅

**Оптимально (полезно для презентации):** 6-8 часов
- Все выше ✅
- Forecast demo mode ✅
- 1-2 advanced visualizations ✅

**Максимум (если есть время):** 10-12 часов
- Все выше ✅
- Performance optimization ✅
- Некоторые Nice-to-Have ✅

---

## Вопросы для обсуждения

1. **Data Export** - какие форматы критичны? (CSV обязательно, Excel опционально?)
2. **Forecast** - нужен реальный ML или mock для демо достаточно?
3. **Visualizations** - какие графики наиболее полезны для вашей презентации?
4. **Timeline** - сколько времени есть до презентации?

---

## Следующий шаг

Давайте начнем с **Приоритета 1: Data Export** - это критично для любой бизнес-презентации!

Команда для старта:
```bash
# Начинаем с export функциональности
git checkout -b feature/phase2-data-export
```
