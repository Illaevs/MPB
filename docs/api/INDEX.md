# API Domains Index

Сгенерировано на 2026-05-29 01:30:42 (local time).

## API Domain Map
- `auth`: Аутентификация, пользователи, роли, компании, оргструктура и справочные интеграции.
- `crm`: Сделки, лиды, этапы, задачи, подзадачи, согласования, продукты, тендеры и исполнение.
- `finance`: Финансы, казначейство, ДДС, штрафы и договоры.
- `documents`: Реестры документов, шаблоны, исходящие, загрузки, хранилище и файловый каталог.
- `communications`: Почта, чаты, корпоративная лента, тех. поддержка, уведомления и пользовательские предпочтения уведомлений.
- `legal_compliance`: Юридическая работа, аккредитации и нормативная база.
- `hr`: Профили сотрудников, рабочий день и отсутствия (HR-блок).
- `platform`: Event Bus (outbox/subscriptions), поиск, AI-сервисы, customer portal и data-health диагностика.
- `analytics`: Дашбордовые сводки и аудит событий.

## Domain Files

| Domain | Description | Routers | Endpoints | Models | File |
| --- | --- | --- | --- | --- | --- |
| `auth` | Аутентификация, пользователи, роли, компании, оргструктура и справочные интеграции. | 7 | 63 | 30 | [`auth.md`](auth.md) |
| `crm` | Сделки, лиды, этапы, задачи, подзадачи, согласования, продукты, тендеры и исполнение. | 16 | 166 | 62 | [`crm.md`](crm.md) |
| `finance` | Финансы, казначейство, ДДС, штрафы и договоры. | 4 | 65 | 25 | [`finance.md`](finance.md) |
| `documents` | Реестры документов, шаблоны, исходящие, загрузки, хранилище и файловый каталог. | 6 | 82 | 22 | [`documents.md`](documents.md) |
| `communications` | Почта, чаты, корпоративная лента, тех. поддержка, уведомления и пользовательские предпочтения уведомлений. | 10 | 74 | 44 | [`communications.md`](communications.md) |
| `legal_compliance` | Юридическая работа, аккредитации и нормативная база. | 3 | 34 | 17 | [`legal_compliance.md`](legal_compliance.md) |
| `hr` | Профили сотрудников, рабочий день и отсутствия (HR-блок). | 3 | 18 | 15 | [`hr.md`](hr.md) |
| `platform` | Event Bus (outbox/subscriptions), поиск, AI-сервисы, customer portal и data-health диагностика. | 5 | 28 | 14 | [`platform.md`](platform.md) |
| `analytics` | Дашбордовые сводки и аудит событий. | 2 | 6 | 0 | [`analytics.md`](analytics.md) |

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
