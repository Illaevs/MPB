"""
AI assistant API router.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import Company, Deal, DealProduct, FinancialPlan, IncomeExpenseEntry, Stage
from app.schemas.ai import (
    AiAssistantChatRequest,
    AiAssistantChatResponse,
    AiStatusResponse,
    OutgoingAiAssistRequest,
    OutgoingAiAssistResponse,
)
from app.services.ai_service import (
    AIServiceError,
    ai_is_enabled,
    compact_scalar_mapping,
    list_preview,
    ollama_chat_json,
    ollama_tags,
)
from app.services.document_template_fields import get_template_fields
from app.services.permissions import allowed_deal_ids, get_sections_permissions
from app.routers.outgoing_registry import (
    _build_document_render_payload,
    _build_editor_resolved_fields,
    _build_transient_editor_document,
)


router = APIRouter()


OUTGOING_AI_ACTIONS = {
    "draft": "Сформируй новый деловой текст по задаче пользователя и контексту документа.",
    "improve": "Улучши текст без изменения фактов, имен, дат, сумм и структуры смысла.",
    "formalize": "Сделай текст более официальным и договорным по стилю, не придумывая новые факты.",
    "shorten": "Сократи текст, сохранив все важные факты, реквизиты и смысл.",
}

ASSISTANT_RELEVANT_SECTIONS = ("projects", "finance", "treasury", "income_expense")
ASSISTANT_SECTION_LABELS = {
    "projects": "сделки",
    "finance": "финансы",
    "treasury": "казначейство",
    "income_expense": "ДДС",
}
_SEARCH_STOPWORDS = {
    "и", "в", "во", "на", "по", "с", "со", "к", "ко", "у", "за", "от", "до",
    "для", "что", "как", "какой", "какая", "какие", "какое", "сколько", "где",
    "когда", "следующий", "следующая", "следующее", "платеж", "платежи", "сделке",
    "сделка", "проект", "проекта", "проекту", "месяц", "месяца", "этом", "этот",
    "этой", "нас", "есть", "ли", "по", "из", "факт", "план", "расход", "расходы",
}


def _normalize_search_text(value: Any) -> str:
    raw = str(value or "").strip().lower()
    return re.sub(r"[^0-9a-zа-яё]+", " ", raw, flags=re.IGNORECASE).strip()


def _tokenize_question(value: str) -> list[str]:
    normalized = _normalize_search_text(value)
    return [
        token
        for token in normalized.split()
        if len(token) >= 2 and token not in _SEARCH_STOPWORDS
    ]


def _safe_uuid(value: Any) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def _date_to_iso(value: Any) -> str | None:
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def _money_value(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except Exception:
        return 0.0


def _effective_plan_date(plan: FinancialPlan) -> date | None:
    return getattr(plan, "date_plan_start", None) or getattr(plan, "date_plan_end", None)


def _route_deal_id(page_context: Any) -> str | None:
    if not page_context:
        return None
    entity_type = str(getattr(page_context, "entity_type", "") or "").strip().lower()
    entity_id = str(getattr(page_context, "entity_id", "") or "").strip()
    if entity_type == "deal" and entity_id:
        return entity_id
    route_name = str(getattr(page_context, "route_name", "") or "").strip()
    params = getattr(page_context, "params", None) or {}
    if route_name == "ProjectDetail" and params.get("id"):
        return str(params.get("id"))
    return None


def _history_deal_ids(history: list[Any]) -> list[str]:
    deal_ids: list[str] = []
    seen = set()
    for item in reversed(history or []):
        for deal_id in list(getattr(item, "used_deal_ids", None) or []):
            normalized = str(deal_id or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deal_ids.append(normalized)
    return deal_ids


def _score_deal_match(question: str, tokens: list[str], deal: Deal, customer_name: str, our_company_name: str) -> int:
    title = str(getattr(deal, "title", "") or "")
    obj_name = str(getattr(deal, "obj_name", "") or "")
    address = str(getattr(deal, "address", "") or "")
    blob = _normalize_search_text(" ".join([title, obj_name, address, customer_name, our_company_name]))
    score = 0
    normalized_question = _normalize_search_text(question)
    for source in (title, obj_name):
        source_norm = _normalize_search_text(source)
        if source_norm and source_norm in normalized_question:
            score += 10
    for token in tokens:
        if token in blob:
            score += 2
        if token and token in _normalize_search_text(title):
            score += 3
        if token and token in _normalize_search_text(obj_name):
            score += 3
        if token and token in _normalize_search_text(customer_name):
            score += 2
    return score


def _serialize_payment_plan(plan: FinancialPlan, contractor_name: str) -> dict[str, Any]:
    return {
        "id": str(plan.id),
        "direction": str(plan.direction),
        "amount": _money_value(plan.amount_plan),
        "date": _date_to_iso(_effective_plan_date(plan)),
        "status": str(plan.payment_status or ""),
        "description": str(plan.description or "").strip() or None,
        "contractor_name": contractor_name or None,
        "stage_id": str(plan.stage_id) if getattr(plan, "stage_id", None) else None,
    }


def _format_money_rub(value: Any) -> str:
    amount = _money_value(value)
    formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} ₽"


def _format_iso_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = date.fromisoformat(raw[:10])
        return parsed.strftime("%d.%m.%Y")
    except ValueError:
        return raw


def _summarize_stage_progress(stages: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "total": len(stages),
        "planned": 0,
        "in_progress": 0,
        "completed": 0,
        "delayed": 0,
        "closed": 0,
        "next_stage": None,
        "active_stage": None,
    }
    if not stages:
        return summary

    today = date.today()
    next_stage = None
    active_stage = None
    for stage in stages:
        status = str(stage.get("status") or "planned")
        if status in summary:
            summary[status] += 1
        if stage.get("is_closed"):
            summary["closed"] += 1
        stage_end_raw = str(stage.get("date_end") or "").strip()
        stage_end = None
        try:
            if stage_end_raw:
                stage_end = date.fromisoformat(stage_end_raw[:10])
        except ValueError:
            stage_end = None
        if status == "in_progress" and not active_stage:
            active_stage = stage
        if status != "completed" and not stage.get("is_closed"):
            if not next_stage:
                next_stage = stage
            else:
                current = str(next_stage.get("date_start") or "")
                candidate = str(stage.get("date_start") or "")
                if candidate and (not current or candidate < current):
                    next_stage = stage
        if status not in {"completed", "delayed"} and stage_end and stage_end < today:
            summary["delayed"] += 1

    summary["next_stage"] = next_stage
    summary["active_stage"] = active_stage
    return summary


def _build_assistant_direct_answer(
    message: str,
    context_payload: dict[str, Any],
) -> tuple[str | None, list[str], list[str]]:
    normalized = _normalize_search_text(message)
    section_access = context_payload.get("section_access") or {}
    current_deal = context_payload.get("current_deal") or {}
    matching_deals = list(context_payload.get("matching_deals") or [])
    monthly_expenses = context_payload.get("monthly_expenses") or {}

    answer_parts: list[str] = []
    used_sections: list[str] = []
    used_deal_ids: list[str] = []

    asks_expenses = "расход" in normalized and "месяц" in normalized
    asks_payment = "плат" in normalized
    asks_products = any(token in normalized for token in ("товар", "продукт", "позици", "номенклат"))
    asks_gantt = any(token in normalized for token in ("гант", "этап", "разработк", "прогресс"))
    def candidate_deals() -> list[dict[str, Any]]:
        deals: list[dict[str, Any]] = []
        if current_deal and current_deal.get("id"):
            deals.append(current_deal)
        for item in matching_deals:
            if item.get("id") and all(str(existing.get("id")) != str(item.get("id")) for existing in deals):
                deals.append(item)
        return deals

    if asks_expenses:
        if not section_access.get("income_expense", {}).get("read_all") and not section_access.get("income_expense", {}).get("read_assigned"):
            answer_parts.append("У вас нет доступа к данным ДДС, поэтому я не могу показать расходы за месяц.")
        else:
            actual_total = _money_value(monthly_expenses.get("actual_total"))
            planned_total = _money_value(monthly_expenses.get("planned_total"))
            month_start = _format_iso_date(monthly_expenses.get("month_start")) or monthly_expenses.get("month_start")
            month_end = _format_iso_date(monthly_expenses.get("month_end")) or monthly_expenses.get("month_end")
            if actual_total > 0:
                part = f"Фактические расходы за период {month_start}–{month_end} составляют {_format_money_rub(actual_total)}."
            else:
                part = f"За период {month_start}–{month_end} фактические расходы пока не зафиксированы."
            if planned_total > 0:
                part += f" Плановые расходы на этот же период: {_format_money_rub(planned_total)}."
            top_actual = list(monthly_expenses.get("top_actual") or [])
            if top_actual:
                top_item = top_actual[0]
                deal_title = str(top_item.get("deal_title") or "").strip()
                payee_name = str(top_item.get("payee_name") or "").strip()
                top_bits = [f"Крупнейший факт: {_format_money_rub(top_item.get('amount'))}"]
                if deal_title:
                    top_bits.append(f"сделка «{deal_title}»")
                if payee_name:
                    top_bits.append(f"контрагент {payee_name}")
                part += " " + ", ".join(top_bits) + "."
            answer_parts.append(part)
            used_sections.append("income_expense")

    if asks_payment:
        finance_allowed = any(
            section_access.get(section, {}).get("read_all") or section_access.get(section, {}).get("read_assigned")
            for section in ("finance", "treasury", "projects")
        )
        if not finance_allowed:
            answer_parts.append("У вас нет доступа к платежному контуру, поэтому я не могу показать следующий платеж.")
        else:
            candidate_deals = candidate_deals()
            if len(candidate_deals) > 1 and not current_deal:
                options = ", ".join(
                    f"«{str(item.get('title') or item.get('obj_name') or item.get('id'))}»"
                    for item in candidate_deals[:5]
                )
                answer_parts.append(f"Нашел несколько подходящих сделок. Уточните, пожалуйста, какую именно имеете в виду: {options}.")
            elif candidate_deals:
                target_deal = candidate_deals[0]
                next_payments = list(target_deal.get("next_payments") or [])
                deal_label = str(target_deal.get("title") or target_deal.get("obj_name") or "сделке").strip()
                if next_payments:
                    next_payment = next_payments[0]
                    payment_date = _format_iso_date(next_payment.get("date")) or "без даты"
                    amount_text = _format_money_rub(next_payment.get("amount"))
                    contractor_name = str(next_payment.get("contractor_name") or "").strip()
                    description = str(next_payment.get("description") or "").strip()
                    payment_part = f"Следующий платеж по сделке «{deal_label}»: {payment_date}, {amount_text}"
                    if contractor_name:
                        payment_part += f", получатель {contractor_name}"
                    if description:
                        payment_part += f", основание: {description}"
                    payment_part += "."
                    answer_parts.append(payment_part)
                    used_deal_ids.append(str(target_deal.get("id")))
                    used_sections.extend(["projects", "finance"])
                else:
                    answer_parts.append(f"По сделке «{deal_label}» не найдено ближайших незакрытых плановых платежей.")
                    used_deal_ids.append(str(target_deal.get("id")))
                    used_sections.append("projects")
            else:
                answer_parts.append("Не нашел сделку по вашему запросу. Уточните название сделки или откройте карточку нужного проекта.")

    if asks_products:
        candidate_deals_list = candidate_deals()
        if len(candidate_deals_list) > 1 and not current_deal:
            options = ", ".join(
                f"«{str(item.get('title') or item.get('obj_name') or item.get('id'))}»"
                for item in candidate_deals_list[:5]
            )
            answer_parts.append(f"Нашел несколько подходящих сделок. Уточните, пожалуйста, по какой именно нужны товары: {options}.")
        elif candidate_deals_list:
            target_deal = candidate_deals_list[0]
            products = list(target_deal.get("products") or [])
            deal_label = str(target_deal.get("title") or target_deal.get("obj_name") or "сделке").strip()
            if products:
                preview = []
                for item in products[:8]:
                    name = str(item.get("name") or "Без названия").strip()
                    quantity = item.get("quantity")
                    unit = str(item.get("unit") or "").strip()
                    status = str(item.get("status") or "").strip()
                    chunk = name
                    if quantity not in (None, "", 0):
                        chunk += f" — {quantity:g}" if isinstance(quantity, float) else f" — {quantity}"
                        if unit:
                            chunk += f" {unit}"
                    if status:
                        chunk += f", статус {status}"
                    preview.append(chunk)
                suffix = ""
                if len(products) > len(preview):
                    suffix = f" Показал первые {len(preview)} из {len(products)}."
                answer_parts.append(f"По сделке «{deal_label}» товары: " + "; ".join(preview) + "." + suffix)
                used_deal_ids.append(str(target_deal.get("id")))
                used_sections.append("projects")
            else:
                answer_parts.append(f"По сделке «{deal_label}» товары пока не заведены.")
                used_deal_ids.append(str(target_deal.get("id")))
                used_sections.append("projects")
        else:
            answer_parts.append("Не нашел сделку по вашему запросу. Уточните название сделки или откройте карточку нужного проекта.")

    if asks_gantt:
        candidate_deals_list = candidate_deals()
        if len(candidate_deals_list) > 1 and not current_deal:
            options = ", ".join(
                f"«{str(item.get('title') or item.get('obj_name') or item.get('id'))}»"
                for item in candidate_deals_list[:5]
            )
            answer_parts.append(f"Нашел несколько подходящих сделок. Уточните, пожалуйста, по какой именно нужен гант: {options}.")
        elif candidate_deals_list:
            target_deal = candidate_deals_list[0]
            deal_label = str(target_deal.get("title") or target_deal.get("obj_name") or "сделке").strip()
            gantt_summary = target_deal.get("gantt_summary") or {}
            total = int(gantt_summary.get("total") or 0)
            if total <= 0:
                answer_parts.append(f"По сделке «{deal_label}» этапы для ганта пока не заведены.")
            else:
                in_progress = int(gantt_summary.get("in_progress") or 0)
                completed = int(gantt_summary.get("completed") or 0)
                delayed = int(gantt_summary.get("delayed") or 0)
                planned = int(gantt_summary.get("planned") or 0)
                part = (
                    f"По ганту сделки «{deal_label}»: всего этапов {total}, "
                    f"в работе {in_progress}, завершено {completed}, запланировано {planned}, просрочено {delayed}."
                )
                active_stage = gantt_summary.get("active_stage") or {}
                next_stage = gantt_summary.get("next_stage") or {}
                if active_stage.get("name"):
                    part += (
                        f" Сейчас в работе этап «{active_stage.get('name')}»"
                        f"{', срок до ' + _format_iso_date(active_stage.get('date_end')) if active_stage.get('date_end') else ''}."
                    )
                elif next_stage.get("name"):
                    part += (
                        f" Ближайший этап: «{next_stage.get('name')}»"
                        f"{', старт ' + _format_iso_date(next_stage.get('date_start')) if next_stage.get('date_start') else ''}"
                        f"{', окончание ' + _format_iso_date(next_stage.get('date_end')) if next_stage.get('date_end') else ''}."
                    )
                answer_parts.append(part)
            used_deal_ids.append(str(target_deal.get("id")))
            used_sections.append("projects")
        else:
            answer_parts.append("Не нашел сделку по вашему запросу. Уточните название сделки или откройте карточку нужного проекта.")

    if not answer_parts:
        return None, [], []

    normalized_sections = []
    for section in used_sections:
        if section not in normalized_sections:
            normalized_sections.append(section)
    normalized_deal_ids = []
    for deal_id in used_deal_ids:
        if deal_id and deal_id not in normalized_deal_ids:
            normalized_deal_ids.append(deal_id)

    return " ".join(answer_parts), normalized_sections, normalized_deal_ids


def _outgoing_ai_system_prompt() -> str:
    return (
        "Ты внутренний AI-ассистент Nexus ERP для подготовки исходящих документов. "
        "Всегда отвечай по-русски. "
        "Нельзя придумывать отсутствующие факты, даты, номера, суммы, имена, компании, этапы или реквизиты. "
        "Можно использовать только данные из переданного контекста. "
        "Если данных не хватает, опускай фразу или используй только доступные плейсхолдеры. "
        "Если используешь системные поля, вставляй их строго в формате {{ field.key }}. "
        "Разрешенные HTML-теги в ответе: p, br, ul, ol, li, strong, em. "
        "Не используй markdown, code fences, таблицы и пояснения вне JSON. "
        "Верни только JSON-объект вида "
        "{\"html\":\"<p>...</p>\",\"text\":\"...\",\"used_fields\":[\"field.key\"],\"warnings\":[],\"summary\":\"...\"}."
    )


def _build_outgoing_ai_context(render_payload: dict[str, Any], document_kind: str) -> dict[str, Any]:
    resolved_fields = _build_editor_resolved_fields(render_payload, document_kind)
    document_payload = render_payload.get("document") or {}
    deal_payload = render_payload.get("deal") or {}
    contract_payload = render_payload.get("contract") or {}
    recipient_payload = render_payload.get("recipient") or {}
    our_company_payload = render_payload.get("our_company") or {}
    stages_payload = render_payload.get("stages") or []
    payment_payload = render_payload.get("linked_payment_items") or []

    available_fields = get_template_fields(module="outgoing_registry", document_kind=document_kind)
    return {
        "document_kind": document_kind,
        "document": {
            key: document_payload.get(key)
            for key in ["kind", "kind_label", "outgoing_number", "letter_date", "subject", "basis", "payment_due_date"]
            if document_payload.get(key) not in (None, "")
        },
        "deal": {
            key: deal_payload.get(key)
            for key in ["title", "obj_name", "address", "vat_rate", "vat_included"]
            if deal_payload.get(key) not in (None, "")
        },
        "contract": {
            key: contract_payload.get(key)
            for key in ["number", "date", "formatted_title", "type", "status", "total_amount"]
            if contract_payload.get(key) not in (None, "")
        },
        "recipient": {
            key: recipient_payload.get(key)
            for key in ["name", "short_name", "eio", "to_name", "genitive_name", "address", "inn", "kpp"]
            if recipient_payload.get(key) not in (None, "")
        },
        "our_company": {
            key: our_company_payload.get(key)
            for key in ["name", "short_name", "full_name", "address", "inn", "kpp", "director_name", "director_name_short", "bank_name", "bank_bik", "bank_account", "bank_correspondent_account"]
            if our_company_payload.get(key) not in (None, "")
        },
        "stages_preview": list_preview(stages_payload, ["name", "date_start", "date_end", "status", "amount"], limit=12),
        "payments_preview": list_preview(payment_payload, ["entry_number", "entry_date", "amount", "allocated_amount", "kind", "note"], limit=12),
        "resolved_fields": compact_scalar_mapping(resolved_fields, limit=80),
        "available_fields": [
            {
                "key": str(item.get("key") or ""),
                "label": str(item.get("label") or ""),
            }
            for item in available_fields
            if str(item.get("key") or "").strip()
        ],
    }


def _build_outgoing_ai_user_prompt(request_payload: OutgoingAiAssistRequest, context_payload: dict[str, Any]) -> str:
    action_instruction = OUTGOING_AI_ACTIONS.get(request_payload.action, OUTGOING_AI_ACTIONS["improve"])
    current_html = (request_payload.current_html or "").strip()
    selection_text = (request_payload.selection_text or "").strip()
    user_prompt = (request_payload.prompt or "").strip()
    return (
        f"Действие: {request_payload.action}\n"
        f"Инструкция для модели: {action_instruction}\n\n"
        f"Пользовательская задача:\n{user_prompt or 'Не указана'}\n\n"
        f"Выделенный текст:\n{selection_text or '[нет выделения]'}\n\n"
        f"Текущий HTML блока:\n{current_html or '[пусто]'}\n\n"
        f"Контекст документа JSON:\n{json.dumps(context_payload, ensure_ascii=False)}\n\n"
        "Если есть выделенный текст, работай прежде всего с ним. "
        "Если выделения нет, работай со всем текущим блоком. "
        "Если нужно подставить данные системы, используй только плейсхолдеры из available_fields."
    )


async def _build_assistant_context(
    payload: AiAssistantChatRequest,
    request: Request,
    db: AsyncSession,
    user: Any,
) -> dict[str, Any]:
    permissions = await get_sections_permissions(db, user.role_id, ASSISTANT_RELEVANT_SECTIONS)
    section_access = {
        section: {
            "read_all": bool(permissions.get(section, (False, False))[0]),
            "read_assigned": bool(permissions.get(section, (False, False))[1]),
        }
        for section in ASSISTANT_RELEVANT_SECTIONS
    }
    has_global_access = any(item["read_all"] for item in section_access.values())
    has_scoped_access = any(item["read_assigned"] for item in section_access.values())
    visible_deal_ids = None if has_global_access else (await allowed_deal_ids(db, request, user) if has_scoped_access else [])

    question = str(payload.message or "").strip()
    tokens = _tokenize_question(question)
    route_deal_id = _route_deal_id(payload.page_context)
    history_deal_ids = _history_deal_ids(payload.history)
    preferred_deal_ids = [deal_id for deal_id in [route_deal_id, *history_deal_ids] if str(deal_id or "").strip()]

    visible_deals: list[Deal] = []
    deal_query = select(Deal)
    if visible_deal_ids is None:
        visible_deals = (await db.execute(deal_query)).scalars().all()
    elif visible_deal_ids:
        visible_deals = (await db.execute(deal_query.where(Deal.id.in_(visible_deal_ids)))).scalars().all()

    company_ids = set()
    for deal in visible_deals:
        if getattr(deal, "customer_id", None):
            company_ids.add(str(deal.customer_id))
        if getattr(deal, "our_company_id", None):
            company_ids.add(str(deal.our_company_id))

    company_map: dict[str, Company] = {}
    if company_ids:
        company_result = await db.execute(select(Company).where(Company.id.in_(list(company_ids))))
        company_map = {str(item.id): item for item in company_result.scalars().all()}

    matched_deals: list[Deal] = []
    if visible_deals and (tokens or preferred_deal_ids):
        scored: list[tuple[int, Deal]] = []
        for deal in visible_deals:
            customer_name = str(getattr(company_map.get(str(getattr(deal, "customer_id", "") or "")), "name", "") or "")
            our_company_name = str(getattr(company_map.get(str(getattr(deal, "our_company_id", "") or "")), "name", "") or "")
            score = _score_deal_match(question, tokens, deal, customer_name, our_company_name)
            if preferred_deal_ids and str(deal.id) in {str(item) for item in preferred_deal_ids}:
                score += 50
            if score > 0:
                scored.append((score, deal))
        scored.sort(key=lambda item: (-item[0], str(item[1].title or "")))
        matched_deals = [item[1] for item in scored[:5]]

    current_deal = next((deal for deal in visible_deals if preferred_deal_ids and str(deal.id) in {str(item) for item in preferred_deal_ids}), None)
    if current_deal and all(str(item.id) != str(current_deal.id) for item in matched_deals):
        matched_deals.insert(0, current_deal)
        matched_deals = matched_deals[:5]

    matched_deal_ids = [str(item.id) for item in matched_deals]
    deal_context_ids = []
    for deal_id in [str(current_deal.id)] if current_deal else []:
        if deal_id not in deal_context_ids:
            deal_context_ids.append(deal_id)
    for deal_id in matched_deal_ids:
        if deal_id not in deal_context_ids:
            deal_context_ids.append(deal_id)
    financial_plans: list[FinancialPlan] = []
    if deal_context_ids and (
        section_access["finance"]["read_all"]
        or section_access["finance"]["read_assigned"]
        or section_access["treasury"]["read_all"]
        or section_access["treasury"]["read_assigned"]
    ):
        financial_plan_ids = [deal_id for deal_id in (_safe_uuid(value) for value in deal_context_ids) if deal_id]
        if financial_plan_ids:
            plan_result = await db.execute(select(FinancialPlan).where(FinancialPlan.deal_id.in_(financial_plan_ids)))
            financial_plans = plan_result.scalars().all()
            contractor_ids = {str(item.contractor_id) for item in financial_plans if getattr(item, "contractor_id", None)}
            if contractor_ids:
                contractor_result = await db.execute(select(Company).where(Company.id.in_(list(contractor_ids))))
                for company in contractor_result.scalars().all():
                    company_map[str(company.id)] = company

    plans_by_deal: dict[str, list[FinancialPlan]] = {}
    for plan in financial_plans:
        plans_by_deal.setdefault(str(getattr(plan, "deal_id", "") or ""), []).append(plan)

    products_by_deal: dict[str, list[dict[str, Any]]] = {}
    stages_by_deal: dict[str, list[dict[str, Any]]] = {}
    if deal_context_ids and (section_access["projects"]["read_all"] or section_access["projects"]["read_assigned"]):
        for deal_id in deal_context_ids:
            deal_products = await DealProduct.get_by_deal(db, deal_id)
            product_payload = []
            for item in deal_products:
                product_name = str(item.custom_name or (item.product.name if item.product else "Без названия")).strip()
                product_payload.append(
                    {
                        "id": str(item.id),
                        "name": product_name,
                        "quantity": float(item.quantity or 0),
                        "unit": str(item.unit or "").strip(),
                        "status": str(item.status or "planned"),
                        "final_price": _money_value(item.final_price),
                        "tax_rate": float(item.tax_rate or 0),
                    }
                )
            product_payload.sort(key=lambda entry: entry["name"].lower())
            products_by_deal[str(deal_id)] = product_payload

            deal_stages = await Stage.get_by_deal_id(db, deal_id)
            stage_payload = []
            for stage in deal_stages:
                stage_payload.append(
                    {
                        "id": str(stage.id),
                        "name": str(stage.name or "").strip(),
                        "date_start": _date_to_iso(getattr(stage, "date_start", None)),
                        "date_end": _date_to_iso(getattr(stage, "date_end", None)),
                        "close_date": _date_to_iso(getattr(stage, "close_date", None)),
                        "status": str(getattr(stage, "status", "") or "planned"),
                        "is_closed": bool(getattr(stage, "is_closed", False)),
                        "planned_cost": _money_value(getattr(stage, "planned_cost", 0)),
                        "actual_cost": _money_value(getattr(stage, "actual_cost", 0)),
                    }
                )
            stage_payload.sort(key=lambda entry: (entry["date_start"] or "9999-12-31", entry["name"]))
            stages_by_deal[str(deal_id)] = stage_payload

    month_start = date.today().replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)

    expense_entries: list[IncomeExpenseEntry] = []
    if section_access["income_expense"]["read_all"] or section_access["income_expense"]["read_assigned"]:
        expense_query = select(IncomeExpenseEntry).where(
            IncomeExpenseEntry.direction == "expense",
            or_(
                and_(IncomeExpenseEntry.actual_date.is_not(None), IncomeExpenseEntry.actual_date >= month_start, IncomeExpenseEntry.actual_date <= month_end),
                and_(IncomeExpenseEntry.plan_date.is_not(None), IncomeExpenseEntry.plan_date >= month_start, IncomeExpenseEntry.plan_date <= month_end),
            ),
        )
        if visible_deal_ids is None:
            pass
        elif visible_deal_ids:
            expense_query = expense_query.where(IncomeExpenseEntry.deal_id.in_(visible_deal_ids))
        else:
            expense_query = None
        if expense_query is not None:
            expense_result = await db.execute(expense_query)
            expense_entries = expense_result.scalars().all()
            payee_ids = {str(item.payee_id) for item in expense_entries if item.payee_id}
            if payee_ids:
                payee_result = await db.execute(select(Company).where(Company.id.in_(list(payee_ids))))
                for company in payee_result.scalars().all():
                    company_map[str(company.id)] = company

    actual_expenses = [item for item in expense_entries if item.actual_date and month_start <= item.actual_date <= month_end]
    planned_expenses = [item for item in expense_entries if item.plan_date and month_start <= item.plan_date <= month_end]
    deal_lookup = {str(item.id): item for item in visible_deals}

    def _deal_to_summary(deal: Deal) -> dict[str, Any]:
        customer_name = str(getattr(company_map.get(str(getattr(deal, "customer_id", "") or "")), "name", "") or "")
        our_company_name = str(getattr(company_map.get(str(getattr(deal, "our_company_id", "") or "")), "name", "") or "")
        plans = plans_by_deal.get(str(deal.id), [])
        upcoming = [
            plan for plan in plans
            if _effective_plan_date(plan) and _effective_plan_date(plan) >= date.today() and str(plan.payment_status or "") != "paid"
        ]
        upcoming = sorted(upcoming, key=lambda item: _effective_plan_date(item) or date.max)
        return {
            "id": str(deal.id),
            "title": str(deal.title or ""),
            "obj_name": str(getattr(deal, "obj_name", "") or ""),
            "address": str(getattr(deal, "address", "") or ""),
            "status": str(getattr(deal, "status", "") or ""),
            "customer_name": customer_name or None,
            "our_company_name": our_company_name or None,
            "total_contract_value": _money_value(getattr(deal, "total_contract_value", 0)),
            "total_paid": _money_value(getattr(deal, "total_paid", 0)),
            "next_payments": [
                {
                    **_serialize_payment_plan(plan, str(getattr(company_map.get(str(getattr(plan, "contractor_id", "") or "")), "name", "") or "")),
                }
                for plan in upcoming[:3]
            ],
            "products": products_by_deal.get(str(deal.id), [])[:12],
            "stages": stages_by_deal.get(str(deal.id), [])[:12],
            "gantt_summary": _summarize_stage_progress(stages_by_deal.get(str(deal.id), [])),
        }

    monthly_expenses = {
        "month_start": month_start.isoformat(),
        "month_end": month_end.isoformat(),
        "actual_total": round(sum(_money_value(item.amount) for item in actual_expenses), 2),
        "planned_total": round(sum(_money_value(item.amount) for item in planned_expenses), 2),
        "actual_count": len(actual_expenses),
        "planned_count": len(planned_expenses),
        "top_actual": [
            {
                "id": str(item.id),
                "amount": _money_value(item.amount),
                "actual_date": _date_to_iso(item.actual_date),
                "plan_date": _date_to_iso(item.plan_date),
                "deal_title": str(getattr(deal_lookup.get(str(item.deal_id)), "title", "") or ""),
                "payee_name": str(getattr(company_map.get(str(item.payee_id or "")), "name", "") or ""),
                "category_code": str(item.category_code or "") or None,
            }
            for item in sorted(actual_expenses, key=lambda entry: (_money_value(entry.amount), _date_to_iso(entry.actual_date) or ""), reverse=True)[:8]
        ],
    }

    return {
        "today": date.today().isoformat(),
        "question_tokens": tokens,
        "available_sections": [section for section, access in section_access.items() if access["read_all"] or access["read_assigned"]],
        "section_access": section_access,
        "page_context": payload.page_context.model_dump() if payload.page_context else None,
        "current_deal": _deal_to_summary(current_deal) if current_deal else None,
        "matching_deals": [_deal_to_summary(item) for item in matched_deals],
        "monthly_expenses": monthly_expenses,
    }


def _assistant_system_prompt() -> str:
    return (
        "Ты универсальный AI-ассистент Nexus ERP. "
        "Отвечай только по данным из переданного JSON-контекста и только по-русски. "
        "Нельзя придумывать сделки, платежи, расходы, даты, суммы, компании и статусы. "
        "Если данных недостаточно или у пользователя нет доступа к разделу, скажи это прямо. "
        "Если найдено несколько похожих сделок, попроси уточнить и перечисли варианты. "
        "Под фразой 'расходы за этот месяц' по умолчанию понимай факт по actual_date, а план отдельно оговаривай как план. "
        "Под 'следующим платежом' понимай ближайшую запись из next_payments. "
        "Верни только JSON-объект вида {\"answer\":\"...\",\"warnings\":[],\"used_deal_ids\":[],\"used_sections\":[]}."
    )


def _assistant_user_prompt(payload: AiAssistantChatRequest, context_payload: dict[str, Any]) -> str:
    history_items = []
    for item in payload.history[-8:]:
        role = "Пользователь" if item.role == "user" else "Ассистент"
        history_items.append(f"{role}: {item.content}")
    history_text = "\n".join(history_items) if history_items else "[история пуста]"
    return (
        f"История диалога:\n{history_text}\n\n"
        f"Новый вопрос пользователя:\n{payload.message}\n\n"
        f"JSON-контекст CRM:\n{json.dumps(context_payload, ensure_ascii=False)}\n\n"
        "Ответь кратко и по делу. Если вопрос подразумевает расчет, используй только данные из JSON-контекста."
    )


@router.get("/status", response_model=AiStatusResponse)
async def get_ai_status():
    if not ai_is_enabled():
        return AiStatusResponse(enabled=False, detail="AI assistant is disabled in configuration")
    try:
        payload = await ollama_tags()
    except AIServiceError as exc:
        return AiStatusResponse(enabled=True, model=None, reachable=False, detail=str(exc))
    models = payload.get("models") or []
    available_models = {
        str(model.get("name") or "").strip()
        for model in models
        if isinstance(model, dict) and str(model.get("name") or "").strip()
    }
    configured_model = (settings.AI_MODEL or "").strip() or None
    active_model = configured_model or (next(iter(available_models)) if available_models else None)
    detail = None
    if configured_model and configured_model not in available_models:
        detail = f"Configured model '{configured_model}' is not available in Ollama"
    return AiStatusResponse(
        enabled=True,
        provider="ollama",
        model=active_model,
        reachable=True,
        detail=detail,
    )


@router.post("/outgoing/assist", response_model=OutgoingAiAssistResponse)
async def assist_outgoing_document(
    payload: OutgoingAiAssistRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not ai_is_enabled():
        raise HTTPException(status_code=503, detail="AI assistant is disabled")

    preview_context = await _build_transient_editor_document(payload.document_payload, request, db, user)
    transient_document = preview_context.get("transient_document")
    if transient_document is None:
        raise HTTPException(status_code=400, detail="Recipient company is required for AI assistant")

    render_payload = await _build_document_render_payload(db, transient_document)
    document_kind = preview_context["document_kind"]
    context_payload = _build_outgoing_ai_context(render_payload, document_kind)
    prompt = _build_outgoing_ai_user_prompt(payload, context_payload)
    try:
        ai_response = await ollama_chat_json(
            system_prompt=_outgoing_ai_system_prompt(),
            user_prompt=prompt,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    html_value = str(ai_response.get("html") or "").strip()
    text_value = str(ai_response.get("text") or "").strip()
    if not html_value and not text_value:
        raise HTTPException(status_code=502, detail="AI returned empty response")

    return OutgoingAiAssistResponse(
        action=payload.action,
        model=str(ai_response.get("model") or ""),
        html=html_value,
        text=text_value,
        used_fields=list(ai_response.get("used_fields") or []),
        warnings=list(ai_response.get("warnings") or []),
        summary=ai_response.get("summary"),
        raw=ai_response.get("raw"),
    )


@router.post("/assistant/chat", response_model=AiAssistantChatResponse)
async def chat_with_assistant(
    payload: AiAssistantChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not ai_is_enabled():
        raise HTTPException(status_code=503, detail="AI assistant is disabled")

    message = str(payload.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    context_payload = await _build_assistant_context(payload, request, db, user)
    direct_answer, direct_sections, direct_deal_ids = _build_assistant_direct_answer(message, context_payload)
    if direct_answer:
        return AiAssistantChatResponse(
            answer=direct_answer,
            model="rule-based",
            warnings=[],
            used_deal_ids=direct_deal_ids,
            used_sections=direct_sections,
            raw={"source": "rule-based", "context": {"sections": direct_sections, "deal_ids": direct_deal_ids}},
        )

    prompt = _assistant_user_prompt(payload, context_payload)
    try:
        ai_response = await ollama_chat_json(
            system_prompt=_assistant_system_prompt(),
            user_prompt=prompt,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    answer = str(ai_response.get("answer") or "").strip()
    if not answer:
        raise HTTPException(status_code=502, detail="AI returned empty response")

    used_deal_ids = [
        str(item)
        for item in (ai_response.get("used_deal_ids") or [])
        if str(item or "").strip()
    ]
    if not used_deal_ids:
        current_deal = context_payload.get("current_deal") or {}
        if current_deal.get("id"):
            used_deal_ids = [str(current_deal.get("id"))]

    used_sections = [
        str(item)
        for item in (ai_response.get("used_sections") or [])
        if str(item or "").strip()
    ]
    if not used_sections:
        used_sections = list(context_payload.get("available_sections") or [])

    return AiAssistantChatResponse(
        answer=answer,
        model=str(ai_response.get("model") or settings.AI_MODEL or ""),
        warnings=list(ai_response.get("warnings") or []),
        used_deal_ids=used_deal_ids,
        used_sections=used_sections,
        raw=ai_response.get("raw"),
    )
