# Event Bus — Onboarding для команды интеграции

**Аудитория:** разработчик, который пишет внешнюю интеграцию (Telegram /
1С / Банк / Диадок / ЭЦП / Почта / BI / СОДы) с июля.

**Что обязательно прочитать:** этот документ + `docs/EVENT_BUS_RESUME_v2.md`
(архитектурное резюме) + `docs/events.json` (каталог событий —
**production source of truth**, не правится руками).

---

## 0. TL;DR за 60 секунд

CRM умеет двум типам коммуникации с внешним миром:

1. **Outbound (CRM → внешний сервис):** при бизнес-факте (создание/изменение
   сущности) пишется строка в `event_outbox`, воркер ходит по подпискам
   из `event_subscriptions` и POST'ит JSON с HMAC-подписью.
2. **Inbound (внешний сервис → CRM):** под `/api/v1/integrations/<vendor>`
   живёт приёмник вебхуков. Проверяет HMAC, парсит payload, делает
   CRM-side мутацию, эмитит внутреннее событие (`*.after_inbound`).

Большинство интеграций — **двусторонние**. Telegram и Диадок — точно.
1С и Bank — асимметричные (мы получаем, иногда отдаём).

---

## 1. Какие события у нас есть

Полный каталог — `docs/events.json`. Регенерируется командой:

```bash
cd backend && python -m app.tools.dump_event_types
```

Структура одного события в каталоге:

```json
{
  "event_key": "contract.after_status_change",
  "entity_type": "contract",
  "action": "status_change",
  "phase": "after",
  "payload_version": 1,
  "emitted_from": ["app/routers/contracts.py:605"],
  "handlers": [
    "app/event_handlers/contracts.py:36 (validate_status_transition)"
  ]
}
```

Фазы:
- `before` — синхронный хук **до** мутации. Может вернуть `Cancel`/`Mutate`.
  Использовать для валидаций («нельзя завершить договор без оплат») и
  патчей payload («автозаполнить `closed_at`»). Подписки извне НЕ
  доставляются на before — это in-process only.
- `after` — асинхронная доставка через outbox. Сюда подписываются внешние
  сервисы. Идёт через `event_outbox` → `event_outbox_worker`.
- `batch` — композитное событие на множество записей (`items: [...]`),
  используется при импорте от 1С/банка. Доставляется как одно
  webhook-сообщение.

Если нужного события нет — попросить добавить, это 5 минут (4 строчки
кода в роутере + `dump_event_types` для каталога).

---

## 2. Outbound: написать своего консьюмера

### Шаг 1. Получить или сгенерировать `hmac_secret`

64+ байт random hex. Хранится с обеих сторон — на нашей в
`event_subscriptions.hmac_secret`, у вас — в env вашего сервиса.

### Шаг 2. Зарегистрировать подписку

Через UI Event Bus в админке или напрямую в БД:

```sql
INSERT INTO event_subscriptions (
  id, name, event_type_pattern, target_url, hmac_secret,
  is_active, condition_json
) VALUES (
  '<uuid>',
  'Telegram-канал продаж',
  'deal.after_*',
  'https://your-service.example.com/webhook',
  'a-long-random-hex-string',
  1,
  NULL  -- или JSON-Logic условие, см. ниже
);
```

Поля:
- `event_type_pattern` — glob по `event_key`. Примеры:
  `deal.*` — все события сделок;
  `*.after_create` — все создания;
  `contract.after_status_change` — точное совпадение.
- `target_url` — POST endpoint вашего сервиса.
- `hmac_secret` — для проверки подписи.
- `is_active` — выключатель без удаления.
- `condition_json` — JSON-Logic фильтр поверх payload (см. §4).

### Шаг 3. Принять и проверить

CRM шлёт `POST <target_url>` со следующими заголовками:

| Header | Что внутри |
|---|---|
| `Content-Type` | `application/json` |
| `X-Event-Id` | UUID события (для идемпотентности на вашей стороне) |
| `X-Event-Type` | event_key (`contract.after_status_change`) |
| `X-Event-Schema-Version` | `payload_version` (`1`) |
| `X-Event-Signature` | hex HMAC-SHA256(body, hmac_secret) |
| `X-Subscription-Id` | UUID подписки (для отладки) |

**Обязательная проверка на вашей стороне (Python):**

```python
import hashlib
import hmac

def verify(raw_body: bytes, signature_header: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header.strip())
```

Без подписи или с неверной — **отказываем 401**. Не парсим body раньше
проверки подписи.

### Шаг 4. Идемпотентность

Воркер ретраит при 5xx/timeout (exp.backoff 5→15→45→135→405с, max 5).
Это значит, **одно событие может прилететь 2-5 раз**. Дедуп — на вашей
стороне:

```python
# Минимальный паттерн: храните таблицу processed_events(event_id PRIMARY KEY).
# INSERT OR IGNORE на event_id перед обработкой.
```

Альтернатива — использовать `X-Event-Id` как ключ в Redis с TTL 24 часа.
То же самое делает наш `event_delivery_dedup` для повторных доставок к
нам — паттерн зеркальный.

### Шаг 5. Ответ

- **2xx** — событие принято, воркер пометит `delivered`.
- **4xx** — мы НЕ ретраим (это ваш баг или плохой payload). Событие
  → `failed`, попадает в DLQ-витрину `/integrations/outbox`.
- **5xx / timeout (>10с)** — ретрай с backoff'ом, потом DLQ после
  5 попыток.

---

## 3. Inbound: написать приёмник вебхуков

Каркас и пилот — `backend/app/routers/integrations/diadoc_inbound.py`.

### Структура каждого приёмника

Файл `<vendor>_inbound.py` в `routers/integrations/`. Эндпоинт делает
**ровно 4 шага в одной транзакции**:

1. **Verify HMAC** (fail-closed, 401 при ошибке);
2. **Idempotency dedup** (по `source_type` + `source_id` в нашей БД);
3. **CRM-side mutation** (создание/обновление сущности);
4. **`emit_event_safe`** для внутренних слушателей.

Подключение в `main.py`:

```python
from app.routers.integrations.<vendor>_inbound import router as <vendor>_inbound_router
app.include_router(
    <vendor>_inbound_router,
    prefix="/api/v1/integrations/<vendor>",
    tags=["integrations-<vendor>"],
)
```

Дополнительно: `/api/v1/integrations/` уже в `open_prefixes` AuthMiddleware,
поэтому cookie-auth и CSRF не требуются. Защита — HMAC + IP allow-list на
nginx.

### Шаблон файла (минимальный)

```python
import hashlib, hmac, json, logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.models import <YourCrmModel>
from app.services.event_outbox import emit_event_safe

router = APIRouter()
logger = logging.getLogger(__name__)


def _verify(raw_body: bytes, sig: Optional[str]) -> bool:
    secret = getattr(settings, "<VENDOR>_HMAC_SECRET", "") or ""
    if not secret:
        raise HTTPException(503, "vendor secret not configured")
    if not sig:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig.strip())


class VendorPayload(BaseModel):
    external_id: str
    # ... ваши поля


@router.post("/inbound")
async def inbound(
    request: Request,
    x_vendor_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    raw = await request.body()

    # 1. Подпись
    if not _verify(raw, x_vendor_signature):
        raise HTTPException(401, "invalid signature")

    # 2. Парсинг
    try:
        payload = VendorPayload(**json.loads(raw))
    except Exception as exc:
        raise HTTPException(400, f"invalid payload: {exc}")

    # 3a. Idempotency
    existing = (await db.execute(
        select(<YourCrmModel>).where(
            <YourCrmModel>.source_type == "<vendor>",
            <YourCrmModel>.source_id == payload.external_id,
        )
    )).scalar_one_or_none()
    if existing:
        return {"status": "ok", "deduplicated": True, "id": str(existing.id)}

    # 3b. Мутация
    item = <YourCrmModel>(
        source_type="<vendor>",
        source_id=payload.external_id,
        # ...
    )
    db.add(item)
    await db.flush()

    # 4. Внутреннее событие
    await emit_event_safe(
        db,
        event_type="<entity>.after_inbound",
        entity_type="<entity>",
        entity_id=str(item.id),
        payload={"source": "<vendor>", "external_id": payload.external_id, ...},
        payload_version=1,
    )
    await db.commit()
    return {"status": "ok", "id": str(item.id), "deduplicated": False}
```

### Настройка ENV

В `backend/app/core/config.py` добавить:

```python
<VENDOR>_HMAC_SECRET: str = ""
```

В `.env` на проде:

```
<VENDOR>_HMAC_SECRET=<длинная случайная строка, та же что у вендора>
```

---

## 4. JSON-Logic фильтр подписок (опционально)

Подписка может фильтровать ДОставку по содержимому payload. Это уровень
выше pattern-match — pattern отбирает по типу события, JSON-Logic — по
самому payload.

Поддержанные операторы:
- Сравнение: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Булева логика: `and`, `or`, `!`
- Доступ к payload: `{"var": "field.subfield"}` (dot-path с опциональным default)
- Коллекции: `in` (массив или подстрока), `missing` (поля отсутствуют в payload)

### Примеры

**Только крупные подписанные контракты (>1M ₽):**

```json
{
  "and": [
    {"==": [{"var": "status"}, "signed"]},
    {">":  [{"var": "amount"}, 1000000]}
  ]
}
```

**Только сделки в воронке «Новостройки»:**

```json
{"==": [{"var": "pipeline_code"}, "novostroyki"]}
```

**Лиды из конкретных источников:**

```json
{"in": [{"var": "source"}, ["telegram", "email", "phone"]]}
```

**Что не сработает** (логически некорректный rule) — оценивается в `False`
с предупреждением в логах. Это намеренно: чтобы один битый rule не валил
весь worker.

---

## 5. Simulate endpoint — DRY-RUN перед добавлением подписки

`POST /api/v1/event-bus/simulate` (только для суперюзеров).

Что показывает:
- **Для `before_*`:** запускает все in-process хендлеры в DRY-RUN режиме
  (payload НЕ мутируется). Возвращает финальный результат
  (`Continue` / `Cancel{reason,code}` / `Mutate{patch}`), список сработавших
  и пропущенных хендлеров.
- **Для `after_*` и `batch_*`:** проверяет, какие подписки сработали бы
  (pattern + JSON-Logic) и какие отвалились (с причиной).

### Запрос

```json
POST /api/v1/event-bus/simulate
{
  "event_type": "contract.after_status_change",
  "entity_type": "contract",
  "entity_id": "550e8400-...",
  "payload": {
    "id": "550e8400-...",
    "status": "signed",
    "amount": 1500000,
    "pipeline_code": "novostroyki"
  }
}
```

### Ответ

```json
{
  "event_type": "contract.after_status_change",
  "would_proceed": true,
  "matched_subscriptions": [
    {
      "id": "sub-1", "name": "BI: крупные контракты",
      "condition_json": "{\"and\":...}",
      "match_reason": "pattern + condition_passed"
    }
  ],
  "skipped_subscriptions": [
    {
      "id": "sub-2", "name": "Telegram-новостройки",
      "skip_reason": "condition_failed"
    }
  ]
}
```

Используется при отладке: вместо «закинуть тестовое событие через
prod-БД и смотреть outbox» можно spot-check'нуть конкретный payload.

---

## 6. Best practices

### 6.1. Никогда не доверяйте payload без подписи

Подпись проверяется ВСЕГДА. Даже на test sink'е (`/_test/webhook-sink`).
Тащить в продакшен «закомментированную проверку для отладки» — `git revert`
ваш PR.

### 6.2. Принцип единственной правды

Каталог `docs/events.json` — source of truth. Если в нём нет события,
которое вам нужно — пишите PR (роутер + регенерация каталога), не
догадывайтесь по похожему имени.

### 6.3. Версионирование payload

Каждая эмиссия имеет `payload_version` (по умолчанию `1`). При изменении
схемы — bump version, добавьте handler в внешнем сервисе на новую версию,
старую не ломаем. На уровне HTTP — `X-Event-Schema-Version` header.

### 6.4. Идемпотентность с обеих сторон

- **Outbound от нас:** мы пишем `event_outbox.event_id` (UUID) и
  отслеживаем доставки в `event_delivery_dedup`. Один event_id × один
  subscription_id = одна доставка (≥1, но эффективно 1 после нашего
  fix'а в V1.5).
- **Inbound к нам:** ваш `external_id` храним в `source_id`.
  Повторный POST с тем же external_id → 200 OK + `deduplicated: true`.

### 6.5. Backpressure

Воркер `event_outbox_worker.py` обрабатывает события в строго
последовательном порядке per `(entity_type, entity_id)`. Это значит:
- Внутри одной сделки события не переставляются.
- Между сделками — могут идти в параллель.

Если ваш внешний сервис не справляется — return 503, наш воркер сделает
бэкофф. Не делайте queue-внутри-queue.

### 6.6. Логирование на вашей стороне

Минимум:
- `event_id` каждого принятого вебхука.
- Результат проверки подписи.
- Финальный статус (success / dedup / error + reason).
- Время обработки (для SLA).

---

## 7. Чеклист перед запуском интеграции

- [ ] Прочитан этот документ + `EVENT_BUS_RESUME_v2.md`.
- [ ] Получен `hmac_secret` от админа CRM (или отдан свой для inbound).
- [ ] Выбраны event-key'и по каталогу `docs/events.json`.
- [ ] Написана подписка/приёмник по шаблону.
- [ ] Проверка HMAC — first thing в обработчике, fail-closed.
- [ ] Идемпотентность по `event_id` (outbound) или `external_id` (inbound).
- [ ] DRY-RUN: прогнан 5+ типичных payload'ов через `/simulate`.
- [ ] Стенды: тест в test-контуре, потом прод.
- [ ] Мониторинг: `/integrations/outbox` для DLQ, логи на вашей стороне.
- [ ] Документация: пара экранов README в репозитории интеграции с
      описанием маппинга event_key → action в вашей системе.

---

## 8. Контакты и эскалация

- **Архитектурные вопросы (новые события / новые сущности):** см.
  `EVENTS_API.md` (оригинальная спека), `EVENT_BUS_RESUME_v2.md` (как
  реализовано). Изменения проходят PR-ревью.
- **Прод-проблемы доставки:** `/integrations/outbox` (UI Event Bus).
  Видно failed / dlq / scheduled события и их payload.
- **Поломанная подпись / 401:** проверить `hmac_secret` и порядок байт.
  Часто — забытый `gzip`/`encoding` на стороне отправителя.
- **Бесконечный retry / circular events:** проверить causation_chain в
  payload, MAX_DEPTH=5 нас защищает от бесконечности, но первопричина —
  это ваш код, который эмитит событие в ответ на доставку.

---

## 9. Roadmap (что появится позже)

- **Manifest подписок** — декларация схемы payload, которую ожидает
  подписка. Защищает от приёма несовместимой версии. Добавится после
  первой схемной эволюции (v2.0+).
- **Replay events** — кнопка «переотправить событие N» в UI. Сейчас есть
  retry для failed, replay для delivered будет под отладку.
- **GraphQL-подписки** — пока не планируется; HTTP-webhook достаточен.

---

**Версия документа:** v2.1 (после фазы E — pilot inbound).
**Источник правды по событиям:** `docs/events.json` (auto-generated).
