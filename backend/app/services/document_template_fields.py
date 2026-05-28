"""
System registry and parser for document template placeholders.
"""
from __future__ import annotations

import re
import zipfile
from io import BytesIO
from typing import Dict, Iterable, List, Optional
from xml.etree import ElementTree

try:  # L3: prefer defusedxml to block entity-expansion (billion laughs) DoS
    from defusedxml.ElementTree import fromstring as _xml_fromstring
except Exception:  # pragma: no cover - fallback if defusedxml is absent
    _xml_fromstring = ElementTree.fromstring


ALL_OUTGOING_KINDS = ["letter", "invoice", "upd", "act", "vat_invoice"]
ALL_MODULES = ["outgoing_registry", "contracts", "document_registry"]


FIELD_REGISTRY: List[Dict] = [
    {
        "key": "document.number",
        "label": "Номер документа",
        "group": "Документ",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "190326/00001",
        "description": "Номер текущего документа.",
        "requires": [],
    },
    {
        "key": "document.date",
        "label": "Дата документа",
        "group": "Документ",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "date",
        "example": "19.03.2026",
        "description": "Дата текущего документа в печатном формате.",
        "requires": [],
    },
    {
        "key": "document.subject",
        "label": "Тема / основание",
        "group": "Документ",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS,
        "type": "string",
        "example": "Передача проектной документации",
        "description": "Краткое основание или тема документа.",
        "requires": [],
    },
    {
        "key": "deal.title",
        "label": "Имя проекта / сделки",
        "group": "Сделка",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "Новоленская ТЭС. Пожарное депо",
        "description": "Название сделки.",
        "requires": ["deal"],
    },
    {
        "key": "deal.obj_name",
        "label": "Наименование объекта",
        "group": "Сделка",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "Пожарное депо",
        "description": "Поле сделки: наименование объекта.",
        "requires": ["deal"],
    },
    {
        "key": "deal.address",
        "label": "Адрес объекта",
        "group": "Сделка",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "Республика Саха (Якутия), г. Якутск",
        "description": "Адрес строительства из сделки.",
        "requires": ["deal"],
    },
    {
        "key": "contract.number",
        "label": "Номер договора",
        "group": "Договор",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "37",
        "description": "Номер выбранного договора.",
        "requires": ["contract"],
    },
    {
        "key": "contract.date",
        "label": "Дата договора",
        "group": "Договор",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "date",
        "example": "14.11.2023",
        "description": "Дата выбранного договора.",
        "requires": ["contract"],
    },
    {
        "key": "contract.amount",
        "label": "Цена договора",
        "group": "Договор",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "money",
        "example": "1 500 000,00",
        "description": "Сумма выбранного договора.",
        "requires": ["contract"],
    },
    {
        "key": "recipient.name",
        "label": "Получатель полное наименование",
        "group": "Получатель",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "ООО «Инжпроект»",
        "description": "Полное наименование контрагента-получателя.",
        "requires": ["recipient"],
    },
    {
        "key": "recipient.short_name",
        "label": "Получатель кратко",
        "group": "Получатель",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS,
        "type": "string",
        "example": "ООО «Инжпроект»",
        "description": "Краткое наименование получателя.",
        "requires": ["recipient"],
    },
    {
        "key": "recipient.to_name",
        "label": "Кому",
        "group": "Получатель",
        "modules": ["outgoing_registry"],
        "document_kinds": ["letter"],
        "type": "string",
        "example": "Иванову И.И.",
        "description": "Адресат в дательном падеже для письма.",
        "requires": ["recipient"],
    },
    {
        "key": "recipient.genitive_name",
        "label": "Кем",
        "group": "Получатель",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice"],
        "type": "string",
        "example": "Заказчика",
        "description": "Получатель в нужном падеже для закрывающих документов.",
        "requires": ["recipient"],
    },
    {
        "key": "recipient.eio",
        "label": "ЕИО получателя",
        "group": "Получатель",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS,
        "type": "string",
        "example": "Генеральному директору",
        "description": "Должность/ЕИО получателя.",
        "requires": ["recipient"],
    },
    {
        "key": "recipient.bank.name",
        "label": "Банк получателя",
        "group": "Банковские реквизиты",
        "modules": ["outgoing_registry", "contracts"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice", "contract"],
        "type": "string",
        "example": "ПАО Сбербанк",
        "description": "Название выбранного банка получателя.",
        "requires": ["recipient", "bank_account"],
    },
    {
        "key": "recipient.bank.rs",
        "label": "Расчетный счет получателя",
        "group": "Банковские реквизиты",
        "modules": ["outgoing_registry", "contracts"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice", "contract"],
        "type": "string",
        "example": "40702810...",
        "description": "Расчетный счет выбранных банковских реквизитов получателя.",
        "requires": ["recipient", "bank_account"],
    },
    {
        "key": "recipient.bank.bik",
        "label": "БИК получателя",
        "group": "Банковские реквизиты",
        "modules": ["outgoing_registry", "contracts"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice", "contract"],
        "type": "string",
        "example": "044525225",
        "description": "БИК выбранных банковских реквизитов получателя.",
        "requires": ["recipient", "bank_account"],
    },
    {
        "key": "our_company.name",
        "label": "Наша компания",
        "group": "Наша компания",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "ООО «НОРМБУД»",
        "description": "Наименование нашей компании.",
        "requires": ["our_company"],
    },
    {
        "key": "our_company.inn",
        "label": "ИНН нашей компании",
        "group": "Наша компания",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "7700000000",
        "description": "ИНН нашей компании.",
        "requires": ["our_company"],
    },
    {
        "key": "stages",
        "label": "Список этапов",
        "group": "Табличные блоки",
        "modules": ["outgoing_registry"],
        "document_kinds": ["act", "upd", "vat_invoice"],
        "type": "block",
        "example": "{{# stages }}...{{/ stages }}",
        "description": "Блок для вывода выбранных этапов.",
        "requires": ["deal", "stages"],
    },
    {
        "key": "stage.name",
        "label": "Этап: наименование",
        "group": "Этапы",
        "modules": ["outgoing_registry"],
        "document_kinds": ["act", "upd", "vat_invoice"],
        "type": "string",
        "example": "Разработка проектной документации",
        "description": "Название этапа внутри блока stages.",
        "requires": ["stages"],
    },
    {
        "key": "stage.amount",
        "label": "Этап: сумма",
        "group": "Этапы",
        "modules": ["outgoing_registry"],
        "document_kinds": ["act", "upd", "vat_invoice"],
        "type": "money",
        "example": "128 000,00",
        "description": "Плановая стоимость этапа внутри блока stages.",
        "requires": ["stages"],
    },
    {
        "key": "linked_payment_items",
        "label": "Зачеты аванса",
        "group": "Табличные блоки",
        "modules": ["outgoing_registry"],
        "document_kinds": ["act"],
        "type": "block",
        "example": "{{# linked_payment_items }}...{{/ linked_payment_items }}",
        "description": "Блок частичных зачетов платежей в акте.",
        "requires": ["payments"],
    },
    {
        "key": "payment.amount",
        "label": "Платеж: сумма зачета",
        "group": "Платежи",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice", "act"],
        "type": "money",
        "example": "50 000,00",
        "description": "Сумма выбранного платежа или частичного зачета.",
        "requires": ["payments"],
    },
    {
        "key": "payment.date",
        "label": "Платеж: дата",
        "group": "Платежи",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice", "act"],
        "type": "date",
        "example": "28.02.2026",
        "description": "Дата выбранного платежа.",
        "requires": ["payments"],
    },
]

FIELD_REGISTRY.extend([
    {
        "key": "document.basis",
        "label": "Основание документа",
        "group": "Документ",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice"],
        "type": "string",
        "example": "Договор №37 от 14.11.2023",
        "description": "Основание по выбранному договору: номер и дата договора.",
        "requires": ["contract"],
    },
    {
        "key": "document.total_amount",
        "label": "Общая сумма документа",
        "group": "Документ",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice"],
        "type": "money",
        "example": "120 000,00",
        "description": "Итоговая сумма документа с учетом НДС.",
        "requires": [],
    },
    {
        "key": "document.vat_amount",
        "label": "Сумма НДС",
        "group": "Документ",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice"],
        "type": "money",
        "example": "20 000,00",
        "description": "Расчетная сумма НДС по ставке сделки.",
        "requires": [],
    },
    {
        "key": "document.vat_rate",
        "label": "Ставка НДС",
        "group": "Документ",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice"],
        "type": "number",
        "example": "20",
        "description": "Ставка НДС числом, без знака процента.",
        "requires": [],
    },
    {
        "key": "document.total_amount_words",
        "label": "Итоговая сумма прописью",
        "group": "Документ",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice"],
        "type": "string",
        "example": "Сто двадцать тысяч рублей 00 копеек",
        "description": "Итоговая сумма документа прописью в формате рублей и копеек.",
        "requires": [],
    },
    {
        "key": "document.payment_due_date",
        "label": "Оплатить не позднее",
        "group": "Документ",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice"],
        "type": "date",
        "example": "26.03.2026",
        "description": "Дата документа плюс 5 рабочих дней.",
        "requires": [],
    },
    {
        "key": "invoice.number",
        "label": "Счет: номер",
        "group": "Счет",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice"],
        "type": "string",
        "example": "190326/00001",
        "description": "Номер счета. Дублирует document.number для удобства шаблонов счета.",
        "requires": [],
    },
    {
        "key": "invoice.date",
        "label": "Счет: дата",
        "group": "Счет",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice"],
        "type": "date",
        "example": "19.03.2026",
        "description": "Дата счета. Дублирует document.date для удобства шаблонов счета.",
        "requires": [],
    },
    {
        "key": "invoice.basis",
        "label": "Счет: основание",
        "group": "Счет",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice"],
        "type": "string",
        "example": "Договор №37 от 14.11.2023",
        "description": "Основание счета по выбранному договору.",
        "requires": ["contract"],
    },
    {
        "key": "invoice.total_amount",
        "label": "Счет: общая сумма",
        "group": "Счет",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice"],
        "type": "money",
        "example": "120 000,00",
        "description": "Общая сумма счета.",
        "requires": [],
    },
    {
        "key": "invoice.vat_amount",
        "label": "Счет: сумма НДС",
        "group": "Счет",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice"],
        "type": "money",
        "example": "20 000,00",
        "description": "Сумма НДС в счете.",
        "requires": [],
    },
    {
        "key": "invoice.vat_rate",
        "label": "Счет: ставка НДС",
        "group": "Счет",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice"],
        "type": "number",
        "example": "20",
        "description": "Ставка НДС в счете числом, без знака процента.",
        "requires": [],
    },
    {
        "key": "invoice.total_amount_words",
        "label": "Счет: сумма прописью",
        "group": "Счет",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice"],
        "type": "string",
        "example": "Сто двадцать тысяч рублей 00 копеек",
        "description": "Итоговая сумма счета прописью.",
        "requires": [],
    },
    {
        "key": "invoice.payment_due_date",
        "label": "Счет: оплатить не позднее",
        "group": "Счет",
        "modules": ["outgoing_registry"],
        "document_kinds": ["invoice"],
        "type": "date",
        "example": "26.03.2026",
        "description": "Дата счета плюс 5 рабочих дней.",
        "requires": [],
    },
    {
        "key": "recipient.inn",
        "label": "ИНН адресата",
        "group": "Получатель",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "7700000000",
        "description": "ИНН контрагента-получателя.",
        "requires": ["recipient"],
    },
    {
        "key": "recipient.kpp",
        "label": "КПП адресата",
        "group": "Получатель",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "770001001",
        "description": "КПП контрагента-получателя, если поле есть в карточке контрагента.",
        "requires": ["recipient"],
    },
    {
        "key": "recipient.address",
        "label": "Адрес адресата",
        "group": "Получатель",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "г. Москва, ул. Примерная, д. 1",
        "description": "Адрес контрагента-получателя.",
        "requires": ["recipient"],
    },
    {
        "key": "recipient.bank.ks",
        "label": "Корреспондентский счет получателя",
        "group": "Банковские реквизиты",
        "modules": ["outgoing_registry", "contracts"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice", "contract"],
        "type": "string",
        "example": "30101810...",
        "description": "Корреспондентский счет выбранных банковских реквизитов получателя.",
        "requires": ["recipient", "bank_account"],
    },
    {
        "key": "our_company.short_name",
        "label": "Наша компания кратко",
        "group": "Наша компания",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "ООО «НОРМБУД»",
        "description": "Краткое наименование нашей компании.",
        "requires": ["our_company"],
    },
    {
        "key": "our_company.full_name",
        "label": "Наша компания полное наименование",
        "group": "Наша компания",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "Общество с ограниченной ответственностью «НОРМБУД»",
        "description": "Полное наименование нашей компании.",
        "requires": ["our_company"],
    },
    {
        "key": "our_company.kpp",
        "label": "КПП нашей компании",
        "group": "Наша компания",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "771701001",
        "description": "КПП нашей компании.",
        "requires": ["our_company"],
    },
    {
        "key": "our_company.address",
        "label": "Адрес нашей компании",
        "group": "Наша компания",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "129226, г. Москва, ул. Сельскохозяйственная, д. 4 стр. 16",
        "description": "Адрес нашей компании.",
        "requires": ["our_company"],
    },
    {
        "key": "our_company.director_name",
        "label": "ГД нашей компании",
        "group": "Наша компания",
        "modules": ALL_MODULES,
        "document_kinds": ALL_OUTGOING_KINDS + ["contract", "additional_agreement", "contract_act"],
        "type": "string",
        "example": "Воронин С. В.",
        "description": "Генеральный директор нашей компании в формате Фамилия И. О.",
        "requires": ["our_company"],
    },
    {
        "key": "our_company.bank.name",
        "label": "Банк нашей компании",
        "group": "Банковские реквизиты",
        "modules": ["outgoing_registry", "contracts"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice", "contract"],
        "type": "string",
        "example": "ПАО Сбербанк",
        "description": "Название банка нашей компании.",
        "requires": ["our_company", "bank_account"],
    },
    {
        "key": "our_company.bank.bik",
        "label": "БИК нашей компании",
        "group": "Банковские реквизиты",
        "modules": ["outgoing_registry", "contracts"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice", "contract"],
        "type": "string",
        "example": "044525225",
        "description": "БИК банка нашей компании.",
        "requires": ["our_company", "bank_account"],
    },
    {
        "key": "our_company.bank.rs",
        "label": "Расчетный счет нашей компании",
        "group": "Банковские реквизиты",
        "modules": ["outgoing_registry", "contracts"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice", "contract"],
        "type": "string",
        "example": "40702810...",
        "description": "Расчетный счет нашей компании.",
        "requires": ["our_company", "bank_account"],
    },
    {
        "key": "our_company.bank.ks",
        "label": "Корреспондентский счет нашей компании",
        "group": "Банковские реквизиты",
        "modules": ["outgoing_registry", "contracts"],
        "document_kinds": ["invoice", "upd", "act", "vat_invoice", "contract"],
        "type": "string",
        "example": "30101810...",
        "description": "Корреспондентский счет банка нашей компании.",
        "requires": ["our_company", "bank_account"],
    },
])

LEGACY_OUTGOING_FIELDS = [
    ("outgoing_number", "Исходящий номер", "Номер письма в текущем рендере."),
    ("letter_date", "Дата письма", "Дата письма в печатном формате."),
    ("subject", "Тема письма", "Тема или основание письма."),
    ("body", "Текст письма", "Текст письма без HTML-разметки."),
    ("body_lines", "Строки текста письма", "Повторяемый блок строк текста письма."),
    ("text", "Текст строки", "Текстовая строка внутри блоков body_lines или attachments_lines."),
    ("attachments_list", "Список приложений", "Список приложений без HTML-разметки."),
    ("attachments_lines", "Строки приложений", "Повторяемый блок строк приложений."),
    ("recipient_company_name", "Получатель", "Полное наименование получателя."),
    ("recipient_short_name", "Получатель кратко", "Краткое наименование получателя."),
    ("recipient_to_name", "Кому", "Получатель в дательном падеже."),
    ("recipient_appeal", "Обращение", "Имя/обращение для приветствия."),
    ("recipient_eio", "ЕИО получателя", "Должность адресата."),
    ("recipient_salutation", "Форма обращения", "Уважаемый/Уважаемая и аналогичные формы."),
    ("recipient_salutation_full", "Полное обращение", "Форма обращения вместе с именем."),
    ("signer_title", "Подписант: должность", "Должность подписанта нашей компании."),
    ("signer_name", "Подписант: имя", "Имя подписанта нашей компании."),
]

FIELD_REGISTRY.extend(
    {
        "key": key,
        "label": label,
        "group": "Письмо: текущий рендер",
        "modules": ["outgoing_registry"],
        "document_kinds": ["letter"],
        "type": "block" if key in {"body_lines", "attachments_lines"} else "string",
        "example": f"{{{key}}}",
        "description": description,
        "requires": [],
    }
    for key, label, description in LEGACY_OUTGOING_FIELDS
)


FIELD_BY_KEY = {item["key"]: item for item in FIELD_REGISTRY}


DOUBLE_PLACEHOLDER_RE = re.compile(r"{{\s*([#/^]?)\s*([a-zA-Z0-9_.-]+)\s*}}")
SINGLE_PLACEHOLDER_RE = re.compile(r"(?<!{){\s*([#/^]?)\s*([a-zA-Z0-9_.-]+)\s*}(?!})")


def get_template_fields(
    *,
    search: Optional[str] = None,
    module: Optional[str] = None,
    document_kind: Optional[str] = None,
    group: Optional[str] = None,
) -> List[Dict]:
    needle = (search or "").strip().lower()
    result = []
    for item in FIELD_REGISTRY:
        if module and module not in item.get("modules", []):
            continue
        if document_kind and document_kind not in item.get("document_kinds", []):
            continue
        if group and item.get("group") != group:
            continue
        haystack = " ".join(
            str(item.get(key, ""))
            for key in ("key", "label", "group", "description", "example", "type")
        ).lower()
        if needle and needle not in haystack:
            continue
        result.append(dict(item))
    return result


def get_template_field_groups() -> List[str]:
    return sorted({str(item.get("group")) for item in FIELD_REGISTRY if item.get("group")})


def get_template_field_keys() -> set[str]:
    return set(FIELD_BY_KEY.keys())


def _docx_text_parts(content: bytes) -> Iterable[str]:
    with zipfile.ZipFile(BytesIO(content)) as archive:
        for name in archive.namelist():
            lowered = name.lower()
            if not lowered.startswith("word/") or not lowered.endswith(".xml"):
                continue
            if lowered.startswith("word/_rels/"):
                continue
            try:
                root = _xml_fromstring(archive.read(name))
            except Exception:
                continue
            text = "".join(root.itertext())
            if text:
                yield text


def extract_docx_placeholders(content: bytes) -> List[Dict]:
    found: Dict[str, Dict] = {}
    for text in _docx_text_parts(content):
        for pattern, braces in ((DOUBLE_PLACEHOLDER_RE, "double"), (SINGLE_PLACEHOLDER_RE, "single")):
            for match in pattern.finditer(text):
                marker = match.group(1) or ""
                key = match.group(2).strip()
                if not key:
                    continue
                raw = (
                    f"{{{{{marker + ' ' if marker else ' '}{key} }}}}"
                    if braces == "double"
                    else f"{{{marker + ' ' if marker else ''}{key}}}"
                )
                entry = found.setdefault(
                    key,
                    {
                        "key": key,
                        "raw": raw,
                        "marker": marker,
                        "known": key in FIELD_BY_KEY,
                    },
                )
                if marker and not entry.get("marker"):
                    entry["marker"] = marker
    return sorted(found.values(), key=lambda item: item["key"])


def unknown_placeholder_keys(placeholders: Iterable[Dict]) -> List[str]:
    known = get_template_field_keys()
    return sorted({item["key"] for item in placeholders if item.get("key") not in known})
