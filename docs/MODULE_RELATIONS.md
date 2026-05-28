# Module Relations

Документ фиксирует верхнеуровневые связи между основными модулями `Nexus ERP`.

Диаграмма ниже не претендует на детализацию по каждой таблице или API-роуту. Ее задача —
показать, как бизнес-контуры связаны между собой на уровне экранов, сущностей и потоков данных.

## Mermaid Diagram

```mermaid
flowchart LR
    subgraph Core["Базовый контур"]
        Users["Пользователи, роли и права"]
        Companies["Компании и контрагенты"]
    end

    subgraph CRM["CRM и проекты"]
        Leads["Лиды"]
        Projects["Сделки / проекты"]
        DealProducts["Товары сделки"]
        Stages["Этапы и план-график"]
        Contracts["Договоры"]
        Payments["Оплаты и платежные события"]
    end

    subgraph Delivery["Контрактация и исполнение"]
        Contracting["Контрактация"]
        Execution["Исполнение / De facto"]
        Gantt["Гант по этапам и товарам"]
        Tasks["Задачи и аукционы"]
        Executor["Панель исполнителя"]
        Customer["Кабинет заказчика"]
    end

    subgraph Docs["Документы и коммуникации"]
        DocRegistry["Реестр документов"]
        Files["Каталог файлов и хранилище"]
        Outgoing["Исходящие письма"]
        Mail["Почта"]
        Messenger["Мессенджер и чаты"]
        Support["Тех. поддержка"]
        Notifications["Уведомления"]
    end

    subgraph Finance["Финансовый контур"]
        Treasury["Казначейство"]
        DDS["Доходы / расходы"]
        FinanceView["Финансы"]
    end

    subgraph HR["Команда и HR"]
        Profiles["Профили сотрудников"]
        Workday["Рабочий день"]
        Absences["Отсутствия"]
    end

    subgraph Communications["Корпоративная коммуникация"]
        Feed["Корпоративная лента (Home/Feed)"]
        Reglaments["Нормативная база (Reglaments)"]
    end

    subgraph Platform["Платформа и интеграции"]
        Search["Глобальный поиск (FTS5 + bge-m3)"]
        EventBus["Event Bus v2"]
        Approvals["Согласования"]
        Mobile["Мобильный клиент (Flutter)"]
    end

    Companies --> Leads
    Companies --> Projects
    Users --> Projects
    Users --> Tasks
    Users --> Support

    Leads --> Projects
    Projects --> DealProducts
    Projects --> Stages
    Projects --> Contracts
    Projects --> Payments
    Projects --> DocRegistry
    Projects --> Outgoing
    Projects --> Tasks

    DealProducts --> Contracting
    Stages --> Contracting
    Contracts --> Contracting

    Contracting --> Execution
    Execution --> Gantt
    Execution --> Executor
    Execution --> Customer

    Tasks --> Execution
    Tasks --> Messenger
    Support --> Tasks
    Support --> Notifications
    Messenger --> Notifications
    Mail --> Outgoing
    Outgoing --> Files
    DocRegistry --> Files
    Contracts --> Files

    Payments --> Treasury
    Treasury --> DDS
    DDS --> FinanceView
    Payments --> Customer

    Files --> Customer
    Outgoing --> Customer
    Gantt --> Customer

    Companies --> Executor
    Users --> Executor
    Companies --> Customer
    Users --> Customer

    Users --> Profiles
    Users --> Workday
    Users --> Absences
    Profiles --> Customer

    Users --> Feed
    Feed --> Notifications
    Reglaments --> Search

    Projects --> Approvals
    Tasks --> Approvals
    Projects --> EventBus
    Tasks --> EventBus
    Contracts --> EventBus
    Outgoing --> EventBus
    Users --> EventBus
    EventBus --> Notifications

    Projects --> Search
    Tasks --> Search
    Leads --> Search
    Contracts --> Search
    Files --> Search
    Feed --> Search

    Mobile --> Notifications
    Mobile --> Tasks
    Mobile --> Workday
```

## Краткая Логика Связей

- `Лиды` являются входом в воронку и при успешной квалификации переходят в `Сделки / проекты`.
- `Сделка / проект` является центральной сущностью, к которой привязаны товары, этапы, договоры, оплаты, задачи, документы и исходящие письма.
- `Контрактация` связывает этапы, товары и договорный контур, после чего переходит в слой `Исполнения`.
- `Исполнение / De facto` управляет назначениями исполнителей, рабочими сроками, договорными сроками, подзадачами и gantt-представлениями.
- `Панель исполнителя` показывает только назначенные пользователю объекты, товары и подзадачи.
- `Кабинет заказчика` строится на данных проекта, оплат, gantt, документов и исходящих писем, видимых заказчику.
- `Казначейство`, `Доходы / расходы` и `Финансы` образуют финансовый контур, связанный с платежами и проектами.
- `Реестр документов`, `Каталог файлов`, `Исходящие письма` и `Почта` формируют единый документный и коммуникационный слой.
- `Тех. поддержка` — тикет-система: пользователь заводит обращение, сотрудник поддержки ведёт его, может породить `Задачу` из тикета и инициирует `Уведомления`.
- **HR-блок** (`Профили / Рабочий день / Отсутствия`) живёт от пользователей, через секционные права `profiles`/`workday`/`absences`. `Workday` пишет фактические сессии работы, `Absences` — отпуска и больничные с таймлайном.
- **`Корпоративная лента`** (`Home / Feed`) — корпоративная коммуникация: посты, опросы, реакции, комментарии, @mentions, прикрепление изображений и файлов. Источник `feed_*` событий для `Уведомлений`.
- **`Нормативная база`** (`Reglaments`) — каталог СП/ГОСТ/СНиП с собственным изолированным поисковым доменом (`reglament_fts` + `reglament_embeddings`). Питает свой раздел `Поиска`, не пересекается с основным CRM-индексом.
- **`Согласования`** (`Approvals`) — состояния согласования по сделкам/проектам/задачам с шаблонами и шагами.
- **`Глобальный поиск`** — гибридный (FTS5 BM25 + bge-m3 cosine, объединение через RRF). Индексирует Сделки/Задачи/Лиды/Договоры/Файлы/Посты ленты/Нормы. ACL применяется per-row (child-entity сущности проверяются через родителя — см. `INTERNAL.md` §9.1).
- **`Event Bus v2`** — шина для интеграций с внешними системами: transactional outbox + подписки с JSON-Logic фильтрацией + HMAC-подпись + retry/DLQ. Источники: эмиссии из сделок/задач/договоров/исходящих/пользователей. Потребители: внешние сервисы (Telegram, 1С, Диадок, ЭЦП и т.п.) + внутренний `search_indexer` как первый consumer.
- **`Мобильный клиент`** — Flutter-приложение (`mobile_app/`) с фокусом на уведомления, задачи и рабочее время. CI через Codemagic.

## Где Использовать Эту Диаграмму

- в `docs/PROJECT_OVERVIEW.md` как верхнеуровневую карту модулей;
- в `docs/TECHNICAL_SPECIFICATION.md` как схему предметного контура;
- в презентационных и договорных материалах как краткое описание состава платформы.
