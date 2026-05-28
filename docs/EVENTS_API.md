# Event API

Документ описывает целевую структуру событийного слоя для CRM/ERP. Сейчас в проекте уже есть `EventLog`, `AuditLog` и `NotificationRule`, но полноценного настраиваемого event bus пока нет. Эта спецификация фиксирует, как его стоит развивать.

## Цели

- Дать каждой сущности единый набор событий жизненного цикла.
- Разделить события до действия (`before_*`) и после действия (`after_*`).
- Позволить обработчикам отменять действие, изменять payload или переадресовывать выполнение.
- Поддержать внутренние функции, webhooks, очереди, workflow и уведомления.
- Сохранять историю события, обработчиков и результата выполнения.

## Базовая Терминология

- `event_key` - уникальный ключ события, например `deal.after_update`.
- `entity_type` - тип сущности, например `deal`, `stage`, `task`.
- `entity_id` - идентификатор конкретной сущности.
- `phase` - фаза события: `before` или `after`.
- `action` - действие: `create`, `update`, `delete`, `close`, `assign`, `render`.
- `handler` - обработчик события.
- `redirect` - переадресация события на другой обработчик.

## Базовая Структура События

```json
{
  "id": "2f6cf6e8-40a1-4e4b-9d7b-e10ce8d14d2e",
  "event_key": "deal.after_update",
  "entity_type": "deal",
  "entity_id": "1d3ff5c8-4037-4603-a5b5-43c765a7d9f7",
  "phase": "after",
  "action": "update",
  "payload": {
    "deal_title": "Строительство склада",
    "changes": {
      "status": {
        "before": "active",
        "after": "paused"
      }
    }
  },
  "context": {
    "user_id": "9e2b70c2-9c09-4513-88b9-4e62f37b3ef8",
    "source": "api",
    "request_id": "req-20260522-001"
  },
  "result": {
    "status": "handled",
    "redirected_to": null
  },
  "created_at": "2026-05-22T12:00:00Z"
}
```

## Предлагаемые Таблицы

### `event_types`

Справочник доступных событий.

```text
id
entity_type
action
phase
event_key
title
description
is_active
created_at
updated_at
```

Пример:

```json
{
  "entity_type": "outgoing_document",
  "action": "render",
  "phase": "before",
  "event_key": "outgoing_document.before_render",
  "title": "Перед рендером исходящего документа",
  "is_active": true
}
```

### `event_handlers`

Настраиваемые обработчики событий.

```text
id
name
event_key
handler_type
handler_target
priority
is_active
can_cancel
can_mutate_payload
timeout_seconds
conditions_json
created_at
updated_at
```

Типы `handler_type`:

```text
internal_function
http_webhook
notification
workflow
queue
```

Пример:

```json
{
  "name": "Проверка договора перед рендером",
  "event_key": "outgoing_document.before_render",
  "handler_type": "internal_function",
  "handler_target": "app.events.outgoing.validate_contract_before_render",
  "priority": 10,
  "is_active": true,
  "can_cancel": true,
  "can_mutate_payload": false,
  "conditions_json": {
    "document_kind": ["act", "invoice", "upd"]
  }
}
```

### `event_redirects`

Правила переадресации обработчика.

```text
id
event_key
from_handler_target
to_handler_target
condition_json
is_active
created_at
updated_at
```

Пример:

```json
{
  "event_key": "outgoing_document.before_render",
  "from_handler_target": "app.events.outgoing.render_default",
  "to_handler_target": "app.events.outgoing.render_structured_editor",
  "condition_json": {
    "editor_mode": "structured"
  },
  "is_active": true
}
```

### `event_dispatches`

История выполнения обработчиков.

```text
id
event_id
handler_id
status
input_json
output_json
error
started_at
finished_at
```

Статусы:

```text
pending
handled
skipped
redirected
cancelled
failed
timeout
```

## Стандартные События Сущностей

Для большинства сущностей:

```text
{entity}.before_create
{entity}.after_create
{entity}.before_update
{entity}.after_update
{entity}.before_delete
{entity}.after_delete
{entity}.before_status_change
{entity}.after_status_change
{entity}.before_link
{entity}.after_link
{entity}.before_unlink
{entity}.after_unlink
```

## События По Доменам

### Сделки И Лиды

```text
deal.before_create
deal.after_create
deal.before_update
deal.after_update
deal.before_delete
deal.after_delete
deal.after_gip_assign
deal.after_status_change

lead.before_create
lead.after_create
lead.before_update
lead.after_update
lead.before_convert_to_deal
lead.after_convert_to_deal
```

### Компании И Пользователи

```text
company.before_create
company.after_create
company.before_update
company.after_update
company.after_document_attach
company.after_user_link

user.after_create
user.before_update
user.after_update
user.after_role_change
user.after_login

role.before_permission_change
role.after_permission_change
```

### Этапы И Исполнение

```text
stage.before_create
stage.after_create
stage.before_update
stage.after_update
stage.before_close
stage.after_close
stage.before_dependency_change
stage.after_dependency_change
stage.before_recalculate_dates
stage.after_recalculate_dates

stage_dependency.before_create
stage_dependency.after_create
stage_dependency.before_delete
stage_dependency.after_delete

deal_product.before_add_to_deal
deal_product.after_add_to_deal
deal_product.before_price_change
deal_product.after_price_change

stage_product_assignment.before_assign
stage_product_assignment.after_assign
stage_product_assignment.before_executor_change
stage_product_assignment.after_executor_change

work_result.before_submit
work_result.after_submit
work_result.before_review
work_result.after_review
```

### Договоры И Документы

```text
contract.before_create
contract.after_create
contract.before_update
contract.after_update
contract.after_document_attach
contract.after_status_change

contract_document.before_upload
contract_document.after_upload
contract_document.before_link_product
contract_document.after_link_product

document.before_create
document.after_create
document.before_send
document.after_send
document.before_receive
document.after_receive
document.after_status_change

document_template.before_create
document_template.after_create
document_template.before_publish_version
document_template.after_publish_version
```

### Исходящие Документы

```text
outgoing_document.before_create
outgoing_document.after_create
outgoing_document.before_update
outgoing_document.after_update
outgoing_document.before_number_generate
outgoing_document.after_number_generate
outgoing_document.before_render
outgoing_document.after_render
outgoing_document.before_version_create
outgoing_document.after_version_create
outgoing_document.before_delete
outgoing_document.after_delete
```

### Финансы

```text
treasury_transaction.after_import
treasury_transaction.before_allocate
treasury_transaction.after_allocate
treasury_transaction.before_link
treasury_transaction.after_link
treasury_transaction.before_ignore
treasury_transaction.after_ignore

treasury_allocation.before_create
treasury_allocation.after_create
treasury_allocation.before_update
treasury_allocation.after_update
treasury_allocation.after_delete

income_expense_entry.before_create
income_expense_entry.after_create
income_expense_entry.before_update
income_expense_entry.after_update

financial_plan.before_create
financial_plan.after_create
financial_plan.before_payment_status_change
financial_plan.after_payment_status_change

penalty_rule.before_apply
penalty_rule.after_apply
```

### Задачи И Коммуникации

```text
task.before_create
task.after_create
task.before_assign
task.after_assign
task.before_status_change
task.after_status_change
task.before_deadline_change
task.after_deadline_change
task.after_message_add
task.after_attachment_add

mail_message.after_sync
mail_message.after_receive
mail_message.before_send
mail_message.after_send
mail_message.after_link_entity

notification.before_create
notification.after_create
notification.before_deliver
notification.after_deliver
```

### Согласования

```text
approval_instance.before_start
approval_instance.after_start
approval_instance.before_step_complete
approval_instance.after_step_complete
approval_instance.before_complete
approval_instance.after_complete
approval_instance.before_reject
approval_instance.after_reject
```

## Поведение `before_*`

События `before_*` выполняются до изменения данных и до commit.

Обработчик может вернуть:

```json
{
  "status": "continue"
}
```

```json
{
  "status": "cancel",
  "reason": "Нельзя закрыть этап без даты закрытия"
}
```

```json
{
  "status": "mutate",
  "payload_patch": {
    "close_date": "2026-05-22"
  }
}
```

```json
{
  "status": "redirect",
  "redirect_to": "app.events.stages.close_with_dependency_recalculation"
}
```

## Поведение `after_*`

События `after_*` выполняются после успешного изменения данных.

Типичные действия:

- запись в `event_logs`;
- запись в `audit_logs`;
- создание уведомления;
- отправка Telegram/email;
- постановка задачи в очередь;
- пересчет связанных агрегатов;
- обновление data health.

## API Событий

### Список типов событий

```http
GET /api/v1/events/types
```

Ответ:

```json
[
  {
    "id": "uuid",
    "event_key": "deal.after_update",
    "entity_type": "deal",
    "action": "update",
    "phase": "after",
    "title": "После обновления сделки",
    "is_active": true
  }
]
```

### Создать тип события

```http
POST /api/v1/events/types
```

```json
{
  "entity_type": "stage",
  "action": "close",
  "phase": "before",
  "event_key": "stage.before_close",
  "title": "Перед закрытием этапа",
  "description": "Валидация этапа перед закрытием",
  "is_active": true
}
```

### Обновить тип события

```http
PUT /api/v1/events/types/{id}
```

### Удалить или отключить тип события

```http
DELETE /api/v1/events/types/{id}
```

Для боевой системы предпочтительно не удалять, а переводить `is_active=false`.

## API Обработчиков

### Список обработчиков

```http
GET /api/v1/events/handlers?event_key=stage.before_close
```

### Создать обработчик

```http
POST /api/v1/events/handlers
```

```json
{
  "name": "Проверить зависимости этапа",
  "event_key": "stage.before_close",
  "handler_type": "internal_function",
  "handler_target": "app.events.stages.validate_dependencies_before_close",
  "priority": 10,
  "is_active": true,
  "can_cancel": true,
  "can_mutate_payload": false,
  "timeout_seconds": 10,
  "conditions_json": {
    "stage_type": "stage"
  }
}
```

### Обновить обработчик

```http
PUT /api/v1/events/handlers/{id}
```

### Отключить обработчик

```http
DELETE /api/v1/events/handlers/{id}
```

## API Переадресаций

### Список переадресаций

```http
GET /api/v1/events/redirects
```

### Создать переадресацию

```http
POST /api/v1/events/redirects
```

```json
{
  "event_key": "outgoing_document.before_render",
  "from_handler_target": "app.events.outgoing.render_default",
  "to_handler_target": "app.events.outgoing.render_structured_editor",
  "condition_json": {
    "editor_mode": "structured"
  },
  "is_active": true
}
```

## API Генерации И Диагностики

### Ручная генерация события

```http
POST /api/v1/events/emit
```

```json
{
  "event_key": "deal.after_update",
  "entity_type": "deal",
  "entity_id": "1d3ff5c8-4037-4603-a5b5-43c765a7d9f7",
  "payload": {
    "deal_title": "Строительство склада",
    "changes": {
      "status": {
        "before": "active",
        "after": "paused"
      }
    }
  }
}
```

Ответ:

```json
{
  "event_id": "2f6cf6e8-40a1-4e4b-9d7b-e10ce8d14d2e",
  "status": "handled",
  "dispatches": [
    {
      "handler": "Создать уведомление ГИП",
      "status": "handled"
    }
  ]
}
```

### Симуляция события

```http
POST /api/v1/events/simulate
```

```json
{
  "event_key": "stage.before_close",
  "entity_type": "stage",
  "entity_id": "71dd4e42-9f1c-44a0-9c91-9b5cc655d6f2",
  "payload": {
    "close_date": "2026-05-22",
    "stage_type": "stage"
  }
}
```

Ответ:

```json
{
  "event_key": "stage.before_close",
  "matched_handlers": [
    {
      "name": "Проверить зависимости этапа",
      "handler_target": "app.events.stages.validate_dependencies_before_close",
      "priority": 10,
      "can_cancel": true
    }
  ],
  "redirects": []
}
```

### История событий

```http
GET /api/v1/events/logs
```

Фильтры:

```text
entity_type
entity_id
event_key
action
phase
created_by
date_from
date_to
status
```

### События конкретной сущности

```http
GET /api/v1/events/entity/{entity_type}/{entity_id}
```

Пример:

```http
GET /api/v1/events/entity/deal/1d3ff5c8-4037-4603-a5b5-43c765a7d9f7
```

## Пример: Закрытие Этапа

Поток:

```text
1. API получает запрос на закрытие этапа.
2. Dispatcher вызывает stage.before_close.
3. Обработчик проверяет зависимости.
4. Если проверка успешна, backend закрывает этап.
5. После commit вызывается stage.after_close.
6. Система пересчитывает зависимые даты, пишет EventLog/AuditLog, создает уведомления.
```

Пример `before` payload:

```json
{
  "event_key": "stage.before_close",
  "entity_type": "stage",
  "entity_id": "stage-id",
  "payload": {
    "deal_id": "deal-id",
    "stage_name": "Монтаж",
    "close_date": "2026-05-22",
    "status": "completed"
  }
}
```

Пример отмены:

```json
{
  "status": "cancel",
  "reason": "Нельзя закрыть этап: не закрыт предшествующий этап"
}
```

## Пример: Рендер Исходящего Документа

```text
outgoing_document.before_render
  -> проверить договор
  -> проверить номер
  -> выбрать renderer
  -> при editor_mode=structured переадресовать на structured renderer
  -> outgoing_document.after_render
```

Пример переадресации:

```json
{
  "status": "redirect",
  "redirect_to": "app.events.outgoing.render_structured_editor",
  "payload_patch": {
    "renderer": "structured"
  }
}
```

## Интеграция С Текущим Кодом

Сейчас в проекте есть:

- `EventLog` - простой журнал событий.
- `AuditLog` - системный аудит.
- `NotificationRule` - правила уведомлений по `trigger`.
- `log_event(...)` - helper, который пишет событие и audit log.

Целевой поток:

```text
router/service
  -> event_dispatcher.emit("entity.before_action")
  -> business action
  -> commit
  -> event_dispatcher.emit("entity.after_action")
  -> EventLog
  -> AuditLog
  -> NotificationRule
```

`log_event(...)` стоит сохранить как совместимый слой, но внутри перевести на новый dispatcher.

## Правила Безопасности

- Из UI нельзя разрешать произвольный Python path без allowlist.
- `internal_function` должен выбирать обработчик только из зарегистрированного реестра.
- `http_webhook` должен иметь timeout, retry policy и лог ошибок.
- `before_*` обработчики должны быть короткими и детерминированными.
- `after_*` тяжелые задачи лучше отправлять в очередь.
- Нельзя позволять обычному пользователю менять обработчики событий. Минимум: superuser/admin.

## Минимальный План Внедрения

1. Добавить модели `EventType`, `EventHandler`, `EventRedirect`, `EventDispatch`.
2. Добавить `event_dispatcher`.
3. Зарегистрировать allowlist внутренних обработчиков.
4. Подключить dispatcher к `log_event(...)`.
5. Начать с ключевых событий: `deal`, `stage`, `task`, `outgoing_document`, `contract`, `treasury_transaction`.
6. Добавить API управления типами, обработчиками и переадресациями.
7. Добавить `simulate` endpoint для безопасной проверки.
8. Постепенно заменить прямые вызовы `log_event(...)` на `before/after` события там, где нужна отмена или мутация payload.
