
import datetime as dt
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs' / 'API.md'
OUT_DIR = ROOT / 'docs' / 'api'

DOMAIN_CONFIG = [
    {
        'slug': 'auth',
        'title': 'Identity & Access API',
        'description': 'Аутентификация, пользователи, роли, компании и справочные интеграции.',
        'routers': ['auth', 'users', 'roles', 'companies', 'banks', 'dadata'],
    },
    {
        'slug': 'crm',
        'title': 'CRM Core API',
        'description': 'Сделки, лиды, этапы, задачи, продукты, тендеры и исполнение.',
        'routers': [
            'deals', 'leads', 'stages', 'tasks', 'products', 'task_auctions',
            'tenders', 'deal_execution', 'executor', 'subcontractors',
            'subcontractor_stages', 'subcontractor_products', 'result_reviews', 'kp',
        ],
    },
    {
        'slug': 'finance',
        'title': 'Finance & Billing API',
        'description': 'Финансы, казначейство, ДДС, экономика, штрафы и договоры.',
        'routers': ['finance', 'income_expense', 'economy', 'penalty_rules', 'contracts'],
    },
    {
        'slug': 'documents',
        'title': 'Document Flow & Storage API',
        'description': 'Реестры документов, исходящие, загрузки, хранилище и файловый каталог.',
        'routers': ['document_registry', 'outgoing_registry', 'uploads', 'storage', 'files_catalog'],
    },
    {
        'slug': 'communications',
        'title': 'Communications & Notifications API',
        'description': 'Почта, чаты, тех. поддержка, уведомления и пользовательские предпочтения уведомлений.',
        'routers': [
            'mail', 'task_messages', 'global_chat', 'support', 'notifications',
            'notification_rules', 'notification_preferences', 'notification_subscriptions',
        ],
    },
    {
        'slug': 'legal_compliance',
        'title': 'Legal & Compliance API',
        'description': 'Юридическая работа и аккредитации.',
        'routers': ['legal_work', 'accreditations'],
    },
    {
        'slug': 'analytics',
        'title': 'Analytics & Audit API',
        'description': 'Дашбордовые сводки и аудит событий.',
        'routers': ['dashboard', 'audit_logs'],
    },
]


def read_lines(path: Path):
    return path.read_text(encoding='utf-8').splitlines()


def find_line(lines, prefix: str):
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            return i
    raise ValueError(f'Heading not found: {prefix}')


def slice_blocks(lines, heading_pattern: str):
    idx = []
    for i, line in enumerate(lines):
        m = re.match(heading_pattern, line)
        if m:
            idx.append((i, m.group(1)))
    blocks = {}
    if not idx:
        return blocks, lines
    intro = lines[:idx[0][0]]
    for j, (start, name) in enumerate(idx):
        end = idx[j + 1][0] if j + 1 < len(idx) else len(lines)
        blocks[name] = lines[start:end]
    return blocks, intro


def anchor(name: str):
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return f'#model-{slug}'

def collect_refs(router_lines):
    text = '\n'.join(router_lines)
    return sorted(set(re.findall(r'\[`([^`]+)`\]\(#model-[^)]+\)', text)))


def collect_endpoints(router_lines):
    return set(re.findall(r'^#### `([^`]+)`', '\n'.join(router_lines), flags=re.M))


def extract_usage_blocks(usage_lines):
    blocks = {}
    idx = []
    for i, line in enumerate(usage_lines):
        m = re.match(r'^### `([^`]+)`', line)
        if m:
            idx.append((i, m.group(1)))
    for j, (start, key) in enumerate(idx):
        end = idx[j + 1][0] if j + 1 < len(idx) else len(usage_lines)
        blocks[key] = usage_lines[start:end]
    intro = usage_lines[:idx[0][0]] if idx else usage_lines
    return intro, blocks


def render_domain(domain, router_blocks, model_blocks, usage_blocks):
    lines = []
    domain_router_names = [r for r in domain['routers'] if r in router_blocks]

    all_router_lines = []
    for r in domain_router_names:
        all_router_lines.extend(router_blocks[r])
        all_router_lines.append('')

    model_names = []
    for r in domain_router_names:
        refs = collect_refs(router_blocks[r])
        for ref in refs:
            if ref in model_blocks and ref not in model_names:
                model_names.append(ref)

    endpoint_keys = set()
    for r in domain_router_names:
        endpoint_keys.update(collect_endpoints(router_blocks[r]))

    selected_usage = []
    for key in sorted(endpoint_keys):
        if key in usage_blocks:
            selected_usage.extend(usage_blocks[key])
            selected_usage.append('')

    endpoint_count = sum(len(collect_endpoints(router_blocks[r])) for r in domain_router_names)

    lines.append(f"# {domain['title']}")
    lines.append('')
    lines.append(f"Сгенерировано из `docs/API.md` на {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (local time).")
    lines.append('')
    lines.append('## Scope')
    lines.append(f"- Домен: `{domain['slug']}`")
    lines.append(f"- Описание: {domain['description']}")
    lines.append(f"- Routers: `{len(domain_router_names)}`")
    lines.append(f"- Endpoints: `{endpoint_count}`")
    lines.append(f"- Список роутеров: {', '.join('`'+r+'`' for r in domain_router_names)}")
    lines.append('')
    lines.append('## Common Rules')
    lines.append('- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.')
    lines.append('- Ниже сохранена детальная структура endpoint\'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.')
    lines.append('')

    lines.append('## Data Contract Catalog (Domain)')
    lines.append('')
    if model_names:
        lines.append(f"Модели, используемые в домене: `{len(model_names)}`.")
        lines.append('')
        for name in model_names:
            lines.extend(model_blocks[name])
            lines.append('')
    else:
        lines.append('Модели не обнаружены (endpoint\'ы используют примитивные параметры или свободный JSON).')
        lines.append('')

    lines.append('## Routers / Controllers Reference')
    lines.append('')
    if all_router_lines:
        lines.extend(all_router_lines)
    else:
        lines.append('Нет роутеров в текущем домене.')
        lines.append('')

    lines.append('## Usage Examples (Domain)')
    lines.append('')
    if selected_usage:
        lines.extend(selected_usage)
    else:
        lines.append('Ключевые примеры отсутствуют для этого домена в исходном monolith reference.')
        lines.append('')

    return '\n'.join(lines).strip() + '\n', endpoint_count, len(model_names)


def build_index(domains_meta):
    lines = []
    lines.append('# API Domains Index')
    lines.append('')
    lines.append(f"Сгенерировано на {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (local time).")
    lines.append('')
    lines.append('## API Domain Map')
    for meta in domains_meta:
        lines.append(f"- `{meta['slug']}`: {meta['description']}")
    lines.append('')
    lines.append('## Domain Files')
    lines.append('')
    lines.append('| Domain | Description | Routers | Endpoints | Models | File |')
    lines.append('| --- | --- | --- | --- | --- | --- |')
    for meta in domains_meta:
        lines.append(
            f"| `{meta['slug']}` | {meta['description']} | {meta['router_count']} | {meta['endpoint_count']} | {meta['model_count']} | [`{meta['file']}`]({meta['file']}) |"
        )
    lines.append('')
    lines.append('## Global Rules')
    lines.append('')
    lines.append('### Base URL')
    lines.append('- Локально: `http://localhost:8000/api/v1`')
    lines.append('- Production: `<your-domain>/api/v1`')
    lines.append('')
    lines.append('### Authentication Header')
    lines.append('- `Authorization: Bearer <access_token>` для всех защищённых endpoint\'ов.')
    lines.append('- Публичные исключения: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`.')
    lines.append('')
    lines.append('### Common Error Codes')
    lines.append('| Code | Meaning | Typical Body |')
    lines.append('| --- | --- | --- |')
    lines.append('| `400` | Ошибка бизнес-валидации/формата данных | `{"detail": "..."}` |')
    lines.append('| `401` | Ошибка аутентификации/токена | `{"detail": "..."}` |')
    lines.append('| `403` | Недостаточно прав | `{"detail": "..."}` |')
    lines.append('| `404` | Сущность/ресурс не найден | `{"detail": "..."}` |')
    lines.append('| `422` | Ошибка валидации запроса FastAPI/Pydantic | `{ "detail": [{"loc": [...], "msg": "...", "type": "..."}] }` |')
    lines.append('| `500` | Внутренняя ошибка сервера | `{"detail": "Internal Server Error"}` или текст исключения |')
    lines.append('')
    lines.append('### Error Envelope')
    lines.append('- Базовый формат: `{"detail": "..."}` (`HTTPException`).')
    lines.append('- Для `422`: `detail[]` с массивом ошибок валидации.')
    lines.append('')
    lines.append('### Update Rule')
    lines.append('- При изменении роутеров/схем: сначала перегенерировать `docs/API.md`, затем заново запустить `scripts/split_api_reference.py`.')
    lines.append('')
    return '\n'.join(lines).strip() + '\n'

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = read_lines(SOURCE)

    idx_auth = find_line(lines, '## Global Authentication & Authorization')
    idx_error = find_line(lines, '## Global Error Envelope')
    idx_data = find_line(lines, '## Data Contract Catalog (Pydantic DTO)')
    idx_routers = find_line(lines, '## Routers / Controllers Reference')
    idx_usage = find_line(lines, '## Usage Examples (Key Endpoints)')

    data_lines = lines[idx_data:idx_routers]
    routers_lines = lines[idx_routers:idx_usage]
    usage_lines = lines[idx_usage:]

    model_blocks, data_intro = slice_blocks(data_lines, r'^### Model `([^`]+)`')
    router_blocks, routers_intro = slice_blocks(routers_lines, r'^### Router `([^`]+)`')
    usage_intro, usage_blocks = extract_usage_blocks(usage_lines)

    all_routers = set(router_blocks.keys())
    mapped = set()
    for d in DOMAIN_CONFIG:
        mapped.update(d['routers'])

    unmapped = sorted(all_routers - mapped)
    if unmapped:
        DOMAIN_CONFIG.append({
            'slug': 'misc',
            'title': 'Misc API',
            'description': 'Автоматически добавленные роутеры, не попавшие в ручную карту доменов.',
            'routers': unmapped,
        })

    domains_meta = []
    for domain in DOMAIN_CONFIG:
        content, endpoint_count, model_count = render_domain(domain, router_blocks, model_blocks, usage_blocks)
        filename = f"{domain['slug']}.md"
        (OUT_DIR / filename).write_text(content, encoding='utf-8')
        domains_meta.append({
            'slug': domain['slug'],
            'description': domain['description'],
            'router_count': len([r for r in domain['routers'] if r in router_blocks]),
            'endpoint_count': endpoint_count,
            'model_count': model_count,
            'file': filename,
        })

    index_md = build_index(domains_meta)
    (OUT_DIR / 'INDEX.md').write_text(index_md, encoding='utf-8')

    legacy = []
    legacy.append('# API Reference (Modular)')
    legacy.append('')
    legacy.append('Монолитный reference разбит на модульные документы по бизнес-доменам.')
    legacy.append('')
    legacy.append('Новая точка входа: `docs/api/INDEX.md`.')
    legacy.append('')
    legacy.append('## Domain Files')
    for meta in domains_meta:
        legacy.append(f"- `docs/api/{meta['file']}`")
    legacy.append('')
    legacy.append('## Regeneration')
    legacy.append('1. Обновить `docs/API.md` генератором API reference (если менялись роутеры/схемы).')
    legacy.append('2. Запустить `python scripts/split_api_reference.py` для актуализации модульных файлов.')
    legacy.append('')
    SOURCE.write_text('\n'.join(legacy), encoding='utf-8')

    print(f'Wrote domain docs to: {OUT_DIR}')
    print('Created files:')
    for meta in domains_meta:
        print(f"  - {meta['file']}: routers={meta['router_count']}, endpoints={meta['endpoint_count']}, models={meta['model_count']}")
    print('  - INDEX.md')


if __name__ == '__main__':
    main()
