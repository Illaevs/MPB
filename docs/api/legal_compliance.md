# Legal & Compliance API

Сгенерировано из `docs/API.md` на 2026-05-19 01:30:03 (local time).

## Scope
- Домен: `legal_compliance`
- Описание: Юридическая работа и аккредитации.
- Routers: `2`
- Endpoints: `26`
- Список роутеров: `legal_work`, `accreditations`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `17`.

### Model `LegalCaseCreate`

Source: `backend/app/schemas/legal_work.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| case_number | Optional[str] | no | None | - |
| judge | Optional[str] | no | None | - |
| jurisdiction | Optional[str] | no | None | - |
| judge_assistant | Optional[str] | no | None | - |
| judge_assistant_phone | Optional[str] | no | None | - |
| plaintiff_id | Optional[str] | no | None | - |
| defendant_id | Optional[str] | no | None | - |
| description | Optional[str] | no | None | - |


### Model `LegalCaseEventCreate`

Source: `backend/app/schemas/legal_work.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| event_type | str | yes | - | - |
| event_date | date | yes | - | - |
| event_time | Optional[time] | no | None | - |
| courtroom | Optional[str] | no | None | - |


### Model `LegalCaseEventFileResponse`

Source: `backend/app/schemas/legal_work.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| event_id | str | yes | - | - |
| file_name | str | yes | - | - |
| storage_path | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |


### Model `LegalCaseEventResponse`

Source: `backend/app/schemas/legal_work.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| event_type | str | yes | - | - |
| event_date | date | yes | - | - |
| event_time | Optional[time] | no | None | - |
| courtroom | Optional[str] | no | None | - |
| id | str | yes | - | - |
| legal_case_id | str | yes | - | - |
| files | List[LegalCaseEventFileResponse] | no | [] | - |
| created_at | Optional[datetime] | no | None | - |


### Model `LegalCaseEventUpdate`

Source: `backend/app/schemas/legal_work.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| event_type | Optional[str] | no | None | - |
| event_date | Optional[date] | no | None | - |
| event_time | Optional[time] | no | None | - |
| courtroom | Optional[str] | no | None | - |


### Model `LegalCaseResponse`

Source: `backend/app/schemas/legal_work.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| case_number | Optional[str] | no | None | - |
| judge | Optional[str] | no | None | - |
| jurisdiction | Optional[str] | no | None | - |
| judge_assistant | Optional[str] | no | None | - |
| judge_assistant_phone | Optional[str] | no | None | - |
| plaintiff_id | Optional[str] | no | None | - |
| defendant_id | Optional[str] | no | None | - |
| description | Optional[str] | no | None | - |
| id | str | yes | - | - |
| plaintiff_name | Optional[str] | no | None | - |
| defendant_name | Optional[str] | no | None | - |
| events | List[LegalCaseEventResponse] | no | [] | - |
| tasks | List[LegalCaseTaskResponse] | no | [] | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `LegalCaseTaskLinkCreate`

Source: `backend/app/schemas/legal_work.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| task_id | str | yes | - | - |


### Model `LegalCaseTaskResponse`

Source: `backend/app/schemas/legal_work.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| title | str | yes | - | - |
| status | Optional[str] | no | None | - |
| due_date | Optional[date] | no | None | - |
| deal_id | Optional[str] | no | None | - |
| deal_title | Optional[str] | no | None | - |


### Model `LegalCaseUpdate`

Source: `backend/app/schemas/legal_work.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| case_number | Optional[str] | no | None | - |
| judge | Optional[str] | no | None | - |
| jurisdiction | Optional[str] | no | None | - |
| judge_assistant | Optional[str] | no | None | - |
| judge_assistant_phone | Optional[str] | no | None | - |
| plaintiff_id | Optional[str] | no | None | - |
| defendant_id | Optional[str] | no | None | - |
| description | Optional[str] | no | None | - |


### Model `AccreditationBulkAction`

Source: `backend/app/schemas/accreditation.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| ids | List[str] | yes | - | - |
| status | str | yes | - | - |
| comment | Optional[str] | no | None | - |


### Model `AccreditationCreate`

Source: `backend/app/schemas/accreditation.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| company_id | str | yes | - | - |
| direction_id | str | yes | - | - |
| status | Optional[str] | no | None | - |
| comment | Optional[str] | no | None | - |


### Model `AccreditationRequest`

Source: `backend/app/schemas/accreditation.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| company_id | str | yes | - | - |
| direction_ids | List[str] | yes | - | - |


### Model `AccreditationResponse`

Source: `backend/app/schemas/accreditation.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| company_id | str | yes | - | - |
| direction_id | str | yes | - | - |
| status | str | yes | - | - |
| comment | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `AccreditationUpdate`

Source: `backend/app/schemas/accreditation.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| status | Optional[str] | no | None | - |
| comment | Optional[str] | no | None | - |


### Model `CompanyDocumentCreate`

Source: `backend/app/schemas/company_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| company_id | str | yes | - | - |
| our_company_id | Optional[str] | no | None | - |
| doc_type | str | yes | - | - |
| doc_value | Optional[str] | no | None | - |
| file_name | Optional[str] | no | None | - |
| file_url | Optional[str] | no | None | - |
| storage_path | Optional[str] | no | None | - |
| file_size | Optional[int] | no | None | - |
| content_type | Optional[str] | no | None | - |
| parent_id | Optional[str] | no | None | - |
| status | Optional[str] | no | None | - |
| comment | Optional[str] | no | None | - |


### Model `CompanyDocumentResponse`

Source: `backend/app/schemas/company_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| company_id | str | yes | - | - |
| our_company_id | Optional[str] | no | None | - |
| our_company_name | Optional[str] | no | None | - |
| doc_type | str | yes | - | - |
| doc_value | Optional[str] | no | None | - |
| file_name | Optional[str] | no | None | - |
| file_url | Optional[str] | no | None | - |
| storage_path | Optional[str] | no | None | - |
| file_size | Optional[int] | no | None | - |
| content_type | Optional[str] | no | None | - |
| parent_id | Optional[str] | no | None | - |
| status | str | yes | - | - |
| comment | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `CompanyDocumentUpdate`

Source: `backend/app/schemas/company_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| our_company_id | Optional[str] | no | None | - |
| doc_value | Optional[str] | no | None | - |
| file_name | Optional[str] | no | None | - |
| file_url | Optional[str] | no | None | - |
| storage_path | Optional[str] | no | None | - |
| file_size | Optional[int] | no | None | - |
| content_type | Optional[str] | no | None | - |
| parent_id | Optional[str] | no | None | - |
| status | Optional[str] | no | None | - |
| comment | Optional[str] | no | None | - |


## Routers / Controllers Reference

### Router `legal_work`

Source: `backend/app/routers/legal_work.py`

Prefix: `/api/v1/legal-work`

Endpoints: `13`

#### `GET /api/v1/legal-work`

- Controller: `backend/app/routers/legal_work.py::list_legal_cases`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[LegalCaseResponse]`
  - Response contracts: [`LegalCaseResponse`](#model-legalcaseresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `events_result.scalars().all`
    - `db.execute`
    - `events_map.setdefault(event.legal_case_id, []).append`
    - `select(LegalCaseEvent).where(LegalCaseEvent.legal_case_id.in_(case_ids)).order_by`
    - `events_result.scalars`
    - `files_map.setdefault(file_item.event_id, []).append`
    - `selectinload`
    - `LegalCaseEvent.event_date.desc`
    - `LegalCaseEvent.created_at.desc`
    - `events_map.setdefault`
    - `select(LegalCaseEventFile).where`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/legal-work`

- Controller: `backend/app/routers/legal_work.py::create_legal_case`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LegalCaseCreate`](#model-legalcasecreate)
  - Response model: `LegalCaseResponse`
  - Response contracts: [`LegalCaseResponse`](#model-legalcaseresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LegalCase.create`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/legal-work/events/files/{file_id}`

- Controller: `backend/app/routers/legal_work.py::delete_event_file`
- Data Contract:
  - Path params: `file_id`: str (required, default=-, constraints=-)
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
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `storage_available`
    - `LegalCaseEventFile.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `delete(LegalCaseEventFile).where`
    - `delete_path`
    - `delete`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - `404`: `File not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/legal-work/events/files/{file_id}/download`

- Controller: `backend/app/routers/legal_work.py::download_event_file`
- Data Contract:
  - Path params: `file_id`: str (required, default=-, constraints=-)
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
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LegalCaseEventFile.get_by_id`
    - `HTTPException`
    - `storage_available`
    - `get_download_href`
  - Side effects: File/storage operation
- Error Handling:
  - `404`: `File not found`; `File not found in storage`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `502`: `Failed to resolve storage download link`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/legal-work/events/{event_id}`

- Controller: `backend/app/routers/legal_work.py::delete_event`
- Data Contract:
  - Path params: `event_id`: str (required, default=-, constraints=-)
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
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `storage_available`
    - `LegalCaseEvent.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `LegalCaseEvent.delete`
    - `select(LegalCaseEventFile).where`
    - `delete(LegalCaseEventFile).where`
    - `select`
    - `delete_path`
    - `delete`
  - Side effects: DB read, File/storage operation
- Error Handling:
  - `404`: `Event not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/legal-work/events/{event_id}`

- Controller: `backend/app/routers/legal_work.py::update_event`
- Data Contract:
  - Path params: `event_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LegalCaseEventUpdate`](#model-legalcaseeventupdate)
  - Response model: `LegalCaseEventResponse`
  - Response contracts: [`LegalCaseEventResponse`](#model-legalcaseeventresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LegalCaseEventResponse`
    - `HTTPException`
    - `LegalCaseEvent.get_by_id`
    - `LegalCaseEvent.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `Unknown event type`; body schema `{"detail": "..."}`
  - `404`: `Event not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/legal-work/events/{event_id}/files/upload`

- Controller: `backend/app/routers/legal_work.py::upload_event_files`
- Data Contract:
  - Path params: `event_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `files`: List[UploadFile] (required, default=-, constraints=-)
  - Body: none
  - Response model: `List[LegalCaseEventFileResponse]`
  - Response contracts: [`LegalCaseEventFileResponse`](#model-legalcaseeventfileresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `_legal_event_storage_path`
    - `storage_available`
    - `HTTPException`
    - `LegalCaseEvent.get_by_id`
    - `LegalCase.get_by_id`
    - `ensure_path`
    - `clean_name`
    - `LegalCaseEventFile`
    - `db.add`
    - `db.commit`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `404`: `Event not found`; `Case not found`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/legal-work/{case_id}`

- Controller: `backend/app/routers/legal_work.py::delete_legal_case`
- Data Contract:
  - Path params: `case_id`: str (required, default=-, constraints=-)
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
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LegalCase.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `LegalCase.delete`
    - `select(LegalCaseEvent.id).where`
    - `event_ids.all`
    - `delete(LegalCaseEvent).where`
    - `delete(LegalCaseEventFile).where`
    - `select`
    - `LegalCaseEventFile.event_id.in_`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - `404`: `Case not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/legal-work/{case_id}`

- Controller: `backend/app/routers/legal_work.py::get_legal_case`
- Data Contract:
  - Path params: `case_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `LegalCaseResponse`
  - Response contracts: [`LegalCaseResponse`](#model-legalcaseresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `events_result.scalars().all`
    - `db.execute`
    - `HTTPException`
    - `LegalCaseTaskResponse`
    - `select(LegalCaseEvent).where(LegalCaseEvent.legal_case_id == case.id).order_by`
    - `events_result.scalars`
    - `files_map.setdefault(file_item.event_id, []).append`
    - `LegalCaseEventResponse`
    - `LegalCaseEvent.event_date.desc`
    - `LegalCaseEvent.created_at.desc`
    - `select(LegalCaseEventFile).where`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - `404`: `Case not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/legal-work/{case_id}`

- Controller: `backend/app/routers/legal_work.py::update_legal_case`
- Data Contract:
  - Path params: `case_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LegalCaseUpdate`](#model-legalcaseupdate)
  - Response model: `LegalCaseResponse`
  - Response contracts: [`LegalCaseResponse`](#model-legalcaseresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LegalCase.get_by_id`
    - `HTTPException`
    - `LegalCase.update`
  - Side effects: DB write
- Error Handling:
  - `404`: `Case not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/legal-work/{case_id}/events`

- Controller: `backend/app/routers/legal_work.py::create_event`
- Data Contract:
  - Path params: `case_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LegalCaseEventCreate`](#model-legalcaseeventcreate)
  - Response model: `LegalCaseEventResponse`
  - Response contracts: [`LegalCaseEventResponse`](#model-legalcaseeventresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LegalCaseEventResponse`
    - `HTTPException`
    - `LegalCase.get_by_id`
    - `LegalCaseEvent.create`
  - Side effects: DB write
- Error Handling:
  - `400`: `Unknown event type`; body schema `{"detail": "..."}`
  - `404`: `Case not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/legal-work/{case_id}/tasks/link`

- Controller: `backend/app/routers/legal_work.py::link_task`
- Data Contract:
  - Path params: `case_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LegalCaseTaskLinkCreate`](#model-legalcasetasklinkcreate)
  - Response model: `LegalCaseTaskResponse`
  - Response contracts: [`LegalCaseTaskResponse`](#model-legalcasetaskresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LegalCaseTask`
    - `db.add`
    - `LegalCaseTaskResponse`
    - `LegalCase.get_by_id`
    - `HTTPException`
    - `Task.get_by_id`
    - `db.execute`
    - `db.commit`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Task already linked`; body schema `{"detail": "..."}`
  - `404`: `Case not found`; `Task not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/legal-work/{case_id}/tasks/{task_id}`

- Controller: `backend/app/routers/legal_work.py::unlink_task`
- Data Contract:
  - Path params: `case_id`: str (required, default=-, constraints=-); `task_id`: str (required, default=-, constraints=-)
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
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `db.commit`
    - `HTTPException`
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Task link not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `accreditations`

Source: `backend/app/routers/accreditations.py`

Prefix: `/api/v1/accreditations`

Endpoints: `13`

#### `GET /api/v1/accreditations`

- Controller: `backend/app/routers/accreditations.py::list_accreditations`
- Data Contract:
  - Path params: none
  - Query params: `company_id`: Optional[str] (optional, default=None, constraints=-); `direction_id`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[AccreditationResponse]`
  - Response contracts: [`AccreditationResponse`](#model-accreditationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `db.execute`
    - `AccreditationResponse.model_validate`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/accreditations`

- Controller: `backend/app/routers/accreditations.py::create_accreditation`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AccreditationCreate`](#model-accreditationcreate)
  - Response model: `AccreditationResponse`
  - Response contracts: [`AccreditationResponse`](#model-accreditationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `CompanyAccreditation`
    - `db.add`
    - `AccreditationResponse.model_validate`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/accreditations/accredited-company-ids`

- Controller: `backend/app/routers/accreditations.py::accredited_company_ids`
- Summary: Company ids that have `status` accreditation in **every** direction
- Data Contract:
  - Path params: none
  - Query params: `direction_ids`: str (required, default=-, constraints=-); `status`: str (optional, default='approved', constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[str]`
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `and_`
    - `select`
    - `CompanyAccreditation.direction_id.in_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/accreditations/bulk`

- Controller: `backend/app/routers/accreditations.py::bulk_update_accreditations`
- Summary: Bulk approve/reject accreditation records by id.
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AccreditationBulkAction`](#model-accreditationbulkaction)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `CompanyAccreditation.id.in_`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `status must be approved or rejected`; `Comment is required for rejection`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/accreditations/bulk-directions`

- Controller: `backend/app/routers/accreditations.py::bulk_set_company_directions`
- Summary: Admin bulk approve/reject several DIRECTIONS for one company,
- Data Contract:
  - Path params: none
  - Query params: `status`: str (optional, default='approved', constraints=-); `comment`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AccreditationRequest`](#model-accreditationrequest)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `db.commit`
    - `db.execute`
    - `db.add`
    - `CompanyAccreditation`
    - `and_`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `status must be approved or rejected`; `Comment is required for rejection`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/accreditations/companies/{company_id}/documents`

- Controller: `backend/app/routers/accreditations.py::list_company_documents`
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[CompanyDocumentResponse]`
  - Response contracts: [`CompanyDocumentResponse`](#model-companydocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `CompanyDocumentResponse.model_validate`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/accreditations/companies/{company_id}/documents`

- Controller: `backend/app/routers/accreditations.py::create_company_document`
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`CompanyDocumentCreate`](#model-companydocumentcreate)
  - Response model: `CompanyDocumentResponse`
  - Response contracts: [`CompanyDocumentResponse`](#model-companydocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `CompanyDocument`
    - `db.add`
    - `CompanyDocumentResponse.model_validate`
    - `db.commit`
    - `db.refresh`
    - `db.execute`
    - `HTTPException`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Invalid parent document`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/accreditations/companies/{company_id}/documents/upload`

- Controller: `backend/app/routers/accreditations.py::upload_company_document`
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: `doc_type`: str (required, default=-, constraints=-); `doc_value`: Optional[str] (optional, default=None, constraints=-); `parent_id`: Optional[str] (optional, default=None, constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `CompanyDocumentResponse`
  - Response contracts: [`CompanyDocumentResponse`](#model-companydocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Form`
    - `File`
    - `Depends`
    - `clean_name`
    - `CompanyDocument`
    - `db.add`
    - `CompanyDocumentResponse.model_validate`
    - `storage_available`
    - `HTTPException`
    - `ensure_path`
    - `upload_bytes_with_safe_extension`
    - `db.commit`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - `400`: `Invalid parent document`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/accreditations/documents/{document_id}`

- Controller: `backend/app/routers/accreditations.py::delete_company_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
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
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Approved documents cannot be deleted`; body schema `{"detail": "..."}`
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/accreditations/documents/{document_id}`

- Controller: `backend/app/routers/accreditations.py::update_company_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`CompanyDocumentUpdate`](#model-companydocumentupdate)
  - Response model: `CompanyDocumentResponse`
  - Response contracts: [`CompanyDocumentResponse`](#model-companydocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `CompanyDocumentResponse.model_validate`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Comment is required for rejection`; body schema `{"detail": "..."}`
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/accreditations/documents/{document_id}/download`

- Controller: `backend/app/routers/accreditations.py::download_company_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
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
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `storage_available`
    - `HTTPException`
    - `db.execute`
    - `get_download_href`
    - `select`
  - Side effects: DB read, File/storage operation
- Error Handling:
  - `400`: `Document does not have storage path`; body schema `{"detail": "..."}`
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/accreditations/request`

- Controller: `backend/app/routers/accreditations.py::request_accreditations`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AccreditationRequest`](#model-accreditationrequest)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.commit`
    - `db.execute`
    - `CompanyAccreditation`
    - `db.add`
    - `and_`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/accreditations/{accreditation_id}`

- Controller: `backend/app/routers/accreditations.py::update_accreditation`
- Data Contract:
  - Path params: `accreditation_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AccreditationUpdate`](#model-accreditationupdate)
  - Response model: `AccreditationResponse`
  - Response contracts: [`AccreditationResponse`](#model-accreditationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `AccreditationResponse.model_validate`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Comment is required for rejection`; body schema `{"detail": "..."}`
  - `404`: `Accreditation not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


## Usage Examples (Domain)

Ключевые примеры отсутствуют для этого домена в исходном monolith reference.
