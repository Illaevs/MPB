# Identity & Access API

Сгенерировано из `docs/API.md` на 2026-02-15 03:22:39 (local time).

## Scope
- Домен: `auth`
- Описание: Аутентификация, пользователи, роли, компании и справочные интеграции.
- Routers: `6`
- Endpoints: `28`
- Список роутеров: `auth`, `users`, `roles`, `companies`, `banks`, `dadata`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `14`.

### Model `LoginRequest`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| email | EmailStr | yes | - | - |
| password | str | yes | - | - |


### Model `RefreshRequest`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| refresh_token | str | yes | - | - |


### Model `TokenResponse`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| access_token | str | yes | - | - |
| refresh_token | str | yes | - | - |
| token_type | str | no | 'bearer' | - |
| user | Optional[UserResponse] | no | None | - |
| permissions | Dict[str, Dict[str, bool]] | no | {} | - |
| is_superuser | bool | no | False | - |


### Model `UserCreate`

Source: `backend/app/schemas/user.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| email | EmailStr | yes | - | - |
| full_name | str | yes | - | - |
| role_id | Optional[Union[str, UUID]] | no | None | - |
| is_active | Optional[bool] | no | True | - |
| password | str | yes | - | - |


### Model `UserResponse`

Source: `backend/app/schemas/user.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| email | EmailStr | yes | - | - |
| full_name | str | yes | - | - |
| role_id | Optional[Union[str, UUID]] | no | None | - |
| is_active | Optional[bool] | no | True | - |
| id | Union[str, UUID] | yes | - | - |
| rating | Optional[float] | no | None | - |
| rating_count | Optional[int] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `UserUpdate`

Source: `backend/app/schemas/user.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| email | Optional[EmailStr] | no | None | - |
| full_name | Optional[str] | no | None | - |
| role_id | Optional[Union[str, UUID]] | no | None | - |
| is_active | Optional[bool] | no | None | - |
| password | Optional[str] | no | None | - |


### Model `RoleCreate`

Source: `backend/app/schemas/role.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| is_system | Optional[bool] | no | False | - |


### Model `RolePermissionResponse`

Source: `backend/app/schemas/role_permission.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| role_id | Optional[Union[str, UUID]] | no | None | - |
| section | str | yes | - | - |
| read_all | Optional[bool] | no | False | - |
| read_assigned | Optional[bool] | no | False | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `RolePermissionSet`

Source: `backend/app/schemas/role_permission.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| section | str | yes | - | - |
| read_all | Optional[bool] | no | False | - |
| read_assigned | Optional[bool] | no | False | - |


### Model `RoleResponse`

Source: `backend/app/schemas/role.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| is_system | Optional[bool] | no | False | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `RoleUpdate`

Source: `backend/app/schemas/role.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | Optional[str] | no | None | - |
| description | Optional[str] | no | None | - |
| is_system | Optional[bool] | no | None | - |


### Model `CompanyCreate`

Source: `backend/app/schemas/company.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| inn | str | yes | - | - |
| type | Optional[str] | no | 'customer' | - |
| name | str | yes | - | - |
| short_name | Optional[str] | no | None | - |
| full_name | Optional[str] | no | None | - |
| contact_person | Optional[str] | no | None | - |
| phone | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| phones | Optional[List[str]] | no | [] | - |
| emails | Optional[List[str]] | no | [] | - |
| bank_accounts | Optional[List[BankAccount]] | no | [] | - |
| address | Optional[str] | no | None | - |
| rating_speed | Optional[float] | no | 0.0 | - |
| rating_quality | Optional[float] | no | 0.0 | - |


### Model `CompanyResponse`

Source: `backend/app/schemas/company.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| inn | str | yes | - | - |
| type | Optional[str] | no | 'customer' | - |
| name | str | yes | - | - |
| short_name | Optional[str] | no | None | - |
| full_name | Optional[str] | no | None | - |
| contact_person | Optional[str] | no | None | - |
| phone | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| phones | Optional[List[str]] | no | [] | - |
| emails | Optional[List[str]] | no | [] | - |
| bank_accounts | Optional[List[BankAccount]] | no | [] | - |
| address | Optional[str] | no | None | - |
| rating_speed | Optional[float] | no | 0.0 | - |
| rating_quality | Optional[float] | no | 0.0 | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `CompanyUpdate`

Source: `backend/app/schemas/company.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| inn | str | yes | - | - |
| type | Optional[str] | no | 'customer' | - |
| name | str | yes | - | - |
| short_name | Optional[str] | no | None | - |
| full_name | Optional[str] | no | None | - |
| contact_person | Optional[str] | no | None | - |
| phone | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| phones | Optional[List[str]] | no | [] | - |
| emails | Optional[List[str]] | no | [] | - |
| bank_accounts | Optional[List[BankAccount]] | no | [] | - |
| address | Optional[str] | no | None | - |
| rating_speed | Optional[float] | no | 0.0 | - |
| rating_quality | Optional[float] | no | 0.0 | - |


## Routers / Controllers Reference

### Router `auth`

Source: `backend/app/routers/auth.py`

Prefix: `/api/v1/auth`

Endpoints: `3`

#### `POST /api/v1/auth/impersonate/{user_id}`

- Controller: `backend/app/routers/auth.py::impersonate_user`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `TokenResponse`
  - Response contracts: [`TokenResponse`](#model-tokenresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware); route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `User.get_by_id`
    - `EventLog.create`
    - `Role.get_by_id`
  - Side effects: DB write, Audit/Event logging
- Error Handling:
  - `403`: `Not enough permissions`; `Target user inactive`; body schema `{"detail": "..."}`
  - `404`: `Target user not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `POST /api/v1/auth/login`

- Controller: `backend/app/routers/auth.py::login`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LoginRequest`](#model-loginrequest)
  - Response model: `TokenResponse`
  - Response contracts: [`TokenResponse`](#model-tokenresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: Public
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `User.get_by_email`
    - `HTTPException`
    - `verify_password`
    - `Role.get_by_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `401`: `Incorrect email or password`; body schema `{"detail": "..."}`
  - `403`: `User inactive`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `POST /api/v1/auth/refresh`

- Controller: `backend/app/routers/auth.py::refresh_tokens`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`RefreshRequest`](#model-refreshrequest)
  - Response model: `TokenResponse`
  - Response contracts: [`TokenResponse`](#model-tokenresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: Public
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `decode_token`
    - `is_token_type`
    - `HTTPException`
    - `User.get_by_id`
    - `Role.get_by_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `401`: `Invalid token type`; `Invalid token payload`; `User inactive or not found`; `Invalid refresh token`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

### Router `users`

Source: `backend/app/routers/users.py`

Prefix: `/api/v1/users`

Endpoints: `7`

#### `GET /api/v1/users`

- Controller: `backend/app/routers/users.py::list_users`
- Data Contract:
  - Path params: none
  - Query params: `role_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[UserResponse]`
  - Response contracts: [`UserResponse`](#model-userresponse)
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
    - `User.full_name.asc`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `POST /api/v1/users`

- Controller: `backend/app/routers/users.py::create_user`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`UserCreate`](#model-usercreate)
  - Response model: `UserResponse`
  - Response contracts: [`UserResponse`](#model-userresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write("users"))`
  - Write policy: superuser OR role with read_all=true in section `users`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `hash_password`
    - `User.get_by_email`
    - `HTTPException`
    - `User.create`
    - `Role.get_by_id`
  - Side effects: DB write
- Error Handling:
  - `403`: `Write access denied for section: users`; body schema `{"detail": "..."}`
  - `400`: `Email already exists`; body schema `{"detail": "..."}`
  - `404`: `Role not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `GET /api/v1/users/company-links`

- Controller: `backend/app/routers/users.py::list_company_links`
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
    - `get_section_permissions`
    - `db.execute`
    - `select`
    - `Company.id.in_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `DELETE /api/v1/users/{user_id}`

- Controller: `backend/app/routers/users.py::delete_user`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
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
    - `_: Depends(require_section_write("users"))`
  - Write policy: superuser OR role with read_all=true in section `users`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `User.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `403`: `Write access denied for section: users`; body schema `{"detail": "..."}`
  - `404`: `User not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `PUT /api/v1/users/{user_id}`

- Controller: `backend/app/routers/users.py::update_user`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`UserUpdate`](#model-userupdate)
  - Response model: `UserResponse`
  - Response contracts: [`UserResponse`](#model-userresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write("users"))`
  - Write policy: superuser OR role with read_all=true in section `users`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `hash_password`
    - `User.update`
    - `HTTPException`
    - `Role.get_by_id`
  - Side effects: DB write
- Error Handling:
  - `403`: `Write access denied for section: users`; body schema `{"detail": "..."}`
  - `404`: `User not found`; `Role not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `POST /api/v1/users/{user_id}/company-links`

- Controller: `backend/app/routers/users.py::add_company_link`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: dict (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write("users"))`
  - Write policy: superuser OR role with read_all=true in section `users`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `CompanyUserLink`
    - `db.add`
    - `HTTPException`
    - `User.get_by_id`
    - `Company.get_by_id`
    - `db.execute`
    - `db.commit`
    - `db.refresh`
    - `CompanyUserLink.company_id.in_`
    - `select`
    - `Company.id.in_`
  - Side effects: DB write, DB read
- Error Handling:
  - `403`: `Write access denied for section: users`; body schema `{"detail": "..."}`
  - `400`: `Invalid link_type`; `company_id is required`; body schema `{"detail": "..."}`
  - `404`: `User not found`; `Company not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `DELETE /api/v1/users/{user_id}/company-links/{link_id}`

- Controller: `backend/app/routers/users.py::delete_company_link`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-); `link_id`: str (required, default=-, constraints=-)
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
    - `_: Depends(require_section_write("users"))`
  - Write policy: superuser OR role with read_all=true in section `users`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `User.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `select`
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
  - `403`: `Write access denied for section: users`; body schema `{"detail": "..."}`
  - `404`: `User not found`; `Link not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

### Router `roles`

Source: `backend/app/routers/roles.py`

Prefix: `/api/v1/roles`

Endpoints: `7`

#### `GET /api/v1/roles`

- Controller: `backend/app/routers/roles.py::list_roles`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[RoleResponse]`
  - Response contracts: [`RoleResponse`](#model-roleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Role.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `POST /api/v1/roles`

- Controller: `backend/app/routers/roles.py::create_role`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`RoleCreate`](#model-rolecreate)
  - Response model: `RoleResponse`
  - Response contracts: [`RoleResponse`](#model-roleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write("roles"))`
  - Write policy: superuser OR role with read_all=true in section `roles`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Role.get_by_name`
    - `HTTPException`
    - `Role.create`
  - Side effects: DB write
- Error Handling:
  - `403`: `Write access denied for section: roles`; body schema `{"detail": "..."}`
  - `400`: `Role name already exists`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `GET /api/v1/roles/sections`

- Controller: `backend/app/routers/roles.py::list_sections`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[str]`
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security: none at function level
- Logic Flow:
  - Internal calls: none (or not statically detected)
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `DELETE /api/v1/roles/{role_id}`

- Controller: `backend/app/routers/roles.py::delete_role`
- Data Contract:
  - Path params: `role_id`: str (required, default=-, constraints=-)
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
    - `_: Depends(require_section_write("roles"))`
  - Write policy: superuser OR role with read_all=true in section `roles`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Role.get_by_id`
    - `HTTPException`
    - `Role.delete`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `403`: `Write access denied for section: roles`; body schema `{"detail": "..."}`
  - `400`: `System role cannot be deleted`; body schema `{"detail": "..."}`
  - `404`: `Role not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `PUT /api/v1/roles/{role_id}`

- Controller: `backend/app/routers/roles.py::update_role`
- Data Contract:
  - Path params: `role_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`RoleUpdate`](#model-roleupdate)
  - Response model: `RoleResponse`
  - Response contracts: [`RoleResponse`](#model-roleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write("roles"))`
  - Write policy: superuser OR role with read_all=true in section `roles`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Role.update`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `403`: `Write access denied for section: roles`; body schema `{"detail": "..."}`
  - `404`: `Role not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `GET /api/v1/roles/{role_id}/permissions`

- Controller: `backend/app/routers/roles.py::get_role_permissions`
- Data Contract:
  - Path params: `role_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[RolePermissionResponse]`
  - Response contracts: [`RolePermissionResponse`](#model-rolepermissionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Role.get_by_id`
    - `HTTPException`
    - `RolePermission.get_by_role`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Role not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `PUT /api/v1/roles/{role_id}/permissions`

- Controller: `backend/app/routers/roles.py::set_role_permissions`
- Data Contract:
  - Path params: `role_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`RolePermissionSet`](#model-rolepermissionset)
  - Response model: `List[RolePermissionResponse]`
  - Response contracts: [`RolePermissionResponse`](#model-rolepermissionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write("roles"))`
  - Write policy: superuser OR role with read_all=true in section `roles`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Role.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `RolePermission`
    - `db.add`
    - `delete`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `403`: `Write access denied for section: roles`; body schema `{"detail": "..."}`
  - `400`: `f'Unknown section: {item.section}`; body schema `{"detail": "..."}`
  - `404`: `Role not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

### Router `companies`

Source: `backend/app/routers/companies.py`

Prefix: `/api/v1/companies`

Endpoints: `9`

#### `GET /api/v1/companies`

- Controller: `backend/app/routers/companies.py::get_companies`
- Summary: Получить список всех компаний
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `company_type`: Optional[str] (optional, default=None, constraints=-); `sort_by`: Optional[str] (optional, default='name', constraints=-); `sort_dir`: Optional[str] (optional, default='asc', constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[CompanyResponse]`
  - Response contracts: [`CompanyResponse`](#model-companyresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Company.get_all`
    - `get_section_permissions`
    - `allowed_deal_ids`
    - `db.execute`
    - `Deal.id.in_`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `POST /api/v1/companies`

- Controller: `backend/app/routers/companies.py::create_company`
- Summary: Создать новую компанию
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`CompanyCreate`](#model-companycreate)
  - Response model: `CompanyResponse`
  - Response contracts: [`CompanyResponse`](#model-companyresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write("companies"))`
  - Write policy: superuser OR role with read_all=true in section `companies`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Company.create`
  - Side effects: DB write
- Error Handling:
  - `403`: `Write access denied for section: companies`; body schema `{"detail": "..."}`
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `GET /api/v1/companies/count`

- Controller: `backend/app/routers/companies.py::get_companies_count`
- Summary: Получить количество компаний с фильтрами
- Data Contract:
  - Path params: none
  - Query params: `search`: Optional[str] (optional, default=None, constraints=-); `company_type`: Optional[str] (optional, default=None, constraints=-)
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
    - `Company.get_count`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `POST /api/v1/companies/refresh-all`

- Controller: `backend/app/routers/companies.py::refresh_all_companies`
- Summary: Обновить данные всех компаний через DaData по ИНН.
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
    - `_: Depends(require_section_write("companies"))`
  - Write policy: superuser OR role with read_all=true in section `companies`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `db.execute`
    - `httpx.AsyncClient`
    - `db.commit`
    - `select`
    - `asyncio.sleep`
    - `logger.warning`
  - Side effects: DB write, DB read
- Error Handling:
  - `403`: `Write access denied for section: companies`; body schema `{"detail": "..."}`
  - `500`: `Dadata token is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `DELETE /api/v1/companies/{company_id}`

- Controller: `backend/app/routers/companies.py::delete_company`
- Summary: Удалить компанию
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
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
    - `_: Depends(require_section_write("companies"))`
  - Write policy: superuser OR role with read_all=true in section `companies`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Company.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `403`: `Write access denied for section: companies`; body schema `{"detail": "..."}`
  - `404`: `Компания не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `GET /api/v1/companies/{company_id}`

- Controller: `backend/app/routers/companies.py::get_company`
- Summary: Получить компанию по ID
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `CompanyResponse`
  - Response contracts: [`CompanyResponse`](#model-companyresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Company.get_by_id`
    - `HTTPException`
    - `get_section_permissions`
    - `allowed_deal_ids`
    - `db.execute`
    - `Deal.id.in_`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `Компания не найдена`; `РљРѕРјРїР°РЅРёСЏ РЅРµ РЅР°Р№РґРµРЅР°`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `PUT /api/v1/companies/{company_id}`

- Controller: `backend/app/routers/companies.py::update_company`
- Summary: Обновить компанию
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`CompanyUpdate`](#model-companyupdate)
  - Response model: `CompanyResponse`
  - Response contracts: [`CompanyResponse`](#model-companyresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write("companies"))`
  - Write policy: superuser OR role with read_all=true in section `companies`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Company.update`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `403`: `Write access denied for section: companies`; body schema `{"detail": "..."}`
  - `404`: `Компания не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `GET /api/v1/companies/{company_id}/users`

- Controller: `backend/app/routers/companies.py::get_company_users`
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
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
    - `Company.get_by_id`
    - `HTTPException`
    - `CompanyUserLink.get_by_company`
    - `db.execute`
    - `User.id.in_`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `Company not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`
#### `PUT /api/v1/companies/{company_id}/users`

- Controller: `backend/app/routers/companies.py::set_company_users`
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: dict (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write("companies"))`
  - Write policy: superuser OR role with read_all=true in section `companies`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Company.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.add`
    - `db.commit`
    - `CompanyUserLink`
    - `User.id.in_`
    - `delete`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `403`: `Write access denied for section: companies`; body schema `{"detail": "..."}`
  - `400`: `Invalid user id in payload`; body schema `{"detail": "..."}`
  - `404`: `Company not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

### Router `banks`

Source: `backend/app/routers/banks.py`

Prefix: `/api/v1`

Endpoints: `1`

#### `POST /api/v1/banks/lookup`

- Controller: `backend/app/routers/banks.py::lookup_bank`
- Data Contract:
  - Path params: none
  - Query params: `request`: BankLookupRequest (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security: none at function level
- Logic Flow:
  - Internal calls:
    - `HTTPException`
    - `httpx.AsyncClient`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Query is required`; body schema `{"detail": "..."}`
  - `500`: `Dadata token is not configured`; body schema `{"detail": "..."}`
  - `502`: `Failed to lookup bank data`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

### Router `dadata`

Source: `backend/app/routers/dadata.py`

Prefix: `/api/v1`

Endpoints: `1`

#### `POST /api/v1/dadata/party`

- Controller: `backend/app/routers/dadata.py::lookup_party`
- Data Contract:
  - Path params: none
  - Query params: `request`: PartyLookupRequest (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security: none at function level
- Logic Flow:
  - Internal calls:
    - `HTTPException`
    - `httpx.AsyncClient`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Query is required`; body schema `{"detail": "..."}`
  - `500`: `Dadata token is not configured`; body schema `{"detail": "..."}`
  - `502`: `Failed to lookup party data`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

## Usage Examples (Domain)

### `POST /api/v1/auth/login`

```bash
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email": "user@example.com", "password": "string"}'
```

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "is_superuser": false,
  "permissions": {},
  "token_type": "string",
  "user": "string"
}
```


### `POST /api/v1/auth/refresh`

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh -H "Content-Type: application/json" -d '{"refresh_token": "string"}'
```

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "is_superuser": false,
  "permissions": {},
  "token_type": "string",
  "user": "string"
}
```
