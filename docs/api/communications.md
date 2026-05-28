# Communications & Notifications API

Сгенерировано из `docs/API.md` на 2026-02-15 03:22:39 (local time).

## Scope
- Домен: `communications`
- Описание: Почта, чаты, уведомления и пользовательские предпочтения уведомлений.
- Routers: `7`
- Endpoints: `32`
- Список роутеров: `mail`, `task_messages`, `global_chat`, `notifications`, `notification_rules`, `notification_preferences`, `notification_subscriptions`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `20`.

### Model `MailMessageList`

Source: `backend/app/schemas/mail.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| items | List[MailMessageResponse] | yes | - | - |


### Model `MailSendRequest`

Source: `backend/app/schemas/mail.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| to | List[EmailStr] | yes | - | - |
| subject | str | yes | - | - |
| body | str | yes | - | - |
| cc | List[EmailStr] | no | [] | - |
| bcc | List[EmailStr] | no | [] | - |


### Model `MailSendResponse`

Source: `backend/app/schemas/mail.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| message | str | no | 'ok' | - |


### Model `MailboxAppPassword`

Source: `backend/app/schemas/mail.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| app_password | str | yes | - | - |


### Model `MailboxAuthUrl`

Source: `backend/app/schemas/mail.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| auth_url | str | yes | - | - |


### Model `MailboxCreate`

Source: `backend/app/schemas/mail.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| email | EmailStr | yes | - | - |


### Model `MailboxResponse`

Source: `backend/app/schemas/mail.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| name | str | yes | - | - |
| email | EmailStr | yes | - | - |
| provider | str | yes | - | - |
| status | str | yes | - | - |
| last_sync_at | Optional[datetime] | no | None | - |


### Model `TaskMessageResponse`

Source: `backend/app/schemas/task_message.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| task_id | str | yes | - | - |
| user_id | str | yes | - | - |
| user_name | Optional[str] | no | None | - |
| body | Optional[str] | no | None | - |
| attachments | List[Dict[str, Any]] | no | [] | - |
| mentions | List[str] | no | [] | - |
| is_deleted | bool | no | False | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |
| edited_at | Optional[datetime] | no | None | - |
| deleted_at | Optional[datetime] | no | None | - |


### Model `TaskMessageUpdate`

Source: `backend/app/schemas/task_message.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| body | Optional[str] | no | None | - |


### Model `GlobalChatMessageResponse`

Source: `backend/app/schemas/global_chat_message.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| user_id | str | yes | - | - |
| user_name | Optional[str] | no | None | - |
| body | Optional[str] | no | None | - |
| attachments | List[Dict[str, Any]] | no | [] | - |
| mentions | List[str] | no | [] | - |
| is_deleted | bool | no | False | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |
| edited_at | Optional[datetime] | no | None | - |
| deleted_at | Optional[datetime] | no | None | - |


### Model `GlobalChatMessageUpdate`

Source: `backend/app/schemas/global_chat_message.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| body | Optional[str] | no | None | - |


### Model `NotificationResponse`

Source: `backend/app/schemas/notification.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | UUID | yes | - | - |
| user_id | str | yes | - | - |
| type | str | yes | - | - |
| priority | Optional[str] | no | None | - |
| title | str | yes | - | - |
| message | Optional[str] | no | None | - |
| entity_type | Optional[str] | no | None | - |
| entity_id | Optional[str] | no | None | - |
| action_url | Optional[str] | no | None | - |
| rule_id | Optional[str] | no | None | - |
| source_event_id | Optional[str] | no | None | - |
| is_read | bool | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| read_at | Optional[datetime] | no | None | - |
| deliver_at | Optional[datetime] | no | None | - |


### Model `NotificationRuleCreate`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| trigger | str | yes | - | - |
| entity_type | Optional[str] | no | None | - |
| priority | Optional[str] | no | 'info' | - |
| audience_type | Optional[str] | no | 'assigned_user' | - |
| audience_value | Optional[str] | no | None | - |
| require_subscription | Optional[bool] | no | False | - |
| conditions | Optional[Dict[str, Any]] | no | None | - |
| quiet_policy | Optional[str] | no | 'respect' | - |
| deliver_in_app | Optional[bool] | no | True | - |
| throttle_minutes | Optional[int] | no | 0 | - |
| title_template | Optional[str] | no | None | - |
| message_template | Optional[str] | no | None | - |
| action_url_template | Optional[str] | no | None | - |
| is_active | Optional[bool] | no | True | - |


### Model `NotificationRuleResponse`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| trigger | str | yes | - | - |
| entity_type | Optional[str] | no | None | - |
| priority | Optional[str] | no | 'info' | - |
| audience_type | Optional[str] | no | 'assigned_user' | - |
| audience_value | Optional[str] | no | None | - |
| require_subscription | Optional[bool] | no | False | - |
| conditions | Optional[Dict[str, Any]] | no | None | - |
| quiet_policy | Optional[str] | no | 'respect' | - |
| deliver_in_app | Optional[bool] | no | True | - |
| throttle_minutes | Optional[int] | no | 0 | - |
| title_template | Optional[str] | no | None | - |
| message_template | Optional[str] | no | None | - |
| action_url_template | Optional[str] | no | None | - |
| is_active | Optional[bool] | no | True | - |
| id | str | yes | - | - |
| created_by | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `NotificationRuleUpdate`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | Optional[str] | no | None | - |
| trigger | Optional[str] | no | None | - |
| entity_type | Optional[str] | no | None | - |
| priority | Optional[str] | no | None | - |
| audience_type | Optional[str] | no | None | - |
| audience_value | Optional[str] | no | None | - |
| require_subscription | Optional[bool] | no | None | - |
| conditions | Optional[Dict[str, Any]] | no | None | - |
| quiet_policy | Optional[str] | no | None | - |
| deliver_in_app | Optional[bool] | no | None | - |
| throttle_minutes | Optional[int] | no | None | - |
| title_template | Optional[str] | no | None | - |
| message_template | Optional[str] | no | None | - |
| action_url_template | Optional[str] | no | None | - |
| is_active | Optional[bool] | no | None | - |


### Model `NotificationPreferenceResponse`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| user_id | str | yes | - | - |
| timezone | str | yes | - | - |
| quiet_hours_start | str | yes | - | - |
| quiet_hours_end | str | yes | - | - |
| digest_enabled | bool | yes | - | - |
| digest_time | str | yes | - | - |
| deliver_in_app | bool | yes | - | - |
| digest_last_sent_at | Optional[datetime] | no | None | - |


### Model `NotificationPreferenceUpdate`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| timezone | Optional[str] | no | None | - |
| quiet_hours_start | Optional[str] | no | None | - |
| quiet_hours_end | Optional[str] | no | None | - |
| digest_enabled | Optional[bool] | no | None | - |
| digest_time | Optional[str] | no | None | - |
| deliver_in_app | Optional[bool] | no | None | - |


### Model `NotificationSubscriptionCreate`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| entity_type | str | yes | - | - |
| entity_id | str | yes | - | - |


### Model `NotificationSubscriptionResponse`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| user_id | str | yes | - | - |
| entity_type | str | yes | - | - |
| entity_id | str | yes | - | - |
| is_muted | bool | yes | - | - |
| mute_until | Optional[datetime] | no | None | - |
| created_at | Optional[datetime] | no | None | - |


### Model `NotificationSubscriptionUpdate`

Source: `backend/app/schemas/notification_rules.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| is_muted | Optional[bool] | no | None | - |
| mute_until | Optional[datetime] | no | None | - |


## Routers / Controllers Reference

### Router `mail`

Source: `backend/app/routers/mail.py`

Prefix: `/api/v1/mail`

Endpoints: `10`

#### `GET /api/v1/mail/mailboxes`

- Controller: `backend/app/routers/mail.py::list_mailboxes`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[MailboxResponse]`
  - Response contracts: [`MailboxResponse`](#model-mailboxresponse)
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
    - `select(Mailbox).order_by`
    - `Mailbox.created_at.asc`
    - `select`
  - Side effects: DB write, DB read, Mail integration
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/mail/mailboxes`

- Controller: `backend/app/routers/mail.py::create_mailbox`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`MailboxCreate`](#model-mailboxcreate)
  - Response model: `MailboxResponse`
  - Response contracts: [`MailboxResponse`](#model-mailboxresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Mailbox`
    - `db.add`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select(Mailbox).where`
    - `select`
  - Side effects: DB write, DB read, Mail integration
- Error Handling:
  - `400`: `Mailbox already exists`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/mail/mailboxes/{mailbox_id}`

- Controller: `backend/app/routers/mail.py::delete_mailbox`
- Data Contract:
  - Path params: `mailbox_id`: str (required, default=-, constraints=-)
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
    - `db.get`
    - `HTTPException`
    - `db.execute`
    - `db.delete`
    - `db.commit`
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Mailbox not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/mail/mailboxes/{mailbox_id}/connect`

- Controller: `backend/app/routers/mail.py::connect_mailbox`
- Data Contract:
  - Path params: `mailbox_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `MailboxAuthUrl`
  - Response contracts: [`MailboxAuthUrl`](#model-mailboxauthurl)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `build_state`
    - `build_auth_url`
    - `MailboxAuthUrl`
    - `db.get`
    - `HTTPException`
  - Side effects: Mail integration
- Error Handling:
  - `400`: `OAuth is not configured`; body schema `{"detail": "..."}`
  - `404`: `Mailbox not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/mail/mailboxes/{mailbox_id}/connect-app-password`

- Controller: `backend/app/routers/mail.py::connect_mailbox_app_password`
- Data Contract:
  - Path params: `mailbox_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`MailboxAppPassword`](#model-mailboxapppassword)
  - Response model: `MailboxResponse`
  - Response contracts: [`MailboxResponse`](#model-mailboxresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.get`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `sync_mailbox`
  - Side effects: DB write, Mail integration
- Error Handling:
  - `400`: `App password required`; body schema `{"detail": "..."}`
  - `404`: `Mailbox not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/mail/mailboxes/{mailbox_id}/export`

- Controller: `backend/app/routers/mail.py::export_mailbox`
- Data Contract:
  - Path params: `mailbox_id`: str (required, default=-, constraints=-)
  - Query params: `days`: int (optional, default=30, constraints=-)
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
    - `f'mailbox_{mailbox.email}_{days}d.csv'.replace`
    - `Response`
    - `db.get`
    - `HTTPException`
    - `db.execute`
    - `select(MailMessage).where(MailMessage.mailbox_id == mailbox.id).where(MailMessage.date.is_(None) | (MailMessage.date >= since)).order_by`
    - `MailMessage.date.desc().nullslast`
    - `select(MailMessage).where(MailMessage.mailbox_id == mailbox.id).where`
    - `MailMessage.date.desc`
    - `MailMessage.date.is_`
    - `select`
  - Side effects: DB read, Mail integration
- Error Handling:
  - `404`: `Mailbox not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/mail/mailboxes/{mailbox_id}/messages`

- Controller: `backend/app/routers/mail.py::list_messages`
- Data Contract:
  - Path params: `mailbox_id`: str (required, default=-, constraints=-)
  - Query params: `limit`: int (optional, default=50, constraints=-); `refresh`: int (optional, default=0, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `MailMessageList`
  - Response contracts: [`MailMessageList`](#model-mailmessagelist)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `MailMessageList`
    - `db.get`
    - `HTTPException`
    - `db.execute`
    - `select(MailMessage).where(MailMessage.mailbox_id == mailbox.id).order_by(MailMessage.date.desc().nullslast()).limit`
    - `sync_mailbox`
    - `db.commit`
    - `MailMessageResponse`
    - `select(MailMessage).where(MailMessage.mailbox_id == mailbox.id).order_by`
    - `MailMessage.date.desc().nullslast`
    - `MailMessage.date.desc`
  - Side effects: DB write, DB read, Mail integration
- Error Handling:
  - `404`: `Mailbox not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/mail/mailboxes/{mailbox_id}/send`

- Controller: `backend/app/routers/mail.py::send_mail`
- Data Contract:
  - Path params: `mailbox_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`MailSendRequest`](#model-mailsendrequest)
  - Response model: `MailSendResponse`
  - Response contracts: [`MailSendResponse`](#model-mailsendresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `MailSendResponse`
    - `db.get`
    - `HTTPException`
    - `ensure_valid_token`
    - `asyncio.to_thread`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Mailbox not authorized`; body schema `{"detail": "..."}`
  - `404`: `Mailbox not found`; body schema `{"detail": "..."}`
  - `500`: `f'SMTP error: {exc}`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/mail/messages/{message_id}`

- Controller: `backend/app/routers/mail.py::get_message_body`
- Data Contract:
  - Path params: `message_id`: str (required, default=-, constraints=-)
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
    - `db.get`
    - `HTTPException`
    - `ensure_valid_token`
    - `normalize_snippet_text`
    - `asyncio.to_thread`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Mailbox not authorized`; body schema `{"detail": "..."}`
  - `404`: `Message not found`; `Mailbox not found`; body schema `{"detail": "..."}`
  - `500`: `Message body load failed`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/mail/oauth/yandex/callback`

- Controller: `backend/app/routers/mail.py::yandex_oauth_callback`
- Data Contract:
  - Path params: none
  - Query params: `code`: Optional[str] (optional, default=None, constraints=-); `state`: Optional[str] (optional, default=None, constraints=-); `error`: Optional[str] (optional, default=None, constraints=-); `error_description`: Optional[str] (optional, default=None, constraints=-)
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
    - `Depends`
    - `verify_state`
    - `RedirectResponse`
    - `HTTPException`
    - `db.get`
    - `db.commit`
    - `db.refresh`
    - `exchange_code`
    - `sync_mailbox`
  - Side effects: DB write, Mail integration
- Error Handling:
  - `400`: `Invalid state`; body schema `{"detail": "..."}`
  - `404`: `Mailbox not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `task_messages`

Source: `backend/app/routers/task_messages.py`

Prefix: `/api/v1`

Endpoints: `4`

#### `DELETE /api/v1/tasks/messages/{message_id}`

- Controller: `backend/app/routers/task_messages.py::delete_task_message`
- Data Contract:
  - Path params: `message_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.get`
    - `HTTPException`
    - `Task.get_by_id`
    - `db.commit`
  - Side effects: DB write
- Error Handling:
  - `403`: `Not enough permissions`; body schema `{"detail": "..."}`
  - `404`: `Message not found`; `Task not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/tasks/messages/{message_id}`

- Controller: `backend/app/routers/task_messages.py::update_task_message`
- Data Contract:
  - Path params: `message_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TaskMessageUpdate`](#model-taskmessageupdate)
  - Response model: `TaskMessageResponse`
  - Response contracts: [`TaskMessageResponse`](#model-taskmessageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.get`
    - `HTTPException`
    - `Task.get_by_id`
    - `db.commit`
    - `db.refresh`
    - `joinedload`
  - Side effects: DB write
- Error Handling:
  - `400`: `Message deleted`; `Message cannot be empty`; body schema `{"detail": "..."}`
  - `403`: `Not enough permissions`; body schema `{"detail": "..."}`
  - `404`: `Message not found`; `Task not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/tasks/{task_id}/messages`

- Controller: `backend/app/routers/task_messages.py::list_task_messages`
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=200, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[TaskMessageResponse]`
  - Response contracts: [`TaskMessageResponse`](#model-taskmessageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Task.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `TaskMessage.created_at.asc`
    - `joinedload`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Task not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/tasks/{task_id}/messages`

- Controller: `backend/app/routers/task_messages.py::create_task_message`
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: `body`: Optional[str] (optional, default=None, constraints=-); `mentions`: Optional[str] (optional, default=None, constraints=-)
  - File params: `files`: Union[UploadFile, List[UploadFile], None] (optional, default=None, constraints=-)
  - Body: none
  - Response model: `TaskMessageResponse`
  - Response contracts: [`TaskMessageResponse`](#model-taskmessageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Form`
    - `File`
    - `Depends`
    - `TaskMessage`
    - `db.add`
    - `Task.get_by_id`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `db.execute`
    - `storage_available`
    - `ensure_path`
  - Side effects: DB write, DB read, Notification dispatch, File/storage operation
- Error Handling:
  - `400`: `Message or files are required`; body schema `{"detail": "..."}`
  - `404`: `Task not found`; body schema `{"detail": "..."}`
  - `413`: `File too large`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `global_chat`

Source: `backend/app/routers/global_chat.py`

Prefix: `/api/v1/chat`

Endpoints: `4`

#### `GET /api/v1/chat/messages`

- Controller: `backend/app/routers/global_chat.py::list_global_messages`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=200, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[GlobalChatMessageResponse]`
  - Response contracts: [`GlobalChatMessageResponse`](#model-globalchatmessageresponse)
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
    - `GlobalChatMessage.created_at.asc`
    - `joinedload`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/chat/messages`

- Controller: `backend/app/routers/global_chat.py::create_global_message`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `body`: Optional[str] (optional, default=None, constraints=-); `mentions`: Optional[str] (optional, default=None, constraints=-)
  - File params: `files`: Union[UploadFile, List[UploadFile], None] (optional, default=None, constraints=-)
  - Body: none
  - Response model: `GlobalChatMessageResponse`
  - Response contracts: [`GlobalChatMessageResponse`](#model-globalchatmessageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Form`
    - `File`
    - `Depends`
    - `GlobalChatMessage`
    - `db.add`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `db.execute`
    - `storage_available`
    - `ensure_path`
    - `clean_name`
  - Side effects: DB write, DB read, Notification dispatch, File/storage operation
- Error Handling:
  - `400`: `Message or files are required`; body schema `{"detail": "..."}`
  - `413`: `File too large`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/chat/messages/{message_id}`

- Controller: `backend/app/routers/global_chat.py::delete_global_message`
- Data Contract:
  - Path params: `message_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.get`
    - `HTTPException`
    - `db.commit`
  - Side effects: DB write
- Error Handling:
  - `403`: `Not enough permissions`; body schema `{"detail": "..."}`
  - `404`: `Message not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/chat/messages/{message_id}`

- Controller: `backend/app/routers/global_chat.py::update_global_message`
- Data Contract:
  - Path params: `message_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`GlobalChatMessageUpdate`](#model-globalchatmessageupdate)
  - Response model: `GlobalChatMessageResponse`
  - Response contracts: [`GlobalChatMessageResponse`](#model-globalchatmessageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.get`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `joinedload`
  - Side effects: DB write
- Error Handling:
  - `400`: `Message deleted`; `Message cannot be empty`; body schema `{"detail": "..."}`
  - `403`: `Not enough permissions`; body schema `{"detail": "..."}`
  - `404`: `Message not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `notifications`

Source: `backend/app/routers/notifications.py`

Prefix: `/api/v1/notifications`

Endpoints: `4`

#### `GET /api/v1/notifications`

- Controller: `backend/app/routers/notifications.py::list_notifications`
- Data Contract:
  - Path params: none
  - Query params: `unread`: Optional[bool] (optional, default=None, constraints=-); `type`: Optional[str] (optional, default=None, constraints=-); `priority`: Optional[str] (optional, default=None, constraints=-); `date_from`: Optional[datetime] (optional, default=None, constraints=-); `date_to`: Optional[datetime] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `entity_type`: Optional[str] (optional, default=None, constraints=-); `entity_id`: Optional[str] (optional, default=None, constraints=-); `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=50, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[NotificationResponse]`
  - Response contracts: [`NotificationResponse`](#model-notificationresponse)
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
    - `Notification.list_by_user`
    - `NotificationResponse.model_validate`
  - Side effects: Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/notifications/read-all`

- Controller: `backend/app/routers/notifications.py::mark_all_notifications_read`
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
    - `Notification.mark_all_read`
  - Side effects: Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/notifications/unread-count`

- Controller: `backend/app/routers/notifications.py::unread_notifications_count`
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
    - `Notification.is_read.is_`
    - `select`
    - `Notification.deliver_at.is_`
    - `func.count`
    - `func.now`
  - Side effects: DB read, Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/notifications/{notification_id}/read`

- Controller: `backend/app/routers/notifications.py::mark_notification_read`
- Data Contract:
  - Path params: `notification_id`: str (required, default=-, constraints=-)
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
    - `Notification.mark_read`
  - Side effects: Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `notification_rules`

Source: `backend/app/routers/notification_rules.py`

Prefix: `/api/v1/notification-rules`

Endpoints: `4`

#### `GET /api/v1/notification-rules`

- Controller: `backend/app/routers/notification_rules.py::list_rules`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[NotificationRuleResponse]`
  - Response contracts: [`NotificationRuleResponse`](#model-notificationruleresponse)
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
    - `NotificationRule.created_at.desc`
    - `select`
  - Side effects: DB write, DB read, Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/notification-rules`

- Controller: `backend/app/routers/notification_rules.py::create_rule`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`NotificationRuleCreate`](#model-notificationrulecreate)
  - Response model: `NotificationRuleResponse`
  - Response contracts: [`NotificationRuleResponse`](#model-notificationruleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `NotificationRule.create`
  - Side effects: DB write, Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/notification-rules/{rule_id}`

- Controller: `backend/app/routers/notification_rules.py::delete_rule`
- Data Contract:
  - Path params: `rule_id`: str (required, default=-, constraints=-)
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
    - `NotificationRule.get_by_id`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
  - Side effects: DB write, Notification dispatch
- Error Handling:
  - `404`: `Rule not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/notification-rules/{rule_id}`

- Controller: `backend/app/routers/notification_rules.py::update_rule`
- Data Contract:
  - Path params: `rule_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`NotificationRuleUpdate`](#model-notificationruleupdate)
  - Response model: `NotificationRuleResponse`
  - Response contracts: [`NotificationRuleResponse`](#model-notificationruleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `NotificationRule.update`
    - `HTTPException`
  - Side effects: DB write, Notification dispatch
- Error Handling:
  - `404`: `Rule not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `notification_preferences`

Source: `backend/app/routers/notification_preferences.py`

Prefix: `/api/v1/notification-preferences`

Endpoints: `2`

#### `GET /api/v1/notification-preferences/me`

- Controller: `backend/app/routers/notification_preferences.py::get_my_preferences`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `NotificationPreferenceResponse`
  - Response contracts: [`NotificationPreferenceResponse`](#model-notificationpreferenceresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/notification-preferences/me`

- Controller: `backend/app/routers/notification_preferences.py::update_my_preferences`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`NotificationPreferenceUpdate`](#model-notificationpreferenceupdate)
  - Response model: `NotificationPreferenceResponse`
  - Response contracts: [`NotificationPreferenceResponse`](#model-notificationpreferenceresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `notification_subscriptions`

Source: `backend/app/routers/notification_subscriptions.py`

Prefix: `/api/v1/notification-subscriptions`

Endpoints: `4`

#### `DELETE /api/v1/notification-subscriptions`

- Controller: `backend/app/routers/notification_subscriptions.py::delete_subscription`
- Data Contract:
  - Path params: none
  - Query params: `entity_type`: str (required, default=-, constraints=-); `entity_id`: str (required, default=-, constraints=-)
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
    - `db.execute`
    - `db.commit`
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/notification-subscriptions`

- Controller: `backend/app/routers/notification_subscriptions.py::create_subscription`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`NotificationSubscriptionCreate`](#model-notificationsubscriptioncreate)
  - Response model: `NotificationSubscriptionResponse`
  - Response contracts: [`NotificationSubscriptionResponse`](#model-notificationsubscriptionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `NotificationSubscription`
    - `db.add`
    - `db.execute`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read, Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/notification-subscriptions/me`

- Controller: `backend/app/routers/notification_subscriptions.py::list_subscriptions`
- Data Contract:
  - Path params: none
  - Query params: `entity_type`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[NotificationSubscriptionResponse]`
  - Response contracts: [`NotificationSubscriptionResponse`](#model-notificationsubscriptionresponse)
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
    - `db.execute`
    - `select`
    - `NotificationSubscription.created_at.desc`
  - Side effects: DB write, DB read, Notification dispatch
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/notification-subscriptions/{subscription_id}`

- Controller: `backend/app/routers/notification_subscriptions.py::update_subscription`
- Data Contract:
  - Path params: `subscription_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`NotificationSubscriptionUpdate`](#model-notificationsubscriptionupdate)
  - Response model: `NotificationSubscriptionResponse`
  - Response contracts: [`NotificationSubscriptionResponse`](#model-notificationsubscriptionresponse)
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
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Subscription not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


## Usage Examples (Domain)

### `GET /api/v1/notifications`

```bash
curl -X GET http://localhost:8000/api/v1/notifications -H "Authorization: Bearer $ACCESS_TOKEN" 
```

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "is_read": false,
  "title": "string",
  "type": "string",
  "user_id": "string",
  "action_url": "string",
  "created_at": "2026-01-01T00:00:00Z",
  "deliver_at": "2026-01-01T00:00:00Z"
}
```


### `POST /api/v1/mail/mailboxes/{mailbox_id}/send`

```bash
curl -X POST http://localhost:8000/api/v1/mail/mailboxes/{mailbox_id}/send -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '{"body": "string", "subject": "string", "to": "user@example.com", "bcc": "user@example.com", "cc": "user@example.com"}'
```

```json
{
  "message": "string"
}
```
