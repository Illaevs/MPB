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
        Notifications["Уведомления"]
    end

    subgraph Finance["Финансовый контур"]
        Treasury["Казначейство"]
        DDS["Доходы / расходы"]
        FinanceView["Финансы"]
        Economy["Экономика"]
    end

    Companies --> Leads
    Companies --> Projects
    Users --> Projects
    Users --> Tasks

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
    Messenger --> Notifications
    Mail --> Outgoing
    Outgoing --> Files
    DocRegistry --> Files
    Contracts --> Files

    Payments --> Treasury
    Treasury --> DDS
    DDS --> FinanceView
    DDS --> Economy
    Payments --> Customer

    Files --> Customer
    Outgoing --> Customer
    Gantt --> Customer

    Companies --> Executor
    Users --> Executor
    Companies --> Customer
    Users --> Customer
```

## Краткая Логика Связей

- `Лиды` являются входом в воронку и при успешной квалификации переходят в `Сделки / проекты`.
- `Сделка / проект` является центральной сущностью, к которой привязаны товары, этапы, договоры, оплаты, задачи, документы и исходящие письма.
- `Контрактация` связывает этапы, товары и договорный контур, после чего переходит в слой `Исполнения`.
- `Исполнение / De facto` управляет назначениями исполнителей, рабочими сроками, договорными сроками, подзадачами и gantt-представлениями.
- `Панель исполнителя` показывает только назначенные пользователю объекты, товары и подзадачи.
- `Кабинет заказчика` строится на данных проекта, оплат, gantt, документов и исходящих писем, видимых заказчику.
- `Казначейство`, `Доходы / расходы`, `Финансы` и `Экономика` образуют единый финансовый контур, связанный с платежами и проектами.
- `Реестр документов`, `Каталог файлов`, `Исходящие письма` и `Почта` формируют единый документный и коммуникационный слой.

## Где Использовать Эту Диаграмму

- в `docs/PROJECT_OVERVIEW.md` как верхнеуровневую карту модулей;
- в `docs/TECHNICAL_SPECIFICATION.md` как схему предметного контура;
- в презентационных и договорных материалах как краткое описание состава платформы.
