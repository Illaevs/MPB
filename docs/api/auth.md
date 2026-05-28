# Identity & Access API

Сгенерировано из `docs/API.md` на 2026-05-29 01:30:41 (local time).

## Scope
- Домен: `auth`
- Описание: Аутентификация, пользователи, роли, компании, оргструктура и справочные интеграции.
- Routers: `7`
- Endpoints: `63`
- Список роутеров: `auth`, `users`, `roles`, `companies`, `banks`, `dadata`, `org_structure`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `30`.

### Model `LoginRequest`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| email | EmailStr | yes | - | - |
| password | str | yes | - | - |


### Model `LoginResponse`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| access_token | Optional[str] | no | None | - |
| refresh_token | Optional[str] | no | None | - |
| token_type | str | no | 'bearer' | - |
| user | Optional[UserResponse] | no | None | - |
| permissions | Dict[str, Dict[str, bool]] | no | {} | - |
| is_superuser | bool | no | False | - |
| requires_2fa | bool | no | False | - |
| requires_2fa_setup | bool | no | False | - |
| challenge_token | Optional[str] | no | None | - |


### Model `RefreshRequest`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| refresh_token | Optional[str] | no | None | - |


### Model `SessionResponse`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| user | Optional[UserResponse] | no | None | - |
| permissions | Dict[str, Dict[str, bool]] | no | {} | - |
| is_superuser | bool | no | False | - |


### Model `TokenResponse`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| user | Optional[UserResponse] | no | None | - |
| permissions | Dict[str, Dict[str, bool]] | no | {} | - |
| is_superuser | bool | no | False | - |
| access_token | Optional[str] | no | None | - |
| refresh_token | Optional[str] | no | None | - |
| token_type | str | no | 'bearer' | - |


### Model `TwoFactorBackupCodesResponse`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| enabled | bool | no | False | - |
| enabled_at | Optional[datetime] | no | None | - |
| backup_codes_remaining | int | no | 0 | - |
| backup_codes | List[str] | no | [] | - |


### Model `TwoFactorDisableRequest`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| password | str | yes | - | - |


### Model `TwoFactorRegenerateBackupCodesRequest`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| code | str | yes | - | - |


### Model `TwoFactorSetupConfirmRequest`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| secret | str | yes | - | - |
| code | str | yes | - | - |


### Model `TwoFactorSetupStartResponse`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| secret | str | yes | - | - |
| otpauth_url | str | yes | - | - |
| issuer | str | yes | - | - |
| email | EmailStr | yes | - | - |


### Model `TwoFactorStatusResponse`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| enabled | bool | no | False | - |
| enabled_at | Optional[datetime] | no | None | - |
| backup_codes_remaining | int | no | 0 | - |


### Model `TwoFactorVerifyRequest`

Source: `backend/app/schemas/auth.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| challenge_token | str | yes | - | - |
| code | str | yes | - | - |


### Model `CompanyLinkCreate`

Source: `backend/app/schemas/user.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| company_id | Union[str, UUID] | yes | - | - |
| link_type | str | yes | - | - |


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
| role_name | Optional[str] | no | None | - |
| avatar_url | Optional[str] | no | None | - |
| wallpaper_url | Optional[str] | no | None | - |
| two_factor_enabled | Optional[bool] | no | False | - |
| two_factor_enabled_at | Optional[datetime] | no | None | - |
| rating | Optional[float] | no | None | - |
| rating_count | Optional[int] | no | None | - |
| ui_preferences | Optional[Dict[str, Any]] | no | None | - |
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
| subtree_scope | Optional[bool] | no | False | - |
| track_work_time | Optional[bool] | no | False | - |
| idle_timeout_minutes | Optional[int] | no | None | - |


### Model `RolePermissionResponse`

Source: `backend/app/schemas/role_permission.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| role_id | Optional[Union[str, UUID]] | no | None | - |
| section | str | yes | - | - |
| read_all | Optional[bool] | no | False | - |
| read_assigned | Optional[bool] | no | False | - |
| edit_all | Optional[bool] | no | False | - |
| edit_assigned | Optional[bool] | no | False | - |
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
| edit_all | Optional[bool] | no | False | - |
| edit_assigned | Optional[bool] | no | False | - |


### Model `RoleResponse`

Source: `backend/app/schemas/role.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| subtree_scope | Optional[bool] | no | False | - |
| track_work_time | Optional[bool] | no | False | - |
| idle_timeout_minutes | Optional[int] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| is_system | bool | no | False | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `RoleUpdate`

Source: `backend/app/schemas/role.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | Optional[str] | no | None | - |
| description | Optional[str] | no | None | - |
| subtree_scope | Optional[bool] | no | None | - |
| track_work_time | Optional[bool] | no | None | - |
| idle_timeout_minutes | Optional[int] | no | None | - |


### Model `CompanyCreate`

Source: `backend/app/schemas/company.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| inn | str | yes | - | - |
| type | Optional[str] | no | 'customer' | - |
| name | str | yes | - | - |
| short_name | Optional[str] | no | None | - |
| full_name | Optional[str] | no | None | - |
| kpp | Optional[str] | no | None | - |
| contact_person | Optional[str] | no | None | - |
| phone | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| phones | Optional[List[str]] | no | [] | - |
| emails | Optional[List[str]] | no | [] | - |
| contacts | Optional[List[ContactPerson]] | no | [] | - |
| bank_accounts | Optional[List[BankAccount]] | no | [] | - |
| address | Optional[str] | no | None | - |
| rating_speed | Optional[float] | no | 0.0 | - |
| rating_quality | Optional[float] | no | 0.0 | - |
| work_directions | Optional[List[Union[str, int]]] | no | [] | - |
| rating | Optional[float] | no | 0.0 | - |
| note | Optional[str] | no | None | - |
| is_default | Optional[bool] | no | False | - |


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


### Model `CompanyResponse`

Source: `backend/app/schemas/company.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| inn | str | yes | - | - |
| type | Optional[str] | no | 'customer' | - |
| name | str | yes | - | - |
| short_name | Optional[str] | no | None | - |
| full_name | Optional[str] | no | None | - |
| kpp | Optional[str] | no | None | - |
| contact_person | Optional[str] | no | None | - |
| phone | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| phones | Optional[List[str]] | no | [] | - |
| emails | Optional[List[str]] | no | [] | - |
| contacts | Optional[List[ContactPerson]] | no | [] | - |
| bank_accounts | Optional[List[BankAccount]] | no | [] | - |
| address | Optional[str] | no | None | - |
| rating_speed | Optional[float] | no | 0.0 | - |
| rating_quality | Optional[float] | no | 0.0 | - |
| work_directions | Optional[List[Union[str, int]]] | no | [] | - |
| rating | Optional[float] | no | 0.0 | - |
| note | Optional[str] | no | None | - |
| is_default | Optional[bool] | no | False | - |
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
| kpp | Optional[str] | no | None | - |
| contact_person | Optional[str] | no | None | - |
| phone | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| phones | Optional[List[str]] | no | [] | - |
| emails | Optional[List[str]] | no | [] | - |
| contacts | Optional[List[ContactPerson]] | no | [] | - |
| bank_accounts | Optional[List[BankAccount]] | no | [] | - |
| address | Optional[str] | no | None | - |
| rating_speed | Optional[float] | no | 0.0 | - |
| rating_quality | Optional[float] | no | 0.0 | - |
| work_directions | Optional[List[Union[str, int]]] | no | [] | - |
| rating | Optional[float] | no | 0.0 | - |
| note | Optional[str] | no | None | - |
| is_default | Optional[bool] | no | False | - |


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


## Routers / Controllers Reference

### Router `auth`

Source: `backend/app/routers/auth.py`

Prefix: `/api/v1/auth`

Endpoints: `14`

#### `POST /api/v1/auth/2fa/disable`

- Controller: `backend/app/routers/auth.py::disable_two_factor`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TwoFactorDisableRequest`](#model-twofactordisablerequest)
  - Response model: `TwoFactorStatusResponse`
  - Response contracts: [`TwoFactorStatusResponse`](#model-twofactorstatusresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `User.get_by_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `403`: `Отключение 2FA запрещено политикой безопасности.`; body schema `{"detail": "..."}`
  - `404`: `Пользователь не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/auth/2fa/regenerate-backup-codes`

- Controller: `backend/app/routers/auth.py::regenerate_backup_codes`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TwoFactorRegenerateBackupCodesRequest`](#model-twofactorregeneratebackupcodesrequest)
  - Response model: `TwoFactorBackupCodesResponse`
  - Response contracts: [`TwoFactorBackupCodesResponse`](#model-twofactorbackupcodesresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `decrypt_totp_secret`
    - `generate_backup_codes`
    - `hash_backup_codes`
    - `TwoFactorBackupCodesResponse`
    - `User.get_by_id`
    - `HTTPException`
    - `verify_totp_code`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `2FA не настроена.`; `Секрет 2FA поврежден или отсутствует.`; body schema `{"detail": "..."}`
  - `401`: `Неверный код 2FA.`; body schema `{"detail": "..."}`
  - `404`: `Пользователь не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/auth/2fa/setup/confirm`

- Controller: `backend/app/routers/auth.py::confirm_two_factor_setup`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TwoFactorSetupConfirmRequest`](#model-twofactorsetupconfirmrequest)
  - Response model: `TwoFactorBackupCodesResponse`
  - Response contracts: [`TwoFactorBackupCodesResponse`](#model-twofactorbackupcodesresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `generate_backup_codes`
    - `encrypt_totp_secret`
    - `hash_backup_codes`
    - `TwoFactorBackupCodesResponse`
    - `User.get_by_id`
    - `HTTPException`
    - `verify_totp_code`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `2FA уже настроена.`; `Неверный код подтверждения.`; body schema `{"detail": "..."}`
  - `404`: `Пользователь не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/auth/2fa/setup/start`

- Controller: `backend/app/routers/auth.py::start_two_factor_setup`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `TwoFactorSetupStartResponse`
  - Response contracts: [`TwoFactorSetupStartResponse`](#model-twofactorsetupstartresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `generate_totp_secret`
    - `TwoFactorSetupStartResponse`
    - `User.get_by_id`
    - `HTTPException`
    - `build_otpauth_uri`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `2FA уже настроена.`; body schema `{"detail": "..."}`
  - `404`: `Пользователь не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/auth/2fa/status`

- Controller: `backend/app/routers/auth.py::two_factor_status`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `TwoFactorStatusResponse`
  - Response contracts: [`TwoFactorStatusResponse`](#model-twofactorstatusresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `User.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Пользователь не найден.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/auth/impersonate/{user_id}`

- Controller: `backend/app/routers/auth.py::impersonate_user`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `SessionResponse`
  - Response contracts: [`SessionResponse`](#model-sessionresponse)
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
  - `403`: `Недостаточно прав для выполнения действия.`; `Имперсонация доступна только после подтвержденной 2FA.`; `Пользователь для переключения отключен.`; `Нельзя переключиться на пользователя без настроенной 2FA.`; body schema `{"detail": "..."}`
  - `404`: `Пользователь для переключения не найден.`; body schema `{"detail": "..."}`
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
  - Response model: `LoginResponse`
  - Response contracts: [`LoginResponse`](#model-loginresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: Public
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `_login_rate_key`
    - `LoginResponse`
    - `_check_login_rate_limit_redis`
    - `_load_login_user`
    - `_ensure_login_two_factor_state`
    - `create_two_factor_challenge_token`
    - `_emit_login_event`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/auth/logout`

- Controller: `backend/app/routers/auth.py::logout`
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
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `decode_token`
    - `emit_event_safe`
    - `client_ip`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/auth/mobile/login`

- Controller: `backend/app/routers/auth.py::mobile_login`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LoginRequest`](#model-loginrequest)
  - Response model: `LoginResponse`
  - Response contracts: [`LoginResponse`](#model-loginresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: Public
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `_login_rate_key`
    - `_login_response_with_tokens`
    - `_check_login_rate_limit_redis`
    - `_load_login_user`
    - `_ensure_login_two_factor_state`
    - `create_two_factor_challenge_token`
    - `LoginResponse`
    - `_emit_login_event`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/auth/mobile/refresh`

- Controller: `backend/app/routers/auth.py::mobile_refresh_tokens`
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
    - `HTTPException`
    - `decode_token`
    - `is_token_type`
    - `User.get_by_id`
    - `Role.get_by_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `401`: `Refresh token РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚.`; `РќРµРґРµР№СЃС‚РІРёС‚РµР»СЊРЅС‹Р№ С‚РёРї С‚РѕРєРµРЅР°.`; `РќРµРєРѕСЂСЂРµРєС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ С‚РѕРєРµРЅР°.`; `РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РЅР°Р№РґРµРЅ РёР»Рё РѕС‚РєР»СЋС‡РµРЅ.`; `РЎСЂРѕРє РґРµР№СЃС‚РІРёСЏ refresh token РёСЃС‚РµРє. Р’РѕР№РґРёС‚Рµ Р·Р°РЅРѕРІРѕ.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/auth/mobile/verify-2fa`

- Controller: `backend/app/routers/auth.py::mobile_verify_two_factor`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TwoFactorVerifyRequest`](#model-twofactorverifyrequest)
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
    - `decrypt_totp_secret`
    - `verify_totp_code`
    - `decode_token`
    - `is_token_type`
    - `HTTPException`
    - `User.get_by_id`
    - `verify_and_consume_backup_code`
    - `_emit_login_event`
    - `Role.get_by_id`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `Р”Р»СЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РЅРµ РЅР°СЃС‚СЂРѕРµРЅР° РґРІСѓС…С„Р°РєС‚РѕСЂРЅР°СЏ Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ.`; `РЎРµРєСЂРµС‚ 2FA РїРѕРІСЂРµР¶РґРµРЅ РёР»Рё РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚.`; body schema `{"detail": "..."}`
  - `401`: `РќРµРґРµР№СЃС‚РІРёС‚РµР»СЊРЅС‹Р№ С‚РёРї С‚РѕРєРµРЅР°.`; `РќРµРґРµР№СЃС‚РІРёС‚РµР»СЊРЅС‹Р№ С‚РѕРєРµРЅ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ 2FA.`; `РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РЅР°Р№РґРµРЅ РёР»Рё РѕС‚РєР»СЋС‡РµРЅ.`; `РќРµРІРµСЂРЅС‹Р№ РєРѕРґ 2FA РёР»Рё СЂРµР·РµСЂРІРЅС‹Р№ РєРѕРґ.`; `РЎСЂРѕРє РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ 2FA РёСЃС‚РµРє. Р’РѕР№РґРёС‚Рµ Р·Р°РЅРѕРІРѕ.`; body schema `{"detail": "..."}`
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
  - Response model: `SessionResponse`
  - Response contracts: [`SessionResponse`](#model-sessionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: Public
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `decode_token`
    - `is_token_type`
    - `User.get_by_id`
    - `Role.get_by_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `401`: `Refresh token отсутствует.`; `Недействительный тип токена.`; `Некорректные данные токена.`; `Пользователь не найден или отключен.`; `Срок действия refresh token истек. Войдите заново.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/auth/session`

- Controller: `backend/app/routers/auth.py::get_session`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `SessionResponse`
  - Response contracts: [`SessionResponse`](#model-sessionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `User.get_by_id`
    - `HTTPException`
    - `Role.get_by_id`
    - `secrets.token_urlsafe`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `401`: `Пользователь не найден или отключен.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/auth/verify-2fa`

- Controller: `backend/app/routers/auth.py::verify_two_factor`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TwoFactorVerifyRequest`](#model-twofactorverifyrequest)
  - Response model: `SessionResponse`
  - Response contracts: [`SessionResponse`](#model-sessionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: Public
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `decrypt_totp_secret`
    - `verify_totp_code`
    - `decode_token`
    - `is_token_type`
    - `HTTPException`
    - `User.get_by_id`
    - `verify_and_consume_backup_code`
    - `_emit_login_event`
    - `Role.get_by_id`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `Для пользователя не настроена двухфакторная аутентификация.`; `Секрет 2FA поврежден или отсутствует.`; body schema `{"detail": "..."}`
  - `401`: `Недействительный тип токена.`; `Недействительный токен подтверждения 2FA.`; `Пользователь не найден или отключен.`; `Неверный код 2FA или резервный код.`; `Срок подтверждения 2FA истек. Войдите заново.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `users`

Source: `backend/app/routers/users.py`

Prefix: `/api/v1/users`

Endpoints: `17`

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
  - Access mode: JWT (AuthMiddleware); route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write('users'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `User.get_by_email`
    - `HTTPException`
    - `run_in_threadpool`
    - `User.create`
    - `emit_event_safe`
    - `Role.get_by_id`
  - Side effects: DB write
- Error Handling:
  - `400`: `Email already exists`; body schema `{"detail": "..."}`
  - `403`: `Назначение системной роли разрешено только системному суперпользователю.`; body schema `{"detail": "..."}`
  - `404`: `Role not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/users/avatar-file/{filename}`

- Controller: `backend/app/routers/users.py::get_avatar_file_v2`
- Data Contract:
  - Path params: `filename`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `_user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FileResponse`
    - `HTTPException`
    - `avatars_root`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `???????????????????????? ?????? ??????????`; `???????????????????????? ????????`; body schema `{"detail": "..."}`
  - `404`: `???????????? ???? ????????????`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/users/avatar-user/{user_id}`

- Controller: `backend/app/routers/users.py::get_avatar_by_user`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
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
    - `_user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FileResponse`
    - `User.get_by_id`
    - `HTTPException`
  - Side effects: File/storage operation
- Error Handling:
  - `404`: `Аватар не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/users/avatar/{filename}`

- Controller: `backend/app/routers/users.py::get_avatar_file`
- Data Contract:
  - Path params: `filename`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `_user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FileResponse`
    - `HTTPException`
    - `avatars_root`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `???????????????????????? ?????? ??????????`; `???????????????????????? ????????`; body schema `{"detail": "..."}`
  - `404`: `???????????? ???? ????????????`; body schema `{"detail": "..."}`
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

#### `POST /api/v1/users/me/avatar`

- Controller: `backend/app/routers/users.py::upload_my_avatar`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `UserResponse`
  - Response contracts: [`UserResponse`](#model-userresponse)
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
    - `ensure_user_avatar_schema`
    - `HTTPException`
    - `User.get_by_id`
    - `avatars_root`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `400`: `Допустимы только JPG, PNG, WEBP или GIF`; `Файл пустой`; `Максимальный размер аватара 5 МБ`; `Файл не является корректным изображением`; body schema `{"detail": "..."}`
  - `404`: `User not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/users/me/ui-preferences`

- Controller: `backend/app/routers/users.py::get_my_ui_preferences`
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
    - `User.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `User not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/users/me/ui-preferences`

- Controller: `backend/app/routers/users.py::update_my_ui_preferences`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: `payload`: Dict[str, Any]
  - Response model: `UserResponse`
  - Response contracts: [`UserResponse`](#model-userresponse)
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
    - `User.get_by_id`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `Ожидается объект настроек`; `Настройки слишком большие`; body schema `{"detail": "..."}`
  - `404`: `User not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/users/me/wallpaper`

- Controller: `backend/app/routers/users.py::clear_my_wallpaper`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `UserResponse`
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
    - `ensure_user_avatar_schema`
    - `User.get_by_id`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `404`: `User not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/users/me/wallpaper`

- Controller: `backend/app/routers/users.py::upload_my_wallpaper`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `UserResponse`
  - Response contracts: [`UserResponse`](#model-userresponse)
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
    - `ensure_user_avatar_schema`
    - `HTTPException`
    - `User.get_by_id`
    - `wallpapers_root`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `400`: `Допустимы только JPG, PNG или GIF`; `Файл пустой`; `Максимальный размер обоев 12 МБ`; `Файл не является корректным изображением`; body schema `{"detail": "..."}`
  - `404`: `User not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/users/wallpaper-file/{filename}`

- Controller: `backend/app/routers/users.py::get_wallpaper_file_v2`
- Data Contract:
  - Path params: `filename`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `_user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `wallpapers_root`
    - `FileResponse`
    - `HTTPException`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Invalid wallpaper filename`; `Invalid wallpaper path`; body schema `{"detail": "..."}`
  - `404`: `Wallpaper file not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/users/wallpaper-user/{user_id}`

- Controller: `backend/app/routers/users.py::get_wallpaper_by_user`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
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
    - `_user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FileResponse`
    - `User.get_by_id`
    - `HTTPException`
  - Side effects: File/storage operation
- Error Handling:
  - `404`: `Обои не найдены`; body schema `{"detail": "..."}`
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
    - `_: Depends(require_section_write('users'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `User.get_by_id`
    - `HTTPException`
    - `User.delete`
    - `revoke_user_tokens`
    - `emit_event_safe`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
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
  - Access mode: JWT (AuthMiddleware); route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write('users'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `User.get_by_id`
    - `HTTPException`
    - `User.update`
    - `emit_event_safe`
    - `Role.get_by_id`
    - `run_in_threadpool`
    - `revoke_user_tokens`
  - Side effects: DB write
- Error Handling:
  - `403`: `Назначение системной роли разрешено только системному суперпользователю.`; body schema `{"detail": "..."}`
  - `404`: `User not found`; `Role not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/users/{user_id}/company-links`

- Controller: `backend/app/routers/users.py::add_company_link`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`CompanyLinkCreate`](#model-companylinkcreate)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write('users'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `CompanyUserLink`
    - `db.add`
    - `require_section_write`
    - `HTTPException`
    - `User.get_by_id`
    - `Company.get_by_id`
    - `db.execute`
    - `db.commit`
    - `db.refresh`
    - `CompanyUserLink.company_id.in_`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Invalid link_type`; `company_id is required`; `Customer link is allowed only for customer companies`; body schema `{"detail": "..."}`
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
    - `_: Depends(require_section_write('users'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `User.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `select`
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
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
    - `_: Depends(require_section_read('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_read`
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
    - `_: Depends(require_section_write('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `Role.get_by_name`
    - `HTTPException`
    - `Role.create`
  - Side effects: DB write
- Error Handling:
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
  - Depends/Security:
    - `_: Depends(require_section_read('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_read`
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
  - Access mode: JWT (AuthMiddleware); route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `Role.get_by_id`
    - `HTTPException`
    - `Role.delete`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `System role cannot be deleted`; body schema `{"detail": "..."}`
  - `403`: `Системную роль может удалять только системный суперпользователь.`; body schema `{"detail": "..."}`
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
  - Access mode: JWT (AuthMiddleware); route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `Role.get_by_id`
    - `HTTPException`
    - `Role.update`
  - Side effects: DB write
- Error Handling:
  - `403`: `Системную роль может изменять только системный суперпользователь.`; body schema `{"detail": "..."}`
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
    - `_: Depends(require_section_read('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_read`
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
  - Access mode: JWT (AuthMiddleware); route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write('roles'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
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
  - `400`: `f'Unknown section: {item.section}`; body schema `{"detail": "..."}`
  - `403`: `Права системной роли может изменять только системный суперпользователь.`; body schema `{"detail": "..."}`
  - `404`: `Role not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `companies`

Source: `backend/app/routers/companies.py`

Prefix: `/api/v1/companies`

Endpoints: `17`

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
    - `_: Depends(require_section_write('companies'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `Company.create`
    - `emit_event_safe`
  - Side effects: DB write
- Error Handling:
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

#### `GET /api/v1/companies/default-our-company`

- Controller: `backend/app/routers/companies.py::get_default_our_company`
- Summary: Returns the system-wide "наша компания" default — the company whose
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
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Company.get_default_our_company`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Default our company is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/companies/documents/{document_id}`

- Controller: `backend/app/routers/companies.py::delete_company_file_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
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
    - `_: Depends(require_section_write('companies'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `db.execute`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
    - `delete_path`
    - `logger.warning`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/companies/documents/{document_id}/download`

- Controller: `backend/app/routers/companies.py::download_company_file_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
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
    - `_: Depends(require_section_write('companies'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `HTTPException`
    - `db.execute`
    - `httpx.AsyncClient`
    - `db.commit`
    - `select`
    - `asyncio.sleep`
    - `logger.warning`
  - Side effects: DB write, DB read
- Error Handling:
  - `500`: `Dadata token is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/companies/types-summary`

- Controller: `backend/app/routers/companies.py::get_companies_types_summary`
- Summary: Распределение количества контрагентов по типам (для chip-фильтров).
- Data Contract:
  - Path params: none
  - Query params: `search`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `Company.name.ilike`
    - `Company.short_name.ilike`
    - `Company.full_name.ilike`
    - `Company.inn.ilike`
    - `Company.contact_person.ilike`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
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
    - `_: Depends(require_section_write('companies'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `Company.get_by_id`
    - `Company.delete`
    - `HTTPException`
    - `emit_event_safe`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
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
    - `_: Depends(require_section_write('companies'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `Company.update`
    - `HTTPException`
    - `emit_event_safe`
  - Side effects: DB write
- Error Handling:
  - `404`: `Компания не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/companies/{company_id}/documents`

- Controller: `backend/app/routers/companies.py::list_company_documents`
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
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `aliased`
    - `db.execute`
    - `CompanyDocument.created_at.desc`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/companies/{company_id}/documents/upload`

- Controller: `backend/app/routers/companies.py::upload_company_file_document`
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: `our_company_id`: Optional[str] (optional, default=None, constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `CompanyDocumentResponse`
  - Response contracts: [`CompanyDocumentResponse`](#model-companydocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('companies'))`
- Logic Flow:
  - Internal calls:
    - `Form`
    - `File`
    - `Depends`
    - `validate_upload_metadata`
    - `CompanyDocument`
    - `db.add`
    - `require_section_write`
    - `storage_available`
    - `HTTPException`
    - `Company.get_by_id`
    - `write_upload_to_tmp`
    - `db.commit`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `400`: `Default our_company is not configured; set one via /companies/{id}/set-default`; `Our company not found`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/companies/{company_id}/related-deals`

- Controller: `backend/app/routers/companies.py::get_company_related_deals`
- Summary: Сделки, где компания фигурирует как заказчик/наша/генподрядчик.
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
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
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `Deal.created_at.desc`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/companies/{company_id}/set-default`

- Controller: `backend/app/routers/companies.py::set_default_our_company`
- Summary: Mark this company as the default "наша компания". Only internal
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
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(require_section_write('companies'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `Company.get_by_id`
    - `HTTPException`
    - `Company.set_default`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Only internal companies can be set as default our_company`; body schema `{"detail": "..."}`
  - `404`: `Company not found`; body schema `{"detail": "..."}`
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
    - `_: Depends(require_section_write('companies'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
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
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `_: Depends(CurrentUser)`
    - `__: Depends(require_section_read('companies'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_read`
    - `HTTPException`
    - `httpx.AsyncClient`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Query is required`; body schema `{"detail": "..."}`
  - `500`: `Dadata token is not configured`; body schema `{"detail": "..."}`
  - `502`: `Failed to lookup party data`; body schema `{"detail": "..."}`
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


## Usage Examples (Domain)

### `POST /api/v1/auth/login`

```bash
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email": "user@example.com", "password": "string"}'
```

```json
{
  "access_token": "string",
  "challenge_token": "string",
  "is_superuser": false,
  "permissions": {},
  "refresh_token": "string",
  "requires_2fa": false,
  "requires_2fa_setup": false,
  "token_type": "string"
}
```


### `POST /api/v1/auth/refresh`

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh -H "Content-Type: application/json" -d '{"refresh_token": "string"}'
```

```json
{
  "is_superuser": false,
  "permissions": {},
  "user": "string"
}
```
