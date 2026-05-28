# Platform & Integration API

Сгенерировано из `docs/API.md` на 2026-05-29 01:30:42 (local time).

## Scope
- Домен: `platform`
- Описание: Event Bus (outbox/subscriptions), поиск, AI-сервисы, customer portal и data-health диагностика.
- Routers: `5`
- Endpoints: `28`
- Список роутеров: `event_bus`, `search`, `ai`, `customer_portal`, `data_health`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `14`.

### Model `EventOutboxResponse`

Source: `backend/app/schemas/event_bus.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| event_id | str | yes | - | - |
| event_type | str | yes | - | - |
| entity_type | str | yes | - | - |
| entity_id | str | yes | - | - |
| payload | Dict[str, Any] | no | factory:dict | - |
| payload_version | int | no | 1 | - |
| causation_chain | List[str] | no | factory:list | - |
| status | str | yes | - | - |
| attempt_count | int | no | 0 | - |
| last_error | Optional[str] | no | None | - |
| scheduled_at | Optional[datetime] | no | None | - |
| delivered_at | Optional[datetime] | no | None | - |
| created_at | Optional[datetime] | no | None | - |


### Model `EventSubscriptionCreate`

Source: `backend/app/schemas/event_bus.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| event_type_pattern | str | yes | - | - |
| delivery_method | str | no | 'webhook' | - |
| target_url | str | yes | - | - |
| hmac_secret | str | yes | - | - |
| is_active | bool | no | True | - |
| description | Optional[str] | no | None | - |


### Model `EventSubscriptionResponse`

Source: `backend/app/schemas/event_bus.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| event_type_pattern | str | yes | - | - |
| delivery_method | str | no | 'webhook' | - |
| target_url | str | yes | - | - |
| hmac_secret | str | yes | - | - |
| is_active | bool | no | True | - |
| description | Optional[str] | no | None | - |
| id | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `EventSubscriptionUpdate`

Source: `backend/app/schemas/event_bus.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | Optional[str] | no | None | - |
| event_type_pattern | Optional[str] | no | None | - |
| delivery_method | Optional[str] | no | None | - |
| target_url | Optional[str] | no | None | - |
| hmac_secret | Optional[str] | no | None | - |
| is_active | Optional[bool] | no | None | - |
| description | Optional[str] | no | None | - |


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


## Routers / Controllers Reference

### Router `event_bus`

Source: `backend/app/routers/event_bus.py`

Prefix: `/api/v1/event-bus`

Endpoints: `11`

#### `POST /api/v1/event-bus/_test/webhook-sink`

- Controller: `backend/app/routers/event_bus.py::test_sink`
- Summary: Тестовый приёмник. Логирует входящее событие в jsonl-файл и
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: `x_event_id`: Optional[str] (optional, default=None, constraints=-); `x_event_type`: Optional[str] (optional, default=None, constraints=-); `x_event_signature`: Optional[str] (optional, default=None, constraints=-); `x_subscription_id`: Optional[str] (optional, default=None, constraints=-)
  - Form params: none
  - File params: none
  - Body: `body`: dict
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: Public
  - Depends/Security: none at function level
- Logic Flow:
  - Internal calls:
    - `Body`
    - `Header`
    - `_os.makedirs`
    - `_os.path.dirname`
    - `logger.exception`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/event-bus/_test/webhook-sink/log`

- Controller: `backend/app/routers/event_bus.py::test_sink_log`
- Summary: Вернуть последние строки лога test-sink для UI проверки.
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
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `_os.path.exists`
    - `logger.exception`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/event-bus/outbox`

- Controller: `backend/app/routers/event_bus.py::list_outbox`
- Data Contract:
  - Path params: none
  - Query params: `status`: Optional[str] (optional, default=None, constraints=-); `event_type`: Optional[str] (optional, default=None, constraints=-); `entity_type`: Optional[str] (optional, default=None, constraints=-); `entity_id`: Optional[str] (optional, default=None, constraints=-); `limit`: int (optional, default=100, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[EventOutboxResponse]`
  - Response contracts: [`EventOutboxResponse`](#model-eventoutboxresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select(EventOutbox).order_by(EventOutbox.created_at.desc()).limit`
    - `serialize_outbox_row`
    - `select(EventOutbox).order_by`
    - `EventOutbox.created_at.desc`
    - `EventOutbox.status.in_`
    - `select`
    - `db.execute`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/event-bus/outbox/{row_id}`

- Controller: `backend/app/routers/event_bus.py::get_outbox_row`
- Data Contract:
  - Path params: `row_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `EventOutboxResponse`
  - Response contracts: [`EventOutboxResponse`](#model-eventoutboxresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `(await db.execute(select(EventOutbox).where(EventOutbox.id == row_id))).scalar_one_or_none`
    - `serialize_outbox_row`
    - `HTTPException`
    - `db.execute`
    - `select(EventOutbox).where`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `Outbox row not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/event-bus/outbox/{row_id}/retry`

- Controller: `backend/app/routers/event_bus.py::retry_outbox_row`
- Summary: Сбросить строку обратно в pending (для DLQ или failed).
- Data Contract:
  - Path params: `row_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `EventOutboxResponse`
  - Response contracts: [`EventOutboxResponse`](#model-eventoutboxresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `(await db.execute(select(EventOutbox).where(EventOutbox.id == row_id))).scalar_one_or_none`
    - `serialize_outbox_row`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `update(EventOutbox).where(EventOutbox.id == row_id).values`
    - `select(EventOutbox).where`
    - `update(EventOutbox).where`
    - `select`
    - `update`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Already delivered`; body schema `{"detail": "..."}`
  - `404`: `Outbox row not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/event-bus/simulate`

- Controller: `backend/app/routers/event_bus.py::simulate_event`
- Summary: DRY-RUN прогон события: что произойдёт, если этот event эмитнётся.
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: `body`: dict
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Body`
    - `Depends`
    - `(body.get('event_key') or '').strip`
    - `EventContext`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `event_key required`; `payload must be an object`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/event-bus/stats`

- Controller: `backend/app/routers/event_bus.py::event_bus_stats`
- Summary: Сводка для observability admin-страницы.
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
    - `(await db.execute(select(EventOutbox.status, _f.count(EventOutbox.id)).group_by(EventOutbox.status))).all`
    - `(await db.execute(select(EventOutbox.event_type, _f.count(EventOutbox.id).label('c')).group_by(EventOutbox.event_type).order_by(_f.count(EventOutbox.id).desc()).limit(10))).all`
    - `(await db.execute(select(EventSubscription).order_by(EventSubscription.created_at.desc()))).scalars().all`
    - `(await db.execute(select(EventDeliveryDedup.event_id, EventDeliveryDedup.delivered_at).where(EventDeliveryDedup.subscription_id == str(sub.id)).order_by(EventDeliveryDedup.delivered_at.desc()).limit(1))).first`
    - `(await db.execute(select(_f.count(EventDeliveryDedup.event_id)))).scalar`
    - `(await db.execute(select(EventSubscription).order_by(EventSubscription.created_at.desc()))).scalars`
    - `(await db.execute(select(_f.count(EventDeliveryDedup.event_id)).where(EventDeliveryDedup.subscription_id == str(sub.id)))).scalar`
    - `db.execute`
    - `select(EventOutbox.status, _f.count(EventOutbox.id)).group_by`
    - `select(EventOutbox.event_type, _f.count(EventOutbox.id).label('c')).group_by(EventOutbox.event_type).order_by(_f.count(EventOutbox.id).desc()).limit`
    - `select(EventDeliveryDedup.event_id, EventDeliveryDedup.delivered_at).where(EventDeliveryDedup.subscription_id == str(sub.id)).order_by(EventDeliveryDedup.delivered_at.desc()).limit`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/event-bus/subscriptions`

- Controller: `backend/app/routers/event_bus.py::list_subscriptions`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[EventSubscriptionResponse]`
  - Response contracts: [`EventSubscriptionResponse`](#model-eventsubscriptionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `(await db.execute(select(EventSubscription).order_by(EventSubscription.created_at.desc()))).scalars().all`
    - `(await db.execute(select(EventSubscription).order_by(EventSubscription.created_at.desc()))).scalars`
    - `db.execute`
    - `select(EventSubscription).order_by`
    - `EventSubscription.created_at.desc`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/event-bus/subscriptions`

- Controller: `backend/app/routers/event_bus.py::create_subscription`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`EventSubscriptionCreate`](#model-eventsubscriptioncreate)
  - Response model: `EventSubscriptionResponse`
  - Response contracts: [`EventSubscriptionResponse`](#model-eventsubscriptionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `EventSubscription.create`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/event-bus/subscriptions/{sub_id}`

- Controller: `backend/app/routers/event_bus.py::delete_subscription`
- Data Contract:
  - Path params: `sub_id`: str (required, default=-, constraints=-)
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
    - `(await db.execute(select(EventSubscription).where(EventSubscription.id == sub_id))).scalar_one_or_none`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
    - `db.execute`
    - `select(EventSubscription).where`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Subscription not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/event-bus/subscriptions/{sub_id}`

- Controller: `backend/app/routers/event_bus.py::update_subscription`
- Data Contract:
  - Path params: `sub_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`EventSubscriptionUpdate`](#model-eventsubscriptionupdate)
  - Response model: `EventSubscriptionResponse`
  - Response contracts: [`EventSubscriptionResponse`](#model-eventsubscriptionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `(await db.execute(select(EventSubscription).where(EventSubscription.id == sub_id))).scalar_one_or_none`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `update(EventSubscription).where(EventSubscription.id == sub_id).values`
    - `select(EventSubscription).where`
    - `update(EventSubscription).where`
    - `select`
    - `update`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Subscription not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `search`

Source: `backend/app/routers/search.py`

Prefix: `/api/v1`

Endpoints: `1`

#### `POST /api/v1/search`

- Controller: `backend/app/routers/search.py::search`
- Summary: Полнотекстовый поиск по сущностям CRM.
- Data Contract:
  - Path params: none
  - Query params: `payload`: SearchRequest (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `SearchResponse`
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `is_hybrid_enabled`
    - `get_section_permissions`
    - `_types_with_embeddings`
    - `embed_query`
    - `db.execute`
    - `semantic_candidates`
    - `text`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


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


## Usage Examples (Domain)

Ключевые примеры отсутствуют для этого домена в исходном monolith reference.
