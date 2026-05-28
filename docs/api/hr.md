# HR & Workforce API

Сгенерировано из `docs/API.md` на 2026-05-29 01:30:42 (local time).

## Scope
- Домен: `hr`
- Описание: Профили сотрудников, рабочий день и отсутствия (HR-блок).
- Routers: `3`
- Endpoints: `18`
- Список роутеров: `profiles`, `workday`, `absences`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `15`.

### Model `UserProfilePatchAdmin`

Source: `backend/app/schemas/profile.py`

Description: Админ может править всё.


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| birth_date | Optional[date] | no | None | - |
| birth_show_year | Optional[bool] | no | None | - |
| bio | Optional[str] | no | None | max_length=4000 |
| interests | Optional[List[str]] | no | None | - |
| skills | Optional[List[str]] | no | None | - |
| telegram_username | Optional[str] | no | None | max_length=64 |
| job_title | Optional[str] | no | None | max_length=255 |
| department | Optional[str] | no | None | max_length=255 |
| manager_id | Optional[str] | no | None | - |
| hire_date | Optional[date] | no | None | - |


### Model `UserProfilePatchSelf`

Source: `backend/app/schemas/profile.py`

Description: Что можно править САМОМУ. Формальные поля сюда не входят.


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| birth_date | Optional[date] | no | None | - |
| birth_show_year | Optional[bool] | no | None | - |
| bio | Optional[str] | no | None | max_length=4000 |
| interests | Optional[List[str]] | no | None | - |
| skills | Optional[List[str]] | no | None | - |
| telegram_username | Optional[str] | no | None | max_length=64 |


### Model `UserProfileResponse`

Source: `backend/app/schemas/profile.py`

Description: Полный профиль для вывода. Если `birth_show_year=False` — год
в `birth_date` уже занулён бэком (см. router).


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| job_title | Optional[str] | no | None | max_length=255 |
| department | Optional[str] | no | None | max_length=255 |
| manager_id | Optional[str] | no | None | - |
| hire_date | Optional[date] | no | None | - |
| birth_date | Optional[date] | no | None | - |
| birth_show_year | bool | no | True | - |
| bio | Optional[str] | no | None | max_length=4000 |
| interests | List[str] | no | [] | - |
| skills | List[str] | no | [] | - |
| telegram_username | Optional[str] | no | None | max_length=64 |
| user_id | str | yes | - | - |
| full_name | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| avatar_url | Optional[str] | no | None | - |
| role_name | Optional[str] | no | None | - |
| manager_full_name | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `WorkSessionResponse`

Source: `backend/app/schemas/workday.py`

Description: Одна сессия учёта (активная или закрытая).


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| user_id | str | yes | - | - |
| started_at | datetime | yes | - | - |
| ended_at | Optional[datetime] | no | None | - |
| ended_reason | Optional[str] | no | None | - |
| last_activity_at | datetime | yes | - | - |
| note_start | Optional[str] | no | None | - |
| note_end | Optional[str] | no | None | - |
| duration_seconds | int | no | 0 | - |
| is_active | bool | no | False | - |


### Model `WorkdayActiveResponse`

Source: `backend/app/schemas/workday.py`

Description: Состояние «рабочего дня» для текущего пользователя.

`session` — активная сейчас (или null, если не начат). FE по нему
решает: показать модал «Начать рабочий день» или счётчик в топбаре.
`track_work_time` — выключатель фичи для роли (если False, FE
вообще ничего не показывает по учёту). `idle_timeout_minutes` —
через сколько минут бездействия фронт сам закрывает сессию (с
отметкой `ended_at = last_activity_at`, причина `idle`).

`worked_today_seconds` — сумма ЗАКРЫТЫХ сессий за сегодняшний день
по московской дате (UTC+3 без DST). Фронт прибавляет к этому числу
live-elapsed активной сессии — чтобы счётчик в чипе показывал не
отдельный отрезок, а накопленный итог за день. Атрибуция по
`started_at`: сессия попадает в день своего начала.


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| session | Optional[WorkSessionResponse] | no | None | - |
| track_work_time | bool | no | False | - |
| idle_timeout_minutes | int | no | DEFAULT_IDLE_TIMEOUT_MINUTES | - |
| worked_today_seconds | int | no | 0 | - |


### Model `WorkdayEndRequest`

Source: `backend/app/schemas/workday.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| reason | str | no | 'manual' | pattern='^(manual\|idle)$' |
| ended_at | Optional[datetime] | no | None | - |
| note_end | Optional[str] | no | None | max_length=4000 |


### Model `WorkdayGridItem`

Source: `backend/app/schemas/workday.py`

Description: Строка табличного вида: один сотрудник + посуточная разбивка
отработанных секунд за период.

`days` — карта `ISO-дата → секунды` (только дни, где что-то было).
Сессия атрибутируется дню своего `started_at` (как в /stats day).


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| user_id | str | yes | - | - |
| full_name | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| role_name | Optional[str] | no | None | - |
| total_seconds | int | no | 0 | - |
| has_active | bool | no | False | - |
| days | dict[str, int] | no | {} | - |


### Model `WorkdayHeartbeatResponse`

Source: `backend/app/schemas/workday.py`

Description: Возвращает обновлённый last_activity_at либо null если сессии нет.


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| session_id | Optional[str] | no | None | - |
| last_activity_at | Optional[datetime] | no | None | - |


### Model `WorkdayListItem`

Source: `backend/app/schemas/workday.py`

Description: Строка для боковой панели статистики: один пользователь + его
суммарное время за период (для админа — все юзеры, иначе только себя).

`worked_today` — был ли у юзера хотя бы один тик активности
в сегодняшний день (server UTC). Используется фронтом, чтобы
подсветить «не был сегодня» в сайдбаре независимо от фильтра дат.


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| user_id | str | yes | - | - |
| full_name | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| role_name | Optional[str] | no | None | - |
| total_seconds | int | no | 0 | - |
| sessions_count | int | no | 0 | - |
| has_active | bool | no | False | - |
| worked_today | bool | no | False | - |


### Model `WorkdaySessionPatch`

Source: `backend/app/schemas/workday.py`

Description: Админ-правка существующей сессии.


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| started_at | Optional[datetime] | no | None | - |
| ended_at | Optional[datetime] | no | None | - |
| ended_reason | Optional[str] | no | None | pattern='^(manual\|idle\|admin)$' |
| note_start | Optional[str] | no | None | max_length=4000 |
| note_end | Optional[str] | no | None | max_length=4000 |


### Model `WorkdayStartRequest`

Source: `backend/app/schemas/workday.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| note_start | Optional[str] | no | None | max_length=4000 |


### Model `WorkdayStatsResponse`

Source: `backend/app/schemas/workday.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| user_id | str | yes | - | - |
| full_name | Optional[str] | no | None | - |
| email | Optional[str] | no | None | - |
| role_name | Optional[str] | no | None | - |
| total_seconds | int | no | 0 | - |
| sessions_count | int | no | 0 | - |
| buckets | list[WorkdayBucket] | no | [] | - |


### Model `AbsenceCreate`

Source: `backend/app/schemas/profile.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| type | str | yes | - | - |
| date_from | date | yes | - | - |
| date_to | date | yes | - | - |
| comment | Optional[str] | no | None | max_length=2000 |
| user_id | Optional[str] | no | None | - |


### Model `AbsencePatch`

Source: `backend/app/schemas/profile.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| type | Optional[str] | no | None | - |
| date_from | Optional[date] | no | None | - |
| date_to | Optional[date] | no | None | - |
| comment | Optional[str] | no | None | max_length=2000 |


### Model `AbsenceResponse`

Source: `backend/app/schemas/profile.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| type | str | yes | - | - |
| date_from | date | yes | - | - |
| date_to | date | yes | - | - |
| comment | Optional[str] | no | None | max_length=2000 |
| id | str | yes | - | - |
| user_id | str | yes | - | - |
| user_full_name | Optional[str] | no | None | - |
| created_by | Optional[str] | no | None | - |
| created_by_full_name | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


## Routers / Controllers Reference

### Router `profiles`

Source: `backend/app/routers/profiles.py`

Prefix: `/api/v1/profiles`

Endpoints: `6`

#### `GET /api/v1/profiles/birthdays`

- Controller: `backend/app/routers/profiles.py::upcoming_birthdays`
- Summary: Ближайшие дни рождения сотрудников в окне `window` дней.
- Data Contract:
  - Path params: none
  - Query params: `window`: int (optional, default=30, constraints=ge=1, le=365)
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
    - `UserProfile.birth_date.is_not`
    - `select`
  - Side effects: DB read, File/storage operation
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/profiles/me`

- Controller: `backend/app/routers/profiles.py::get_my_profile`
- Summary: Мой профиль — создаётся пустой при первом обращении.
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `UserProfileResponse`
  - Response contracts: [`UserProfileResponse`](#model-userprofileresponse)
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

#### `PATCH /api/v1/profiles/me`

- Controller: `backend/app/routers/profiles.py::patch_my_profile`
- Summary: Правка ЛИЧНЫХ полей своего профиля. Формальные поля
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`UserProfilePatchSelf`](#model-userprofilepatchself)
  - Response model: `UserProfileResponse`
  - Response contracts: [`UserProfileResponse`](#model-userprofileresponse)
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

#### `GET /api/v1/profiles/suggest`

- Controller: `backend/app/routers/profiles.py::suggest_chips`
- Summary: Уникальные значения чипов из всех профилей, опционально
- Data Contract:
  - Path params: none
  - Query params: `field`: str (required, default=-, constraints=pattern='^(skills|interests)$'); `q`: Optional[str] (optional, default=None, constraints=max_length=64); `limit`: int (optional, default=20, constraints=ge=1, le=100)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[str]`
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
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/profiles/{user_id}`

- Controller: `backend/app/routers/profiles.py::get_user_profile`
- Summary: Профиль другого пользователя — публично для авторизованных.
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `UserProfileResponse`
  - Response contracts: [`UserProfileResponse`](#model-userprofileresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `db.execute`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `Пользователь не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/profiles/{user_id}`

- Controller: `backend/app/routers/profiles.py::patch_user_profile`
- Summary: Админская правка любого профиля. Нужен `users.edit_all`
- Data Contract:
  - Path params: `user_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`UserProfilePatchAdmin`](#model-userprofilepatchadmin)
  - Response model: `UserProfileResponse`
  - Response contracts: [`UserProfileResponse`](#model-userprofileresponse)
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
    - `db.commit`
    - `db.refresh`
    - `db.execute`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Сотрудник не может быть своим руководителем`; `Руководитель не найден`; body schema `{"detail": "..."}`
  - `403`: `Нет прав на правку профиля`; `Личные поля правьте через /profiles/me; формальные — только админ`; body schema `{"detail": "..."}`
  - `404`: `Пользователь не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `workday`

Source: `backend/app/routers/workday.py`

Prefix: `/api/v1/workday`

Endpoints: `8`

#### `GET /api/v1/workday/active`

- Controller: `backend/app/routers/workday.py::get_active`
- Summary: Текущее состояние трекера для меня.
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `WorkdayActiveResponse`
  - Response contracts: [`WorkdayActiveResponse`](#model-workdayactiveresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `WorkdayActiveResponse`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/workday/end`

- Controller: `backend/app/routers/workday.py::end_workday`
- Summary: Закончить активную сессию.
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`WorkdayEndRequest`](#model-workdayendrequest)
  - Response model: `WorkSessionResponse`
  - Response contracts: [`WorkSessionResponse`](#model-worksessionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `emit_event_safe`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `404`: `Активная сессия не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/workday/grid`

- Controller: `backend/app/routers/workday.py::workday_grid`
- Summary: Табличный вид: на каждого сотрудника — посуточная разбивка
- Data Contract:
  - Path params: none
  - Query params: `from_`: Optional[str] (optional, default=None, constraints=-); `to`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `list[WorkdayGridItem]`
  - Response contracts: [`WorkdayGridItem`](#model-workdaygriditem)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Query`
    - `get_section_acl`
    - `is_superuser`
    - `db.execute`
    - `WorkdayGridItem`
    - `WorkSession.user_id.in_`
    - `User.full_name.asc`
    - `select`
    - `WorkSession.ended_at.is_`
    - `Role.track_work_time.is_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/workday/heartbeat`

- Controller: `backend/app/routers/workday.py::heartbeat`
- Summary: Обновить last_activity_at у активной сессии. Шлётся фронтом
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `WorkdayHeartbeatResponse`
  - Response contracts: [`WorkdayHeartbeatResponse`](#model-workdayheartbeatresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `WorkdayHeartbeatResponse`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/workday/list`

- Controller: `backend/app/routers/workday.py::list_users_summary`
- Summary: Сайдбар-фид статистики.
- Data Contract:
  - Path params: none
  - Query params: `from_`: Optional[str] (optional, default=None, constraints=-); `to`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `list[WorkdayListItem]`
  - Response contracts: [`WorkdayListItem`](#model-workdaylistitem)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Query`
    - `get_section_acl`
    - `is_superuser`
    - `db.execute`
    - `WorkdayListItem`
    - `WorkSession.user_id.in_`
    - `User.full_name.asc`
    - `select`
    - `WorkSession.ended_at.is_`
    - `Role.track_work_time.is_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/workday/start`

- Controller: `backend/app/routers/workday.py::start_workday`
- Summary: Начать рабочий день. Идемпотентно: если активная сессия уже есть,
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`WorkdayStartRequest`](#model-workdaystartrequest)
  - Response model: `WorkSessionResponse`
  - Response contracts: [`WorkSessionResponse`](#model-worksessionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `WorkSession`
    - `db.add`
    - `db.flush`
    - `emit_event_safe`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/workday/stats`

- Controller: `backend/app/routers/workday.py::user_stats`
- Summary: Детальная статистика по одному пользователю за период.
- Data Contract:
  - Path params: none
  - Query params: `user_id`: Optional[str] (optional, default=None, constraints=-); `from_`: Optional[str] (optional, default=None, constraints=-); `to`: Optional[str] (optional, default=None, constraints=-); `groupby`: str (optional, default='day', constraints=pattern='^(day|week|month)$')
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `WorkdayStatsResponse`
  - Response contracts: [`WorkdayStatsResponse`](#model-workdaystatsresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Query`
    - `WorkdayStatsResponse`
    - `HTTPException`
    - `db.execute`
    - `WorkdayBucket`
    - `WorkSession.started_at.asc`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `Пользователь не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/workday/{session_id}`

- Controller: `backend/app/routers/workday.py::admin_patch_session`
- Summary: Админская правка существующей сессии. Требует `workday_admin`
- Data Contract:
  - Path params: `session_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`WorkdaySessionPatch`](#model-workdaysessionpatch)
  - Response model: `WorkSessionResponse`
  - Response contracts: [`WorkSessionResponse`](#model-worksessionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `is_superuser`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `get_section_acl`
    - `db.execute`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `403`: `Нет прав на правку сессий`; body schema `{"detail": "..."}`
  - `404`: `Сессия не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `absences`

Source: `backend/app/routers/absences.py`

Prefix: `/api/v1/absences`

Endpoints: `4`

#### `GET /api/v1/absences`

- Controller: `backend/app/routers/absences.py::list_absences`
- Summary: Список отсутствий с фильтрами.
- Data Contract:
  - Path params: none
  - Query params: `user_id`: Optional[str] (optional, default=None, constraints=-); `type_`: Optional[str] (optional, default=None, constraints=-); `from_`: Optional[date] (optional, default=None, constraints=-); `to`: Optional[date] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[AbsenceResponse]`
  - Response contracts: [`AbsenceResponse`](#model-absenceresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Query`
    - `select`
    - `UserAbsence.date_from.desc`
    - `db.execute`
    - `HTTPException`
    - `and_`
  - Side effects: DB read
- Error Handling:
  - `400`: `Неизвестный тип`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/absences`

- Controller: `backend/app/routers/absences.py::create_absence`
- Summary: Создать запись об отсутствии.
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AbsenceCreate`](#model-absencecreate)
  - Response model: `AbsenceResponse`
  - Response contracts: [`AbsenceResponse`](#model-absenceresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `UserAbsence`
    - `db.add`
    - `db.commit`
    - `db.refresh`
    - `HTTPException`
    - `get_section_acl`
    - `is_superuser`
    - `db.execute`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Сотрудник не найден`; body schema `{"detail": "..."}`
  - `403`: `Можно создавать только свои отсутствия`; `Раздел «Отсутствия» не доступен вашей роли`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/absences/{absence_id}`

- Controller: `backend/app/routers/absences.py::delete_absence`
- Summary: Удалить. Свою — владелец, чужую — админ.
- Data Contract:
  - Path params: `absence_id`: str (required, default=-, constraints=-)
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
    - `HTTPException`
    - `db.delete`
    - `db.commit`
    - `db.execute`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `403`: `Нет прав на удаление`; body schema `{"detail": "..."}`
  - `404`: `Запись не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/absences/{absence_id}`

- Controller: `backend/app/routers/absences.py::patch_absence`
- Summary: Правка записи. Свою — сам владелец; чужую — админ.
- Data Contract:
  - Path params: `absence_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AbsencePatch`](#model-absencepatch)
  - Response model: `AbsenceResponse`
  - Response contracts: [`AbsenceResponse`](#model-absenceresponse)
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
    - `db.commit`
    - `db.refresh`
    - `db.execute`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `403`: `Нет прав на правку чужой записи`; body schema `{"detail": "..."}`
  - `404`: `Запись не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


## Usage Examples (Domain)

Ключевые примеры отсутствуют для этого домена в исходном monolith reference.
