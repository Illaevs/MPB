# Event Bus — Gap Analysis (что ещё покрыть)

**Дата:** 2026-05-27 (после фаз A+B+D+E).
**Цель документа:** аудит всех 84 моделей и 55 роутеров на предмет
эмиссий событий; разделить пробелы на «закрыть до июля», «по запросу»
и «никогда».

---

## 1. Текущее состояние

| | Значение |
|---|---|
| event_keys в каталоге | **73** |
| Покрытых сущностей (есть emit или handler) | **18** из 84 моделей (~21%) |
| Роутеров с эмиссиями | **13** из 55 (24%) |
| Before-хуков | 17 |
| Batch-событий | 1 |
| In-process хендлеров | 24 |

**Покрытые сущности (18):** approval_instance, approval_instance_step,
approval_template, company, contract, deal, document, document_dispatch,
income_expense_entry, kp_document, lead, mail_message, outgoing_document,
product, task, tender, tender_offer, treasury_transaction.

**Роутеры с эмиссиями:** approvals, companies, contracts, deals,
document_registry, finance, income_expense, leads, outgoing_registry,
products, tasks, tenders, event_bus (служебно).

---

## 2. Карта пробелов: roughly 30 непокрытых mutating-роутеров

Подсчёт endpoint'ов, изменяющих данные, без эмиссий:

| Router | Mutating endpoints | Критичность | Кому из 8 интеграций нужен |
|---|---|---|---|
| `users` | 9 | **HIGH** | Telegram (привязка), BI (логин-аналитика), все (профили) |
| `task_messages` | 4 | **HIGH** | Telegram (echo chats), Search (FTS) |
| `task_subtasks` | 4 | MEDIUM | Telegram (мини-уведомления) |
| `subcontractors` | 4 | **HIGH** | Диадок (отсылка контрагентам), 1С (контрагенты) |
| `mail` | 6 | MEDIUM | Mail-сервер (reg.ru), Search |
| `deal_execution` | 7 | **HIGH** | СОДы (Sarex/ProjectPoint) |
| `stages` | 7 | **HIGH** | СОДы (ПД/РД/ВОР/сметы), BI |
| `legal_work` | 10 | MEDIUM | Диадок (юр.документы) |
| `feed` | 9 | LOW | BI (engagement) |
| `task_auctions` | 9 | MEDIUM | Telegram (аукционы ставок) |
| `org_structure` | 4 | LOW | Audit only |
| `result_reviews` | 1 | MEDIUM | СОДы (приёмка работ) |
| `kp` | 5 | MEDIUM | Диадок (отправка КП), BI |
| `roles` | 4 | LOW | Audit only |
| `accreditations` | ? | MEDIUM | Диадок (verify counterparty) |
| `notifications` (rules) | ? | LOW | (внутреннее, anti-pattern) |
| `auth` | 6 | MEDIUM | BI (login analytics), security audit |
| `customer_portal` | ? | LOW | (внутренняя секция, нет внешнего consumer) |
| `workday` | ? | MEDIUM | HR/BI (учёт рабочего времени) |
| `absences` | ? | LOW | HR (внутренний календарь) |
| `profiles` | ? | LOW | (профили читаемы, мутации редки) |

**Итого:** ≈14 роутеров с реальной интеграционной ценностью, **~62 events**
не эмитятся (rough estimate).

---

## 3. Анализ по 8 интеграциям

### 3.1. Telegram (двусторонний)

**Outbound (notifications):** Telegram-бот хочет echo'ить:
- Задачи: ✅ (создание/статус/срок); 🟡 не хватает `task_message.after_create`,
  `task_subtask.after_*`, `task_assignee.after_add`, `task_watcher.after_add`.
- Сделки: ✅ create/status_change; 🟡 не хватает `deal.after_delete`,
  `deal.after_gip_change`.
- Лиды: ✅ полностью.
- Договоры: ✅ полностью + sign.
- Лента: ⬜ `feed.after_post`, `feed_comment.after_create`, `feed_mention.after_create`.
- Аукционы задач: ⬜ `task_auction.after_open/close`, `task_auction_bid.after_place`.
- Логин: ⬜ `user.after_login` (для «вы зашли с нового устройства»).

**Inbound (входящие сообщения):**
- Нет приёмника. Нужен `routers/integrations/telegram_inbound.py` (E2-style),
  который принимает payload Telegram Bot API, идентифицирует пользователя
  по `chat_id` → создаёт lead/task/message.

### 3.2. 1С (Бухгалтерия 8.3, двусторонняя)

**Outbound:**
- Контрагенты: 🟡 `company` ✅, но нужно `subcontractor_card.after_create/update`
  (это другая модель, аналог поставщиков).
- Каталог: ✅ `product.after_*`; ⬜ `product_category.after_*`.
- Платежи: ✅ `treasury_transaction.after_*` + batch ✅; ⬜ нужно
  `transaction_allocation.after_*` (привязка платежа к договору/счёту —
  критично для 1С-сверки!).
- Расходы/доходы: ✅ `income_expense_entry.after_*`.
- Договоры: ✅.

**Inbound:**
- Нет приёмника. Нужен `routers/integrations/onec_inbound.py` для
  получения изменений из 1С (контрагент изменился, платёж обновлён).

### 3.3. Bank (выписки в формате 1С 1.03)

**Inbound:** batch-импорт через `emit_batch_event` ✅ готов; нужен приёмник
`routers/integrations/bank_inbound.py` (или загрузка XML через UI с уже
готовой эмиссией). 

**Outbound:** не требуется (банки → CRM, не наоборот).

### 3.4. Диадок (Контур.Диадок, двусторонняя)

**Outbound:**
- Документы: ✅ `document.before_send`, `document.after_sign`.
- КП: 🟡 только `kp_document.before_render`; ⬜ `kp_document.after_send_to_diadoc`.
- Контракты: ✅ before_sign/after_sign.
- Outgoing (письма): ✅.
- Юр.документы: ⬜ `legal_case.after_create/document_attach`.
- Контрагент в Диадоке: ⬜ `company.after_register_in_diadoc`, нужен для
  привязки.

**Inbound:** ✅ pilot `diadoc_inbound.py` готов (E2).

### 3.5. ЭЦП (внутренняя для физлиц, Госключ)

**Outbound:** ✅ полностью (E1) — document/contract/outgoing × sign.

**Inbound (Госключ callback):**
- Нет приёмника. Нужен `routers/integrations/gosklyuch_inbound.py`
  (когда подпись готова — callback к нам с signature blob'ом).

### 3.6. Почта (reg.ru SMTP/IMAP, свой сервер)

**Outbound:**
- ✅ `mail_message.before_send` (валидация);
- ⬜ `mail_message.after_send` (для индексации/BI/audit);
- ⬜ `mail_message.after_receive` (входящие письма);
- ⬜ `mail_message.after_read` (флаги).

**Inbound:** не нужен — сами читаем через IMAP (`MailSync` service).

### 3.7. BI (TBD стек)

BI читает события и строит дашборды. Что критично:
- Финансы: ✅ полностью.
- Сделки/договоры/лиды: ✅.
- Активность пользователей: ⬜ `user.after_login`, `user.after_logout`,
  `work_session.after_start/stop`.
- Выполнение работ: ⬜ `stage.after_complete`, `stage_result.after_submit`,
  `work_result.after_review`.
- Engagement: ⬜ `feed.after_post/like/comment`.

### 3.8. СОДы (Sarex / ProjectPoint / Signal)

**Outbound:**
- Документы (ПД/РД/ВОР/сметы): ✅ `document.after_*` уже эмитится для
  загруженных в реестр.
- Этапы проекта: ⬜ **критично** — `stage.after_create/status_change`,
  `stage_result.after_submit/approve`, `stage_dependency.after_*`.
- Подрядные этапы: ⬜ `subcontractor_stage.after_status_change`.
- Работы: ⬜ `work_result.after_submit/review`.

**Inbound:** TBD (форматы СОДов ещё не определены).

---

## 4. Рекомендуемая F-фаза (3 спринта)

### F1 — User lifecycle + Task ecosystem (1-1.5 дня)

**Цель:** покрыть всё, что нужно Telegram (главный приоритет).

| Event | Где эмитить | Зачем |
|---|---|---|
| `user.after_create` | `users.py` create_user | Telegram-бот пингует новых юзеров |
| `user.after_update` | `users.py` update_user | Аватар/имя обновились — обновить в Telegram |
| `user.after_delete` | `users.py` delete_user | Отвязать Telegram-чат |
| `user.after_role_change` | `users.py` PATCH role | Audit + права на BI |
| `user.after_login` | `auth.py` login | BI usage analytics |
| `user.after_logout` | `auth.py` logout | (опционально) |
| `task_message.after_create` | `task_messages.py` POST | Telegram echo, FTS index |
| `task_message.after_update/delete` | `task_messages.py` | Telegram edit/delete sync |
| `task_subtask.after_create/update/check/delete` | `task_subtasks.py` | Telegram чек-листы |
| `task_watcher.after_add/remove` | `tasks.py` watcher endpoints | Notify добавленных |

**Итого: ~13 событий.** Бэкенд-эмиссии однострочные.

### F2 — Execution (СОДы + BI) (1.5-2 дня)

**Цель:** покрыть весь execution chain (stages → work → results).

| Event | Где эмитить | Зачем |
|---|---|---|
| `stage.after_create/update/delete/status_change` | `stages.py` | СОДы (ПД/РД/ВОР/сметы), BI |
| `stage_dependency.after_change` | `stages.py` PUT /dependency | СОДы (DAG проекта) |
| `stage_result.after_submit/approve/reject` | `result_reviews.py` | СОДы + BI (приёмка работ) |
| `work_session.after_start/stop` | `workday.py` | BI (рабочее время), 1С (зарплата) |
| `work_result.after_submit/review` | `deal_execution.py` | СОДы, BI |
| `stage_product_assignment.after_create/delete` | `deal_execution.py` | 1С (списание материалов) |

**Итого: ~14 событий.** + 1-2 before-хука валидации (нельзя закрыть этап
без приёмки).

### F3 — 1С + counterparty completion (1 день)

**Цель:** покрыть всё, что нужно для двусторонней 1С-синхронизации.

| Event | Где эмитить | Зачем |
|---|---|---|
| `subcontractor_card.after_create/update/delete` | `subcontractors.py` | 1С (контрагенты) |
| `subcontractor_stage.after_create/status_change` | `subcontractor_stages.py` | СОДы + 1С |
| `transaction_allocation.after_create/delete` | `finance.py` allocation endpoints | **1С (сверка платежей)** |
| `treasury_allocation.after_create/delete` | `finance.py` | 1С |
| `product_category.after_create/update/delete` | `products.py` categories | 1С каталог |
| `company_accreditation.after_grant/revoke/expire` | `accreditations.py` | Audit + Диадок |

**Итого: ~12 событий.**

### F4 — Долги по фронту integrations + inbound приёмники (2 дня)

**Цель:** второй inbound-приёмник по шаблону (после Diadoc) + дополнить
outbound.

| Что | Файл |
|---|---|
| Telegram inbound (echo) | `routers/integrations/telegram_inbound.py` |
| 1С inbound (изменения контрагентов/платежей) | `routers/integrations/onec_inbound.py` |
| Bank inbound (XML 1С 1.03) | `routers/integrations/bank_inbound.py` |
| Госключ callback | `routers/integrations/gosklyuch_inbound.py` |
| Mail send/receive events | `mail.py` |
| KP send events | `kp.py` |
| Legal case events | `legal_work.py` |
| Feed engagement events | `feed.py` (опционально) |
| Task auction events | `task_auctions.py` |

**Итого:** 4 inbound-приёмника + ~15 outbound-events.

---

## 5. Что НЕ делать (anti-patterns)

### 5.1. Никогда

| Сущность | Почему не покрываем |
|---|---|
| `audit_log` | Это сам **журнал** событий. Эмитить event про event = бесконечный цикл. |
| `event_outbox`, `event_subscription`, `event_log`, `event_delivery_dedup` | Внутренние таблицы шины — антипаттерн self-emission |
| `notification`, `notification_delivery`, `notification_job` | Они consumer'ы event'ов; эмитить ради них = циклы (causation_chain нас защищает, но не надо тестировать защиту) |
| `outgoing_daily_number_sequence`, `outgoing_number_sequence` | Счётчики, не бизнес-сущности |
| `data_health_issue` | Внутренний диагностический инструмент |
| `task_user_matrix` | Кэш прав, обновляется триггерами |
| `task_read` | Метаданные чтения, не бизнес-факт |
| `upload_job` | Очередь загрузок, технический внутренник |
| `cb_rate` | Курс ЦБ, downloaded data |
| `chat_conversation` | Метаданные диалогов |

### 5.2. По запросу (когда понадобится конкретному консьюмеру)

| Сущность | Когда добавить |
|---|---|
| `role`, `role_permission` | Когда BI попросит security audit |
| `org_unit` | Когда HR-система понадобится |
| `mailbox` | Когда понадобится сменить mail-провайдера |
| `user_profile`, `user_absence` | Когда HR/calendar integration |
| `support_ticket` | Когда подключится helpdesk-система |
| `feed*` модели | Когда BI попросит engagement |
| `customer_portal_*` | Когда выкатим клиентский портал |
| `penalty_rule` | Admin-config, по запросу |
| `treasury_auto_rule` | Admin-config, по запросу |
| `cb_rate` history | Если BI попросит финансовые отчёты с курсом ЦБ |

---

## 6. Резюме и рекомендация

**Если просто закрыть event bus как тему до июля:**
- Сделать F1 + F3 (≈25 событий, 2-2.5 дня) → покрытие 73 → **~98**.
- Это закроет Telegram, 1С и поднимет общее покрытие до ~85% от спеки
  EVENTS_API.md.

**Если идти на максимум перед стартом интеграций:**
- F1 + F2 + F3 + F4 (~60 событий + 4 inbound приёмника, 5-6 дней) →
  покрытие 73 → **~135**.
- Это «закрытый» вариант — после этого любая из 8 интеграций сможет
  начать работу без бэкенд-обновлений с нашей стороны.

**Если идти минимально — closely-binding:**
- Только то, что попросят интеграторы в первую неделю июля по факту.
- Каждая правка — 30 минут (1-2 файла, регенерация каталога).
- Минус: интегратор ждёт нашего PR, замедление.

### Моё мнение

**Делать F1 сейчас (Telegram + User), F2 — следом за ним (СОДы + BI критичны),
F3 — параллельно с July'ским 1С-онбордингом.** F4 inbound — по факту
запросов вендоров (Telegram/1С точно нужны, Bank/Госключ зависит от их
архитектурных решений).

Это даёт +25-30 событий до конца недели = **общее покрытие ~100 events**
без перегрева кодовой базы.

---

## 7. Метрики после каждой фазы (план)

| Фаза | Events после | Entities | Before-хуки |
|---|---|---|---|
| Сейчас (после E) | 73 | 18 | 17 |
| После F1 | ~86 | 22 | 18 |
| После F2 | ~100 | 27 | 20 |
| После F3 | ~112 | 31 | 21 |
| После F4 | ~127 | 36 | 23 |

Цели измеримые, регенерация каталога — однострочник в CI.
