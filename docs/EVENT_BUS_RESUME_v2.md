# Event Bus — Резюме v2.2

**Контекст:** обновление после фаз A + B + D + E + **F** (полный sweep по 30+ непокрытым роутерам, 4 inbound-приёмника, 11 новых entities). Предыдущая версия — v2.1.

**Покрытие на момент v2.2:** **117 event_key** в каталоге (**33 entities**), **24+ in-process хендлера**, **17 before-хуков**, **1 batch**, JSON-Logic фильтрация подписок, simulate-эндпоинт для DRY-RUN, **5 inbound-приёмников** (Diadoc / Telegram / 1С / Bank / Госключ) под все 8 запланированных интеграций.

---

## 1. Резюме одной фразой

Реализованы **runtime (a) in-process before-фаза + runtime (c) outbox-доставка**, типизация событий, before/mutate/cancel-семантика, JSON-Logic фильтрация, batch-события, payload-versioning, simulate-эндпоинт, **5 inbound-приёмников**. **117 уникальных event_key** в каталоге (было 8 в v1.5), 24+ in-process обработчиков на 33 сущностях. Архитектурно покрывает **~95% спеки** `EVENTS_API.md` БЕЗ Bitrix-style UI-конструктора обработчиков; outbound (CRM→внешние) и inbound (внешние→CRM) каналы готовы для всех 8 июльских интеграций (Telegram / 1С / Bank / Diadoc / Госключ / Mail / BI / СОДы).

---

## 2. Соответствие пунктам спецификации

| # | Что предлагалось в спеке | Что у нас сейчас | Статус |
|---|---|---|---|
| 1 | Outbox pattern | EventOutbox + emit_event в той же сессии | ✅ Полностью |
| 2 | Worker → webhook → retry + DLQ | exp.backoff 5→15→45→135→405с, max_attempts=5 → DLQ | ✅ Полностью |
| 3 | HMAC sha256 sign | X-Event-Signature через hmac_secret | ✅ Полностью |
| 4 | Ordering per entity | Sort by (entity_type, entity_id, created_at) | ✅ Полностью |
| 5 | Idempotency через event_id | unique constraint + повтор-emit → no-op | ✅ Полностью |
| 6 | Per-subscription dedup | V1.5: event_delivery_dedup + INSERT OR IGNORE | ✅ Полностью |
| 7 | Recursion guard | causation_chain + MAX_DEPTH=5 + _in_emit contextvar | ✅ Полностью |
| 8 | Schema versioning | payload_version=1 на каждой эмиссии + X-Event-Schema-Version header | ✅ **Полностью (v2)** |
| 9 | Observability admin UI | /event-bus/stats endpoint + IntegrationsOutbox/Subscriptions страницы | ✅ Базовый уровень |
| 10 | **DSL для conditions** | **JSON-Logic поверх payload (15 операторов, 23 теста)** | ✅ **v2** |
| 11 | **Batch / композитные события** | **emit_batch_event + batch_* фаза в каталоге** | ✅ **v2** |
| 12 | Архитектурная сегрегация 3-х runtime | **(a) in-process before + (c) outbox** реализованы. (b) in-process after через `@on` тоже работает | ✅ **v2** (2 из 3) |
| 13 | Реестр EventType (event_types таблица) | **Autogen-каталог в `docs/events.json`** (file-based, не DB) | ⚠️ **Иначе (v2)** |
| 14 | **EventHandler модель** (UI-настраиваемые) | **Не делаем. Хендлеры регистрируются `@on` декоратором в коде** | ❌ Намеренно |
| 15 | EventRedirect модель | **Не делаем. Заменяется `if/else` внутри handler'а** | ❌ Намеренно |
| 16 | EventDispatch | через EventOutbox.status + event_delivery_dedup | ⚠️ Иначе |
| 17 | **before_*** фаза c cancel/mutate/redirect | **Continue/Cancel(reason,code)/Mutate(patch) реализованы** | ✅ **v2** |
| 18 | simulate endpoint | **`POST /api/v1/event-bus/simulate`** — DRY-RUN: показывает what-if по before-фазе, matched/skipped подпискам, JSON-Logic | ✅ **v2** |
| 19 | Allowlist внутренних обработчиков | Не нужен — нет UI-handler'ов, регистрация через @on в коде | ❌ Не применимо |
| 20 | Покрытие событиями: 600 типов | **117 event_keys в коде на 33 сущностях, ~140 emit-точек, 17 before-хуков.** Покрыты все 8 интеграций | ✅ **D+E+F-фазы** |
| 21 | Inbound-приёмники (внешние→CRM) | **5 приёмников: Diadoc / Telegram / 1С / Bank / Госключ** (HMAC verify, idempotent, emits `*.after_inbound`) | ✅ **E+F-фазы** |

---

## 3. Что сделали иначе — и почему

### 3.1. In-process хендлеры через `@on`-декоратор вместо EventHandler DB-таблицы

**Спека предлагала:** таблица `event_handlers` с `handler_target` (строка, путь к Python-функции), `priority`, `can_cancel`, `can_mutate`, `conditions_json`. Админ настраивает через UI. Реестр allowlist'а для безопасности.

**Мы сделали:** регистрация через декоратор в коде:

```python
@on("contract.before_status_change", priority=100, can_cancel=True)
async def validate_status_transition(ctx: EventContext):
    if ctx.payload.get("status_after") == "completed" and ctx.payload.get("paid_amount", 0) == 0:
        return Cancel("Нельзя завершить договор без оплат", code="contract.completed_without_payment")
    return Continue()
```

**Почему:**
- грепабельность (`grep "@on(.contract.before"` найдёт ВСЕ хендлеры события);
- юнит-тесты обычные (импорт функции + вызов с ctx);
- PR-ревью видит изменения в логике, не миграцию в БД;
- IDE refactor работает;
- нет supply-chain риска от UI-input → Python-import.

**Минус:** добавление хендлера требует деплой. На текущей стадии — приемлемо, у нас не SaaS-инсталляции, где админы должны кастомизировать без программиста.

### 3.2. EventRedirect через `if/else`, не через таблицу

**Спека:** табличный redirect `from_handler` → `to_handler` с `condition_json`.

**Мы:** обычный branching в handler'е:

```python
@on("outgoing_document.before_render")
async def render_router(ctx):
    if ctx.payload["editor_mode"] == "structured":
        return await render_structured(ctx)
    return await render_default(ctx)
```

**Почему:** та же гибкость, отлаживается breakpoint'ом, видна в стеке вызовов, ревьюится PR'ом.

### 3.3. event_types как autogen-файл, не DB-таблица

**Спека:** таблица `event_types` управляется через UI.

**Мы:** `backend/app/tools/dump_event_types.py` обходит AST всего `backend/app/`, находит `emit_event(..., event_type="...")`, `dispatch_before/after("...")`, `@on("...")`, генерирует `docs/events.json`:

```json
{
  "events": [
    {
      "event_key": "contract.before_status_change",
      "entity_type": "contract", "action": "status_change", "phase": "before",
      "payload_version": 1,
      "emitted_from": ["app/routers/contracts.py:605"],
      "handlers": [
        "app/event_handlers/contracts.py:36 (validate_status_transition)",
        "app/event_handlers/contracts.py:65 (normalize_status_change_meta)"
      ]
    }
  ]
}
```

**Почему:**
- источник правды — код, каталог производный;
- невозможен дрейф (CI: `python -m app.tools.dump_event_types --check`);
- PR-ревью видит «появилось новое событие» по diff'у каталога;
- никаких миграций при добавлении новых событий.

### 3.4. JSON-Logic вместо CEL/Sentinel

**Спека:** «DSL для conditions».

**Мы:** свой 200-строчный JSON-Logic-evaluator. Поддержанные операторы: `==`, `!=`, `<`, `>`, `<=`, `>=`, `and`, `or`, `!`, `var` (dot-path с default), `in`, `missing`.

**Почему свой а не пакет:**
- полный `json-logic-py` тащит 100+ операторов и transitive deps;
- нам хватает 15;
- легко ревьюить/тестировать (23 теста, все зелёные);
- легко расширить когда понадобится.

**Применение в worker'е:** перед каждой доставкой подписке проверяется `condition_json`; если не match — доставка пропускается (с фиксацией в логах debug-уровня).

### 3.5. Batch-события через `emit_batch_event(items=[...])`

**Кейс:** 1С/банк присылают пачку 500 транзакций. 500 webhook'ов — болезненно для подписчика. Решение: одно композитное событие с `items: [...]` в payload + summary-aggregate.

```python
await emit_batch_event(
    db,
    event_type="treasury_transaction.batch_imported",
    entity_type="treasury_transaction",
    items=[{"id": "...", "amount": 1500}, ...],
    parent_id=str(import_job.id),
    summary={"total_amount": 850_000, "matched": 487, "errors": 13},
)
```

В autogen-парсере добавлена фаза `batch` (`{entity}.batch_{action}` → entity_type + action + phase=batch).

### 3.6. Сужение объёма событий

**Спека:** ~600 типов событий.

**Мы:** 30 уникальных event_keys в каталоге, ~50 emit-точек в коде. Покрыты domain-critical entity: contract, deal, task, lead, document, outgoing_document, approval_instance, mail_message, kp_document.

**Почему:** расширяем под конкретного консьюмера, не впрок. Когда команда Диадок попросит «нужен `document_dispatch.after_signed_by_counterparty`» — 5 минут добавить.

### 3.7. Causation chain вместо опционального flag'а

Реализован как explicit `causation_chain: List[str]` в outbox-строке + `causation_scope()` context-manager. MAX_DEPTH=5. Это **строже** спеки, потому что обнаруживается на каждой эмиссии, а не только при подозрении.

---

## 4. Что НЕ сделано

| Что | Зачем нужно | Когда уместно |
|---|---|---|
| `EventHandler` DB-таблица + UI-конструктор | Per-tenant кастомизация без деплоя | Никогда (антипаттерн Bitrix-стиля) |
| `EventRedirect` через таблицу | Замена обработчиков под условиями | Никогда (заменяется `if/else`) |
| ~~`simulate` endpoint~~ | ~~Безопасная проверка «что сработает»~~ | ✅ **Сделано в v2 — нужен под 5+ параллельных команд** |
| Покрытие всех 600 событий впрок | Готовность к произвольным интеграциям | По запросу — мини-задача на 5 минут |
| In-process `(b)` runtime отдельным API | Замена NotificationRule на единую модель | Никогда (NotificationRule покрывает кейс) |
| Manifest подписок (схема payload объявляется подписчиком) | Защита от приёма несовместимой payload-версии | После 1-2 эволюций payload (v2.0) |

---

## 5. Текущее состояние deploy

**Локалка:** v2 полностью (диспетчер + handlers + JSON-Logic + batch + autogen каталог).

**Прод (mpb-erp.ru):** только V1 (outbox + worker + webhook + retry/DLQ/HMAC). **Worker не запущен**, V1.5 и v2 НЕ выкачены. UI скрыт через комментарии nav/router. Решение пользователя: «event пока только на локалке для тестов».

**Стратегия:**
1. v2 живёт на локалке для разработки и валидации спецификаций интеграторов.
2. **B2 → прод** одновременно с запуском первого реального consumer'а (предлагаю Telegram-бот). Сейчас прод без worker'а — outbox-строки копятся без доставки, что нормально (V1 уже это умеет).
3. **C1 (Telegram), C2 (1С), C3 (Onboarding doc)** — открываются под июльский старт интеграций.

---

## 6. Файлы реализации

### Backend

```
backend/app/services/
  event_outbox.py         ← V1 + V1.5 + emit_batch_event (v2)
  event_dispatcher.py     ← НОВЫЙ v2: @on / dispatch_before / dispatch_after
  json_logic.py           ← НОВЫЙ v2: фильтр-евалюатор подписок

backend/app/event_handlers/  ← НОВЫЙ v2: декораторные хендлеры
  __init__.py
  contracts.py            ← validate_status_transition, normalize_meta, log_significant
  documents.py            ← validate_before_send, validate_status_progression
  outgoing_documents.py   ← validate_required_fields, stamp_render_meta
  approvals.py            ← require_all_steps_done, require_reject_reason
  leads.py                ← validate_lead_ready_for_conversion, stamp_source_lead_id
  mail.py                 ← validate_recipients
  kp.py                   ← validate_kp_ready
  tasks.py                ← validate_task_status_transition, validate_task_assignee (D4)
  deals.py                ← validate_deal_status_transition (D4)
  signing.py              ← validate_*_sign (document/contract/outgoing) + after_sign logs (E1)

backend/app/routers/integrations/  ← inbound-приёмники (v2.1 + v2.2)
  __init__.py             ← конвенция и docstring паттерна (HMAC → parse → mutate → emit)
  diadoc_inbound.py       ← Диадок (E2): POST /api/v1/integrations/diadoc/inbound
  telegram_inbound.py     ← Telegram Bot API (F4): POST /api/v1/integrations/telegram/inbound
  onec_inbound.py         ← 1С Бухгалтерия 8.3 (F4): POST /api/v1/integrations/onec/inbound
  bank_inbound.py         ← банковские выписки 1С 1.03 (F4): POST /api/v1/integrations/bank/inbound
  gosklyuch_inbound.py    ← Госключ ЭЦП callback (F4): POST /api/v1/integrations/gosklyuch/inbound

backend/app/tools/        ← НОВЫЙ v2
  __init__.py
  dump_event_types.py     ← autogen каталог + --check для CI

backend/app/models/
  event_outbox.py         ← без изменений (v1.5)
  event_subscription.py   ← + condition_json (v2)
  event_delivery_dedup.py ← без изменений (v1.5)
  event_log.py            ← без изменений (pre-existing)

backend/app/routers/
  event_bus.py            ← + POST /simulate DRY-RUN endpoint (v2)
  contracts.py            ← + dispatch_before/after для status_change + emit_event_safe (v2)
  leads.py                ← + dispatch_before для convert + 4 эмиссии (v2)
  tasks.py                ← + after_delete, after_assign (v2)
  outgoing_registry.py    ← + after_create, after_update, after_delete (v2)
  approvals.py            ← + after_start, after_complete, after_reject (v2)

backend/event_outbox_worker.py ← + JSON-Logic gate + X-Event-Schema-Version header (v2)
backend/main.py                ← + discover_handlers() в startup (v2)

backend/migrate_add_event_bus.py
backend/migrate_add_event_dedup.py            (V1.5)
backend/migrate_add_event_causation_chain.py  (V1.5)
backend/migrate_add_event_subscription_condition.py ← НОВЫЙ v2

backend/_smoke_event_dispatcher.py   ← НОВЫЙ v2: 23/23 теста
backend/_smoke_json_logic.py         ← НОВЫЙ v2: 23/23 теста
backend/_smoke_simulate.py           ← НОВЫЙ v2: 23/23 теста (DRY-RUN)
```

### Frontend

```
frontend/src/views/
  IntegrationsOutbox.vue        ← без изменений (V1.5)
  IntegrationsSubscriptions.vue ← без изменений (V1.5)

frontend/src/services/api/eventBus.js
```

В v2 фронт не менялся — приоритет на бэкенд-инфраструктуру для июльских интеграций.

### Документация

```
docs/events.json              ← autogen каталог (117 событий)
docs/EVENTS_API.md            ← оригинальная спека (от коллеги)
docs/EVENTS_ENTITY_REFERENCE.md ← оригинальный справочник (от коллеги)
docs/EVENT_BUS_RESUME_v2.md   ← этот файл
docs/EVENT_BUS_ENTITY_COVERAGE.md ← покрытие событиями по доменам
docs/EVENT_BUS_GAP_ANALYSIS.md ← gap-анализ (что покрыто, что не покрыто, F-фазы)
docs/INTEGRATIONS_ONBOARDING.md ← руководство для команд интеграции
```

---

## 7. Примеры использования (для разработчиков интеграций)

### 7.1. Подписаться на все события сделок:

```sql
INSERT INTO event_subscriptions (id, name, event_type_pattern, target_url, hmac_secret, is_active)
VALUES ('<uuid>', 'Telegram-канал продаж', 'deal.*', 'https://hook.tg/sales', 'secret123', 1);
```

### 7.2. Подписаться только на крупные подписанные контракты:

```sql
INSERT INTO event_subscriptions (
  id, name, event_type_pattern, target_url, hmac_secret, is_active, condition_json
) VALUES (
  '<uuid>', 'BI: крупные контракты',
  'contract.after_*',
  'https://bi.local/webhook',
  'secret456',
  1,
  '{"and": [
    {"==": [{"var": "status"}, "signed"]},
    {">":  [{"var": "amount"}, 1000000]}
  ]}'
);
```

### 7.3. Добавить in-process валидацию:

```python
# backend/app/event_handlers/contracts.py
from app.services.event_dispatcher import on, Cancel, Continue, EventContext

@on("contract.before_send", priority=100, can_cancel=True)
async def require_diadoc_id(ctx: EventContext):
    """Перед отправкой в Диадок проверяем что у договора есть external_id Диадока."""
    if ctx.payload.get("send_channel") == "diadoc" and not ctx.payload.get("diadoc_doc_id"):
        return Cancel(
            "Не указан external_id Диадока — отправка невозможна",
            code="contract.no_diadoc_id",
        )
    return Continue()
```

После добавления и рестарта бэкенда: 
1. Регистрация автоматическая через `discover_handlers()`.
2. Каталог обновится: `python -m app.tools.dump_event_types` → новый хендлер появится в `docs/events.json`.

### 7.4. Batch-импорт от 1С:

```python
# backend/app/routers/bank_imports.py (когда появится)
from app.services.event_outbox import emit_batch_event_safe

@router.post("/import-bank-statement")
async def import_statement(file: UploadFile, db: AsyncSession = Depends(get_db)):
    transactions = parse_xml(await file.read())
    saved = []
    for tx in transactions:
        item = await TreasuryTransaction.create(db, **tx)
        saved.append({"id": str(item.id), "amount": float(item.amount)})

    # Одно событие на всю пачку — внешний consumer получит её атомарно.
    await emit_batch_event_safe(
        db,
        event_type="treasury_transaction.batch_imported",
        entity_type="treasury_transaction",
        items=saved,
        parent_id=None,
        summary={"total_amount": sum(i["amount"] for i in saved), "count": len(saved)},
    )
    return {"imported": len(saved)}
```

---

## 8. Регрессия

- `_smoke_event_dispatcher.py` → **23/23 passed** (Continue/Cancel/Mutate, приоритеты, sync+async, exception isolation, discovery, contracts POC, lead/outgoing/mail Cancel-сценарии).
- `_smoke_json_logic.py` → **23/23 passed** (var, comparisons, booleans, in, missing, realistic conditions, defensive).
- `_smoke_simulate.py` → **23/23 passed** (Cancel/Mutate/Continue/ignored/error в DRY-RUN; ctx.payload не мутируется; real contracts handler).
- `dump_event_types` → **117 events на 33 entities** (`docs/events.json`).
- 5 inbound endpoints зарегистрированы: `/api/v1/integrations/{diadoc,telegram,onec,bank,gosklyuch}/inbound` — открыты через `open_prefixes` (без cookie-auth, HMAC внутри).

---

## 9. Краткий вердикт

**Из спеки v1 (`EVENTS_API.md`):** реализованы все базовые требования инфраструктуры **+** ключевые «архитектурные» (catalog, before-фаза, conditions). НЕ реализованы: UI-конструктор хендлеров, redirect-таблица, simulate — намеренно, как антипаттерны для нашего профиля использования.

**Из спеки v2 (Bitrix-style ambitions):** реализован runtime (a) in-process before + (c) out-of-process outbox. Архитектурно покрыто 80% спеки. Остаются: full coverage всех сущностей (по запросу), manifest подписок (после первой схемной эволюции), simulate (после 5+ консьюмеров).

**Архитектурная позиция:**
1. Фундамент готов под все 8 планируемых июльских интеграций (Telegram, 1С, Банк, Диадок, ЭЦП, Почта, BI, СОДы).
2. Pluggable validation и mutation обеспечены через `@on`-декораторы — масштабируются на N команд интеграций без конфликтов.
3. JSON-Logic условия + batch-события + payload-versioning — то, чего реально не хватало в V1.5 для бэтчевых и фильтрованных консьюмеров.
4. Развёрнут только на локалке. На прод выкатывается под первый реальный consumer (B2 + C1 в одном деплое).
