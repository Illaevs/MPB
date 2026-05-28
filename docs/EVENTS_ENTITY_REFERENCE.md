# Entity Events Reference

Справочник описывает события для сущностей проекта в стиле Bitrix: событие имеет строковый код, обработчики регистрируются отдельно, обработчик можно отключить, заменить, переадресовать или поставить выше по приоритету.

Документ является проектной спецификацией. Он не означает, что все перечисленные API уже реализованы в текущем коде.

## Bitrix-Style Модель

В Bitrix-подходе бизнес-код не вызывает конкретную функцию напрямую. Он генерирует событие:

```python
result = await events.emit(
    "deal.before_update",
    entity_type="deal",
    entity_id=deal_id,
    payload=payload,
    context={"user_id": current_user.id},
)
```

А система сама находит зарегистрированные обработчики:

```python
events.register(
    event_key="deal.before_update",
    handler="app.event_handlers.deals.validate_deal_update",
    priority=100,
    can_cancel=True,
    can_mutate_payload=True,
)
```

Переопределение функции события делается через redirect:

```python
events.redirect(
    event_key="outgoing_document.before_render",
    from_handler="app.event_handlers.outgoing.render_default",
    to_handler="app.event_handlers.outgoing.render_structured",
    condition={"editor_mode": "structured"},
)
```

## Универсальные События Для Каждой Сущности

Эти события доступны для каждой сущности из справочника ниже.

### `{entity}.before_create`

Вызывается перед созданием записи.

```http
POST /api/v1/events/emit
```

```json
{
  "event_key": "deal.before_create",
  "entity_type": "deal",
  "payload": {
    "title": "Новая сделка"
  }
}
```

Обработчик может отменить создание:

```json
{
  "status": "cancel",
  "reason": "Не указан заказчик"
}
```

### `{entity}.after_create`

Вызывается после создания записи.

```json
{
  "event_key": "deal.after_create",
  "entity_type": "deal",
  "entity_id": "deal-id",
  "payload": {
    "title": "Новая сделка"
  }
}
```

Типичные действия: лог, уведомление, аудит, постановка задачи.

### `{entity}.before_update`

Вызывается перед обновлением.

```json
{
  "event_key": "deal.before_update",
  "entity_type": "deal",
  "entity_id": "deal-id",
  "payload": {
    "changes": {
      "status": {
        "before": "active",
        "after": "paused"
      }
    }
  }
}
```

Обработчик может изменить входные данные:

```json
{
  "status": "mutate",
  "payload_patch": {
    "updated_by_event": true
  }
}
```

### `{entity}.after_update`

Вызывается после обновления.

```json
{
  "event_key": "deal.after_update",
  "entity_type": "deal",
  "entity_id": "deal-id",
  "payload": {
    "changes": {
      "status": {
        "before": "active",
        "after": "paused"
      }
    }
  }
}
```

### `{entity}.before_delete`

Вызывается перед удалением.

```json
{
  "event_key": "deal.before_delete",
  "entity_type": "deal",
  "entity_id": "deal-id",
  "payload": {
    "reason": "manual_delete"
  }
}
```

Обработчик может запретить удаление:

```json
{
  "status": "cancel",
  "reason": "Нельзя удалить сделку с договорами"
}
```

### `{entity}.after_delete`

Вызывается после удаления.

```json
{
  "event_key": "deal.after_delete",
  "entity_type": "deal",
  "entity_id": "deal-id",
  "payload": {
    "deleted": true
  }
}
```

### `{entity}.before_status_change`

Вызывается перед сменой статуса.

```json
{
  "event_key": "task.before_status_change",
  "entity_type": "task",
  "entity_id": "task-id",
  "payload": {
    "status_before": "in_progress",
    "status_after": "completed"
  }
}
```

### `{entity}.after_status_change`

Вызывается после смены статуса.

```json
{
  "event_key": "task.after_status_change",
  "entity_type": "task",
  "entity_id": "task-id",
  "payload": {
    "status_before": "in_progress",
    "status_after": "completed"
  }
}
```

### `{entity}.before_link`

Вызывается перед созданием связи.

```json
{
  "event_key": "contract.before_link",
  "entity_type": "contract",
  "entity_id": "contract-id",
  "payload": {
    "linked_entity_type": "deal",
    "linked_entity_id": "deal-id"
  }
}
```

### `{entity}.after_link`

Вызывается после создания связи.

```json
{
  "event_key": "contract.after_link",
  "entity_type": "contract",
  "entity_id": "contract-id",
  "payload": {
    "linked_entity_type": "deal",
    "linked_entity_id": "deal-id"
  }
}
```

### `{entity}.before_unlink`

Вызывается перед удалением связи.

```json
{
  "event_key": "contract.before_unlink",
  "entity_type": "contract",
  "entity_id": "contract-id",
  "payload": {
    "linked_entity_type": "deal",
    "linked_entity_id": "deal-id"
  }
}
```

### `{entity}.after_unlink`

Вызывается после удаления связи.

```json
{
  "event_key": "contract.after_unlink",
  "entity_type": "contract",
  "entity_id": "contract-id",
  "payload": {
    "linked_entity_type": "deal",
    "linked_entity_id": "deal-id"
  }
}
```

## API Регистрации И Переопределения

### Зарегистрировать обработчик

```http
POST /api/v1/events/handlers
```

```json
{
  "event_key": "stage.before_close",
  "name": "Проверить зависимости этапа",
  "handler_type": "internal_function",
  "handler_target": "app.event_handlers.stages.validate_dependencies",
  "priority": 100,
  "can_cancel": true,
  "can_mutate_payload": false,
  "is_active": true
}
```

### Переопределить обработчик

```http
POST /api/v1/events/redirects
```

```json
{
  "event_key": "stage.before_close",
  "from_handler_target": "app.event_handlers.stages.close_default",
  "to_handler_target": "app.event_handlers.stages.close_with_dependency_recalc",
  "condition_json": {
    "has_dependencies": true
  },
  "is_active": true
}
```

### Отключить стандартный обработчик

```http
PUT /api/v1/events/handlers/{handler_id}
```

```json
{
  "is_active": false
}
```

### Проверить, что будет вызвано

```http
POST /api/v1/events/simulate
```

```json
{
  "event_key": "outgoing_document.before_render",
  "entity_type": "outgoing_document",
  "entity_id": "document-id",
  "payload": {
    "document_kind": "invoice",
    "editor_mode": "structured"
  }
}
```

Ответ:

```json
{
  "event_key": "outgoing_document.before_render",
  "matched_handlers": [
    {
      "handler_target": "app.event_handlers.outgoing.validate_render_context",
      "priority": 100
    },
    {
      "handler_target": "app.event_handlers.outgoing.render_structured",
      "priority": 50,
      "redirected_from": "app.event_handlers.outgoing.render_default"
    }
  ]
}
```

## Справочник Сущностей И Событий

Формат:

```text
entity_type
  universal: все универсальные события из раздела выше
  domain: доменные события сущности
```

Каждое доменное событие вызывается тем же API `POST /api/v1/events/emit`.

## CRM Core

### `deal`

Сущность: сделка/проект.

```text
universal:
  deal.before_create
  deal.after_create
  deal.before_update
  deal.after_update
  deal.before_delete
  deal.after_delete
  deal.before_status_change
  deal.after_status_change

domain:
  deal.before_gip_assign
  deal.after_gip_assign
  deal.before_vat_change
  deal.after_vat_change
  deal.after_activity_add
  deal.before_recalculate_total
  deal.after_recalculate_total
```

Пример:

```json
{
  "event_key": "deal.after_gip_assign",
  "entity_type": "deal",
  "entity_id": "deal-id",
  "payload": {
    "user_id": "user-id",
    "deal_title": "Проект"
  }
}
```

### `lead`

```text
universal:
  lead.before_create
  lead.after_create
  lead.before_update
  lead.after_update
  lead.before_delete
  lead.after_delete
  lead.before_status_change
  lead.after_status_change

domain:
  lead.before_convert_to_deal
  lead.after_convert_to_deal
  lead.before_product_add
  lead.after_product_add
```

```json
{
  "event_key": "lead.before_convert_to_deal",
  "entity_type": "lead",
  "entity_id": "lead-id",
  "payload": {
    "target_deal_title": "Новая сделка"
  }
}
```

### `company`

```text
universal:
  company.before_create
  company.after_create
  company.before_update
  company.after_update
  company.before_delete
  company.after_delete

domain:
  company.before_user_link
  company.after_user_link
  company.before_document_attach
  company.after_document_attach
  company.before_accreditation_change
  company.after_accreditation_change
```

```json
{
  "event_key": "company.after_document_attach",
  "entity_type": "company",
  "entity_id": "company-id",
  "payload": {
    "document_id": "company-document-id",
    "doc_type": "license"
  }
}
```

### `user`

```text
universal:
  user.before_create
  user.after_create
  user.before_update
  user.after_update
  user.before_delete
  user.after_delete

domain:
  user.after_login
  user.after_logout
  user.before_role_change
  user.after_role_change
  user.before_avatar_update
  user.after_avatar_update
  user.before_two_factor_enable
  user.after_two_factor_enable
```

```json
{
  "event_key": "user.after_role_change",
  "entity_type": "user",
  "entity_id": "user-id",
  "payload": {
    "role_before": "old-role-id",
    "role_after": "new-role-id"
  }
}
```

### `role`

```text
universal:
  role.before_create
  role.after_create
  role.before_update
  role.after_update
  role.before_delete
  role.after_delete

domain:
  role.before_permission_change
  role.after_permission_change
```

```json
{
  "event_key": "role.after_permission_change",
  "entity_type": "role",
  "entity_id": "role-id",
  "payload": {
    "section": "projects",
    "read_all": true,
    "read_assigned": false
  }
}
```

### `role_permission`

```text
universal:
  role_permission.before_create
  role_permission.after_create
  role_permission.before_update
  role_permission.after_update
  role_permission.before_delete
  role_permission.after_delete
```

```json
{
  "event_key": "role_permission.after_update",
  "entity_type": "role_permission",
  "entity_id": "permission-id",
  "payload": {
    "section": "finance",
    "changes": {
      "read_all": {
        "before": false,
        "after": true
      }
    }
  }
}
```

### `company_user_link`

```text
universal:
  company_user_link.before_create
  company_user_link.after_create
  company_user_link.before_update
  company_user_link.after_update
  company_user_link.before_delete
  company_user_link.after_delete
```

```json
{
  "event_key": "company_user_link.after_create",
  "entity_type": "company_user_link",
  "entity_id": "link-id",
  "payload": {
    "company_id": "company-id",
    "user_id": "user-id",
    "link_type": "leader"
  }
}
```

### `deal_gip`

```text
universal:
  deal_gip.before_create
  deal_gip.after_create
  deal_gip.before_delete
  deal_gip.after_delete
```

```json
{
  "event_key": "deal_gip.after_create",
  "entity_type": "deal_gip",
  "entity_id": "deal-gip-id",
  "payload": {
    "deal_id": "deal-id",
    "user_id": "user-id"
  }
}
```

## Catalog And Products

### `product_category`

```text
universal:
  product_category.before_create
  product_category.after_create
  product_category.before_update
  product_category.after_update
  product_category.before_delete
  product_category.after_delete
```

```json
{
  "event_key": "product_category.after_create",
  "entity_type": "product_category",
  "entity_id": "category-id",
  "payload": {
    "name": "Монтаж"
  }
}
```

### `product`

```text
universal:
  product.before_create
  product.after_create
  product.before_update
  product.after_update
  product.before_delete
  product.after_delete

domain:
  product.before_price_change
  product.after_price_change
```

```json
{
  "event_key": "product.after_price_change",
  "entity_type": "product",
  "entity_id": "product-id",
  "payload": {
    "price_before": 1000,
    "price_after": 1200
  }
}
```

### `deal_product`

```text
universal:
  deal_product.before_create
  deal_product.after_create
  deal_product.before_update
  deal_product.after_update
  deal_product.before_delete
  deal_product.after_delete

domain:
  deal_product.before_add_to_deal
  deal_product.after_add_to_deal
  deal_product.before_price_change
  deal_product.after_price_change
  deal_product.before_stage_assign
  deal_product.after_stage_assign
```

```json
{
  "event_key": "deal_product.after_add_to_deal",
  "entity_type": "deal_product",
  "entity_id": "deal-product-id",
  "payload": {
    "deal_id": "deal-id",
    "product_id": "product-id",
    "quantity": 2
  }
}
```

### `lead_product`

```text
universal:
  lead_product.before_create
  lead_product.after_create
  lead_product.before_update
  lead_product.after_update
  lead_product.before_delete
  lead_product.after_delete

domain:
  lead_product.before_convert_to_deal_product
  lead_product.after_convert_to_deal_product
```

```json
{
  "event_key": "lead_product.after_convert_to_deal_product",
  "entity_type": "lead_product",
  "entity_id": "lead-product-id",
  "payload": {
    "deal_product_id": "deal-product-id"
  }
}
```

## Stages And Execution

### `stage`

```text
universal:
  stage.before_create
  stage.after_create
  stage.before_update
  stage.after_update
  stage.before_delete
  stage.after_delete
  stage.before_status_change
  stage.after_status_change

domain:
  stage.before_close
  stage.after_close
  stage.before_dependency_change
  stage.after_dependency_change
  stage.before_products_change
  stage.after_products_change
  stage.before_recalculate_dates
  stage.after_recalculate_dates
  stage.before_copy
  stage.after_copy
```

```json
{
  "event_key": "stage.before_close",
  "entity_type": "stage",
  "entity_id": "stage-id",
  "payload": {
    "deal_id": "deal-id",
    "close_date": "2026-05-22"
  }
}
```

Переопределение закрытия:

```json
{
  "event_key": "stage.before_close",
  "from_handler_target": "app.event_handlers.stages.close_default",
  "to_handler_target": "app.event_handlers.stages.close_with_dependency_recalc",
  "condition_json": {
    "has_dependencies": true
  }
}
```

### `stage_dependency`

```text
universal:
  stage_dependency.before_create
  stage_dependency.after_create
  stage_dependency.before_update
  stage_dependency.after_update
  stage_dependency.before_delete
  stage_dependency.after_delete

domain:
  stage_dependency.before_propagate
  stage_dependency.after_propagate
```

```json
{
  "event_key": "stage_dependency.after_create",
  "entity_type": "stage_dependency",
  "entity_id": "dependency-id",
  "payload": {
    "predecessor_id": "stage-id",
    "successor_id": "stage-id",
    "dependency_type": "FS"
  }
}
```

### `stage_product_link`

```text
universal:
  stage_product_link.before_create
  stage_product_link.after_create
  stage_product_link.before_delete
  stage_product_link.after_delete
```

```json
{
  "event_key": "stage_product_link.after_create",
  "entity_type": "stage_product_link",
  "entity_id": "link-id",
  "payload": {
    "stage_id": "stage-id",
    "product_id": "product-id"
  }
}
```

### `stage_product_assignment`

```text
universal:
  stage_product_assignment.before_create
  stage_product_assignment.after_create
  stage_product_assignment.before_update
  stage_product_assignment.after_update
  stage_product_assignment.before_delete
  stage_product_assignment.after_delete

domain:
  stage_product_assignment.before_assign
  stage_product_assignment.after_assign
  stage_product_assignment.before_executor_change
  stage_product_assignment.after_executor_change
  stage_product_assignment.before_contract_link
  stage_product_assignment.after_contract_link
```

```json
{
  "event_key": "stage_product_assignment.after_assign",
  "entity_type": "stage_product_assignment",
  "entity_id": "assignment-id",
  "payload": {
    "deal_id": "deal-id",
    "stage_id": "stage-id",
    "product_id": "product-id",
    "subcontractor_card_id": "card-id"
  }
}
```

### `stage_product_subtask`

```text
universal:
  stage_product_subtask.before_create
  stage_product_subtask.after_create
  stage_product_subtask.before_update
  stage_product_subtask.after_update
  stage_product_subtask.before_delete
  stage_product_subtask.after_delete
  stage_product_subtask.before_status_change
  stage_product_subtask.after_status_change
```

```json
{
  "event_key": "stage_product_subtask.after_status_change",
  "entity_type": "stage_product_subtask",
  "entity_id": "subtask-id",
  "payload": {
    "status_before": "planned",
    "status_after": "done"
  }
}
```

### `stage_result`

```text
universal:
  stage_result.before_create
  stage_result.after_create
  stage_result.before_update
  stage_result.after_update
  stage_result.before_delete
  stage_result.after_delete

domain:
  stage_result.before_submit
  stage_result.after_submit
  stage_result.before_review
  stage_result.after_review
```

```json
{
  "event_key": "stage_result.after_review",
  "entity_type": "stage_result",
  "entity_id": "result-id",
  "payload": {
    "review_status": "approved"
  }
}
```

### `work_result`

```text
universal:
  work_result.before_create
  work_result.after_create
  work_result.before_update
  work_result.after_update
  work_result.before_delete
  work_result.after_delete
  work_result.before_status_change
  work_result.after_status_change

domain:
  work_result.before_submit
  work_result.after_submit
  work_result.before_accept
  work_result.after_accept
  work_result.before_reject
  work_result.after_reject
```

```json
{
  "event_key": "work_result.after_accept",
  "entity_type": "work_result",
  "entity_id": "work-result-id",
  "payload": {
    "deal_id": "deal-id",
    "stage_id": "stage-id"
  }
}
```

## Subcontractors

### `subcontractor_card`

```text
universal:
  subcontractor_card.before_create
  subcontractor_card.after_create
  subcontractor_card.before_update
  subcontractor_card.after_update
  subcontractor_card.before_delete
  subcontractor_card.after_delete

domain:
  subcontractor_card.before_company_link
  subcontractor_card.after_company_link
```

```json
{
  "event_key": "subcontractor_card.after_company_link",
  "entity_type": "subcontractor_card",
  "entity_id": "card-id",
  "payload": {
    "company_id": "company-id"
  }
}
```

### `subcontractor_product`

```text
universal:
  subcontractor_product.before_create
  subcontractor_product.after_create
  subcontractor_product.before_update
  subcontractor_product.after_update
  subcontractor_product.before_delete
  subcontractor_product.after_delete
```

```json
{
  "event_key": "subcontractor_product.after_create",
  "entity_type": "subcontractor_product",
  "entity_id": "subcontractor-product-id",
  "payload": {
    "subcontractor_card_id": "card-id",
    "product_id": "product-id"
  }
}
```

### `subcontractor_stage`

```text
universal:
  subcontractor_stage.before_create
  subcontractor_stage.after_create
  subcontractor_stage.before_update
  subcontractor_stage.after_update
  subcontractor_stage.before_delete
  subcontractor_stage.after_delete
  subcontractor_stage.before_status_change
  subcontractor_stage.after_status_change

domain:
  subcontractor_stage.before_close
  subcontractor_stage.after_close
  subcontractor_stage.before_dependency_change
  subcontractor_stage.after_dependency_change
```

```json
{
  "event_key": "subcontractor_stage.before_close",
  "entity_type": "subcontractor_stage",
  "entity_id": "subcontractor-stage-id",
  "payload": {
    "close_date": "2026-05-22"
  }
}
```

### `subcontractor_stage_dependency`

```text
universal:
  subcontractor_stage_dependency.before_create
  subcontractor_stage_dependency.after_create
  subcontractor_stage_dependency.before_delete
  subcontractor_stage_dependency.after_delete
```

```json
{
  "event_key": "subcontractor_stage_dependency.after_create",
  "entity_type": "subcontractor_stage_dependency",
  "entity_id": "dependency-id",
  "payload": {
    "predecessor_id": "stage-id",
    "successor_id": "stage-id"
  }
}
```

## Contracts And Documents

### `contract`

```text
universal:
  contract.before_create
  contract.after_create
  contract.before_update
  contract.after_update
  contract.before_delete
  contract.after_delete
  contract.before_status_change
  contract.after_status_change

domain:
  contract.before_deal_link
  contract.after_deal_link
  contract.before_subcontractor_link
  contract.after_subcontractor_link
  contract.before_document_attach
  contract.after_document_attach
```

```json
{
  "event_key": "contract.after_document_attach",
  "entity_type": "contract",
  "entity_id": "contract-id",
  "payload": {
    "contract_document_id": "document-id",
    "doc_type": "act"
  }
}
```

### `contract_document`

```text
universal:
  contract_document.before_create
  contract_document.after_create
  contract_document.before_update
  contract_document.after_update
  contract_document.before_delete
  contract_document.after_delete

domain:
  contract_document.before_upload
  contract_document.after_upload
  contract_document.before_product_link
  contract_document.after_product_link
```

```json
{
  "event_key": "contract_document.after_upload",
  "entity_type": "contract_document",
  "entity_id": "contract-document-id",
  "payload": {
    "contract_id": "contract-id",
    "file_name": "act.pdf"
  }
}
```

### `contract_document_product_link`

```text
universal:
  contract_document_product_link.before_create
  contract_document_product_link.after_create
  contract_document_product_link.before_delete
  contract_document_product_link.after_delete
```

```json
{
  "event_key": "contract_document_product_link.after_create",
  "entity_type": "contract_document_product_link",
  "entity_id": "link-id",
  "payload": {
    "contract_document_id": "document-id",
    "product_id": "product-id"
  }
}
```

### `document`

```text
universal:
  document.before_create
  document.after_create
  document.before_update
  document.after_update
  document.before_delete
  document.after_delete
  document.before_status_change
  document.after_status_change

domain:
  document.before_send
  document.after_send
  document.before_receive
  document.after_receive
  document.before_package_add
  document.after_package_add
```

```json
{
  "event_key": "document.after_send",
  "entity_type": "document",
  "entity_id": "document-id",
  "payload": {
    "deal_id": "deal-id",
    "channel": "email"
  }
}
```

### `document_relation`

```text
universal:
  document_relation.before_create
  document_relation.after_create
  document_relation.before_delete
  document_relation.after_delete
```

```json
{
  "event_key": "document_relation.after_create",
  "entity_type": "document_relation",
  "entity_id": "relation-id",
  "payload": {
    "document_id": "document-id",
    "related_entity_type": "deal",
    "related_entity_id": "deal-id"
  }
}
```

### `document_package`

```text
universal:
  document_package.before_create
  document_package.after_create
  document_package.before_update
  document_package.after_update
  document_package.before_delete
  document_package.after_delete
```

```json
{
  "event_key": "document_package.after_create",
  "entity_type": "document_package",
  "entity_id": "package-id",
  "payload": {
    "title": "Пакет ИД"
  }
}
```

### `document_package_item`

```text
universal:
  document_package_item.before_create
  document_package_item.after_create
  document_package_item.before_delete
  document_package_item.after_delete
```

```json
{
  "event_key": "document_package_item.after_create",
  "entity_type": "document_package_item",
  "entity_id": "item-id",
  "payload": {
    "package_id": "package-id",
    "document_id": "document-id"
  }
}
```

### `document_dispatch`

```text
universal:
  document_dispatch.before_create
  document_dispatch.after_create
  document_dispatch.before_update
  document_dispatch.after_update

domain:
  document_dispatch.before_send
  document_dispatch.after_send
```

```json
{
  "event_key": "document_dispatch.after_send",
  "entity_type": "document_dispatch",
  "entity_id": "dispatch-id",
  "payload": {
    "document_id": "document-id",
    "status": "sent"
  }
}
```

### `document_dispatch_channel`

```text
universal:
  document_dispatch_channel.before_create
  document_dispatch_channel.after_create
  document_dispatch_channel.before_update
  document_dispatch_channel.after_update
```

```json
{
  "event_key": "document_dispatch_channel.after_update",
  "entity_type": "document_dispatch_channel",
  "entity_id": "channel-id",
  "payload": {
    "status": "delivered"
  }
}
```

### `document_template`

```text
universal:
  document_template.before_create
  document_template.after_create
  document_template.before_update
  document_template.after_update
  document_template.before_delete
  document_template.after_delete

domain:
  document_template.before_version_publish
  document_template.after_version_publish
```

```json
{
  "event_key": "document_template.after_version_publish",
  "entity_type": "document_template",
  "entity_id": "template-id",
  "payload": {
    "version_id": "version-id"
  }
}
```

### `document_template_version`

```text
universal:
  document_template_version.before_create
  document_template_version.after_create
  document_template_version.before_update
  document_template_version.after_update
  document_template_version.before_delete
  document_template_version.after_delete
```

```json
{
  "event_key": "document_template_version.after_create",
  "entity_type": "document_template_version",
  "entity_id": "version-id",
  "payload": {
    "template_id": "template-id"
  }
}
```

## Outgoing Registry

### `outgoing_document`

```text
universal:
  outgoing_document.before_create
  outgoing_document.after_create
  outgoing_document.before_update
  outgoing_document.after_update
  outgoing_document.before_delete
  outgoing_document.after_delete
  outgoing_document.before_status_change
  outgoing_document.after_status_change

domain:
  outgoing_document.before_number_generate
  outgoing_document.after_number_generate
  outgoing_document.before_render
  outgoing_document.after_render
  outgoing_document.before_preview_pdf
  outgoing_document.after_preview_pdf
  outgoing_document.before_version_create
  outgoing_document.after_version_create
  outgoing_document.before_attachment_add
  outgoing_document.after_attachment_add
```

```json
{
  "event_key": "outgoing_document.before_render",
  "entity_type": "outgoing_document",
  "entity_id": "outgoing-id",
  "payload": {
    "document_kind": "invoice",
    "editor_mode": "structured",
    "deal_id": "deal-id"
  }
}
```

Переопределение рендера:

```json
{
  "event_key": "outgoing_document.before_render",
  "from_handler_target": "app.event_handlers.outgoing.render_default",
  "to_handler_target": "app.event_handlers.outgoing.render_structured",
  "condition_json": {
    "editor_mode": "structured"
  }
}
```

### `outgoing_document_version`

```text
universal:
  outgoing_document_version.before_create
  outgoing_document_version.after_create
  outgoing_document_version.before_delete
  outgoing_document_version.after_delete
```

```json
{
  "event_key": "outgoing_document_version.after_create",
  "entity_type": "outgoing_document_version",
  "entity_id": "version-id",
  "payload": {
    "document_id": "outgoing-id",
    "version_number": 2
  }
}
```

### `outgoing_document_file`

```text
universal:
  outgoing_document_file.before_create
  outgoing_document_file.after_create
  outgoing_document_file.before_delete
  outgoing_document_file.after_delete
```

```json
{
  "event_key": "outgoing_document_file.after_create",
  "entity_type": "outgoing_document_file",
  "entity_id": "file-id",
  "payload": {
    "document_id": "outgoing-id",
    "file_name": "invoice.pdf"
  }
}
```

### `outgoing_number_sequence`

```text
universal:
  outgoing_number_sequence.before_create
  outgoing_number_sequence.after_create
  outgoing_number_sequence.before_update
  outgoing_number_sequence.after_update
```

```json
{
  "event_key": "outgoing_number_sequence.after_update",
  "entity_type": "outgoing_number_sequence",
  "entity_id": "sequence-id",
  "payload": {
    "next_number": 1200
  }
}
```

### `outgoing_daily_number_sequence`

```text
universal:
  outgoing_daily_number_sequence.before_create
  outgoing_daily_number_sequence.after_create
  outgoing_daily_number_sequence.before_update
  outgoing_daily_number_sequence.after_update
```

```json
{
  "event_key": "outgoing_daily_number_sequence.after_update",
  "entity_type": "outgoing_daily_number_sequence",
  "entity_id": "sequence-id",
  "payload": {
    "company_key": "main",
    "document_kind": "invoice",
    "day": "2026-05-22"
  }
}
```

## Finance

### `financial_plan`

```text
universal:
  financial_plan.before_create
  financial_plan.after_create
  financial_plan.before_update
  financial_plan.after_update
  financial_plan.before_delete
  financial_plan.after_delete
  financial_plan.before_status_change
  financial_plan.after_status_change

domain:
  financial_plan.before_payment_status_change
  financial_plan.after_payment_status_change
```

```json
{
  "event_key": "financial_plan.after_payment_status_change",
  "entity_type": "financial_plan",
  "entity_id": "plan-id",
  "payload": {
    "payment_status_before": "pending",
    "payment_status_after": "paid"
  }
}
```

### `income_expense_entry`

```text
universal:
  income_expense_entry.before_create
  income_expense_entry.after_create
  income_expense_entry.before_update
  income_expense_entry.after_update
  income_expense_entry.before_delete
  income_expense_entry.after_delete
```

```json
{
  "event_key": "income_expense_entry.after_create",
  "entity_type": "income_expense_entry",
  "entity_id": "entry-id",
  "payload": {
    "deal_id": "deal-id",
    "amount": 100000
  }
}
```

### `treasury_transaction`

```text
universal:
  treasury_transaction.before_create
  treasury_transaction.after_create
  treasury_transaction.before_update
  treasury_transaction.after_update
  treasury_transaction.before_delete
  treasury_transaction.after_delete

domain:
  treasury_transaction.after_import
  treasury_transaction.before_allocate
  treasury_transaction.after_allocate
  treasury_transaction.before_link
  treasury_transaction.after_link
  treasury_transaction.before_ignore
  treasury_transaction.after_ignore
  treasury_transaction.before_auto_rule_apply
  treasury_transaction.after_auto_rule_apply
```

```json
{
  "event_key": "treasury_transaction.after_allocate",
  "entity_type": "treasury_transaction",
  "entity_id": "transaction-id",
  "payload": {
    "allocation_id": "allocation-id",
    "amount": 50000
  }
}
```

### `treasury_allocation`

```text
universal:
  treasury_allocation.before_create
  treasury_allocation.after_create
  treasury_allocation.before_update
  treasury_allocation.after_update
  treasury_allocation.before_delete
  treasury_allocation.after_delete
```

```json
{
  "event_key": "treasury_allocation.after_create",
  "entity_type": "treasury_allocation",
  "entity_id": "allocation-id",
  "payload": {
    "transaction_id": "transaction-id",
    "amount": 50000
  }
}
```

### `transaction_allocation`

```text
universal:
  transaction_allocation.before_create
  transaction_allocation.after_create
  transaction_allocation.before_update
  transaction_allocation.after_update
  transaction_allocation.before_delete
  transaction_allocation.after_delete
```

```json
{
  "event_key": "transaction_allocation.after_create",
  "entity_type": "transaction_allocation",
  "entity_id": "allocation-id",
  "payload": {
    "transaction_id": "transaction-id"
  }
}
```

### `treasury_auto_rule`

```text
universal:
  treasury_auto_rule.before_create
  treasury_auto_rule.after_create
  treasury_auto_rule.before_update
  treasury_auto_rule.after_update
  treasury_auto_rule.before_delete
  treasury_auto_rule.after_delete

domain:
  treasury_auto_rule.before_apply
  treasury_auto_rule.after_apply
```

```json
{
  "event_key": "treasury_auto_rule.after_apply",
  "entity_type": "treasury_auto_rule",
  "entity_id": "rule-id",
  "payload": {
    "matched_transactions": 12
  }
}
```

### `cb_rate`

```text
universal:
  cb_rate.before_create
  cb_rate.after_create
  cb_rate.before_update
  cb_rate.after_update
```

```json
{
  "event_key": "cb_rate.after_update",
  "entity_type": "cb_rate",
  "entity_id": "rate-id",
  "payload": {
    "currency": "USD",
    "rate": 91.5
  }
}
```

### `penalty_rule`

```text
universal:
  penalty_rule.before_create
  penalty_rule.after_create
  penalty_rule.before_update
  penalty_rule.after_update
  penalty_rule.before_delete
  penalty_rule.after_delete

domain:
  penalty_rule.before_apply
  penalty_rule.after_apply
```

```json
{
  "event_key": "penalty_rule.after_apply",
  "entity_type": "penalty_rule",
  "entity_id": "rule-id",
  "payload": {
    "entity_type": "task",
    "entity_id": "task-id"
  }
}
```

## Tasks And Auctions

### `task`

```text
universal:
  task.before_create
  task.after_create
  task.before_update
  task.after_update
  task.before_delete
  task.after_delete
  task.before_status_change
  task.after_status_change

domain:
  task.before_assign
  task.after_assign
  task.before_deadline_change
  task.after_deadline_change
  task.before_attachment_add
  task.after_attachment_add
  task.before_penalty_recalculate
  task.after_penalty_recalculate
```

```json
{
  "event_key": "task.after_assign",
  "entity_type": "task",
  "entity_id": "task-id",
  "payload": {
    "assigned_to_user_id": "user-id",
    "deal_id": "deal-id"
  }
}
```

### `task_message`

```text
universal:
  task_message.before_create
  task_message.after_create
  task_message.before_update
  task_message.after_update
  task_message.before_delete
  task_message.after_delete

domain:
  task_message.before_attachment_add
  task_message.after_attachment_add
```

```json
{
  "event_key": "task_message.after_create",
  "entity_type": "task_message",
  "entity_id": "message-id",
  "payload": {
    "task_id": "task-id",
    "author_id": "user-id"
  }
}
```

### `task_user_matrix`

```text
universal:
  task_user_matrix.before_create
  task_user_matrix.after_create
  task_user_matrix.before_update
  task_user_matrix.after_update
  task_user_matrix.before_delete
  task_user_matrix.after_delete

domain:
  task_user_matrix.before_reorder
  task_user_matrix.after_reorder
```

```json
{
  "event_key": "task_user_matrix.after_reorder",
  "entity_type": "task_user_matrix",
  "entity_id": "matrix-id",
  "payload": {
    "user_id": "user-id"
  }
}
```

### `task_auction`

```text
universal:
  task_auction.before_create
  task_auction.after_create
  task_auction.before_update
  task_auction.after_update
  task_auction.before_delete
  task_auction.after_delete
  task_auction.before_status_change
  task_auction.after_status_change

domain:
  task_auction.before_publish
  task_auction.after_publish
  task_auction.before_close
  task_auction.after_close
```

```json
{
  "event_key": "task_auction.after_publish",
  "entity_type": "task_auction",
  "entity_id": "auction-id",
  "payload": {
    "task_id": "task-id"
  }
}
```

### `task_auction_bid`

```text
universal:
  task_auction_bid.before_create
  task_auction_bid.after_create
  task_auction_bid.before_update
  task_auction_bid.after_update
  task_auction_bid.before_delete
  task_auction_bid.after_delete

domain:
  task_auction_bid.before_accept
  task_auction_bid.after_accept
  task_auction_bid.before_reject
  task_auction_bid.after_reject
```

```json
{
  "event_key": "task_auction_bid.after_accept",
  "entity_type": "task_auction_bid",
  "entity_id": "bid-id",
  "payload": {
    "auction_id": "auction-id",
    "user_id": "user-id"
  }
}
```

### `tender`

```text
universal:
  tender.before_create
  tender.after_create
  tender.before_update
  tender.after_update
  tender.before_delete
  tender.after_delete
  tender.before_status_change
  tender.after_status_change

domain:
  tender.before_publish
  tender.after_publish
  tender.before_close
  tender.after_close
```

```json
{
  "event_key": "tender.after_publish",
  "entity_type": "tender",
  "entity_id": "tender-id",
  "payload": {
    "deal_id": "deal-id"
  }
}
```

### `tender_offer`

```text
universal:
  tender_offer.before_create
  tender_offer.after_create
  tender_offer.before_update
  tender_offer.after_update
  tender_offer.before_delete
  tender_offer.after_delete

domain:
  tender_offer.before_accept
  tender_offer.after_accept
  tender_offer.before_reject
  tender_offer.after_reject
```

```json
{
  "event_key": "tender_offer.after_accept",
  "entity_type": "tender_offer",
  "entity_id": "offer-id",
  "payload": {
    "tender_id": "tender-id"
  }
}
```

## Communications

### `mailbox`

```text
universal:
  mailbox.before_create
  mailbox.after_create
  mailbox.before_update
  mailbox.after_update
  mailbox.before_delete
  mailbox.after_delete

domain:
  mailbox.before_sync
  mailbox.after_sync
```

```json
{
  "event_key": "mailbox.after_sync",
  "entity_type": "mailbox",
  "entity_id": "mailbox-id",
  "payload": {
    "messages_synced": 15
  }
}
```

### `mail_message`

```text
universal:
  mail_message.before_create
  mail_message.after_create
  mail_message.before_update
  mail_message.after_update
  mail_message.before_delete
  mail_message.after_delete

domain:
  mail_message.after_sync
  mail_message.after_receive
  mail_message.before_send
  mail_message.after_send
  mail_message.before_link_entity
  mail_message.after_link_entity
```

```json
{
  "event_key": "mail_message.after_receive",
  "entity_type": "mail_message",
  "entity_id": "message-id",
  "payload": {
    "mailbox_id": "mailbox-id",
    "subject": "Новое письмо"
  }
}
```

### `chat_conversation`

```text
universal:
  chat_conversation.before_create
  chat_conversation.after_create
  chat_conversation.before_update
  chat_conversation.after_update
  chat_conversation.before_delete
  chat_conversation.after_delete

domain:
  chat_conversation.before_member_add
  chat_conversation.after_member_add
  chat_conversation.before_member_remove
  chat_conversation.after_member_remove
```

```json
{
  "event_key": "chat_conversation.after_member_add",
  "entity_type": "chat_conversation",
  "entity_id": "conversation-id",
  "payload": {
    "user_id": "user-id"
  }
}
```

### `chat_conversation_member`

```text
universal:
  chat_conversation_member.before_create
  chat_conversation_member.after_create
  chat_conversation_member.before_delete
  chat_conversation_member.after_delete
```

```json
{
  "event_key": "chat_conversation_member.after_create",
  "entity_type": "chat_conversation_member",
  "entity_id": "member-id",
  "payload": {
    "conversation_id": "conversation-id",
    "user_id": "user-id"
  }
}
```

### `global_chat_message`

```text
universal:
  global_chat_message.before_create
  global_chat_message.after_create
  global_chat_message.before_update
  global_chat_message.after_update
  global_chat_message.before_delete
  global_chat_message.after_delete
```

```json
{
  "event_key": "global_chat_message.after_create",
  "entity_type": "global_chat_message",
  "entity_id": "message-id",
  "payload": {
    "author_id": "user-id"
  }
}
```

### `telegram_connection`

```text
universal:
  telegram_connection.before_create
  telegram_connection.after_create
  telegram_connection.before_update
  telegram_connection.after_update
  telegram_connection.before_delete
  telegram_connection.after_delete

domain:
  telegram_connection.before_verify
  telegram_connection.after_verify
```

```json
{
  "event_key": "telegram_connection.after_verify",
  "entity_type": "telegram_connection",
  "entity_id": "connection-id",
  "payload": {
    "user_id": "user-id"
  }
}
```

## Notifications, Events, Audit

### `notification`

```text
universal:
  notification.before_create
  notification.after_create
  notification.before_update
  notification.after_update
  notification.before_delete
  notification.after_delete

domain:
  notification.before_deliver
  notification.after_deliver
  notification.before_mark_read
  notification.after_mark_read
```

```json
{
  "event_key": "notification.before_deliver",
  "entity_type": "notification",
  "entity_id": "notification-id",
  "payload": {
    "user_id": "user-id",
    "priority": "warning"
  }
}
```

### `notification_delivery`

```text
universal:
  notification_delivery.before_create
  notification_delivery.after_create
  notification_delivery.before_update
  notification_delivery.after_update

domain:
  notification_delivery.before_send
  notification_delivery.after_send
  notification_delivery.after_fail
```

```json
{
  "event_key": "notification_delivery.after_fail",
  "entity_type": "notification_delivery",
  "entity_id": "delivery-id",
  "payload": {
    "channel": "telegram",
    "error": "timeout"
  }
}
```

### `notification_rule`

```text
universal:
  notification_rule.before_create
  notification_rule.after_create
  notification_rule.before_update
  notification_rule.after_update
  notification_rule.before_delete
  notification_rule.after_delete

domain:
  notification_rule.before_apply
  notification_rule.after_apply
```

```json
{
  "event_key": "notification_rule.after_apply",
  "entity_type": "notification_rule",
  "entity_id": "rule-id",
  "payload": {
    "source_event_id": "event-id"
  }
}
```

### `notification_subscription`

```text
universal:
  notification_subscription.before_create
  notification_subscription.after_create
  notification_subscription.before_update
  notification_subscription.after_update
  notification_subscription.before_delete
  notification_subscription.after_delete
```

```json
{
  "event_key": "notification_subscription.after_create",
  "entity_type": "notification_subscription",
  "entity_id": "subscription-id",
  "payload": {
    "user_id": "user-id",
    "entity_type": "deal",
    "entity_id": "deal-id"
  }
}
```

### `notification_preference`

```text
universal:
  notification_preference.before_create
  notification_preference.after_create
  notification_preference.before_update
  notification_preference.after_update
```

```json
{
  "event_key": "notification_preference.after_update",
  "entity_type": "notification_preference",
  "entity_id": "preference-id",
  "payload": {
    "user_id": "user-id"
  }
}
```

### `notification_job`

```text
universal:
  notification_job.before_create
  notification_job.after_create
  notification_job.before_update
  notification_job.after_update

domain:
  notification_job.before_run
  notification_job.after_run
  notification_job.after_fail
```

```json
{
  "event_key": "notification_job.after_run",
  "entity_type": "notification_job",
  "entity_id": "job-id",
  "payload": {
    "name": "event_logs"
  }
}
```

### `event_log`

```text
universal:
  event_log.before_create
  event_log.after_create
```

```json
{
  "event_key": "event_log.after_create",
  "entity_type": "event_log",
  "entity_id": "event-id",
  "payload": {
    "source_event_key": "deal.after_update"
  }
}
```

### `audit_log`

```text
universal:
  audit_log.before_create
  audit_log.after_create
```

```json
{
  "event_key": "audit_log.after_create",
  "entity_type": "audit_log",
  "entity_id": "audit-id",
  "payload": {
    "entity_type": "deal",
    "entity_id": "deal-id"
  }
}
```

## Approvals

### `approval_template`

```text
universal:
  approval_template.before_create
  approval_template.after_create
  approval_template.before_update
  approval_template.after_update
  approval_template.before_delete
  approval_template.after_delete
```

```json
{
  "event_key": "approval_template.after_create",
  "entity_type": "approval_template",
  "entity_id": "template-id",
  "payload": {
    "entity_type": "contract"
  }
}
```

### `approval_template_step`

```text
universal:
  approval_template_step.before_create
  approval_template_step.after_create
  approval_template_step.before_update
  approval_template_step.after_update
  approval_template_step.before_delete
  approval_template_step.after_delete
```

```json
{
  "event_key": "approval_template_step.after_create",
  "entity_type": "approval_template_step",
  "entity_id": "step-id",
  "payload": {
    "template_id": "template-id",
    "step_order": 1
  }
}
```

### `approval_instance`

```text
universal:
  approval_instance.before_create
  approval_instance.after_create
  approval_instance.before_update
  approval_instance.after_update
  approval_instance.before_status_change
  approval_instance.after_status_change

domain:
  approval_instance.before_start
  approval_instance.after_start
  approval_instance.before_complete
  approval_instance.after_complete
  approval_instance.before_reject
  approval_instance.after_reject
```

```json
{
  "event_key": "approval_instance.after_start",
  "entity_type": "approval_instance",
  "entity_id": "approval-id",
  "payload": {
    "target_entity_type": "contract",
    "target_entity_id": "contract-id"
  }
}
```

### `approval_instance_step`

```text
universal:
  approval_instance_step.before_create
  approval_instance_step.after_create
  approval_instance_step.before_update
  approval_instance_step.after_update
  approval_instance_step.before_status_change
  approval_instance_step.after_status_change

domain:
  approval_instance_step.before_complete
  approval_instance_step.after_complete
  approval_instance_step.before_reject
  approval_instance_step.after_reject
```

```json
{
  "event_key": "approval_instance_step.after_complete",
  "entity_type": "approval_instance_step",
  "entity_id": "step-id",
  "payload": {
    "approval_instance_id": "approval-id",
    "completed_by": "user-id"
  }
}
```

### `approval_action_log`

```text
universal:
  approval_action_log.before_create
  approval_action_log.after_create
```

```json
{
  "event_key": "approval_action_log.after_create",
  "entity_type": "approval_action_log",
  "entity_id": "action-log-id",
  "payload": {
    "approval_instance_id": "approval-id",
    "action": "approve"
  }
}
```

## Legal

### `legal_case`

```text
universal:
  legal_case.before_create
  legal_case.after_create
  legal_case.before_update
  legal_case.after_update
  legal_case.before_delete
  legal_case.after_delete
  legal_case.before_status_change
  legal_case.after_status_change
```

```json
{
  "event_key": "legal_case.after_update",
  "entity_type": "legal_case",
  "entity_id": "case-id",
  "payload": {
    "case_number": "А00-0000/2026"
  }
}
```

### `legal_case_event`

```text
universal:
  legal_case_event.before_create
  legal_case_event.after_create
  legal_case_event.before_update
  legal_case_event.after_update
  legal_case_event.before_delete
  legal_case_event.after_delete

domain:
  legal_case_event.before_schedule
  legal_case_event.after_schedule
```

```json
{
  "event_key": "legal_case_event.after_schedule",
  "entity_type": "legal_case_event",
  "entity_id": "case-event-id",
  "payload": {
    "legal_case_id": "case-id",
    "event_type": "hearing"
  }
}
```

### `legal_case_event_file`

```text
universal:
  legal_case_event_file.before_create
  legal_case_event_file.after_create
  legal_case_event_file.before_delete
  legal_case_event_file.after_delete
```

```json
{
  "event_key": "legal_case_event_file.after_create",
  "entity_type": "legal_case_event_file",
  "entity_id": "file-id",
  "payload": {
    "event_id": "case-event-id",
    "file_name": "notice.pdf"
  }
}
```

### `legal_case_task`

```text
universal:
  legal_case_task.before_create
  legal_case_task.after_create
  legal_case_task.before_delete
  legal_case_task.after_delete
```

```json
{
  "event_key": "legal_case_task.after_create",
  "entity_type": "legal_case_task",
  "entity_id": "case-task-id",
  "payload": {
    "legal_case_id": "case-id",
    "task_id": "task-id"
  }
}
```

## KP, Uploads, Data Health

### `kp_template`

```text
universal:
  kp_template.before_create
  kp_template.after_create
  kp_template.before_update
  kp_template.after_update
  kp_template.before_delete
  kp_template.after_delete
```

```json
{
  "event_key": "kp_template.after_create",
  "entity_type": "kp_template",
  "entity_id": "kp-template-id",
  "payload": {
    "name": "Базовый шаблон КП"
  }
}
```

### `kp_template_binding`

```text
universal:
  kp_template_binding.before_create
  kp_template_binding.after_create
  kp_template_binding.before_update
  kp_template_binding.after_update
  kp_template_binding.before_delete
  kp_template_binding.after_delete
```

```json
{
  "event_key": "kp_template_binding.after_create",
  "entity_type": "kp_template_binding",
  "entity_id": "binding-id",
  "payload": {
    "template_id": "kp-template-id"
  }
}
```

### `kp_document`

```text
universal:
  kp_document.before_create
  kp_document.after_create
  kp_document.before_update
  kp_document.after_update
  kp_document.before_delete
  kp_document.after_delete

domain:
  kp_document.before_render
  kp_document.after_render
  kp_document.before_version_create
  kp_document.after_version_create
```

```json
{
  "event_key": "kp_document.after_render",
  "entity_type": "kp_document",
  "entity_id": "kp-document-id",
  "payload": {
    "lead_id": "lead-id"
  }
}
```

### `kp_version`

```text
universal:
  kp_version.before_create
  kp_version.after_create
  kp_version.before_delete
  kp_version.after_delete
```

```json
{
  "event_key": "kp_version.after_create",
  "entity_type": "kp_version",
  "entity_id": "kp-version-id",
  "payload": {
    "kp_document_id": "kp-document-id"
  }
}
```

### `upload_job`

```text
universal:
  upload_job.before_create
  upload_job.after_create
  upload_job.before_update
  upload_job.after_update
  upload_job.before_status_change
  upload_job.after_status_change

domain:
  upload_job.before_process
  upload_job.after_process
  upload_job.after_fail
```

```json
{
  "event_key": "upload_job.after_fail",
  "entity_type": "upload_job",
  "entity_id": "upload-id",
  "payload": {
    "file_name": "bad.zip",
    "error": "blocked extension"
  }
}
```

### `data_health_issue`

```text
universal:
  data_health_issue.before_create
  data_health_issue.after_create
  data_health_issue.before_update
  data_health_issue.after_update
  data_health_issue.before_delete
  data_health_issue.after_delete

domain:
  data_health_issue.before_resolve
  data_health_issue.after_resolve
  data_health_issue.before_reopen
  data_health_issue.after_reopen
```

```json
{
  "event_key": "data_health_issue.after_resolve",
  "entity_type": "data_health_issue",
  "entity_id": "issue-id",
  "payload": {
    "related_entity_type": "deal",
    "related_entity_id": "deal-id"
  }
}
```

### `company_accreditation`

```text
universal:
  company_accreditation.before_create
  company_accreditation.after_create
  company_accreditation.before_update
  company_accreditation.after_update
  company_accreditation.before_delete
  company_accreditation.after_delete
  company_accreditation.before_status_change
  company_accreditation.after_status_change
```

```json
{
  "event_key": "company_accreditation.after_status_change",
  "entity_type": "company_accreditation",
  "entity_id": "accreditation-id",
  "payload": {
    "company_id": "company-id",
    "status_after": "approved"
  }
}
```

### `company_document`

```text
universal:
  company_document.before_create
  company_document.after_create
  company_document.before_update
  company_document.after_update
  company_document.before_delete
  company_document.after_delete
```

```json
{
  "event_key": "company_document.after_create",
  "entity_type": "company_document",
  "entity_id": "company-document-id",
  "payload": {
    "company_id": "company-id",
    "doc_type": "sro"
  }
}
```

## Дополнительные Сущности Из `backend/app/models`

Эти модели есть в дереве `backend/app/models`, но не импортируются в `app.models.__init__`. Для них тоже можно заложить события, если контуры будут активированы.

### `advance_payment`

```text
universal:
  advance_payment.before_create
  advance_payment.after_create
  advance_payment.before_update
  advance_payment.after_update
  advance_payment.before_delete
  advance_payment.after_delete
```

```json
{
  "event_key": "advance_payment.after_create",
  "entity_type": "advance_payment",
  "entity_id": "advance-payment-id",
  "payload": {
    "deal_id": "deal-id",
    "amount": 100000
  }
}
```

### `inflation_index`

```text
universal:
  inflation_index.before_create
  inflation_index.after_create
  inflation_index.before_update
  inflation_index.after_update
  inflation_index.before_delete
  inflation_index.after_delete
```

```json
{
  "event_key": "inflation_index.after_update",
  "entity_type": "inflation_index",
  "entity_id": "index-id",
  "payload": {
    "period": "2026-05",
    "value": 1.02
  }
}
```

### `overhead`

```text
universal:
  overhead.before_create
  overhead.after_create
  overhead.before_update
  overhead.after_update
  overhead.before_delete
  overhead.after_delete
```

```json
{
  "event_key": "overhead.after_create",
  "entity_type": "overhead",
  "entity_id": "overhead-id",
  "payload": {
    "amount": 50000
  }
}
```

### `overhead_allocation`

```text
universal:
  overhead_allocation.before_create
  overhead_allocation.after_create
  overhead_allocation.before_update
  overhead_allocation.after_update
  overhead_allocation.before_delete
  overhead_allocation.after_delete
```

```json
{
  "event_key": "overhead_allocation.after_create",
  "entity_type": "overhead_allocation",
  "entity_id": "allocation-id",
  "payload": {
    "overhead_id": "overhead-id",
    "deal_id": "deal-id"
  }
}
```

### `pricing_model`

```text
universal:
  pricing_model.before_create
  pricing_model.after_create
  pricing_model.before_update
  pricing_model.after_update
  pricing_model.before_delete
  pricing_model.after_delete
```

```json
{
  "event_key": "pricing_model.after_update",
  "entity_type": "pricing_model",
  "entity_id": "pricing-model-id",
  "payload": {
    "name": "Базовая модель"
  }
}
```

### `pricing_quote`

```text
universal:
  pricing_quote.before_create
  pricing_quote.after_create
  pricing_quote.before_update
  pricing_quote.after_update
  pricing_quote.before_delete
  pricing_quote.after_delete
```

```json
{
  "event_key": "pricing_quote.after_create",
  "entity_type": "pricing_quote",
  "entity_id": "quote-id",
  "payload": {
    "deal_id": "deal-id"
  }
}
```

### `quality_alert`

```text
universal:
  quality_alert.before_create
  quality_alert.after_create
  quality_alert.before_update
  quality_alert.after_update
  quality_alert.before_delete
  quality_alert.after_delete
  quality_alert.before_status_change
  quality_alert.after_status_change
```

```json
{
  "event_key": "quality_alert.after_create",
  "entity_type": "quality_alert",
  "entity_id": "alert-id",
  "payload": {
    "severity": "warning"
  }
}
```

### `stage_closing`

```text
universal:
  stage_closing.before_create
  stage_closing.after_create
  stage_closing.before_update
  stage_closing.after_update
  stage_closing.before_delete
  stage_closing.after_delete
```

```json
{
  "event_key": "stage_closing.after_create",
  "entity_type": "stage_closing",
  "entity_id": "stage-closing-id",
  "payload": {
    "stage_id": "stage-id",
    "close_date": "2026-05-22"
  }
}
```

### `wip_monthly`

```text
universal:
  wip_monthly.before_create
  wip_monthly.after_create
  wip_monthly.before_update
  wip_monthly.after_update
  wip_monthly.before_delete
  wip_monthly.after_delete
```

```json
{
  "event_key": "wip_monthly.after_update",
  "entity_type": "wip_monthly",
  "entity_id": "wip-id",
  "payload": {
    "period": "2026-05"
  }
}
```

## Рекомендуемый Реестр Внутренних Обработчиков

Внутренние обработчики должны регистрироваться через allowlist, а не произвольной строкой из UI.

```python
INTERNAL_EVENT_HANDLERS = {
    "app.event_handlers.deals.validate_update": validate_deal_update,
    "app.event_handlers.stages.validate_dependencies": validate_stage_dependencies,
    "app.event_handlers.stages.close_with_dependency_recalc": close_stage_with_dependency_recalc,
    "app.event_handlers.outgoing.validate_render_context": validate_outgoing_render_context,
    "app.event_handlers.outgoing.render_default": render_outgoing_default,
    "app.event_handlers.outgoing.render_structured": render_outgoing_structured,
    "app.event_handlers.tasks.notify_assignee": notify_task_assignee,
    "app.event_handlers.finance.apply_treasury_rule": apply_treasury_rule
}
```

## Контракт Ответа Обработчика

```json
{
  "status": "continue|cancel|mutate|redirect|fail",
  "reason": "Опциональное описание",
  "payload_patch": {},
  "redirect_to": "app.event_handlers.some.handler",
  "meta": {}
}
```

## Правила Приоритета

- Чем больше `priority`, тем раньше вызывается обработчик.
- `before_*` события выполняются в одной транзакции с бизнес-действием.
- `after_*` события выполняются после commit.
- Если `before_*` вернул `cancel`, бизнес-действие не выполняется.
- Если обработчик вернул `redirect`, следующий вызов идет в `redirect_to`.
- Если `can_mutate_payload=false`, `payload_patch` игнорируется.

## Минимальная Интеграция В Код

Целевой паттерн:

```python
before_result = await events.emit(
    "stage.before_close",
    entity_type="stage",
    entity_id=stage_id,
    payload=payload,
    context={"user_id": current_user.id},
)

if before_result.cancelled:
    raise HTTPException(status_code=400, detail=before_result.reason)

payload = before_result.payload

stage = await close_stage(db, stage_id, payload)

await events.emit(
    "stage.after_close",
    entity_type="stage",
    entity_id=stage_id,
    payload={"stage_id": stage_id, "deal_id": stage.deal_id},
    context={"user_id": current_user.id},
)
```

