# CODEX_HANDOFF.md


## 1. Короткий рабочий prompt для второго Codex

Используй этот текст как стартовый prompt для нового Codex:

```text
Ты работаешь в монолитной CRM/ERP-системе для управления строительными проектами.

Главная бизнес-сущность системы — Сделка / Project / Deal. Почти все остальные контуры должны рассматриваться как связанные со сделкой: товары, этапы, контрактация, исполнение, договоры, исходящие документы, документация, файлы, платежи, активность, задачи, почта, внешние панели.

Стек:
- Frontend: Vue 3 + Pinia + Vue Router + Vite
- Backend: FastAPI + SQLAlchemy + Pydantic
- База: SQLite/PostgreSQL в зависимости от контура
- Файлы: локальное/смонтированное storage

Ключевой принцип:
- сначала понять бизнес-поток;
- затем определить центральную сущность;
- затем идти от view -> router -> service -> model/schema;
- не вносить изменения наугад по UI без проверки backend-контракта;
- не ломать связи сделки, этапов, договоров, исходящих, платежей и ролей.

Правила работы:
- перед изменениями читай проектную документацию;
- routers держи тонкими, бизнес-логику размещай в services;
- новые API/изменения API синхронизируй с документацией;
- сохраняй русский текст в UTF-8, не допускай mojibake и unicode-escape вместо нормальной кириллицы;
- не переименовывай и не вычищай существующие сущности, пока не понял, не используются ли они скрыто в других модулях;
- особенно осторожно работай с: Deal, Stage, Contract, OutgoingDocument, Treasury/DDS, Role/Subrole, linked company logic.

Основные зоны активной разработки:
- ProjectDetail
- OutgoingRegistry
- DataHealth
- Tasks
- Mail
- Treasury / DDS
- Companies
- DocumentTemplates

Если меняешь что-то важное, обязательно проверь:
- карточку сделки;
- этапы и их drag/drop/иерархию;
- исходящие документы и рендер;
- связи с договорами;
- платежи/ДДС;
- роли и видимость данных.
```

## 2. Что читать в первую очередь

Порядок чтения для нового Codex:

1. `README.md`
2. `docs/PROJECT_OVERVIEW.md`
3. `docs/DEVELOPER_ARCHITECTURE.md`
4. `docs/INTERNAL.md`
5. `docs/MODULE_RELATIONS.md`
6. `docs/TECHNICAL_SPECIFICATION.md`
7. `docs/OUTGOING_REGISTRY.md`
8. `docs/OPERATIONS.md`
9. `docs/DEPLOYMENT.md`
10. этот файл `docs/CODEX_HANDOFF.md`

Если задача касается конкретного модуля, после этого сразу открывать профильные frontend/backend файлы из раздела 4.

## 3. Бизнес-модель, которую нужно держать в голове

Упрощенная центральная цепочка:

```text
Лид -> Сделка -> Товары сделки -> Этапы -> Контрактация -> Исполнение
     -> Договоры -> Исходящие / Документы / Файлы
     -> Платежи -> Казначейство -> ДДС -> Финансы
     -> Задачи / Активность / Контроль данных / Почта / Панели
```

### Наиболее важные сущности

- `Deal` — главный контейнер проектной логики
- `Company` / `Контрагент` — стороны проекта и маппинг доступа
- `DealProduct` — товар внутри конкретной сделки
- `Stage` — этап проектного/производственного плана
- `Stage dependency` — зависимость этапов и сроков
- `StageProductAssignment` / контрактация — связка этапа, товара и исполнителя
- `Contract` — юридическая и документарная основа
- `OutgoingDocument` — письма, счета, акты, УПД, счет-фактуры
- `TreasuryTransaction` / `IncomeExpense` — финансовый факт и ДДС
- `Task` — операционная координация
- `Activity` / event log — единая лента событий
- `Role + Subrole + linked_company` — бизнес-модель доступа

### Самые чувствительные места

- изменение структуры сделки;
- изменение логики этапов и их зависимостей;
- изменение логики исходящих документов;
- изменение финансовых связей;
- изменение ролей/субролей;
- изменение хранения файлов;
- изменение русскоязычных текстов с риском поломки кодировки.

## 4. Ключевые файлы, через которые быстрее всего понять проект

### 4.1 Frontend — основные экраны

#### Центральные экраны

- `frontend/src/views/ProjectDetail.vue`
  - главный экран системы;
  - тут сходятся: обзор, товары, этапы, gantt, контрактация, исполнение, документация, письма, активность, data health;
  - это первый файл для изучения, если задача связана со сделками.

- `frontend/src/views/Projects.vue`
  - список сделок;
  - фильтры, компактные/основные представления, вход в карточку проекта.

- `frontend/src/views/Leads.vue`
  - входной коммерческий контур;
  - нужен для задач по лидам и конвертации.

#### Документы и коммуникации

- `frontend/src/views/OutgoingRegistry.vue`
  - один из самых часто меняемых модулей;
  - unified registry для писем, счетов, актов, УПД, счет-фактур;
  - содержит новый structured editor, превью и AI-assisted сценарии.

- `frontend/src/components/outgoing/StructuredDocumentEditor.vue`
  - структура редактора исходящих документов.

- `frontend/src/components/outgoing/StructuredRichTextBlock.vue`
  - rich text блок внутри structured editor.

- `frontend/src/views/DocumentTemplates.vue`
  - реестр шаблонов документов и справочник полей.

- `frontend/src/views/DocumentRegistry.vue`
  - реестр документации.

- `frontend/src/views/FilesCatalog.vue`
  - отдельный файловый каталог.

- `frontend/src/views/Mail.vue`
  - почтовый модуль;
  - синхронизация, папки, письмо, body/render, вложения.

- `frontend/src/views/Messenger.vue`
  - внутренние коммуникации / мессенджер.

#### Производство и управление

- `frontend/src/views/Tasks.vue`
  - задачи, канбан, матрица Эйзенхауэра, статусы, наблюдатели, исполнители.

- `frontend/src/views/Calendar.vue`
  - календарный срез по задачам и срокам.

- `frontend/src/views/Gantt.vue`
  - gantt-представления.

- `frontend/src/views/ExecutorPanel.vue`
  - внешний/ограниченный срез для исполнителя/подрядчика.

- `frontend/src/views/CustomerPanel.vue`
  - внешний/ограниченный срез для заказчика.

#### Финансы и справочники

- `frontend/src/views/Treasury.vue`
  - казначейство, распределение платежей, связь с ДДС.

- `frontend/src/views/IncomeExpense.vue`
  - записи ДДС.

- `frontend/src/views/Finance.vue`
  - финансовый обзор/аналитика.

- `frontend/src/views/Catalog.vue`
  - каталог товаров/разделов.

- `frontend/src/views/Companies.vue`
  - контрагенты, реквизиты, документы компаний.

- `frontend/src/views/Contracts.vue`
- `frontend/src/views/ContractDetail.vue`
  - договорный контур.

#### Администрирование и системные блоки

- `frontend/src/views/Roles.vue`
  - матрица прав, роли, гранулярность доступа.

- `frontend/src/views/Users.vue`
  - пользователи.

- `frontend/src/views/DataHealth.vue`
  - контроль данных / системные проблемы.

#### Shell приложения

- `frontend/src/App.vue`
  - глобальный layout, боковая навигация, шапка, глобальные виджеты.

- `frontend/src/config/appVariant.js`
  - брендинг, variant-specific значения, компании превью и общий app-identity слой.

### 4.2 Backend — роутеры, которые нужно знать

#### Центральные

- `backend/app/routers/deals.py`
- `backend/app/routers/stages.py`
- `backend/app/routers/deal_execution.py`
- `backend/app/routers/products.py`
- `backend/app/routers/contracts.py`

Это ядро проектной модели.

#### Документы и шаблоны

- `backend/app/routers/outgoing_registry.py`
- `backend/app/routers/document_templates.py`
- `backend/app/routers/document_registry.py`
- `backend/app/routers/files_catalog.py`
- `backend/app/routers/storage.py`

#### Почта, сообщения, уведомления

- `backend/app/routers/mail.py`
- `backend/app/routers/global_chat.py`
- `backend/app/routers/notifications.py`
- `backend/app/routers/telegram_notifications.py`

#### Финансы

- `backend/app/routers/finance.py`
- `backend/app/routers/income_expense.py`
- `backend/app/routers/banks.py`

#### Доступ и пользователи

- `backend/app/routers/auth.py`
- `backend/app/routers/users.py`
- `backend/app/routers/roles.py`

#### AI и системные расширения

- `backend/app/routers/ai.py`
- `backend/app/routers/data_health.py`

### 4.3 Backend — сервисы, где реально лежит логика

#### Самые важные

- `backend/app/services/gantt_service.py`
  - логика gantt и производственных зависимостей.

- `backend/app/services/subcontractor_gantt_service.py`
  - gantt/логика по субподрядчикам.

- `backend/app/services/finance_service.py`
- `backend/app/services/economy_service.py`
  - расчеты финансовых производных.

- `backend/app/services/data_health.py`
- `backend/app/services/data_health_report.py`
  - правила и сборка системных проблем.

- `backend/app/services/storage.py`
  - файловый контур.

- `backend/app/services/mail_imap.py`
- `backend/app/services/mail_smtp.py`
- `backend/app/services/mail_sync.py`
  - прием/синхронизация/отправка почты.

- `backend/app/services/outgoing_document_editor.py`
  - structured document layer для исходящих.

- `backend/app/services/document_template_fields.py`
  - справочник полей и логика плейсхолдеров.

- `backend/app/services/permissions.py`
  - если меняются права и логика видимости.

- `backend/app/services/ai_service.py`
  - интеграция AI-контуров.

### 4.4 Модели и схемы, куда смотреть при изменении структуры данных

- `backend/app/models/`
- `backend/app/schemas/`

Особенно важны модели:
- сделок;
- этапов;
- продуктов сделки;
- договоров;
- исходящих документов;
- ДДС/казначейства;
- ролей/пользователей;
- data health issue.

## 5. Где чаще всего вносятся изменения

### Если меняется карточка проекта

Открывать:
- `frontend/src/views/ProjectDetail.vue`
- `backend/app/routers/deals.py`
- `backend/app/routers/stages.py`
- `backend/app/routers/products.py`
- `backend/app/routers/deal_execution.py`

### Если меняются этапы / gantt / зависимости

Открывать:
- `frontend/src/views/ProjectDetail.vue`
- `frontend/src/views/Gantt.vue`
- `backend/app/routers/stages.py`
- `backend/app/services/gantt_service.py`
- `backend/app/services/subcontractor_gantt_service.py`

### Если меняются документы / исходящие / шаблоны

Открывать:
- `frontend/src/views/OutgoingRegistry.vue`
- `frontend/src/components/outgoing/StructuredDocumentEditor.vue`
- `frontend/src/views/DocumentTemplates.vue`
- `backend/app/routers/outgoing_registry.py`
- `backend/app/routers/document_templates.py`
- `backend/app/services/outgoing_document_editor.py`
- `backend/app/services/document_template_fields.py`

### Если меняется казначейство / ДДС

Открывать:
- `frontend/src/views/Treasury.vue`
- `frontend/src/views/IncomeExpense.vue`
- `backend/app/routers/finance.py`
- `backend/app/routers/income_expense.py`
- `backend/app/services/finance_service.py`

### Если меняется почта

Открывать:
- `frontend/src/views/Mail.vue`
- `backend/app/routers/mail.py`
- `backend/app/services/mail_imap.py`
- `backend/app/services/mail_smtp.py`
- `backend/app/services/mail_sync.py`

### Если меняются права доступа

Открывать:
- `frontend/src/views/Roles.vue`
- `frontend/src/App.vue`
- `backend/app/routers/roles.py`
- `backend/app/routers/users.py`
- `backend/app/services/permissions.py`

## 6. Самые хрупкие участки проекта

Новый Codex должен считать высокорискованными:

- `ProjectDetail.vue`
- этапы и их drag/drop/иерархию;
- связи этапов и close_date;
- исходящие документы, preview, нумерацию, шаблоны;
- зачеты платежей в актах/счетах;
- контрагентов и банковские реквизиты;
- роли, суброли и contractor mapping;
- почтовый body-render и вложения;
- файловое хранилище и entity-bound file links;
- кодировку русских строк во frontend-файлах.

### Типовые ошибки, которые здесь особенно опасны

- изменение UI без учета backend-контракта;
- изменение stage relation logic без проверки gantt и de facto;
- изменение исходящих без проверки связи с договорами и платежами;
- неявный слом прав доступа;
- сохранение файлов в неверную кодировку;
- фронтенд-выкладка с неправильными правами на `/assets`.

## 7. Практический алгоритм работы для нового Codex

На любую задачу:

1. Определи центральную сущность задачи.
2. Найди frontend entry point.
3. Найди backend router.
4. Найди service с реальной логикой.
5. Проверь, нет ли связанных модулей, которые автоматически затрагиваются.
6. Только после этого меняй код.
7. После правки проверь:
   - сборку frontend;
   - основные API;
   - смежный UI, который может использовать те же данные.

## 8. Минимальный self-check перед завершением задачи

Перед тем как считать задачу завершенной, новый Codex должен ответить себе:

- понял ли я, какая сущность здесь главная;
- проверил ли я view -> router -> service;
- не ломаю ли я сделку, этапы, договоры, исходящие, платежи или права;
- не внес ли я кодировку в broken state;
- проверил ли я смежный сценарий, который использует те же данные.

## 9. Специфика тестового VPS и выкладки

Если второй Codex будет работать с тестовым контуром на `mpb-erp.ru`, нужно помнить:

- после `scp` фронтенд-asset'ы периодически получают неправильные права;
- нужно отдельно проверять, что:
  - каталог `/assets` имеет `755`;
  - новые `js/css` имеют владельца `www-root:www-root`;
  - новые `js/css` имеют права `644`.

Иначе домен может открываться, а новые frontend bundles будут отдавать `403`.

### Текущий тестовый контур

- домен: `https://mpb-erp.ru`
- webroot: `/var/www/www-root/data/www/mpb-erp.ru`
- runtime проекта: `/opt/mpb-erp-test`
- backend service: `mpb-erp-test-backend.service`
- тестовая БД: `/opt/mpb-erp-test/test_portal/crm_test_portal.db`
- storage вынесен на `/mnt/storage20/mpb-erp-test/`


## 11. Короткая версия для вставки в чат второму Codex

```text
Начни с README.md, docs/PROJECT_OVERVIEW.md, docs/DEVELOPER_ARCHITECTURE.md, docs/INTERNAL.md и docs/CODEX_HANDOFF.md.

Смотри на систему как на монолитную CRM/ERP, где центральная сущность — Deal / Project. Почти все должно пониматься через сделку: товары, этапы, договоры, исходящие, документы, файлы, платежи, активность, задачи, панели.

Если меняешь что-то важное:
- ищи сначала frontend entry point;
- затем backend router;
- затем service;
- отдельно проверяй смежные блоки.

Самые важные файлы:
- frontend/src/views/ProjectDetail.vue
- frontend/src/views/OutgoingRegistry.vue
- frontend/src/views/Tasks.vue
- frontend/src/views/Treasury.vue
- frontend/src/views/Mail.vue
- frontend/src/views/Companies.vue
- backend/app/routers/deals.py
- backend/app/routers/stages.py
- backend/app/routers/outgoing_registry.py
- backend/app/routers/finance.py
- backend/app/routers/mail.py
- backend/app/services/gantt_service.py
- backend/app/services/outgoing_document_editor.py
- backend/app/services/finance_service.py
- backend/app/services/data_health.py

Особо не ломай:
- этапы и их зависимости;
- исходящие документы и шаблоны;
- связи с договорами;
- платежи и ДДС;
- роли/суброли;
- русский текст и кодировку UTF-8.
```

