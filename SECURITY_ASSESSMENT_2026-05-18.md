# Security Assessment — CRM/ERP «for-apps.ru»

- **Дата:** 2026-05-18
- **Аудитор:** автоматизированный аудит (статический разбор кода + верификация)
- **Объём:** backend (FastAPI), frontend (Vue 3), mobile (Flutter), деплой/инфраструктура, артефакты репозитория
- **Метод:** статический анализ исходного кода с прямой верификацией ключевых находок; динамическая проверка на `test_portal` — на этапе верификации фиксов
- **Предыдущий аудит:** `AUDIT_REPORT.md` (2026-02-15) — устарел, см. раздел 2

> Прим.: живые секреты и реальные данные (`backend/.env`, `crm.db`, `_exports/`,
> deploy‑тарболы) по согласованию **только документируются** (раздел 7), файлы не
> изменяются. По коду — устраняются все подтверждённые находки.

---

## 1. Резюме

Архитектура аутентификации и сессий в целом сильная (JWT с фиксированным
алгоритмом, PBKDF2‑SHA256 390k + сравнение в постоянное время, обязательная 2FA на
уровне middleware, hard‑fail при слабом `SECRET_KEY`, ротация refresh‑токенов,
секционный RBAC с учётом метода запроса). Однако **авторизация на уровне
объекта (object‑level) систематически отсутствует на путях доступа к файлам**, что
даёт любому аутентифицированному пользователю чтение всего файлового хранилища
организации. Это — главный системный риск.

| Severity | Кол-во | Находки |
|---|---|---|
| CRITICAL | 2 | C1 (arbitrary file read), C2 (экспозиция секретов/данных) |
| HIGH | 6 | H1 HTML→PDF LFR/SSRF, H2 rate‑limit bypass, H3 IDOR на download, H4 деградация security‑store, H5 CVE зависимостей, H6 хэш суперюзера в репо |
| MEDIUM | 7 | M1 валидация загрузок, M2 /static stored‑XSS, M3 IDOR approvals, M4 login‑lockout/spray, M5 frontend XSS, M6 subprocess без timeout, M7 overwrite/size |
| LOW/INFO | 7 | L1 /test, L2 edit_assigned→edit_all, L3 billion‑laughs, L4 telegram secret в URL, L5 CORS regex, L6 mobile cleartext, L7 nginx |

---

## 2. Статус находок прошлого аудита (2026-02-15)

| ID | Прошлая находка | Статус сейчас | Пруф |
|---|---|---|---|
| C-01 | Битый `schemas/event_log.py` | **Resolved** | файл удалён; импортов `app.schemas.event_log` нет |
| C-02 | Секреты в `.env` | **Open** | см. C2 — живые токены в `backend/.env` |
| C-03 | Path traversal в `storage.py` (`startswith`) | **Resolved** | `storage.py:62-88` — `resolve()`+`relative_to()` |
| C-04 | Отключённая валидация скачивания | **Resolved** | `document_registry.py:96-104,606,624` — `_validate_channel_file_path` |
| C-05 | Нет RBAC на мутациях | **В основном resolved** | `main.py:196-241` секционный RBAC с учётом метода; per‑object — см. C1/H3 |

Вывод: критические дефекты прошлого аудита по коду закрыты, **кроме экспозиции
секретов**. Но выявлен новый системный класс — отсутствие object‑level авторизации.

---

## 3. CRITICAL

### C1 — Неограниченное чтение файлового хранилища (broken object‑level authorization / arbitrary file read)
- **Severity:** CRITICAL (CVSS ~8.7, AV:N/PR:L/S:C — горизонтальный обход в пределах всей системы)
- **Где:**
  - `app/routers/storage.py:58-95` `GET /api/v1/storage/download?path=` (подтверждено чтением кода)
  - `app/routers/executor.py:553-625` `/executor/storage/{list,download,upload,delete,create-folder,publish}`
  - `app/routers/files_catalog.py:139-358` `list/upload/move/delete/download`
- **Вектор:** `path` полностью контролируется клиентом (`Query`/`Form`). Единственная
  защита — router‑level `require_any_section_access(*AUTHENTICATED_SECTION_KEYS)`
  (`main.py:208,212,233`), т.е. «аутентифицирован + есть ЛЮБОЕ из ~30 секционных
  прав». Проверки принадлежности файла записи/пользователю нет. `_local_path`
  ограничивает только корнем `STORAGE_LOCAL_ROOT`, но не сужает внутри него.
- **Impact:** пользователь с минимальными правами (напр. только `leads` read)
  читает **любой файл всей организации** — договоры, юр.документы, аккредитации,
  вложения почты, исходящие письма, вложения чатов. Для каталога возвращается ZIP
  (`storage.py:74-86`) → массовая выгрузка деревьев. `executor`/`files_catalog`
  write дополнительно дают **перезапись** и **рекурсивное удаление** (`shutil.rmtree`)
  чужих файлов между модулями (деструктивная потеря данных). `storage.get_download_href`
  (`storage.py:240-242`) — общий сток: ссылки из legal_work/accreditations/
  document_registry/outgoing_registry ведут именно сюда.
- **Fix:** не отдавать файлы по сырому клиентскому `path`. Отдавать только через
  record‑scoped эндпойнты: загрузить запись из БД → проверить
  `read_all/read_assigned` + `allowed_deal_ids`/ownership для конкретной записи →
  читать серверно‑производный путь. `/storage/download`, executor/files_catalog
  raw‑path — ограничить суперпользователем или убрать; мигрировать вызовы на
  авторизованные per‑record эндпойнты. Эталон корректной реализации —
  `customer_portal.py:217-382` (строгое scoping по сделке/компании).

### C2 — Экспозиция секретов и реальных данных в рабочем дереве *(документируется, не изменяется)*
- **Severity:** CRITICAL
- **Где / что:**
  - `backend/.env` — живые `YANDEX_TOKEN`, `YANDEX_OAUTH_CLIENT_SECRET`,
    `DADATA_TOKEN`; слабый `SECRET_KEY=change-me-in-prod`.
  - `crm.db` (1.5 МБ, корень) — **реальные данные**: 7 пользователей включая
    `SuperUser` (`dlinfo0@inbox.ru`) и реальные e‑mail людей, полные PBKDF2‑хэши
    паролей, 60+ бизнес‑таблиц (contracts, deals, finance, legal_cases, companies).
  - `update_superuser.sql` — PBKDF2‑хэш пароля суперпользователя открытым текстом.
  - Дубли БД/исходников/секретов в `_exports/crm-sanitized-*`, `.codex_deploy/*.tgz`,
    `frontend-dist-deploy.tar`, `__tmp_approvals_backend_deploy.tar`; раздаётся
    коллегам по `SETUP_COLLEAGUE.md`.
- **Impact:** офлайн‑перебор хэшей всех пользователей (вкл. суперюзера),
  компрометация почтового/Dadata доступа по токенам, подделка JWT при слабом
  `SECRET_KEY`, утечка всей бизнес‑базы и PII.
- **Runbook (выполняется владельцем, вне правок кода):**
  1. Ротировать: Yandex OAuth client secret + токен, Dadata token, `SECRET_KEY`
     (≥64 случайных байт; смена инвалидирует все сессии — ожидаемо).
  2. Принудительный сброс паролей всех учёток (хэши считать скомпрометированными),
     особенно `dlinfo0@inbox.ru`.
  3. Убрать `crm.db`, `*.sql` с хэшами, `_exports/`, deploy‑тарболы из рабочего
     дерева и каналов раздачи; хранить секреты вне репозитория (env/secret‑manager).
  4. Для раздачи коллегам — только санитизированный дамп без реальных PII/хэшей.

---

## 4. HIGH

### H1 — Инъекция HTML в рендер PDF/DOCX → чтение локальных файлов и SSRF
- **Где:** `app/routers/outgoing_registry.py:1840` (`pisa.CreatePDF` без `link_callback`),
  непросанитизированный путь `:2645-2649`, `:2722`, `:682-688`; эндпойнт
  `POST /editor/preview-pdf` (~`:3894`, только `Depends(CurrentUser)`, без section‑write).
- **Вектор:** структурный `rich_text_block.attrs.html` / v2 `editable_regions.body`
  не проходит `_sanitize_html` (в отличие от legacy `_render_company_html:1869`) и
  попадает в xhtml2pdf без `link_callback`. Payload `<img src="file:///etc/passwd">`
  или `http://169.254.169.254/...` → чтение локальных файлов в PDF / SSRF к
  внутренним/метадата‑эндпойнтам.
- **Fix:** прогонять весь пользовательский HTML документов через существующий
  `_sanitize_html` до всех путей рендера; передать строгий `link_callback`
  (запрет `file:`, не‑allowlist хостов, internal‑IP).

### H2 — Обход API rate‑limit через подделываемый `X-Forwarded-For`
- **Где:** `main.py:135-143` `_api_rate_limit_client_key` — берёт `X-Forwarded-For.split(",")[0]`.
- **Вектор:** клиент отправляет произвольный `X-Forwarded-For` на каждый запрос →
  бесконечно новые бакеты → единственная глобальная объёмная защита (вкл. write‑лимит
  на `/auth/login`, `/verify-2fa`) не работает; enumeration/scraping/брутфорс.
- **Fix:** не доверять `X-Forwarded-For` от клиента; брать реальный peer и доверять
  proxy‑заголовку только от известного nginx (trusted‑proxy список / `request.client`).

### H3 — Отсутствие per‑object авторизации на download‑эндпойнтах (IDOR)
- **Где:** `mail.py:376-502` (чужой почтовый ящик по message_id — нет проверки
  владельца ящика), `outgoing_registry.py:4605-4653` (минует `_get_accessible_outgoing_document`),
  `legal_work.py:436-452`, `accreditations.py:348-366`, `document_registry.py:593-608`.
- **Impact:** межзаписное чтение в пределах секции (письма, исходящие, юр.файлы,
  аккредитации) по перебору id.
- **Fix:** в каждом — загрузить запись, разрешить владеющую сделку/компанию/ящик,
  применить тот же `read_all/read_assigned`+`allowed_deal_ids`/owner, что в
  `document_registry.py:698-706` / `outgoing_registry.py:3488-3495`.

### H4 — Тихая деградация security‑store до in‑memory (нет Redis)
- **Где:** `app/services/auth_security_store.py`; `config.py:115 REDIS_URL=""` (в
  `.env` не задан).
- **Вектор:** без Redis блэклист токенов/logout, «отзыв всех сессий»,
  login‑throttle, лимит попыток 2FA, API‑rate‑limit — per‑process, теряются при
  рестарте и не разделяются между воркерами uvicorn. Refresh‑токен живёт 30 дней и
  фактически не отзывается; logout не инвалидирует токен после рестарта.
- **Fix:** требовать Redis в проде (fail‑fast, если `APP_VARIANT != test_portal` и
  `REDIS_URL` пуст), либо реализовать персистентное/общее хранилище отзыва.

### H5 — Уязвимые версии зависимостей
- **Где:** `backend/requirements.txt`: `python-multipart==0.0.6` (CVE‑2024‑24762,
  ReDoS/DoS при парсинге форм), `fastapi==0.104.1` + старый Starlette
  (CVE‑2024‑47874, DoS multipart без лимита).
- **Fix:** `python-multipart>=0.0.18`, `fastapi>=0.109.1` (Starlette ≥0.36),
  пересобрать lock; smoke‑тест загрузок.

### H6 — Хэш пароля суперпользователя в репозитории
- **Где:** `update_superuser.sql` (часть C2, выделено отдельно).
- **Fix:** удалить файл из дерева/раздачи; ротация пароля суперюзера (см. C2 runbook).

---

## 5. MEDIUM

- **M1 — Непоследовательная валидация загрузок.** `executor.py:595/628`,
  `document_registry.py:559-590`, `legal_work.py:391-433`, `accreditations.py:306-345`,
  `task_messages.py:119-193`, `users.py` avatar/wallpaper — пишут сырой
  `upload.read()` минуя `upload_security` (нет проверки расширения/типа/сигнатуры).
  Хранится активный контент (HTML/SVG/полиглот), который затем читается через C1.
  Локальная ветка `files_catalog.upload` тоже минует `validate_upload_signature`.
  **Fix:** все `UploadFile` — через `validate_upload_metadata`+`validate_upload_signature`.
- **M2 — Stored‑XSS / неаутентифицированная отдача медиа через `/static`.**
  `main.py:243-253`: mount `/static` вне `/api/v1` (AuthMiddleware не защищает);
  блокируются только `/static/avatars/*`, а `/static/wallpapers/*` доступны без
  авторизации. `users.py:226-266` доверяет клиентскому `Content-Type` для
  расширения, без сигнатуры. **Fix:** валидация по магич.байтам; не размещать
  пользовательские медиа под публичным `/static`; `Content-Disposition: attachment`.
- **M3 — IDOR/избыточная экспозиция в approvals.** `approvals.py:654,747,877` —
  `list/get/inbox/start` под `require_any_section_access(*AUTHENTICATED_SECTION_KEYS)`:
  любой залогиненный перечисляет/читает все инстансы согласования организации
  (entity labels, комментарии, action logs, `payload_json`) и может стартовать
  согласование на произвольный `entity_id`. (Действия approve/reject корректно
  ограничены `_ensure_can_act`.) **Fix:** scoping по `involved_by_me`/сущности;
  проверка доступа к `entity_id` в `start_instance`.
- **M4 — Account‑lockout DoS и password‑spray.** `auth.py:256-258` ключ
  throttle = `request.client.host` (за nginx = `127.0.0.1`) + email. Атакующий
  5 неудач → блок e‑mail жертвы на 15 мин (таргетированный DoS логина);
  низко‑интенсивный перебор по множеству e‑mail не ограничивается по источнику.
  **Fix:** ключ от доверенного client‑IP + прогрессивная задержка/CAPTCHA; не
  блокировать жертву по чужим попыткам (учитывать и IP, и аккаунт).
- **M5 — Frontend stored‑XSS.** `frontend/src/views/outgoing/templateV2/EditableRegion.vue:39`
  `innerHTML = html` без DOMPurify (+ `OutgoingTemplateRenderer.vue:48,137`). Вход
  привилегированный, частично смягчён CSP `script-src 'self'`, но `onerror`/`onload`
  срабатывают. **Fix:** `DOMPurify.sanitize` перед `innerHTML` (как в
  `useOutgoingRegistryState.js`). (Mail/Chat — проверено, санитизация корректна.)
- **M6 — subprocess без timeout (DoS).** `outgoing_registry.py:1982,2012,2031,2603`
  (`soffice`/`node`) без `timeout=`; вредоносный документ вешает процесс и воркер
  `run_in_threadpool`. (Командной инъекции нет — list‑args, без `shell=True`.)
  **Fix:** `timeout=` + обработка `TimeoutExpired` + kill осиротевших процессов.
- **M7 — Перезапись и неограниченный размер загрузок.** `storage.py:272-275`
  `write_bytes` без проверки существования; `legal_work/accreditations/
  document_registry/executor` читают `upload.read()` без лимита размера.
  **Fix:** запрет overwrite (уникальный подпуть) + max‑size на всех путях.

---

## 6. LOW / INFO

- **L1** `GET /test` без аутентификации (`main.py:321-324`) — удалить.
- **L2** Для не‑ownable секций (finance, companies, document_registry, mail…)
  `edit_assigned` эквивалентно `edit_all` (`ownership.py:29-40`,
  `permissions.can_edit_record`) — least‑privilege footgun, задокументировать/пересмотреть.
- **L3** Billion‑laughs DoS при разборе загруженного DOCX
  (`document_template_fields.py:681`, `ElementTree`) — привилегированный вход;
  `defusedxml` + лимит размера распаковки.
- **L4** Telegram webhook‑secret в URL‑пути (`telegram_notifications.py:128`) —
  попадает в логи; fail‑closed при пустом секрете (ок). Перенести в заголовок.
- **L5** CORS `allow_origin_regex` `127\\.0\\.0\\.1` (`main.py:172`) — некорректный
  regex; косметика, только dev‑origins.
- **L6** Mobile: нет явного запрета cleartext (`AndroidManifest.xml`); vite dev‑proxy
  `secure:false` (только dev). Зависимости mobile/frontend — без известных CVE.
- **L7** Инфра: `for-apps.ru.conf` — `client_max_body_size 50g`, TLS 1.0/1.1;
  `fix_nginx_assets.sh` снимает `try_files =404`. Ужесточить (TLS 1.2+, лимит тела).

---

## 7. Корректно реализовано (положительное)

JWT с фиксированным алгоритмом (`decode_token` `algorithms=[ALGORITHM]`),
PBKDF2‑SHA256 390k + `hmac.compare_digest`, обязательная 2FA на middleware,
hard‑fail при дефолтном/слабом `SECRET_KEY`, секционный RBAC с учётом HTTP‑метода,
ротация refresh + блэклист, импersonation требует superuser+2FA, отключение 2FA
запрещено политикой; frontend — токены в httpOnly‑cookie + CSRF double‑submit,
DOMPurify на почте/чате корректен, redirect‑sanitization, `rel=noopener`; mobile —
`flutter_secure_storage`, проверяемый TLS, без логирования токенов; нет SQL‑инъекций
(сплошь ORM), нет командной инъекции, ElementTree без внешних сущностей;
`customer_portal` строго scoped по сделке/компании (эталон).

---

## 8. Дорожная карта устранения (по приоритету)

1. **C1** — record‑scoped отдача файлов; закрыть raw‑path `/storage/download`,
   executor, files_catalog.
2. **H1** — санитизация HTML документов + `link_callback` в xhtml2pdf.
3. **H3** — per‑object авторизация на mail/outgoing/legal/accreditation/doc‑registry download.
4. **H2** — доверенный источник client‑IP для rate‑limit.
5. **H4** — fail‑fast на отсутствие Redis в проде.
6. **H5** — апгрейд `python-multipart`/`fastapi`.
7. **M1/M2/M7** — единая валидация и лимиты загрузок; убрать медиа из `/static`.
8. **M3/M4/M5/M6** — scoping approvals; throttle логина; DOMPurify в EditableRegion; timeout subprocess.
9. **L1–L7** — /test, defusedxml, telegram secret в заголовок, CORS regex, nginx/mobile hardening.
10. **C2/H6** — runbook ротации и очистки (владелец, вне правок кода).

## 9. Статус устранения (2026-05-18, по коду)

Живые секреты/данные (C2, H6) — **только задокументированы** (раздел 3, runbook),
файлы не изменялись по согласованию.

| ID | Статус | Что сделано |
|---|---|---|
| C1 | **Fixed+Verified** | Централизованный fail-closed авторизатор `app/services/storage_authz.py`; подключён в `storage.py` `/storage/download`, всех raw‑path эндпойнтах `executor.py` и `files_catalog.py`. Динамически: non‑superuser → 403 на `/etc/passwd`/неизв. префикс; superuser bypass и легитимный секционный доступ сохранены |
| H1 | **Fixed** | Санитайзер `_sanitize_html` применён к `_render_editor_rich_text_html` и v2 `body_html`; добавлен `link_callback`, блокирующий внешние/`file:` ресурсы в xhtml2pdf |
| H2 | **Fixed** | `app/core/request_utils.client_ip` + `TRUSTED_PROXY_HOPS`; rate‑limit middleware больше не доверяет клиентскому `X‑Forwarded‑For` |
| H3 | **Fixed (частично)** | Закрыт через тот же `storage_authz` для path‑based стоков; точечные per‑object проверки в mail/outgoing/legal/accreditation download — остаточная задача (см. ниже) |
| H4 | **Fixed+Verified** | Громкое предупреждение при старте без Redis + opt‑in `REQUIRE_PERSISTENT_SECURITY_STORE` (без падения текущего прод). Предупреждение наблюдалось в логе |
| H5 | **Fixed/Flagged** | `python-multipart` → 0.0.18 (CVE‑2024‑24762). Апгрейд `fastapi`/`starlette` помечен как требующий регрессии в вашем CI (не авто‑бамп) |
| M3 | **Fixed+Verified** | Approvals `get_instance`/`list_instances` ограничены вовлечённостью; non‑superuser не перечисляет чужие согласования |
| M4 | **Fixed** | Ключ throttle логина — от доверенного client‑IP (тот же helper) |
| M5 | **Fixed** | `EditableRegion.vue` — DOMPurify перед `innerHTML` |
| M6 | **Fixed** | `timeout=` + обработка `TimeoutExpired` на всех soffice/node `subprocess.run` |
| M2 | **Fixed** | `/static/wallpapers/*` закрыт; аватар/обои валидируются по магич.байтам |
| M1 | **Fixed (аватар/обои); остальное — остаточно** | Подпись‑валидация добавлена в users avatar/wallpaper; executor/document_registry/legal_work/accreditations/task_messages — остаточная задача |
| L1 | **Fixed** | `/test` удалён (динамически: 404) |
| L3 | **Fixed** | `defusedxml` для разбора DOCX (+ в requirements) |
| L5 | **Fixed** | Исправлен CORS `allow_origin_regex` |
| L7 | **Fixed (частично)** | nginx `ssl_protocols` → TLS1.2/1.3; `client_max_body_size` оставлен (вероятно намеренный для крупных загрузок) |
| L4 | **Принято как остаточное** | Telegram webhook‑secret в URL: fail‑closed при пустом секрете; смена схемы требует перерегистрации webhook (внешняя конфигурация) |

**Остаточные задачи (follow-up, не закрыты в этом проходе):**
- M1 — единая `upload_security` валидация в executor/document_registry/legal_work/
  accreditations/task_messages (механически, но рискованно без регрессии).
- M7 — запрет overwrite + лимит размера на тех же upload‑путях.
- H3 — точечные per‑object проверки владельца в mail/outgoing/legal/accreditation
  download (path‑сток уже закрыт `storage_authz`; это доп. слой).
- H5 — апгрейд fastapi/starlette + прогон вашего CI.
- C2/H6 — ротация секретов и очистка артефактов (владелец, вне правок кода).

## 10. Верификация (выполнено)

- Все изменённые файлы: `py_compile` OK; полный `import main` OK (нет циклов).
- Динамика на изолированном патченном билде (`:8011`, БД `test_portal`):
  L1 `/test`→404; C1 non‑superuser→403 на произвольных/абсолютных путях;
  C1 superuser bypass сохранён; `/auth/session` 200; `approvals/instances` 200
  (scoped). H4 предупреждение — в стартовом логе. Прод‑инстанс пользователя
  (`:8001`) и реальные данные не затрагивались.
