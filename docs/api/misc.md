# Misc API

Сгенерировано из `docs/API.md` на 2026-05-19 01:30:03 (local time).

## Scope
- Домен: `misc`
- Описание: Автоматически добавленные роутеры, не попавшие в ручную карту доменов.
- Routers: `7`
- Endpoints: `51`
- Список роутеров: `ai`, `approvals`, `customer_portal`, `data_health`, `document_templates`, `org_structure`, `telegram_notifications`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `23`.

### Model `AiAssistantChatRequest`

Source: `backend/app/schemas/ai.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| message | str | yes | - | - |
| history | List[AiAssistantMessage] | no | factory:list | - |
| page_context | Optional[AiAssistantPageContext] | no | None | - |


### Model `AiAssistantChatResponse`

Source: `backend/app/schemas/ai.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| answer | str | yes | - | - |
| model | str | yes | - | - |
| warnings | List[str] | no | factory:list | - |
| used_deal_ids | List[str] | no | factory:list | - |
| used_sections | List[str] | no | factory:list | - |
| raw | Optional[Any] | no | None | - |


### Model `AiStatusResponse`

Source: `backend/app/schemas/ai.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| enabled | bool | yes | - | - |
| provider | str | no | 'ollama' | - |
| model | Optional[str] | no | None | - |
| reachable | bool | no | False | - |
| detail | Optional[str] | no | None | - |


### Model `OutgoingAiAssistRequest`

Source: `backend/app/schemas/ai.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| action | Literal['draft', 'improve', 'formalize', 'shorten'] | yes | - | enum='draft', 'improve', 'formalize', 'shorten' |
| prompt | Optional[str] | no | '' | - |
| current_html | Optional[str] | no | '' | - |
| selection_text | Optional[str] | no | '' | - |
| selection_present | bool | no | False | - |
| document_payload | OutgoingDocumentResolveRequest | yes | - | - |


### Model `OutgoingAiAssistResponse`

Source: `backend/app/schemas/ai.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| action | str | yes | - | - |
| model | str | yes | - | - |
| html | str | yes | - | - |
| text | str | yes | - | - |
| used_fields | List[str] | no | factory:list | - |
| warnings | List[str] | no | factory:list | - |
| summary | Optional[str] | no | None | - |
| raw | Optional[Any] | no | None | - |


### Model `ApprovalInboxResponse`

Source: `backend/app/schemas/approval.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| stats | ApprovalInboxStats | yes | - | - |
| items | List[ApprovalInboxItem] | no | factory:list | - |
| total | int | no | 0 | - |
| offset | int | no | 0 | - |
| limit | int | no | 0 | - |


### Model `ApprovalInstanceAction`

Source: `backend/app/schemas/approval.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| comment | Optional[str] | no | None | - |


### Model `ApprovalInstanceResponse`

Source: `backend/app/schemas/approval.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| template_id | str | yes | - | - |
| template_name | str | yes | - | - |
| entity_type | str | yes | - | - |
| entity_id | str | yes | - | - |
| entity_label | Optional[str] | no | None | - |
| status | str | yes | - | - |
| current_step_id | Optional[str] | no | None | - |
| started_by | Optional[str] | no | None | - |
| started_by_label | Optional[str] | no | None | - |
| completed_by | Optional[str] | no | None | - |
| completed_by_label | Optional[str] | no | None | - |
| completed_comment | Optional[str] | no | None | - |
| started_at | Optional[datetime] | no | None | - |
| completed_at | Optional[datetime] | no | None | - |
| steps | List[ApprovalInstanceStepResponse] | no | factory:list | - |
| actions | List[ApprovalActionLogResponse] | no | factory:list | - |


### Model `ApprovalInstanceStart`

Source: `backend/app/schemas/approval.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| template_id | str | yes | - | - |
| entity_id | str | yes | - | - |
| entity_type | Optional[str] | no | None | - |
| entity_label | Optional[str] | no | None | - |


### Model `ApprovalTemplateResponse`

Source: `backend/app/schemas/approval.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| name | str | yes | - | - |
| code | Optional[str] | no | None | - |
| description | Optional[str] | no | None | - |
| entity_type | str | yes | - | - |
| is_active | bool | yes | - | - |
| tags | List[str] | no | factory:list | - |
| created_by | Optional[str] | no | None | - |
| updated_by | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |
| steps | List[ApprovalTemplateStepResponse] | no | factory:list | - |
| active_instances_count | int | no | 0 | - |
| total_instances_count | int | no | 0 | - |


### Model `ApprovalTemplateWrite`

Source: `backend/app/schemas/approval.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| code | Optional[str] | no | None | - |
| description | Optional[str] | no | None | - |
| entity_type | str | yes | - | - |
| is_active | bool | no | True | - |
| tags | List[str] | no | factory:list | - |
| steps | List[ApprovalTemplateStepWrite] | no | factory:list | - |


### Model `DataHealthDealCountsResponse`

Source: `backend/app/schemas/data_health.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| items | List[DataHealthDealCountResponse] | no | factory:list | - |


### Model `DataHealthGroupedListResponse`

Source: `backend/app/schemas/data_health.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| items | List[DataHealthIssueGroupResponse] | no | factory:list | - |
| total | int | no | 0 | - |
| summary | DataHealthSummaryResponse | no | factory:DataHealthSummaryResponse | - |


### Model `DataHealthIgnoreRequest`

Source: `backend/app/schemas/data_health.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| reason | Optional[str] | no | None | max_length=2000 |
| ignored_until | Optional[datetime] | no | None | - |


### Model `DataHealthIssueResponse`

Source: `backend/app/schemas/data_health.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| fingerprint | str | yes | - | - |
| deal_id | Optional[str] | no | None | - |
| deal_title | Optional[str] | no | None | - |
| scope_type | str | yes | - | - |
| scope_id | Optional[str] | no | None | - |
| issue_type | str | yes | - | - |
| module | str | yes | - | - |
| severity | str | yes | - | - |
| status | str | yes | - | - |
| title | str | yes | - | - |
| description | str | no | '' | - |
| payload | Dict[str, Any] | no | factory:dict | - |
| navigation_path | Optional[str] | no | None | - |
| navigation_query | Dict[str, Any] | no | factory:dict | - |
| first_detected_at | Optional[datetime] | no | None | - |
| last_detected_at | Optional[datetime] | no | None | - |
| resolved_at | Optional[datetime] | no | None | - |
| ignored_reason | Optional[str] | no | None | - |
| ignored_until | Optional[datetime] | no | None | - |
| ignored_by_user_id | Optional[str] | no | None | - |
| ignored_at | Optional[datetime] | no | None | - |


### Model `DataHealthListResponse`

Source: `backend/app/schemas/data_health.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| items | List[DataHealthIssueResponse] | no | factory:list | - |
| total | int | no | 0 | - |
| summary | DataHealthSummaryResponse | no | factory:DataHealthSummaryResponse | - |


### Model `OrgUnitAssign`

Source: `backend/app/schemas/org_unit.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| user_id | str | yes | - | - |
| org_unit_id | Optional[str] | no | None | - |


### Model `OrgUnitCreate`

Source: `backend/app/schemas/org_unit.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| parent_id | Optional[str] | no | None | - |
| kind | Optional[str] | no | None | - |
| head_user_id | Optional[str] | no | None | - |
| sort_order | Optional[int] | no | 0 | - |


### Model `OrgUnitResponse`

Source: `backend/app/schemas/org_unit.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| parent_id | Optional[str] | no | None | - |
| name | str | yes | - | - |
| kind | Optional[str] | no | None | - |
| head_user_id | Optional[str] | no | None | - |
| sort_order | int | no | 0 | - |
| depth | int | no | 0 | - |
| path | Optional[str] | no | None | - |
| member_count | int | no | 0 | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `OrgUnitTreeNode`

Source: `backend/app/schemas/org_unit.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| parent_id | Optional[str] | no | None | - |
| name | str | yes | - | - |
| kind | Optional[str] | no | None | - |
| head_user_id | Optional[str] | no | None | - |
| sort_order | int | no | 0 | - |
| depth | int | no | 0 | - |
| path | Optional[str] | no | None | - |
| member_count | int | no | 0 | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |
| children | List['OrgUnitTreeNode'] | no | [] | - |
| members | List[OrgUnitMember] | no | [] | - |


### Model `OrgUnitUpdate`

Source: `backend/app/schemas/org_unit.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | Optional[str] | no | None | - |
| parent_id | Optional[str] | no | None | - |
| kind | Optional[str] | no | None | - |
| head_user_id | Optional[str] | no | None | - |
| sort_order | Optional[int] | no | None | - |


### Model `TelegramConnectionStatusResponse`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| bot_configured | bool | yes | - | - |
| bot_username | Optional[str] | no | None | - |
| is_connected | bool | yes | - | - |
| is_enabled | bool | yes | - | - |
| is_verified | bool | yes | - | - |
| telegram_username | Optional[str] | no | None | - |
| chat_id_masked | Optional[str] | no | None | - |
| linked_at | Optional[datetime] | no | None | - |
| deliver_telegram | bool | yes | - | - |


### Model `TelegramLinkResponse`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| bot_configured | bool | yes | - | - |
| bot_username | Optional[str] | no | None | - |
| link_url | Optional[str] | no | None | - |
| expires_at | Optional[datetime] | no | None | - |


## Routers / Controllers Reference

### Router `ai`

Source: `backend/app/routers/ai.py`

Prefix: `/api/v1/ai`

Endpoints: `3`

#### `POST /api/v1/ai/assistant/chat`

- Controller: `backend/app/routers/ai.py::chat_with_assistant`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AiAssistantChatRequest`](#model-aiassistantchatrequest)
  - Response model: `AiAssistantChatResponse`
  - Response contracts: [`AiAssistantChatResponse`](#model-aiassistantchatresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `AiAssistantChatResponse`
    - `ai_is_enabled`
    - `HTTPException`
    - `ollama_chat_json`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Message is required`; body schema `{"detail": "..."}`
  - `502`: `AI returned empty response`; `str(exc)`; body schema `{"detail": "..."}`
  - `503`: `AI assistant is disabled`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/ai/outgoing/assist`

- Controller: `backend/app/routers/ai.py::assist_outgoing_document`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`OutgoingAiAssistRequest`](#model-outgoingaiassistrequest)
  - Response model: `OutgoingAiAssistResponse`
  - Response contracts: [`OutgoingAiAssistResponse`](#model-outgoingaiassistresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `OutgoingAiAssistResponse`
    - `ai_is_enabled`
    - `HTTPException`
    - `_build_transient_editor_document`
    - `_build_document_render_payload`
    - `ollama_chat_json`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Recipient company is required for AI assistant`; body schema `{"detail": "..."}`
  - `502`: `AI returned empty response`; `str(exc)`; body schema `{"detail": "..."}`
  - `503`: `AI assistant is disabled`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/ai/status`

- Controller: `backend/app/routers/ai.py::get_ai_status`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `AiStatusResponse`
  - Response contracts: [`AiStatusResponse`](#model-aistatusresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security: none at function level
- Logic Flow:
  - Internal calls:
    - `AiStatusResponse`
    - `ai_is_enabled`
    - `ollama_tags`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `approvals`

Source: `backend/app/routers/approvals.py`

Prefix: `/api/v1/approvals`

Endpoints: `15`

#### `GET /api/v1/approvals/inbox`

- Controller: `backend/app/routers/approvals.py::get_inbox`
- Data Contract:
  - Path params: none
  - Query params: `scope`: str (optional, default='pending_me', constraints=-); `entity_type`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `limit`: int (optional, default=200, constraints=ge=1, le=500); `offset`: int (optional, default=0, constraints=ge=0)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `ApprovalInboxResponse`
  - Response contracts: [`ApprovalInboxResponse`](#model-approvalinboxresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `ApprovalInboxStats`
    - `ApprovalInboxResponse`
    - `require_any_section_access`
    - `ApprovalInstance.started_at.desc`
    - `db.execute`
    - `select`
    - `ApprovalInstanceStep.instance_id.in_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/approvals/instances`

- Controller: `backend/app/routers/approvals.py::list_instances`
- Data Contract:
  - Path params: none
  - Query params: `entity_type`: Optional[str] (optional, default=None, constraints=-); `entity_id`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `mine_only`: bool (optional, default=False, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[ApprovalInstanceResponse]`
  - Response contracts: [`ApprovalInstanceResponse`](#model-approvalinstanceresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `require_any_section_access`
    - `ApprovalInstance.started_at.desc`
    - `db.execute`
    - `is_superuser`
    - `select`
    - `or_`
    - `ApprovalInstance.id.in_`
    - `and_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/approvals/instances`

- Controller: `backend/app/routers/approvals.py::start_instance`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ApprovalInstanceStart`](#model-approvalinstancestart)
  - Response model: `ApprovalInstanceResponse`
  - Response contracts: [`ApprovalInstanceResponse`](#model-approvalinstanceresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `ApprovalInstance`
    - `db.add`
    - `require_any_section_access`
    - `db.get`
    - `HTTPException`
    - `db.execute`
    - `db.flush`
    - `ApprovalInstanceStep`
    - `ApprovalActionLog`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, DB read, Notification dispatch
- Error Handling:
  - `400`: `Шаблон согласования выключен.`; `Тип сущности не соответствует шаблону согласования.`; `Недопустимый тип сущности.`; `Для этой сущности уже запущено активное согласование.`; `Шаблон согласования не содержит ни одного шага.`; body schema `{"detail": "..."}`
  - `404`: `Шаблон согласования не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/approvals/instances/{instance_id}`

- Controller: `backend/app/routers/approvals.py::get_instance`
- Data Contract:
  - Path params: `instance_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `ApprovalInstanceResponse`
  - Response contracts: [`ApprovalInstanceResponse`](#model-approvalinstanceresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_any_section_access`
    - `db.get`
    - `HTTPException`
    - `is_superuser`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `403`: `Нет доступа к этому согласованию.`; body schema `{"detail": "..."}`
  - `404`: `Экземпляр согласования не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/approvals/instances/{instance_id}/approve`

- Controller: `backend/app/routers/approvals.py::approve_instance_step`
- Data Contract:
  - Path params: `instance_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ApprovalInstanceAction`](#model-approvalinstanceaction)
  - Response model: `ApprovalInstanceResponse`
  - Response contracts: [`ApprovalInstanceResponse`](#model-approvalinstanceresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.add`
    - `require_any_section_access`
    - `db.get`
    - `HTTPException`
    - `ApprovalActionLog`
    - `db.execute`
    - `db.commit`
    - `db.refresh`
    - `_notify_for_step`
    - `select`
  - Side effects: DB write, DB read, Notification dispatch
- Error Handling:
  - `400`: `Согласование уже завершено.`; `У согласования нет активного шага.`; body schema `{"detail": "..."}`
  - `404`: `Экземпляр согласования не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/approvals/instances/{instance_id}/reject`

- Controller: `backend/app/routers/approvals.py::reject_instance_step`
- Data Contract:
  - Path params: `instance_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ApprovalInstanceAction`](#model-approvalinstanceaction)
  - Response model: `ApprovalInstanceResponse`
  - Response contracts: [`ApprovalInstanceResponse`](#model-approvalinstanceresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.add`
    - `require_any_section_access`
    - `db.get`
    - `HTTPException`
    - `ApprovalActionLog`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `Согласование уже завершено.`; `У согласования нет активного шага.`; `Для отклонения согласования требуется комментарий.`; body schema `{"detail": "..."}`
  - `404`: `Экземпляр согласования не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/approvals/meta`

- Controller: `backend/app/routers/approvals.py::get_approval_meta`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_read('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_read`
    - `User.get_all`
    - `Role.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/approvals/templates`

- Controller: `backend/app/routers/approvals.py::list_templates`
- Data Contract:
  - Path params: none
  - Query params: `entity_type`: Optional[str] (optional, default=None, constraints=-); `active`: Optional[bool] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[ApprovalTemplateResponse]`
  - Response contracts: [`ApprovalTemplateResponse`](#model-approvaltemplateresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_read('roles'))`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `require_section_read`
    - `ApprovalTemplate.updated_at.desc`
    - `ApprovalTemplate.created_at.desc`
    - `db.execute`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/approvals/templates`

- Controller: `backend/app/routers/approvals.py::create_template`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ApprovalTemplateWrite`](#model-approvaltemplatewrite)
  - Response model: `ApprovalTemplateResponse`
  - Response contracts: [`ApprovalTemplateResponse`](#model-approvaltemplateresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `ApprovalTemplate`
    - `db.add`
    - `require_section_write`
    - `HTTPException`
    - `db.flush`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `Недопустимый тип сущности для шаблона согласования.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/approvals/templates/runtime`

- Controller: `backend/app/routers/approvals.py::list_runtime_templates`
- Data Contract:
  - Path params: none
  - Query params: `entity_type`: Optional[str] (optional, default=None, constraints=-); `active`: bool (optional, default=True, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[ApprovalTemplateResponse]`
  - Response contracts: [`ApprovalTemplateResponse`](#model-approvaltemplateresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `require_any_section_access`
    - `ApprovalTemplate.updated_at.desc`
    - `ApprovalTemplate.created_at.desc`
    - `db.execute`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/approvals/templates/{template_id}`

- Controller: `backend/app/routers/approvals.py::delete_template`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `db.get`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
  - Side effects: DB write
- Error Handling:
  - `404`: `Шаблон согласования не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/approvals/templates/{template_id}`

- Controller: `backend/app/routers/approvals.py::get_template`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `ApprovalTemplateResponse`
  - Response contracts: [`ApprovalTemplateResponse`](#model-approvaltemplateresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_read('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_read`
    - `db.get`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Шаблон согласования не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/approvals/templates/{template_id}`

- Controller: `backend/app/routers/approvals.py::update_template`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ApprovalTemplateWrite`](#model-approvaltemplatewrite)
  - Response model: `ApprovalTemplateResponse`
  - Response contracts: [`ApprovalTemplateResponse`](#model-approvaltemplateresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `db.get`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `Недопустимый тип сущности для шаблона согласования.`; body schema `{"detail": "..."}`
  - `404`: `Шаблон согласования не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/approvals/templates/{template_id}/duplicate`

- Controller: `backend/app/routers/approvals.py::duplicate_template`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `ApprovalTemplateResponse`
  - Response contracts: [`ApprovalTemplateResponse`](#model-approvaltemplateresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `ApprovalTemplate`
    - `db.add`
    - `require_section_write`
    - `db.get`
    - `HTTPException`
    - `db.execute`
    - `db.flush`
    - `ApprovalTemplateStep`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Шаблон согласования не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/approvals/templates/{template_id}/usage`

- Controller: `backend/app/routers/approvals.py::get_template_usage`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_read('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_read`
    - `db.get`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Шаблон согласования не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `customer_portal`

Source: `backend/app/routers/customer_portal.py`

Prefix: `/api/v1/customer`

Endpoints: `5`

#### `GET /api/v1/customer/projects`

- Controller: `backend/app/routers/customer_portal.py::customer_projects`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `Deal.title.asc`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/customer/projects/{deal_id}`

- Controller: `backend/app/routers/customer_portal.py::customer_project_detail`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `get_defacto_view`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/customer/projects/{deal_id}/letters/{letter_id}/download`

- Controller: `backend/app/routers/customer_portal.py::customer_project_letter_download`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-); `letter_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Response`
    - `db.execute`
    - `HTTPException`
    - `_resolve_effective_render_payload`
    - `clean_name`
    - `and_`
    - `_content_disposition`
    - `select`
    - `_build_outgoing_file_base_clean`
  - Side effects: DB read, File/storage operation
- Error Handling:
  - `404`: `Письмо не найдено`; body schema `{"detail": "..."}`
  - `409`: `Файл письма недоступен`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/customer/projects/{deal_id}/storage/download`

- Controller: `backend/app/routers/customer_portal.py::customer_project_storage_download`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: `section`: str (required, default=-, constraints=-); `path`: str (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `_build_root_paths`
    - `_resolve_customer_storage_path`
    - `mimetypes.guess_type`
    - `is_local_storage`
    - `Response`
    - `HTTPException`
    - `storage_available`
    - `_local_path`
    - `tempfile.mkdtemp`
    - `os.path.join`
  - Side effects: Background task trigger, File/storage operation
- Error Handling:
  - `400`: `Неизвестный раздел документов`; body schema `{"detail": "..."}`
  - `404`: `Файл не найден`; body schema `{"detail": "..."}`
  - `500`: `Хранилище не настроено`; body schema `{"detail": "..."}`
  - `502`: `Не удалось скачать файл`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/customer/projects/{deal_id}/storage/list`

- Controller: `backend/app/routers/customer_portal.py::customer_project_storage_list`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: `section`: str (required, default=-, constraints=-); `path`: str | None (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `_build_root_paths`
    - `_resolve_customer_storage_path`
    - `HTTPException`
    - `storage_available`
    - `list_items`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Неизвестный раздел документов`; body schema `{"detail": "..."}`
  - `500`: `Хранилище не настроено`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `data_health`

Source: `backend/app/routers/data_health.py`

Prefix: `/api/v1/data-health`

Endpoints: `8`

#### `GET /api/v1/data-health/deal-counts`

- Controller: `backend/app/routers/data_health.py::list_deal_health_counts`
- Data Contract:
  - Path params: none
  - Query params: `refresh`: bool (optional, default=False, constraints=-); `deal_ids`: Optional[list[str]] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `DataHealthDealCountsResponse`
  - Response contracts: [`DataHealthDealCountsResponse`](#model-datahealthdealcountsresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `get_deal_health_counts`
    - `refresh_all_health_issues`
    - `refresh_deal_health_issues`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/data-health/deals/{deal_id}/issues`

- Controller: `backend/app/routers/data_health.py::list_deal_health_issues`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: `refresh`: bool (optional, default=True, constraints=-); `severity`: Optional[str] (optional, default=None, constraints=-); `issue_type`: Optional[str] (optional, default=None, constraints=-); `module`: Optional[str] (optional, default=None, constraints=-); `status`: str (optional, default='active', constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `offset`: int (optional, default=0, constraints=ge=0); `limit`: int (optional, default=200, constraints=ge=1, le=500)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `DataHealthListResponse`
  - Response contracts: [`DataHealthListResponse`](#model-datahealthlistresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `get_health_issues`
    - `refresh_deal_health_issues`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/data-health/issues`

- Controller: `backend/app/routers/data_health.py::list_health_issues`
- Data Contract:
  - Path params: none
  - Query params: `refresh`: bool (optional, default=False, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `severity`: Optional[str] (optional, default=None, constraints=-); `issue_type`: Optional[str] (optional, default=None, constraints=-); `module`: Optional[str] (optional, default=None, constraints=-); `status`: str (optional, default='active', constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `offset`: int (optional, default=0, constraints=ge=0); `limit`: int (optional, default=100, constraints=ge=1, le=500)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `DataHealthListResponse`
  - Response contracts: [`DataHealthListResponse`](#model-datahealthlistresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `get_health_issues`
    - `refresh_deal_health_issues`
    - `refresh_all_health_issues`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/data-health/issues/groups`

- Controller: `backend/app/routers/data_health.py::list_grouped_health_issues`
- Data Contract:
  - Path params: none
  - Query params: `refresh`: bool (optional, default=False, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `severity`: Optional[str] (optional, default=None, constraints=-); `issue_type`: Optional[str] (optional, default=None, constraints=-); `module`: Optional[str] (optional, default=None, constraints=-); `status`: str (optional, default='active', constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `offset`: int (optional, default=0, constraints=ge=0); `limit`: int (optional, default=100, constraints=ge=1, le=500)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `DataHealthGroupedListResponse`
  - Response contracts: [`DataHealthGroupedListResponse`](#model-datahealthgroupedlistresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `get_grouped_health_issues`
    - `refresh_deal_health_issues`
    - `refresh_all_health_issues`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/data-health/issues/{issue_id}/ignore`

- Controller: `backend/app/routers/data_health.py::ignore_health_issue`
- Data Contract:
  - Path params: `issue_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DataHealthIgnoreRequest`](#model-datahealthignorerequest)
  - Response model: `DataHealthIssueResponse`
  - Response contracts: [`DataHealthIssueResponse`](#model-datahealthissueresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `DataHealthIgnoreRequest`
    - `set_health_issue_status`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Issue not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/data-health/issues/{issue_id}/open`

- Controller: `backend/app/routers/data_health.py::reopen_health_issue`
- Data Contract:
  - Path params: `issue_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `DataHealthIssueResponse`
  - Response contracts: [`DataHealthIssueResponse`](#model-datahealthissueresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `set_health_issue_status`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Issue not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/data-health/refresh`

- Controller: `backend/app/routers/data_health.py::refresh_health_issues`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-); `orphan_only`: bool (optional, default=False, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `DataHealthListResponse`
  - Response contracts: [`DataHealthListResponse`](#model-datahealthlistresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `get_health_issues`
    - `refresh_orphan_health_issues`
    - `refresh_deal_health_issues`
    - `refresh_all_health_issues`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/data-health/report.pdf`

- Controller: `backend/app/routers/data_health.py::download_health_report_pdf`
- Data Contract:
  - Path params: none
  - Query params: `refresh`: bool (optional, default=False, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `severity`: Optional[str] (optional, default=None, constraints=-); `issue_type`: Optional[str] (optional, default=None, constraints=-); `module`: Optional[str] (optional, default=None, constraints=-); `status`: str (optional, default='active', constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `grouped`: bool (optional, default=True, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `Response`
    - `build_data_health_report_pdf`
    - `refresh_deal_health_issues`
    - `refresh_all_health_issues`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `document_templates`

Source: `backend/app/routers/document_templates.py`

Prefix: `/api/v1/document-templates`

Endpoints: `10`

#### `GET /api/v1/document-templates`

- Controller: `backend/app/routers/document_templates.py::list_templates`
- Data Contract:
  - Path params: none
  - Query params: `search`: Optional[str] (optional, default=None, constraints=-); `module`: Optional[str] (optional, default=None, constraints=-); `document_kind`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `active`: Optional[bool] (optional, default=None, constraints=-); `skip`: int (optional, default=0, constraints=ge=0); `limit`: int (optional, default=50, constraints=ge=1, le=200)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_read('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `select`
    - `require_section_read`
    - `db.execute`
    - `or_`
    - `and_`
    - `DocumentTemplate.name.ilike`
    - `DocumentTemplate.description.ilike`
    - `DocumentTemplate.module.ilike`
    - `DocumentTemplate.document_kind.ilike`
    - `DocumentTemplate.updated_at.desc`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/document-templates`

- Controller: `backend/app/routers/document_templates.py::create_template`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `name`: str (required, default=-, constraints=-); `module`: str (optional, default='outgoing_registry', constraints=-); `document_kind`: str (optional, default='letter', constraints=-); `status`: str (optional, default='draft', constraints=-); `is_active`: bool (optional, default=False, constraints=-); `description`: Optional[str] (optional, default=None, constraints=-); `our_company_key`: Optional[str] (optional, default=None, constraints=-); `binding_type`: str (optional, default='global', constraints=-); `binding_id`: Optional[str] (optional, default=None, constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `Form`
    - `File`
    - `Depends`
    - `DocumentTemplate`
    - `db.add`
    - `require_section_write`
    - `db.flush`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-templates/field-groups`

- Controller: `backend/app/routers/document_templates.py::list_template_field_groups`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `_: Depends(require_section_read('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `get_template_field_groups`
    - `require_section_read`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-templates/fields`

- Controller: `backend/app/routers/document_templates.py::list_template_fields`
- Data Contract:
  - Path params: none
  - Query params: `search`: Optional[str] (optional, default=None, constraints=-); `module`: Optional[str] (optional, default=None, constraints=-); `document_kind`: Optional[str] (optional, default=None, constraints=-); `group`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `_: Depends(require_section_read('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `get_template_fields`
    - `require_section_read`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-templates/meta`

- Controller: `backend/app/routers/document_templates.py::get_template_meta`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `_: Depends(require_section_read('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_read`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/document-templates/{template_id}`

- Controller: `backend/app/routers/document_templates.py::delete_template`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `db.get`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
  - Side effects: DB write
- Error Handling:
  - `404`: `Template not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-templates/{template_id}`

- Controller: `backend/app/routers/document_templates.py::get_template`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_read('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_read`
    - `db.get`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Template not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/document-templates/{template_id}`

- Controller: `backend/app/routers/document_templates.py::update_template`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: dict (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `db.get`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `404`: `Template not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-templates/{template_id}/download`

- Controller: `backend/app/routers/document_templates.py::download_template`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: `version_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_read('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `quote`
    - `Response`
    - `require_section_read`
    - `db.get`
    - `HTTPException`
    - `db.execute`
    - `read_file_bytes`
    - `and_`
    - `select`
  - Side effects: DB read, File/storage operation
- Error Handling:
  - `404`: `Template not found`; `Template version not found`; `Template file not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/document-templates/{template_id}/versions`

- Controller: `backend/app/routers/document_templates.py::upload_template_version`
- Data Contract:
  - Path params: `template_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('document_templates'))`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `require_section_write`
    - `db.get`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `404`: `Template not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `org_structure`

Source: `backend/app/routers/org_structure.py`

Prefix: `/api/v1/org-structure`

Endpoints: `6`

#### `GET /api/v1/org-structure`

- Controller: `backend/app/routers/org_structure.py::list_org_units`
- Data Contract:
  - Path params: none
  - Query params: `flat`: int (optional, default=0, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[OrgUnitTreeNode]`
  - Response contracts: [`OrgUnitTreeNode`](#model-orgunittreenode)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_read(SECTION))`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `require_section_read`
    - `OrgUnit.get_all`
    - `db.execute`
    - `OrgUnitTreeNode.model_validate`
    - `User.org_unit_id.isnot`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/org-structure`

- Controller: `backend/app/routers/org_structure.py::create_org_unit`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`OrgUnitCreate`](#model-orgunitcreate)
  - Response model: `OrgUnitResponse`
  - Response contracts: [`OrgUnitResponse`](#model-orgunitresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write(SECTION))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `OrgUnit`
    - `db.add`
    - `require_section_write`
    - `db.flush`
    - `db.commit`
    - `db.refresh`
    - `OrgUnit.get_by_id`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `400`: `Родительский узел не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/org-structure/assign`

- Controller: `backend/app/routers/org_structure.py::assign_user`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`OrgUnitAssign`](#model-orgunitassign)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write(SECTION))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.add`
    - `require_section_write`
    - `User.get_by_id`
    - `HTTPException`
    - `db.commit`
    - `OrgUnit.get_by_id`
  - Side effects: DB write
- Error Handling:
  - `400`: `Подразделение не найдено`; body schema `{"detail": "..."}`
  - `404`: `Пользователь не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/org-structure/{unit_id}`

- Controller: `backend/app/routers/org_structure.py::delete_org_unit`
- Data Contract:
  - Path params: `unit_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write(SECTION))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `OrgUnit.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `select`
    - `delete`
    - `func.count`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Подразделение не найдено`; body schema `{"detail": "..."}`
  - `409`: `У узла есть дочерние подразделения — сначала перенесите или удалите их`; `В узле есть сотрудники — сначала переназначьте их`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/org-structure/{unit_id}`

- Controller: `backend/app/routers/org_structure.py::get_org_unit`
- Data Contract:
  - Path params: `unit_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `OrgUnitTreeNode`
  - Response contracts: [`OrgUnitTreeNode`](#model-orgunittreenode)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_read(SECTION))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `OrgUnitTreeNode.model_validate`
    - `require_section_read`
    - `OrgUnit.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `Подразделение не найдено`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/org-structure/{unit_id}`

- Controller: `backend/app/routers/org_structure.py::update_org_unit`
- Data Contract:
  - Path params: `unit_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`OrgUnitUpdate`](#model-orgunitupdate)
  - Response model: `OrgUnitResponse`
  - Response contracts: [`OrgUnitResponse`](#model-orgunitresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write(SECTION))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.add`
    - `require_section_write`
    - `OrgUnit.get_by_id`
    - `HTTPException`
    - `db.flush`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `Узел не может быть родителем сам себе`; `Родительский узел не найден`; `Нельзя переместить узел внутрь его собственного поддерева`; body schema `{"detail": "..."}`
  - `404`: `Подразделение не найдено`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `telegram_notifications`

Source: `backend/app/routers/telegram_notifications.py`

Prefix: `/api/v1/telegram`

Endpoints: `4`

#### `POST /api/v1/telegram/link`

- Controller: `backend/app/routers/telegram_notifications.py::create_telegram_link`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `TelegramLinkResponse`
  - Response contracts: [`TelegramLinkResponse`](#model-telegramlinkresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `utcnow_naive`
    - `secrets.token_urlsafe`
    - `TelegramLinkResponse`
    - `telegram_bot_configured`
    - `TelegramConnection`
    - `db.add`
    - `db.commit`
    - `build_telegram_deep_link`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/telegram/me`

- Controller: `backend/app/routers/telegram_notifications.py::unlink_my_telegram`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `get_or_create_notification_preference`
    - `db.commit`
  - Side effects: DB write, Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/telegram/me`

- Controller: `backend/app/routers/telegram_notifications.py::get_my_telegram_status`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `TelegramConnectionStatusResponse`
  - Response contracts: [`TelegramConnectionStatusResponse`](#model-telegramconnectionstatusresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `TelegramConnectionStatusResponse`
    - `get_or_create_notification_preference`
    - `telegram_bot_configured`
  - Side effects: Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/telegram/webhook/{webhook_secret}`

- Controller: `backend/app/routers/telegram_notifications.py::telegram_webhook`
- Data Contract:
  - Path params: `webhook_secret`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: `payload`: Optional[dict[str, Any]]
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Body`
    - `Depends`
    - `HTTPException`
    - `handle_telegram_update`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


## Usage Examples (Domain)

Ключевые примеры отсутствуют для этого домена в исходном monolith reference.
