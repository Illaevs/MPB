# API Reference (Modular)

Монолитный reference разбит на модульные документы по бизнес-доменам.

Новая точка входа: `docs/api/INDEX.md`.

## Domain Files
- `docs/api/auth.md`
- `docs/api/crm.md`
- `docs/api/finance.md`
- `docs/api/documents.md`
- `docs/api/communications.md`
- `docs/api/legal_compliance.md`
- `docs/api/analytics.md`
- `docs/api/misc.md`

## Regeneration
1. Обновить `docs/API.md` генератором API reference (если менялись роутеры/схемы).
2. Запустить `python scripts/split_api_reference.py` для актуализации модульных файлов.
