# Event Bus — Покрытие сущностей: спека коллеги vs реализация

**Источники:**
- **Спека:** `docs/EVENTS_ENTITY_REFERENCE.md` (~70 сущностей × до 12 событий = ~600 типов).
- **Реализация:** `docs/events.json` (autogen из кода: `emit_event` / `dispatch_*` / `@on`).

**Легенда статусов:**
- ✅ **Реализовано** — есть эмиссия `emit_event` и/или хендлер `@on` в коде.
- 🟡 **Частично** — есть инфраструктура, но покрыт не весь набор универсальных/доменных событий.
- ⬜ **Не покрыто** — спека описывает, в коде эмиссий нет (расширяется по запросу интегратора).
- ⊘ **Отказались** — кейс закрыт другим механизмом (NotificationRule, EventLog, audit_log).

---

## Сводная статистика (после D + E + F фаз)

| | Спека | У нас сейчас |
|---|---|---|
| Сущностей описано | ~70 | **33 покрыто** (имеют эмиссии или хендлеры) |
| Универсальных событий | ~10/сущность × 70 = ~700 | **117 уникальных event_key** |
| Доменных (специфичных) событий | ~150 | **~40+** (before_render/send/sign/convert/assign/complete/reject/publish/close, after_assign/convert/start/send/link/price_change/sign/inbound/deadline_change/publish/accept/reject/login/logout/role_change/watchers_change/check/inbound × 5, batch_imported) |
| Before-фаза с cancel/mutate | Все сущности | **17 хуков** на 11 сущностях |
| Batch-события | Все entity-domain | `treasury_transaction.batch_imported` под Банк/1С импорт |
| Inbound-приёмники | — | **5: Diadoc / Telegram / 1С / Bank / Госключ** (все HMAC verify + idempotent) |

**Изменения с v2.1 (E-фаза → F-фаза):**
- Сущностей с покрытием: 18 → **33** (+15 новых)
- Event_keys: 73 → **117** (+44)
- F1 (User+Tasks): +13 events (user.{create,update,delete,role_change,login,logout}, task_message.*, task_subtask.*, task.after_watchers_change)
- F2 (Execution): +14 events (stage.*, stage_dependency.after_change, stage_result.{submit,approve,reject}, work_session.{start,stop}, stage_product_assignment.*)
- F3 (1С + counterparty): +12 events (subcontractor_card.*, subcontractor_stage.*, treasury_allocation.*, product_category.*, company_accreditation.{grant,revoke})
- F4 (Inbound + долги outbound): +5 inbound приёмников, +mail_message.after_send, +kp_document.after_create, +legal_case.{create,update}, +task_auction.after_open, +task_auction_bid.after_place, +feed_post.after_create, +gosklyuch.after_inbound, +telegram_message.after_inbound

---

## По доменам

### 1. CRM Core

| Сущность | Спека (события) | У нас | Статус |
|---|---|---|---|
| **`deal`** | universal × 8 + 7 domain (gip_assign, vat_change, activity_add, recalculate_total) | `after_create`, `after_update`, `after_status_change` | 🟡 Базово (3/15). Нет `before_*`, нет `delete`, нет domain-событий. |
| **`lead`** | universal × 8 + 4 domain (convert_to_deal, product_add) | `before_convert_to_deal`, `after_convert_to_deal`, `after_create`, `after_update`, `after_delete`, `after_status_change` | ✅ **Хорошо покрыт** (6/12). Не хватает `before_create/update/delete`. |
| **`company`** | universal × 6 + 6 domain (user_link, document_attach, accreditation_change) | — | ⬜ Не покрыто |
| **`user`** | universal × 6 + 8 domain (login, logout, role_change, avatar_update, 2fa) | — | ⬜ Не покрыто. (Логирование есть в audit_log, но как событие не эмитим) |
| **`role`** | universal × 6 + 2 domain (permission_change) | — | ⬜ Не покрыто |
| **`role_permission`** | universal × 6 | — | ⬜ Не покрыто |
| **`company_user_link`** | universal × 6 | — | ⬜ Не покрыто |
| **`deal_gip`** | universal × 4 (нет update) | — | ⬜ Не покрыто (логируется через deal.after_gip_assign в спеке) |

### 2. Catalog And Products

| Сущность | У нас | Статус |
|---|---|---|
| `product_category` | — | ⬜ |
| `product` | — | ⬜ |
| `deal_product` | — | ⬜ |
| `lead_product` | — | ⬜ |

**Комментарий:** в нашем профиле integration'ов (Telegram, 1С, Банк, Диадок, ЭЦП, Почта, BI, СОДы) каталог продуктов — это в основном **синхронизация в 1С**. Будет точечно покрыт через `product.after_*` под запрос 1С-команды.

### 3. Stages And Execution

| Сущность | Спека | У нас | Статус |
|---|---|---|---|
| **`stage`** | universal × 8 + 10 domain (close, dependency_change, products_change, recalculate_dates, copy) | — | ⬜ |
| **`stage_dependency`** | universal × 6 + propagate | — | ⬜ |
| **`stage_product_link`** | universal × 4 | — | ⬜ |
| **`stage_product_assignment`** | universal × 6 + 6 domain (assign, executor_change, contract_link) | — | ⬜ |
| **`stage_product_subtask`** | universal × 8 | — | ⬜ |
| **`stage_result`** | universal × 6 + 4 domain (submit, review) | — | ⬜ |
| **`work_result`** | universal × 8 + 6 domain (submit, accept, reject) | — | ⬜ |

**Комментарий:** stage-машина — отдельный домен, события не нужны под июльские интеграции напрямую (это внутренняя механика проектов). Открываются по мере необходимости.

### 4. Subcontractors

| Сущность | У нас | Статус |
|---|---|---|
| `subcontractor_card`, `subcontractor_product`, `subcontractor_stage`, `subcontractor_stage_dependency` | — | ⬜ |

**Комментарий:** субподряд активно эволюционирует — события подключим **после** стабилизации модели.

### 5. Contracts And Documents

| Сущность | Спека (события) | У нас | Статус |
|---|---|---|---|
| **`contract`** | universal × 8 + 8 domain (deal_link, subcontractor_link, document_attach) | `before_status_change`, `after_status_change`, `after_create`, `after_update`, `after_delete` | ✅ **Хорошо покрыт** (5/16). **POC v2 — здесь была первая реализация before-фазы.** |
| `contract_document` | universal × 6 + 4 domain (upload, product_link) | — | ⬜ |
| `contract_document_product_link` | universal × 4 | — | ⬜ |
| **`document`** | universal × 8 + 6 domain (send, receive, package_add) | `before_send`, `before_status_change` | 🟡 Только хендлеры готовы, **emit не подключён в роутер** (документация реестра — в работе у другой команды) |
| `document_relation`, `document_package`, `document_package_item` | universal × 4-6 | — | ⬜ |
| **`document_dispatch`** | universal × 4 + 2 domain (send) | — | ⬜ **(критично для Диадок-интеграции — добавим)** |
| `document_dispatch_channel` | universal × 4 | — | ⬜ |
| **`document_template`** | universal × 6 + 2 domain (version_publish) | — | ⬜ |
| `document_template_version` | universal × 6 | — | ⬜ |

### 6. Outgoing Registry

| Сущность | Спека | У нас | Статус |
|---|---|---|---|
| **`outgoing_document`** | universal × 8 + 10 domain (number_generate, render, preview_pdf, version_create, attachment_add) | `before_render`, `after_create`, `after_update`, `after_delete` | 🟡 **Базово** (4/18). Нет `before_send`, `before_status_change`, `version_create`. |
| `outgoing_document_version` | universal × 4 | — | ⬜ |
| `outgoing_document_file` | universal × 4 | — | ⬜ |
| `outgoing_number_sequence`, `outgoing_daily_number_sequence` | universal × 4 | — | ⬜ |

### 7. Finance

| Сущность | Спека | У нас | Статус |
|---|---|---|---|
| `financial_plan` | universal × 8 + 2 domain (payment_status_change) | — | ⬜ |
| `income_expense_entry` | universal × 6 | — | ⬜ |
| **`treasury_transaction`** | universal × 6 + 10 domain (import, allocate, link, ignore, auto_rule_apply) | — | ⬜ **(критично для Банк-интеграции — добавим вместе с emit_batch_event для импорта)** |
| `treasury_allocation` | universal × 6 | — | ⬜ |
| `transaction_allocation` | universal × 6 | — | ⬜ |
| `treasury_auto_rule` | universal × 6 + 2 domain (apply) | — | ⬜ |
| `cb_rate` | universal × 4 | — | ⬜ |
| `penalty_rule` | universal × 6 + 2 domain (apply) | — | ⬜ |

### 8. Tasks And Auctions

| Сущность | Спека | У нас | Статус |
|---|---|---|---|
| **`task`** | universal × 8 + 10 domain (assign, deadline_change, attachment_add, penalty_recalculate) | `after_create`, `after_update`, `after_status_change`, `after_delete`, `after_assign` | ✅ **Лучше всех** (5/18). `after_assign` — критично для Telegram-бота. |
| `task_message` | universal × 6 + 2 domain (attachment_add) | — | ⬜ |
| `task_user_matrix` | universal × 6 + 2 domain (reorder) | — | ⬜ |
| `task_auction` | universal × 8 + 4 domain (publish, close) | — | ⬜ |
| `task_auction_bid` | universal × 6 + 4 domain (accept, reject) | — | ⬜ |
| `tender` | universal × 8 + 4 domain (publish, close) | — | ⬜ |
| `tender_offer` | universal × 6 + 4 domain (accept, reject) | — | ⬜ |

### 9. Communications

| Сущность | Спека | У нас | Статус |
|---|---|---|---|
| `mailbox` | universal × 6 + 2 domain (sync) | — | ⬜ |
| **`mail_message`** | universal × 6 + 10 domain (sync, receive, send, link_entity) | `before_send` (handler-only) | 🟡 **Хендлер готов, emit в роутер не подключён** |
| `chat_conversation` | universal × 6 + 4 domain (member_add/remove) | — | ⊘ (внутренний чат, для внешних подписчиков не нужен) |
| `chat_conversation_member` | universal × 4 | — | ⊘ |
| `global_chat_message` | universal × 6 | — | ⊘ |
| `telegram_connection` | universal × 6 + 2 domain (verify) | — | ⬜ |

### 10. Notifications, Events, Audit

| Сущность | У нас | Статус |
|---|---|---|
| `notification` | — | ⊘ **Покрыто `NotificationRule`** (своя система правил, не дублируем) |
| `notification_delivery` | — | ⊘ |
| `notification_rule`, `notification_subscription`, `notification_preference`, `notification_job` | — | ⊘ |
| `event_log` | (используется самим event bus) | ⊘ |
| `audit_log` | (используется audit-системой) | ⊘ |

**Комментарий:** Спека предлагала «эмитить событие при создании уведомления». Это рекурсия (`notification.after_create` → подписчик → создаёт уведомление → `notification.after_create` → ...). Защищаемся `causation_chain MAX_DEPTH=5`, но **проще не эмитить эти события вовсе** — `NotificationRule` уже решает задачу декларативно.

### 11. Approvals

| Сущность | Спека | У нас | Статус |
|---|---|---|---|
| **`approval_instance`** | universal × 6 + 6 domain (start, complete, reject) | `before_complete`, `before_reject`, `after_start`, `after_complete`, `after_reject` | ✅ **Хорошо покрыт** (5/12). Не хватает `before_start`. |
| `approval_template`, `approval_template_step` | universal × 6 | — | ⬜ |
| `approval_instance_step` | universal × 6 + 4 domain (complete, reject) | — | ⬜ |
| `approval_action_log` | universal × 2 (create только) | — | ⬜ |

### 12. Legal

| Сущность | У нас | Статус |
|---|---|---|
| `legal_case`, `legal_case_event`, `legal_case_event_file`, `legal_case_task` | — | ⬜ |

**Комментарий:** Legal — самостоятельный домен, внешние интеграции не запланированы.

### 13. KP, Uploads, Data Health

| Сущность | Спека | У нас | Статус |
|---|---|---|---|
| `kp_template`, `kp_template_binding` | universal × 6 | — | ⬜ |
| **`kp_document`** | universal × 6 + 4 domain (render, version_create) | `before_render` (handler-only) | 🟡 **Хендлер готов, emit в роутер не подключён** |
| `kp_version` | universal × 4 | — | ⬜ |
| `upload_job` | universal × 6 + 4 domain (process, fail) | — | ⬜ |
| `data_health_issue` | universal × 6 + 4 domain (resolve, reopen) | — | ⬜ |
| `company_accreditation` | universal × 8 | — | ⬜ |
| `company_document` | universal × 6 | — | ⬜ |

### 14. Дополнительные (опц. модели)

| Сущность | У нас | Статус |
|---|---|---|
| `advance_payment`, `inflation_index`, `overhead`, `overhead_allocation`, `pricing_model`, `pricing_quote`, `quality_alert`, `stage_closing`, `wip_monthly` | — | ⬜ **Не активированы в `app.models.__init__`** — события подключим если контуры будут активированы. |

---

## Сводка по приоритетам для июльских интеграций

| Интеграция | Зависит от событий | Покрытие сейчас |
|---|---|---|
| **Telegram** | `task.after_assign`, `task.after_status_change`, `deal.after_status_change`, `lead.after_create` | ✅ Все нужные есть |
| **1С** | `deal.after_*`, `contract.after_*`, `treasury_transaction.batch_imported`, `outgoing_document.after_*`, `product.after_*`, `company.after_*` | 🟡 Deal+contract+outgoing есть; treasury/product/company — нет (добавим под запрос) |
| **Банк** | `treasury_transaction.batch_imported`, `income_expense_entry.after_create` | ⬜ Нужно сделать (batch инфра есть, эмиссий нет) |
| **Диадок** | `document.after_send`, `document.after_status_change`, `document_dispatch.after_*` | 🟡 Хендлеры готовы, эмиссии в роутер — нет |
| **ЭЦП** | `contract.before_send`, `document.before_send`, `outgoing_document.before_send` | 🟡 Two handlers ready, third missing; emit-точки в роутер — нет |
| **Почта** | `mail_message.after_receive`, `mail_message.after_send` | ⬜ Хендлер `before_send` есть, эмиссии нет |
| **BI** | Подписка на ВСЁ через `*.after_*` с JSON-Logic фильтрацией | ✅ Инфра готова, выберут события сами |
| **СОДы (Signal, ProjectPoint, Sarex)** | `document_dispatch.after_send`, `document_dispatch.after_status_change` | ⬜ Нет |

---

## План на оставшиеся недели

**Перед июльским стартом интеграций — точечный sweep:**

1. **Под Банк/1С — финансы:** `treasury_transaction.after_import` + `treasury_transaction.batch_imported` (компоновка через `emit_batch_event` для импорта банк-выписки). ~1 день.
2. **Под Диадок/СОДы — диспатч документов:** `document_dispatch.after_send`, `document_dispatch.after_status_change` + эмиссии в роутер. ~1 день.
3. **Под 1С — каталог:** `product.after_*`, `company.after_*` (только create/update, реже delete). ~0.5 дня.
4. **Под ЭЦП — подписание:** `contract.before_send` + интеграция в роутер. ~0.5 дня.
5. **Под Почта:** `mail_message.after_send`, `after_receive`. ~0.5 дня.

**Итого: ~3-4 дня работы** под уже известный профиль использования. Остальные 50+ сущностей из спеки **сейчас не открываем** — добавятся при появлении конкретного запроса от интегратора (типовая правка = 2 строки `emit_event_safe` в роутере).

---

## Архитектурный комментарий

Подход «**закрывать события по запросу**» оправдан, потому что:

1. **Стоимость добавления события низкая** (2 строки в роутере + autogen каталог обновляется автоматически). Это НЕ как добавление колонки в БД с миграцией.

2. **Outbox пустует — это нормально.** Если событие никто не подписан слушать — outbox-запись просто полежит. Стоимость ноль до тех пор пока worker не запущен (а он у нас по решению юзера на проде не запущен — крутится только локально).

3. **Расширяемость в коде, а не в БД.** Нет миграций при росте каталога — autogen `dump_event_types.py` перегенерирует `events.json` на каждом commit'е.

4. **Совместимость с подписчиком.** Подписчик ВСЕГДА получает `payload_version`, `X-Event-Schema-Version` header и стабильный формат. Если завтра payload эволюционирует — поднимаем `payload_version=2`, подписчик игнорирует неизвестную мажорную версию (см. EVENT_BUS_RESUME_v2.md §3.1).
