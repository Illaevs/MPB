"""
Helpers for structured outgoing document drafts.
"""
from __future__ import annotations

import copy
import json
import uuid
from typing import Any, Dict, List, Optional


EDITOR_SCHEMA_VERSION = 1
EDITOR_MODES = {"classic", "structured"}

BLOCK_CATALOG: List[Dict[str, Any]] = [
    {
        "type": "document_meta",
        "label": "Шапка документа",
        "description": "Номер, дата и служебные параметры документа.",
        "document_kinds": ["letter", "invoice", "upd", "act", "vat_invoice"],
        "default_attrs": {
            "number_mode": "auto",
            "payment_due_date_mode": "workdays_plus",
            "payment_due_days": 5,
        },
    },
    {
        "type": "party_details",
        "label": "Блок стороны",
        "description": "Реквизиты нашей компании или получателя.",
        "document_kinds": ["letter", "invoice", "upd", "act", "vat_invoice"],
        "default_attrs": {
            "role": "recipient",
            "show_bank_details": False,
        },
    },
    {
        "type": "intro_paragraph",
        "label": "Вводный абзац",
        "description": "Стартовый абзац документа с ручным или шаблонным текстом.",
        "document_kinds": ["letter"],
        "default_attrs": {
            "mode": "contract_intro",
            "text": "",
        },
    },
    {
        "type": "basis_block",
        "label": "Основание",
        "description": "Основание документа по договору или пользовательскому шаблону.",
        "document_kinds": ["invoice", "upd", "act", "vat_invoice"],
        "default_attrs": {
            "mode": "contract_auto",
            "text_pattern": "Основание: договор № {{ contract.number }} от {{ contract.date }}",
        },
    },
    {
        "type": "rich_text_block",
        "label": "Текстовый блок",
        "description": "Свободный текст документа.",
        "document_kinds": ["letter", "invoice", "upd", "act", "vat_invoice"],
        "default_attrs": {
            "html": "",
        },
    },
    {
        "type": "invoice_items_table",
        "label": "Таблица счета",
        "description": "Строки счета по платежам или ручным позициям.",
        "document_kinds": ["invoice"],
        "default_attrs": {
            "rows": [],
            "show_vat_rate": True,
        },
    },
    {
        "type": "stage_lines_block",
        "label": "Строки по этапам",
        "description": "Табличная часть документа по этапам сделки.",
        "document_kinds": ["upd", "act", "vat_invoice"],
        "default_attrs": {
            "selected_stage_ids": [],
            "rows": [],
        },
    },
    {
        "type": "payment_allocation_block",
        "label": "Зачеты платежей",
        "description": "Частичные зачеты платежей и аванса.",
        "document_kinds": ["act"],
        "default_attrs": {
            "linked_payment_items": [],
            "show_remaining_after_offset": True,
        },
    },
    {
        "type": "totals_block",
        "label": "Итоги",
        "description": "Итоги документа, НДС, сумма прописью.",
        "document_kinds": ["invoice", "upd", "act", "vat_invoice"],
        "default_attrs": {
            "show_vat_amount": True,
            "show_total_words": True,
            "show_vat_rate": True,
        },
    },
    {
        "type": "signature_stamp",
        "label": "Подписи и печать",
        "description": "Финальный блок подписей, печати и должностей.",
        "document_kinds": ["letter", "invoice", "upd", "act", "vat_invoice"],
        "default_attrs": {
            "show_director": True,
            "show_accountant": False,
            "show_stamp": True,
        },
    },
]

BLOCK_TYPES = {item["type"] for item in BLOCK_CATALOG}
BLOCK_BY_TYPE = {item["type"]: item for item in BLOCK_CATALOG}


def _block(block_type: str, **attrs: Any) -> Dict[str, Any]:
    default_attrs = copy.deepcopy(BLOCK_BY_TYPE[block_type]["default_attrs"])
    default_attrs.update(attrs)
    return {
        "id": str(uuid.uuid4()),
        "type": block_type,
        "attrs": default_attrs,
    }


def default_editor_draft(document_kind: str) -> Dict[str, Any]:
    kind = str(document_kind or "letter")
    if kind == "letter":
        content = [
            _block("document_meta"),
            _block("party_details", role="recipient", show_bank_details=False),
            _block("intro_paragraph"),
            _block("rich_text_block"),
            _block("signature_stamp", show_accountant=False),
        ]
    elif kind == "invoice":
        content = [
            _block("document_meta", payment_due_date_mode="workdays_plus", payment_due_days=5),
            _block("party_details", role="our_company", show_bank_details=True),
            _block("party_details", role="recipient", show_bank_details=False),
            _block("basis_block"),
            _block("invoice_items_table"),
            _block("totals_block"),
            _block("signature_stamp", show_accountant=True),
        ]
    elif kind == "act":
        content = [
            _block("document_meta"),
            _block("party_details", role="our_company", show_bank_details=False),
            _block("party_details", role="recipient", show_bank_details=False),
            _block("basis_block"),
            _block("stage_lines_block"),
            _block("payment_allocation_block"),
            _block("totals_block"),
            _block("signature_stamp", show_accountant=False),
        ]
    elif kind in {"upd", "vat_invoice"}:
        content = [
            _block("document_meta"),
            _block("party_details", role="our_company", show_bank_details=True),
            _block("party_details", role="recipient", show_bank_details=False),
            _block("basis_block"),
            _block("stage_lines_block"),
            _block("totals_block"),
            _block("signature_stamp", show_accountant=True),
        ]
    else:
        content = [_block("document_meta"), _block("rich_text_block")]
    return {
        "schema_version": EDITOR_SCHEMA_VERSION,
        "document_kind": kind,
        "content": content,
    }


def normalize_editor_mode(value: Optional[str]) -> str:
    normalized = str(value or "classic").strip().lower()
    return normalized if normalized in EDITOR_MODES else "classic"


def normalize_editor_draft(value: Any, document_kind: str) -> Dict[str, Any]:
    base = default_editor_draft(document_kind)
    if value in (None, "", {}):
        return base
    payload = value
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            return base
    if not isinstance(payload, dict):
        return base

    content = payload.get("content")
    normalized_content = []
    if isinstance(content, list):
        for raw_block in content:
            if not isinstance(raw_block, dict):
                continue
            block_type = str(raw_block.get("type") or "").strip()
            if block_type not in BLOCK_TYPES:
                continue
            attrs = raw_block.get("attrs")
            if not isinstance(attrs, dict):
                attrs = {}
            merged_attrs = copy.deepcopy(BLOCK_BY_TYPE[block_type]["default_attrs"])
            merged_attrs.update(attrs)
            normalized_content.append(
                {
                    "id": str(raw_block.get("id") or uuid.uuid4()),
                    "type": block_type,
                    "attrs": merged_attrs,
                }
            )
    if not normalized_content:
        normalized_content = base["content"]
    return {
        "schema_version": int(payload.get("schema_version") or EDITOR_SCHEMA_VERSION),
        "document_kind": str(payload.get("document_kind") or document_kind or "letter"),
        "content": normalized_content,
    }


def validate_editor_draft(draft: Any, document_kind: str) -> Dict[str, List[str]]:
    normalized = normalize_editor_draft(draft, document_kind)
    errors: List[str] = []
    warnings: List[str] = []
    content = normalized.get("content") or []
    if not content:
        errors.append("Конструктор документа не содержит блоков.")
    block_types = [str(item.get("type") or "") for item in content if isinstance(item, dict)]
    if "document_meta" not in block_types:
        warnings.append("В структуре отсутствует блок шапки документа.")
    if document_kind != "letter" and "signature_stamp" not in block_types:
        warnings.append("В структуре отсутствует блок подписей.")
    if document_kind == "invoice" and "invoice_items_table" not in block_types:
        warnings.append("Для счета обычно требуется табличная часть.")
    if document_kind in {"act", "upd", "vat_invoice"} and "stage_lines_block" not in block_types:
        warnings.append("Для выбранного типа документа нет блока строк по этапам.")
    if document_kind == "act" and "payment_allocation_block" not in block_types:
        warnings.append("Для акта не добавлен блок зачетов платежей.")
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "")
        attrs = block.get("attrs") if isinstance(block.get("attrs"), dict) else {}
        if block_type == "party_details":
            role = str(attrs.get("role") or "")
            if role not in {"our_company", "recipient"}:
                warnings.append("В блоке стороны не выбран корректный источник данных.")
        if block_type == "basis_block" and not str(attrs.get("text_pattern") or "").strip():
            warnings.append("В блоке основания пустой текст шаблона.")
    return {
        "errors": errors,
        "warnings": warnings,
    }


def get_editor_block_catalog(document_kind: Optional[str] = None) -> List[Dict[str, Any]]:
    kind = str(document_kind or "").strip()
    items = []
    for block in BLOCK_CATALOG:
        if kind and kind not in block["document_kinds"]:
            continue
        items.append(copy.deepcopy(block))
    return items


def get_editor_blocks(draft: Any, document_kind: str, block_type: Optional[str] = None) -> List[Dict[str, Any]]:
    normalized = normalize_editor_draft(draft, document_kind)
    blocks = [item for item in (normalized.get("content") or []) if isinstance(item, dict)]
    if not block_type:
        return blocks
    expected = str(block_type or "").strip()
    return [item for item in blocks if str(item.get("type") or "").strip() == expected]


def get_first_editor_block(draft: Any, document_kind: str, block_type: str) -> Optional[Dict[str, Any]]:
    blocks = get_editor_blocks(draft, document_kind, block_type)
    return blocks[0] if blocks else None
