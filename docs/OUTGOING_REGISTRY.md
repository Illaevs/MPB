# Реестр исходящей документации (направляемой)

Документ описывает модуль исходящей документации в CRM. Модуль предназначен для подготовки писем, ведения версий и хранения PDF/приложений в файловом хранилище (local или Яндекс.Диск). Отправка по email пока не реализована. Контроль статусов отправки и пачек ведется в модуле "Консолидированный реестр документации" (статусы: проект/направлен/получен/архив; каналы: Почта РФ/курьер/эл. почта/ЭДО).

## 1. Назначение

- Формирование карточки исходящего письма.
- Автоматическое присвоение исходящего номера.
- Генерация PDF-версий на основе шаблона (HTML → PDF).
- Хранение PDF и приложений в файловом хранилище.

## 2. Жизненный цикл письма

1. Создать карточку письма.
2. При необходимости загрузить приложения.
3. Нажать "Создать версию" — система сформирует PDF и сохранит его в историю.

Согласование и отправка по email будут добавлены позже.

## 3. Поля карточки

Обязательные:
- **Адресат** (`recipient_company_id`)
- **Тема письма** (`subject`)

Опциональные:
- **Дата письма** (`letter_date`), если не указана — используется текущая.
- **Привязка к сделке** (`deal_id`)
- **Текст письма** (`body`)
- **Список приложений** (`attachments_list`)
- **Статус** (`status`, пока используется `draft`)
- **Файлы приложений** (`attachments_files[]`)

## 4. Нумерация

Формат исходящего номера: `[number/YYYY-MM]`.
- Стартовый номер задается в `OUTGOING_NUMBER_START` (по умолчанию 1193).
- Следующий номер = max(outgoing_number_seq) + 1.

Пример: `1100/2026-01`.

## 5. Версии и PDF

- Версия создается кнопкой "Создать версию".
- PDF формируется из HTML-шаблона (xhtml2pdf).
- PDF сохраняется как **OutgoingDocumentVersion** и доступен по ссылке (в local-режиме через `/api/v1/storage/download`).

## 6. Хранение в файловом хранилище

Для каждого письма создается отдельная папка:
```
{ROOT}/Outgoing/{outgoing_number}/
  Attachments/
  Versions/
```

- `ROOT` = `STORAGE_LOCAL_ROOT` (local) или `YANDEX_ROOT_PATH` (yandex).
- В `Attachments` сохраняются файлы приложений.
- В `Versions` сохраняются PDF-версии.

## 7. Уведомления

- Создание письма и создание версии пишут события `outgoing.create` и `outgoing.version`.
- По умолчанию уведомляются ГИПы сделки (in-app).
- Правила, подписки и тихие часы настраиваются через систему уведомлений.

## 8. Сущности

### OutgoingDocument
- id (uuid)
- outgoing_number_seq (int)
- outgoing_number (string)
- recipient_company_id (uuid)
- deal_id (uuid, nullable)
- letter_date (date)
- subject (string)
- body (text)
- attachments_list (text)
- status (draft)

### OutgoingDocumentVersion
- id (uuid)
- document_id (uuid)
- version_number (int)
- status (draft)
- created_at (datetime)
- created_by (string)
- comment (text)
- pdf_public_url (string)

### OutgoingDocumentFile
- id (uuid)
- document_id (uuid)
- version_id (uuid, nullable)
- file_type (attachment | pdf)
- file_path (string)
- file_name (string)
- public_url (string)

## 9. API

| Метод | URL | Параметры | Примечание |
| --- | --- | --- | --- |
| GET | `/api/v1/outgoing-registry` | `recipient_company_id?`, `deal_id?`, `search?` | Список писем |
| GET | `/api/v1/outgoing-registry/{id}` | `id` (path) | Детали письма + версии/файлы |
| POST | `/api/v1/outgoing-registry` | form: `recipient_company_id`, `letter_date?`, `deal_id?`, `subject`, `body?`, `attachments_list?`, `status?`, `attachments_files[]?` | Создание |
| PUT | `/api/v1/outgoing-registry/{id}` | `id` (path) + тело | Обновление |
| POST | `/api/v1/outgoing-registry/{id}/attachments` | form: `attachments_files[]` | Добавить файлы |
| POST | `/api/v1/outgoing-registry/{id}/versions` | form: `comment?`, `created_by?` | Создать PDF-версию |

## 10. Связь с консолидированным реестром

- Реестр исходящих писем остается специализированным модулем подготовки и версионности писем.
- Контроль статусов "направлен/получен/архив", связей документов и отправок по каналам ведется в консолидированном реестре.
- Исходящее письмо может попадать в консолидированный реестр как документ типа `outgoing_letter`.

## 11. Что отложено

- Отправка по email.
- Согласование (1-ступенчатое).
- Каналы отправки (курьер/почта/СДЭК) и трекинг внутри карточки исходящего письма.
