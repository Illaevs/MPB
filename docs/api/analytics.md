# Analytics & Audit API

Сгенерировано из `docs/API.md` на 2026-05-29 01:30:42 (local time).

## Scope
- Домен: `analytics`
- Описание: Дашбордовые сводки и аудит событий.
- Routers: `2`
- Endpoints: `6`
- Список роутеров: `dashboard`, `audit_logs`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели не обнаружены (endpoint'ы используют примитивные параметры или свободный JSON).

## Routers / Controllers Reference

### Router `dashboard`

Source: `backend/app/routers/dashboard.py`

Prefix: `/api/v1/dashboard`

Endpoints: `4`

#### `GET /api/v1/dashboard/activity`

- Controller: `backend/app/routers/dashboard.py::get_activity`
- Data Contract:
  - Path params: none
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
    - `Query`
    - `Depends`
    - `func.date`
    - `select(day_column.label('day'), func.count(EventLog.id)).where`
    - `db.execute`
    - `select`
    - `and_`
    - `func.count`
    - `EventLog.entity_id.in_`
  - Side effects: DB read, Audit/Event logging
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/dashboard/manager-summary`

- Controller: `backend/app/routers/dashboard.py::get_manager_summary`
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
    - `Task.status.notin_`
    - `and_`
    - `Task.due_date.is_not`
    - `db.execute`
    - `desc`
    - `User.full_name.asc`
    - `select`
    - `Deal.id.in_`
    - `Task.deal_id.in_`
    - `func.sum`
    - `func.count`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/dashboard/my-task-counts`

- Controller: `backend/app/routers/dashboard.py::my_task_counts`
- Summary: Счётчики виджета «Мои задачи» (только незавершённые):
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
    - `Task.status.in_`
    - `select`
    - `Task.assigned_to_user_id.is_`
    - `func.count`
    - `func.distinct`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/dashboard/summary`

- Controller: `backend/app/routers/dashboard.py::get_summary`
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
    - `select(func.count(UploadJob.id)).where`
    - `UploadJob.updated_at.is_not`
    - `db.execute`
    - `Notification.is_read.is_`
    - `Task.due_date.is_not`
    - `select`
    - `Notification.deliver_at.is_`
    - `Deal.id.in_`
    - `Task.deal_id.in_`
    - `OutgoingDocument.deal_id.in_`
    - `Document.project_id.in_`
  - Side effects: DB write, DB read, Notification dispatch, File/storage operation
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `audit_logs`

Source: `backend/app/routers/audit_logs.py`

Prefix: `/api/v1/audit-logs`

Endpoints: `2`

#### `GET /api/v1/audit-logs`

- Controller: `backend/app/routers/audit_logs.py::list_audit_logs`
- Data Contract:
  - Path params: none
  - Query params: `entity_type`: Optional[str] (optional, default=None, constraints=-); `entity_id`: Optional[str] (optional, default=None, constraints=-); `action`: Optional[str] (optional, default=None, constraints=-); `user_id`: Optional[str] (optional, default=None, constraints=-); `date_from`: Optional[datetime] (optional, default=None, constraints=-); `date_to`: Optional[datetime] (optional, default=None, constraints=-); `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[Dict[str, Any]]`
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
    - `select`
    - `query.order_by(AuditLog.created_at.desc()).offset(skip).limit`
    - `db.execute`
    - `query.order_by(AuditLog.created_at.desc()).offset`
    - `AuditLog.created_at.desc`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/audit-logs/{entity_type}/{entity_id}`

- Controller: `backend/app/routers/audit_logs.py::list_entity_audit_logs`
- Data Contract:
  - Path params: `entity_type`: str (required, default=-, constraints=-); `entity_id`: str (required, default=-, constraints=-)
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[Dict[str, Any]]`
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
    - `select(AuditLog).where(AuditLog.entity_type == entity_type, AuditLog.entity_id == str(entity_id)).order_by(AuditLog.created_at.desc()).offset(skip).limit`
    - `select(AuditLog).where(AuditLog.entity_type == entity_type, AuditLog.entity_id == str(entity_id)).order_by(AuditLog.created_at.desc()).offset`
    - `select(AuditLog).where(AuditLog.entity_type == entity_type, AuditLog.entity_id == str(entity_id)).order_by`
    - `AuditLog.created_at.desc`
    - `select(AuditLog).where`
    - `select`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


## Usage Examples (Domain)

Ключевые примеры отсутствуют для этого домена в исходном monolith reference.
