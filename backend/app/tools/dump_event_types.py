#!/usr/bin/env python3
"""
Автогенератор каталога событий Event Bus v2.

Что делает:
  • грепит весь backend/app/ AST-парсером;
  • находит ВСЕ вызовы `emit_event(...)`, `emit_event_safe(...)`,
    `dispatch_before("...")`, `dispatch_after(..., "...")`;
  • находит все декораторы `@on("...")`;
  • извлекает строковый event_key из аргументов;
  • группирует по entity_type / action / phase;
  • складывает итог в `docs/events.json`.

Зачем: единая «карта событий» проекта без DB-таблицы. PR ревьюится по
файлу, любой разработчик одной командой видит «какие у нас события и
кто их обрабатывает». Полностью read-only — никаких UI-настроек.

Запуск:
    cd backend && python -m app.tools.dump_event_types
        → пишет ../docs/events.json + краткий отчёт в stdout.

CI-режим (валидация без записи):
    python -m app.tools.dump_event_types --check
        → exit 1 если есть рассинхрон со committed events.json.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


# ────────────────────────────────────────────────────────────────────
# Public types
# ────────────────────────────────────────────────────────────────────

@dataclass
class EventRecord:
    """Сводная запись по одному event_key."""

    event_key: str
    entity_type: str
    action: str
    phase: str  # 'before' | 'after' | 'other'
    emitted_from: List[str] = field(default_factory=list)
    handlers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "event_key": self.event_key,
            "entity_type": self.entity_type,
            "action": self.action,
            "phase": self.phase,
            # payload_version всегда 1 в v1-эре. Когда схема payload
            # backwards-incompatibly изменится — bump'нём вручную здесь
            # и в коде emit_event(payload_version=2, ...). Подписчик
            # сравнивает с своим manifest, отказывается обрабатывать
            # неизвестную мажорную версию.
            "payload_version": 1,
            "emitted_from": sorted(set(self.emitted_from)),
            "handlers": sorted(set(self.handlers)),
        }


# ────────────────────────────────────────────────────────────────────
# Parsing
# ────────────────────────────────────────────────────────────────────

# Функции, у которых ПЕРВЫЙ positional аргумент — event_key.
# Пример: dispatch_before("contract.before_status_change", ctx)
POSITIONAL_FIRST: Set[str] = {"on"}

# Функции, у которых event_key — это ВТОРОЙ positional (после db).
# Пример: dispatch_after(db, "contract.after_status_change", ctx)
POSITIONAL_SECOND: Set[str] = {"dispatch_after"}

# Функции, где event_key — первый позиционный, но из dispatch-семьи.
# dispatch_before(event_key, ctx) — без db.
DISPATCH_FIRST: Set[str] = {"dispatch_before"}

# Функции, у которых event_key передаётся как keyword `event_type=`.
# Пример: emit_event(db, event_type="deal.after_create", ...)
KEYWORD_EVENT_TYPE: Set[str] = {
    "emit_event",
    "emit_event_safe",
    "emit_batch_event",
    "emit_batch_event_safe",
}


def _parse_event_key(key: str) -> Tuple[str, str, str]:
    """Разбирает 'deal.before_status_change' → ('deal', 'status_change', 'before')."""
    if "." not in key:
        return (key, "", "other")
    entity, action_part = key.split(".", 1)
    if action_part.startswith("before_"):
        return (entity, action_part[len("before_"):], "before")
    if action_part.startswith("after_"):
        return (entity, action_part[len("after_"):], "after")
    if action_part.startswith("batch_"):
        # batch_imported / batch_sent — отдельная фаза, чтобы подписчик
        # понимал «это композитное событие с массивом items».
        return (entity, action_part[len("batch_"):], "batch")
    return (entity, action_part, "other")


def _extract_str_arg(node) -> Optional[str]:
    """Возвращает строковое значение из ast-узла, если это литерал."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _scan_file(path: str, rel_to: str) -> List[Tuple[str, str, str]]:
    """
    Возвращает список (event_key, location, kind) для одного файла.
    kind: 'emit' | 'dispatch' | 'handler'
    """
    # utf-8-sig — корректно глотает BOM (U+FEFF), который в некоторых
    # моделях/роутерах добавил Windows-редактор (treasury_transaction.py,
    # finance.py и т.п.). Чистый 'utf-8' на этих файлах роняет ast.parse.
    try:
        with open(path, encoding="utf-8-sig") as fh:
            tree = ast.parse(fh.read(), filename=path)
    except (OSError, SyntaxError) as exc:
        print(f"  WARN: cannot parse {path}: {exc}", file=sys.stderr)
        return []

    rel = os.path.relpath(path, rel_to).replace("\\", "/")
    results: List[Tuple[str, str, str]] = []

    for node in ast.walk(tree):
        # Декоратор @on("...")
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            for deco in node.decorator_list:
                # @on("...")  или  @on("...", priority=...)
                if not isinstance(deco, ast.Call):
                    continue
                func = deco.func
                func_name = (
                    func.id if isinstance(func, ast.Name)
                    else func.attr if isinstance(func, ast.Attribute)
                    else None
                )
                if func_name != "on" or not deco.args:
                    continue
                key = _extract_str_arg(deco.args[0])
                if key:
                    loc = f"{rel}:{node.lineno} ({node.name})"
                    results.append((key, loc, "handler"))

        # Вызовы emit_event(...)/dispatch_*(...)
        if isinstance(node, ast.Call):
            func = node.func
            func_name = (
                func.id if isinstance(func, ast.Name)
                else func.attr if isinstance(func, ast.Attribute)
                else None
            )
            if not func_name:
                continue

            loc = f"{rel}:{node.lineno}"

            if func_name in KEYWORD_EVENT_TYPE:
                # event_type=... keyword arg
                for kw in node.keywords:
                    if kw.arg == "event_type":
                        key = _extract_str_arg(kw.value)
                        if key:
                            results.append((key, loc, "emit"))
            elif func_name in DISPATCH_FIRST:
                # dispatch_before("...", ctx) — первый positional
                if node.args:
                    key = _extract_str_arg(node.args[0])
                    if key:
                        results.append((key, loc, "dispatch"))
            elif func_name in POSITIONAL_SECOND:
                # dispatch_after(db, "...", ctx) — второй positional
                if len(node.args) >= 2:
                    key = _extract_str_arg(node.args[1])
                    if key:
                        results.append((key, loc, "dispatch"))

    return results


def collect(app_root: str) -> Dict[str, EventRecord]:
    """Обходит дерево backend/app/** и собирает все упоминания event_key."""
    records: Dict[str, EventRecord] = {}

    for dirpath, dirnames, filenames in os.walk(app_root):
        # Пропускаем cache/venv и сам tools/ (внутри есть «отрицательные»
        # упоминания event_key в строках — например, в этом docstring).
        if "__pycache__" in dirpath or "/.venv" in dirpath:
            continue
        if dirpath.endswith(os.sep + "tools"):
            continue
        for name in filenames:
            if not name.endswith(".py"):
                continue
            full = os.path.join(dirpath, name)
            for key, loc, kind in _scan_file(full, rel_to=os.path.dirname(app_root)):
                entity, action, phase = _parse_event_key(key)
                rec = records.setdefault(
                    key,
                    EventRecord(event_key=key, entity_type=entity, action=action, phase=phase),
                )
                if kind in ("emit", "dispatch"):
                    rec.emitted_from.append(loc)
                elif kind == "handler":
                    rec.handlers.append(loc)
    return records


# ────────────────────────────────────────────────────────────────────
# Output
# ────────────────────────────────────────────────────────────────────

def build_catalog(records: Dict[str, EventRecord]) -> Dict:
    """Финальная JSON-структура: events + статистика."""
    events_sorted = sorted(records.values(), key=lambda r: r.event_key)
    by_entity: Dict[str, int] = {}
    by_phase: Dict[str, int] = {}
    for r in events_sorted:
        by_entity[r.entity_type] = by_entity.get(r.entity_type, 0) + 1
        by_phase[r.phase] = by_phase.get(r.phase, 0) + 1

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "_generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "_generated_by": "backend/app/tools/dump_event_types.py",
        "_warning": (
            "Этот файл — autogen-результат AST-обхода backend/app/. "
            "Не редактируйте руками: при следующем запуске будет перезаписан. "
            "Чтобы добавить событие — emit_event/dispatch_before/dispatch_after или @on в коде."
        ),
        "stats": {
            "total_event_keys": len(events_sorted),
            "by_entity_type": dict(sorted(by_entity.items())),
            "by_phase": dict(sorted(by_phase.items())),
        },
        "events": [r.to_dict() for r in events_sorted],
    }


def write_catalog(catalog: Dict, target: str) -> None:
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)


def print_summary(catalog: Dict) -> None:
    print(f"events:        {catalog['stats']['total_event_keys']}")
    print("by entity:")
    for entity, count in catalog["stats"]["by_entity_type"].items():
        print(f"  {entity:<32} {count}")
    print("by phase:")
    for phase, count in catalog["stats"]["by_phase"].items():
        print(f"  {phase:<10} {count}")


# ────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Не писать файл, exit 1 если каталог отличается от committed.",
    )
    parser.add_argument(
        "--app-root",
        default=None,
        help="Override path to backend/app (default: auto-detect from this file's location).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Override output path (default: ../docs/events.json relative to backend/).",
    )
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))                 # backend/app/tools
    app_root = args.app_root or os.path.dirname(here)                 # backend/app
    backend_root = os.path.dirname(app_root)                          # backend
    repo_root = os.path.dirname(backend_root)                         # crm/Новая папка
    out_path = args.out or os.path.join(repo_root, "docs", "events.json")

    records = collect(app_root)
    catalog = build_catalog(records)

    if args.check:
        if not os.path.exists(out_path):
            print(f"FAIL: {out_path} does not exist; run without --check first", file=sys.stderr)
            return 1
        with open(out_path, encoding="utf-8") as fh:
            committed = json.load(fh)
        # Сравниваем без полей _generated_at (динамическое).
        a = {k: v for k, v in catalog.items() if not k.startswith("_generated_at")}
        b = {k: v for k, v in committed.items() if not k.startswith("_generated_at")}
        if a != b:
            print(f"FAIL: {out_path} is out of sync with code. Re-run without --check.", file=sys.stderr)
            return 1
        print(f"OK: {out_path} matches code ({catalog['stats']['total_event_keys']} events)")
        return 0

    write_catalog(catalog, out_path)
    print(f"wrote {out_path}")
    print_summary(catalog)
    return 0


if __name__ == "__main__":
    sys.exit(main())
