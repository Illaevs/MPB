"""
CRM System for Construction Project Management
Main FastAPI application entry point
"""
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.auth_middleware import AuthMiddleware
from app.core.config import settings
from app.core.request_utils import client_ip
from app.routers.auth import router as auth_router
from app.routers.deals import router as deals_router
from app.routers.leads import router as leads_router
from app.routers.companies import router as companies_router
from app.routers.stages import router as stages_router
from app.routers.finance import router as finance_router
from app.routers.income_expense import router as income_expense_router
from app.routers.products import router as products_router
from app.routers.tasks import router as tasks_router
from app.routers.contracts import router as contracts_router
from app.routers.subcontractors import router as subcontractors_router
from app.routers.subcontractor_stages import router as subcontractor_stages_router
from app.routers.subcontractor_products import router as subcontractor_products_router
from app.routers.executor import router as executor_router
from app.routers.deal_execution import router as deal_execution_router
from app.routers.outgoing_registry import router as outgoing_registry_router
from app.routers.document_registry import router as document_registry_router
from app.routers.files_catalog import router as files_catalog_router
from app.routers.file_folder_permissions import router as file_folder_permissions_router
from app.routers.tenders import router as tenders_router
from app.routers.accreditations import router as accreditations_router
from app.routers.roles import router as roles_router
from app.routers.org_structure import router as org_structure_router
from app.routers.support import router as support_router
from app.routers.users import router as users_router
from app.routers.task_auctions import router as task_auctions_router
from app.routers.penalty_rules import router as penalty_rules_router
from app.routers.result_reviews import router as result_reviews_router
from app.routers.kp import router as kp_router
from app.routers.banks import router as banks_router
from app.routers.dadata import router as dadata_router
from app.routers.legal_work import router as legal_work_router
from app.routers.uploads import router as uploads_router
from app.routers.notifications import router as notifications_router
from app.routers.notification_rules import router as notification_rules_router
from app.routers.notification_preferences import router as notification_preferences_router
from app.routers.notification_subscriptions import router as notification_subscriptions_router
from app.routers.telegram_notifications import router as telegram_notifications_router
from app.routers.dashboard import router as dashboard_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.storage import router as storage_router
from app.routers.mail import router as mail_router, yandex_oauth_callback
from app.routers.task_messages import router as task_messages_router
from app.routers.task_subtasks import router as task_subtasks_router
from app.routers.global_chat import router as global_chat_router
from app.routers.customer_portal import router as customer_portal_router
from app.routers.data_health import router as data_health_router, public_router as data_health_public_router
from app.routers.document_templates import router as document_templates_router
from app.routers.approvals import router as approvals_router
from app.routers.ai import router as ai_router
from app.routers.workday import router as workday_router
from app.routers.profiles import router as profiles_router
from app.routers.absences import router as absences_router
from app.routers.feed import router as feed_router
from app.routers.event_bus import router as event_bus_router
# Step 0 поиска: глобальный полнотекстовый поиск (FTS5 + ACL).
from app.routers.search import router as search_router
# Reglaments Phase 0: ИЗОЛИРОВАННЫЙ домен нормативной базы (СНиП/ГОСТ/СП).
# Отдельный от основного /api/v1/search — свои таблицы, свой ранкинг.
from app.routers.reglaments import router as reglaments_router
# Inbound integrations (vendor webhooks). Каркас в F2; реальная маршрутизация
# (создание lead/задач/документов из payload) дописывается командой
# интеграции в июле через `@on("<vendor>.after_inbound")` handlers.
from app.routers.integrations.diadoc_inbound import router as diadoc_inbound_router
from app.routers.integrations.telegram_inbound import router as telegram_inbound_router
from app.routers.integrations.onec_inbound import router as onec_inbound_router
from app.routers.integrations.bank_inbound import router as bank_inbound_router
from app.routers.integrations.gosklyuch_inbound import router as gosklyuch_inbound_router
from app.services import permissions as permissions_service
from app.services.chat_bootstrap import ensure_chat_schema
from app.services.auth_security_store import consume_rate_limit
from app.services.upload_security import cleanup_temp_uploads
from app.services.stage_product_assignment_bootstrap import ensure_stage_product_assignment_schema
from app.services.user_avatar_bootstrap import ensure_user_avatar_schema
from app.services.user_two_factor_bootstrap import ensure_user_two_factor_schema
from app.services.customer_portal_bootstrap import ensure_customer_portal_role
from app.services.telegram_notifications_bootstrap import ensure_telegram_notifications_schema
from app.services.data_health_bootstrap import ensure_data_health_schema
from app.services.contract_documents_bootstrap import ensure_contract_documents_schema
from app.services.task_matrix_bootstrap import ensure_task_matrix_schema
from app.services.deal_products_bootstrap import ensure_deal_products_schema
from app.services.company_documents_bootstrap import ensure_company_documents_schema
from app.services.outgoing_documents_bootstrap import ensure_outgoing_documents_schema
from app.services.document_templates_bootstrap import ensure_document_templates_schema
from app.services.approval_bootstrap import ensure_approval_schema

AUTHENTICATED_SECTION_KEYS = getattr(
    permissions_service,
    "AUTHENTICATED_SECTION_KEYS",
    getattr(permissions_service, "SECTION_KEYS", []),
)
require_any_section_access = permissions_service.require_any_section_access
require_section_access = permissions_service.require_section_access

# Create FastAPI app
app = FastAPI(
    title="Construction CRM API",
    description="CRM system for managing construction projects, Gantt planning, and financial calculations",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", settings.SECURITY_CSP)
    response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.middleware("http")
async def relativize_api_redirects(request: Request, call_next):
    """Kill the trailing-slash CSP bug class.

    FastAPI's redirect_slashes emits a 307 with an ABSOLUTE Location built
    from the backend host (e.g. http://localhost:8001/...). Behind the dev
    proxy that is cross-origin + http, so the page CSP
    (connect-src 'self' https:) blocks the follow-up request and the call
    silently fails. Rewriting the Location of such /api/* redirects to a
    relative path makes the browser follow it same-origin through the
    proxy. Scoped to /api/* so external redirects (OAuth, etc.) are
    untouched; routing behaviour is unchanged."""
    response = await call_next(request)
    if response.status_code in (301, 302, 303, 307, 308):
        location = response.headers.get("location")
        if location:
            from urllib.parse import urlsplit, urlunsplit
            parts = urlsplit(location)
            if (parts.scheme or parts.netloc) and (parts.path or "").startswith("/api/"):
                response.headers["location"] = urlunsplit(
                    ("", "", parts.path, parts.query, parts.fragment)
                )
    return response


def _api_rate_limit_client_key(request: Request) -> str:
    return client_ip(request) or "unknown"


@app.middleware("http")
async def enforce_api_rate_limit(request: Request, call_next):
    path = request.url.path
    if not path.startswith("/api/v1") or request.method == "OPTIONS":
        return await call_next(request)

    is_write = request.method.upper() not in {"GET", "HEAD", "OPTIONS"}
    limit = settings.API_RATE_LIMIT_WRITE_REQUESTS if is_write else settings.API_RATE_LIMIT_READ_REQUESTS
    retry_after = await consume_rate_limit(
        "api-write" if is_write else "api-read",
        _api_rate_limit_client_key(request),
        limit,
        settings.API_RATE_LIMIT_WINDOW_SECONDS,
    )
    if retry_after:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Слишком много запросов. Повторите через {retry_after} сек."},
            headers={"Retry-After": str(retry_after)},
        )
    return await call_next(request)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):(3000|3001|8080)$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", settings.CSRF_HEADER_NAME],
)

app.add_middleware(
    AuthMiddleware,
    open_paths={
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/verify-2fa",
        "/api/v1/auth/mobile/login",
        "/api/v1/auth/mobile/refresh",
        "/api/v1/auth/mobile/verify-2fa",
        # Test-sink event_bus — синтетический webhook-приёмник для smoke
        # тестов воркера. HMAC-проверка реализована логикой на стороне
        # endpoint; auth не нужен (это «внешний» приёмник по контракту).
        "/api/v1/event-bus/_test/webhook-sink",
    },
    open_prefixes=(
        "/health",
        "/api/v1/telegram/webhook/",
        # Inbound integrations: аутентификация по HMAC-подписи внутри
        # каждого приёмника + IP allow-list на уровне nginx; cookie-auth
        # и CSRF не нужны (это внешние клиенты).
        "/api/v1/integrations/",
    ),
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(deals_router, prefix="/api/v1/deals", tags=["deals"], dependencies=[Depends(require_section_access("projects"))])
app.include_router(leads_router, prefix="/api/v1/leads", tags=["leads"], dependencies=[Depends(require_section_access("leads"))])
app.include_router(companies_router, prefix="/api/v1/companies", tags=["companies"], dependencies=[Depends(require_section_access("companies"))])
app.include_router(stages_router, prefix="/api/v1/stages", tags=["stages"], dependencies=[Depends(require_section_access("projects"))])
app.include_router(finance_router, prefix="/api/v1/finance", tags=["finance"], dependencies=[Depends(require_any_section_access("finance", "treasury"))])
app.include_router(income_expense_router, prefix="/api/v1/income-expense", tags=["income-expense"], dependencies=[Depends(require_section_access("income_expense"))])
app.include_router(products_router, prefix="/api/v1/products", tags=["products"], dependencies=[Depends(require_any_section_access("catalog", "projects", "leads"))])
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"], dependencies=[Depends(require_section_access("tasks"))])
app.include_router(contracts_router, prefix="/api/v1/contracts", tags=["contracts"], dependencies=[Depends(require_section_access("contracts"))])
app.include_router(subcontractors_router, prefix="/api/v1/subcontractors", tags=["subcontractors"], dependencies=[Depends(require_section_access("contracts"))])
app.include_router(subcontractor_stages_router, prefix="/api/v1/subcontractor-stages", tags=["subcontractor-stages"], dependencies=[Depends(require_section_access("contracts"))])
app.include_router(subcontractor_products_router, prefix="/api/v1/subcontractor-products", tags=["subcontractor-products"], dependencies=[Depends(require_section_access("contracts"))])
app.include_router(executor_router, prefix="/api/v1", tags=["executor"], dependencies=[Depends(require_section_access("executor"))])
app.include_router(deal_execution_router, prefix="/api/v1", tags=["deal-execution"], dependencies=[Depends(require_section_access("projects"))])
app.include_router(outgoing_registry_router, prefix="/api/v1/outgoing-registry", tags=["outgoing-registry"], dependencies=[Depends(require_section_access("outgoing_registry"))])
app.include_router(document_registry_router, prefix="/api/v1/document-registry", tags=["document-registry"], dependencies=[Depends(require_section_access("document_registry"))])
app.include_router(files_catalog_router, prefix="/api/v1", tags=["files-catalog"], dependencies=[Depends(require_section_access("files_catalog"))])
# Per-folder ACL management — гейтится той же section_access (видеть/менять
# правила могут только те, у кого есть доступ к разделу), а на уровне самого
# роутера — MANAGE на конкретной папке через folder_acl.require_folder_perm.
app.include_router(file_folder_permissions_router, prefix="/api/v1", tags=["files-catalog-permissions"], dependencies=[Depends(require_section_access("files_catalog"))])
app.include_router(tenders_router, prefix="/api/v1/tenders", tags=["tenders"], dependencies=[Depends(require_any_section_access("tenders_admin", "tenders_subcontractor"))])
app.include_router(accreditations_router, prefix="/api/v1/accreditations", tags=["accreditations"], dependencies=[Depends(require_any_section_access("accreditations_admin", "accreditations_subcontractor"))])
app.include_router(roles_router, prefix="/api/v1/roles", tags=["roles"], dependencies=[Depends(require_section_access("roles"))])
app.include_router(org_structure_router, prefix="/api/v1/org-structure", tags=["org-structure"], dependencies=[Depends(require_section_access("org_structure"))])
app.include_router(support_router, prefix="/api/v1/support", tags=["support"], dependencies=[Depends(require_section_access("support"))])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(task_auctions_router, prefix="/api/v1", tags=["task-auctions"], dependencies=[Depends(require_any_section_access("task_auctions_manage", "task_auctions_bid"))])
app.include_router(penalty_rules_router, prefix="/api/v1/penalty-rules", tags=["penalty-rules"], dependencies=[Depends(require_section_access("tasks_penalties_manage"))])
app.include_router(result_reviews_router, prefix="/api/v1", tags=["result-reviews"], dependencies=[Depends(require_section_access("work_results_reviews"))])
app.include_router(kp_router, prefix="/api/v1", tags=["kp"], dependencies=[Depends(require_any_section_access("projects", "leads"))])
app.include_router(banks_router, prefix="/api/v1", tags=["banks"], dependencies=[Depends(require_any_section_access("finance", "treasury"))])
app.include_router(dadata_router, prefix="/api/v1", tags=["dadata"], dependencies=[Depends(permissions_service.require_section_read("companies"))])
app.include_router(legal_work_router, prefix="/api/v1/legal-work", tags=["legal-work"], dependencies=[Depends(require_section_access("legal_work"))])
app.include_router(uploads_router, prefix="/api/v1/uploads", tags=["uploads"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(notification_rules_router, prefix="/api/v1/notification-rules", tags=["notification-rules"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(notification_preferences_router, prefix="/api/v1/notification-preferences", tags=["notification-preferences"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(notification_subscriptions_router, prefix="/api/v1/notification-subscriptions", tags=["notification-subscriptions"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(telegram_notifications_router, prefix="/api/v1/telegram", tags=["telegram-notifications"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(audit_logs_router, prefix="/api/v1/audit-logs", tags=["audit-logs"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(storage_router, prefix="/api/v1", tags=["storage"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(mail_router, prefix="/api/v1/mail", tags=["mail"], dependencies=[Depends(require_section_access("mail"))])
app.include_router(task_messages_router, prefix="/api/v1", tags=["task-chat"], dependencies=[Depends(require_section_access("task_chat"))])
# Подзадачи (чек-лист) — гейт по секции `tasks` (как сама задача),
# per-task ACL внутри роутера через _require_task_access.
app.include_router(task_subtasks_router, prefix="/api/v1", tags=["task-subtasks"], dependencies=[Depends(require_section_access("tasks"))])
app.include_router(global_chat_router, prefix="/api/v1/chat", tags=["global-chat"], dependencies=[Depends(require_section_access("global_chat"))])
app.include_router(customer_portal_router, prefix="/api/v1/customer", tags=["customer-portal"], dependencies=[Depends(require_section_access("customer_portal"))])
app.include_router(data_health_router, prefix="/api/v1/data-health", tags=["data-health"], dependencies=[Depends(require_section_access("data_health"))])
# Public data-health endpoints — открытый набор для ГИПов/помощников
# которые видят свои проекты но не имеют отдельных прав на data_health.
# Сейчас тут только GET /deal-counts (индикатор «здоровья» в списке проектов).
app.include_router(data_health_public_router, prefix="/api/v1/data-health", tags=["data-health"], dependencies=[Depends(require_any_section_access("projects", "leads", "data_health"))])
app.include_router(document_templates_router, prefix="/api/v1/document-templates", tags=["document-templates"], dependencies=[Depends(require_section_access("document_templates"))])
app.include_router(approvals_router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
app.include_router(workday_router, prefix="/api/v1/workday", tags=["workday"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
# Профиль сотрудника — публично-читаемый, доступ любому авторизованному.
app.include_router(profiles_router, prefix="/api/v1/profiles", tags=["profiles"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
# Отсутствия — отдельная секция `absences`; collection-level гейт.
app.include_router(absences_router, prefix="/api/v1/absences", tags=["absences"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])
# Лента новостей — читают все авторизованные; постинг гейтит сам роутер (feed.edit_all).
app.include_router(feed_router, prefix="/api/v1/feed", tags=["feed"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])

# Event bus management — admin-only внутри роутера через _require_superuser.
# Test-sink (/_test/webhook-sink) намеренно без auth — синтетический приёмник.
app.include_router(event_bus_router, prefix="/api/v1/event-bus", tags=["event-bus"])

# Глобальный поиск (Step 0): доступен любому авторизованному. Per-section
# ACL применяется внутри роутера — пользователь не увидит результатов из
# секций, к которым у него нет даже read_assigned.
app.include_router(search_router, prefix="/api/v1", tags=["search"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])

# Reglaments — нормативная база. Чтение любому авторизованному (нормы =
# общесправочник); запись (upload, reindex) гейтит сам роутер через CurrentUser.
app.include_router(reglaments_router, prefix="/api/v1/reglaments", tags=["reglaments"], dependencies=[Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS))])

# Inbound integrations — приёмники вебхуков от внешних вендоров.
# Маршруты НЕ висят под cookie-auth/CSRF (см. open_prefixes выше);
# аутентификация — HMAC-подпись внутри каждого приёмника.
app.include_router(diadoc_inbound_router, prefix="/api/v1/integrations/diadoc", tags=["integrations-diadoc"])
app.include_router(telegram_inbound_router, prefix="/api/v1/integrations/telegram", tags=["integrations-telegram"])
app.include_router(onec_inbound_router, prefix="/api/v1/integrations/onec", tags=["integrations-onec"])
app.include_router(bank_inbound_router, prefix="/api/v1/integrations/bank", tags=["integrations-bank"])
app.include_router(gosklyuch_inbound_router, prefix="/api/v1/integrations/gosklyuch", tags=["integrations-gosklyuch"])

_static_local_root = getattr(settings, "STATIC_LOCAL_ROOT", "") or ""
STATIC_DIR = Path(_static_local_root).expanduser() if _static_local_root else Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/static/avatars/{filename:path}", include_in_schema=False)
async def block_public_avatar_access(filename: str):
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/static/wallpapers/{filename:path}", include_in_schema=False)
async def block_public_wallpaper_access(filename: str):
    # M2: user-uploaded wallpapers must not be reachable unauthenticated via
    # the /static mount; they are served through the authenticated
    # /api/v1/users/wallpaper-* endpoints instead.
    raise HTTPException(status_code=404, detail="Not found")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# OAuth callback (must match external redirect URI without /api/v1)
app.add_api_route(
    "/oauth/yandex/callback",
    yandex_oauth_callback,
    methods=["GET"],
    include_in_schema=False,
)


async def _auto_migrate_on_startup():
    """Run all idempotent schema migrations so the DB never silently
    drifts (missing column -> cryptic 500). Opt-in via AUTO_MIGRATE;
    defaults ON for the local test_portal variant, OFF elsewhere
    (prod runs migrations during deploy). Fully best-effort."""
    import os
    import logging

    default_on = (getattr(settings, "APP_VARIANT", "default") == "test_portal")
    flag = os.getenv("AUTO_MIGRATE")
    enabled = default_on if flag is None else flag.strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return
    log = logging.getLogger("uvicorn.error")
    try:
        from fastapi.concurrency import run_in_threadpool
        import migrate_all
        log.info("AUTO_MIGRATE: running idempotent schema migrations...")
        summary = await run_in_threadpool(migrate_all.run_all, False)
        if summary.get("failed"):
            log.error("AUTO_MIGRATE: %d migration(s) failed: %s "
                      "(run `python migrate_all.py` for details)",
                      len(summary["failed"]), summary["failed"])
        else:
            log.info("AUTO_MIGRATE: %d migrations ok, no drift.",
                     len(summary.get("ok", [])))
    except Exception as exc:  # noqa: BLE001 — never block startup
        log.error("AUTO_MIGRATE skipped due to error: %s", exc)


async def _check_security_store_backend():
    """H4: warn loudly (or fail fast if explicitly required) when the auth
    security store has no shared/persistent backend. Without Redis, token
    blacklist / logout / session revocation / login throttle / API rate limit
    live per-process and are lost on restart and across workers."""
    import logging

    from app.services.auth_security_store import _get_redis

    log = logging.getLogger("uvicorn.error")
    client = await _get_redis()
    if client is not None:
        return
    message = (
        "SECURITY: auth security store has NO Redis backend — token "
        "revocation, logout, session revocation, login throttle and API "
        "rate limit are per-process and lost on restart / not shared across "
        "workers. Set REDIS_URL (recommended) and run a single worker, or "
        "expect best-effort revocation only."
    )
    if settings.REQUIRE_PERSISTENT_SECURITY_STORE:
        raise RuntimeError(message)
    log.warning(message)


@app.on_event("startup")
async def bootstrap_chat():
    await _check_security_store_backend()
    await _auto_migrate_on_startup()
    ensure_customer_portal_role()
    ensure_telegram_notifications_schema()
    await ensure_data_health_schema()
    ensure_user_avatar_schema()
    ensure_user_two_factor_schema()
    ensure_stage_product_assignment_schema()
    ensure_contract_documents_schema()
    ensure_task_matrix_schema()
    ensure_deal_products_schema()
    ensure_company_documents_schema()
    ensure_outgoing_documents_schema()
    ensure_document_templates_schema()
    ensure_approval_schema()
    await ensure_chat_schema()
    cleanup_temp_uploads()
    # Event Bus v2: автодискавер in-process обработчиков. Они
    # регистрируются декоратором @on в модулях app/event_handlers/*.py.
    # Discovery идёт ПОСЛЕ всех ensure_* — чтобы хендлеры могли
    # безопасно ссылаться на готовые таблицы.
    try:
        from app.services.event_dispatcher import discover_handlers
        discover_handlers()
    except Exception as exc:
        log.exception("event_dispatcher discovery failed: %s", exc)

    # Step 1 поиска: eager-load embedding-модели если hybrid включён.
    # Без warmup'а первый запрос пользователя ждёт 20-40 сек на загрузке
    # bge-m3. С warmup'ом — стартап на 30 сек медленнее, но первый
    # search мгновенный.
    if os.environ.get("ENABLE_HYBRID_SEARCH") == "1":
        import logging as _logging
        _warmup_log = _logging.getLogger("uvicorn.error")
        try:
            from app.services.search_semantic import embed_query
            _warmup_log.info("Step 1 search: eager warmup of embedding model...")
            await embed_query("warmup")
            _warmup_log.info("Step 1 search: embedding model warmed up")
        except Exception as exc:
            _warmup_log.warning("eager warmup failed (search will lazy-load on first query): %s", exc)

@app.get("/")
async def root():
    return {"message": "Construction CRM API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
