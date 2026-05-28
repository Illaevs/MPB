"""
Минимальный JSON-Logic evaluator для фильтрации подписок Event Bus.

Зачем своя реализация а не библиотека:
  • полный json-logic-py — 100+ операторов, нам нужны 15;
  • dependency-free → меньше supply-chain рисков;
  • маленький aud — легче review/тестировать.

Поддерживаемые операторы:
  • `==`, `!=`, `<`, `>`, `<=`, `>=` — сравнение значений
  • `and`, `or`, `!` (not) — булева логика (массив или унарный)
  • `var` — получение значения из payload по пути
        {"var": "amount"}            → payload["amount"]
        {"var": "deal.title"}        → payload["deal"]["title"]
        {"var": ["amount", 0]}       → payload.get("amount", 0)
  • `in` — вхождение значения в массив:
        {"in": [{"var": "status"}, ["signed", "completed"]]}
  • `missing` — список ключей, которых нет в payload (возвращает массив отсутствующих)

Поведение при ошибке: bezопасно false. Подписчик НЕ получит событие
если правило сломано — это лучше чем спамить webhook'и из-за бага в
condition.

Использование:

    from app.services.json_logic import evaluate

    if evaluate({"==": [{"var": "status"}, "signed"]}, payload={"status": "signed"}):
        deliver(...)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_var(spec: Any, payload: Dict[str, Any]) -> Any:
    """{"var": "path"} или {"var": ["path", default]} или {"var": []} → весь payload."""
    if isinstance(spec, list):
        path = spec[0] if spec else ""
        default = spec[1] if len(spec) > 1 else None
    else:
        path = spec
        default = None
    if not path:
        return payload
    cur: Any = payload
    for part in str(path).split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return default
        else:
            return default
    return cur


def evaluate(rule: Any, payload: Dict[str, Any]) -> bool:
    """Главная точка входа: возвращает bool после оценки правила.

    `rule=None` или пустой словарь → True (нет фильтра = пропускать всё).
    Любая ошибка → False с warning в лог.
    """
    if rule is None or rule == {} or rule == "":
        return True
    try:
        result = _eval(rule, payload or {})
        return bool(result)
    except Exception as exc:
        logger.warning("json_logic evaluation failed: %s; rule=%s", exc, rule)
        return False


def _eval(rule: Any, payload: Dict[str, Any]) -> Any:
    """Рекурсивная оценка одного узла."""
    # Литерал (не dict) — возвращаем как есть.
    if not isinstance(rule, dict):
        if isinstance(rule, list):
            return [_eval(item, payload) for item in rule]
        return rule

    if len(rule) != 1:
        # JSON-Logic требует ровно один оператор на узел. Иначе
        # неоднозначность — считаем правило битым.
        raise ValueError(f"json_logic node must have exactly 1 key: {list(rule.keys())}")

    op, args = next(iter(rule.items()))

    # `var` — единственный «листовой» оператор, не оценивает args
    # рекурсивно (а извлекает значение из payload).
    if op == "var":
        return _get_var(args, payload)

    # Оцениваем аргументы.
    if isinstance(args, list):
        values = [_eval(a, payload) for a in args]
    else:
        values = [_eval(args, payload)]

    # ── Сравнения ────────────────────────────────────────────────
    if op == "==":
        return values[0] == values[1]
    if op == "!=":
        return values[0] != values[1]
    if op == "<":
        return _num(values[0]) < _num(values[1])
    if op == ">":
        return _num(values[0]) > _num(values[1])
    if op == "<=":
        return _num(values[0]) <= _num(values[1])
    if op == ">=":
        return _num(values[0]) >= _num(values[1])

    # ── Булева ───────────────────────────────────────────────────
    if op == "and":
        return all(values)
    if op == "or":
        return any(values)
    if op == "!":
        # Унарный: {"!": x} или {"!": [x]}.
        return not (values[0] if values else False)

    # ── Множества ────────────────────────────────────────────────
    if op == "in":
        # {"in": [needle, haystack]} — есть ли needle в haystack.
        needle, haystack = values[0], values[1]
        if isinstance(haystack, (list, tuple, set, str)):
            return needle in haystack
        return False

    if op == "missing":
        # {"missing": ["key1", "key2"]} → список тех, чего нет/None.
        keys = values if values and isinstance(values[0], (list, tuple)) is False else values[0]
        missing = []
        for key in keys or []:
            if _get_var(key, payload) in (None, "", []):
                missing.append(key)
        return missing

    # Неизвестный оператор — лучше зафейлить громко, чем тихо считать True.
    raise ValueError(f"json_logic: unknown operator {op!r}")


def _num(v: Any) -> float:
    """Coerce к числу для сравнений. None → -inf чтобы любое > None было True."""
    if v is None:
        return float("-inf")
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("-inf")
