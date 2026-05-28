import hashlib
import json
import logging
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import String, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Contract,
    DataHealthIssue,
    Deal,
    DealProduct,
    OutgoingDocument,
    Stage,
    StageDependency,
    StageProductAssignment,
    StageProductLink,
    StageProductSubtask,
)
from app.models.stage_dependency import normalize_dependency_type

logger = logging.getLogger(__name__)

RESOLVED_STATUS = "resolved"
OPEN_STATUS = "open"
IGNORED_STATUS = "ignored"
ACTIVE_STATUSES = {OPEN_STATUS, IGNORED_STATUS}
TERMINAL_STATUSES = {
    "completed",
    "done",
    "closed",
    "ready",
    "finished",
    "resolved",
    "approved",
    "success",
}
ORPHAN_ISSUE_TYPES = {"outgoing_without_deal", "contract_without_deal"}


def _normalized_column(column):
    return func.replace(func.lower(cast(column, String)), "-", "")


def _normalize_uuid_like(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    try:
        parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return parsed.hex
    except (ValueError, TypeError):
        return str(value).replace("-", "").strip().lower() or None


def _matches(column, value: Any):
    normalized = _normalize_uuid_like(value)
    if not normalized:
        return _normalized_column(column) == "__never_match__"
    return _normalized_column(column) == normalized


def _in_values(column, values: Iterable[Any]):
    normalized = [value for value in (_normalize_uuid_like(item) for item in values) if value]
    if not normalized:
        return _normalized_column(column).in_(["__never_match__"])
    return _normalized_column(column).in_(normalized)


def _safe_date(value: Any) -> Optional[date]:
    return value if isinstance(value, date) else None


def _is_terminal_status(value: Any) -> bool:
    normalized = str(value or "").strip().lower()
    return normalized in TERMINAL_STATUSES


def _is_assignment_started(assignment: StageProductAssignment) -> bool:
    start_date = _safe_date(getattr(assignment, "start_date", None))
    status = str(getattr(assignment, "status", "") or "").strip().lower()
    return bool(start_date or status not in {"", "not_started", "planned"})


def _is_stage_closed(stage: Stage) -> bool:
    return bool(getattr(stage, "is_closed", False)) or str(getattr(stage, "status", "")).strip().lower() == "completed"


def _stage_finish_date(stage: Stage) -> Optional[date]:
    close_date = _safe_date(getattr(stage, "close_date", None))
    if close_date and _is_stage_closed(stage):
        return close_date
    return _safe_date(getattr(stage, "date_end", None)) or _safe_date(getattr(stage, "date_start", None))


def _stage_display_name(stage: Optional[Stage]) -> str:
    return (getattr(stage, "name", None) or "Этап").strip()


def _date_to_label(value: Optional[date]) -> str:
    if not value:
        return "не задано"
    return value.strftime("%d.%m.%Y")


def _deal_display_title(deal: Optional[Deal]) -> str:
    if not deal:
        return "Сделка"
    return (deal.title or deal.obj_name or deal.address or "Сделка").strip()


def _product_display_name(deal_product: Optional[DealProduct]) -> str:
    if not deal_product:
        return "Товар"
    custom_name = getattr(deal_product, "custom_name", None)
    product = getattr(deal_product, "product", None)
    product_name = getattr(product, "name", None) if product else None
    return (custom_name or product_name or "Товар").strip()


def _payload_fingerprint(data: Dict[str, Any]) -> str:
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    return value


def _build_issue(
    *,
    issue_type: str,
    module: str,
    severity: str,
    title: str,
    description: str,
    scope_type: str,
    scope_id: Optional[Any] = None,
    deal_id: Optional[Any] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = _json_safe_value(payload or {})
    fingerprint = _payload_fingerprint(
        {
            "issue_type": issue_type,
            "scope_type": scope_type,
            "scope_id": _normalize_uuid_like(scope_id),
            "deal_id": _normalize_uuid_like(deal_id),
            "module": module,
            "payload": payload,
        }
    )
    return {
        "fingerprint": fingerprint,
        "deal_id": str(deal_id) if deal_id is not None else None,
        "scope_type": scope_type,
        "scope_id": str(scope_id) if scope_id is not None else None,
        "issue_type": issue_type,
        "module": module,
        "severity": severity,
        "status": OPEN_STATUS,
        "title": title,
        "description": description,
        "payload_json": payload,
    }


async def _load_deal_context(db: AsyncSession, deal_id: str) -> Dict[str, Any]:
    deal_result = await db.execute(select(Deal).where(_matches(Deal.id, deal_id)))
    deal = deal_result.scalar_one_or_none()

    stages_result = await db.execute(select(Stage).where(_matches(Stage.deal_id, deal_id)))
    stages = stages_result.scalars().all()
    stage_ids = [_normalize_uuid_like(stage.id) for stage in stages]

    dependencies: List[StageDependency] = []
    if stage_ids:
        dep_result = await db.execute(
            select(StageDependency).where(
                _in_values(StageDependency.predecessor_id, stage_ids) | _in_values(StageDependency.successor_id, stage_ids)
            )
        )
        dependencies = dep_result.scalars().all()

    links_result = await db.execute(select(StageProductLink).where(_matches(StageProductLink.deal_id, deal_id)))
    links = links_result.scalars().all()

    deal_products_result = await db.execute(
        select(DealProduct)
        .options(selectinload(DealProduct.product))
        .where(_matches(DealProduct.deal_id, deal_id))
    )
    deal_products = deal_products_result.scalars().all()

    assignments_result = await db.execute(select(StageProductAssignment).where(_matches(StageProductAssignment.deal_id, deal_id)))
    assignments = assignments_result.scalars().all()

    contracts_result = await db.execute(select(Contract).where(_matches(Contract.deal_id, deal_id)))
    contracts = contracts_result.scalars().all()

    assignment_ids = [assignment.id for assignment in assignments]
    subtasks: List[StageProductSubtask] = []
    if assignment_ids:
        subtasks_result = await db.execute(select(StageProductSubtask).where(StageProductSubtask.assignment_id.in_(assignment_ids)))
        subtasks = subtasks_result.scalars().all()

    return {
        "deal": deal,
        "stages": stages,
        "dependencies": dependencies,
        "links": links,
        "deal_products": deal_products,
        "assignments": assignments,
        "subtasks": subtasks,
        "contracts": contracts,
    }


def _collect_deal_issues(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    deal: Optional[Deal] = context["deal"]
    if not deal:
        return []

    deal_id = str(deal.id)
    issues: List[Dict[str, Any]] = []

    stages: List[Stage] = context["stages"]
    dependencies: List[StageDependency] = context["dependencies"]
    links: List[StageProductLink] = context["links"]
    deal_products: List[DealProduct] = context["deal_products"]
    assignments: List[StageProductAssignment] = context["assignments"]
    subtasks: List[StageProductSubtask] = context["subtasks"]
    contracts: List[Contract] = context["contracts"]

    if not deal.customer_id:
        issues.append(
            _build_issue(
                issue_type="deal_without_customer",
                module="projects",
                severity="warning",
                title="Сделка без заказчика",
                description=f'В сделке "{_deal_display_title(deal)}" не указан заказчик.',
                scope_type="deal",
                scope_id=deal.id,
                deal_id=deal_id,
                payload={"deal_id": deal_id, "deal_title": _deal_display_title(deal)},
            )
        )

    if not deal.our_company_id:
        issues.append(
            _build_issue(
                issue_type="deal_without_our_company",
                module="projects",
                severity="warning",
                title="Сделка без нашей компании",
                description=f'В сделке "{_deal_display_title(deal)}" не указана наша компания.',
                scope_type="deal",
                scope_id=deal.id,
                deal_id=deal_id,
                payload={"deal_id": deal_id, "deal_title": _deal_display_title(deal)},
            )
        )

    stage_by_id = {_normalize_uuid_like(stage.id): stage for stage in stages}
    children_by_parent: Dict[str, List[Stage]] = defaultdict(list)
    for stage in stages:
        parent_id = _normalize_uuid_like(stage.parent_id)
        if parent_id:
            children_by_parent[parent_id].append(stage)

    assignments_by_stage: Dict[str, List[StageProductAssignment]] = defaultdict(list)
    assignment_pairs = set()
    for assignment in assignments:
        stage_key = _normalize_uuid_like(assignment.stage_id)
        product_key = _normalize_uuid_like(assignment.product_id)
        if stage_key:
            assignments_by_stage[stage_key].append(assignment)
        if stage_key and product_key:
            assignment_pairs.add((stage_key, product_key))

    subtasks_by_assignment: Dict[str, List[StageProductSubtask]] = defaultdict(list)
    for subtask in subtasks:
        subtasks_by_assignment[str(subtask.assignment_id)].append(subtask)

    deal_product_by_id = {_normalize_uuid_like(item.id): item for item in deal_products}
    deal_product_by_product_id = {_normalize_uuid_like(item.product_id): item for item in deal_products}

    for stage in stages:
        if stage.date_start and stage.date_end and stage.date_end < stage.date_start:
            issues.append(
                _build_issue(
                    issue_type="stage_invalid_range",
                    module="stages",
                    severity="error",
                    title="Диапазон этапа некорректен",
                    description=(
                        f'Этап "{_stage_display_name(stage)}" заканчивается {_date_to_label(stage.date_end)} '
                        f'раньше старта {_date_to_label(stage.date_start)}.'
                    ),
                    scope_type="stage",
                    scope_id=stage.id,
                    deal_id=deal_id,
                    payload={
                        "stage_id": str(stage.id),
                        "stage_name": _stage_display_name(stage),
                        "date_start": stage.date_start,
                        "date_end": stage.date_end,
                    },
                )
            )
        close_date = _safe_date(getattr(stage, "close_date", None))
        if close_date and stage.date_start and stage.date_end and not (stage.date_start <= close_date <= stage.date_end):
            issues.append(
                _build_issue(
                    issue_type="stage_close_date_outside_range",
                    module="stages",
                    severity="warning",
                    title="Дата закрытия этапа вне диапазона",
                    description=(
                        f'Этап "{_stage_display_name(stage)}" закрыт датой {_date_to_label(close_date)}, '
                        f'которая не попадает в диапазон {_date_to_label(stage.date_start)} - {_date_to_label(stage.date_end)}.'
                    ),
                    scope_type="stage",
                    scope_id=stage.id,
                    deal_id=deal_id,
                    payload={
                        "stage_id": str(stage.id),
                        "stage_name": _stage_display_name(stage),
                        "date_start": stage.date_start,
                        "date_end": stage.date_end,
                        "close_date": close_date,
                    },
                )
            )

    for dependency in dependencies:
        predecessor = stage_by_id.get(_normalize_uuid_like(dependency.predecessor_id))
        successor = stage_by_id.get(_normalize_uuid_like(dependency.successor_id))
        if not predecessor or not successor:
            continue

        dependency_type = normalize_dependency_type(getattr(dependency, "dependency_type", "FS"))
        lag_days = int(getattr(dependency, "lag", 0) or 0)
        predecessor_start = _safe_date(getattr(predecessor, "date_start", None))
        predecessor_finish = _stage_finish_date(predecessor)
        successor_start = _safe_date(getattr(successor, "date_start", None))
        successor_finish = _safe_date(getattr(successor, "date_end", None))

        expected_date = None
        actual_date = None
        actual_field = "date_start"
        if dependency_type == "SS":
            expected_date = predecessor_start + timedelta(days=lag_days) if predecessor_start else None
            actual_date = successor_start
        elif dependency_type == "FF":
            expected_date = predecessor_finish + timedelta(days=lag_days) if predecessor_finish else None
            actual_date = successor_finish
            actual_field = "date_end"
        elif dependency_type == "SF":
            expected_date = predecessor_start + timedelta(days=lag_days) if predecessor_start else None
            actual_date = successor_finish
            actual_field = "date_end"
        else:
            expected_date = predecessor_finish + timedelta(days=lag_days) if predecessor_finish else None
            actual_date = successor_start

        if expected_date and actual_date and actual_date < expected_date:
            issues.append(
                _build_issue(
                    issue_type="stage_dependency_conflict",
                    module="stages",
                    severity="error",
                    title="Конфликт по зависимости этапов",
                    description=(
                        f'Этап "{_stage_display_name(successor)}" имеет {actual_field} {_date_to_label(actual_date)}, '
                        f'что раньше допустимой даты {_date_to_label(expected_date)} по связи {dependency_type} '
                        f'с этапом "{_stage_display_name(predecessor)}".'
                    ),
                    scope_type="dependency",
                    scope_id=dependency.id,
                    deal_id=deal_id,
                    payload={
                        "dependency_id": str(dependency.id),
                        "dependency_type": dependency_type,
                        "lag": lag_days,
                        "predecessor_id": str(predecessor.id),
                        "predecessor_name": _stage_display_name(predecessor),
                        "successor_id": str(successor.id),
                        "successor_name": _stage_display_name(successor),
                        "expected_date": expected_date,
                        "actual_date": actual_date,
                        "actual_field": actual_field,
                    },
                )
            )

    for stage in stages:
        if not _is_stage_closed(stage):
            continue

        open_children = [child for child in children_by_parent.get(_normalize_uuid_like(stage.id), []) if not _is_stage_closed(child)]
        open_assignments = [assignment for assignment in assignments_by_stage.get(_normalize_uuid_like(stage.id), []) if not _is_terminal_status(assignment.status)]
        open_subtasks = []
        for assignment in assignments_by_stage.get(_normalize_uuid_like(stage.id), []):
            open_subtasks.extend(
                subtask for subtask in subtasks_by_assignment.get(str(assignment.id), []) if not _is_terminal_status(subtask.status)
            )

        if open_children or open_assignments or open_subtasks:
            description_parts = []
            if open_children:
                description_parts.append(f"незакрытые дочерние этапы: {len(open_children)}")
            if open_assignments:
                description_parts.append(f"незавершенные товары: {len(open_assignments)}")
            if open_subtasks:
                description_parts.append(f"незавершенные подзадачи: {len(open_subtasks)}")
            issues.append(
                _build_issue(
                    issue_type="stage_closed_with_open_tails",
                    module="contracting",
                    severity="warning",
                    title="Закрытый этап имеет открытые хвосты",
                    description=(
                        f'Этап "{_stage_display_name(stage)}" закрыт, но содержит '
                        + ", ".join(description_parts)
                        + "."
                    ),
                    scope_type="stage",
                    scope_id=stage.id,
                    deal_id=deal_id,
                    payload={
                        "stage_id": str(stage.id),
                        "stage_name": _stage_display_name(stage),
                        "open_children": len(open_children),
                        "open_assignments": len(open_assignments),
                        "open_subtasks": len(open_subtasks),
                    },
                )
            )

    missing_executor_seen = set()
    for link in links:
        stage_key = _normalize_uuid_like(link.stage_id)
        deal_product = deal_product_by_id.get(_normalize_uuid_like(link.deal_product_id))
        product_key = _normalize_uuid_like(getattr(deal_product, "product_id", None))
        stage = stage_by_id.get(stage_key)
        if not stage_key or not product_key or not deal_product or not stage or _is_stage_closed(stage):
            continue
        pair_key = (stage_key, product_key)
        if pair_key in assignment_pairs or pair_key in missing_executor_seen:
            continue
        missing_executor_seen.add(pair_key)
        issues.append(
            _build_issue(
                issue_type="stage_product_without_executor",
                module="contracting",
                severity="warning",
                title="Товар этапа без исполнителя",
                description=(
                    f'Товар "{_product_display_name(deal_product)}" привязан к этапу "{_stage_display_name(stage)}", '
                    "но по нему не создано ни одного назначения исполнителя."
                ),
                scope_type="stage_product",
                scope_id=link.id,
                deal_id=deal_id,
                payload={
                    "link_id": str(link.id),
                    "stage_id": str(stage.id),
                    "stage_name": _stage_display_name(stage),
                    "deal_product_id": str(deal_product.id),
                    "product_id": str(deal_product.product_id),
                    "product_name": _product_display_name(deal_product),
                },
            )
        )

    for assignment in assignments:
        stage = stage_by_id.get(_normalize_uuid_like(assignment.stage_id))
        deal_product = deal_product_by_product_id.get(_normalize_uuid_like(assignment.product_id))
        assignment_start = _safe_date(getattr(assignment, "start_date", None))
        assignment_due = _safe_date(getattr(assignment, "due_date", None))
        contract_due = _safe_date(getattr(assignment, "contract_due_date", None))

        if stage and stage.date_start and assignment_start and assignment_start < stage.date_start:
            issues.append(
                _build_issue(
                    issue_type="assignment_start_before_stage",
                    module="contracting",
                    severity="warning",
                    title="Дата начала товара раньше этапа",
                    description=(
                        f'Товар "{_product_display_name(deal_product)}" начинается {_date_to_label(assignment_start)}, '
                        f'раньше старта этапа "{_stage_display_name(stage)}" {_date_to_label(stage.date_start)}.'
                    ),
                    scope_type="assignment",
                    scope_id=assignment.id,
                    deal_id=deal_id,
                    payload={
                        "assignment_id": str(assignment.id),
                        "stage_id": str(stage.id),
                        "stage_name": _stage_display_name(stage),
                        "product_name": _product_display_name(deal_product),
                        "assignment_start": assignment_start,
                        "stage_start": stage.date_start,
                    },
                )
            )

        if stage and stage.date_end and assignment_due and assignment_due > stage.date_end:
            issues.append(
                _build_issue(
                    issue_type="assignment_due_after_stage",
                    module="contracting",
                    severity="warning",
                    title="Рабочий срок товара позже этапа",
                    description=(
                        f'У товара "{_product_display_name(deal_product)}" рабочий срок {_date_to_label(assignment_due)}, '
                        f'что позже окончания этапа "{_stage_display_name(stage)}" {_date_to_label(stage.date_end)}.'
                    ),
                    scope_type="assignment",
                    scope_id=assignment.id,
                    deal_id=deal_id,
                    payload={
                        "assignment_id": str(assignment.id),
                        "stage_id": str(stage.id),
                        "stage_name": _stage_display_name(stage),
                        "product_name": _product_display_name(deal_product),
                        "assignment_due": assignment_due,
                        "stage_end": stage.date_end,
                    },
                )
            )

        if contract_due and assignment_due and contract_due < assignment_due:
            issues.append(
                _build_issue(
                    issue_type="assignment_contract_due_before_work_due",
                    module="contracting",
                    severity="warning",
                    title="Договорной срок раньше рабочего",
                    description=(
                        f'У товара "{_product_display_name(deal_product)}" договорной срок {_date_to_label(contract_due)} '
                        f'раньше рабочего срока {_date_to_label(assignment_due)}.'
                    ),
                    scope_type="assignment",
                    scope_id=assignment.id,
                    deal_id=deal_id,
                    payload={
                        "assignment_id": str(assignment.id),
                        "stage_id": str(assignment.stage_id),
                        "stage_name": _stage_display_name(stage),
                        "product_name": _product_display_name(deal_product),
                        "contract_due": contract_due,
                        "assignment_due": assignment_due,
                    },
                )
            )

        assignment_subtasks = subtasks_by_assignment.get(str(assignment.id), [])
        open_subtasks = [subtask for subtask in assignment_subtasks if not _is_terminal_status(subtask.status)]
        if _is_terminal_status(assignment.status) and open_subtasks:
            issues.append(
                _build_issue(
                    issue_type="closed_assignment_with_open_subtasks",
                    module="contracting",
                    severity="warning",
                    title="Готовый товар имеет открытые подзадачи",
                    description=(
                        f'Товар "{_product_display_name(deal_product)}" отмечен завершенным, '
                        f'но содержит открытые подзадачи: {len(open_subtasks)}.'
                    ),
                    scope_type="assignment",
                    scope_id=assignment.id,
                    deal_id=deal_id,
                    payload={
                        "assignment_id": str(assignment.id),
                        "stage_id": str(assignment.stage_id),
                        "stage_name": _stage_display_name(stage),
                        "product_name": _product_display_name(deal_product),
                        "open_subtasks": len(open_subtasks),
                    },
                )
            )

        for subtask in assignment_subtasks:
            subtask_due = _safe_date(getattr(subtask, "due_date", None))
            if assignment_due and subtask_due and subtask_due > assignment_due:
                issues.append(
                    _build_issue(
                        issue_type="subtask_due_after_assignment_due",
                        module="contracting",
                        severity="warning",
                        title="Срок подзадачи позже срока товара",
                        description=(
                            f'Подзадача "{subtask.title}" имеет срок {_date_to_label(subtask_due)}, '
                            f'что позже рабочего срока товара "{_product_display_name(deal_product)}" {_date_to_label(assignment_due)}.'
                        ),
                        scope_type="subtask",
                        scope_id=subtask.id,
                        deal_id=deal_id,
                        payload={
                            "assignment_id": str(assignment.id),
                            "subtask_id": str(subtask.id),
                            "subtask_title": subtask.title,
                            "stage_id": str(assignment.stage_id),
                            "stage_name": _stage_display_name(stage),
                            "product_name": _product_display_name(deal_product),
                            "subtask_due": subtask_due,
                            "assignment_due": assignment_due,
                        },
                    )
                )

    for contract in contracts:
        missing_fields = []
        if not contract.customer_id:
            missing_fields.append("заказчик")
        if not contract.executor_id:
            missing_fields.append("исполнитель")
        if not missing_fields:
            continue
        issues.append(
            _build_issue(
                issue_type="contract_missing_party",
                module="contracts",
                severity="warning",
                title="В договоре не заполнены стороны",
                description=f'В договоре "{contract.contract_number}" не заполнено: {", ".join(missing_fields)}.',
                scope_type="contract",
                scope_id=contract.id,
                deal_id=deal_id,
                payload={
                    "contract_id": str(contract.id),
                    "contract_number": contract.contract_number,
                    "missing_fields": missing_fields,
                },
            )
        )

    return issues


async def _collect_orphan_issues(db: AsyncSession) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    outgoing_result = await db.execute(select(OutgoingDocument).where(OutgoingDocument.deal_id.is_(None)))
    outgoing_documents = outgoing_result.scalars().all()
    for item in outgoing_documents:
        issues.append(
            _build_issue(
                issue_type="outgoing_without_deal",
                module="outgoing",
                severity="warning",
                title="Исходящее письмо без привязки к сделке",
                description=f'Письмо №{item.outgoing_number} "{item.subject}" не привязано к сделке.',
                scope_type="outgoing",
                scope_id=item.id,
                payload={
                    "outgoing_id": str(item.id),
                    "outgoing_number": item.outgoing_number,
                    "subject": item.subject,
                },
            )
        )

    contract_result = await db.execute(select(Contract).where(Contract.deal_id.is_(None)))
    contracts = contract_result.scalars().all()
    for item in contracts:
        issues.append(
            _build_issue(
                issue_type="contract_without_deal",
                module="contracts",
                severity="warning",
                title="Договор без привязки к сделке",
                description=f'Договор "{item.contract_number}" не привязан к сделке.',
                scope_type="contract",
                scope_id=item.id,
                payload={
                    "contract_id": str(item.id),
                    "contract_number": item.contract_number,
                    "contract_type": item.contract_type,
                },
            )
        )

    return issues


async def _sync_issue_scope(
    db: AsyncSession,
    *,
    current_issues: List[Dict[str, Any]],
    existing_issues: List[DataHealthIssue],
) -> None:
    now = datetime.utcnow()
    existing_by_fingerprint = {issue.fingerprint: issue for issue in existing_issues}
    current_fingerprints = set()

    for payload in current_issues:
        fingerprint = payload["fingerprint"]
        current_fingerprints.add(fingerprint)
        existing = existing_by_fingerprint.get(fingerprint)
        if existing:
            existing.scope_type = payload["scope_type"]
            existing.scope_id = payload["scope_id"]
            existing.issue_type = payload["issue_type"]
            existing.module = payload["module"]
            existing.severity = payload["severity"]
            existing.title = payload["title"]
            existing.description = payload["description"]
            existing.payload_json = payload["payload_json"]
            if existing.status == RESOLVED_STATUS:
                existing.status = OPEN_STATUS
            existing.resolved_at = None
            existing.last_detected_at = now
            continue

        db.add(
            DataHealthIssue(
                fingerprint=fingerprint,
                deal_id=payload["deal_id"],
                scope_type=payload["scope_type"],
                scope_id=payload["scope_id"],
                issue_type=payload["issue_type"],
                module=payload["module"],
                severity=payload["severity"],
                status=payload.get("status", OPEN_STATUS),
                title=payload["title"],
                description=payload["description"],
                payload_json=payload["payload_json"],
                first_detected_at=now,
                last_detected_at=now,
            )
        )

    for issue in existing_issues:
        if issue.fingerprint in current_fingerprints or issue.status == RESOLVED_STATUS:
            continue
        issue.status = RESOLVED_STATUS
        issue.resolved_at = now
        issue.last_detected_at = now

    await db.flush()


async def _release_expired_ignored(db: AsyncSession) -> None:
    now = datetime.utcnow()
    result = await db.execute(
        select(DataHealthIssue).where(
            DataHealthIssue.status == IGNORED_STATUS,
            DataHealthIssue.ignored_until.is_not(None),
            DataHealthIssue.ignored_until <= now,
        )
    )
    issues = result.scalars().all()
    if not issues:
        return
    for issue in issues:
        issue.status = OPEN_STATUS
        issue.last_detected_at = now
    await db.commit()


async def refresh_deal_health_issues(db: AsyncSession, deal_id: str) -> None:
    context = await _load_deal_context(db, deal_id)
    current_issues = _collect_deal_issues(context)
    existing_result = await db.execute(select(DataHealthIssue).where(_matches(DataHealthIssue.deal_id, deal_id)))
    existing_issues = existing_result.scalars().all()
    await _sync_issue_scope(db, current_issues=current_issues, existing_issues=existing_issues)
    await db.commit()


async def refresh_orphan_health_issues(db: AsyncSession) -> None:
    current_issues = await _collect_orphan_issues(db)
    existing_result = await db.execute(
        select(DataHealthIssue).where(
            DataHealthIssue.deal_id.is_(None),
            DataHealthIssue.issue_type.in_(sorted(ORPHAN_ISSUE_TYPES)),
        )
    )
    existing_issues = existing_result.scalars().all()
    await _sync_issue_scope(db, current_issues=current_issues, existing_issues=existing_issues)
    await db.commit()


async def refresh_all_health_issues(db: AsyncSession) -> None:
    deals_result = await db.execute(select(Deal.id))
    deal_ids = [row[0] for row in deals_result.all()]
    for deal_id in deal_ids:
        await refresh_deal_health_issues(db, str(deal_id))
    await refresh_orphan_health_issues(db)


async def safe_refresh_deal_health_issues(db: AsyncSession, deal_id: Optional[Any]) -> None:
    if not deal_id:
        return
    try:
        await refresh_deal_health_issues(db, str(deal_id))
    except Exception as error:
        logger.warning("Data health deal refresh failed for %s: %s", deal_id, error)
        try:
            await db.rollback()
        except Exception:
            pass


async def safe_refresh_orphan_health_issues(db: AsyncSession) -> None:
    try:
        await refresh_orphan_health_issues(db)
    except Exception as error:
        logger.warning("Data health orphan refresh failed: %s", error)
        try:
            await db.rollback()
        except Exception:
            pass


def _build_navigation(issue: DataHealthIssue) -> Dict[str, Any]:
    payload = issue.payload_json or {}
    if issue.issue_type in {"contract_without_deal", "contract_missing_party"}:
        return {"navigation_path": f"/contracts/{payload.get('contract_id')}", "navigation_query": {}}
    if issue.issue_type == "outgoing_without_deal":
        return {"navigation_path": "/outgoing-registry", "navigation_query": {"document_id": payload.get("outgoing_id")}}

    deal_id = issue.deal_id
    if issue.issue_type in {"deal_without_customer", "deal_without_our_company"}:
        return {
            "navigation_path": f"/projects/{deal_id}" if deal_id else None,
            "navigation_query": {"tab": "overview"},
        }
    if issue.issue_type in {"stage_invalid_range", "stage_dependency_conflict", "stage_close_date_outside_range"}:
        return {
            "navigation_path": f"/projects/{deal_id}" if deal_id else None,
            "navigation_query": {"tab": "stages", "focus_stage": payload.get("stage_id") or payload.get("successor_id")},
        }
    if issue.issue_type in {
        "stage_closed_with_open_tails",
        "assignment_start_before_stage",
        "assignment_due_after_stage",
        "assignment_contract_due_before_work_due",
        "closed_assignment_with_open_subtasks",
        "subtask_due_after_assignment_due",
    }:
        return {
            "navigation_path": f"/projects/{deal_id}" if deal_id else None,
            "navigation_query": {
                "tab": "defacto",
                "focus_stage": payload.get("stage_id"),
                "focus_assignment": payload.get("assignment_id"),
            },
        }
    if issue.issue_type == "stage_product_without_executor":
        return {
            "navigation_path": f"/projects/{deal_id}" if deal_id else None,
            "navigation_query": {"tab": "dejure", "focus_stage": payload.get("stage_id")},
        }
    return {"navigation_path": f"/projects/{deal_id}" if deal_id else None, "navigation_query": {"tab": "overview"}}


async def _load_deal_titles(db: AsyncSession, deal_ids: Iterable[str]) -> Dict[str, str]:
    normalized_ids = [value for value in (_normalize_uuid_like(item) for item in deal_ids) if value]
    if not normalized_ids:
        return {}
    result = await db.execute(select(Deal).where(_in_values(Deal.id, normalized_ids)))
    return {_normalize_uuid_like(deal.id): _deal_display_title(deal) for deal in result.scalars().all()}


def _serialize_issue(issue: DataHealthIssue, deal_titles: Dict[str, str]) -> Dict[str, Any]:
    navigation = _build_navigation(issue)
    deal_key = _normalize_uuid_like(issue.deal_id)
    return {
        "id": issue.id,
        "fingerprint": issue.fingerprint,
        "deal_id": issue.deal_id,
        "deal_title": deal_titles.get(deal_key),
        "scope_type": issue.scope_type,
        "scope_id": issue.scope_id,
        "issue_type": issue.issue_type,
        "module": issue.module,
        "severity": issue.severity,
        "status": issue.status,
        "title": issue.title,
        "description": issue.description or "",
        "payload": issue.payload_json or {},
        "navigation_path": navigation["navigation_path"],
        "navigation_query": navigation["navigation_query"],
        "first_detected_at": issue.first_detected_at,
        "last_detected_at": issue.last_detected_at,
        "resolved_at": issue.resolved_at,
        "ignored_reason": issue.ignored_reason,
        "ignored_until": issue.ignored_until,
        "ignored_by_user_id": issue.ignored_by_user_id,
        "ignored_at": issue.ignored_at,
    }


def _build_summary(items: List[Dict[str, Any]]) -> Dict[str, int]:
    summary = {
        "total": len(items),
        "open": 0,
        "ignored": 0,
        "resolved": 0,
        "errors": 0,
        "warnings": 0,
        "infos": 0,
    }
    for item in items:
        status = str(item.get("status") or "").lower()
        severity = str(item.get("severity") or "").lower()
        if status in summary:
            summary[status] += 1
        if severity == "error":
            summary["errors"] += 1
        elif severity == "warning":
            summary["warnings"] += 1
        else:
            summary["infos"] += 1
    return summary


def _severity_rank(value: Any) -> int:
    normalized = str(value or "").lower()
    if normalized == "error":
        return 0
    if normalized == "warning":
        return 1
    return 2


def _issue_group_scope(item: Dict[str, Any]) -> str:
    payload = item.get("payload") or {}
    for key in ("stage_id", "successor_id", "contract_id", "outgoing_id", "deal_product_id", "assignment_id"):
        value = payload.get(key)
        if value:
            return f"{key}:{value}"
    return f"{item.get('scope_type') or ''}:{item.get('scope_id') or ''}"


def _group_serialized_issues(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for item in items:
        key = "|".join(
            [
                str(item.get("issue_type") or ""),
                str(item.get("deal_id") or ""),
                _issue_group_scope(item),
            ]
        )
        group = groups.get(key)
        if not group:
            group = {
                "id": item.get("id"),
                "group_key": _payload_fingerprint({"group": key}),
                "count": 0,
                "deal_id": item.get("deal_id"),
                "deal_title": item.get("deal_title"),
                "issue_type": item.get("issue_type"),
                "module": item.get("module"),
                "severity": item.get("severity"),
                "status": item.get("status"),
                "title": item.get("title"),
                "description": item.get("description") or "",
                "payload": item.get("payload") or {},
                "navigation_path": item.get("navigation_path"),
                "navigation_query": item.get("navigation_query") or {},
                "first_detected_at": item.get("first_detected_at"),
                "last_detected_at": item.get("last_detected_at"),
                "items": [],
            }
            groups[key] = group
        group["count"] += 1
        group["items"].append(item)
        if _severity_rank(item.get("severity")) < _severity_rank(group.get("severity")):
            group["severity"] = item.get("severity")
        if item.get("last_detected_at") and (
            not group.get("last_detected_at") or item.get("last_detected_at") > group.get("last_detected_at")
        ):
            group["last_detected_at"] = item.get("last_detected_at")
        if item.get("first_detected_at") and (
            not group.get("first_detected_at") or item.get("first_detected_at") < group.get("first_detected_at")
        ):
            group["first_detected_at"] = item.get("first_detected_at")

    return sorted(
        groups.values(),
        key=lambda group: (
            _severity_rank(group.get("severity")),
            str(group.get("module") or ""),
            -(group.get("last_detected_at").timestamp() if group.get("last_detected_at") else 0),
        ),
    )


async def get_health_issues(
    db: AsyncSession,
    *,
    deal_id: Optional[str] = None,
    allowed_deal_ids: Optional[Iterable[str]] = None,
    severity: Optional[str] = None,
    issue_type: Optional[str] = None,
    module: Optional[str] = None,
    status: str = "active",
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    await _release_expired_ignored(db)
    query = select(DataHealthIssue)
    if deal_id:
        query = query.where(_matches(DataHealthIssue.deal_id, deal_id))
    if allowed_deal_ids is not None:
        query = query.where(DataHealthIssue.deal_id.is_not(None), _in_values(DataHealthIssue.deal_id, allowed_deal_ids))
    if severity:
        query = query.where(func.lower(DataHealthIssue.severity) == str(severity).lower())
    if issue_type:
        query = query.where(DataHealthIssue.issue_type == issue_type)
    if module:
        query = query.where(DataHealthIssue.module == module)

    normalized_status = str(status or "active").lower()
    if normalized_status == "active":
        query = query.where(DataHealthIssue.status.in_(sorted(ACTIVE_STATUSES)))
    elif normalized_status in {OPEN_STATUS, IGNORED_STATUS, RESOLVED_STATUS}:
        query = query.where(DataHealthIssue.status == normalized_status)

    query = query.order_by(
        case((DataHealthIssue.severity == "error", 0), (DataHealthIssue.severity == "warning", 1), else_=2),
        case(
            (DataHealthIssue.module == "stages", 0),
            (DataHealthIssue.module == "contracting", 1),
            (DataHealthIssue.module == "contracts", 2),
            (DataHealthIssue.module == "outgoing", 3),
            else_=4,
        ),
        DataHealthIssue.last_detected_at.desc(),
    )
    result = await db.execute(query)
    issues = result.scalars().all()

    deal_titles = await _load_deal_titles(db, [issue.deal_id for issue in issues if issue.deal_id])
    serialized = [_serialize_issue(issue, deal_titles) for issue in issues]

    if search:
        needle = search.strip().lower()
        serialized = [
            item
            for item in serialized
            if needle in " ".join(
                [
                    item.get("title") or "",
                    item.get("description") or "",
                    item.get("deal_title") or "",
                    item.get("module") or "",
                ]
            ).lower()
        ]

    summary = _build_summary(serialized)
    paginated = serialized[offset : offset + limit]
    return {"items": paginated, "total": len(serialized), "summary": summary}


async def get_grouped_health_issues(
    db: AsyncSession,
    *,
    deal_id: Optional[str] = None,
    allowed_deal_ids: Optional[Iterable[str]] = None,
    severity: Optional[str] = None,
    issue_type: Optional[str] = None,
    module: Optional[str] = None,
    status: str = "active",
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    data = await get_health_issues(
        db,
        deal_id=deal_id,
        allowed_deal_ids=allowed_deal_ids,
        severity=severity,
        issue_type=issue_type,
        module=module,
        status=status,
        search=search,
        offset=0,
        limit=10000,
    )
    groups = _group_serialized_issues(data.get("items") or [])
    return {
        "items": groups[offset : offset + limit],
        "total": len(groups),
        "summary": data.get("summary") or _build_summary([]),
    }


async def get_deal_health_counts(
    db: AsyncSession,
    *,
    deal_ids: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    await _release_expired_ignored(db)
    query = select(
        DataHealthIssue.deal_id,
        DataHealthIssue.severity,
        DataHealthIssue.status,
        func.count(DataHealthIssue.id),
    ).where(
        DataHealthIssue.deal_id.is_not(None),
        DataHealthIssue.status.in_(sorted(ACTIVE_STATUSES)),
    )
    if deal_ids is not None:
        query = query.where(_in_values(DataHealthIssue.deal_id, deal_ids))
    query = query.group_by(DataHealthIssue.deal_id, DataHealthIssue.severity, DataHealthIssue.status)
    result = await db.execute(query)

    counts: Dict[str, Dict[str, Any]] = {}
    for deal_id, severity, status, amount in result.all():
        key = str(deal_id)
        item = counts.setdefault(key, {"deal_id": key, "total": 0, "errors": 0, "warnings": 0, "ignored": 0})
        value = int(amount or 0)
        item["total"] += value
        if str(status) == IGNORED_STATUS:
            item["ignored"] += value
        if str(severity) == "error":
            item["errors"] += value
        elif str(severity) == "warning":
            item["warnings"] += value
    return list(counts.values())


async def set_health_issue_status(
    db: AsyncSession,
    issue_id: str,
    status: str,
    *,
    ignored_reason: Optional[str] = None,
    ignored_until: Optional[datetime] = None,
    ignored_by_user_id: Optional[str] = None,
) -> Optional[DataHealthIssue]:
    result = await db.execute(select(DataHealthIssue).where(DataHealthIssue.id == str(issue_id)))
    issue = result.scalar_one_or_none()
    if not issue:
        return None

    normalized_status = str(status or "").lower()
    if normalized_status not in {OPEN_STATUS, IGNORED_STATUS, RESOLVED_STATUS}:
        return None

    issue.status = normalized_status
    issue.resolved_at = datetime.utcnow() if normalized_status == RESOLVED_STATUS else None
    if normalized_status == IGNORED_STATUS:
        issue.ignored_reason = (ignored_reason or "").strip() or None
        issue.ignored_until = ignored_until
        issue.ignored_by_user_id = str(ignored_by_user_id) if ignored_by_user_id else None
        issue.ignored_at = datetime.utcnow()
    elif normalized_status == OPEN_STATUS:
        issue.ignored_reason = None
        issue.ignored_until = None
        issue.ignored_by_user_id = None
        issue.ignored_at = None
    issue.last_detected_at = datetime.utcnow()
    await db.commit()
    await db.refresh(issue)
    return issue
