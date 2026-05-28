
import ast
import datetime as dt
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_FILE = ROOT / 'backend' / 'main.py'
ROUTERS_DIR = ROOT / 'backend' / 'app' / 'routers'
SCHEMAS_DIR = ROOT / 'backend' / 'app' / 'schemas'
OUT_FILE = ROOT / 'docs' / 'API.md'

HTTP_METHODS = {'get','post','put','patch','delete','head','options','api_route'}
PARAM_CALLS = {'Query','Path','Body','Form','File','Header','Cookie'}
PRIMITIVES = {'str','int','float','bool','dict','list','set','tuple','Any','date','datetime','UUID','EmailStr','Decimal','bytes'}
IGNORE_CALL_PREFIX = {'str','int','float','bool','len','dict','list','set','tuple','print','uuid','datetime','date','timedelta','json','re','Path'}
CONSTRAINT_KEYS = {'gt','ge','lt','le','multiple_of','min_length','max_length','pattern','max_digits','decimal_places','min_items','max_items','description','examples'}


@dataclass
class ModelField:
    name: str
    typ: str
    required: bool
    default: str
    constraints: str


@dataclass
class ModelInfo:
    name: str
    file: str
    bases: list[str] = field(default_factory=list)
    fields: list[ModelField] = field(default_factory=list)
    doc: str = ''


@dataclass
class ParamInfo:
    name: str
    location: str
    typ: str
    required: bool
    default: str
    constraints: str


@dataclass
class EndpointInfo:
    router_module: str
    router_prefix: str
    file: str
    func_name: str
    func_doc: str
    method: str
    full_path: str
    response_model: str
    status_code: str
    dependencies: list[str]
    params: list[ParamInfo]
    body_models: list[str]
    response_models: list[str]
    service_calls: list[str]
    side_effects: list[str]
    errors: dict[str, list[str]]
    auth_mode: str


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8-sig')


def expr(node):
    if node is None:
        return ''
    try:
        return ast.unparse(node)
    except Exception:
        return ''


def short(node):
    if node is None:
        return '-'
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    return expr(node)


def kw_map(call: ast.Call):
    out = {}
    for kw in call.keywords:
        if kw.arg:
            out[kw.arg] = kw.value
    return out


def first_name(call: ast.Call):
    if not call.args:
        return ''
    arg = call.args[0]
    if isinstance(arg, ast.Name):
        return arg.id
    return expr(arg)


def md_escape(value: str):
    return value.replace('|', '\\|').replace('\n', ' ').strip()


def anchor_for_model(name: str):
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return f'#model-{slug}'


def literal(node, default=None):
    if node is None:
        return default
    try:
        return ast.literal_eval(node)
    except Exception:
        return default


def extract_model_tokens(type_expr: str, known_models: set[str]):
    tokens = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', type_expr or '')
    return [t for t in tokens if t in known_models]

def parse_main():
    tree = ast.parse(read_text(MAIN_FILE))
    alias_to_module = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('app.routers.'):
            mod = node.module.split('.')[-1]
            for a in node.names:
                alias_to_module[a.asname or a.name] = mod

    prefixes = {}
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == 'include_router' and call.args:
                first = call.args[0]
                if isinstance(first, ast.Name):
                    mod = alias_to_module.get(first.id)
                    if not mod:
                        continue
                    pfx = ''
                    for kw in call.keywords:
                        if kw.arg == 'prefix' and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            pfx = kw.value.value
                    prefixes[mod] = pfx

    open_paths = set()
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == 'add_middleware':
                if call.args and expr(call.args[0]).endswith('AuthMiddleware'):
                    for kw in call.keywords:
                        if kw.arg == 'open_paths':
                            vals = literal(kw.value, default=set())
                            if isinstance(vals, (set, list, tuple)):
                                for v in vals:
                                    if isinstance(v, str):
                                        open_paths.add(v)
    return prefixes, open_paths


def parse_schema_models():
    models = {}
    skipped = []
    for path in sorted(SCHEMAS_DIR.glob('*.py')):
        if path.name == '__init__.py':
            continue
        try:
            tree = ast.parse(read_text(path))
        except SyntaxError:
            skipped.append(str(path.relative_to(ROOT)).replace('\\', '/'))
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            bases = [expr(b) for b in node.bases]
            info = ModelInfo(
                name=node.name,
                file=str(path.relative_to(ROOT)).replace('\\', '/'),
                bases=bases,
                doc=ast.get_docstring(node) or '',
            )
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fname = item.target.id
                    if fname in {'model_config', 'Config'}:
                        continue
                    typ = expr(item.annotation) or 'Any'
                    required = item.value is None
                    default = '-' if required else short(item.value)
                    constraints = []
                    if isinstance(item.value, ast.Call) and expr(item.value.func).endswith('Field'):
                        kws = kw_map(item.value)
                        if item.value.args:
                            first = item.value.args[0]
                            if isinstance(first, ast.Constant) and first.value is Ellipsis:
                                required, default = True, '-'
                            else:
                                required, default = False, short(first)
                        if 'default' in kws:
                            dv = kws['default']
                            if isinstance(dv, ast.Constant) and dv.value is Ellipsis:
                                required, default = True, '-'
                            else:
                                required, default = False, short(dv)
                        if 'default_factory' in kws:
                            required, default = False, f"factory:{expr(kws['default_factory'])}"
                        for k, v in kws.items():
                            if k in CONSTRAINT_KEYS:
                                constraints.append(f"{k}={short(v)}")
                    if 'Literal[' in typ:
                        lit = typ.split('Literal[', 1)[1].rstrip(']')
                        constraints.append(f"enum={lit}")
                    info.fields.append(ModelField(fname, typ, required, default, ', '.join(constraints) if constraints else '-'))
            models[info.name] = info
    if skipped:
        print('Skipped malformed schema files:')
        for item in skipped:
            print(f'  - {item}')
    return models


def flatten_model_fields(models: dict[str, ModelInfo]):
    cache = {}

    def resolve(name: str, trail=None):
        if name in cache:
            return cache[name]
        if name not in models:
            return []
        trail = trail or set()
        if name in trail:
            return []
        trail.add(name)

        info = models[name]
        ordered = []
        seen = set()
        for base in info.bases:
            b = base.split('[', 1)[0].split('.')[-1]
            if b in models:
                for fld in resolve(b, trail):
                    if fld.name not in seen:
                        ordered.append(fld)
                        seen.add(fld.name)
        for fld in info.fields:
            if fld.name in seen:
                for i, old in enumerate(ordered):
                    if old.name == fld.name:
                        ordered[i] = fld
                        break
            else:
                ordered.append(fld)
                seen.add(fld.name)
        cache[name] = ordered
        return ordered

    return {name: resolve(name) for name in models.keys()}

def parse_dep(default_node):
    if isinstance(default_node, ast.Call):
        fn = expr(default_node.func)
        if fn in {'Depends', 'Security'}:
            target = first_name(default_node)
            return f"{fn}({target})" if target else fn
    return ''


def parse_param_call(default_node):
    if isinstance(default_node, ast.Call):
        fn = expr(default_node.func).split('.')[-1]
        if fn in PARAM_CALLS:
            kws = kw_map(default_node)
            required = True
            default = '-'
            if default_node.args:
                first = default_node.args[0]
                if isinstance(first, ast.Constant) and first.value is Ellipsis:
                    required, default = True, '-'
                else:
                    required, default = False, short(first)
            if 'default' in kws:
                dv = kws['default']
                if isinstance(dv, ast.Constant) and dv.value is Ellipsis:
                    required, default = True, '-'
                else:
                    required, default = False, short(dv)
            if 'default_factory' in kws:
                required, default = False, f"factory:{expr(kws['default_factory'])}"
            cons = []
            for k, v in kws.items():
                if k in CONSTRAINT_KEYS:
                    cons.append(f"{k}={short(v)}")
            return fn.lower(), required, default, ', '.join(cons) if cons else '-'
    return '', False, '', ''


def is_complex_type(typ: str, known_models: set[str]):
    normalized = typ.replace('typing.', '').strip()
    if normalized in {'Request', 'Response', 'AsyncSession', 'BackgroundTasks'}:
        return False
    return len(extract_model_tokens(typ, known_models)) > 0


def combine_path(prefix: str, route_path: str):
    p = (prefix or '').rstrip('/')
    r = (route_path or '').lstrip('/')
    if p and r:
        return f"{p}/{r}"
    if p:
        return p
    if r:
        return f"/{r}"
    return '/'


def parse_router_endpoints(module: str, prefix: str, open_paths: set[str], known_models: set[str]):
    path = ROUTERS_DIR / f'{module}.py'
    if not path.exists():
        return []

    text = read_text(path)
    tree = ast.parse(text)

    imported_symbols = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for a in node.names:
                imported_symbols.add(a.asname or a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                imported_symbols.add(a.asname or a.name.split('.')[-1])

    endpoints = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        decorators = []
        for dec in node.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            op = dec.func.attr
            if op not in HTTP_METHODS:
                continue

            methods = []
            if op == 'api_route':
                mvals = None
                for kw in dec.keywords:
                    if kw.arg == 'methods':
                        mvals = literal(kw.value)
                        break
                if isinstance(mvals, (list, tuple)):
                    methods = [str(x).upper() for x in mvals]
            else:
                methods = [op.upper()]

            route_path = '/'
            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                route_path = dec.args[0].value

            response_model = '-'
            status_code = '200'
            decorator_deps = []
            for kw in dec.keywords:
                if kw.arg == 'response_model':
                    response_model = expr(kw.value)
                if kw.arg == 'status_code':
                    status_code = short(kw.value)
                if kw.arg == 'dependencies' and isinstance(kw.value, (ast.List, ast.Tuple)):
                    for dep in kw.value.elts:
                        d = parse_dep(dep)
                        if d:
                            decorator_deps.append(d)

            for m in methods:
                decorators.append((m, route_path, response_model, status_code, decorator_deps))

        if not decorators:
            continue

        path_params = set(re.findall(r'\{([^{}]+)\}', ' '.join([d[1] for d in decorators])))
        args = node.args.args
        defaults = node.args.defaults
        default_map = {}
        if defaults:
            for i, d in enumerate(defaults):
                arg = args[len(args) - len(defaults) + i]
                default_map[arg.arg] = d

        dependencies = []
        params = []
        body_models = []

        for arg in args:
            name = arg.arg
            if name in {'self', 'cls'}:
                continue
            typ = expr(arg.annotation) or 'Any'
            default_node = default_map.get(name)

            dep = parse_dep(default_node)
            if dep:
                dependencies.append(f"{name}: {dep}")
                continue

            if typ in {'Request', 'Response', 'BackgroundTasks'}:
                continue

            loc, req, dflt, cons = parse_param_call(default_node)
            if not loc:
                if name in path_params:
                    loc, req, dflt, cons = 'path', True, '-', '-'
                else:
                    mutating = any(m in {'POST', 'PUT', 'PATCH'} for m, *_ in decorators)
                    if mutating and is_complex_type(typ, known_models):
                        loc, req, dflt, cons = 'body', default_node is None, '-' if default_node is None else short(default_node), '-'
                    else:
                        loc, req, dflt, cons = 'query', default_node is None, '-' if default_node is None else short(default_node), '-'

            params.append(ParamInfo(name, loc, typ, req, dflt, cons))
            if loc == 'body':
                for token in extract_model_tokens(typ, known_models):
                    if token not in body_models:
                        body_models.append(token)

        response_models = []
        for _, _, rm, _, _ in decorators:
            for token in extract_model_tokens(rm, known_models):
                if token not in response_models:
                    response_models.append(token)

        calls = []
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                c = expr(sub.func)
                if not c or c.split('.')[0] in IGNORE_CALL_PREFIX:
                    continue
                low = c.lower()
                include = c.startswith('db.') or any(c == s or c.startswith(s + '.') for s in imported_symbols)
                include = include or any(k in low for k in ['service', 'log', 'notify', 'upload', 'storage', 'event', 'audit', 'add_task', 'send', 'mailbox', 'imap', 'smtp'])
                if include and c not in calls:
                    calls.append(c)

        all_calls = ' | '.join(calls).lower()
        side = []
        if any(x in all_calls for x in ['db.commit', 'db.add', 'db.delete', '.create', '.update']):
            side.append('DB write')
        if any(x in all_calls for x in ['db.execute', 'select']):
            side.append('DB read')
        if any(x in all_calls for x in ['eventlog', 'audit', 'log_event', 'log_']):
            side.append('Audit/Event logging')
        if any(x in all_calls for x in ['notification', 'notify']):
            side.append('Notification dispatch')
        if any(x in all_calls for x in ['mailbox', 'smtp', 'imap', 'yandex', 'mail_', 'send_email', 'send_message']):
            side.append('Mail integration')
        if any(x in all_calls for x in ['add_task', 'background']):
            side.append('Background task trigger')
        if any(x in all_calls for x in ['storage', 'upload', 'file', 'download']):
            side.append('File/storage operation')
        if not side:
            side.append('No explicit side effects (read/transform path)')

        errors = defaultdict(list)
        for sub in ast.walk(node):
            if isinstance(sub, ast.Raise) and isinstance(sub.exc, ast.Call) and expr(sub.exc.func).endswith('HTTPException'):
                kws = kw_map(sub.exc)
                status = short(kws['status_code']).strip("'") if 'status_code' in kws else (short(sub.exc.args[0]).strip("'") if sub.exc.args else '-')
                detail = short(kws['detail']).strip("'") if 'detail' in kws else (short(sub.exc.args[1]).strip("'") if len(sub.exc.args) > 1 else 'HTTPException')
                if detail not in errors[status]:
                    errors[status].append(detail)

        for method, route_path, rm, status_code, dec_deps in decorators:
            full = combine_path(prefix, route_path)
            route_deps = list(dict.fromkeys(dependencies + [f"decorator: {d}" for d in dec_deps]))
            if full in open_paths or full in {'/health', '/', '/test'}:
                auth_mode = 'Public'
            else:
                auth_mode = 'JWT (AuthMiddleware)'
                dep_text = ' '.join(route_deps).lower()
                if 'currentuser' in dep_text or 'request.state.user' in text.lower():
                    auth_mode += ' + current user context'
                if any(s == '403' for s in errors.keys()):
                    auth_mode += '; route may enforce role/section checks'

            endpoints.append(EndpointInfo(
                router_module=module,
                router_prefix=prefix,
                file=str(path.relative_to(ROOT)).replace('\\', '/'),
                func_name=node.name,
                func_doc=ast.get_docstring(node) or '',
                method=method,
                full_path=full,
                response_model=rm,
                status_code=status_code,
                dependencies=route_deps,
                params=params,
                body_models=body_models,
                response_models=response_models,
                service_calls=calls[:12],
                side_effects=side,
                errors=dict(errors),
                auth_mode=auth_mode,
            ))

    return endpoints

def format_model_contract_section(models: dict[str, ModelInfo], flattened: dict[str, list[ModelField]]):
    lines = []
    lines.append('## Data Contract Catalog (Pydantic DTO)\n')
    lines.append('В проекте обнаружены только Pydantic-модели (`BaseModel`); Marshmallow-схемы не используются.\n')
    for name in sorted(models.keys()):
        info = models[name]
        lines.append(f"### Model `{name}`\n")
        lines.append(f"Source: `{info.file}`")
        if info.doc:
            lines.append(f"\nDescription: {info.doc.strip()}")
        lines.append('\n')
        lines.append('| Field | Type | Required | Default | Constraints |')
        lines.append('| --- | --- | --- | --- | --- |')
        fields = flattened.get(name, [])
        if not fields:
            lines.append('| - | - | - | - | - |')
        else:
            for f in fields:
                lines.append('| ' + md_escape(f.name) + ' | ' + md_escape(f.typ) + ' | ' + ('yes' if f.required else 'no') + ' | ' + md_escape(f.default) + ' | ' + md_escape(f.constraints) + ' |')
        lines.append('')
    return '\n'.join(lines)


def fmt_params(params: list[ParamInfo], location: str):
    subset = [p for p in params if p.location == location]
    if not subset:
        return 'none'
    out = []
    for p in subset:
        req = 'required' if p.required else 'optional'
        out.append(f"`{p.name}`: {p.typ} ({req}, default={p.default}, constraints={p.constraints})")
    return '; '.join(out)


def endpoint_to_markdown(ep: EndpointInfo):
    out = []
    out.append(f"#### `{ep.method} {ep.full_path}`")
    out.append('')
    out.append(f"- Controller: `{ep.file}::{ep.func_name}`")
    if ep.func_doc:
        out.append(f"- Summary: {ep.func_doc.strip().splitlines()[0]}")
    out.append('- Data Contract:')
    out.append(f"  - Path params: {fmt_params(ep.params, 'path')}")
    out.append(f"  - Query params: {fmt_params(ep.params, 'query')}")
    out.append(f"  - Header params: {fmt_params(ep.params, 'header')}")
    out.append(f"  - Form params: {fmt_params(ep.params, 'form')}")
    out.append(f"  - File params: {fmt_params(ep.params, 'file')}")
    if ep.body_models:
        links = [f"[`{m}`]({anchor_for_model(m)})" for m in ep.body_models]
        out.append(f"  - Body models: {', '.join(links)}")
    else:
        body_params = [p for p in ep.params if p.location == 'body']
        out.append('  - Body: ' + ('; '.join(f"`{p.name}`: {p.typ}" for p in body_params) if body_params else 'none'))
    if ep.response_model and ep.response_model != '-':
        out.append(f"  - Response model: `{ep.response_model}`")
    if ep.response_models:
        links = [f"[`{m}`]({anchor_for_model(m)})" for m in ep.response_models]
        out.append(f"  - Response contracts: {', '.join(links)}")
    out.append(f"  - Success status: `{ep.status_code}`")

    out.append('- Authentication & Authorization:')
    out.append(f"  - Access mode: {ep.auth_mode}")
    if ep.dependencies:
        out.append('  - Depends/Security:')
        for d in ep.dependencies:
            out.append(f"    - `{d}`")
    else:
        out.append('  - Depends/Security: none at function level')

    out.append('- Logic Flow:')
    if ep.service_calls:
        out.append('  - Internal calls:')
        for c in ep.service_calls:
            out.append(f"    - `{c}`")
    else:
        out.append('  - Internal calls: none (or not statically detected)')
    out.append(f"  - Side effects: {', '.join(ep.side_effects)}")

    out.append('- Error Handling:')
    if ep.errors:
        for status in sorted(ep.errors.keys(), key=lambda x: (x == '-', x)):
            details = ep.errors[status]
            body = '`{"detail": "..."}`'
            if details:
                detail_join = '; '.join(f"`{d}`" for d in details[:5])
                out.append(f"  - `{status}`: {detail_join}; body schema {body}")
            else:
                out.append(f"  - `{status}`: body schema {body}")
    else:
        out.append('  - Explicit `HTTPException` not found in handler body')
    out.append("  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`")
    out.append('')
    return '\n'.join(out)


def sample_for_type(typ: str):
    t = typ.strip()
    if 'Literal[' in t:
        vals = re.findall(r"'([^']+)'|\"([^\"]+)\"", t)
        if vals:
            for a, b in vals:
                if a or b:
                    return a or b
    if 'EmailStr' in t:
        return 'user@example.com'
    if 'UUID' in t:
        return '00000000-0000-0000-0000-000000000000'
    if 'datetime' in t:
        return '2026-01-01T00:00:00Z'
    if re.search(r'\bdate\b', t):
        return '2026-01-01'
    if 'Dict[' in t or 'dict[' in t:
        return {}
    if 'List[' in t or 'list[' in t:
        return []
    if 'bool' in t:
        return False
    if 'int' in t:
        return 0
    if 'float' in t or 'Decimal' in t:
        return 0.0
    return 'string'


def build_model_sample(model_name: str, flattened):
    fields = flattened.get(model_name, [])
    out = {}
    ordered = sorted(fields, key=lambda f: (not f.required, f.name))
    for fld in ordered[:8]:
        out[fld.name] = sample_for_type(fld.typ)
    return out


def build_key_examples(endpoints: list[EndpointInfo], flattened):
    lines = []
    lines.append('## Usage Examples (Key Endpoints)\n')
    preferred = [
        ('POST', '/api/v1/auth/login'),
        ('POST', '/api/v1/auth/refresh'),
        ('GET', '/api/v1/deals'),
        ('POST', '/api/v1/deals'),
        ('GET', '/api/v1/tasks'),
        ('POST', '/api/v1/tasks'),
        ('GET', '/api/v1/finance/cashflow'),
        ('POST', '/api/v1/finance/treasury/transactions'),
        ('GET', '/api/v1/document-registry'),
        ('POST', '/api/v1/document-registry'),
        ('GET', '/api/v1/outgoing-registry'),
        ('POST', '/api/v1/outgoing-registry'),
        ('GET', '/api/v1/notifications'),
        ('POST', '/api/v1/mail/mailboxes/{mailbox_id}/send'),
        ('POST', '/api/v1/uploads/contracts/documents'),
    ]
    emap = {(e.method, e.full_path): e for e in endpoints}
    selected = [emap[k] for k in preferred if k in emap] or endpoints[:10]

    for ep in selected:
        lines.append(f"### `{ep.method} {ep.full_path}`\n")
        lines.append('```bash')
        hdr = '-H "Authorization: Bearer $ACCESS_TOKEN" ' if 'Public' not in ep.auth_mode else ''
        if ep.method in {'POST', 'PUT', 'PATCH'}:
            body = build_model_sample(ep.body_models[0], flattened) if ep.body_models else {p.name: sample_for_type(p.typ) for p in ep.params if p.location == 'body'}
            body_json = json.dumps(body, ensure_ascii=False)
            lines.append(f"curl -X {ep.method} http://localhost:8000{ep.full_path} {hdr}-H \"Content-Type: application/json\" -d '{body_json}'")
        else:
            lines.append(f"curl -X {ep.method} http://localhost:8000{ep.full_path} {hdr}")
        lines.append('```\n')

        resp = build_model_sample(ep.response_models[0], flattened) if ep.response_models else {'status': 'ok'}
        lines.append('```json')
        lines.append(json.dumps(resp, ensure_ascii=False, indent=2))
        lines.append('```\n')
    return '\n'.join(lines)

def generate():
    prefixes, open_paths = parse_main()
    models = parse_schema_models()
    flattened = flatten_model_fields(models)
    known_models = set(models.keys())

    endpoints = []
    for module in sorted(prefixes.keys()):
        endpoints.extend(parse_router_endpoints(module, prefixes[module], open_paths, known_models))
    endpoints.sort(key=lambda e: (e.router_module, e.full_path, e.method, e.func_name))

    lines = []
    lines.append('# API Reference (Enterprise)\n')
    lines.append(f"Сгенерировано из `backend/app/routers` и `backend/app/schemas` на {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (local time).")
    lines.append('')
    lines.append('## Coverage')
    lines.append(f"- Routers: `{len(prefixes)}`")
    lines.append(f"- Endpoints: `{len(endpoints)}`")
    lines.append(f"- Pydantic models: `{len(models)}`")
    lines.append('- Controller scope: `backend/app/routers/*.py`')
    lines.append('- DTO scope: `backend/app/schemas/*.py`')
    lines.append('')

    lines.append('## Global Authentication & Authorization')
    lines.append('- `AuthMiddleware` применяется ко всем маршрутам `/api/v1/*`, кроме явно открытых путей `POST /api/v1/auth/login` и `POST /api/v1/auth/refresh`.')
    lines.append('- Внутри endpoint\'ов дополнительно используются `Depends(...)` (например, `CurrentUser`, `get_db`) и локальные role/section checks.')
    lines.append('- Для `403` обычно используется `HTTPException(status_code=403, detail=...)` с причиной отказа в поле `detail`.')
    lines.append('')

    lines.append('## Global Error Envelope')
    lines.append("- Бизнес- и permission-ошибки: `{'detail': '...'}` (через `HTTPException`).")
    lines.append("- Валидационные ошибки (`422`): `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`.")
    lines.append('- Нормализация собственного `error code` поверх `detail` в кодовой базе пока не стандартизована.')
    lines.append('')

    lines.append(format_model_contract_section(models, flattened))
    lines.append('## Routers / Controllers Reference\n')

    grouped = defaultdict(list)
    for ep in endpoints:
        grouped[ep.router_module].append(ep)

    for module in sorted(grouped.keys()):
        grp = grouped[module]
        lines.append(f"### Router `{module}`\n")
        lines.append(f"Source: `{grp[0].file}`")
        lines.append(f"\nPrefix: `{grp[0].router_prefix}`")
        lines.append(f"\nEndpoints: `{len(grp)}`\n")
        for ep in grp:
            lines.append(endpoint_to_markdown(ep))

    lines.append(build_key_examples(endpoints, flattened))

    OUT_FILE.write_text('\n'.join(lines).replace('\r\n', '\n'), encoding='utf-8')
    print(f'Generated: {OUT_FILE}')


if __name__ == '__main__':
    generate()
