# API Domains Index

Сгенерировано на 2026-02-15 03:22:39 (local time).

## API Domain Map
- `auth`: Аутентификация, пользователи, роли, компании и справочные интеграции.
- `crm`: Сделки, лиды, этапы, задачи, продукты, тендеры и исполнение.
- `finance`: Финансы, казначейство, ДДС, экономика, штрафы и договоры.
- `documents`: Реестры документов, исходящие, загрузки, хранилище и файловый каталог.
- `communications`: Почта, чаты, уведомления и пользовательские предпочтения уведомлений.
- `legal_compliance`: Юридическая работа и аккредитации.
- `analytics`: Дашбордовые сводки и аудит событий.

## Domain Files

| Domain | Description | Routers | Endpoints | Models | File |
| --- | --- | --- | --- | --- | --- |
| `auth` | Аутентификация, пользователи, роли, компании и справочные интеграции. | 6 | 28 | 14 | [`auth.md`](auth.md) |
| `crm` | Сделки, лиды, этапы, задачи, продукты, тендеры и исполнение. | 14 | 122 | 48 | [`crm.md`](crm.md) |
| `finance` | Финансы, казначейство, ДДС, экономика, штрафы и договоры. | 5 | 87 | 45 | [`finance.md`](finance.md) |
| `documents` | Реестры документов, исходящие, загрузки, хранилище и файловый каталог. | 5 | 54 | 21 | [`documents.md`](documents.md) |
| `communications` | Почта, чаты, уведомления и пользовательские предпочтения уведомлений. | 7 | 32 | 20 | [`communications.md`](communications.md) |
| `legal_compliance` | Юридическая работа и аккредитации. | 2 | 23 | 16 | [`legal_compliance.md`](legal_compliance.md) |
| `analytics` | Дашбордовые сводки и аудит событий. | 2 | 4 | 0 | [`analytics.md`](analytics.md) |

## Global Rules

### Base URL
- Локально: `http://localhost:8000/api/v1`
- Production: `<your-domain>/api/v1`

### Authentication Header
- `Authorization: Bearer <access_token>` для всех защищённых endpoint'ов.
- Публичные исключения: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`.

### Common Error Codes
| Code | Meaning | Typical Body |
| --- | --- | --- |
| `400` | Ошибка бизнес-валидации/формата данных | `{"detail": "..."}` |
| `401` | Ошибка аутентификации/токена | `{"detail": "..."}` |
| `403` | Недостаточно прав | `{"detail": "..."}` |
| `404` | Сущность/ресурс не найден | `{"detail": "..."}` |
| `422` | Ошибка валидации запроса FastAPI/Pydantic | `{ "detail": [{"loc": [...], "msg": "...", "type": "..."}] }` |
| `500` | Внутренняя ошибка сервера | `{"detail": "Internal Server Error"}` или текст исключения |

### Error Envelope
- Базовый формат: `{"detail": "..."}` (`HTTPException`).
- Для `422`: `detail[]` с массивом ошибок валидации.

### Update Rule
- При изменении роутеров/схем: сначала перегенерировать `docs/API.md`, затем заново запустить `scripts/split_api_reference.py`.
