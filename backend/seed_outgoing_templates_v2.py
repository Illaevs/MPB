#!/usr/bin/env python3
"""
Seed / upsert template_v2 layouts for all outgoing document kinds:
letter, invoice (Счёт), upd (УПД), act (Акт), vat_invoice (Счёт-фактура).

Each template carries:
- layout_html         — locked text + [data-placeholder] chips + one
                        [data-editable="body"] region + optional
                        [data-table="stages"|"payments"] markers.
- editable_regions    — single "body".
- placeholder_fields  — each field tagged with role:
                          "anchor"   → user input drives /editor/resolve
                          "resolved" → read-only, filled from resolve
                        plus type/source/group for the right panel.

Idempotent: matches on (name, module, document_kind) and updates in place.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import DocumentTemplate

MODULE = "outgoing_registry"
EDITABLE = [{"key": "body", "label": "Текст документа",
             "allowed_marks": ["bold", "italic", "underline", "list", "alignment", "link"],
             "default_html": "<p></p>"}]

# ---- Reusable field defs --------------------------------------------------
F_RECIPIENT = {"key": "recipient.name", "label": "Контрагент", "type": "company-select",
               "source": "recipient", "role": "anchor", "required": True, "group": "parties"}
F_OUR = {"key": "our_company.name", "label": "Наша компания", "type": "our-company-select",
         "source": "our_company", "role": "anchor", "required": True, "group": "parties"}
F_DEAL = {"key": "deal.title", "label": "Сделка", "type": "deal-select",
          "source": "deal", "role": "anchor", "group": "context"}
F_CONTRACT = {"key": "contract.number", "label": "Договор", "type": "contract-select",
              "source": "contract", "role": "anchor", "group": "context"}
F_BANK = {"key": "recipient.bank.rs", "label": "Банк получателя", "type": "bank-account-select",
          "source": "recipient_bank", "role": "anchor", "group": "bank"}
F_STAGES = {"key": "linked_stage_ids", "label": "Этапы", "type": "stage-multiselect",
            "source": "stages", "role": "anchor", "group": "lines"}
F_PAYMENTS = {"key": "linked_payment_items", "label": "Платежи / зачёт аванса",
              "type": "payment-rows", "source": "payments", "role": "anchor", "group": "lines"}
F_DOCNUM = {"key": "document.number", "label": "Исходящий №", "type": "text",
            "role": "resolved", "group": "document"}
F_DOCDATE = {"key": "document.date", "label": "Дата документа", "type": "date",
             "role": "resolved", "group": "document"}

# resolved read-only requisites
def _resolved(key, label, group="requisites"):
    return {"key": key, "label": label, "type": "text", "role": "resolved", "group": group}

REQ_RECIPIENT = [
    _resolved("recipient.inn", "ИНН получателя"),
    _resolved("recipient.kpp", "КПП получателя"),
    _resolved("recipient.address", "Адрес получателя"),
    _resolved("recipient.bank.name", "Банк получателя"),
    _resolved("recipient.bank.bik", "БИК получателя"),
    _resolved("recipient.bank.ks", "Корр. счёт получателя"),
]
REQ_OUR = [
    _resolved("our_company.inn", "ИНН (наша)"),
    _resolved("our_company.kpp", "КПП (наша)"),
    _resolved("our_company.bank.name", "Банк (наш)"),
    _resolved("our_company.bank.rs", "Р/с (наш)"),
    _resolved("our_company.bank.bik", "БИК (наш)"),
    _resolved("our_company.bank.ks", "Корр. счёт (наш)"),
]
REQ_TOTALS = [
    _resolved("document.total_amount", "Сумма итого", "totals"),
    _resolved("document.vat_rate", "Ставка НДС", "totals"),
    _resolved("document.vat_amount", "Сумма НДС", "totals"),
    _resolved("document.total_amount_words", "Сумма прописью", "totals"),
]

PH = lambda k: f'<span data-placeholder="{k}"></span>'  # noqa: E731

# ---- Layouts --------------------------------------------------------------
LETTER_HTML = f"""\
<div class="doc-letterhead" data-locked="true">
  <div class="lh-name"><strong>{PH('our_company.full_name')}</strong></div>
  <div class="lh-req">{PH('our_company.address')} · ИНН {PH('our_company.inn')} · КПП {PH('our_company.kpp')}</div>
</div>
<div class="doc-rule" data-locked="true"></div>
<table class="nb" data-locked="true">
  <tr>
    <td style="width:56%">Исх. № {PH('document.number')}<br/>от {PH('document.date')}</td>
    <td style="width:44%" class="doc-recipient">{PH('recipient.eio')}<br/>{PH('recipient.short_name')}</td>
  </tr>
</table>
<p class="doc-salutation" data-locked="true">{PH('recipient.appeal')}</p>
<section class="doc-body" data-editable="body">
  <p>Настоящим уведомляем Вас о ходе выполнения работ по договору.</p>
</section>
<table class="nb doc-sign" data-locked="true">
  <tr>
    <td style="width:56%">Генеральный директор</td>
    <td style="width:44%" class="doc-sign-name">{PH('our_company.director_name')}</td>
  </tr>
</table>
"""

INVOICE_HTML = f"""\
<header><h1 data-locked="true">СЧЁТ № {PH('document.number')} от {PH('document.date')}</h1></header>
<section class="doc-req" data-locked="true">
  <p><b>Поставщик:</b> {PH('our_company.name')}, ИНН {PH('our_company.inn')}, КПП {PH('our_company.kpp')}</p>
  <p>{PH('our_company.bank.name')}, р/с {PH('our_company.bank.rs')}, БИК {PH('our_company.bank.bik')}, к/с {PH('our_company.bank.ks')}</p>
  <p><b>Покупатель:</b> {PH('recipient.name')}, ИНН {PH('recipient.inn')}, КПП {PH('recipient.kpp')}</p>
  <p><b>Основание:</b> договор {PH('contract.number')} от {PH('contract.date')}</p>
</section>
<div data-table="stages" data-locked="true"></div>
<section class="doc-totals" data-locked="true">
  <p>Итого: {PH('document.total_amount')}</p>
  <p>В том числе НДС {PH('document.vat_rate')}: {PH('document.vat_amount')}</p>
  <p>Всего к оплате: {PH('document.total_amount_words')}</p>
  <p>Оплатить до {PH('document.payment_due_date')}</p>
</section>
<section class="doc-letter__body" data-editable="body"><p></p></section>
<section class="doc-letter__signature" data-locked="true">
  <p>Руководитель {PH('our_company.director_name')}</p>
</section>
"""

UPD_HTML = f"""\
<header><h1 data-locked="true">УНИВЕРСАЛЬНЫЙ ПЕРЕДАТОЧНЫЙ ДОКУМЕНТ № {PH('document.number')} от {PH('document.date')}</h1></header>
<section class="doc-req" data-locked="true">
  <p><b>Продавец:</b> {PH('our_company.name')}, ИНН {PH('our_company.inn')}, КПП {PH('our_company.kpp')}, {PH('our_company.address')}</p>
  <p><b>Покупатель:</b> {PH('recipient.name')}, ИНН {PH('recipient.inn')}, КПП {PH('recipient.kpp')}, {PH('recipient.address')}</p>
  <p><b>Основание:</b> договор {PH('contract.number')} от {PH('contract.date')}</p>
</section>
<div data-table="stages" data-locked="true"></div>
<section class="doc-totals" data-locked="true">
  <p>Итого: {PH('document.total_amount')}, в т.ч. НДС {PH('document.vat_rate')}: {PH('document.vat_amount')}</p>
</section>
<section class="doc-letter__body" data-editable="body"><p></p></section>
<section class="doc-letter__signature" data-locked="true">
  <p>Руководитель {PH('our_company.director_name')}</p>
</section>
"""

ACT_HTML = f"""\
<header><h1 data-locked="true">АКТ выполненных работ № {PH('document.number')} от {PH('document.date')}</h1></header>
<section class="doc-req" data-locked="true">
  <p><b>Исполнитель:</b> {PH('our_company.name')}, ИНН {PH('our_company.inn')}</p>
  <p><b>Заказчик:</b> {PH('recipient.name')}, ИНН {PH('recipient.inn')}</p>
  <p><b>Основание:</b> договор {PH('contract.number')} от {PH('contract.date')}</p>
</section>
<div data-table="stages" data-locked="true"></div>
<section class="doc-locked" data-locked="true"><p><b>Зачёт аванса / платежи:</b></p></section>
<div data-table="payments" data-locked="true"></div>
<section class="doc-totals" data-locked="true">
  <p>Итого выполнено: {PH('document.total_amount')}, в т.ч. НДС {PH('document.vat_rate')}: {PH('document.vat_amount')}</p>
</section>
<section class="doc-letter__body" data-editable="body"><p>Работы выполнены в полном объёме, стороны претензий не имеют.</p></section>
<section class="doc-letter__signature" data-locked="true">
  <p>Исполнитель {PH('our_company.director_name')}</p>
</section>
"""

VAT_HTML = f"""\
<header><h1 data-locked="true">СЧЁТ-ФАКТУРА № {PH('document.number')} от {PH('document.date')}</h1></header>
<section class="doc-req" data-locked="true">
  <p><b>Продавец:</b> {PH('our_company.name')}, ИНН {PH('our_company.inn')}, КПП {PH('our_company.kpp')}</p>
  <p><b>Покупатель:</b> {PH('recipient.name')}, ИНН {PH('recipient.inn')}, КПП {PH('recipient.kpp')}</p>
  <p><b>Основание:</b> договор {PH('contract.number')} от {PH('contract.date')}</p>
</section>
<div data-table="stages" data-locked="true"></div>
<section class="doc-totals" data-locked="true">
  <p>Всего к оплате: {PH('document.total_amount')}, в т.ч. НДС {PH('document.vat_rate')}: {PH('document.vat_amount')}</p>
</section>
<section class="doc-letter__body" data-editable="body"><p></p></section>
<section class="doc-letter__signature" data-locked="true">
  <p>Руководитель {PH('our_company.director_name')}</p>
</section>
"""

TEMPLATES = [
    {
        "name": "Письмо-уведомление (v2)", "kind": "letter", "html": LETTER_HTML,
        "fields": [F_RECIPIENT, F_OUR, F_DEAL,
                   {"key": "recipient.eio", "label": "ЕИО получателя (кому)", "type": "text",
                    "role": "anchor", "group": "parties"},
                   {"key": "recipient.appeal", "label": "Обращение (приветствие)", "type": "text",
                    "role": "anchor", "group": "parties"},
                   F_DOCNUM, F_DOCDATE,
                   _resolved("recipient.short_name", "Получатель кратко", "parties"),
                   _resolved("our_company.full_name", "Наша компания (полное)"),
                   _resolved("our_company.address", "Адрес (наш)"),
                   _resolved("our_company.inn", "ИНН (наша)"),
                   _resolved("our_company.kpp", "КПП (наша)"),
                   _resolved("our_company.director_name", "Подписант (наш)")],
    },
    {
        "name": "Счёт (v2)", "kind": "invoice", "html": INVOICE_HTML,
        "fields": [F_RECIPIENT, F_OUR, F_DEAL, F_CONTRACT, F_BANK, F_STAGES,
                   F_DOCNUM, F_DOCDATE,
                   _resolved("document.payment_due_date", "Оплатить до", "totals"),
                   *REQ_RECIPIENT, *REQ_OUR, *REQ_TOTALS,
                   _resolved("contract.date", "Дата договора", "context"),
                   _resolved("our_company.director_name", "Подписант (наш)")],
    },
    {
        "name": "УПД (v2)", "kind": "upd", "html": UPD_HTML,
        "fields": [F_RECIPIENT, F_OUR, F_DEAL, F_CONTRACT, F_STAGES,
                   F_DOCNUM, F_DOCDATE,
                   *REQ_RECIPIENT, *REQ_OUR, *REQ_TOTALS,
                   _resolved("contract.date", "Дата договора", "context"),
                   _resolved("our_company.director_name", "Подписант (наш)")],
    },
    {
        "name": "Акт выполненных работ (v2)", "kind": "act", "html": ACT_HTML,
        "fields": [F_RECIPIENT, F_OUR, F_DEAL, F_CONTRACT, F_STAGES, F_PAYMENTS,
                   F_DOCNUM, F_DOCDATE,
                   *REQ_RECIPIENT, *REQ_OUR, *REQ_TOTALS,
                   _resolved("contract.date", "Дата договора", "context"),
                   _resolved("our_company.director_name", "Подписант (наш)")],
    },
    {
        "name": "Счёт-фактура (v2)", "kind": "vat_invoice", "html": VAT_HTML,
        "fields": [F_RECIPIENT, F_OUR, F_DEAL, F_CONTRACT, F_STAGES,
                   F_DOCNUM, F_DOCDATE,
                   *REQ_RECIPIENT, *REQ_OUR, *REQ_TOTALS,
                   _resolved("contract.date", "Дата договора", "context"),
                   _resolved("our_company.director_name", "Подписант (наш)")],
    },
]


async def main():
    from app.core.config import settings
    url = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(url, echo=False)
    Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        for tpl in TEMPLATES:
            existing = (await db.execute(
                select(DocumentTemplate).where(
                    DocumentTemplate.name == tpl["name"],
                    DocumentTemplate.module == MODULE,
                    DocumentTemplate.document_kind == tpl["kind"],
                )
            )).scalars().first()
            if existing:
                existing.layout_html = tpl["html"]
                existing.editable_regions_json = EDITABLE
                existing.placeholder_fields_json = tpl["fields"]
                existing.fields_json = [f["key"] for f in tpl["fields"]]
                existing.is_active = True
                existing.status = "approved"
                print(f"updated {tpl['kind']}: {existing.id}")
            else:
                row = DocumentTemplate(
                    name=tpl["name"],
                    description=f"template_v2 — {tpl['kind']}",
                    module=MODULE, document_kind=tpl["kind"],
                    binding_type="global", status="approved", is_active=True,
                    fields_json=[f["key"] for f in tpl["fields"]],
                    layout_html=tpl["html"],
                    editable_regions_json=EDITABLE,
                    placeholder_fields_json=tpl["fields"],
                )
                db.add(row)
                print(f"inserted {tpl['kind']}")
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
