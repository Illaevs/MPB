"""
Event dispatcher — слой v2 поверх существующего outbox.

Что делает:
  • before-фаза (in-process): декораторно зарегистрированные обработчики
    могут отменить (Cancel) или модифицировать (Mutate) payload до того,
    как роутер совершит бизнес-действие;
  • after-фаза: записывает событие в outbox для внешних подписчиков
    (Telegram, 1С, банк, Диадок и т.д.) И параллельно вызывает
    in-process after-обработчики (например, локальный invalidation
    кэшей, переиндексация поиска и т.п.).

Что НЕ делает (намеренно):
  • не хранит обработчики в БД и не позволяет конфигурировать их через UI.
    Регистрация — декоратор `@on(...)` в коде. Это даёт грепабельность,
    юнит-тесты, ревью PR'ом и нормальный рефакторинг.
  • не делает redirects-таблицу. Если нужно «при условии X — другая
    логика», это `if/else` внутри обработчика, а не запись в БД.

Архитектурные принципы:
  • before-фаза выполняется СИНХРОННО в той же async-транзакции, что и
    бизнес-действие. Cancel прерывает действие, бросая ValueError —
    роутер ловит и возвращает 400.
  • after-фаза тоже синхронна (внутри transaction), но её ошибки
    soft-fail: упавший after-хендлер логируется, но не валит запрос.
    Outbox-запись делается до in-process after-хендлеров, чтобы внешний
    consumer не зависел от стабильности локального хендлера.
  • before-обработчики не должны делать запись в БД. Только валидация
    + мутация payload. Тяжёлая работа — в after.
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import pkgutil
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────
# Public types
# ────────────────────────────────────────────────────────────────────

@dataclass
class EventContext:
    """Контекст события, передаётся всем обработчикам."""

    event_key: str
    entity_type: str
    entity_id: Optional[str]
    payload: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    source: str = "api"  # api / worker / migration / system
    request_id: Optional[str] = None
    # Свободные метаданные для проброса между обработчиками одной фазы.
    # Не уходит в outbox/internal log — только in-process.
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Continue:
    """Обработчик не возражает. Эквивалент `return None`."""
    pass


@dataclass
class Cancel:
    """Обработчик отменяет бизнес-действие. Роутер ловит и возвращает 400.

    `reason` — человекочитаемое объяснение (попадёт в HTTP-ответ).
    `code` — машинный код (для UI-локализации).
    """
    reason: str
    code: Optional[str] = None


@dataclass
class Mutate:
    """Обработчик модифицирует payload до выполнения бизнес-действия.

    Patch применяется к `ctx.payload` через `dict.update`. Несколько
    хендлеров могут мутировать одно и то же поле — побеждает последний
    (по priority — последний вызванный, т.е. с меньшим priority).
    """
    payload_patch: Dict[str, Any]


BeforeResult = Union[Continue, Cancel, Mutate, None]


# Внутренний кортеж в реестре. Зачем явная запись, а не словарь:
# реестр читается на каждый dispatch_*, словари в Python чуть дороже
# по доступу к атрибутам.
_HandlerRecord = Tuple[
    int,  # priority (больше = раньше)
    Callable[[EventContext], Union[BeforeResult, Awaitable[BeforeResult]]],
    bool,  # can_cancel
    bool,  # can_mutate
    str,   # phase: 'before' | 'after'
]


# ────────────────────────────────────────────────────────────────────
# Registry (in-memory, заполняется декоратором @on на import)
# ────────────────────────────────────────────────────────────────────

# event_key → отсортированный по priority desc список обработчиков
_HANDLERS: Dict[str, List[_HandlerRecord]] = defaultdict(list)


def on(
    event_key: str,
    *,
    priority: int = 100,
    can_cancel: bool = False,
    can_mutate: bool = False,
):
    """Декоратор регистрации обработчика на событие.

    Аргументы:
      event_key: ключ события, например 'contract.before_status_change'.
        Фаза вычисляется из имени: если в ключе есть '.before_' — это
        before-обработчик, иначе — after.
      priority: больше — раньше вызывается. По умолчанию 100. Системные
        хендлеры с приоритетом 1000+; пользовательские 100; cleanup —
        ниже 50.
      can_cancel: разрешено ли возвращать Cancel. По умолчанию False —
        случайный Cancel из чужого хендлера не сломает чужой роутер.
        Включается explicit для валидаторов.
      can_mutate: разрешено ли возвращать Mutate. По умолчанию False.

    Один и тот же хендлер можно повесить на несколько event_key —
    просто несколько декораторов.

    Example:
        @on("contract.before_send", priority=100, can_cancel=True)
        async def validate_contract_signers(ctx: EventContext):
            if not ctx.payload.get("signatories"):
                return Cancel("Не указаны подписанты")
            return Continue()
    """
    phase = "before" if ".before_" in event_key else "after"

    def decorator(func: Callable):
        record: _HandlerRecord = (priority, func, can_cancel, can_mutate, phase)
        _HANDLERS[event_key].append(record)
        # Сортируем сразу при регистрации (платим на старте, экономим
        # на каждом dispatch).
        _HANDLERS[event_key].sort(key=lambda r: -r[0])
        logger.debug(
            "registered handler %s.%s on %s (priority=%d, can_cancel=%s, can_mutate=%s)",
            func.__module__, func.__qualname__, event_key, priority, can_cancel, can_mutate,
        )
        return func

    return decorator


# ────────────────────────────────────────────────────────────────────
# Dispatch
# ────────────────────────────────────────────────────────────────────

async def _call(handler, ctx: EventContext):
    """Унифицированный вызов sync/async хендлера."""
    result = handler(ctx)
    if asyncio.iscoroutine(result):
        return await result
    return result


async def dispatch_before_simulate(event_key: str, ctx: EventContext) -> Dict[str, Any]:
    """DRY-RUN версия `dispatch_before` для simulate-endpoint'а.

    Отличия от боевой:
      • НЕ мутирует `ctx.payload` (изменения копятся в отдельный patch);
      • НЕ прерывается на первом Cancel — собирает ВСЕ результаты, чтобы
        UI/диагностика видела «что бы случилось с каждым хендлером»;
      • вернуть структурированный отчёт по каждому хендлеру.

    Возвращает:
        {
          "phase": "before",
          "handlers_invoked": [{handler, priority, can_cancel, can_mutate, result}],
          "final_result": {type: "Cancel|Continue|Mutate", reason?, payload_patch?},
          "would_proceed": bool,
        }
    """
    handlers_invoked = []
    aggregated_patch: Dict[str, Any] = {}
    first_cancel = None
    # Копию payload используем для Mutate-evaluation: следующий хендлер
    # должен видеть изменения предыдущих, как в реальном dispatch.
    sim_payload = dict(ctx.payload)

    for priority, handler, can_cancel, can_mutate, phase in _HANDLERS.get(event_key, []):
        if phase != "before":
            continue
        entry: Dict[str, Any] = {
            "handler": f"{handler.__module__}.{handler.__qualname__}",
            "priority": priority,
            "can_cancel": can_cancel,
            "can_mutate": can_mutate,
        }
        # Если уже был Cancel в более раннем хендлере — все последующие
        # отмечаем как «не вызывались бы». Это match'ит боевую логику.
        if first_cancel is not None:
            entry["result"] = {
                "type": "skipped",
                "reason": "previous handler cancelled",
            }
            handlers_invoked.append(entry)
            continue

        sim_ctx = EventContext(
            event_key=ctx.event_key,
            entity_type=ctx.entity_type,
            entity_id=ctx.entity_id,
            payload=sim_payload,  # этот же dict — следующий хендлер увидит мутации
            user_id=ctx.user_id,
            source=ctx.source,
            request_id=ctx.request_id,
            meta=dict(ctx.meta),
        )
        try:
            raw_result = await _call(handler, sim_ctx)
        except Exception as exc:
            entry["result"] = {
                "type": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }
            handlers_invoked.append(entry)
            continue

        if raw_result is None or isinstance(raw_result, Continue):
            entry["result"] = {"type": "Continue"}
        elif isinstance(raw_result, Cancel):
            if can_cancel:
                entry["result"] = {
                    "type": "Cancel",
                    "reason": raw_result.reason,
                    "code": raw_result.code,
                }
                first_cancel = raw_result
            else:
                entry["result"] = {
                    "type": "ignored_cancel",
                    "reason": raw_result.reason,
                    "note": "handler returned Cancel but can_cancel=False; ignored",
                }
        elif isinstance(raw_result, Mutate):
            if can_mutate:
                # Применяем к нашей копии payload — следующий хендлер
                # увидит изменение, точно как на бою.
                sim_payload.update(raw_result.payload_patch)
                aggregated_patch.update(raw_result.payload_patch)
                entry["result"] = {
                    "type": "Mutate",
                    "payload_patch": raw_result.payload_patch,
                }
            else:
                entry["result"] = {
                    "type": "ignored_mutate",
                    "payload_patch": raw_result.payload_patch,
                    "note": "handler returned Mutate but can_mutate=False; ignored",
                }
        else:
            entry["result"] = {
                "type": "unknown",
                "raw_type": type(raw_result).__name__,
            }
        handlers_invoked.append(entry)

    if first_cancel is not None:
        final = {
            "type": "Cancel",
            "reason": first_cancel.reason,
            "code": first_cancel.code,
        }
        would_proceed = False
    elif aggregated_patch:
        final = {"type": "Mutate", "payload_patch": aggregated_patch}
        would_proceed = True
    else:
        final = {"type": "Continue"}
        would_proceed = True

    return {
        "phase": "before",
        "handlers_invoked": handlers_invoked,
        "final_result": final,
        "would_proceed": would_proceed,
        "effective_payload_after_mutations": sim_payload,
    }


async def dispatch_before(event_key: str, ctx: EventContext) -> BeforeResult:
    """Выполнить все before-обработчики на ключ.

    Возвращает:
      • Cancel(reason) — если хотя бы один обработчик отменил
        (роутер должен бросить HTTPException(400, reason));
      • Mutate(patch) — если кто-то модифицировал payload (в ctx уже
        применено, для удобства возвращаем агрегированный patch);
      • Continue() — все согласны.

    Ошибки внутри обработчиков подавляются и логируются (но не молча —
    через ERROR-level). Альтернатива «упасть на всё» опасна: один сбойный
    обработчик не должен класть production-route.
    """
    if event_key not in _HANDLERS:
        return Continue()

    aggregated_patch: Dict[str, Any] = {}

    for priority, handler, can_cancel, can_mutate, phase in _HANDLERS[event_key]:
        if phase != "before":
            continue
        try:
            result = await _call(handler, ctx)
        except Exception as exc:
            logger.exception(
                "before-handler %s for %s raised: %s",
                getattr(handler, "__qualname__", str(handler)), event_key, exc,
            )
            continue

        if result is None or isinstance(result, Continue):
            continue
        if isinstance(result, Cancel):
            if can_cancel:
                logger.info(
                    "event %s cancelled by %s: %s",
                    event_key, getattr(handler, "__qualname__", "?"), result.reason,
                )
                return result
            logger.warning(
                "handler %s on %s tried to Cancel but can_cancel=False; ignored",
                getattr(handler, "__qualname__", "?"), event_key,
            )
            continue
        if isinstance(result, Mutate):
            if can_mutate:
                # Применяем сразу — следующий обработчик увидит изменения.
                ctx.payload.update(result.payload_patch)
                aggregated_patch.update(result.payload_patch)
            else:
                logger.warning(
                    "handler %s on %s tried to Mutate but can_mutate=False; ignored",
                    getattr(handler, "__qualname__", "?"), event_key,
                )
            continue
        logger.warning(
            "handler %s on %s returned unexpected type %s; ignored",
            getattr(handler, "__qualname__", "?"), event_key, type(result).__name__,
        )

    if aggregated_patch:
        return Mutate(payload_patch=aggregated_patch)
    return Continue()


async def dispatch_after(
    db: AsyncSession,
    event_key: str,
    ctx: EventContext,
    *,
    payload_version: int = 1,
    write_outbox: bool = True,
) -> None:
    """Выполнить after-фазу: outbox + in-process after-обработчики.

    Порядок важен:
      1) outbox-запись (внешним подписчикам) — делается ВСЕГДА, даже
         если in-process хендлеров нет. Иначе будущий внешний consumer
         не получит ретро-событий.
      2) in-process @on(after_*) хендлеры — soft-fail: упавший хендлер
         логируется, остальные продолжают.

    `write_outbox=False` — особый кейс для каскадных в-after-перевозбуждений
    (когда after-хендлер уже сам пишет своё событие; не сохранять
    «обёртку» дважды).
    """
    # 1. Outbox для внешних подписок.
    if write_outbox:
        # Импорт локальный — избегаем циклов при старте.
        from app.services.event_outbox import emit_event

        try:
            await emit_event(
                db,
                event_type=event_key,
                entity_type=ctx.entity_type,
                entity_id=ctx.entity_id or "",
                payload=ctx.payload,
                payload_version=payload_version,
            )
        except Exception as exc:
            # Outbox-запись — критичная. Логируем, но не валим бизнес-flow:
            # сама бизнес-транзакция уже зафиксирована к моменту dispatch_after.
            logger.exception(
                "outbox write failed for %s/%s: %s",
                event_key, ctx.entity_id, exc,
            )

    # 2. In-process after-обработчики.
    if event_key not in _HANDLERS:
        return
    for priority, handler, _, _, phase in _HANDLERS[event_key]:
        if phase != "after":
            continue
        try:
            await _call(handler, ctx)
        except Exception as exc:
            logger.exception(
                "after-handler %s for %s raised: %s",
                getattr(handler, "__qualname__", str(handler)), event_key, exc,
            )


# ────────────────────────────────────────────────────────────────────
# Discovery (auto-import handlers package)
# ────────────────────────────────────────────────────────────────────

def discover_handlers() -> int:
    """Импортирует все модули из `app.event_handlers.*` — это запускает
    регистрацию @on-декораторов. Вызывается из main.py на startup.

    Возвращает кол-во зарегистрированных хендлеров (для логирования).
    Идемпотентно: повторный вызов не дублирует регистрации, т.к. модули
    уже импортированы.
    """
    try:
        from app import event_handlers
    except ImportError:
        logger.info("event_handlers package not found; no handlers registered")
        return 0

    count_before = sum(len(v) for v in _HANDLERS.values())
    for _, module_name, _ in pkgutil.iter_modules(event_handlers.__path__):
        try:
            importlib.import_module(f"app.event_handlers.{module_name}")
        except Exception as exc:
            logger.exception("failed to import event_handlers.%s: %s", module_name, exc)
    count_after = sum(len(v) for v in _HANDLERS.values())
    delta = count_after - count_before
    logger.info(
        "event_dispatcher: discovered %d handlers across %d event keys",
        count_after, len(_HANDLERS),
    )
    return delta


def list_handlers() -> Dict[str, List[Dict[str, Any]]]:
    """Для observability / API endpoint /events/handlers:
    event_key → [{handler, priority, can_cancel, can_mutate, phase}].
    """
    return {
        key: [
            {
                "handler": f"{rec[1].__module__}.{rec[1].__qualname__}",
                "priority": rec[0],
                "can_cancel": rec[2],
                "can_mutate": rec[3],
                "phase": rec[4],
            }
            for rec in handlers
        ]
        for key, handlers in _HANDLERS.items()
    }


def reset_for_tests() -> None:
    """Полная очистка реестра — только для юнит-тестов."""
    _HANDLERS.clear()
