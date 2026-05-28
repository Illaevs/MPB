# Documentation Index

Единая точка входа в документацию проекта Nexus Tech CRM.

## Основные Документы
- `README.md` (корень): архитектура, запуск, env-конфигурация, карта модулей.
- `docs/API.md`: входная точка в модульную API-документацию (генерируется из кода).
- `docs/api/INDEX.md`: индекс API-доменов (9 доменов), общие правила auth/errors и карта файлов.
- `docs/INTERNAL.md`: внутреннее устройство, ответственность модулей, обработка ошибок, логирование, ключевые архитектурные паттерны (§9: ACL для child-entity, гибридный поиск, Event Bus v2, feed storage).
- `docs/OPERATIONS.md`: runbook эксплуатации, релизов, инцидентов, backup/restore.

## Доменные И Операционные Документы
- `docs/TECHNICAL_SPECIFICATION.md`: базовое ТЗ на внедрение и адаптацию платформы `Nexus ERP` для договорного использования.
- `docs/WORK_SCHEDULE.md`: Приложение №2 с графиком работ по этапам внедрения.
- `docs/PROJECT_OVERVIEW.md`: бизнес-обзор подсистем и предметной области.
- `docs/DEVELOPER_ARCHITECTURE.md`: понятное описание проекта, модулей и архитектуры процессов для разработчика.
- `docs/MODULE_RELATIONS.md`: Mermaid-диаграмма верхнеуровневых связей между модулями системы.
- `docs/ADMIN_VISUAL_SYSTEM_MAP.md`: визуальная карта системы простым языком для нетехнического администратора.
- `docs/OUTGOING_REGISTRY.md`: детали модуля исходящей документации.
- `docs/DEPLOYMENT.md`: деплой и эксплуатация на VPS.
- `docs/TREASURY_AUTORULES_PROPOSALS.md`: аналитика и предложения по автоправилам казначейства.
- `docs/CONTRIBUTING_AI.md`: правила работы AI-агентов с репозиторием.
- `docs/MOBILE_FLUTTER_MVP.md`, `docs/IOS_CLOUD_BUILD_TESTFLIGHT.md`: проработка мобильного клиента и iOS-сборки.

## Event Bus v2
- `docs/EVENTS_API.md`: публичный API для consumer'ов (подписки, payload, retry, HMAC-подпись).
- `docs/EVENTS_ENTITY_REFERENCE.md`: справочник по сущностям и связанным событиям.
- `docs/events.json`: автогенерируемый каталог типов событий (~140+), читается `event_types.py`.
- `docs/EVENT_BUS_ENTITY_COVERAGE.md`, `docs/EVENT_BUS_GAP_ANALYSIS.md`, `docs/EVENT_BUS_RESUME_v2.md`: инженерные заметки по покрытию сущностей и план развития.
- `docs/INTEGRATIONS_ONBOARDING.md`: подключение нового внешнего consumer'а к Event Bus.

## Корневые Документы (вне `docs/`)
- `SECURITY_ASSESSMENT_2026-05-18.md`: срез безопасности на дату проведения.
- `SETUP_COLLEAGUE.md`: онбординг разработчика с нуля (Windows / Git Bash / venv / npm).
- `CONTRIBUTING_AI.md`: основные правила работы AI-агентов на этом репозитории.

## Сопутствующие Артефакты
- `docs/RESTRUCTURE_MAP.csv`: вспомогательная карта реструктуризации/сопоставления.
- `docs/CODEX_HANDOFF.md`, `docs/CODEX_PROJECT_PROMPTS.md`: handoff-заметки и промпт-артефакты.
- `docs/api/misc.md` (исторический) удалён — все роутеры теперь распределены по 9 доменам.

## Принцип Актуализации
- Изменился endpoint, schema или service-сигнатура -> запустить `python scripts/generate_api_reference.py` (перегенерирует `docs/API.md`), затем `python scripts/split_api_reference.py` (актуализирует `docs/api/*`). Если добавляется НОВЫЙ роутер — сначала добавить его в `DOMAIN_CONFIG` внутри `split_api_reference.py`, иначе он попадёт в `misc`.
- Изменились потоки, ответственность модулей, логирование/ошибки, архитектурные паттерны -> обновить `docs/INTERNAL.md`.
- Появился новый бизнес-модуль или поменялась модель доступа -> обновить `docs/PROJECT_OVERVIEW.md`.
- Изменились команды запуска/переменные окружения -> обновить корневой `README.md`.
- Изменилась поверхность Event Bus -> регенерация каталога (`event_types.py`) + обновление `docs/EVENTS_API.md` / `docs/events.json`.
