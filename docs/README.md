# Documentation Index

Единая точка входа в документацию проекта NMBD Tech CRM.

## Основные Документы
- `README.md` (корень): архитектура, запуск, env-конфигурация, карта модулей.
- `docs/API.md`: входная точка в модульную API-документацию.
- `docs/api/INDEX.md`: индекс API-доменов, общие правила auth/errors и карта файлов.
- `docs/INTERNAL.md`: внутреннее устройство, ответственность модулей, обработка ошибок и логирование.
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

## Сопутствующие Артефакты
- `docs/RESTRUCTURE_MAP.csv`: вспомогательная карта реструктуризации/сопоставления.
- `docs/CODEX_HANDOFF.md`, `docs/CODEX_PROJECT_PROMPTS.md`: handoff-заметки и промпт-артефакты.

## Принцип Актуализации
- Изменился endpoint, schema или service-сигнатура -> обновить `docs/API.md`, затем перегенерировать `docs/api/*` через `python scripts/split_api_reference.py`.
- Изменились потоки, ответственность модулей, логирование/ошибки -> обновить `docs/INTERNAL.md`.
- Изменились команды запуска/переменные окружения -> обновить корневой `README.md`.
