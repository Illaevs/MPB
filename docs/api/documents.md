# Document Flow & Storage API

Сгенерировано из `docs/API.md` на 2026-02-15 03:22:39 (local time).

## Scope
- Домен: `documents`
- Описание: Реестры документов, исходящие, загрузки, хранилище и файловый каталог.
- Routers: `5`
- Endpoints: `54`
- Список роутеров: `document_registry`, `outgoing_registry`, `uploads`, `storage`, `files_catalog`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `21`.

### Model `DocumentCreate`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| doc_type | str | yes | - | - |
| title | str | yes | - | - |
| number | Optional[str] | no | None | - |
| document_date | Optional[date] | no | None | - |
| status | Optional[str] | no | 'draft' | - |
| project_id | Optional[str] | no | None | - |
| counterparty_id | Optional[str] | no | None | - |
| our_company_id | Optional[str] | no | None | - |
| source_type | Optional[str] | no | None | - |
| source_id | Optional[str] | no | None | - |


### Model `DocumentDispatchChannelCreate`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| channel | str | yes | - | - |
| channel_date | date | yes | - | - |
| confirmation_file | Optional[str] | no | None | - |
| track_number | Optional[str] | no | None | - |


### Model `DocumentDispatchChannelResponse`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| dispatch_id | str | yes | - | - |
| channel | str | yes | - | - |
| channel_date | date | yes | - | - |
| confirmation_file | Optional[str] | no | None | - |
| track_number | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |


### Model `DocumentDispatchChannelUpdate`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| channel_date | Optional[date] | no | None | - |
| confirmation_file | Optional[str] | no | None | - |
| track_number | Optional[str] | no | None | - |


### Model `DocumentDispatchCreate`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| document_id | Optional[str] | no | None | - |
| package_id | Optional[str] | no | None | - |
| status | Optional[str] | no | 'sent' | - |
| note | Optional[str] | no | None | - |


### Model `DocumentDispatchResponse`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| document_id | Optional[str] | no | None | - |
| package_id | Optional[str] | no | None | - |
| status | str | yes | - | - |
| note | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |


### Model `DocumentPackageCreate`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| package_date | Optional[date] | no | None | - |
| status | Optional[str] | no | 'draft' | - |
| project_id | Optional[str] | no | None | - |
| counterparty_id | Optional[str] | no | None | - |
| our_company_id | Optional[str] | no | None | - |


### Model `DocumentPackageItemCreate`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| document_id | str | yes | - | - |


### Model `DocumentPackageItemResponse`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| package_id | str | yes | - | - |
| document_id | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |


### Model `DocumentPackageResponse`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| package_date | Optional[date] | no | None | - |
| status | Optional[str] | no | 'draft' | - |
| project_id | Optional[str] | no | None | - |
| counterparty_id | Optional[str] | no | None | - |
| our_company_id | Optional[str] | no | None | - |
| id | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |


### Model `DocumentPackageUpdate`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | Optional[str] | no | None | - |
| package_date | Optional[date] | no | None | - |
| status | Optional[str] | no | None | - |
| project_id | Optional[str] | no | None | - |
| counterparty_id | Optional[str] | no | None | - |
| our_company_id | Optional[str] | no | None | - |


### Model `DocumentRelationCreate`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| related_document_id | str | yes | - | - |
| relation_type | Optional[str] | no | 'link' | - |


### Model `DocumentRelationResponse`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| document_id | str | yes | - | - |
| related_document_id | str | yes | - | - |
| relation_type | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| related_document | Optional[DocumentResponse] | no | None | - |
| document | Optional[DocumentResponse] | no | None | - |


### Model `DocumentResponse`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| doc_type | str | yes | - | - |
| title | str | yes | - | - |
| number | Optional[str] | no | None | - |
| document_date | Optional[date] | no | None | - |
| status | Optional[str] | no | 'draft' | - |
| project_id | Optional[str] | no | None | - |
| counterparty_id | Optional[str] | no | None | - |
| our_company_id | Optional[str] | no | None | - |
| source_type | Optional[str] | no | None | - |
| source_id | Optional[str] | no | None | - |
| id | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `DocumentUpdate`

Source: `backend/app/schemas/document_registry.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| doc_type | Optional[str] | no | None | - |
| title | Optional[str] | no | None | - |
| number | Optional[str] | no | None | - |
| document_date | Optional[date] | no | None | - |
| status | Optional[str] | no | None | - |
| project_id | Optional[str] | no | None | - |
| counterparty_id | Optional[str] | no | None | - |
| our_company_id | Optional[str] | no | None | - |
| source_type | Optional[str] | no | None | - |
| source_id | Optional[str] | no | None | - |


### Model `OutgoingDocumentDetailResponse`

Source: `backend/app/schemas/outgoing_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| recipient_company_id | Union[str, UUID] | yes | - | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| letter_date | date | yes | - | - |
| subject | str | yes | - | - |
| body | Optional[str] | no | '' | - |
| attachments_list | Optional[str] | no | '' | - |
| recipient_short_name | Optional[str] | no | None | - |
| recipient_to_name | Optional[str] | no | None | - |
| recipient_appeal | Optional[str] | no | None | - |
| recipient_eio | Optional[str] | no | None | - |
| recipient_salutation | Optional[str] | no | None | - |
| status | Optional[str] | no | 'draft' | - |
| id | Union[str, UUID] | yes | - | - |
| outgoing_number | str | yes | - | - |
| outgoing_number_seq | int | yes | - | - |
| outgoing_number_display | Optional[str] | no | None | - |
| our_company_key | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |
| recipient_company_name | Optional[str] | no | None | - |
| deal_title | Optional[str] | no | None | - |
| versions | List[OutgoingDocumentVersionResponse] | no | [] | - |
| files | List[OutgoingDocumentFileResponse] | no | [] | - |


### Model `OutgoingDocumentFileResponse`

Source: `backend/app/schemas/outgoing_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | Union[str, UUID] | yes | - | - |
| document_id | Union[str, UUID] | yes | - | - |
| version_id | Optional[Union[str, UUID]] | no | None | - |
| file_type | str | yes | - | - |
| file_path | Optional[str] | no | None | - |
| file_name | Optional[str] | no | None | - |
| public_url | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |


### Model `OutgoingDocumentResponse`

Source: `backend/app/schemas/outgoing_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| recipient_company_id | Union[str, UUID] | yes | - | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| letter_date | date | yes | - | - |
| subject | str | yes | - | - |
| body | Optional[str] | no | '' | - |
| attachments_list | Optional[str] | no | '' | - |
| recipient_short_name | Optional[str] | no | None | - |
| recipient_to_name | Optional[str] | no | None | - |
| recipient_appeal | Optional[str] | no | None | - |
| recipient_eio | Optional[str] | no | None | - |
| recipient_salutation | Optional[str] | no | None | - |
| status | Optional[str] | no | 'draft' | - |
| id | Union[str, UUID] | yes | - | - |
| outgoing_number | str | yes | - | - |
| outgoing_number_seq | int | yes | - | - |
| outgoing_number_display | Optional[str] | no | None | - |
| our_company_key | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |
| recipient_company_name | Optional[str] | no | None | - |
| deal_title | Optional[str] | no | None | - |


### Model `OutgoingDocumentUpdate`

Source: `backend/app/schemas/outgoing_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| recipient_company_id | Optional[Union[str, UUID]] | no | None | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| letter_date | Optional[date] | no | None | - |
| subject | Optional[str] | no | None | - |
| body | Optional[str] | no | None | - |
| attachments_list | Optional[str] | no | None | - |
| recipient_short_name | Optional[str] | no | None | - |
| recipient_to_name | Optional[str] | no | None | - |
| recipient_appeal | Optional[str] | no | None | - |
| recipient_eio | Optional[str] | no | None | - |
| recipient_salutation | Optional[str] | no | None | - |
| status | Optional[str] | no | None | - |
| our_company_key | Optional[str] | no | None | - |
| outgoing_number_suffix | Optional[str] | no | None | - |


### Model `OutgoingDocumentVersionResponse`

Source: `backend/app/schemas/outgoing_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | Union[str, UUID] | yes | - | - |
| document_id | Union[str, UUID] | yes | - | - |
| version_number | int | yes | - | - |
| status | Optional[str] | no | 'draft' | - |
| created_at | Optional[datetime] | no | None | - |
| created_by | Optional[str] | no | None | - |
| comment | Optional[str] | no | None | - |
| pdf_path | Optional[str] | no | None | - |
| pdf_public_url | Optional[str] | no | None | - |


### Model `UploadJobResponse`

Source: `backend/app/schemas/upload_job.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| status | str | yes | - | - |
| module | Optional[str] | no | None | - |
| entity_id | Optional[str] | no | None | - |
| file_kind | Optional[str] | no | None | - |
| file_name | Optional[str] | no | None | - |
| size_bytes | Optional[int] | no | None | - |
| error_message | Optional[str] | no | None | - |
| created_by | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |
| meta | Optional[Dict[str, Any]] | no | None | - |


## Routers / Controllers Reference

### Router `document_registry`

Source: `backend/app/routers/document_registry.py`

Prefix: `/api/v1/document-registry`

Endpoints: `27`

#### `GET /api/v1/document-registry`

- Controller: `backend/app/routers/document_registry.py::list_documents`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `doc_type`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `date_from`: Optional[str] (optional, default=None, constraints=-); `date_to`: Optional[str] (optional, default=None, constraints=-); `project_id`: Optional[str] (optional, default=None, constraints=-); `counterparty_id`: Optional[str] (optional, default=None, constraints=-); `our_company_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[DocumentResponse]`
  - Response contracts: [`DocumentResponse`](#model-documentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `get_section_permissions`
    - `db.execute`
    - `date_type.fromisoformat`
    - `allowed_deal_ids`
    - `Document.project_id.in_`
    - `Document.doc_type.in_`
    - `Document.status.in_`
    - `HTTPException`
    - `Document.document_date.desc`
    - `Document.created_at.desc`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Invalid date_from`; `Invalid date_to`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/document-registry`

- Controller: `backend/app/routers/document_registry.py::create_document`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DocumentCreate`](#model-documentcreate)
  - Response model: `DocumentResponse`
  - Response contracts: [`DocumentResponse`](#model-documentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Document`
    - `db.add`
    - `db.commit`
    - `db.refresh`
    - `log_event`
  - Side effects: DB write, Audit/Event logging
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-registry/dispatches`

- Controller: `backend/app/routers/document_registry.py::list_dispatches`
- Data Contract:
  - Path params: none
  - Query params: `document_id`: Optional[str] (optional, default=None, constraints=-); `package_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[DocumentDispatchResponse]`
  - Response contracts: [`DocumentDispatchResponse`](#model-documentdispatchresponse)
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
    - `DocumentDispatch.created_at.desc`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/document-registry/dispatches`

- Controller: `backend/app/routers/document_registry.py::create_dispatch`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DocumentDispatchCreate`](#model-documentdispatchcreate)
  - Response model: `DocumentDispatchResponse`
  - Response contracts: [`DocumentDispatchResponse`](#model-documentdispatchresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `DocumentDispatch`
    - `db.add`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `db.execute`
    - `log_event`
    - `select`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - `400`: `Provide either document_id or package_id`; body schema `{"detail": "..."}`
  - `404`: `Document not found`; `Package not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/document-registry/dispatches/{dispatch_id}`

- Controller: `backend/app/routers/document_registry.py::delete_dispatch`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-)
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
  - `404`: `Dispatch not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-registry/dispatches/{dispatch_id}/channels`

- Controller: `backend/app/routers/document_registry.py::list_dispatch_channels`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[DocumentDispatchChannelResponse]`
  - Response contracts: [`DocumentDispatchChannelResponse`](#model-documentdispatchchannelresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/document-registry/dispatches/{dispatch_id}/channels`

- Controller: `backend/app/routers/document_registry.py::add_dispatch_channel`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DocumentDispatchChannelCreate`](#model-documentdispatchchannelcreate)
  - Response model: `DocumentDispatchChannelResponse`
  - Response contracts: [`DocumentDispatchChannelResponse`](#model-documentdispatchchannelresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `DocumentDispatchChannel`
    - `db.add`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `log_event`
    - `select`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - `404`: `Dispatch not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/document-registry/dispatches/{dispatch_id}/channels/{channel_id}`

- Controller: `backend/app/routers/document_registry.py::delete_dispatch_channel`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-); `channel_id`: str (required, default=-, constraints=-)
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
  - `404`: `Channel not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/document-registry/dispatches/{dispatch_id}/channels/{channel_id}`

- Controller: `backend/app/routers/document_registry.py::update_dispatch_channel`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-); `channel_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DocumentDispatchChannelUpdate`](#model-documentdispatchchannelupdate)
  - Response model: `DocumentDispatchChannelResponse`
  - Response contracts: [`DocumentDispatchChannelResponse`](#model-documentdispatchchannelresponse)
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
    - `log_event`
    - `select`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - `404`: `Channel not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-registry/dispatches/{dispatch_id}/channels/{channel_id}/download`

- Controller: `backend/app/routers/document_registry.py::download_dispatch_channel_file`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-); `channel_id`: str (required, default=-, constraints=-)
  - Query params: `file_path`: str (required, default=-, constraints=-)
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
    - `db.execute`
    - `HTTPException`
    - `get_download_href`
    - `select`
  - Side effects: DB read, File/storage operation
- Error Handling:
  - `400`: `Invalid file path`; body schema `{"detail": "..."}`
  - `404`: `Channel not found`; `Files not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/document-registry/dispatches/{dispatch_id}/channels/{channel_id}/files`

- Controller: `backend/app/routers/document_registry.py::delete_dispatch_channel_file`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-); `channel_id`: str (required, default=-, constraints=-)
  - Query params: `file_path`: str (required, default=-, constraints=-)
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
    - `db.execute`
    - `HTTPException`
    - `delete_path`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `400`: `Invalid file path`; body schema `{"detail": "..."}`
  - `404`: `Channel not found`; `Files not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-registry/dispatches/{dispatch_id}/channels/{channel_id}/files`

- Controller: `backend/app/routers/document_registry.py::list_dispatch_channel_files`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-); `channel_id`: str (required, default=-, constraints=-)
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
    - `list_items`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `Channel not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/document-registry/dispatches/{dispatch_id}/channels/{channel_id}/upload`

- Controller: `backend/app/routers/document_registry.py::upload_dispatch_channel_files`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-); `channel_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `files`: List[UploadFile] (required, default=-, constraints=-)
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `storage_available`
    - `HTTPException`
    - `db.execute`
    - `ensure_path`
    - `upload.read`
    - `upload_bytes_with_safe_extension`
    - `db.commit`
    - `db.refresh`
    - `clean_name`
    - `select`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - `400`: `Files are required`; body schema `{"detail": "..."}`
  - `404`: `Dispatch not found`; `Channel not found`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-registry/packages`

- Controller: `backend/app/routers/document_registry.py::list_packages`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `project_id`: Optional[str] (optional, default=None, constraints=-); `counterparty_id`: Optional[str] (optional, default=None, constraints=-); `our_company_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[DocumentPackageResponse]`
  - Response contracts: [`DocumentPackageResponse`](#model-documentpackageresponse)
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
    - `or_`
    - `DocumentPackage.status.in_`
    - `DocumentPackage.title.like`
    - `DocumentPackage.created_at.desc`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/document-registry/packages`

- Controller: `backend/app/routers/document_registry.py::create_package`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DocumentPackageCreate`](#model-documentpackagecreate)
  - Response model: `DocumentPackageResponse`
  - Response contracts: [`DocumentPackageResponse`](#model-documentpackageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `DocumentPackage`
    - `db.add`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/document-registry/packages/items/{item_id}`

- Controller: `backend/app/routers/document_registry.py::delete_package_item`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
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
  - `404`: `Package item not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/document-registry/packages/{package_id}`

- Controller: `backend/app/routers/document_registry.py::delete_package`
- Data Contract:
  - Path params: `package_id`: str (required, default=-, constraints=-)
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
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Package not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/document-registry/packages/{package_id}`

- Controller: `backend/app/routers/document_registry.py::update_package`
- Data Contract:
  - Path params: `package_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DocumentPackageUpdate`](#model-documentpackageupdate)
  - Response model: `DocumentPackageResponse`
  - Response contracts: [`DocumentPackageResponse`](#model-documentpackageresponse)
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
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Package not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-registry/packages/{package_id}/items`

- Controller: `backend/app/routers/document_registry.py::list_package_items`
- Data Contract:
  - Path params: `package_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[DocumentPackageItemResponse]`
  - Response contracts: [`DocumentPackageItemResponse`](#model-documentpackageitemresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/document-registry/packages/{package_id}/items`

- Controller: `backend/app/routers/document_registry.py::add_package_item`
- Data Contract:
  - Path params: `package_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DocumentPackageItemCreate`](#model-documentpackageitemcreate)
  - Response model: `DocumentPackageItemResponse`
  - Response contracts: [`DocumentPackageItemResponse`](#model-documentpackageitemresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `DocumentPackageItem`
    - `db.add`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Package not found`; `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/document-registry/relations/{relation_id}`

- Controller: `backend/app/routers/document_registry.py::delete_relation`
- Data Contract:
  - Path params: `relation_id`: str (required, default=-, constraints=-)
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
  - `404`: `Relation not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/document-registry/{document_id}`

- Controller: `backend/app/routers/document_registry.py::delete_document`
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
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-registry/{document_id}`

- Controller: `backend/app/routers/document_registry.py::get_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `DocumentResponse`
  - Response contracts: [`DocumentResponse`](#model-documentresponse)
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
    - `get_section_permissions`
    - `allowed_deal_ids`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/document-registry/{document_id}`

- Controller: `backend/app/routers/document_registry.py::update_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DocumentUpdate`](#model-documentupdate)
  - Response model: `DocumentResponse`
  - Response contracts: [`DocumentResponse`](#model-documentresponse)
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
    - `log_event`
    - `select`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-registry/{document_id}/parent-relations`

- Controller: `backend/app/routers/document_registry.py::list_parent_relations`
- Summary: Get relations where this document is the child (linked TO by other documents)
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[DocumentRelationResponse]`
  - Response contracts: [`DocumentRelationResponse`](#model-documentrelationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `selectinload`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/document-registry/{document_id}/relations`

- Controller: `backend/app/routers/document_registry.py::list_relations`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[DocumentRelationResponse]`
  - Response contracts: [`DocumentRelationResponse`](#model-documentrelationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `selectinload`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/document-registry/{document_id}/relations`

- Controller: `backend/app/routers/document_registry.py::add_relation`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DocumentRelationCreate`](#model-documentrelationcreate)
  - Response model: `DocumentRelationResponse`
  - Response contracts: [`DocumentRelationResponse`](#model-documentrelationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `DocumentRelation`
    - `db.add`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `selectinload`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Cannot link document to itself`; `Relation already exists`; body schema `{"detail": "..."}`
  - `404`: `Document not found`; `Related document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `outgoing_registry`

Source: `backend/app/routers/outgoing_registry.py`

Prefix: `/api/v1/outgoing-registry`

Endpoints: `9`

#### `GET /api/v1/outgoing-registry`

- Controller: `backend/app/routers/outgoing_registry.py::get_outgoing_documents`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=20, constraints=-); `recipient_company_id`: Optional[str] (optional, default=None, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `our_company_key`: Optional[str] (optional, default=None, constraints=-); `date_from`: Optional[str] (optional, default=None, constraints=-); `date_to`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[OutgoingDocumentResponse]`
  - Response contracts: [`OutgoingDocumentResponse`](#model-outgoingdocumentresponse)
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
    - `get_section_permissions`
    - `db.execute`
    - `or_`
    - `and_`
    - `allowed_deal_ids`
    - `OutgoingDocument.deal_id.in_`
    - `OutgoingDocument.subject.ilike`
    - `OutgoingDocument.outgoing_number.ilike`
    - `OutgoingDocument.attachments_list.ilike`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/outgoing-registry`

- Controller: `backend/app/routers/outgoing_registry.py::create_outgoing_document`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `recipient_company_id`: str (required, default=-, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `letter_date`: Optional[str] (optional, default=None, constraints=-); `subject`: str (required, default=-, constraints=-); `body`: Optional[str] (optional, default='', constraints=-); `attachments_list`: Optional[str] (optional, default='', constraints=-); `recipient_short_name`: Optional[str] (optional, default='', constraints=-); `recipient_to_name`: Optional[str] (optional, default='', constraints=-); `recipient_appeal`: Optional[str] (optional, default='', constraints=-); `recipient_eio`: Optional[str] (optional, default='', constraints=-); `recipient_salutation`: Optional[str] (optional, default='', constraints=-); `status`: Optional[str] (optional, default='draft', constraints=-); `our_company_key`: Optional[str] (optional, default=None, constraints=-)
  - File params: `attachments_files`: Optional[List[UploadFile]] (optional, default=None, constraints=-)
  - Body: none
  - Response model: `OutgoingDocumentDetailResponse`
  - Response contracts: [`OutgoingDocumentDetailResponse`](#model-outgoingdocumentdetailresponse)
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
    - `Company.get_by_id`
    - `HTTPException`
    - `Deal.get_by_id`
    - `storage_available`
    - `ensure_path`
    - `clean_name`
    - `log_event`
    - `OutgoingDocument.create`
    - `upload.read`
  - Side effects: DB write, Audit/Event logging, File/storage operation
- Error Handling:
  - `404`: `Recipient company not found`; `Deal not found`; body schema `{"detail": "..."}`
  - `409`: `Unable to allocate unique outgoing number, retry`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/outgoing-registry/sequences`

- Controller: `backend/app/routers/outgoing_registry.py::get_outgoing_sequences`
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
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/outgoing-registry/sequences/{company_key}`

- Controller: `backend/app/routers/outgoing_registry.py::update_outgoing_sequence`
- Data Contract:
  - Path params: `company_key`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: `next_seq`: int
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
    - `HTTPException`
    - `db.execute`
    - `OutgoingNumberSequence`
    - `db.add`
    - `db.commit`
    - `db.rollback`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `next_seq must be >= 1`; body schema `{"detail": "..."}`
  - `409`: `Sequence update busy, retry`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/outgoing-registry/{document_id}`

- Controller: `backend/app/routers/outgoing_registry.py::delete_outgoing_document`
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
    - `OutgoingDocument.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `delete_path`
    - `and_`
    - `delete`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/outgoing-registry/{document_id}`

- Controller: `backend/app/routers/outgoing_registry.py::get_outgoing_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `OutgoingDocumentDetailResponse`
  - Response contracts: [`OutgoingDocumentDetailResponse`](#model-outgoingdocumentdetailresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `OutgoingDocument.get_by_id`
    - `HTTPException`
    - `get_section_permissions`
    - `allowed_deal_ids`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/outgoing-registry/{document_id}`

- Controller: `backend/app/routers/outgoing_registry.py::update_outgoing_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`OutgoingDocumentUpdate`](#model-outgoingdocumentupdate)
  - Response model: `OutgoingDocumentDetailResponse`
  - Response contracts: [`OutgoingDocumentDetailResponse`](#model-outgoingdocumentdetailresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `OutgoingDocument.get_by_id`
    - `HTTPException`
    - `Company.get_by_id`
    - `Deal.get_by_id`
    - `OutgoingDocument.update`
  - Side effects: DB write
- Error Handling:
  - `404`: `Document not found`; `Recipient company not found`; `Deal not found`; body schema `{"detail": "..."}`
  - `422`: `Invalid outgoing registry payload`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/outgoing-registry/{document_id}/attachments`

- Controller: `backend/app/routers/outgoing_registry.py::upload_outgoing_attachments`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `attachments_files`: List[UploadFile] (required, default=-, constraints=-)
  - Body: none
  - Response model: `List[OutgoingDocumentFileResponse]`
  - Response contracts: [`OutgoingDocumentFileResponse`](#model-outgoingdocumentfileresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `storage_available`
    - `HTTPException`
    - `OutgoingDocument.get_by_id`
    - `ensure_path`
    - `clean_name`
    - `OutgoingDocumentFileResponse.model_validate`
    - `upload.read`
    - `upload_bytes_with_safe_extension`
    - `publish`
    - `log_event`
  - Side effects: DB write, Audit/Event logging, File/storage operation
- Error Handling:
  - `400`: `Files are required`; body schema `{"detail": "..."}`
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/outgoing-registry/{document_id}/versions`

- Controller: `backend/app/routers/outgoing_registry.py::create_outgoing_version`
- Summary: Create a new version from uploaded DOCX file (converts to PDF).
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: `comment`: Optional[str] (optional, default=None, constraints=-); `created_by`: Optional[str] (optional, default=None, constraints=-)
  - File params: `file`: Optional[UploadFile] (optional, default=None, constraints=-)
  - Body: none
  - Response model: `OutgoingDocumentVersionResponse`
  - Response contracts: [`OutgoingDocumentVersionResponse`](#model-outgoingdocumentversionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Form`
    - `Depends`
    - `clean_name`
    - `OutgoingDocumentVersionResponse.model_validate`
    - `OutgoingDocument.get_by_id`
    - `HTTPException`
    - `OutgoingDocumentVersion.get_by_document`
    - `storage_available`
    - `ensure_path`
    - `upload_bytes_with_safe_extension`
    - `publish`
  - Side effects: DB write, Audit/Event logging, File/storage operation
- Error Handling:
  - `404`: `Document not found`; `Recipient company not found`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `uploads`

Source: `backend/app/routers/uploads.py`

Prefix: `/api/v1/uploads`

Endpoints: `9`

#### `GET /api/v1/uploads`

- Controller: `backend/app/routers/uploads.py::list_upload_jobs`
- Data Contract:
  - Path params: none
  - Query params: `limit`: int (optional, default=100, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[UploadJobResponse]`
  - Response contracts: [`UploadJobResponse`](#model-uploadjobresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select(UploadJob).where(UploadJob.created_by == str(user.id)).order_by(UploadJob.created_at.desc()).limit`
    - `db.execute`
    - `select(UploadJob).where(UploadJob.created_by == str(user.id)).order_by`
    - `UploadJob.created_at.desc`
    - `select(UploadJob).where`
    - `select`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/uploads/accreditations/documents`

- Controller: `backend/app/routers/uploads.py::queue_accreditation_document_upload`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `company_id`: str (required, default=-, constraints=-); `doc_type`: str (required, default=-, constraints=-); `doc_value`: Optional[str] (optional, default=None, constraints=-); `parent_id`: Optional[str] (optional, default=None, constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `UploadJobResponse`
  - Response contracts: [`UploadJobResponse`](#model-uploadjobresponse)
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
    - `clean_name`
    - `UploadJob`
    - `db.add`
    - `_write_upload_to_tmp`
    - `db.commit`
    - `db.refresh`
    - `db.execute`
    - `HTTPException`
    - `settings.STORAGE_LOCAL_ROOT.rstrip`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - `400`: `Invalid parent document`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/uploads/contracts/documents`

- Controller: `backend/app/routers/uploads.py::queue_contract_document_upload`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `contract_id`: str (required, default=-, constraints=-); `doc_type`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default='draft', constraints=-); `document_id`: Optional[str] (optional, default=None, constraints=-); `file_kind`: str (required, default=-, constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `UploadJobResponse`
  - Response contracts: [`UploadJobResponse`](#model-uploadjobresponse)
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
    - `clean_name`
    - `is_local_storage`
    - `UploadJob`
    - `db.add`
    - `HTTPException`
    - `Contract.get_by_id`
    - `_write_upload_to_tmp`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `400`: `Invalid file_kind`; `Invalid status`; `Document does not belong to contract`; `Invalid doc_type`; body schema `{"detail": "..."}`
  - `404`: `Contract not found`; `Document not found`; body schema `{"detail": "..."}`
  - `500`: `Upload failed`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/uploads/document-registry/dispatches/{dispatch_id}/channels/{channel_id}`

- Controller: `backend/app/routers/uploads.py::queue_document_registry_channel_upload`
- Data Contract:
  - Path params: `dispatch_id`: str (required, default=-, constraints=-); `channel_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `UploadJobResponse`
  - Response contracts: [`UploadJobResponse`](#model-uploadjobresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `clean_name`
    - `UploadJob`
    - `db.add`
    - `db.execute`
    - `HTTPException`
    - `_write_upload_to_tmp`
    - `db.commit`
    - `db.refresh`
    - `_resolve_dispatch_path`
    - `select`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - `404`: `Dispatch not found`; `Channel not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/uploads/executor/results`

- Controller: `backend/app/routers/uploads.py::queue_executor_results_upload`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `stage_id`: str (required, default=-, constraints=-); `product_name`: str (required, default=-, constraints=-); `subcontractor_card_id`: str (required, default=-, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `comment`: Optional[str] (optional, default=None, constraints=-); `created_by`: Optional[str] (optional, default=None, constraints=-)
  - File params: `files`: List[UploadFile] (required, default=-, constraints=-)
  - Body: none
  - Response model: `List[UploadJobResponse]`
  - Response contracts: [`UploadJobResponse`](#model-uploadjobresponse)
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
    - `_build_root_paths`
    - `HTTPException`
    - `SubcontractorCard.get_by_id`
    - `db.execute`
    - `StageResult.create`
    - `clean_name`
    - `UploadJob`
    - `db.add`
    - `db.commit`
  - Side effects: DB write, DB read, File/storage operation
- Error Handling:
  - `400`: `Files are required`; body schema `{"detail": "..."}`
  - `404`: `Subcontractor card not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/uploads/executor/storage`

- Controller: `backend/app/routers/uploads.py::queue_executor_folder_upload`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `path`: str (required, default=-, constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `UploadJobResponse`
  - Response contracts: [`UploadJobResponse`](#model-uploadjobresponse)
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
    - `clean_name`
    - `UploadJob`
    - `db.add`
    - `HTTPException`
    - `_write_upload_to_tmp`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `400`: `Path is required`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/uploads/kp/versions`

- Controller: `backend/app/routers/uploads.py::queue_kp_version_upload`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `kp_id`: str (required, default=-, constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `UploadJobResponse`
  - Response contracts: [`UploadJobResponse`](#model-uploadjobresponse)
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
    - `clean_name`
    - `settings.STORAGE_LOCAL_ROOT.rstrip`
    - `KpVersion`
    - `db.add`
    - `UploadJob`
    - `db.get`
    - `HTTPException`
    - `_write_upload_to_tmp`
    - `LeadProduct.get_by_lead`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `404`: `KP not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/uploads/legal-work/events/{event_id}`

- Controller: `backend/app/routers/uploads.py::queue_legal_event_file_upload`
- Data Contract:
  - Path params: `event_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `UploadJobResponse`
  - Response contracts: [`UploadJobResponse`](#model-uploadjobresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `clean_name`
    - `(settings.STORAGE_LOCAL_ROOT or '').rstrip`
    - `UploadJob`
    - `db.add`
    - `LegalCaseEvent.get_by_id`
    - `HTTPException`
    - `LegalCase.get_by_id`
    - `_write_upload_to_tmp`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `404`: `Event not found`; `Case not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/uploads/outgoing-registry/{document_id}/attachments`

- Controller: `backend/app/routers/uploads.py::queue_outgoing_attachment_upload`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `UploadJobResponse`
  - Response contracts: [`UploadJobResponse`](#model-uploadjobresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `clean_name`
    - `UploadJob`
    - `db.add`
    - `OutgoingDocument.get_by_id`
    - `HTTPException`
    - `_write_upload_to_tmp`
    - `db.commit`
    - `db.refresh`
    - `settings.STORAGE_LOCAL_ROOT.rstrip`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `storage`

Source: `backend/app/routers/storage.py`

Prefix: `/api/v1`

Endpoints: `2`

#### `GET /api/v1/storage/download`

- Controller: `backend/app/routers/storage.py::download_storage_item`
- Data Contract:
  - Path params: none
  - Query params: `path`: str (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `unquote`
    - `mimetypes.guess_type`
    - `is_local_storage`
    - `quote`
    - `Response`
    - `storage_available`
    - `HTTPException`
    - `_local_path`
    - `tempfile.mkdtemp`
    - `os.path.join`
  - Side effects: Background task trigger, File/storage operation
- Error Handling:
  - `403`: `Invalid path`; body schema `{"detail": "..."}`
  - `404`: `File not found`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `502`: `Failed to download file`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/storage/usage`

- Controller: `backend/app/routers/storage.py::storage_usage`
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
    - `_storage_root_path`
    - `storage_available`
    - `HTTPException`
    - `is_local_storage`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Storage usage is only available for local storage`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; `Storage root not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `files_catalog`

Source: `backend/app/routers/files_catalog.py`

Prefix: `/api/v1`

Endpoints: `7`

#### `DELETE /api/v1/files-catalog`

- Controller: `backend/app/routers/files_catalog.py::delete_catalog_item`
- Data Contract:
  - Path params: none
  - Query params: `path`: str (required, default=-, constraints=-); `permanent`: bool (optional, default=False, constraints=-)
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
    - `storage_available`
    - `HTTPException`
    - `delete_path`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Cannot delete root folder`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/files-catalog/download`

- Controller: `backend/app/routers/files_catalog.py::download_catalog_item`
- Data Contract:
  - Path params: none
  - Query params: `path`: str (required, default=-, constraints=-); `redirect`: bool (optional, default=False, constraints=-)
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
    - `storage_available`
    - `HTTPException`
    - `get_download_href`
    - `RedirectResponse`
  - Side effects: File/storage operation
- Error Handling:
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/files-catalog/list`

- Controller: `backend/app/routers/files_catalog.py::list_catalog_items`
- Data Contract:
  - Path params: none
  - Query params: `path`: Optional[str] (optional, default=None, constraints=-); `limit`: int (optional, default=200, constraints=ge=1, le=1000); `search`: Optional[str] (optional, default=None, constraints=-)
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
    - `storage_available`
    - `HTTPException`
    - `search_items`
    - `list_items`
  - Side effects: File/storage operation
- Error Handling:
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/files-catalog/mkdir`

- Controller: `backend/app/routers/files_catalog.py::create_catalog_folder`
- Data Contract:
  - Path params: none
  - Query params: `payload`: CreateFolderPayload (required, default=-, constraints=-)
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
    - `clean_name`
    - `storage_available`
    - `HTTPException`
    - `ensure_path`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Folder name is required`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/files-catalog/move`

- Controller: `backend/app/routers/files_catalog.py::move_catalog_item`
- Data Contract:
  - Path params: none
  - Query params: `payload`: MovePayload (required, default=-, constraints=-)
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
    - `storage_available`
    - `HTTPException`
    - `move_path`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Cannot move root folder`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/files-catalog/rename`

- Controller: `backend/app/routers/files_catalog.py::rename_catalog_item`
- Data Contract:
  - Path params: none
  - Query params: `payload`: RenamePayload (required, default=-, constraints=-)
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
    - `clean_name`
    - `storage_available`
    - `HTTPException`
    - `move_path`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `New name is required`; `Cannot rename root folder`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/files-catalog/upload`

- Controller: `backend/app/routers/files_catalog.py::upload_catalog_files`
- Data Contract:
  - Path params: none
  - Query params: `path`: str (required, default=-, constraints=-)
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
    - `storage_available`
    - `HTTPException`
    - `ensure_path`
    - `is_local_storage`
    - `clean_name`
    - `local_path`
    - `(upload.filename or '').split('/')[-1].split`
    - `upload.close`
    - `_write_upload_to_tmp`
    - `upload_file_with_safe_extension`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Files are required`; body schema `{"detail": "..."}`
  - `413`: `File is too large`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


## Usage Examples (Domain)

### `GET /api/v1/document-registry`

```bash
curl -X GET http://localhost:8000/api/v1/document-registry -H "Authorization: Bearer $ACCESS_TOKEN" 
```

```json
{
  "doc_type": "string",
  "id": "string",
  "title": "string",
  "counterparty_id": "string",
  "created_at": "2026-01-01T00:00:00Z",
  "document_date": "2026-01-01",
  "number": "string",
  "our_company_id": "string"
}
```


### `GET /api/v1/outgoing-registry`

```bash
curl -X GET http://localhost:8000/api/v1/outgoing-registry -H "Authorization: Bearer $ACCESS_TOKEN" 
```

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "letter_date": "2026-01-01",
  "outgoing_number": "string",
  "outgoing_number_seq": 0,
  "recipient_company_id": "00000000-0000-0000-0000-000000000000",
  "subject": "string",
  "attachments_list": "string",
  "body": "string"
}
```


### `POST /api/v1/document-registry`

```bash
curl -X POST http://localhost:8000/api/v1/document-registry -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '{"doc_type": "string", "title": "string", "counterparty_id": "string", "document_date": "2026-01-01", "number": "string", "our_company_id": "string", "project_id": "string", "source_id": "string"}'
```

```json
{
  "doc_type": "string",
  "id": "string",
  "title": "string",
  "counterparty_id": "string",
  "created_at": "2026-01-01T00:00:00Z",
  "document_date": "2026-01-01",
  "number": "string",
  "our_company_id": "string"
}
```


### `POST /api/v1/outgoing-registry`

```bash
curl -X POST http://localhost:8000/api/v1/outgoing-registry -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '{}'
```

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "letter_date": "2026-01-01",
  "outgoing_number": "string",
  "outgoing_number_seq": 0,
  "recipient_company_id": "00000000-0000-0000-0000-000000000000",
  "subject": "string",
  "attachments_list": "string",
  "body": "string"
}
```


### `POST /api/v1/uploads/contracts/documents`

```bash
curl -X POST http://localhost:8000/api/v1/uploads/contracts/documents -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '{}'
```

```json
{
  "id": "string",
  "status": "string",
  "created_at": "2026-01-01T00:00:00Z",
  "created_by": "string",
  "entity_id": "string",
  "error_message": "string",
  "file_kind": "string",
  "file_name": "string"
}
```
