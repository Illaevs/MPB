#!/usr/bin/env python3
"""
Seed a sample `template_v2` outgoing letter ("Письмо-уведомление").

Creates one DocumentTemplate row with:
- layout_html         — A4 letter with locked title, locked recipient block,
                        one editable "body" region, locked signature block.
- editable_regions    — single region {key: "body"}
- placeholder_fields  — schema for the right-side parameters form.

Idempotent: looks up an existing template by name + module + document_kind
and updates it instead of inserting a duplicate.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import DocumentTemplate


TEMPLATE_NAME = "Письмо-уведомление (v2)"
MODULE = "outgoing_registry"
DOCUMENT_KIND = "letter"

LAYOUT_HTML = """\
<header class="doc-letter__header">
  <h1 data-locked="true" class="doc-letter__title">ПИСЬМО-УВЕДОМЛЕНИЕ</h1>
</header>

<section class="doc-letter__recipient" data-locked="true">
  <p>Директору <span data-placeholder="recipient.name"></span></p>
  <p><span data-placeholder="recipient.eio.dative"></span></p>
</section>

<section class="doc-letter__meta" data-locked="true">
  <p>Исх. № <span data-placeholder="document.number"></span> от <span data-placeholder="document.date"></span></p>
</section>

<section class="doc-letter__body" data-editable="body">
  <p>Настоящим уведомляем Вас о том, что <span data-placeholder="our_company.name"></span> готов к выполнению следующего этапа работ по договору <span data-placeholder="contract.number"></span> от <span data-placeholder="contract.date"></span>.</p>
  <p>Просим Вас согласовать дату выезда специалистов.</p>
</section>

<section class="doc-letter__signature" data-locked="true">
  <p>С уважением,</p>
  <p>Генеральный директор <span data-placeholder="our_company.eio"></span></p>
</section>
"""

EDITABLE_REGIONS = [
    {
        "key": "body",
        "label": "Текст письма",
        "allowed_marks": ["bold", "italic", "underline", "list", "alignment", "link"],
        "default_html": "<p></p>",
    }
]

PLACEHOLDER_FIELDS = [
    {
        "key": "our_company.name",
        "label": "Наша компания",
        "type": "company-select",
        "source": "our_company",
        "required": True,
        "group": "company",
    },
    {
        "key": "recipient.name",
        "label": "Контрагент",
        "type": "company-select",
        "source": "recipient",
        "required": True,
        "group": "company",
    },
    {
        "key": "recipient.eio.dative",
        "label": "ЕИО (дат. падеж)",
        "type": "text",
        "placeholder": "Иванову И.И.",
        "group": "company",
    },
    {
        "key": "document.number",
        "label": "Исходящий №",
        "type": "text",
        "required": True,
        "group": "document",
    },
    {
        "key": "document.date",
        "label": "Дата документа",
        "type": "date",
        "required": True,
        "group": "document",
    },
    {
        "key": "contract.number",
        "label": "Номер договора",
        "type": "text",
        "group": "contract",
    },
    {
        "key": "contract.date",
        "label": "Дата договора",
        "type": "date",
        "group": "contract",
    },
    {
        "key": "our_company.eio",
        "label": "Наш ЕИО",
        "type": "text",
        "placeholder": "Смирнов А.В.",
        "group": "company",
    },
]


async def main():
    from app.core.config import settings

    database_url = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(database_url, echo=False)
    Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        existing = (await db.execute(
            select(DocumentTemplate).where(
                DocumentTemplate.name == TEMPLATE_NAME,
                DocumentTemplate.module == MODULE,
                DocumentTemplate.document_kind == DOCUMENT_KIND,
            )
        )).scalars().first()

        if existing:
            existing.layout_html = LAYOUT_HTML
            existing.editable_regions_json = EDITABLE_REGIONS
            existing.placeholder_fields_json = PLACEHOLDER_FIELDS
            existing.is_active = True
            existing.status = "approved"
            await db.commit()
            print(f"Updated existing template: {existing.id}")
        else:
            template = DocumentTemplate(
                name=TEMPLATE_NAME,
                description="Шаблон письма-уведомления нового поколения с редактируемой текстовой секцией и чипами-плейсхолдерами.",
                module=MODULE,
                document_kind=DOCUMENT_KIND,
                our_company_key=None,  # global
                binding_type="global",
                status="approved",
                is_active=True,
                fields_json=[f["key"] for f in PLACEHOLDER_FIELDS],
                layout_html=LAYOUT_HTML,
                editable_regions_json=EDITABLE_REGIONS,
                placeholder_fields_json=PLACEHOLDER_FIELDS,
            )
            db.add(template)
            await db.commit()
            print(f"Inserted new template: {template.id}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
